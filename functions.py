import random, time, math


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
def generate_mating_pool(population, fitnesses):
    n = len(population)
    mating_pool = []

    for _ in range(2):
        indexes = list(range(n))
        random.shuffle(indexes)

        for i in range(0, n - 1, 2):
            a, b = indexes[i], indexes[i + 1]
            if fitnesses[a] > fitnesses[b]:
                mating_pool.append(population[a])
            else:
                mating_pool.append(population[b])

    return mating_pool

# NOVEL FEATURE: ELITISM
def select_elites(population, fitnesses, elite_size):
    """
        Receives the population with their fitnesses calculated
        and returns the best elite_size individuals in a tuple (individual, fitness)
    """

    indexes = list(range(len(population)))
    indexes.sort(key = lambda i: fitnesses[i], reverse=True)
    # sort indexes by their fitness, best first

    elites = []
    for i in indexes[:elite_size]:
        elites.append((list(population[i]), fitnesses[i]))
        # copy of individual
    return elites

def insert_elites(population, fitnesses, elites):
    """
        Inserts the elite individuals into the population, substituting the worst individuals.
        Works in-place (in the variables passed in the arguments)
    """

    indexes = list(range(len(population)))
    indexes.sort(key=lambda i: fitnesses[i]) # worst first

    for position, (elite, elite_fitness) in zip(indexes, elites):
        population[position] = elite
        fitnesses[position] = elite_fitness


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



def two_opt(route, distances):
    best = route.copy()
    n = len(best)
    if n < 4:
        return best

    improved = True
    while improved:
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                a, b = best[i - 1], best[i]
                c, d = best[j], best[(j + 1) % n]
                old = distances[a][b] + distances[c][d]
                new = distances[a][c] + distances[b][d]
                if new < old:
                    best[i:j + 1] = reversed(best[i:j + 1])
                    improved = True
                    break
            if improved:
                break
    return best


# GENETIC ALGORITHM
def run_genetic_algorithm(population_size,
                          individual_size,
                          num_generations,
                          mutation_rate,
                          individual_generator,
                          fitness_function,
                          crossover_function,
                          mutation_function,
                          *args,
                          known_optimal = None,
                          elite_size = None):

    if elite_size is None:
        # by default 5% of the population, and a minimum of 1
        elite_size = max(1, int(0.05 * population_size))
    # safe limit: if elite_size is >= population_size, insert_elites would overwrite all children with copies of the past generations
    elite_size = min(elite_size, population_size - 1)

    # initial population and fitness
    population = generate_population(population_size, individual_generator, individual_size)
    best_fitness = 0
    best_individual = None
    individuals_evaluated = 0
    fitnesses = [fitness_function(individual, *args) for individual in population]

    reached_optimum = False
    for i in range(num_generations):
        if reached_optimum:
            break

        # save the best of this generation
        elites = select_elites(population, fitnesses, elite_size)

        # selection and crossover
        mating_pool = generate_mating_pool(population, fitnesses)
        new_population = []

        for j in range(0, len(mating_pool) -1, 2):
            child1, child2 = crossover_function(mating_pool[j], mating_pool[j+1])
            new_population.append(child1)
            new_population.append(child2)

        # mutation and evaluation of children
        new_fitnesses =[]
        for j in range(len(new_population)):
            new_population[j] = mutation_function(new_population[j], mutation_rate)
            new_fitnesses.append(fitness_function(new_population[j], *args))
        
        individuals_evaluated += len(new_population)

        # elites substitute the worst children
        insert_elites(new_population, new_fitnesses, elites)

        population = new_population
        fitnesses = new_fitnesses

        # update the best fitness found
        generation_best = max(fitnesses)
        
        if generation_best > best_fitness:
            best_fitness = generation_best
            best_individual = list(population[fitnesses.index(generation_best)])
            reached_optimum = has_reached_optimum(best_fitness, fitness_function, known_optimal)

    distance_before_2opt = None

    if fitness_function == fitness_tsp:
        distance_before_2opt = tsp_distance(best_individual, args[0])

        best_individual = two_opt(best_individual, args[0])
        best_fitness = tsp_distance(best_individual, args[0])

    return best_individual, best_fitness, individuals_evaluated, distance_before_2opt


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
    best_fitness = None
    distance_before_2opt = None

    try:
        if run["type"] == "onemax":
            _, best_fitness, _, _ = run_genetic_algorithm(run["population_size"],
                                                       run["gene_length"],
                                                       run["num_generations"],
                                                       run["mutation_rate"],
                                                       generate_individual,
                                                       fitness_onemax,
                                                       crossover_bitstring,
                                                       mutate_bitstring,
                                                       known_optimal=run.get("known_optimal"),
                                                       elite_size=run.get("elite_size"))
        else:
            _, best_fitness, _, distance_before_2opt = run_genetic_algorithm(run["population_size"],
                                                       len(run["cities"]),
                                                       run["num_generations"],
                                                       run["mutation_rate"],
                                                       generate_individual_permutation,
                                                       fitness_tsp,
                                                       crossover_permutation,
                                                       swap_mutation,
                                                       run["distance_matrix"],
                                                       known_optimal=run.get("known_optimal"),
                                                       elite_size=run.get("elite_size"))
    except Exception as error:
        print(f"Run {run["run_id"]} failed: {error}")

    running_time = time.time() - start_time
    return run["run_id"], best_fitness, running_time, distance_before_2opt

# CHECK IF RUN HAS REACHED OPTIMUM
def has_reached_optimum(fitness, fitness_function, known_optimal):
    if known_optimal is None:
        return False
    if fitness_function == fitness_tsp:
        distance = 1 / fitness
        return distance <= known_optimal or math.isclose(distance, known_optimal, abs_tol = 0.01) # to compare values until 2nd decimal
    # else: onemax
    return fitness >= known_optimal