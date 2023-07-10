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
