"""One search of TriGen: the selection by groups, one generation, the record of every
tricluster evaluated, and the run as a whole."""
import math
from collections import Counter

import pytest

from metagen.framework.rng import set_seed
from metagen.metaheuristics import TriclusterFitness
from metagen.metaheuristics.trigen.population import DataHierarchy
from metagen.metaheuristics.trigen.trigen_ga import TriGenGA, select_by_groups
from metagen.triclustering import Tricluster, plant

CUBE, PLANTED = plant((60, 6, 8), [(12, 3, 5)], noise=0.05, seed=0)
SIZES = ((4, 15), (2, 4), (3, 6))


def _search(**arguments):
    settings = {"population_size": 20, "generations": 10, "seed": 3, **arguments}
    fitness = settings.pop("fitness", TriclusterFitness(CUBE))
    return TriGenGA(fitness, SIZES, settings.pop("hierarchy", DataHierarchy(CUBE.shape)),
                    settings.pop("first", True), **settings)


def _tricluster(solution):
    return Tricluster(solution["genes"], solution["conditions"], solution["times"])


def _population(size, seed=0):
    search = _search(population_size=size, seed=seed)
    set_seed(seed)
    population, _ = search.initialize(size)
    return population


# --- the selection ----------------------------------------------------------------

@pytest.mark.parametrize("seed", range(30))
def test_the_best_is_always_selected_and_there_are_at_least_as_many_as_asked(seed):
    population = _population(12, seed)
    set_seed(seed)
    selected = select_by_groups(population, 5)
    assert min(population, key=lambda s: s.get_fitness()) in selected
    assert 5 <= len(selected) <= 5 and len({id(s) for s in selected}) == len(selected)


def test_with_fewer_to_select_than_groups_one_per_group_is_selected():
    population = _population(12)
    counts = Counter()
    for seed in range(200):
        set_seed(seed)
        counts[len(select_by_groups(population, 2))] += 1
    assert set(counts) <= {2, 3} and counts[3] > counts[2]


def test_two_or_fewer_individuals_make_two_groups():
    population = _population(4)[:2]
    for seed in range(50):
        set_seed(seed)
        assert len(select_by_groups(population, 2)) == 2


def test_the_selection_leans_to_the_best_without_being_a_cut():
    population = sorted(_population(10), key=lambda s: s.get_fitness())
    picked = Counter()
    for seed in range(2000):
        set_seed(seed)
        for individual in select_by_groups(population, 5):
            picked[population.index(individual)] += 1
    assert picked[0] == 2000
    assert picked[1] > picked[5] > picked[9] > 0


# --- one generation ---------------------------------------------------------------

def test_a_generation_keeps_the_size_passes_the_selected_untouched_and_evaluates_every_child():
    search = _search()
    set_seed(4)
    population, _ = search.initialize(20)
    evaluations = []
    fitness = search.fitness_function
    search.fitness_function = lambda solution: evaluations.append(1) or fitness(solution)
    before = {id(individual): (_tricluster(individual), individual.get_fitness()) for individual in population}
    next_population, best = search.iterate(population)
    assert len(next_population) == 20
    kept = [individual for individual in next_population if id(individual) in before]
    assert len(kept) == search.selection_count or len(kept) == 3
    assert all((_tricluster(i), i.get_fitness()) == before[id(i)] for i in kept)
    assert len(evaluations) == 20 - len(kept)
    for individual in next_population:
        tricluster = _tricluster(individual)
        assert individual.get_fitness() == search.tricluster_fitness.evaluate(tricluster)
        for positions, (smallest, largest) in zip((tricluster.genes, tricluster.conditions, tricluster.times), SIZES):
            assert smallest <= len(positions) <= largest
    assert best.get_fitness() == min(individual.get_fitness() for individual in next_population)


def test_with_an_odd_number_to_breed_the_last_pair_gives_one_child():
    search = _search(population_size=11, selection_rate=0.3)        # 3 selected and 8 bred, or 4 and 7
    set_seed(5)
    population, _ = search.initialize(11)
    next_population, _ = search.iterate(population)
    assert len(next_population) == 11


# --- the run ----------------------------------------------------------------------

def test_a_run_lasts_its_generations_and_never_gets_worse():
    search = _search(generations=7)
    search.run()
    history = search.best_solution_fitnesses
    assert len(history) == 7
    assert all(later <= earlier for earlier, later in zip(history, history[1:]))


def test_every_tricluster_evaluated_is_recorded_with_its_fitness():
    search = _search()
    seen = []
    fitness = search.tricluster_fitness

    def recording(solution):
        seen.append(_tricluster(solution))
        return fitness(solution)

    search.fitness_function = recording
    search.run()
    assert set(search.evaluated) == set(seen)
    for tricluster, value in search.evaluated.items():
        assert value == fitness.evaluate(tricluster)
    best = search.best_solution
    assert search.evaluated[_tricluster(best)] == best.get_fitness() == min(search.evaluated.values())


def test_the_search_improves_on_where_it_starts():
    improved = 0
    for seed in range(5):
        search = _search(population_size=30, generations=20, seed=seed)
        search.run()
        improved += search.best_solution_fitnesses[-1] < search.best_solution_fitnesses[0]
    assert improved == 5


def test_the_same_seed_gives_the_same_search():
    def run():
        search = _search(seed=9)
        best = search.run()
        return _tricluster(best), search.best_solution_fitnesses, dict(search.evaluated)
    assert run() == run()


def test_a_later_search_starts_from_the_least_explored_coordinates():
    hierarchy = DataHierarchy(CUBE.shape)
    hierarchy.update(Tricluster(range(50), range(4), range(6)))
    search = _search(hierarchy=hierarchy, first=False, random_fraction=0.0)
    set_seed(10)
    population, _ = search.initialize(20)
    for individual in population:
        assert set(individual["genes"]) <= set(range(50, 60)) or len(individual["genes"]) > 10


def test_a_search_resumes_exactly(tmp_path):
    whole = _search(seed=11)
    reference = _tricluster(whole.run()), list(whole.best_solution_fitnesses), dict(whole.evaluated)
    path = str(tmp_path / "search.ckpt")
    search = _search(seed=11, checkpoint=path)
    fitness = search.tricluster_fitness

    def stops_after_three_generations(solution):
        if search.current_iteration >= 3:
            search.request_stop()
        return fitness(solution)

    search.fitness_function = stops_after_three_generations
    search.run()
    resumed = TriGenGA.resume(path, fitness)
    best = resumed.run()
    assert (_tricluster(best), resumed.best_solution_fitnesses, dict(resumed.evaluated)) == reference


@pytest.mark.parametrize("arguments, message", [
    ({"population_size": 3}, "at least 4"),
    ({"generations": 0}, "generation"),
    ({"random_fraction": 1.5}, "random_fraction"),
    ({"mutation_probability": -0.1}, "mutation_probability"),
    ({"selection_rate": 0.05}, "at least 2"),
    ({"selection_rate": 1.0}, "leave at least 1"),
])
def test_parameters_out_of_range_are_rejected(arguments, message):
    with pytest.raises(ValueError, match=message):
        _search(**arguments)


@pytest.mark.parametrize("probability", [0.0, 0.3, 1.0])
def test_each_child_mutates_with_the_probability_given_by_one_step(monkeypatch, probability):
    from metagen.metaheuristics.genetic.genetic_tools import GASolution
    calls = []
    original = GASolution.mutate

    def counting(self, alterations_number=None, alteration_limit=None):
        calls.append((alterations_number, alteration_limit))
        return original(self, alterations_number, alteration_limit)

    search = _search(population_size=40, mutation_probability=probability)
    set_seed(12)
    population, _ = search.initialize(40)
    monkeypatch.setattr(GASolution, "mutate", counting)
    children = 0
    for _ in range(20):
        before = {id(individual) for individual in population}
        population, _ = search.iterate(population)
        children += sum(id(individual) not in before for individual in population)
    assert all(call == (1, 1) for call in calls)
    if probability in (0.0, 1.0):
        assert len(calls) == probability * children
    else:
        assert abs(len(calls) / children - probability) < 0.06


def test_every_pair_of_parents_is_two_different_individuals(monkeypatch):
    from metagen.metaheuristics.genetic.genetic_tools import GASolution
    pairs = []
    original = GASolution.crossover

    def recording(self, other):
        pairs.append((id(self), id(other)))
        return original(self, other)

    monkeypatch.setattr(GASolution, "crossover", recording)
    _search(generations=5).run()
    assert pairs and all(first != second for first, second in pairs)


def test_a_second_run_starts_a_new_record_of_what_it_evaluated():
    search = _search(generations=3)
    search.run()
    first = dict(search.evaluated)
    search.tricluster_fitness.found.append(min(first, key=first.__getitem__))
    search.run()
    assert all(value == search.tricluster_fitness.evaluate(tricluster)
               for tricluster, value in search.evaluated.items())
