from dummy_examples import (all_types_definition, all_types_fitness,
                            categorical_example_definition,
                            categorical_example_fitness,
                            vector_example_definition, vector_example_fitness)
from ml_examples import (knn_classifier_definition, knn_classifier_fitness,
                         knn_regressor_definition, knn_regressor_fitness,
                         random_forest_classifier_definition,
                         random_forest_classifier_fitness,
                         random_forest_regressor_definition,
                         random_forest_regressor_fitness,
                         sgd_classifier_definition, sgd_classifier_fitness,
                         sgd_regressor_definition, sgd_regressor_fitness,
                         support_vector_classifier_definition,
                         support_vector_classifier_fitness,
                         support_vector_regressor_definition,
                         support_vector_regressor_fitness)
from simple_examples import (x_minus_15_raised_to_2_definition,
                             x_minus_15_raised_to_2_fitness,
                             x_raised_to_2_definition, x_raised_to_2_fitness)

from metagen.metaheuristics.cvoa.cvoa import CVOA, cvoa_launcher


def example_dispatcher(example, iterations):
    problem_definition, fitness_function = problem_dispatcher(example)

    solution = cvoa_dispatcher(problem_definition, fitness_function, iterations=iterations)

    return solution


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
        fitness_function = x_raised_to_2_fitness
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
        problem_definition = sgd_classifier_definition
        fitness_function = sgd_classifier_fitness
    elif example == "sgd-r":
        problem_definition = sgd_regressor_definition
        fitness_function = sgd_regressor_fitness
    elif example == "lstm":
        pass
        # problem_definition = lstm_domain
        # fitness_function = lstm_fitness
    else:
        problem_definition = x_raised_to_2_definition
        fitness_function = x_minus_15_raised_to_2_fitness

    return [problem_definition, fitness_function]


def cvoa_dispatcher(problem, fitness, iterations=5):
    CVOA.initialize_pandemic(problem, fitness)
    strain = CVOA("Strain A", pandemic_duration=iterations)
    solution = strain.run()
    return solution
