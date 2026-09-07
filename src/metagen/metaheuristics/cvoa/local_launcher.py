from concurrent.futures.thread import ThreadPoolExecutor
from datetime import timedelta
from time import time
from typing import Callable, List, Optional

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed
from metagen.framework.solution.bounds import SolutionClass
from metagen.logging.metagen_logger import metagen_logger

from metagen.metaheuristics.cvoa.common_tools import StrainProperties
from metagen.metaheuristics.cvoa.cvoa_local import CVOA
from metagen.metaheuristics.cvoa.local_tools import LocalPandemicState


def run_strain(global_state:LocalPandemicState, domain:Domain, fitness_function: Callable[[Solution],float],
               strain_properties:StrainProperties, update_isolated:bool=False, log_dir:Optional[str]=None) -> Solution:
    strain = CVOA(global_state, domain,fitness_function, strain_properties, update_isolated, log_dir)
    return strain.run()



def cvoa_launcher(strains: List[StrainProperties], domain: Domain, fitness_function: Callable[[Solution], float],
                  update_isolated: bool = False, log_dir: Optional[str] = None,
                  seed: Optional[int] = None) -> Solution:
    """
    Run a CVOA pandemic over the given strains and return the best solution.

    :param strains: The strains taking part in the pandemic.
    :type strains: List[StrainProperties]
    :param domain: The problem domain.
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions.
    :type fitness_function: Callable[[Solution], float]
    :param update_isolated: Whether to update the isolated population.
    :type update_isolated: bool, optional
    :param log_dir: Directory the TensorBoard logs are written to. None, the default, writes nothing.
    :type log_dir: str or None, optional
    :param seed: Seed for MetaGen's generators (default is None). Note that a
        pandemic with more than one strain runs them in concurrent threads that
        share those generators, so a seed makes a single-strain run reproducible
        but does not pin down the interleaving of several strains.
    :type seed: Optional[int], optional
    :return: The best solution found across every strain.
    :rtype: Solution
    """
    if seed is not None:
        set_seed(seed)

    # Initialize the global state
    solution_type: type[SolutionClass] = domain.get_connector().get_type(domain.get_core())
    global_state = LocalPandemicState(solution_type(domain, connector=domain.get_connector()))

    t1 = time()
    with ThreadPoolExecutor(max_workers=len(strains)) as executor:
        futures = {strain.strain_id: executor.submit(run_strain, global_state, domain, fitness_function, strain, update_isolated, log_dir) for strain in strains}
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