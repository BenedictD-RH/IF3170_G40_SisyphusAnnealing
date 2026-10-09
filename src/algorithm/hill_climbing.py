import time
import math
import random
import copy
from data_struct import Truck, TruckState, PackageState, Package, objectiveFunction
from concurrent.futures import ThreadPoolExecutor


class HillClimbing:
    def __init__(self, initial_state: TruckState, max_iterations: int = 1000, step_size: int = 2, random_init: bool = True):
        if random_init:
            self.initial_state = initial_state.generate_random_state()
        else:
            self.initial_state = copy.deepcopy(initial_state)

        self.current_state = copy.deepcopy(self.initial_state)
        self.best_state = copy.deepcopy(self.initial_state)
        self.max_iterations = max_iterations
        self.step_size = step_size
        self.history: list[dict] = []
        self.accepted_moves: int = 0
        self.total_iterations: int = 0
        self.execution_time: float = 0.0

    def rotate_90(self, orientation: dict[str, str], axis: str) -> dict[str, str]:
        new_ori = dict(orientation)
        if axis == "x":
            new_ori["y"], new_ori["z"] = new_ori["z"], new_ori["y"]
        elif axis == "y":
            new_ori["x"], new_ori["z"] = new_ori["z"], new_ori["x"]
        elif axis == "z":
            new_ori["x"], new_ori["y"] = new_ori["y"], new_ori["x"]
        return new_ori

    # buat HC SA,stocastic
    def get_neighbor(self, state: TruckState) -> TruckState:
        neighbor = copy.deepcopy(state)
        n_pkgs = len(neighbor.packages)
        if n_pkgs == 0:
            return neighbor

        # Pilih salah satu dari 3 aksi yang diperbolehkan
        actions = ["move", "rotate"]
        if n_pkgs >= 2:
            actions.append("swap")

        action = random.choice(actions)
        truck_dims = neighbor.truck.dimensions

        if action == "swap":
            # 1. Menukar dua paket, baik di dalam maupun di luar truk
            i, j = random.sample(range(n_pkgs), 2)
            p1 = neighbor.packages[i]
            p2 = neighbor.packages[j]
            p1.coordinates, p2.coordinates = copy.deepcopy(p2.coordinates), copy.deepcopy(p1.coordinates)
            p1.orientation, p2.orientation = copy.deepcopy(p2.orientation), copy.deepcopy(p1.orientation)

        elif action == "move":
            # 2. Memindahkan sebuah paket ke suatu koordinat integer yang berbeda (di dalam atau di luar truk)
            pkg = random.choice(neighbor.packages)
            move_mode = random.choice(["shift", "random_inside", "toggle_outside"])

            if move_mode == "shift" and pkg.coordinates["x"] >= 0:
                # Pergeseran lokal di dalam truk
                step = self.step_size
                pkg.coordinates["x"] = max(0, min(truck_dims.get("w", 10) - 1, pkg.coordinates["x"] + random.randint(-step, step)))
                pkg.coordinates["y"] = max(0, min(truck_dims.get("l", 10) - 1, pkg.coordinates["y"] + random.randint(-step, step)))
                pkg.coordinates["z"] = max(0, min(truck_dims.get("h", 10) - 1, pkg.coordinates["z"] + random.randint(-step, step)))
            elif move_mode == "random_inside" or (move_mode == "shift" and pkg.coordinates["x"] < 0):
                # Pindahkan ke koordinat integer acak di dalam truk
                pkg.coordinates = {
                    "x": random.randint(0, max(0, truck_dims.get("w", 10) - 1)),
                    "y": random.randint(0, max(0, truck_dims.get("l", 10) - 1)),
                    "z": random.randint(0, max(0, truck_dims.get("h", 10) - 1))
                }
            elif move_mode == "toggle_outside":
                if pkg.coordinates["x"] >= 0:
                    # Keluarkan paket ke luar peti kemas truk
                    pkg.coordinates = {"x": -1, "y": -1, "z": -1}
                else:
                    # Masukkan paket dari luar ke dalam truk
                    pkg.coordinates = {
                        "x": random.randint(0, max(0, truck_dims.get("w", 10) - 1)),
                        "y": random.randint(0, max(0, truck_dims.get("l", 10) - 1)),
                        "z": random.randint(0, max(0, truck_dims.get("h", 10) - 1))
                    }

        elif action == "rotate":
            # 3. Merotasi paket 90° terhadap sumbu x, y, atau z
            pkg = random.choice(neighbor.packages)
            axis = random.choice(["x", "y", "z"])
            pkg.orientation = self.rotate_90(pkg.orientation, axis)

        return neighbor
            
    # buat HC steppest.sideway etc yang ngambil semua sample neighbor 
    def get_all_neighbors(self, state: TruckState) -> list[TruckState]:
        all_neighbors: list[TruckState] = []
        selected_neighbors: list[TruckState] = []
        n_pkgs = len(state.packages)
        if n_pkgs == 0:
            return all_neighbors

        truck_dims = state.truck.dimensions
        w_max = max(0, truck_dims.get("w", 10) - 1)
        l_max = max(0, truck_dims.get("l", 10) - 1)
        h_max = max(0, truck_dims.get("h", 10) - 1)
        for i in range(n_pkgs):
            for j in range(i + 1, n_pkgs):
                nbr = copy.deepcopy(state)
                p1 = nbr.packages[i]
                p2 = nbr.packages[j]
                p1.coordinates, p2.coordinates = copy.deepcopy(p2.coordinates), copy.deepcopy(p1.coordinates)
                p1.orientation, p2.orientation = copy.deepcopy(p2.orientation), copy.deepcopy(p1.orientation)
                all_neighbors.append(nbr)
        for i in range(n_pkgs):
            for axis in ["x", "y", "z"]:
                nbr = copy.deepcopy(state)
                nbr.packages[i].orientation = self.rotate_90(nbr.packages[i].orientation, axis)
                all_neighbors.append(nbr)
        step = max(1, self.step_size)
        space_matrix = state.getSpaceMatrix()


        
        for i in range(n_pkgs):
            pkg = state.packages[i]
            if pkg.isInTruck(state.truck.dimensions):
                for x_start in range(0, w_max - pkg.package.dimensions[pkg.orientation['x']]) :
                    for y_start in range(0, l_max - pkg.package.dimensions[pkg.orientation['y']]) :
                        for z_start in range(0, h_max - pkg.package.dimensions[pkg.orientation['z']]) :
                            if z_start == 0 or (not(space_matrix[x_start][y_start][z_start]) and space_matrix[x_start][y_start][z_start - 1] == 1) :
                                nbr = copy.deepcopy(state)
                                nbr.packages[i].coordinates = {"x": x_start, "y": y_start, "z": z_start}
                                all_neighbors.append(nbr)
                        
                
                nbr = copy.deepcopy(state)
                nbr.packages[i].coordinates = {"x": -1, "y": -1, "z": -1}
                all_neighbors.append(nbr)

            else:
                for x_start in range(0, w_max - pkg.package.dimensions[pkg.orientation['x']]) :
                    for y_start in range(0, l_max - pkg.package.dimensions[pkg.orientation['y']]) :
                        for z_start in range(0, h_max - pkg.package.dimensions[pkg.orientation['z']]) :
                            if z_start == 0 or (not(space_matrix[x_start][y_start][z_start]) and space_matrix[x_start][y_start][z_start - 1] == 1) :
                                nbr = copy.deepcopy(state)
                                nbr.packages[i].coordinates = {"x": x_start, "y": y_start, "z": z_start}
                                all_neighbors.append(nbr)
                                # for axis in ["x", "y", "z"]:
                                #     nbr2 = copy.deepcopy(nbr)
                                #     nbr2.packages[i].orientation = self.rotate_90(nbr2.packages[i].orientation, axis)
                                #     all_neighbors.append(nbr2)
                                # for dx, dy, dz in shifts:
                                #     new_x = max(0, min(w_max, dx))
                                #     new_y = max(0, min(l_max, dy))
                                #     new_z = max(0, min(h_max, dz))

                                #     if (new_x, new_y, new_z) != (pkg.coordinates["x"], pkg.coordinates["y"], pkg.coordinates["z"]):
                                #         nbr = copy.deepcopy(state)
                                #         nbr.packages[i].coordinates = {"x": new_x, "y": new_y, "z": new_z}
                                #         all_neighbors.append(nbr)
            
                

        

        return all_neighbors

    def should_accept(self, current_cost: float, neighbor_cost: float) -> bool:

        raise NotImplementedError(
            "HillClimbing adalah template class tanpa heuristik bawaan. "
            "Heuristik penerimaan harus diimplementasikan oleh kelas turunannya "
            "(misalnya SimpleHillClimbing, StochasticHillClimbing, atau SimulatedAnnealing)."
        )

    def optimize(self) -> TruckState:
        start_time = time.time()
        current_cost = objectiveFunction(self.current_state)
        best_cost = current_cost
        
        self.history = [{
            "iteration": 0,
            "current_cost": current_cost,
            "best_cost": best_cost,
            "accepted": True
        }]
        self.accepted_moves = 0
        self.total_iterations = 0

        for i in range(1, self.max_iterations + 1):
            self.total_iterations = i
            neighbor = self.get_neighbor(self.current_state)
            neighbor_cost = objectiveFunction(neighbor)

            accepted = self.should_accept(current_cost, neighbor_cost)
            if accepted:
                self.current_state = neighbor
                current_cost = neighbor_cost
                self.accepted_moves += 1

                if current_cost > best_cost:
                    self.best_state = copy.deepcopy(self.current_state)
                    best_cost = current_cost

            self.history.append({
                "iteration": i,
                "current_cost": current_cost,
                "best_cost": best_cost,
                "accepted": accepted
            })

        self.execution_time = time.time() - start_time
        return self.best_state