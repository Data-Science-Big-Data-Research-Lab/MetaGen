"""The state a CVOA pandemic shares, in threads and on Ray, and the copy of a metaheuristic a
distributed iteration sends to its workers: what each sees, and what reaches the shared
state and when."""
import pytest

from metagen.framework import Domain, Solution
from metagen.metaheuristics import RandomSearch
from metagen.metaheuristics.cvoa.local_state import LocalPandemicState


def _domain():
    domain = Domain()
    domain.define_integer("x", 0, 9)
    return domain


def _solution(domain, value, fitness=None):
    solution = Solution(domain)
    solution.set("x", value)
    if fitness is not None:
        solution.set_fitness(fitness)
    return solution


def test_the_best_of_a_pandemic_is_only_replaced_by_a_better_one():
    # Two strains may each read the best and offer theirs; the second, worse, one must not
    # take the place of the first.
    domain = _domain()
    state = LocalPandemicState(_solution(domain, 0))
    state.update_best_individual(_solution(domain, 1, 1.0))
    state.update_best_individual(_solution(domain, 2, 3.0))
    assert state.get_best_individual()["x"] == 1


def test_the_copy_a_distributed_iteration_sends_leaves_out_what_the_workers_do_not_read():
    domain = Domain()
    domain.define_real("x", -1.0, 1.0)
    search = RandomSearch(domain, lambda solution: solution["x"] ** 2, population_size=4, max_iterations=3, seed=0)
    search.run()
    worker = search._worker_copy()
    assert worker.history == [] and worker.best_solution_fitnesses == [] and worker.current_solutions == []
    assert worker.logger is None
    # The original keeps them, and shares the rest with the copy.
    assert len(search.history) == 3 and len(search.current_solutions) == 4
    assert worker.fitness_function is search.fitness_function and worker.domain is search.domain
    assert worker.best_solution is search.best_solution


@pytest.fixture(scope="module")
def ray_runtime():
    ray = pytest.importorskip("ray")
    started_here = not ray.is_initialized()
    if started_here:
        ray.init(num_cpus=2, include_dashboard=False, log_to_driver=False)
    yield ray
    if started_here:
        ray.shutdown()


def test_a_task_sees_the_state_of_the_iteration_with_its_own_changes(ray_runtime):
    from metagen.metaheuristics.cvoa.ray_tools import _IterationView

    domain = _domain()
    one, two, three = (_solution(domain, value) for value in (1, 2, 3))
    view = _IterationView({one._key()}, {three._key()}, actor=None)  # type: ignore[arg-type]
    assert view.get_individual_state(one).recovered and view.get_individual_state(three).dead
    view.get_infected_again(one)
    view.recover_if_not_dead(two)
    view.recover_if_not_dead(three)
    view.isolate(two)
    assert not view.get_individual_state(one).recovered
    assert view.get_individual_state(two).recovered and view.get_individual_state(two).isolated
    assert not view.get_individual_state(three).recovered
    assert view.log == [("discard", one._key()), ("recover", two._key()), ("recover", three._key()),
                        ("isolate", two._key())]


def test_a_strain_on_ray_sends_its_writes_before_it_reads_and_keeps_the_best(ray_runtime):
    from typing import Any, cast

    from metagen.metaheuristics.cvoa.ray_tools import RemotePandemicState, RemotePandemicStateProxy

    domain = _domain()
    handle = cast(Any, RemotePandemicState).remote(_solution(domain, 0))
    proxy = RemotePandemicStateProxy(handle)
    one, two = _solution(domain, 1, 1.0), _solution(domain, 2, 2.0)
    proxy.recover_if_not_dead(one)
    proxy.isolate(two)
    assert proxy._pending
    assert proxy.get_individual_state(one).recovered
    assert proxy.get_pandemic_report()["isolated"] == 1
    proxy.update_deaths([one])
    proxy.update_recovered_with_deaths()
    assert not proxy.get_individual_state(one).recovered and proxy.get_individual_state(one).dead
    # Dead already sent are not sent again.
    proxy.update_deaths([one, two])
    assert proxy._deaths_sent == {one._key(), two._key()}
    # The best is replaced only by a better one, also when a strain offers a worse one.
    proxy.update_best_individual(one)
    other = RemotePandemicStateProxy(handle)
    other.update_best_individual(two)
    assert other.get_best_individual()["x"] == 1 and proxy.get_best_individual()["x"] == 1
    # What a strain writes last reaches the actor when it flushes.
    three = _solution(domain, 3)
    proxy.recover_if_not_dead(three)
    proxy.flush()
    assert ray_runtime.get(handle.get_individual_state.remote(three)).recovered
