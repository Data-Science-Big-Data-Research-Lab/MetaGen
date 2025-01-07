"""
    Copyright (C) 2023 David Gutierrez Avilés and Manuel Jesús Jiménez Navarro

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from metagen.framework import Domain, Solution
from metagen.metaheuristics import GA, GAConnector

# P1 fitness function
def p1_fitness(solution: Solution) -> float:
    x = solution["x"]  # You could use the .get function alternatively.
    return sum(x)

p1_domain: Domain = Domain(connector=GAConnector())
p1_domain.define_static_structure("x", 5)
p1_domain.set_structure_to_integer("x", 0, 10)

ga_search: GA = GA(p1_domain, p1_fitness, max_generations=100, population_size=50, mutation_rate=0.1)
p1_solution: Solution = ga_search.run()

# P1 result
print(p1_solution)