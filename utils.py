from multiprocessing import cpu_count

def is_inrange(n):
    if n not in ["1", "2", "3", "4", "5", "6"]:
        print("Warning: Input must be an integer between 1 and 6.")
        return False
    return True

def is_positive_integer(n):
    try:
        n = int(n)
        if n>0:
            return True
    except ValueError:
        return False
    
    return False

def is_num_cores_valid(num_cores):
    is_positive = is_positive_integer(num_cores)
    available_cores =  cpu_count() 
    # cpu_count counts logic cores, not physical. They could be different because of hyper-threading

    if is_positive and available_cores >= int(num_cores):
        return True

    return False