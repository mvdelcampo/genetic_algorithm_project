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