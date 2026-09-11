from datetime import timedelta
from time import time
from typing import Any, Callable, List, Optional, cast

from metagen.metaheuristics.import_helper import is_package_installed

if is_package_installed("ray"):
    import ray
else:
    raise ImportError("Ray is not installed. Please install it to use distributed CVOA.")

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed, spawn_seed
from metagen.logging.metagen_logger import metagen_logger
from metagen.metaheuristics.cvoa.common_tools import StrainProperties
from metagen.metaheuristics.cvoa.cvoa_distributed import DistributedCVOA
from metagen.metaheuristics.cvoa.distributed_tools import PandemicStateHandle, RemotePandemicState
from metagen.metaheuristics.tools import solution_class


@ray.remote
def run_strain(seed: int, global_state:RemotePandemicState, domain:Domain, fitness_function: Callable[[Solution],float],
               strain_properties:StrainProperties, update_isolated:bool, log_dir:Optional[str]) -> Solution:
    # The strain runs in its own process: seeded here, from a seed drawn in the
    # driver, so the launcher's seed reaches it (A-06).
    set_seed(seed)
    strain = DistributedCVOA(global_state, domain,fitness_function, strain_properties, update_isolated, log_dir)
    return strain.run()



def distributed_cvoa_launcher(strains: List[StrainProperties], domain: Domain, fitness_function: Callable[[Solution], float],
                              update_isolated: bool = False, log_dir: Optional[str] = None,
                              seed: Optional[int] = None) -> Solution:
    """
    Run a distributed CVOA pandemic and return the best solution.

    :param strains: The strains taking part in the pandemic.
    :type strains: List[StrainProperties]
    :param domain: The problem domain.
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions.
    :type fitness_function: Callable[[Solution], float]
    :param update_isolated: Kept for compatibility and ignored: since F-45 every isolated
        individual is counted.
    :type update_isolated: bool, optional
    :param log_dir: Directory the TensorBoard logs are written to. None, the default, writes nothing.
    :type log_dir: str or None, optional
    :param seed: Seed making the pandemic reproducible (default is None). Each
        strain's worker is seeded from a value drawn in the driver, so one strain
        reproduces; with several strains the order in which they reach the shared
        state still depends on timing.
    :type seed: Optional[int], optional
    :return: The best solution found across every strain.
    :rtype: Solution

    Ray is started here only if it was not running, and in that case it is shut down
    before returning, also when a strain fails; a runtime the caller started is left as
    it was.
    """
    if seed is not None:
        set_seed(seed)

    # Started here only when nobody had started it, and stopped here only in that
    # case, also when a strain fails: the launcher used to leave a runtime it had
    # started running for the rest of the process (F-44), the mirror of F-21.
    started_ray = not ray.is_initialized()
    if started_ray:
        ray.init()
    try:
        return _run_pandemic(strains, domain, fitness_function, update_isolated, log_dir)
    finally:
        if started_ray and ray.is_initialized():
            ray.shutdown()


def _run_pandemic(strains: List[StrainProperties], domain: Domain,
                  fitness_function: Callable[[Solution], float], update_isolated: bool,
                  log_dir: Optional[str]) -> Solution:
    """
    Run the strains on an already started Ray runtime and report; see distributed_cvoa_launcher.
    """
    # Initialize the global state
    solution_type = solution_class(domain)
    # The actor class is created through .remote(), which mypy cannot see on the
    # decorated class; the handle it returns is what every strain talks to (P-11).
    global_state: PandemicStateHandle = cast(Any, RemotePandemicState).remote(
        solution_type(domain, connector=domain.get_connector()))

    t1 = time()
    futures = [run_strain.remote(spawn_seed(), global_state, domain, fitness_function, strain_properties,
                                 update_isolated, log_dir)
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


