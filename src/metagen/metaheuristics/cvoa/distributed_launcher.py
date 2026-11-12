from datetime import timedelta
from time import time
from typing import Any, Callable, List, Optional, cast

from metagen.metaheuristics.import_helper import ray_missing, start_ray

# Imported, not asked about: the documentation is built with Ray mocked, which is found
# without a file, and is_package_installed answered no, so autodoc could not import the
# launcher. Whether the package exports it is still decided in cvoa/__init__.py.
try:
    import ray
except ImportError as error:
    raise ImportError(ray_missing("the distributed CVOA")) from error

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed, spawn_seed
from metagen.logging.metagen_logger import metagen_logger
from metagen.metaheuristics._parameters import require_integer, require_number
from metagen.metaheuristics.cvoa.common_tools import BudgetedFitness, StrainProperties
from metagen.metaheuristics.cvoa.cvoa import CVOA
from metagen.metaheuristics.cvoa.ray_tools import PandemicStateHandle, RemotePandemicState, RemotePandemicStateProxy
from metagen.metaheuristics.tools import solution_class


@ray.remote
def run_strain(seed: int, global_state: PandemicStateHandle, domain: Domain,
               fitness_function: Callable[[Solution], float], strain_properties: StrainProperties,
               update_isolated: bool, log_dir: Optional[str], strain_class: type[CVOA]) -> Solution:
    # The strain runs in its own process: seeded here, from a seed drawn in the
    # driver, so the launcher's seed reaches it (A-06).
    set_seed(seed)
    strain = strain_class(global_state, domain, fitness_function, strain_properties, update_isolated, log_dir,
                          distributed=True)
    return strain.run()



def distributed_cvoa_launcher(strains: List[StrainProperties], domain: Domain, fitness_function: Callable[[Solution], float],
                              update_isolated: bool = False, log_dir: Optional[str] = None,
                              seed: Optional[int] = None, strain_class: type[CVOA] = CVOA,
                              max_evaluations: Optional[int] = None, timeout: Optional[float] = None) -> Solution:
    """
    Run a distributed CVOA pandemic and return the best solution.

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
    :param seed: Seed making the pandemic reproducible (default is None). Each
        strain's worker and each carrier's task is seeded from a value drawn in the
        driver; the order in which they reach the shared state still depends on timing,
        which can change a run on a domain small enough for two of them to reach the
        same point at once.
    :type seed: Optional[int], optional
    :param strain_class: The class every strain is built from, run with ``distributed=True``
        (default is CVOA).
    :type strain_class: type[CVOA], optional
    :param max_evaluations: The most evaluations of the fitness function the whole pandemic
        may make, shared by every strain and every task; None, the default, sets no limit.
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

    Ray is started here only if it was not running, and in that case it is shut down
    before returning, also when a strain fails; a runtime the caller started is left as
    it was.
    """
    require_integer("max_evaluations", max_evaluations, 1, optional=True)
    require_number("timeout", timeout, above=0, optional=True)
    if seed is not None:
        set_seed(seed)

    # Started here only when nobody had started it, and stopped here only in that
    # case, also when a strain fails: the launcher used to leave a runtime it had
    # started running for the rest of the process (F-44), the mirror of F-21.
    stop_ray = start_ray(True)
    try:
        return _run_pandemic(strains, domain, fitness_function, update_isolated, log_dir, strain_class,
                             max_evaluations, timeout)
    finally:
        stop_ray()


def _run_pandemic(strains: List[StrainProperties], domain: Domain,
                  fitness_function: Callable[[Solution], float], update_isolated: bool,
                  log_dir: Optional[str], strain_class: type[CVOA], max_evaluations: Optional[int] = None,
                  timeout: Optional[float] = None) -> Solution:
    """
    Run the strains on an already started Ray runtime and report; see distributed_cvoa_launcher.
    """
    # Initialize the global state
    solution_type = solution_class(domain)
    # The actor class is created through .remote(), which mypy cannot see on the
    # decorated class; the handle it returns is what every strain talks to (P-11).
    global_state: PandemicStateHandle = cast(Any, RemotePandemicState).remote(
        solution_type(domain, connector=domain.get_connector()), max_evaluations, timeout)
    if max_evaluations is not None or timeout is not None:
        # The copies the strains and their tasks make of it ask the same actor (F-76).
        fitness_function = BudgetedFitness(fitness_function, RemotePandemicStateProxy(global_state))

    t1 = time()
    futures = [run_strain.remote(spawn_seed(), global_state, domain, fitness_function, strain_properties,
                                 update_isolated, log_dir, strain_class)
               for strain_properties in strains]
    results = ray.get(futures)
    t2 = time()

    best_solution = ray.get(global_state.get_best_individual.remote())

    output = (
            "\n********** Results by strain **********\n"
            + "\n".join(f"[{strain_id}] Best individual: {result}" for strain_id, result in
                        zip([strain.strain_id for strain in strains], results))
            + "\n\n********** Best result **********\n"
            + f"Best individual: {best_solution}\n"
            + "\n********** Pandemic report **********\n"
            + f"Pandemic report: {ray.get(global_state.get_pandemic_report.remote())}\n"
            + "\n********** Performance **********\n"
            + f"Execution time: {timedelta(seconds=t2 - t1)}\n"
    )

    metagen_logger.info(output)

    return best_solution


