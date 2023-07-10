from metagen.framework import Domain, Solution
from metagen.metaheuristics import RandomSearch

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
