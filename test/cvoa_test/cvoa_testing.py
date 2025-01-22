import logging

from metagen.framework import Solution
from metagen.logging.metagen_logger import get_metagen_logger, set_metagen_logger_level_console_output, DETAILED_INFO
from metagen.metaheuristics import cvoa_launcher
from metagen.metaheuristics.cvoa.common_tools import StrainProperties
from metaheuristics_test.problems.dispatcher import problem_dispatcher


def main():
    domain, fitness = problem_dispatcher("math-3")

    strain1: StrainProperties = StrainProperties("Strain#1", pandemic_duration=10)
    strain2: StrainProperties = StrainProperties("Strain#2", pandemic_duration=20)
    strain3: StrainProperties = StrainProperties("Strain#3", pandemic_duration=30)

    set_metagen_logger_level_console_output(DETAILED_INFO)

    get_metagen_logger().info(f"Running CVOA")

    solution: Solution = cvoa_launcher([strain1, strain2, strain3], domain, fitness)

    get_metagen_logger().info(f"Best solution found: {solution}")

if __name__ == "__main__":
    main()