from .hill_climbing import HillClimbing, TruckState
from data_struct import objectiveFunction, TruckState
import math
import time
import copy


class SidewaysHillClimbing(HillClimbing):
    def __init__(self, initial_state: TruckState, max_sideways_moves: int = 100):
        super().__init__(initial_state)
        self.max_sideways_moves = max_sideways_moves

    def search(self):
        current_state = self.initial_state
        current_value = objectiveFunction(current_state)
        sideways_moves = 0

        while True:
            neighbors = self.get_neighbors(current_state)
            best_neighbor = None
            best_value = current_value

            for neighbor in neighbors:
                neighbor_value = objectiveFunction(neighbor)
                if neighbor_value < best_value:
                    best_neighbor = neighbor
                    best_value = neighbor_value

            if best_neighbor is None:
                # No better neighbor found
                break

            if best_value == current_value:
                # Sideways move
                sideways_moves += 1
                if sideways_moves > self.max_sideways_moves:
                    break
            else:
                sideways_moves = 0 

            current_state = best_neighbor
            current_value = best_value

        return current_state, current_value