import itertools
import json
from utils import validate_json_data
from functions import build_distances_matrix
from pathlib import Path


def load_json_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8-sig") as file:
            json_data = json.load(file)

        validate_json_data(json_data)

        return json_data

    except FileNotFoundError:
        print(f"Error: No existe el archivo {file_path}")
        return None

    except json.JSONDecodeError:
        print("Error: El archivo no contiene un JSON válido.")
        return None


def extract_problems(json_data, file_path):
    file_name = Path(file_path).stem

    if "type" in json_data:
        problem_type = json_data["type"]
        problem_id = f"{file_name}_{problem_type}_1"
        return [(problem_id, problem_type, json_data)]

    extracted = []

    for group_name, problem_type in (
        ("onemax_problems", "onemax"),
        ("tsp_problems", "tsp")
    ):
        if group_name in json_data:
            problems = json_data[group_name]

            if not isinstance(problems, list):
                problems = [problems]

            for counter, problem in enumerate(problems, start=1):
                problem_id = f"{file_name}_{problem_type}_{counter}"
                extracted.append((problem_id, problem_type, problem))

    return extracted



def expand_problem_runs(problem_id, problem_type, problem_data):
    parameters = {}

    for name in ("population_size", "num_generations", "mutation_rate"):
        value = problem_data[name]
        if type(value) != list:
            value = [value]
        parameters[name] = value

    combinations = itertools.product(
        parameters["population_size"],
        parameters["num_generations"],
        parameters["mutation_rate"]
    )

    runs = []
    counter = 1

    for population_size, num_generations, mutation_rate in combinations:
        run = {
            "run_id": f"{problem_id}_run_{counter}",
            "problem_id": problem_id,
            "type": problem_type,
            "population_size": population_size,
            "num_generations": num_generations,
            "mutation_rate": mutation_rate
        }

        if problem_type == "onemax":
            run["gene_length"] = problem_data["gene_length"]

        elif problem_type == "tsp":
            cities = problem_data["cities"]
            run["cities"] = cities
            run["distance_matrix"] = build_distances_matrix(cities)

        if "known_optimal" in problem_data:
            run["known_optimal"] = problem_data["known_optimal"]

        if "elite_size" in problem_data:
            run["elite_size"] = problem_data["elite_size"]

        runs.append(run)
        counter += 1

    return runs


def prepare_runs(json_data, file_path):
    problems = extract_problems(json_data, file_path)
    all_runs = []

    for problem_id, problem_type, problem_data in problems:
        runs = expand_problem_runs(problem_id, problem_type, problem_data)
        all_runs.extend(runs)

    return all_runs
