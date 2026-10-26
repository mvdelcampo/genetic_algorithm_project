import multiprocessing
from utils import is_inrange, is_num_cores_valid, write_to_file, can_plot, plot_performance
from functions import solve_run
import time


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
    '''
    Reads: Pending runs info, num cores (functions.py and load_problem)
    Modifies: history, state of each run, running time p-run + total time.
    Error handling: Nothing loaded, nothing pending, errors inside a run, everything run already
    '''
    if not state["runs"]:
        print("There is no problem loaded yet. \nPress 1 to load a problem.")
        return 
    
    pending = []
    for run in state["runs"]:
        if run["status"] == "Pending":
            pending.append(run)
    if len(pending) == 0:
        print("All runs have been executed. Load another problem to execute more runs.")
        return 

    print(f"Running {len(pending)} runs on {state["num_cores"]} cores")

    start_time = time.time()
    with multiprocessing.Pool(processes=state["num_cores"]) as pool:
        results = pool.map(solve_run, pending)
    state["total_time"] = state["total_time"] + (time.time() - start_time)

    for run_id, best_fitness, running_time in results:
        for run in state["runs"]:
            if run_id == run["run_id"]:
                run["best_fitness"] = best_fitness
                run["running_time"] = running_time
                run["status"] = "Finished" if best_fitness is not None else "Failed"

    state["unsaved_results"] = True

    return state


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
    Builds: output file + performance plot
    Error handling: Nothing executed yet
    '''
    # harcoded state to test
    state = {"runs": [{ "run_id": "onemax_1_run_1",
                        "problem_id": "onemax_1",
                        "type": "onemax",
                        "population_size": 20, 
                        "num_generations": 30, 
                        "mutation_rate": 0.1, 
                        "gene_length": 10, 
                        "known_optimal": 10,
                        "best_fitness_found": 10,
                        "running_time": 2.2,
                        "status": "finished"
                        },
                        { "run_id": "onemax_2_run_2",
                        "problem_id": "onemax_2",
                        "type": "onemax",
                        "population_size": 10, 
                        "num_generations": 30, 
                        "mutation_rate": 0.1, 
                        "gene_length": 11, 
                        "known_optimal": 11,
                        "best_fitness_found": 10,
                        "running_time": 3.2,
                        "status": "finished"
                        },
                        { "run_id": "onemax_3_run_3",
                        "problem_id": "onemax_3",
                        "type": "onemax",
                        "population_size": 20, 
                        "num_generations": 30, 
                        "mutation_rate": 0.05, 
                        "gene_length": 15, 
                        "known_optimal": 15,
                        "best_fitness_found": 15,
                        "running_time": 3.5,
                        "status": "finished"
                        },
                        { "run_id": "onemax_4_run_4",
                        "problem_id": "onemax_4",
                        "type": "onemax",
                        "population_size": 50, 
                        "num_generations": 30, 
                        "mutation_rate": 0.1, 
                        "gene_length": 11, 
                        "known_optimal": 11,
                        "best_fitness_found": 11,
                        "running_time": 3.8,
                        "status": "finished"
                        },
                        { "run_id": "onemax_5_run_5",
                        "problem_id": "onemax_5",
                        "type": "onemax",
                        "population_size": 50, 
                        "num_generations": 30, 
                        "mutation_rate": 0.2, 
                        "gene_length": 15, 
                        "known_optimal": 15,
                        "best_fitness_found": 15,
                        "running_time": 4.0,
                        "status": "finished"
                        },
                        { "run_id": "onemax_6_run_6",
                        "problem_id": "onemax_6",
                        "type": "onemax",
                        "population_size": 20, 
                        "num_generations": 30, 
                        "mutation_rate": 0.05, 
                        "gene_length": 13, 
                        "known_optimal": 13,
                        "best_fitness_found": 13,
                        "running_time": 3.8,
                        "status": "finished"
                        },
                        {"run_id": "tsp_1_run_1",
                        "problem_id": "tsp_1",
                        "type": "tsp",
                        "population_size": 50, 
                        "num_generations": 200, 
                        "mutation_rate": 0.2, 
                        "cities": [[17, 72], [97, 8], [32, 15], [63, 97]],
                        "known_optimal": 303,
                        "best_fitness_found": 303,
                        "running_time": 5.6,
                        "status": "finished"
                        },
                        { "run_id": "tsp_2_run_2",
                        "problem_id": "tsp_2",
                        "type": "tsp",
                        "population_size": 30, 
                        "num_generations": 200, 
                        "mutation_rate": 0.1, 
                        "cities": [[17, 72], [97, 8], [32, 15]],
                        "known_optimal": 296,
                        "best_fitness_found": 296,
                        "running_time": 6.1,
                        "status": "finished"
                        },
                        {"run_id": "tsp_3_run_3",
                        "problem_id": "tsp_3",
                        "type": "tsp",
                        "population_size": 50, 
                        "num_generations": 200, 
                        "mutation_rate": 0.2, 
                        "cities": [[17, 72], [97, 8], [32, 15], [63, 97], [10, 10]],
                        "known_optimal": 303,
                        "best_fitness_found": 303,
                        "running_time": 6,
                        "status": "finished"
                        },
            ],
            # "history": [],
            "num_cores": 1,
            "output": {"save_to_file": "history.txt",
                        "performance_plot": True},
            "total_time": 0.0, 
            "unsaved_results": False
        }

    # error handling if any key is not present is done in load_problem
    
    # save history to file
    file_name = state["output"]["save_to_file"]
    print("The results will be saved in the 'output' folder.\nThe configurated file name is", file_name)
    write_to_file(file_name, state["runs"])

    # performance plot
    if state["output"]["performance_plot"] is True:
        runs = state["runs"]
        plottable_types = []
        for problem_type in sorted({run["type"] for run in runs}):
            if can_plot(runs, problem_type):
                plottable_types.append(problem_type)
            else:
                print(f"Plot of {problem_type} cannot be generated:\n user should load at least 2 problems with different problem size (gene_length or number of cities) and a known_optimal.")

        if plottable_types:
            plot_path = plot_performance(runs, plottable_types, "output")
            print(f"Performance plot saved in {plot_path}.")

    return

def exit_program(state):
    '''
    Stops the loop returning boolean.
    Error handling: Warn about non-exported results before exit
    '''
    if state["unsaved_results"] == True:
        print("Warning. You have not exported the results yet. \nAre you sure you want to exit the program?\n")
        decision = input("Type 'y' if you want to exit, 'n' if you want to stay: ")
        if decision.lower() == "y":
            quit = True
        else:
            quit = False
            return quit

    quit = True
    return quit
    

def current_state():
    '''
    Returns initial state: runs, history, cores, time...
    '''
    state = {
        "runs": [],
        "num_cores": 1,
        "output": {"save_to_file": "test3.json"},
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
    print(f"\nExecuting option {option}.")
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
        quit = options_dict[f"{option}"](state) is True
        
        
if __name__ == "__main__":
    cli_menu()