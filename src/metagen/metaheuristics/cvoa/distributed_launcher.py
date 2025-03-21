from datetime import timedelta
from time import time
from typing import Callable, List

from metagen.metaheuristics.import_helper import is_package_installed

if is_package_installed("ray"):
    import ray
else:
    raise ImportError("Ray is not installed. Please install it to use distributed CVOA.")

from metagen.framework import Domain, Solution
from metagen.framework.solution.bounds import SolutionClass
from metagen.logging.metagen_logger import metagen_logger
from metagen.metaheuristics.cvoa.common_tools import StrainProperties
from metagen.metaheuristics.cvoa.cvoa_distributed import DistributedCVOA
from metagen.metaheuristics.cvoa.distributed_tools import RemotePandemicState


@ray.remote
def run_strain(global_state:RemotePandemicState, domain:Domain, fitness_function: Callable[[Solution],float],
               strain_properties:StrainProperties, update_isolated:bool, log_dir:str) -> Solution:
    strain = DistributedCVOA(global_state, domain,fitness_function, strain_properties, update_isolated, log_dir)
    return strain.run()



def distributed_cvoa_launcher(strains: List[StrainProperties], domain: Domain, fitness_function: Callable[[Solution], float],
                              update_isolated: bool = False, log_dir: str = "logs/DCVOA") -> Solution:

    # Initialize Ray
    if not ray.is_initialized():
        ray.init()

    # Initialize the global state
    solution_type: type[SolutionClass] = domain.get_connector().get_type(domain.get_core())
    global_state = RemotePandemicState.remote(solution_type(domain, connector=domain.get_connector()))

    t1 = time()
    futures = [run_strain.remote(global_state, domain, fitness_function, strain_properties, update_isolated, log_dir)
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
            + f"Execution time: {timedelta(milliseconds=t2 - t1)}\n"
    )

    metagen_logger.info(output)

    return best_solution


