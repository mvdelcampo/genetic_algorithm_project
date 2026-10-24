def extract_problems(json_data):
    if "type" in json_data:
        problem_type = json_data["type"]
        problem_id = f"{problem_type}_1"
        problem_info = (problem_id, problem_type, json_data)
        problem = [problem_info]

        return problem

    extracted = []
    for group_name, problem_type in (("onemax_problems", "onemax"), ("tsp_problems", "tsp")):
        if group_name in json_data:
            problems = json_data[group_name]
            counter = 1
            for problem in problems:
                problem_id = f"{problem_type}_{counter}"
                extracted.append((problem_id, problem_type, problem))
                counter += 1

    return extracted