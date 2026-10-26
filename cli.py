import time
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from utils import is_inrange, is_num_cores_valid, write_to_file
from json_loader import prepare_runs
from functions import (
    run_genetic_algorithm,
    generate_individual,
    generate_individual_permutation,
    fitness_onemax,
    fitness_tsp,
    crossover_bitstring,
    crossover_permutation,
    mutate_bitstring,
    swap_mutation
)
import multiprocessing
from queue import Empty


def current_state():
    state = {
        "runs": [],
        "num_cores": 1,
        "output_config": {"save_to_file": "test3.json"},
        "total_time": 0.0,
        "unsaved_results": False,
        "executor": None,
        "manager": None,
        "status_queue": None
    }
    return state


def load_problem(state, file_path):
    if any(not future.done() for future in state["futures"].values()):
        return False

    try:
        runs = prepare_runs(file_path)

        if not runs:
            return False

        for run in runs:
            run["known_optimal"] = run.get("known_optimal")
            run["best_fitness"] = None
            run["running_time"] = None
            run["status"] = "pending"

        state["file_path"] = file_path
        state["runs"] = runs
        state["futures"] = {}
        state["total_time"] = 0.0
        state["unsaved_results"] = False

        return True

    except (ValueError, KeyError, TypeError):
        return False


def execute_run(run, status_queue):
    status_queue.put(run["run_id"])

    start_time = time.perf_counter()

    if run["type"] == "onemax":
        best_individual, best_fitness, individuals_evaluated = run_genetic_algorithm(
            run["population_size"],
            run["gene_length"],
            run["num_generations"],
            run["mutation_rate"],
            generate_individual,
            fitness_onemax,
            crossover_bitstring,
            mutate_bitstring
        )

    else:
        best_individual, best_fitness, individuals_evaluated = run_genetic_algorithm(
            run["population_size"],
            len(run["cities"]),
            run["num_generations"],
            run["mutation_rate"],
            generate_individual_permutation,
            fitness_tsp,
            crossover_permutation,
            swap_mutation,
            run["distance_matrix"]
        )

    running_time = time.perf_counter() - start_time

    return {
        "best_individual": best_individual,
        "best_fitness": best_fitness,
        "individuals_evaluated": individuals_evaluated,
        "running_time": running_time
    }


def adjust_execution_settings(state):
    '''
    Reads: current num cores.
    Modifies: num cores
    Error handling: Only positive value + integer, bigger integer than available cores not valid. 
                    If so, keep prev num cores.
    '''
    print(f"\nCurrent number of cores: {state["num_cores"]}")

    while True:
        num_cores = input("Enter the new number of cores to be used for parallel running (or 'b' to fo back to the main menu): ").strip()

        if num_cores.lower() == "b":
            print("No changes made. Returning to the main menu.")
            return

        if is_num_cores_valid(num_cores):
            state["num_cores"] = int(num_cores)
            print("The number of cores has been successfully updated.")
            return
        else:
            print("The provided number of cores is not valid, either because it is not a positive integer or the computer does not have so many cores available.")


def update_status(state):
    status_queue = state["status_queue"]

    if status_queue is not None:
        while True:
            try:
                run_id = status_queue.get_nowait()

                for run in state["runs"]:
                    if run["run_id"] == run_id and run["status"] == "pending":
                        run["status"] = "running"
                        break

            except Empty:
                break

    for run in state["runs"]:
        future = run.get("future")

        if future is None:
            continue

        if future.done() and run["status"] not in ("completed", "failed"):
            try:
                result = future.result()

                run["best_individual"] = result["best_individual"]
                run["best_fitness"] = result["best_fitness"]
                run["individuals_evaluated"] = result["individuals_evaluated"]
                run["running_time"] = result["running_time"]
                run["status"] = "completed"

                state["total_time"] += result["running_time"]
                state["unsaved_results"] = True

            except Exception as error:
                run["status"] = "failed"
                run["error"] = str(error)


def run_all(state):
    if not state["runs"]:
        print("No problems loaded.")
        return

    # Update results from previous executions
    update_status(state)

    pending_runs = [
        run for run in state["runs"]
        if run["status"] == "pending"
    ]

    if not pending_runs:
        print("No pending runs available.")
        return

    # Create shared queue and process executor
    if state["executor"] is None:
        state["manager"] = multiprocessing.Manager()
        state["status_queue"] = state["manager"].Queue()

        state["executor"] = ProcessPoolExecutor(
            max_workers=state["num_cores"]
        )

    # Submit pending runs
    for run in pending_runs:
        run_data = {
            key: value for key, value in run.items()
            if key != "future"
        }

        run["future"] = state["executor"].submit(
            execute_run,
            run_data,
            state["status_queue"]
        )

    print(f"{len(pending_runs)} runs submitted.")
    print(f"Using {state['num_cores']} workers.")


def check_status(state):
    if not state["runs"]:
        print("No problems loaded.")
        return

    update_status(state)

    total = len(state["runs"])
    pending = sum(run["status"] == "pending" for run in state["runs"])
    running = sum(run["status"] == "running" for run in state["runs"])
    completed = sum(run["status"] == "completed" for run in state["runs"])
    failed = sum(run["status"] == "failed" for run in state["runs"])

    print("\nEXECUTION STATUS")
    print(f"Total runs: {total}")
    print(f"Pending: {pending}")
    print(f"Running: {running}")
    print(f"Completed: {completed}")
    print(f"Failed: {failed}")
    print(f"Number of workers: {state['num_cores']}")

    print("\nRUN DETAILS")

    for run in state["runs"]:
        print(f"\nRun: {run['run_id']}")
        print(f"Problem: {run['problem_id']}")
        print(f"Type: {run['type']}")
        print(f"Population size: {run['population_size']}")
        print(f"Generations: {run['num_generations']}")
        print(f"Mutation rate: {run['mutation_rate']}")
        print(f"Status: {run['status']}")

        if run["status"] == "completed":
            print(f"Best fitness: {run['best_fitness']}")
            print(f"Running time: {run['running_time']:.2f} seconds")

        if run.get("known_optimal") is not None:
            print(f"Known optimal: {run['known_optimal']}")

        if run["status"] == "failed":
            print(f"Error: {run['error']}")



def export_results(state):
    '''
    Reads: final history + output configs
    Builds: output file + performance plot (best fitness over time) & (problem size vs time to optimal)
    Error handling: Nothing executed yet
    '''
    file_name = state["output_config"]["save_to_file"]

    print("The results will be saved in the 'output' folder.\nThe configurated file name is", file_name)
    
    write_to_file(file_name, "test")

    return


def exit_program(state):
    '''
    Stops the loop returning boolean.
    Error handling: Warn about non-exported results before exit
    '''
    quit = True
    return quit
    

def current_state():
    '''
    Returns initial state: runs, history, cores, time...
    '''
    state = {
        "runs": [],           
        "history": [],
        "num_cores": 1,
        "output_config": {"save_to_file": "test3.json"},
        "total_time": 0.0, 
        "unsaved_results": False
    }
    return state


def print_options():
    '''
    Prints 6 options available.
    '''
    print("\nGENETIC ALGORITHM SOLVER \nPlease, choose one of the following options:\n")
    names = ["Load problem", 
             "Adjust execution settings", 
             "Run algorithm", 
             "Check status", 
             "Export results", 
             "Exit Program"]
    for i in range(1, len(names)+1):
        print(f"{i}. {names[i-1]}")


def choose_option():
    '''
    Reads: option from user
    Returns: valid option
    Error handling: strings, out of range integers
    '''
    option = input("\nWhich option would you like to execute?: ").strip()
    while not is_inrange(option):
        option = input("\nWhich option would you like to execute?: ").strip()
    print("\nExecuting option", option, ".")
    return option


def cli_menu():
    '''
    Calls empty state
    Loop to show 6 options with dictionary that ends with boolean from exit_program.
    Error handling.
    '''
    state = current_state()
    options_dict = {
            "1": load_problem,
            "2": adjust_execution_settings,
            "3": run_all,
            "4": check_status,
            "5": export_results,
            "6": exit_program
        }
    quit = False

    while quit == False:
        print_options()
        option = choose_option()
        options_dict[f"{option}"](state)
        

        
if __name__ == "__main__":
    cli_menu()