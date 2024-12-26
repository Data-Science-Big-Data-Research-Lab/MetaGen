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

# P2 legacy_domain
p2_domain = Domain()
p2_domain.define_real("x", 0.0, 1.0)


# P2 fitness function
def p2_fitness(solution: Solution):
    x = solution["x"]  # You could use the .get function alternatively.
    return pow(x, 2)


# P2 resolution
p2_solution: Solution = RandomSearch(p2_domain, p2_fitness).run()

# P2 result
print(p2_solution)
