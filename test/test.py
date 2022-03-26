from pycvoa.cvoa import *
from pycvoa.definition import ProblemDefinition

x_raised_to_2_definition = ProblemDefinition()
x_raised_to_2_definition.register_real_variable("x", 0.0, 100.0, 0.05)


def x_raised_to_2_fitness(individual):
    x = individual.get_variable_value("x")
    return pow(x, 2)


CVOA.initialize_pandemic(x_raised_to_2_definition, x_raised_to_2_fitness)

strain_a = CVOA("Strain A", 5)
strain_b = CVOA("Strain B", 5)
strain_c = CVOA("Strain C", 5)

solution = cvoa_launcher([strain_a, strain_b, strain_c], verbose=True)

print("DONE!")
print("Solution: " + str(solution))
