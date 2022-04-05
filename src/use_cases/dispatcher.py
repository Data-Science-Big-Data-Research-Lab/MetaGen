from dummy import *
from ml import *
from pycvoa.cvoa import CVOA, cvoa_launcher
from simple import *


def example_dispacher(example):
    definition_fitness = problem_dispatcher(example)

    cvoa_dispatcher(definition_fitness[0], definition_fitness[1])


def problem_dispatcher(example):

    if example == "dummy-1":
        problem_definition = categorical_example_definition
        fitness_function = categorical_example_fitness
    elif example == "dummy-2":
        problem_definition = vector_example_definition
        fitness_function = vector_example_fitness
    elif example == "dummy-3":
        problem_definition = all_types_definition
        fitness_function = all_types_fitness
    elif example == "simple-1":
        problem_definition = x_raised_to_2_definition
        fitness_function = x_minus_15_raised_to_2_fitness
    elif example == "simple-2":
        problem_definition = x_minus_15_raised_to_2_definition
        fitness_function = x_minus_15_raised_to_2_fitness
    elif example == "rd-c":
        problem_definition = random_forest_classifier_definition
        fitness_function = random_forest_classifier_fitness
    elif example == "rd-r":
        problem_definition = random_forest_regressor_definition
        fitness_function = random_forest_regressor_fitness
    elif example == "knn-c":
        problem_definition = knn_classifier_definition
        fitness_function = knn_classifier_fitness
    elif example == "knn-r":
        problem_definition = knn_regressor_definition
        fitness_function = knn_regressor_fitness
    elif example == "svm-c":
        problem_definition = support_vector_classifier_definition
        fitness_function = support_vector_classifier_fitness
    elif example == "svm-r":
        problem_definition = support_vector_regressor_definition
        fitness_function = support_vector_regressor_fitness
    elif example == "sgd-c":
        problem_definition = support_vector_classifier_definition
        fitness_function = support_vector_classifier_fitness
    elif example == "sgd-r":
        problem_definition = support_vector_regressor_definition
        fitness_function = support_vector_regressor_fitness
    else:
        problem_definition = x_raised_to_2_definition
        fitness_function = x_minus_15_raised_to_2_fitness

    return [problem_definition,fitness_function]


def cvoa_dispatcher(problem, fitness):
    CVOA.initialize_pandemic(problem, fitness)
    strain_a = CVOA("Strain A", pandemic_duration=10)
    strain_b = CVOA("Strain B", pandemic_duration=10)
    strain_c = CVOA("Strain C", pandemic_duration=10)
    solution = cvoa_launcher([strain_a, strain_b, strain_c])
    print("DONE!")
    print("Solution: " + str(solution))
