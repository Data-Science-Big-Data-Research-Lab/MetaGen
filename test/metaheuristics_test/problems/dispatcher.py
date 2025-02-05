"""
    Copyright (C) 2023 David Gutierrez Avilés and Manuel Jesús Jiménez Navarro

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from typing import Callable, Tuple
from metagen.framework import Domain, Solution
from metagen.framework.connector import BaseConnector

from .dummy_catalog import (get_categorical_domain, get_vector_domain,
                           get_all_types_domain, categorical_example_fitness,
                           vector_example_fitness, all_types_fitness)


from .sklearn_catalog import (get_knn_classifier_domain, knn_classifier_fitness,
                             get_knn_regressor_domain, knn_regressor_fitness,
                             get_random_forest_classifier_domain, random_forest_classifier_fitness,
                             get_random_forest_regressor_domain, random_forest_regressor_fitness,
                             get_sgd_classifier_domain, sgd_classifier_fitness,
                             get_sgd_regressor_domain, sgd_regressor_fitness,
                             get_support_vector_classifier_domain, support_vector_classifier_fitness,
                             get_support_vector_regressor_domain, support_vector_regressor_fitness)

from .math_catalog import (get_x_minus_15_raised_to_2_domain,
                           x_minus_15_raised_to_2_fitness,
                           get_x_raised_to_2_domain, x_raised_to_2_fitness, equation_domain, equation_fitness)

# from .tensorflow_catalog import (nn_fitness, get_nn_domain)




def problem_dispatcher(example: str, connector=BaseConnector()) -> Tuple[Domain, Callable[[Solution], float]]:



    if example == "dummy-1":
        problem_definition = get_categorical_domain
        fitness_function = categorical_example_fitness
    elif example == "dummy-2":
        problem_definition = get_vector_domain
        fitness_function = vector_example_fitness
    elif example == "dummy-3":
        problem_definition = get_all_types_domain
        fitness_function = all_types_fitness
    elif example == "math-1":
        problem_definition = get_x_raised_to_2_domain
        fitness_function = x_raised_to_2_fitness
    elif example == "math-2":
        problem_definition = get_x_minus_15_raised_to_2_domain
        fitness_function = x_minus_15_raised_to_2_fitness
    elif example == "math-3":
        problem_definition = equation_domain
        fitness_function = equation_fitness
    elif example == "rd-c":
        problem_definition = get_random_forest_classifier_domain
        fitness_function = random_forest_classifier_fitness
    elif example == "rd-r":
        problem_definition = get_random_forest_regressor_domain
        fitness_function = random_forest_regressor_fitness
    elif example == "knn-c":
        problem_definition = get_knn_classifier_domain
        fitness_function = knn_classifier_fitness
    elif example == "knn-r":
        problem_definition = get_knn_regressor_domain
        fitness_function = knn_regressor_fitness
    elif example == "svm-c":
        problem_definition = get_support_vector_classifier_domain
        fitness_function = support_vector_classifier_fitness
    elif example == "svm-r":
        problem_definition = get_support_vector_regressor_domain
        fitness_function = support_vector_regressor_fitness
    elif example == "sgd-c":
        problem_definition = get_sgd_classifier_domain
        fitness_function = sgd_classifier_fitness
    elif example == "sgd-r":
        problem_definition = get_sgd_regressor_domain
        fitness_function = sgd_regressor_fitness
    # elif example == "nn":
    #     problem_definition = get_nn_domain
    #     fitness_function = nn_fitness
    else:
        problem_definition = get_x_raised_to_2_domain
        fitness_function = x_minus_15_raised_to_2_fitness

    return problem_definition(connector), fitness_function
