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
from metagen.metaheuristics import RandomSearch

import shutil

#shutil.rmtree("./logs/random_search")
# P1 legacy_domain
p1_domain: Domain = Domain()
p1_domain.define_integer("x", -10, 10)


# P1 fitness function
def p1_fitness(solution: Solution) -> float:
    x = solution["x"]  # You could use the .get function alternatively.
    return x + 5


# P1 resolution
random_search: RandomSearch = RandomSearch(p1_domain, p1_fitness)
p1_solution: Solution = random_search.run()

# P1 result
print(p1_solution)