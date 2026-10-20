import random
import copy
import math
import time
from dataclasses import dataclass
from enum import Enum
from operator import itemgetter
from data_struct import Truck, TruckState, Package, PackageState, objectiveFunction

class AxisPermutation(Enum):
    XYZ = (0, 1, 2)
    XZY = (0, 2, 1)
    YZX = (1, 2, 0)
    YXZ = (1, 0, 2)
    ZXY = (2, 0, 1)
    ZYX = (2, 1, 0)

def axis_permutation_to_orientation(permutation : AxisPermutation) -> dict[str, str]:
    axisToDim = {0 : "w", 1 : "l", 2 : "h"}
    x = axisToDim[permutation.value[0]]
    y = axisToDim[permutation.value[1]]
    z = axisToDim[permutation.value[2]]

    return {"x" : x, "y" : y, "z" : z}

class Gene:
    def __init__(self, 
                 id : str, 
                 loaded_flag : int, 
                 orientation : AxisPermutation) -> None:
        self.id = id
        self.loaded_flag = loaded_flag  
        self.orientation = orientation

class Chromosome:
    def __init__(self, 
                 genes : list[Gene], 
                 placement_order : AxisPermutation) -> None:
        self.genes = genes
        self.placement_order = placement_order

def encoded_coords_to_decoded_coords(coordinates: tuple[int, int, int]) -> dict[str, int]:
    return {"x" : coordinates[0], "y" : coordinates[1], "z" : coordinates[2]}

def populationInitialization(n : int, truckState : TruckState,
                             rng: random.Random | None = None) -> list[Chromosome]:
    rng = rng or random
    packages = [packageState.package for packageState in truckState.packages]
    package_amount = len(packages)
    packages_id = [package.id for package in packages]

    population = []
    for i in range(n):
        genes = []
        available_packages = copy.deepcopy(packages_id)
        for j in range(package_amount):
            id = rng.choice(available_packages)
            available_packages.remove(id)
            loaded_flag = rng.randint(0, 1)
            orientation = rng.choice(list(AxisPermutation))
            gene = Gene(id, loaded_flag, orientation)
            genes.append(gene)
        placementOrder = rng.choice(list(AxisPermutation))

        chromosome = Chromosome(genes, placementOrder)
        population.append(chromosome)

    return population

class AABB:
    def __init__(self, 
                 coordinates : tuple[int, int, int],
                 dimension : dict[str, int], 
                 orientation : AxisPermutation=AxisPermutation.XYZ) -> None:
        phenotype_orientation = axis_permutation_to_orientation(orientation)
        
        self.x_min = coordinates[0]
        self.y_min = coordinates[1]
        self.z_min = coordinates[2]
        self.x_max = self.x_min + dimension[phenotype_orientation["x"]]
        self.y_max = self.y_min + dimension[phenotype_orientation["y"]]
        self.z_max = self.z_min + dimension[phenotype_orientation["z"]]


@dataclass
class OccupiedPackage:
    box: AABB
    is_fragile: bool

def detect_box_collision(aabb1 : AABB, aabb2 : AABB) -> bool:
    front = aabb2.x_min < aabb1.x_max
    back = aabb1.x_min < aabb2.x_max
    right = aabb2.y_min < aabb1.y_max
    left = aabb1.y_min < aabb2.y_max
    up = aabb2.z_min < aabb1.z_max
    down = aabb1.z_min < aabb2.z_max

    return front and back and right and left and up and down

def is_point_in_box(point : tuple[int, int, int], box : AABB) -> bool:
    front = box.x_min <= point[0]
    back = point[0] < box.x_max
    right = box.y_min <= point[1]
    left = point[1] < box.y_max
    up = box.z_min <= point[2]
    down = point[2] < box.z_max

    return front and back and right and left and up and down

# based on Extreme Point Heuristics
def candidate_point_generation(bounding_box : AABB,
                               occupied_space : list[OccupiedPackage]) -> list[tuple[int, int, int]]:
    extreme_x = (bounding_box.x_max, bounding_box.y_min, bounding_box.z_min)
    extreme_y = (bounding_box.x_min, bounding_box.y_max, bounding_box.z_min)
    extreme_z = (bounding_box.x_min, bounding_box.y_min, bounding_box.z_max)

    candidate_point_1 = (extreme_x[0], extreme_x[1], 0)
    candidate_point_2 = (extreme_x[0], 0, extreme_x[2])
    candidate_point_3 = (extreme_y[0], extreme_y[1], 0)
    candidate_point_4 = (0, extreme_y[1], extreme_y[2])
    candidate_point_5 = (extreme_z[0], 0, extreme_z[2])
    candidate_point_6 = (0, extreme_z[1], extreme_z[2])
    for occupied_package in occupied_space:
        box = occupied_package.box
        # x projected on xy plane
        if (extreme_x[0] >= box.x_min and extreme_x[0] < box.x_max and
            extreme_x[1] >= box.y_min and extreme_x[1] < box.y_max and
            extreme_x[2] > box.z_max):
            candidate_point = (extreme_x[0], extreme_x[1], box.z_max)
            if (candidate_point[2] > candidate_point_1[2]):
                candidate_point_1 = candidate_point
            
        # x projected on xz plane
        if (extreme_x[0] >= box.x_min and extreme_x[0] < box.x_max and
            extreme_x[2] >= box.z_min and extreme_x[2] < box.z_max and
            extreme_x[1] > box.y_max):
            candidate_point = (extreme_x[0], box.y_max, extreme_x[2])
            if (candidate_point[1] > candidate_point_2[1]):
                candidate_point_2 = candidate_point
            
        # y projected on xy plane
        if (extreme_y[0] >= box.x_min and extreme_y[0] < box.x_max and
            extreme_y[1] >= box.y_min and extreme_y[1] < box.y_max and
            extreme_y[2] > box.z_max):
            candidate_point = (extreme_y[0], extreme_y[1], box.z_max)
            if (candidate_point[2] > candidate_point_3[2]):
                candidate_point_3 = candidate_point

        # y projected on yz plane
        if (extreme_y[1] >= box.y_min and extreme_y[1] < box.y_max and
            extreme_y[2] >= box.z_min and extreme_y[2] < box.z_max and
            extreme_y[0] > box.x_max):
            candidate_point = (box.x_max, extreme_y[1], extreme_y[2])
            if (candidate_point[0] > candidate_point_4[0]):
                candidate_point_4 = candidate_point

        # z projected on xz plane
        if (extreme_z[0] >= box.x_min and extreme_z[0] < box.x_max and
            extreme_z[2] >= box.z_min and extreme_z[2] < box.z_max and
            extreme_z[1] > box.y_max):
            candidate_point = (extreme_z[0], box.y_max, extreme_z[2])
            if (candidate_point[1] > candidate_point_5[1]):
                candidate_point_5 = candidate_point

        # z projected on yz plane
        if (extreme_z[1] >= box.y_min and extreme_z[1] < box.y_max and
            extreme_z[2] >= box.z_min and extreme_z[2] < box.z_max and
            extreme_z[0] > box.x_max):
            candidate_point = (box.x_max, extreme_z[1], extreme_z[2])
            if (candidate_point[0] > candidate_point_6[0]):
                candidate_point_6 = candidate_point

    candidate_points = [candidate_point_1, candidate_point_2, candidate_point_3,
                        candidate_point_4, candidate_point_5, candidate_point_6]

    return candidate_points

def update_extreme_points(extreme_points : set[tuple[int, int, int]], 
                          candidate_points : list[tuple[int, int, int]],
                          old_occupied_space : list[OccupiedPackage], 
                          truck : Truck,
                          new_package : AABB) -> set[tuple[int, int, int]]:

    to_remove = {point for point in extreme_points if is_point_in_box(point, new_package)}
    extreme_points.difference_update(to_remove)

    for candidate_point in candidate_points:
        if (candidate_point [0] < 0 or 
            candidate_point[0] >= truck.dimensions["w"] or
            candidate_point [1] < 0 or
            candidate_point[1] >= truck.dimensions["l"] or
            candidate_point [2] < 0 or
            candidate_point[2] >= truck.dimensions["h"]):
            continue

        if (is_point_in_box(candidate_point, new_package)):
            continue

        if any(is_point_in_box(candidate_point, occupied.box) for occupied in old_occupied_space):
            continue

        extreme_points.add(candidate_point)

    return extreme_points

def placement_algorithm(placement_order : AxisPermutation, extreme_points : set[tuple[int, int, int]],
                        cur_package_data : Package, orientation : AxisPermutation, 
                        occupied_space : list[OccupiedPackage], truck : Truck) -> tuple[AABB, AxisPermutation]:

    sort_axes = placement_order.value[::-1]
    # check all possible placement points 
    sorted_extreme_points = sorted(extreme_points, 
                                   key=itemgetter(*sort_axes))
    
    list_orientation = list(AxisPermutation)
    start_i_orientation = list_orientation.index(orientation)
    orientation_order = list_orientation[start_i_orientation:] + list_orientation[:start_i_orientation]

    placed = False
    for cur_extreme_point in sorted_extreme_points:
        # try all orientation
        for cur_orientation in orientation_order:
            cur_package_bounding_box = AABB(cur_extreme_point, cur_package_data.dimensions, cur_orientation)

            # reject packages extending beyond the truck.
            if (
                cur_package_bounding_box.x_max > truck.dimensions["w"]
                or cur_package_bounding_box.y_max > truck.dimensions["l"]
                or cur_package_bounding_box.z_max > truck.dimensions["h"]):
                continue

            # reject overlapping packages.
            if any(detect_box_collision(cur_package_bounding_box, occupied.box) for occupied in occupied_space):
                continue

            # check support.
            supported = cur_package_bounding_box.z_min == 0

            if not supported:
                for occupied in occupied_space:
                    support_box = occupied.box

                    if (not occupied.is_fragile
                        and support_box.z_max == cur_package_bounding_box.z_min
                        and min(support_box.x_max, cur_package_bounding_box.x_max) > max(support_box.x_min, cur_package_bounding_box.x_min)
                        and min(support_box.y_max, cur_package_bounding_box.y_max) > max(support_box.y_min, cur_package_bounding_box.y_min)):
                        supported = True
                        break

            if supported:
                placed = True
                chosen_orientation = cur_orientation
                break
           
        if placed:
            break

    if (not placed):
        fallback_point = sorted_extreme_points[0] if sorted_extreme_points else (0, 0, 0)
        chosen_orientation = orientation
        cur_package_bounding_box = AABB(fallback_point, cur_package_data.dimensions, chosen_orientation)

    candidate_points = candidate_point_generation(cur_package_bounding_box, occupied_space)

    update_extreme_points(extreme_points, candidate_points, occupied_space, truck, cur_package_bounding_box)

    occupied_space.append(OccupiedPackage(cur_package_bounding_box, cur_package_data.isFragile))

    return (cur_package_bounding_box, chosen_orientation)

def decode(truck : Truck, packages_data : list[Package], chromosome : Chromosome) -> TruckState:

    package_by_id = {package.id : package for package in packages_data}

    package_states = []
    extreme_points = {(0, 0, 0)}
    occupied_space: list[OccupiedPackage] = []
    for gene in chromosome.genes:
        package_data = package_by_id[gene.id]

        loaded_flag = gene.loaded_flag
        if(loaded_flag):
            placed_package, chosen_orientation = placement_algorithm(chromosome.placement_order, extreme_points, package_data, gene.orientation, occupied_space, truck)
            coordinates = encoded_coords_to_decoded_coords((placed_package.x_min, placed_package.y_min, placed_package.z_min))
            orientation = axis_permutation_to_orientation(chosen_orientation)

            package_state = PackageState(package_data, coordinates, orientation)
        else:
            coordinates = encoded_coords_to_decoded_coords((-1, -1, -1))
            orientation = axis_permutation_to_orientation(gene.orientation)

            package_state = PackageState(package_data, coordinates, orientation)

        package_states.append(package_state)

    return TruckState(truck, package_states)

def validate_feasibility(state: TruckState) -> bool:
    dimensions = state.truck.dimensions

    boxes = []
    total_weight = 0

    for item in state.packages:
        package = item.package
        coords = item.coordinates

        # Unloaded packages are excluded from the physical constraints
        if (coords["x"], coords["y"], coords["z"]) == (-1, -1, -1):
            continue

        low = tuple(coords[k] for k in ("x", "y", "z"))
        high = tuple(
            low[i] + package.dimensions[item.orientation[k]]
            for i, k in enumerate(("x", "y", "z"))
        )

        # Loaded packages cannot penetrate the truck walls
        if (high[0] > dimensions["w"] or
            high[1] > dimensions["l"] or
            high[2] > dimensions["h"]):
            return False

        boxes.append((low, high, package.isFragile))
        total_weight += package.weight

    # Total weight of loaded packages must not exceed maxCapacity
    if total_weight > state.truck.maxCapacity:
        return False

    for i, (low, high, _) in enumerate(boxes):
        supported = low[2] == 0

        for j, (other_low, other_high, other_fragile) in enumerate(boxes):
            if i == j:
                continue

            xy_overlap = (
                min(high[0], other_high[0]) > max(low[0], other_low[0])
                and min(high[1], other_high[1]) > max(low[1], other_low[1])
            )

            if not xy_overlap:
                continue

            # Packages cannot overlap
            if min(high[2], other_high[2]) > max(low[2], other_low[2]):
                return False

            if low[2] == other_high[2]:
                supported = True

                # Fragile package cannot support another package
                if other_fragile:
                    return False

        # Package above the floor needs a supporting base contact
        if not supported:
            return False

    return True


def tournament_selection(population: list[Chromosome], fitnesses: list[float],
                         tournament_size: int = 3,
                         rng: random.Random | None = None) -> Chromosome:
    rng = rng or random
    winner = max((rng.randrange(len(population)) for _ in range(tournament_size)),
                 key=lambda index: fitnesses[index])
    
    return population[winner]


def order_crossover(parent1: Chromosome, parent2: Chromosome,
                    rng: random.Random | None = None) -> tuple[Chromosome, Chromosome]:
    rng = rng or random

    n = len(parent1.genes)
    start, end = sorted(rng.sample(range(n + 1), 2)) if n else (0, 0)
    children: list[Chromosome] = []
    for primary, secondary in ((parent1, parent2), (parent2, parent1)):
        genes = [None] * n
        genes[start:end] = [copy.deepcopy(g) for g in primary.genes[start:end]]
        used = {g.id for g in genes if g is not None}
        fill = (list(range(end, n)) + list(range(end)))
        donor = secondary.genes[end:] + secondary.genes[:end]
        remaining = (g for g in donor if g.id not in used)
        for index in fill:
            if genes[index] is None:
                genes[index] = copy.deepcopy(next(remaining))
        placement = rng.choice((primary.placement_order, secondary.placement_order))
        children.append(Chromosome(genes, placement))

    return children[0], children[1]


def mutate(chromosome: Chromosome, package_probability: float = 0.20,
           placement_probability: float = 0.05,
           rng: random.Random | None = None) -> Chromosome:
    rng = rng or random

    result = copy.deepcopy(chromosome)
    if result.genes and rng.random() < package_probability:
        operations = ["flip", "orientation"]
        if len(result.genes) >= 2:
            operations.append("swap")
        operation = rng.choice(operations)
        if operation == "swap":
            i, j = rng.sample(range(len(result.genes)), 2)
            result.genes[i], result.genes[j] = result.genes[j], result.genes[i]
        else:
            gene = rng.choice(result.genes)
            if operation == "flip":
                gene.loaded_flag = 1 - gene.loaded_flag
            else:
                gene.orientation = rng.choice([p for p in AxisPermutation if p != gene.orientation])

    if rng.random() < placement_probability:
        result.placement_order = rng.choice([p for p in AxisPermutation
                                             if p != result.placement_order])
        
    return result


@dataclass
class GenerationStats:
    generation: int
    maximum_fitness: float
    mean_fitness: float
    best_feasible_fitness: float
    feasible_percentage: float


@dataclass
class GAResult:
    initial_state: TruckState
    final_state: TruckState
    final_fitness: float
    history: list[GenerationStats]
    duration: float


@dataclass
class FeasibleRecord:
    chromosome: Chromosome
    state: TruckState
    fitness: float


def evaluate_population(population: list[Chromosome], truck: Truck,
                        packages: list[Package],
                        archive: FeasibleRecord, generation: int
                        ) -> tuple[list[float], GenerationStats, FeasibleRecord]:
    fitnesses: list[float] = []
    feasible_count = 0
    for chromosome in population:
        state = decode(truck, packages, chromosome)
        fitness = objectiveFunction(state)
        fitnesses.append(fitness)
        if validate_feasibility(state):
            feasible_count += 1
            if fitness > archive.fitness:
                archive = FeasibleRecord(copy.deepcopy(chromosome),
                                          copy.deepcopy(state), fitness)
                
    stats = GenerationStats(generation, max(fitnesses),
                            sum(fitnesses) / len(fitnesses), archive.fitness,
                            100 * feasible_count / len(population))
    
    return fitnesses, stats, archive


def genetic_algorithm(initial_state: TruckState, population_size: int = 100,
                      generations: int = 200, tournament_size: int = 3,
                      crossover_probability: float = 0.8,
                      package_mutation_probability: float = 0.20,
                      placement_mutation_probability: float = 0.05,
                      seed: int | None = None) -> GAResult:
    start_time = time.time()
    rng = random.Random(seed)
    
    packages = [item.package for item in initial_state.packages]

    empty = Chromosome([Gene(package.id, 0, AxisPermutation.XYZ) for package in packages],
                       AxisPermutation.XYZ)
    empty_state = decode(initial_state.truck, packages, empty)

    record = FeasibleRecord(copy.deepcopy(empty), copy.deepcopy(empty_state),
                              objectiveFunction(empty_state))
    
    population = populationInitialization(population_size, initial_state, rng)
    initial_decoded = copy.deepcopy(decode(initial_state.truck, packages, population[0]))

    history: list[GenerationStats] = []
    fitnesses, stats, record = evaluate_population(
        population, initial_state.truck, packages, record, 0)
    history.append(stats)
    for generation in range(1, generations + 1):
        elite_count = min(population_size - 1, max(1, math.ceil(0.02 * population_size)))
        elite_indices = sorted(range(population_size), key=lambda i: fitnesses[i], reverse=True)[:elite_count]

        next_population = [copy.deepcopy(population[i]) for i in elite_indices]
        while len(next_population) < population_size:
            parent1 = tournament_selection(population, fitnesses, tournament_size, rng)
            parent2 = tournament_selection(population, fitnesses, tournament_size, rng)

            if rng.random() < crossover_probability:
                children = order_crossover(parent1, parent2, rng)
            else:
                children = copy.deepcopy(parent1), copy.deepcopy(parent2)
            for child in children:
                if len(next_population) < population_size:
                    next_population.append(mutate(child, package_mutation_probability,
                                                  placement_mutation_probability, rng))
                    
        population = next_population
        fitnesses, stats, record = evaluate_population(
            population, initial_state.truck, packages, record, generation)
        history.append(stats)

    duration = time.time() - start_time

    return GAResult(initial_decoded, record.state, record.fitness, history, duration)
