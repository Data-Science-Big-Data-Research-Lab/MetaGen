Implementing the Random Search metaheuristic with MetaGen
==========================================================

Developing use cases in google colab:
    * https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/duc_rs.ipynb


In this example a simple RandomSearch algorithm has been developed using the metagen framework.

**Initialization**

The RandomSearch class is defined, and its constructor (`__init__`) is provided with the following parameters:

- domain: Domain: The domain of possible solutions.
- fitness: Callable[[Solution], float]: A function that calculates the fitness of a solution.
- search_space_size: int = 30: The number of potential solutions to generate.
- iterations: int = 20: The number of search iterations to perform.
- The constructor stores these parameters as instance variables.

**Generating Potential Solutions**

In the run method, an empty list called potential_solutions is initialized to store potential solution objects.

A loop is used to create self.search_space_size potential solutions. For each iteration of the loop, a Solution object is created, passing in the domain and a connector obtained from the domain. These potential solutions are appended to the potential_solutions list.

**Best Solution search**

The initial best solution is determined by finding the solution with the minimum fitness value among the potential solutions. The deepcopy function is used to create a deep copy of this solution and assign it to the variable solution.

Another loop is used to perform the search for self.iterations iterations.

Inside this loop, each potential solution in the potential_solutions list is processed. For each potential solution (ps), the following steps are performed:

- ps.mutate(): The mutate method is called on the potential solution, which modifies it to explore new possibilities within the solution space by employing the mutate function in Solution.
- ps.evaluate(self.fitness): The fitness of the potential solution is evaluated using the provided fitness function self.fitness by employing the evaluate function in Solution.
- If the fitness of the potential solution (ps) is better (i.e., lower fitness value) than the fitness of the current best solution (solution), the solution is updated with a deep copy of the potential solution. This is done to keep track of the best solution found so far.
- After completing the search loop, the best solution found during the search is returned as the result of the run method.

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
