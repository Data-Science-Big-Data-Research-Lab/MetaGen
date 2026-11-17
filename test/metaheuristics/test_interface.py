"""What a metaheuristic of one's own has to write, and what the base class gives it."""
from copy import deepcopy
from typing import List, Tuple

from metagen.framework import Domain, Solution
from metagen.metaheuristics import Metaheuristic


class _Mutating(Metaheuristic):
    """Only iterate and stopping_criterion: the first population is the default one."""

    def __init__(self, domain, fitness_function, **options):
        super().__init__(domain, fitness_function, **options)
        self.max_iterations = self._iterations(None, 4)

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        moved = []
        for solution in solutions:
            neighbor = deepcopy(solution)
            neighbor.mutate()
            neighbor.evaluate(self.fitness_function)
            moved.append(neighbor)
        return moved, min(moved, key=Solution.get_fitness)

    def stopping_criterion(self) -> bool:
        return self._iterations_done()


def _domain() -> Domain:
    domain = Domain()
    domain.define_real("x", -5.0, 5.0)
    domain.define_integer("n", 0, 10)
    return domain


def test_a_metaheuristic_without_initialize_starts_from_random_solutions_of_the_domain():
    evaluated = []

    def fitness(solution):
        evaluated.append(solution)
        return solution["x"] ** 2 + solution["n"]

    algorithm = _Mutating(_domain(), fitness, population_size=6, seed=0)
    best = algorithm.run()
    # The first population: six solutions drawn at random and evaluated, then four iterations
    assert len(evaluated) == 6 * 5 and len({(s["x"], s["n"]) for s in evaluated[:6]}) == 6
    assert best.get_fitness() == min(fitness_value for fitness_value in algorithm.best_solution_fitnesses)
    again = _Mutating(_domain(), lambda s: s["x"] ** 2 + s["n"], population_size=6, seed=0).run()
    assert again == best
