from os import process_cpu_count
from pathlib import Path

def is_inrange(n):
    if n not in ["1", "2", "3", "4", "5", "6"]:
        print("Warning: Input must be an integer between 1 and 6.")
        return False
    return True

def is_positive_integer(n):
    '''
        Checks if a value is a positive integer.
        Returns a boolean.
    '''
    try:
        n = int(n)
        if n>0:
            return True
    except ValueError:
        return False
    
    return False

def is_num_cores_valid(num_cores):
    '''
        Checks if the number of cores provided is valid: 
            is positive integer and smaller or equal to the cores available in the current computer.
        Returns a boolean.
    '''
    is_positive = is_positive_integer(num_cores)
    available_cores =  process_cpu_count() 
    # process_cpu_count returns available logic cores, not physical. They could be different because of hyper-threading

    if is_positive and available_cores >= int(num_cores):
        return True

    return False

def write_to_file(file_name, content):
    '''
        Creates the folder "output" if it does not exist, to save output files.
        Creates file "file_name" inside the folder, and writes the content of 
        parameter "content" inside it.
        Returns the route to the created file.
    '''

    Path("output").mkdir(parents=True, exist_ok=True)

    route = Path("output") / file_name # / operator joins routes

    route.write_text(content, encoding="utf-8")

    return route



