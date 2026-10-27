from os import process_cpu_count
from pathlib import Path
import matplotlib.pyplot as plt
from json import dumps
from matplotlib.widgets import Button
from pathlib import Path

def is_inrange(n):
    if n not in ["1", "2", "3", "4", "5", "6"]:
        print("Warning: Input must be an integer between 1 and 6.")
        return False
    return True


def validate_json_data(json_data):
    problems = []
    required_onemax = {"population_size", "num_generations", "mutation_rate", "gene_length"}
    required_tsp = {"population_size", "num_generations", "mutation_rate", "cities"}
    optional_problem = {"known_optimal"}
    optional_general = {"num_cores", "output"}
    allowed_groups = {"onemax_problems", "tsp_problems"}

    if "type" in json_data:
        # Un solo problema
        if json_data["type"] not in ("onemax", "tsp"):
            raise ValueError("Tipo de problema no válido.")

        problems.append((json_data["type"], json_data))

    else:
        allowed_keys = allowed_groups | optional_general

        if not set(json_data).issubset(allowed_keys):
            raise ValueError("El JSON contiene claves no permitidas.")

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
        raise ValueError("El JSON no contiene problemas.")

    # 3. Validar configuración general
    num_cores = json_data.get("num_cores", 1)
    if type(num_cores) is not int or num_cores <= 0:
        raise ValueError("'num_cores' debe ser un entero positivo.")

    output = json_data.get("output", {})
    if not isinstance(output, dict):
        raise ValueError("'output' debe ser un diccionario.")

    if not set(output).issubset({"save_to_file", "performance_plot"}):
        raise ValueError("'output' contiene claves no permitidas.")

    if "save_to_file" in output:
        path = output["save_to_file"]
        if path is not None and (not isinstance(path, str) or not path.strip()):
            raise ValueError("'save_to_file' debe ser una ruta válida.")

    if "performance_plot" in output:
        if type(output["performance_plot"]) is not bool:
            raise ValueError("'performance_plot' debe ser booleano.")

    # 4. Validar todos los problemas
    for problem_type, problem in problems:
        if not isinstance(problem, dict):
            raise ValueError("Cada problema debe ser un diccionario.")

        if problem_type == "onemax":
            required_keys = required_onemax
        else:
            required_keys = required_tsp

        allowed_keys = required_keys.union(optional_problem)
        if problem is json_data:
            allowed_keys = allowed_keys.union(optional_general, {"type"})

        if not required_keys.issubset(problem):
            raise ValueError(f"Faltan claves obligatorias en {problem_type}.")

        if not set(problem).issubset(allowed_keys):
            raise ValueError(f"Hay claves no permitidas en {problem_type}.")

        # 5. Validar hiperparámetros
        for key in ("population_size", "num_generations", "mutation_rate"):
            values = problem[key]
            if not isinstance(values, list):
                values = [values]

            if not values:
                raise ValueError(f"'{key}' no puede estar vacío.")

            for item in values:
                if key == "mutation_rate":
                    valid = type(item) in (int, float) and 0 < item <= 1
                else:
                    valid = type(item) is int and item > 0

                if not valid:
                    raise ValueError(f"Valor no válido en '{key}': {item}")

        # 6. Validar OneMax
        if problem_type == "onemax":
            gene_length = problem["gene_length"]
            if type(gene_length) is not int or gene_length <= 0:
                raise ValueError("'gene_length' debe ser un entero positivo.")

        # 7. Validar TSP
        else:
            cities = problem["cities"]

            if not isinstance(cities, list) or len(cities) < 2:
                raise ValueError("TSP requiere al menos dos ciudades.")

            for city in cities:
                if not isinstance(city, list) or len(city) != 2:
                    raise ValueError("Cada ciudad debe contener [x, y].")

                for coordinate in city:
                    if type(coordinate) not in (int, float):
                        raise ValueError("Las coordenadas deben ser numéricas.")

        # 8. Validar óptimo conocido
        if "known_optimal" in problem:
            optimal = problem["known_optimal"]

            if type(optimal) not in (int, float):
                raise ValueError("'known_optimal' debe ser numérico.")

            if problem_type == "onemax" and optimal != problem["gene_length"]:
                raise ValueError(
                    "'known_optimal' debe ser igual a 'gene_length'."
                )

            if problem_type == "tsp" and optimal < 0:
                raise ValueError("'known_optimal' no puede ser negativo.")

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

def get_plottable_runs(runs, problem_type):
    """
        Returns runs of the same type, finished and with known_optimal.
    """
    return [
        run for run in runs
        if run["type"] == problem_type
        and run["status"] == "Finished"
        and run.get("known_optimal") is not None
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
    return (run["population_size"], run["num_generations"], run["mutation_rate"])

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
        population_size, num_generations, mutation_rate = key
        label = f"pop={population_size}, gen={num_generations}, mut={mutation_rate}"

        # separate runs that reached the optimum from the ones that didnt
        reached = []
        failed = []
        for run in configurations:
            if run.get("known_optimal") == run.get("best_fitness"):
                reached.append(run)
            else:
                failed.append(run)

        # lines with the runs that reached the optimum, ordered by N
        reached.sort(key=get_problem_size)
        x = [get_problem_size(run) for run in reached]
        y = [run["running_time"] for run in reached]
        line = ax.plot(x, y, marker="o", label=label)[0]

        # adds an 'X' of same color to the ones that didnt reach the optimum
        x_failed = [get_problem_size(run) for run in failed]
        y_failed = [run["running_time"] for run in failed]
        ax.scatter(x_failed, y_failed, marker="x", s=80, color=line.get_color())

    # plot format

    # keep only actual sizes in x axis
    sizes = [get_problem_size(run) for run in plottable_runs]
    ax.set_xticks(range(min(sizes), max(sizes) + 1))

    ax.set_xlabel(f"N: problem size ({'gene_length' if problem_type == 'onemax' else 'number of cities'})")
    ax.set_ylabel("Time to reach optimum (s)")
    ax.set_title(f"{problem_type.upper()}: time to reach optimum vs N")
    ax.grid(alpha=0.3)

    # add legend entry explaining the 'X' marker
    ax.scatter([], [], marker="x", s=80, color="black", label="didn't reach optimum")

    # legend below the subplot
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15))

def plot_performance(runs, problem_types, output_dir, show=True):
    """
        Generates one subplot per problem type in the same figure, saves it in a PNG and returns the route.
    """

    fig, axes = plt.subplots(1, len(problem_types), figsize=(7 * len(problem_types), 6),
                             layout="constrained", squeeze=False)

    for ax, problem_type in zip(axes[0], problem_types):
        plot_problem(ax, runs, problem_type)

    # save and close
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    plot_path = Path(output_dir) / "performance_plot.png"
    fig.savefig(plot_path)

    if show:
        plt.show()

    plt.close(fig)
    return plot_path
