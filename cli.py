import time
# add imports from functions.py
# add import from utils (check for positive int. etc.)

def load_problem():
    '''
    Reads: JSON file / current history.
    Modifies: runs, history, cores, output configs
    Error handling: Non-existent file, wrong formatting, invalid values
    '''


def adjust_execution_settings():
    '''
    Reads: current num cores.
    Modifies: num cores
    Error handling: Only positive value + integer, very big integer not valid. 
                    If so, keep prev num cores.
    '''


def run_all():
    '''
    Reads: Pending runs info, num cores (functions.py and load_problem)
    Modifies: history, state of each run, running time p-run + total time.
    Error handling: Nothing loaded, nothing pending, errors inside a run, everything run already
    '''


def check_status():
    '''
    Reads: run history // problem, config, best fitness, running time.
    Optional: Known optimal.
    Runs: finished / pending + loaded runs (total) + num cores.
    Error handling: Empty history
    '''


def export_results():
    '''
    Reads: final history + output configs
    Builds: output file + performance plot (best fitness over time) & (problem size vs time to optimal)
    Error handling: Nothing executed yet
    '''


def exit_program():
    '''
    Stops the loop returning boolean.
    Error handling: Warn about non-exported results before exit
    '''


def empty_state():
    '''
    Returns initial state: runs, history, cores, time...
    '''


def print_options():
    '''
    Prints 6 options available.
    '''


def choose_option():
    '''
    Reads: option from user
    Returns: valid option
    Error handling: strings, out of range integers
    '''


def cli_menu():
    '''
    Calls empty state
    Loop to show 6 options with dictionary that ends with boolean from exit_program.
    Error handling.
    '''