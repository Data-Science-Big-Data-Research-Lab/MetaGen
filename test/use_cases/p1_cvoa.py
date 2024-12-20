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
from metagen.metaheuristics import CVOA, cvoa_launcher
import time
# P1 fitness function
def p1_fitness(solution: Solution) -> float:
    x = solution["x"]  # You could use the .get function alternatively.
    return sum(x)


if __name__ == "__main__":
    p1_domain: Domain = Domain()
    p1_domain.define_static_structure("x", 5)
    p1_domain.set_structure_to_integer("x", 0, 10)

    strain1 = CVOA(p1_domain, p1_fitness, "Strain1", pandemic_duration=5)

    strains = [strain1]

    start_time = time.time()
    p1_solution = cvoa_launcher(strains)
    end_time = time.time()
    execution_time = end_time - start_time
    
    """start_time = time.time()

    p1_solution = strain1.run()
    end_time = time.time()
    execution_time = end_time - start_time"""
    # P1 result
    print(p1_solution)

    print("\n********** Results **********")
    print(f"Best solution: {p1_solution}")
    print(f"Total execution time: {execution_time}")