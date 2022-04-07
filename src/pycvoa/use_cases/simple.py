from pycvoa.problem.domain import Domain

# x^2 problem definition
x_raised_to_2_definition = Domain()
x_raised_to_2_definition.define_real_variable("x", 0.0, 100.0, 0.05)


# x^2 fitness function
def x_raised_to_2_fitness(individual):
    x = individual.get_basic_value("x")
    return pow(x, 2)


# (x-15)^2 problem definition
x_minus_15_raised_to_2_definition = Domain()
x_minus_15_raised_to_2_definition.define_real_variable("x", 0.0, 100.0, 0.05)


# (x-15)^2 fitness function
def x_minus_15_raised_to_2_fitness(individual):
    x = individual.get_basic_value("x")
    return pow(x - 15, 2)
