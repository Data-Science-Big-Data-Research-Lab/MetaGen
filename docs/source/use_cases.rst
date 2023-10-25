===========
Use cases
===========

Solving use cases in google colab:

    * https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p1.ipynb
    * https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p2.ipynb
    * https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p3.ipynb
    * https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p4.ipynb

Developing use cases in google colab:
    * https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/duc_rs.ipynb

Hyperparameter optimization with scikit-learn
----------------------------------------------

In this section, a hyperparameter optimization usecase is detailed employing the Metagen library and scikit-learn in five steps.

Step 1: Import the required libraries. In most cases only the Domain and the meta-heuristic is required, the solution is included in this case just for type checking.

.. code-block:: python

     from metagen.framework import Domain, Solution
     from metagen.heuristics import RandomSearch
     from sklearn.ensemble import RandomForestClassifier


Step 2: Select your datasets. In this case, a syntetic classification dataset has been employed. 

.. code-block:: python

    X_classification, y_classification = make_classification(n_samples=1000, n_features=4,
                                                         n_informative=2, n_redundant=0,
                                                         random_state=0, shuffle=False)



Step 3: Define the domain. The usual hyperparameters of a random forect classifier has been defined in our domain.

.. code-block:: python

    random_forest_classifier_definition = Domain()
    random_forest_classifier_definition.define_integer("max_depth", 2, 100, 1)
    random_forest_classifier_definition.define_integer("n_estimators", 10, 500, 1)
    random_forest_classifier_definition.define_categorical("criterion", ['gini', 'entropy'])
    random_forest_classifier_definition.define_categorical("max_features", ['auto', 'sqrt', 'log2'])


Step 4: Define fitness function. In this case, the the averaged accuracy over the folds on the cross validation has been selected. Note that the solution can be accessed like a dictionary to obtain the sampled hyparameters.

.. code-block:: python

    def random_forest_classifier_fitness(solution):
        max_depth = solution["max_depth"]
        n_estimators = solution["n_estimators"]
        criterion = solution["criterion"]
        max_features = solution["max_features"]

        clf = RandomForestClassifier(max_depth=max_depth, n_estimators=n_estimators, criterion=criterion,
                                     max_features=max_features, random_state=0, n_jobs=-1)
        scores = cross_val_score(clf, X_classification, y_classification,
                                 scoring="accuracy", cv=10, n_jobs=-1)

        return -scores.mean()

Step 5: Use an already defined meta-heuristic in the metagen framework.

.. code-block:: python

    random_search: RandomSearch = RandomSearch(random_forest_classifier_definition, random_forest_classifier_fitness)
    best_solution: Solution = random_search.run()

Every meta-heuristic receives the domain definition and the fitness function at least. The instances contains the `run` function which executes the algorithm and always returns a the best Solution.

Hyperparameter optimization with tensorflow
----------------------------------------------

In this section, a hyperparameter optimization usecase is detailed employing the Metagen library and tensorflow in five steps.

Step 1: Import the required libraries. In most cases only the Domain and the meta-heuristic is required, the solution is included in this case just for type checking.
.. code-block:: python

     from metagen.framework import Domain, Solution
     from metagen.heuristics import RandomSearch
     import tensorflow as tf


Step 2: Select your datasets. In this case, a syntetic regression dataset has been employed. 

.. code-block:: python

    from sklearn.datasets import make_regression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import numpy as np

    scaler_x = StandardScaler()
    scaler_y = StandardScaler()

    x, y = make_regression(n_samples=1000, n_features=24)

    xs_train, xs_val, ys_train, ys_val = train_test_split(
        x, y, test_size=0.33, random_state=42)

    xs_train = scaler_x.fit_transform(xs_train)
    ys_train = scaler_y.fit_transform(ys_train)
    xs_val = scaler_x.transform(xs_val)
    ys_val = scaler_y.transform(ys_val)

    x_train = np.reshape(xs_train, (xs_train.shape[0], xs_train.shape[1], 1))
    y_train = np.reshape(ys_train, (ys_train.shape[0], 1))
    x_val = np.reshape(xs_val, (xs_val.shape[0], xs_val.shape[1], 1))
    y_val = np.reshape(ys_val, (ys_val.shape[0], 1))

Step 3: Define the domain. The usual hyperparameters of a neural network has been defined in our domain.

.. code-block:: python

    nn_domain = Domain()
    nn_domain.define_real("learning_rate", 0.0, 0.000001)
    nn_domain.define_categorical("ema", [True, False])
    nn_domain.define_dynamic_structure("arch", 2, 10)
    nn_domain.define_group("layer")
    nn_domain.define_integer_in_group("layer", "neurons", 25, 300)
    nn_domain.define_categorical_in_group("layer", "activation", ["relu", "sigmoid", "softmax", "tanh"])
    nn_domain.define_real_in_group("layer", "dropout", 0.0, 0.45)
    nn_domain.set_structure_to_variable("arch", "layer")

Step 4: Define fitness function. First, the neural network is build considering the solution which encodes the hyperparameters. Secondly, the model is trained on the training set and evaluated on the validation set, returning the validation MSE.

.. code-block:: python

    def build_neural_network(solution: Solution) -> tf.keras.Sequential():
        model = tf.keras.Sequential()

        for i, layer in enumerate(solution["arch"]):
            neurons = layer["neurons"]
            activation = layer["activation"]
            dropout = layer["dropout"]
            rs = True
            if i == len(solution["arch"]):
                rs = False
            model.add(tf.keras.layers.LSTM(neurons, activation=activation, return_sequences=rs))
            model.add(tf.keras.layers.Dropout(dropout))
        model.add(tf.keras.layers.Dense(1))
        # Model compilation
        learning_rate = solution["learning_rate"]
        ema = solution["ema"].value
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate, use_ema=ema),
                    loss="mean_squared_error", metrics=[tf.keras.metrics.MAPE])
        return model
    
    def fitness(solution: Solution, x_train, y_train, x_val, y_val) -> float:
        model = build_neural_network(solution)
        model.fit(x_train, y_train, epochs=10, batch_size=1024)
        mape = model.evaluate(x_val, y_val)[1]
        return mape


Step 5: Execute the optimization algorithm. Note than the fitness function must be Callabe[[Solution], float], so cannot set a function with more than one parameters. For that reason, a lambda function is employed.

.. code-block:: python

    best_solution: Solution = RandomSearch(nn_domain, lambda solution: fitness(solution, x_train, y_train, x_val, y_val), search_space_size=5, iterations=2).run()

Every meta-heuristic receives the domain definition and the fitness function at least. The instances contains the `run` function which executes the algorithm and always returns a the best Solution.


Use metagen to implement your own meta-heuristic
-----------------------------------------------------

In this example a simple RandomSearch algorithm has been developed using the metagen framework. 

**Initialization**

The RandomSearch class is defined, and its constructor (__init__) is provided with the following parameters:

    * domain: Domain: The domain of possible solutions.
    * fitness: Callable[[Solution], float]: A function that calculates the fitness of a solution.
    * search_space_size: int = 30: The number of potential solutions to generate.
    * iterations: int = 20: The number of search iterations to perform.
    * The constructor stores these parameters as instance variables.

**Generating Potential Solutions**

In the run method, an empty list called potential_solutions is initialized to store potential solution objects.

A loop is used to create self.search_space_size potential solutions. For each iteration of the loop, a Solution object is created, passing in the domain and a connector obtained from the domain. These potential solutions are appended to the potential_solutions list.

**Best Solution search**

The initial best solution is determined by finding the solution with the minimum fitness value among the potential solutions. The deepcopy function is used to create a deep copy of this solution and assign it to the variable solution.

Another loop is used to perform the search for self.iterations iterations.

Inside this loop, each potential solution in the potential_solutions list is processed. For each potential solution (ps), the following steps are performed:

    * ps.mutate(): The mutate method is called on the potential solution, which modifies it to explore new possibilities within the solution space by employing the mutate function in Solution.

    * ps.evaluate(self.fitness): The fitness of the potential solution is evaluated using the provided fitness function self.fitness by employing the evaluate function in Solution.

    * If the fitness of the potential solution (ps) is better (i.e., lower fitness value) than the fitness of the current best solution (solution), the solution is updated with a deep copy of the potential solution. This is done to keep track of the best solution found so far.

    * After completing the search loop, the best solution found during the search is returned as the result of the run method.

.. code-block:: python

    class RandomSearch:

        def __init__(self, domain: Domain, fitness: Callable[[Solution], float], search_space_size: int = 30,
                    iterations: int = 20) -> None:

            self.domain = domain
            self.fitness = fitness
            self.search_space_size = search_space_size
            self.iterations = iterations

        def run(self) -> Solution:

            potential_solutions: List[Solution] = list() 
            
            for _ in range(0, self.search_space_size):
                potential_solutions.append(Solution(self.domain, connector=self.domain.get_connector()))
                
            solution: Solution = deepcopy(min(potential_solutions))

            for _ in range(0, self.iterations):
                for ps in potential_solutions:
                    ps.mutate()

                    ps.evaluate(self.fitness)
                    if ps < solution:
                        solution = deepcopy(ps)

            return solution


Implement your own meta-heuristic and extend the functionality of the framework
---------------------------------------------------------------------------------
The provided code defines a Genetic Algorithm (GA) implementation by extending the functionality of some already defined classes and implementing custom classes specifically for the Genetic Algorithm.

**Extending the type classes**
Firsly the Structure and Solution classes are extended to include the crossover function.

* GAStructure is a custom class representing the structure of individuals in the genetic algorithm. It defines a crossover method for performing the crossover operation with another GAStructure instance.
* GASolution is a custom class representing a solution in the genetic algorithm. It inherits from the Solution class and also defines a crossover method for performing crossover with another GASolution instance. The crossover operation involves exchanging variables between two solutions.

.. code-block:: python

    from __future__ import annotations

    import random
    from copy import copy
    from typing import Tuple

    import metagen.framework.solution as types
    from metagen.framework import BaseConnector, Solution
    from metagen.framework.domain import (BaseDefinition, CategoricalDefinition,
                                        DynamicStructureDefinition,
                                        IntegerDefinition, RealDefinition,
                                        StaticStructureDefinition)


    class GAStructure(types.Structure):
        """
        Represents the custom Structure type for the Genetic Algorithm (GA).
        Methods:
            mutate(): Modify the Structure by performing an action selected randomly from three options. Inherited from :py:class:`~metagen.framework.solution.Structure`.
            _resize(): Resizes the vector based on the definition provided at initialization. Inherited from :py:class:`~metagen.framework.solution.Structure`.
            _alterate(): Randomly alters a certain number of elements in the vector by calling their `mutate` method. Inherited from :py:class:`~metagen.framework.solution.Structure`.
            crossover(other: GAStructure) -> Tuple[GAStructure, GAStructure]: Performs crossover operation with another GAStructure instance.
        """

        def crossover(self, other: GAStructure) -> Tuple[GAStructure, GAStructure]:
            """
            Performs crossover operation with another GAStructure instance by randomly modifying list positions. Note that this operation does not support an `DynamicStructureDefinition`.
            """

            child1 = GAStructure(self.get_definition(), connector=self.connector)
            child2 = GAStructure(self.get_definition(), connector=self.connector)

            current_size = min(len(self), len(other))
            number_of_changes = random.randint(1, current_size)
            indexes_to_change = random.sample(
                list(range(0, current_size)), number_of_changes)

            if isinstance(self.get_definition(), DynamicStructureDefinition):
                raise NotImplementedError()
            else:
                for i in range(current_size):
                    if i in indexes_to_change:
                        child1[i], child2[i] = copy(other.get(i)), copy(self.get(i))
                    else:
                        child1[i], child2[i] = copy(self.get(i)), copy(other.get(i))
            return child1, child2


    class GASolution(Solution):
        """
        Represents a Solution type for the Genetic Algorithm (GA).

        Methods:
            mutate(alterations_number: int = None): Modify a random subset of the solution's variables calling its mutate method. Inherited from :py:class:`~metagen.framework.solution.Structure`.
            crossover(other: GASolution) -> Tuple[GASolution, GASolution]: Performs crossover operation with another GASolution instance.
        """

        def crossover(self, other: GASolution) -> Tuple[GASolution, GASolution]:
            """
            Performs crossover operation with another GASolution instance by randomly exchanging variables.
            """
            assert self.get_variables().keys() == other.get_variables().keys()

            basic_variables = [variable_name for variable_name, variable_value in self.get_variables(
            ).items() if self.connector.get_builtin(variable_value) in [int, float, str]]

            if len(basic_variables) > 0:
                n_variables_to_exchange = random.randint(
                    1, len(basic_variables) - 1)

                variables_to_exchange = random.sample(
                    basic_variables, n_variables_to_exchange)
            else:
                variables_to_exchange = []

            child1 = GASolution(self.get_definition(), connector=self.connector)
            child2 = GASolution(self.get_definition(), connector=self.connector)

            for variable_name, variable_value in self.get_variables().items():  # Iterate over all variables

                if variable_name not in basic_variables:
                    variable_child1, variable_child2 = variable_value.crossover(
                        other.get(variable_name))
                    child1.set(variable_name, copy(variable_child1))
                    child2.set(variable_name, copy(variable_child2))
                elif variable_name in variables_to_exchange:
                    child1.set(variable_name, copy(other.get(variable_name)))
                    child2.set(variable_name, copy(variable_value))
                else:
                    child1.set(variable_name, copy(self.get(variable_name)))
                    child2.set(variable_name, copy(variable_value))

            return child1, child2


**Define the genetic algorithm**

The GA class represents the genetic algorithm for optimization problems is implemented using the metagen types.

It takes the following parameters in its constructor:

    * domain: The domain representing the problem space.
    * fitness_func: The fitness function used to evaluate solutions.
    * population_size: The size of the population (default is 10).
    * mutation_rate: The probability of mutation for each solution (default is 0.1).
    * n_generations: The number of generations to run the algorithm (default is 50).

The class initializes the genetic algorithm with the provided parameters and stores them as instance variables.

The initialize method is used to create and evaluate initial solutions to populate the population.

The select_parents method selects the top two parents from the population based on their fitness values.

The run method runs the genetic algorithm for the specified number of generations and returns the best solution found.

.. code-block:: python
    
    import random
    from collections.abc import Callable
    from typing import List

    from metagen.framework import Domain
    from metagen.framework.solution.devsolution import Solution


    class GA:
        """
        Genetic Algorithm (GA) class for optimization problems.
        :param domain: The domain representing the problem space.
        :type domain: Domain
        :param fitness_func: The fitness function used to evaluate solutions.
        :type fitness_func: Callable[[Solution], float]
        :param population_size: The size of the population (default is 10).
        :type population_size: int, optional
        :param mutation_rate: The probability of mutation for each solution (default is 0.1).
        :type mutation_rate: float, optional
        :param n_generations: The number of generations to run the algorithm (default is 50).
        :type n_generations: int, optional

        :ivar population_size: The size of the population.
        :vartype population_size: int
        :ivar mutation_rate: The probability of mutation for each solution.
        :vartype mutation_rate: float
        :ivar n_generations: The number of generations to run the algorithm.
        :vartype n_generations: int
        :ivar domain: The domain representing the problem space.
        :vartype domain: Domain
        :ivar fitness_func: The fitness function used to evaluate solutions.
        :vartype fitness_func: Callable[[Solution], float]"""

        def __init__(self, domain: Domain, fitness_func: Callable[[Solution], float], population_size: int = 10, mutation_rate: float = 0.1, n_generations: int = 50) -> None:
        
            self.population_size: int = population_size
            self.mutation_rate: float = mutation_rate
            self.n_generations: int = n_generations
            self.domain: Domain = domain
            self.fitness_func: Callable[[Solution], float] = fitness_func
            self.population: List[Solution] = []

            self.initialize()

        def initialize(self):
            """
            Initialize the population of solutions by creating and evaluating initial solutions.
            """
            self.population = []

            for _ in range(self.population_size):
                solution = GASolution(
                    self.domain, connector=self.domain.get_connector())
                solution.evaluate(self.fitness_func)
                self.population.append(solution)

        def select_parents(self) -> List[Solution]:
            """
            Select the top two parents from the population based on their fitness values.

            :return: The selected parent solutions.
            :rtype: List[Solution]
            """

            parents = sorted(self.population, key=lambda sol: sol.fitness)[:2]
            return parents

        def run(self) -> Solution:
            """
            Run the genetic algorithm for the specified number of generations and return the best solution found.

            :return: The best solution found by the genetic algorithm.
            :rtype: Solution
            """

            for _ in range(self.n_generations):

                parent1, parent2 = self.select_parents()

                offspring = []
                for _ in range(self.population_size // 2):
                    child1, child2 = parent1.crossover(parent2)

                    if random.uniform(0, 1) <= self.mutation_rate:
                        child1.mutate()

                    if random.uniform(0, 1) <= self.mutation_rate:
                        child2.mutate()

                    child1.evaluate(self.fitness_func)
                    child2.evaluate(self.fitness_func)
                    offspring.extend([child1, child2])

                self.population = offspring

                best_individual = min(
                    self.population, key=lambda sol: sol.get_fitness())

            best_individual = min(
                self.population, key=lambda sol: sol.get_fitness())
            return best_individual

**Customize the BaseConnector**

GAConnector is a custom connector class specifically designed for the genetic algorithm. It maps the custom classes implemented to their corresponding definitions and built-in types.
Specifically, this class is used to define how the custom classes (GASolution and GAStructure) are connected to the definitions and built-in types used in the domain.

.. code-block:: python

    class GAConnector(BaseConnector):
        """
        Represents the custom Connector for the Genetic Algorithm (GA) which link the following classes:

        * `BaseDefinition` - `GASolution` - `dict`
        * `IntegerDefinition` - `types.Integer` - `int`
        * `RealDefinition` - `types.Real` - `float`
        * `CategoricalDefinition` - `types.Categorical` - `str`
        * `StaticStructureDefinition`- `GAStructure` - `list`

        Note that the `Solution` and `Structure` original classes has been replaced by the custom classes. Therefore, when instantiating an `StaticStructureDefinition`, the `GAStructure` will be employed.

        Methods:
            __init__(): Initializes the GAConnector instance.
        """

        def __init__(self) -> None:

            super().__init__()

            self.register(BaseDefinition, GASolution, dict)
            self.register(IntegerDefinition, types.Integer, int)
            self.register(RealDefinition, types.Real, float)
            self.register(CategoricalDefinition, types.Categorical, str)
            self.register(StaticStructureDefinition, GAStructure, list)