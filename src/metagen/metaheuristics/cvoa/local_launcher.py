from concurrent.futures.thread import ThreadPoolExecutor
from datetime import timedelta
from time import time
from typing import Callable, List, Optional

from metagen.framework import Domain, Solution
from metagen.framework.rng import own_generators, set_seed, spawn_seed
from metagen.logging.metagen_logger import metagen_logger

from metagen.metaheuristics._parameters import require_integer, require_number
from metagen.metaheuristics.cvoa.common_tools import BudgetedFitness, StrainProperties
from metagen.metaheuristics.cvoa.cvoa import CVOA
from metagen.metaheuristics.cvoa.local_state import LocalPandemicState
from metagen.metaheuristics.tools import solution_class


def run_strain(global_state: LocalPandemicState, domain: Domain, fitness_function: Callable[[Solution], float],
               strain_properties: StrainProperties, update_isolated: bool = False, log_dir: Optional[str] = None,
               strain_class: type[CVOA] = CVOA, seed: Optional[int] = None) -> Solution:
    if seed is None:
        return strain_class(global_state, domain, fitness_function, strain_properties, update_isolated, log_dir).run()
    with own_generators(seed):
        return strain_class(global_state, domain, fitness_function, strain_properties, update_isolated, log_dir).run()



def cvoa_launcher(strains: List[StrainProperties], domain: Domain, fitness_function: Callable[[Solution], float],
                  update_isolated: bool = False, log_dir: Optional[str] = None,
                  seed: Optional[int] = None, strain_class: type[CVOA] = CVOA,
                  max_evaluations: Optional[int] = None, timeout: Optional[float] = None) -> Solution:
    """
    Run a CVOA pandemic over the given strains, one thread per strain, and return the best solution.

    :param strains: The strains taking part in the pandemic.
    :type strains: List[StrainProperties]
    :param domain: The problem domain.
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions.
    :type fitness_function: Callable[[Solution], float]
    :param update_isolated: Kept for compatibility and ignored: every isolated
        individual is recorded.
    :type update_isolated: bool, optional
    :param log_dir: Directory the TensorBoard logs are written to. None, the default, writes nothing.
    :type log_dir: str or None, optional
    :param seed: Seed making the pandemic reproducible (default is None). With several
        strains each draws from its own generators, seeded from this one; the order in
        which they reach the shared state still depends on timing.
    :type seed: Optional[int], optional
    :param strain_class: The class every strain is built from (default is CVOA). A subclass of CVOA changes what a strain does; the launcher does not.
    :type strain_class: type[CVOA], optional
    :param max_evaluations: The most evaluations of the fitness function the whole pandemic
        may make, shared by every strain; None, the default, sets no limit. See
        :py:class:`~metagen.metaheuristics.StrainProperties` for what a pandemic costs.
    :type max_evaluations: int or None, optional
    :param timeout: The most seconds the pandemic may evaluate for; None, the default, sets
        no limit.
    :type timeout: float or None, optional
    :return: The best solution found across every strain.
    :rtype: Solution
    :raises ValueError: If ``max_evaluations`` is not a positive integer or ``timeout`` a
        positive number.

    Once the budget is spent, nothing more is evaluated: the iteration in course ends
    without calling the fitness function, and every strain stops after it.
    """
    require_integer("max_evaluations", max_evaluations, 1, optional=True)
    require_number("timeout", timeout, above=0, optional=True)
    if seed is not None:
        set_seed(seed)

    # Initialize the global state
    solution_type = solution_class(domain)
    global_state = LocalPandemicState(solution_type(domain, connector=domain.get_connector()), max_evaluations,
                                      timeout)
    if global_state.budget.limited():
        fitness_function = BudgetedFitness(fitness_function, global_state)

    # One strain has nobody to share the generators with and stays on the process's, so
    # what a seed gives a single strain does not change. Several sharing them made the
    # fitness of a seed differ between repeated runs in 29 of 32 cases of three strains.
    several = len(strains) > 1

    t1 = time()
    with ThreadPoolExecutor(max_workers=len(strains)) as executor:
        futures = {strain.strain_id: executor.submit(run_strain, global_state, domain, fitness_function, strain, update_isolated, log_dir,
                                                      strain_class, spawn_seed() if several else None)
                   for strain in strains}
    t2 = time()

    best_solution = global_state.get_best_individual()

    output = (
            "\n********** Results by strain **********\n"
            + "\n".join(f"[{strain_id}] Best individual: {future.result()}" for strain_id, future in futures.items())
            + "\n\n********** Best result **********\n"
            + f"Best individual: {best_solution}\n"
            + "\n********** Pandemic report **********\n"
            + f"Pandemic report: {global_state.get_pandemic_report()}\n"
            + "\n********** Performance **********\n"
            + f"Execution time: {timedelta(seconds=t2 - t1)}\n"
    )

    metagen_logger.info(output)


    return best_solution