import multiprocessing
from utils import is_inrange, is_num_cores_valid, write_to_file
from functions import solve_run
import time


def load_problem(state):
    '''
    Reads: JSON file / current history.
    Modifies: runs, history, cores, output configs
    Error handling: Non-existent file, wrong formatting, invalid values
    '''
    print("Option 1 not implemented yet.")


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
    '''
    Reads: run history // problem, config, best fitness, running time.
    Optional: Known optimal.
    Runs: finished / pending + loaded runs (total) + num cores.
    Error handling: Empty history
    '''
    print("Option 4 not implemented yet.")


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