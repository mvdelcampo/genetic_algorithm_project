import json
import multiprocessing
import time
from utils import is_inrange, is_num_cores_valid, write_to_file, can_plot, plot_performance
from functions import solve_run
from json_loader import prepare_runs, load_json_file
from pathlib import Path


def load_problem(state, file_path):
    '''
    Reads: JSON file path.
    Modifies: runs, num cores, output configs.
    Keeps: previous run history and total execution time.
    '''
    try:
        json_data = load_json_file(file_path)
        if json_data is None:
            return state

        runs = prepare_runs(json_data, file_path)

        if not runs:
            print("No runs found in the JSON file.")
            return state

        cores = json_data.get('num_cores', state['num_cores'])
        if not is_num_cores_valid(str(cores)):
            print("Invalid number of cores.")
            return state

        output = json_data.get('output', state['output']) # TODO: si no hay output no toma el dict vacio y lo va a dar como valido?
        if not isinstance(output, dict):
            print("Invalid output configuration.")
            return state

        # Initialize new runs
        for run in runs:
            run['known_optimal'] = run.get('known_optimal')
            run['best_fitness'] = None
            run['running_time'] = None
            run['status'] = 'Pending'
            run['source_file'] = Path(file_path).name

        # Keep previous history
        state['runs'].extend(runs)

        # Update current configuration
        state['file_path'] = file_path
        state['num_cores'] = int(cores)
        state['output'] = dict(output)

        # Do not reset total_time
        return state

    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"Error loading problem: {error}")
        return state


def adjust_execution_settings(state):
    '''
    Reads: current num cores.
    Modifies: num cores.
    Error handling: Only positive integer up to available cores.
    '''
    print(f"\nCurrent number of cores: {state['num_cores']}")

    while True:
        num_cores = input("Enter the new number of cores to be used for parallel running (or 'b' to go back to the main menu): ").strip()

        if num_cores.lower() == 'b':
            print('No changes made. Returning to the main menu.')
            return state

        if is_num_cores_valid(num_cores):
            state['num_cores'] = int(num_cores)
            print('The number of cores has been successfully updated.')
            return state

        print('The provided number of cores is not valid, either because it is not a positive integer or the computer does not have so many cores available.')


def run_all(state):
    '''
    Reads: Pending runs, num cores.
    Modifies: results, status, running time per run and total time.
    Error handling: Nothing loaded, nothing pending, errors inside a run.
    '''
    if not state['runs']:
        print('There is no problem loaded yet. \nPress 1 to load a problem.')
        return state

    pending = []
    for run in state['runs']:
        if run['status'] == 'Pending':
            pending.append(run)

    if not pending:
        print('All runs have been executed. Load another problem to execute more runs.')
        return state

    print(f"Running {len(pending)} runs on {state['num_cores']} cores")

    start_time = time.perf_counter()
    try:
        with multiprocessing.Pool(processes=state['num_cores']) as pool:
            results = pool.map(solve_run, pending)
    except Exception as error:
        print(f'Error executing runs: {error}')
        return state

    state['total_time'] += time.perf_counter() - start_time

    runs_by_id = {run['run_id']: run for run in state['runs']}
    for run_id, best_fitness, running_time in results:
        run = runs_by_id[run_id]
        run['best_fitness'] = best_fitness
        run['running_time'] = running_time
        run['status'] = 'Finished' if best_fitness is not None else 'Failed'

    state['unsaved_results'] = True
    return state


def check_status(state):
    '''
    Reads: runs, best fitness, running time, known optimal, cores, total time.
    Shows: Loaded, pending, finished and failed runs with their configurations.
    Error handling: Nothing loaded, no results yet.
    '''
    if not state['runs']:
        print('There is no problem loaded yet. \nPress 1 to load a problem.')
        return state

    total = len(state['runs'])
    pending = sum(run['status'] == 'Pending' for run in state['runs'])
    finished = sum(run['status'] == 'Finished' for run in state['runs'])
    failed = sum(run['status'] == 'Failed' for run in state['runs'])

    print('\nEXECUTION STATUS')
    print(f'Total runs: {total}')
    print(f'Pending: {pending}')
    print(f'Finished: {finished}')
    print(f'Failed: {failed}')
    print(f"Number of cores: {state['num_cores']}")
    print(f"Total execution time: {state['total_time']:.4f} seconds")

    print('\nRUN DETAILS')
    for run in state['runs']:
        print(f"\nRun: {run['run_id']}")
        print(f"Problem: {run['problem_id']}")
        print(f"Type: {run['type']}")
        print(f"Population size: {run['population_size']}")
        print(f"Generations: {run['num_generations']}")
        print(f"Mutation rate: {run['mutation_rate']}")
        if run['type'] == 'onemax':
            print(f"Gene length: {run['gene_length']}")
        else:
            print(f"Number of cities: {len(run['cities'])}")
        print(f"Status: {run['status']}")

        if run.get('known_optimal') is not None:
            print(f"Known optimal: {run['known_optimal']}")

        if run['status'] == 'Finished':
            print(f"Best fitness: {run['best_fitness']}")
            print(f"Running time: {run['running_time']:.4f} seconds")

    return state


def export_results(state):
    '''
    Reads: finished runs and output configuration.
    Builds: output file and optional performance plot.
    Error handling: Nothing executed, invalid or missing output configuration.
    '''
    finished = [run for run in state['runs'] if run['status'] in ('Finished', 'Failed')]
    if not finished:
        print('No results available to export. Run the algorithm first.')
        return state

    output = state.get('output', {})
    file_name = output.get('save_to_file')
    if not file_name:
        print('No output file is configured.')
        return state

    print("The results will be saved in the 'output' folder.\nThe configured file name is", file_name)
    try:
        write_to_file(file_name, finished)
    except (OSError, ValueError, TypeError) as error:
        print(f'Error exporting results: {error}')
        return state

    state['unsaved_results'] = False

    if output.get('performance_plot', False):
        plottable_types = []
        for problem_type in sorted({run['type'] for run in finished}):
            if can_plot(finished, problem_type):
                plottable_types.append(problem_type)
            else:
                print(f'Plot of {problem_type} cannot be generated: at least 2 different problem sizes with known_optimal are required.')

        if plottable_types:
            try:
                plot_path = plot_performance(finished, plottable_types, 'output')
                print(f'Performance plot saved in {plot_path}.')
            except (OSError, ValueError, TypeError) as error:
                print(f'Error generating performance plot: {error}')

    return state


def exit_program(state):
    '''
    Stops the menu loop after warning about non-exported results.
    '''
    if state['unsaved_results']:
        print('Warning. You have not exported the results yet. \nAre you sure you want to exit the program?\n')
        decision = input("Type 'y' if you want to exit, 'n' if you want to stay: ").strip().lower()
        if decision != 'y':
            return False

    return True


def current_state():
    '''
    Returns initial state: runs, cores, output configuration, execution time.
    '''
    state = {
        'runs': [],
        'num_cores': 1,
        'output': {},
        'total_time': 0.0,
        'unsaved_results': False
    }
    return state


def print_boxed_title(title, width=60):
    print("+" + "-" * (width - 2) + "+")
    print("|" + title.center(width - 2) + "|")
    print("+" + "-" * (width - 2) + "+")


def print_options():
    options = [
        "1. Load problem",
        "2. Adjust execution settings",
        "3. Run algorithm",
        "4. Check status",
        "5. Export results",
        "6. Exit program"
    ]

    print()
    print_boxed_title("GENETIC ALGORITHM SOLVER")
    print("Please choose one of the following options:\n")

    for option in options:
        print(f"  {option}")

    print("\n" + "-" * 60)


def choose_option():
    '''
    Reads: option from user.
    Returns: valid option.
    Error handling: strings, out of range integers.
    '''
    option = input('\nWhich option would you like to execute?: ').strip()
    while not is_inrange(option):
        option = input('\nWhich option would you like to execute?: ').strip()
    print(f'\nExecuting option {option}.')
    return option


def cli_menu():
    '''
    Creates state and handles the six menu options.
    '''
    state = current_state()
    options_dict = {
        '2': adjust_execution_settings,
        '3': run_all,
        '4': check_status,
        '5': export_results,
        '6': exit_program
    }

    quit = False
    while not quit:
        print_options()
        option = choose_option()

        if option == '1':
            file_path = input('Enter JSON file path: ').strip()

            previous_count = len(state['runs'])
            state = load_problem(state, file_path)

            new_count = len(state['runs']) - previous_count

            if new_count > 0:
                print(f"File loaded successfully: {file_path}")
                print(f"New runs loaded: {new_count}")
                print(f"Total session runs: {len(state['runs'])}")
            else:
                print("No valid runs loaded. Previous session preserved.")
        elif option == '6':
            quit = options_dict[option](state)
        else:
            options_dict[option](state)


if __name__ == '__main__':
    cli_menu()
