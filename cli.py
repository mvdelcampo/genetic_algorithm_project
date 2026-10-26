import time
from utils import is_inrange, is_num_cores_valid, write_to_file, can_plot, plot_performance

# add imports from functions.py
# add import from utils (check for positive int. etc.)

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
    print("Option 3 not implemented yet.")


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