"""
TabuSearch: the algorithm HillClimbing was named after and is not (A-02). Each
test pins one of the three things that make it a tabu search: it moves to a worse
neighbor when nothing improves, the tabu list keeps it from walking straight back,
and the aspiration criterion lets a tabu neighbor through when it beats the best
solution ever found. The walk is driven by hand, one iteration at a time, from a
chosen starting point, because the properties are about single moves.
"""
import pytest

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed
from metagen.metaheuristics import TabuSearch


def _domain():
    domain = Domain()
    domain.define_integer("x", 0, 10)
    return domain


def _fitness(solution):
    # A single optimum at 5 on a flat plateau: from 5, every move is a worsening one.
    return 0.0 if solution["x"] == 5 else 1.0


def _standing_at(x, seed=0, **kwargs):
    """A search started, warmed up and initialized, then placed at x by hand."""
    set_seed(seed)
    domain = _domain()
    search = TabuSearch(domain, _fitness, population_size=10, warmup_iterations=0, max_iterations=5, seed=seed,
                        **kwargs)
    search.pre_execution()
    search._warmup()
    search._initialize()
    search.current_iteration = 0
    standing = Solution(domain)
    standing.set("x", x)
    standing.evaluate(_fitness)
    search.current_solution = standing
    search.best_solution = standing
    return search


def _step(search):
    search.pre_iteration()
    search._iterate()
    search.post_iteration()
    search.current_iteration += 1


def test_it_moves_to_a_worse_neighbor_when_nothing_improves():
    """From the optimum every neighbor is worse, and a tabu search moves anyway;
    the best solution found stays at the optimum."""
    search = _standing_at(5)
    _step(search)
    assert search.current_solution["x"] != 5
    assert search.current_solution.get_fitness() == 1.0
    assert search.best_solution["x"] == 5


def test_the_tabu_list_keeps_it_from_walking_back():
    """Once it has left the optimum, the optimum is tabu and no better than the best
    found, so the walk cannot return to it while the list remembers it."""
    search = _standing_at(5, tabu_size=10)
    for _ in range(5):
        _step(search)
        assert search.current_solution["x"] != 5, "the walk returned to a tabu solution"
    assert any(visited["x"] == 5 for visited in search.tabu_list)
    assert search.best_solution["x"] == 5


def test_a_tabu_neighbor_is_taken_when_it_beats_the_best_found():
    """Aspiration: the optimum is tabu, but the best found so far is worse than it,
    so the walk takes it as soon as a neighbor lands there."""
    search = _standing_at(6, seed=1)
    forbidden = Solution(search.domain)
    forbidden.set("x", 5)
    forbidden.evaluate(_fitness)
    search.tabu_list.append(forbidden)
    assert search.is_tabu(forbidden)

    for _ in range(5):
        _step(search)
        if search.current_solution["x"] == 5:
            break
    assert search.current_solution["x"] == 5
    assert search.best_solution["x"] == 5


def test_the_tabu_radius_covers_a_neighborhood_on_a_real_variable():
    """On a real variable two solutions never coincide, so a tabu solution forbids
    everything within the radius, a fiftieth of the range by default."""
    domain = Domain()
    domain.define_real("x", 0.0, 100.0)
    search = TabuSearch(domain, lambda s: s["x"], seed=0)
    visited = Solution(domain)
    visited.set("x", 50.0)
    search.tabu_list.append(visited)

    close, far = Solution(domain), Solution(domain)
    close.set("x", 51.5)
    far.set("x", 53.0)
    assert search.is_tabu(close)
    assert not search.is_tabu(far)


def test_a_seed_reproduces_a_run():
    domain = Domain()
    domain.define_real("x", -5.0, 5.0)
    domain.define_real("y", -5.0, 5.0)
    sphere = lambda s: s["x"] ** 2 + s["y"] ** 2  # noqa: E731
    runs = [TabuSearch(domain, sphere, population_size=6, warmup_iterations=1, max_iterations=5, seed=3).run()
            for _ in range(2)]
    assert runs[0].get_fitness() == runs[1].get_fitness()
    assert runs[0].get_fitness() == pytest.approx(min(runs[0].get_fitness(), runs[1].get_fitness()))
