from os import process_cpu_count
from pathlib import Path
import matplotlib.pyplot as plt
from json import dumps
import math

def is_inrange(n):
    if n not in ["1", "2", "3", "4", "5", "6"]:
        print("Warning: Input must be an integer between 1 and 6.")
        return False
    return True


def validate_json_data(json_data):
    problems = []
    required_onemax = {"population_size", "num_generations", "mutation_rate", "gene_length"}
    required_tsp = {"population_size", "num_generations", "mutation_rate", "cities"}
    optional_problem = {"known_optimal", "elite_size"}
    optional_general = {"num_cores", "output"}
    allowed_groups = {"onemax_problems", "tsp_problems"}

    if "type" in json_data:
        # Single problem
        if json_data["type"] not in ("onemax", "tsp"):
            raise ValueError("Invalid problem type.")

        problems.append((json_data["type"], json_data))

    else:
        allowed_keys = allowed_groups | optional_general

        if not set(json_data).issubset(allowed_keys):
            raise ValueError("JSON contains invalid keys.")

        for group_name, problem_type in (
            ("onemax_problems", "onemax"),
            ("tsp_problems", "tsp")
        ):
            if group_name not in json_data:
                continue

            group = json_data[group_name]
            group = group if isinstance(group, list) else [group]

            for problem in group:
                problems.append((problem_type, problem))

    if not problems:
        raise ValueError("JSON does not contain any problems.")

    # 3. Validate general configuration
    num_cores = json_data.get("num_cores", 1)
    if type(num_cores) is not int or num_cores <= 0:
        raise ValueError("'num_cores' must be a positive integer.")

    output = json_data.get("output", {})
    if not isinstance(output, dict):
        raise ValueError("'output' must be a dictionary.")

    if not set(output).issubset({"save_to_file", "performance_plot"}):
        raise ValueError("'output' contains invalid keys.")

    if "save_to_file" in output:
        path = output["save_to_file"]
        if path is not None and (not isinstance(path, str) or not path.strip()):
            raise ValueError("'save_to_file' must be a valid path.")

    if "performance_plot" in output:
        if type(output["performance_plot"]) is not bool:
            raise ValueError("'performance_plot' must be a boolean.")

    # 4. Validate all problems
    for problem_type, problem in problems:
        if not isinstance(problem, dict):
            raise ValueError("Each problem must be a dictionary.")

        if problem_type == "onemax":
            required_keys = required_onemax
        else:
            required_keys = required_tsp

        allowed_keys = required_keys.union(optional_problem)
        if problem is json_data:
            allowed_keys = allowed_keys.union(optional_general, {"type"})

        if not required_keys.issubset(problem):
            raise ValueError(f"Missing required keys in {problem_type}.")

        if not set(problem).issubset(allowed_keys):
            raise ValueError(f"Invalid keys in {problem_type}.")

        # 5. Validate hyperparameters
        for key in ("population_size", "num_generations", "mutation_rate"):
            values = problem[key]
            if not isinstance(values, list):
                values = [values]

            if not values:
                raise ValueError(f"'{key}' cannot be empty.")

            for item in values:
                if key == "mutation_rate":
                    valid = type(item) in (int, float) and 0 < item <= 1
                elif key == "population_size":
                    valid = type(item) is int and item >= 2
                else:
                    valid = type(item) is int and item > 0

                if not valid:
                    raise ValueError(f"Invalid value for '{key}': {item}")

        # 6. Validate OneMax
        if problem_type == "onemax":
            gene_length = problem["gene_length"]
            if type(gene_length) is not int or gene_length <= 0:
                raise ValueError("'gene_length' must be a positive integer.")

        # 7. Validate TSP
        else:
            cities = problem["cities"]

            if not isinstance(cities, list) or len(cities) < 4:
                raise ValueError("TSP requires at least 4 cities.")

            for city in cities:
                if not isinstance(city, list) or len(city) != 2:
                    raise ValueError("Each city must contain [x, y].")

                for coordinate in city:
                    if type(coordinate) not in (int, float):
                        raise ValueError("City coordinates must be numeric.")

            # all cities in the same position, makes every route length 0
            if len({tuple(city) for city in cities}) == 1:
                raise ValueError("All cities cannot have the same coordinates.")


        # 8. Validate known optimal
        if "known_optimal" in problem:
            optimal = problem["known_optimal"]

            if type(optimal) not in (int, float):
                raise ValueError("'known_optimal' must be numeric.")

            if problem_type == "onemax" and optimal != problem["gene_length"]:
                raise ValueError(
                    "'known_optimal' must be equal to 'gene_length'."
                )

            if problem_type == "tsp" and optimal < 0:
                raise ValueError("'known_optimal' cannot be negative.")

        # 9. Validate elite_size if present
        if "elite_size" in problem:
            elite = problem["elite_size"]
            if type(elite) is not int or elite < 0:
                raise ValueError("'elite_size' must be an integer >= 0.")


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
    extension = route.suffix.lower()

    if extension == ".json":
        route.write_text(dumps(content, indent=4, ensure_ascii=False), encoding="utf-8")
    else:
        # assumes .txt or any other extension: readable plain text, one block per run
        lines = []
        for run in content:
            for key, value in run.items():
                lines.append(f"{key}: {value}")
            lines.append("")
        route.write_text("\n".join(lines), encoding="utf-8")

    return route

def get_problem_size(run):
    """
        Returns N depending on the type of problem.
    """
    if run["type"] == "onemax":
        return run["gene_length"]
    if run["type"] == "tsp":
        return len(run["cities"])
    return None

def is_optimal_value(value, problem_type, known_optimal):
    """
        Receives value: distance for TSP, number of ones for OneMax, problem_type and known_optimal.
        Returns a boolean, True if value = known_optimal (with tolerance of 2 decimals), or False if they are different.
    """
    if known_optimal is None:
        return False
    if problem_type == "tsp":
        return value <= known_optimal or math.isclose(value, known_optimal, abs_tol=0.01)
    return value >= known_optimal

def get_plottable_runs(runs, problem_type):
    """
        Returns runs of the same type, finished, with a known_optimal and that have acheived it.
    """
    return [
        run for run in runs
        if run["type"] == problem_type
        and run["status"] == "Finished"
        and run.get("known_optimal") is not None
        and is_optimal_value(run.get("best_fitness"), run.get('type'), run.get("known_optimal"))
    ]

def can_plot(runs, problem_type):
    """
        Checks if the conditions to plot are satisfied and returns the corresponding boolean.
        (If there are at least two different problem_sizes between the plottable runs)
    """
    sizes = {get_problem_size(run) for run in get_plottable_runs(runs, problem_type)}
    return len(sizes) >= 2

def get_configurations_tuple(run):
    """
        Returns the configuration tuple of parameters of a run
    """
    return (run["population_size"], run["num_generations"], run["mutation_rate"], run.get("elite_size"))

def plot_problem(ax, runs, problem_type):
    """
        Draws problem_size (N) vs running_time until known_optimal of one problem type in the given ax.
    """
    plottable_runs = get_plottable_runs(runs, problem_type)

    # group runs by configuration
    groups = {}
    for run in plottable_runs:
        key = get_configurations_tuple(run)
        if key not in groups:
            groups[key] = []
        groups[key].append(run)

    for key, configurations in groups.items():
        population_size, num_generations, mutation_rate, elite_size = key
        if elite_size is None:
            elite_label = "default (5% pop)"
        else:
            elite_label = elite_size
        label = f"pop={population_size}, gen={num_generations}, mut={mutation_rate}, elite = {elite_label}"

        # lines with the runs ordered by N
        configurations.sort(key=get_problem_size)
        x = [get_problem_size(run) for run in configurations]
        y = [run["running_time"] for run in configurations]
        ax.plot(x, y, marker="o", label=label)[0]

    # plot format

    # integer ticks every 2 sizes (wider step if the range is large, max 10 ticks)
    sizes = [get_problem_size(run) for run in plottable_runs]
    step = max(1, math.ceil((max(sizes) - min(sizes)) / 10))
    ax.set_xticks(range(min(sizes), max(sizes) + 1, step))

    ax.margins(y=0.03)  # 3% of margin instead of 5% by default
    ax.set_xlabel(f"N: problem size ({'gene length' if problem_type == 'onemax' else 'number of cities'})")
    ax.set_ylabel("Time (s)")
    ax.set_title(f"{problem_type.upper()}: execution time vs problem size")
    ax.grid(alpha=0.3)

    # legend to the right of the subplot, vertically centered
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5))

def plot_performance(runs, problem_types, output_dir, file_name, show=True):
    """
        Generates one subplot per problem type in the same figure (stacked vertically),
        saves it in a PNG and returns the route.
    """

    fig, axes = plt.subplots(len(problem_types), 1, figsize=(10, 4.5 * len(problem_types)),
                             layout="constrained", squeeze=False)

    for ax, problem_type in zip(axes[:, 0], problem_types):
        plot_problem(ax, runs, problem_type)

    # save and close
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    plot_name = Path(file_name).stem + "_plot.png"
    plot_path = Path(output_dir) / plot_name
    fig.savefig(plot_path)

    if show:
        plt.show()

    plt.close(fig)
    return plot_path
