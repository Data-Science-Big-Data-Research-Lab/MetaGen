import ray

from metagen.framework import Solution
from metagen.logging.metagen_logger import metagen_logger, set_metagen_logger_level, DETAILED_INFO
from metagen.metaheuristics.cvoa import distributed_cvoa_launcher

from metagen.metaheuristics.cvoa.common_tools import StrainProperties
from metaheuristics_test.problems.dispatcher import problem_dispatcher


def main():

    domain, fitness = problem_dispatcher("math-3")

    strain1: StrainProperties = StrainProperties("Strain#1", pandemic_duration=5)
    strain2: StrainProperties = StrainProperties("Strain#2", pandemic_duration=5)
    strain3: StrainProperties = StrainProperties("Strain#3", pandemic_duration=5)

    set_metagen_logger_level(DETAILED_INFO)

    print(f"Running distributed CVOA")

    ray.init(num_cpus=4)

    solution: Solution = distributed_cvoa_launcher([strain1, strain2], domain, fitness)

    print(f" ----- Best solution found: {solution}")

if __name__ == "__main__":
    main()