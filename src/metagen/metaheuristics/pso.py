from copy import deepcopy
from random import random
from typing import List, cast

import numpy as np

from metagen.framework import Domain, Solution
from metagen.framework.domain import (Base, BaseDefinition,
                                      CategoricalDefinition)
from metagen.framework.domain.literals import (Attributes, C, CatAttr, CatVal,
                                               I, R)


def solution_to_vector(solution: Solution) -> List[float]:
    vector: List[float] = []
    for k, v in solution.get_variables().items():
        definition: Base = solution.get_definition().get(k)
        if definition.get_type() is C:
            categories = cast(CatAttr, definition.get_attributes())[1]
            vector.append(categories.index(v))  # type: ignore
        elif definition.get_type() in (I, R):
            vector.append(cast(float, v))
    return vector


class Particle:
    def __init__(self, solution: Solution):
        self.definition: BaseDefinition = solution.get_definition()
        self.x: List[float] = solution_to_vector(solution)  # particle position
        # TODO: podríamos hacer un get_number_of_variables
        self.v: List[float] = [0.0] * len(solution.get_variables().keys())  # particle velocity
        self.best_x: List[float] = deepcopy(self.x)  # best position individual
        self.best_fitness: float = -1  # best error individual
        self.current_fitness: float = -1  # error individual

    def update_v(self, gbest: List[float], w: float, c1: float, c2: float):
        for i in range(len(self.x)):
            r1: float = random()
            r2: float = random()
            cognitive_velocity = c1 * r1 * (self.best_x[i] - self.x[i])
            social_velocity = c2 * r2 * (gbest[i] - self.x[i])
            self.v[i] = w * self.v[i] + cognitive_velocity + social_velocity


    def update_x(self):
        for i in range(len(self.x)):
            self.x[i] = self.__check_bounds(i, self.x[i] + self.v[i])

    def __check_bounds(self, i: int, x: float) -> float:
        res: float = x
        attr: Attributes = self.definition.get_by_index(i).get_attributes()
        max_val: float = 0
        if attr[0] is C:
            max_val = len(cast(CatAttr, attr)[1])
        if res < 0:
            res = max_val + 1 + res
        elif res > 0:
            res = res % max_val

        return res

    # def update_position(self):
    #     for i in range(len(self.solution.features)):
    #         self.solution.features[i] = max(self.bounds[i][0],
    #                                     min(self.bounds[i][1], self.solution.features[i] + self.velocity[i]))
    #      if self.solution.fitness < self.best_solution.fitness:
    #       self.best_solution = self.solution.copy()
    #
    #
    # def evaluate(self, costFunc):
    #     self.err_i = costFunc(self.position_i)
    #
    #     if self.err_i < self.err_best_i or self.err_best_i == -1:
    #         self.pos_best_i = self.position_i
    #         self.err_best_i = self.err_i
    #
    # def update_position(self, bounds):
    #     for i in range(0, len(self.position_i)):
    #         self.position_i[i] = self.position_i[i] + self.velocity_i[i]
    #
    #         # adjust maximum position if necessary
    #         if self.position_i[i] > bounds[i][1]:
    #             self.position_i[i] = bounds[i][1]
    #
    #         # adjust minimum position if neseccary
    #         if self.position_i[i] < bounds[i][0]:
    #             self.position_i[i] = bounds[i][0]

# test_dom: Domain = Domain()
# test_dom.define_real("r", 0.0, 1.0)
# test_dom.define_integer("i", 100, 200)
# test_dom.define_categorical("c", ["a", "b", "c"])
#
# sol: Solution = Solution(test_dom.get_core())
# sol.set("r", 0.005)
# sol.set("i", 120)
# sol.set("c", "c")
#
# l = solution_to_vector(sol)
#
# print("VECTOR:" + str(l))

#
# class PSO:
#     def __init__(self, costFunc, bounds, num_particles, maxiter, num_threads):
#         self.err_best_g = -1
#         self.pos_best_g = []
#         self.num_threads = num_threads
#         self.num_particles = num_particles
#         self.maxiter = maxiter
#         self.costFunc = costFunc
#         self.bounds = bounds
#         self.swarm = []
#
#         # create the swarm of particles
#         for i in range(0, self.num_particles):
#             self.swarm.append(Particle(bounds=self.bounds, x0=0))
#
#     def update_particle_position(self, particle):
#         particle.update_position(self.bounds)
#         particle.evaluate(self.costFunc)
#
#         # update global best position
#         if particle.err_i < self.err_best_g or self.err_best_g == -1:
#             self.pos_best_g = list(particle.position_i)
#             self.err_best_g = float(particle.err_i)
#
#     def optimize(self):
#         for i in range(self.maxiter):
#             # create threads for each particle
#             threads = []
#             for particle in self.swarm:
#                 t = threading.Thread(target=self.update_particle_position, args=(particle,))
#                 threads.append(t)
#
#             # start threads
#             for t in threads:
#                 t.start()
#
#             # wait for all threads to finish
#             for t in threads:
#                 t.join()
#
#             # update velocities after all positions have been updated
#             for particle in self.swarm:
#                 # update velocity
#                 for i in range(len(particle.velocity_i)):
#                     r1 = np.random.random()
#                     r2 = np.random.random()
#
#                     vel_cognitive = self.c1 * r1 * (particle.pos_best_i[i] - particle.position_i[i])
#                     vel_social = self.c2 * r2 * (self.pos_best_g[i] - particle.position_i[i])
#                     particle.velocity_i[i] = self.w * particle.velocity_i[i] + vel_cognitive + vel_social
#
#                 # update position and evaluate
#                 particle.update_position(self.bounds)
#                 particle.evaluate(self.costFunc)
#
#                 # update personal best
#                 if particle.err_i < particle.err_best_i or particle.err_best_i == -1:
#                     particle.pos_best_i = list(particle.position_i)
#                     particle.err_best_i = float(particle.err_i)
#
#                 # update global best position
#                 if particle.err_i < self.err_best_g or self.err_best_g == -1:
#                     self.pos_best_g = list(particle.position_i)
#                     self.err_best_g = float(particle.err_i)
#
#         # return best position and value
#         return self.pos_best_g, self.err_best_g
