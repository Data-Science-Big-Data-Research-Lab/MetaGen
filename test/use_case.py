from cvoa import *
from test.pre_defined_problems import *
from test.sklearn_problems import *

problem_name = "ex1"

# Step 1. Build the problem and the fitness function
if problem_name == "ex1":
    problem = x_minus_15_raised_to_2_definition
    fitness_function = x_minus_15_raised_to_2_fitness
elif problem_name == "ex2":
    problem = x_raised_to_2_definition
    fitness_function = x_minus_15_raised_to_2_fitness
elif problem_name == "ex3":
    problem = categorical_example_definition
    fitness_function = categorical_example_fitness
elif problem_name == "ex4":
    problem = vector_example_definition
    fitness_function = vector_example_fitness
elif problem_name == "ex5":
    problem = all_types_definition
    fitness_function = all_types_fitness
elif problem_name == "rfclf":
    problem = random_forest_classifier_definition
    fitness_function = random_forest_classifier_fitness
elif problem_name == "rfregr":
    problem = random_forest_regressor_definition
    fitness_function = random_forest_regressor_fitness
elif problem_name == "knnclf":
    problem = knn_classifier_definition
    fitness_function = knn_classifier_fitness
elif problem_name == "knnregr":
    problem = knn_regressor_definition
    fitness_function = knn_regressor_fitness
elif problem_name == "svclf":
    problem = support_vector_classifier_definition
    fitness_function = support_vector_classifier_fitness
elif problem_name == "svregr":
    problem = support_vector_regressor_definition
    fitness_function = support_vector_regressor_fitness
elif problem_name == "sgdclf":
    problem = support_vector_classifier_definition
    fitness_function = support_vector_classifier_fitness
elif problem_name == "sgdregr":
    problem = support_vector_regressor_definition
    fitness_function = support_vector_regressor_fitness
else:
    problem = x_minus_15_raised_to_2_definition
    fitness_function = x_minus_15_raised_to_2_fitness

# Step 2. Initialize pandemic
CVOA.initialize_pandemic(problem, fitness_function)

# Step 3. Instance the strains
strain_a = CVOA("Strain A", 5)
strain_b = CVOA("Strain B", 5)
strain_c = CVOA("Strain C", 5)

# Step 4. Run multi-threading pandemic
# solution = cvoa_launcher([strain_a], verbose=True)
solution = cvoa_launcher([strain_a, strain_b, strain_c], verbose=True)

# Step 5. Print the solution
print("DONE!")
print("Solution: " + str(solution))