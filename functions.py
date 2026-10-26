import random
import time


# GENERATE INDIVIDUALS
def generate_individual(gene_length):
    individual = []
    for i in range(gene_length):
        individual.append(random.randint(0,1))

    return individual

def generate_individual_permutation(size):
    individual = []
    for i in range(0, size):
        individual.append(i)
    random.shuffle(individual)

    return individual

def generate_population(population_size, individual_generator, size):
    population = []
    for i in range(population_size):
        individual = individual_generator(size)
        population.append(individual)

    return population


# CALCULATE FITNESSES
def tsp_distance(route, distances):
    total = 0
    for i in range(len(route)):
        total+=distances[route[i]][route[(i+1)%len(route)]]

    return total

def fitness_tsp(route, distances):
    return 1/tsp_distance(route, distances)

def fitness_onemax(individual):
    return sum(individual)


# MATING POOL FUNCTION
def generate_mating_pool(population, fitness_function, *args):
    indexes = [x for x in range(len(population))] 
    comparisons = []
    mating_pool = []

    for i in range(2):
        random.shuffle(indexes)
        for i in range(0, len(indexes) - 1, 2):
            tupla = tuple(indexes[i:i+2])
            comparisons.append(tupla)

    for tupla in comparisons:
        if (fitness_function(population[tupla[0]], *args) > fitness_function(population[tupla[1]], *args)):
            mating_pool.append(population[tupla[0]])
        else:
            mating_pool.append(population[tupla[1]])

    return mating_pool


# CROSSOVER FUNCTIONS
def generate_cut_point(gene_length):
    return random.randint(2, gene_length-2)

def crossover_bitstring(parent1, parent2):
    cut = generate_cut_point(len(parent1))
    child1 = parent1[:cut] + parent2[cut:]
    child2 = parent2[:cut] + parent1[cut:]

    return child1, child2

def fill_remaining_in_order(fixed_segment, source_parent):
    genes = []
    for i in range(len(source_parent)):
        if source_parent[i] not in fixed_segment:
            genes.append(source_parent[i])

    return genes

def crossover_permutation(parent1, parent2):
    cut = generate_cut_point(len(parent1))
    child1 = parent1[:cut] + fill_remaining_in_order(parent1[:cut], parent2)
    child2 = parent2[:cut] + fill_remaining_in_order(parent2[:cut], parent1)

    return child1, child2


# MUTATION FUNCTIONS
def mutate_bitstring(individual, mutation_rate):
    # changes individual in-place
    for i in range(len(individual)):
        if random.random() < mutation_rate:
            if individual[i] == 0:
                individual[i] = 1
            else: # == 1
                individual[i] = 0

    return individual

def swap_mutation(individual, mutation_rate):
    if random.random() < mutation_rate:
        # random.sample(range(10), 2) chooses elements from a sequence without repetition, for example: [7, 2]; never [4, 4]
        p1, p2 = random.sample(range(0, len(individual)), 2)
        individual[p1], individual[p2] = individual[p2], individual[p1]

    return individual


# GENETIC ALGORITHM
def run_genetic_algorithm(population_size, 
                          individual_size, 
                          num_generations, 
                          mutation_rate, 
                          individual_generator, 
                          fitness_function,
                          crossover_function,
                          mutation_function,
                          *args):
    population = generate_population(population_size, individual_generator, individual_size)
    best_fitness = 0
    best_individual = None
    individuals_evaluated = 0
    for i in range(num_generations):
        mating_pool = generate_mating_pool(population, fitness_function, *args)
        individuals_evaluated += len(mating_pool)
        new_population = []
        population = []
        for j in range(0, len(mating_pool), 2):
            child1, child2 = crossover_function(mating_pool[j], mating_pool[j+1])
            new_population.append(child1)
            new_population.append(child2)
        for j in range(len(new_population)):
            individual = mutation_function(new_population[j], mutation_rate)
            population.append(individual)
            fitness = fitness_function(individual, *args)
            if fitness > best_fitness:
                best_fitness = fitness
                best_individual = individual
    if fitness_function == fitness_tsp:
        best_fitness = 1 / best_fitness
    return best_individual, best_fitness, individuals_evaluated


# DISTANCE MATRIX
def build_distances_matrix(city_coordinates):
    distances = [[0 for _ in range(len(city_coordinates))] for _ in range(len(city_coordinates))]
    for i in range(len(city_coordinates)):
        for j in range(len(city_coordinates)):
            x1, y1 = city_coordinates[i]
            x2, y2 = city_coordinates[j]

            distance_ij = ((x2 - x1)**2 + (y2 - y1)**2) ** 0.5
            distances[i][j] = distance_ij

    return distances


# RANDOM SEARCH
def random_search(size, distances, time_limit = 3.0):
    routes_tried = 0
    fitness = 0
    best_distance = 1e06
    start_time = time.time()
    while (time.time() - start_time) < time_limit: # and fitness < size --> OPCION
        routes_tried+=1
        route = generate_individual_permutation(size)
        fitness = fitness_tsp(route, distances)
        distance = 1/fitness
        if distance < best_distance:
            best_distance = distance

    return routes_tried, best_distance


# SOLVE RUN FOR MULTIPROCESSING
def solve_run(run):
    start_time = time.time()
    best_fitness = None

    try:
        if run["type"] == "onemax":
            _, best_fitness, _ = run_genetic_algorithm(run["population_size"],
                                                       run["gene_length"],
                                                       run["num_generations"],
                                                       run["mutation_rate"],
                                                       generate_individual,
                                                       fitness_onemax,
                                                       crossover_bitstring,
                                                       mutate_bitstring)
        else:
            _, best_fitness, _ = run_genetic_algorithm(run["population_size"],
                                                       len(run["cities"]),
                                                       run["num_generations"],
                                                       run["mutation_rate"],
                                                       generate_individual_permutation,
                                                       fitness_tsp,
                                                       crossover_permutation,
                                                       swap_mutation,
                                                       run["distance_matrix"])
    except Exception as error:
        print(f"Run {run["run_id"]} failed: {error}")

    running_time = time.time() - start_time
    return run["run_id"], best_fitness, running_time