![https://pypi.org/project/pymetagen-datalabupo/](https://img.shields.io/badge/python->=3.12-orange) ![https://img.shields.io/github/v/release/DataLabUPO/MetaGen](https://img.shields.io/github/v/release/DataLabUPO/MetaGen) [![view - Documentation](https://img.shields.io/badge/view-Documentation-blue)](https://pymetagen.readthedocs.io)

# MetaGen: A framework for metaheuristic development and hyperparameter optimization in machine and deep learning 

Machine and deep learning have transformed the field of computing in recent decades, delivering impressive accuracy results when processing large datasets. However, a common challenge arises when implementing these algorithms: setting the hyperparameters. Many algorithms are sensitive to these adjustments, and the quality of the results heavily depends on the choices made. Metaheuristics are a widely used strategy for finding optimal hyperparameter settings for a specific algorithm.

**MetaGen** is a comprehensive and user-friendly metaheuristic development framework that provides tools to define and solve hyperparameter optimization in machine and deep learning. 

### Instalation 
**MetaGen** only requires python (>=3.10) as the library has been built completely on Python.

For the installation, the easiest way is to use pip:

    pip install pymetagen-datalabupo

### API reference

The official documentation is available in: https://pymetagen.readthedocs.io.

### Development

New contributors from all experience levels are welcomed. To contribute, you can open an issue or sending a pull request.

For testing the repository you just need to execute the following command:

    pytest test

## In this document:

1. [**MetaGen** Features](#metagen-features)
2. [How to implement a metaheuristic with **MetaGen**](#how-to-implement-a-metaheuristic-with-metagen)
3. [How to perform a hyperparameter optimization with **MetaGen**](#how-to-perform-a-hyperparameter-optimization-with-metagen)
4. [Resources](#resources)


## **MetaGen** features

## How to implement a metaheuristic with **MetaGen**

The random search algorithm generates a search space with a specific number of potential solutions, then alters these potential solutions a specified number of times. The potential solution with the lowest fitness function value after each iteration is considered the global solution of the random search.

The [`Domain`](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain) and [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) classes are required, so they are imported from the [`metagen.framework`](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework)  package.

Finally, the `Callable` and `List` classes are imported for typing management, and the `deepcopy` method from the standard copy package is used to preserve a consistent copy of the global solution for each iteration

    from copy import deepcopy
    from typing import Callable, List
    from metagen.framework import Domain, Solution

### Prototype

The `RandomSearch` metaheuristic function takes as input a problem definition, which is composed of a [`Domain`](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain) object and a fitness function that takes a [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) object as input and returns a `float`.

The method also has two arguments to control the metaheuristic, the _search space size_ (default set to `30`) and the _number of iterations_ (default set to `20`). The _search space size_ controls the number of potential solutions generated, and the _number of iterations_ determine the number of times the search space will be altered.

The result of an `RandomSearch` run will be a [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) object that assigns the variables of the [`Domain`](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain) object in a way that optimizes the function. 

In order to encapsulate all these characteristics, a `RandomSearch` class is defined.

    class RandomSearch:

        def __init__(self, domain: Domain, fitness: Callable[[Solution], float], search_space_size: int = 30, iterations: int = 20) -> None:

            self.domain = domain
            self.fitness = fitness
            self.search_space_size = search_space_size
            self.iterations = iterations

### Search space building

The first step of the method involves constructing the search space, which consists of `search_space_size` potential solutions or [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) objects.

Each new potential solution is randomly generated using the [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html)'s `init` method, which creates a [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) object from a [`Domain`](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain).

The newly created [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) is then evaluated using the `evaluate` method passing the fitness function, and all the potential solutions are stored in a `List` of [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html). A copy of the [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) with the minimum function value is also kept.

    def run(self) -> Solution:

        search_space: List[Solution] = list()

        for _ in range(0, search_space_size):
            initial_solution:Solution = Solution()
            initial_solution.evaluate(self.fitness)
            search_space.append(initial_solution)

        global_solution: Solution = deepcopy(min(search_space))

### Altering the search space

The final step involves modifying the potential solutions in the search space over `iteration` iterations. Each [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) is modified using the `mutate` method, which modifies the variable values of a [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) while taking into account the [`Domain`](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain).

The method randomly selects a variable in the [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) to modify and changes its value randomly while also respecting the [`Domain`](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain). If the modified [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) is better than the current global [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html), the latter is updated with a copy of the former.

Finally, the `global_solution` is returned.

    for _ in range(0, iterations):
            for ps in search_space:
                ps.mutate()
                ps.evaluate(self.fitness)
                if ps < solution:
                    global_solution = deepcopy(ps)
    return global_solution

### See also
- [Solution API](https://pymetagen.readthedocs.io/en/latest/solution/solution.html)
- [Domain API](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain)
- [Google Colab Notebook of _Implementing Random Search metaheuristic with MetaGen_](https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/duc_rs.ipynb)


## How to perform a hyperparameter optimization with **MetaGen**

In order to work metagen we first need to import the [Domain](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain) definition and an available [metaheuristic](https://pymetagen.readthedocs.io/en/latest/metaheuristics/index.html).  

    from metagen.framework import Domain, Solution
    from metagen.metaheuristics import RandomSearch

Every problem in metagen is defined by two elements: a **domain** and a **fitness**.

The **domain** of the problem is constructed by using the [Domain](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain) imported previously . In this case we defined a simple domain with one integer variable in range [-10, 10].

    domain: Domain = Domain()
    domain.define_integer("x", -10, 10)

The fitness is a callable which receives a [Solution](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) as parameter and returns a float value.

    def p1_fitness(solution: Solution) -> float:
        x = solution["x"] # The variable represents a potential solution instance which can be used as an map returning the builtin value.
        return x + 5

Finally, we only need to instantiate our metaherustic (in this case a simple random search) indicating the **domain** and **fitness** and run it returning the best solution.

    random_search: RandomSearch = RandomSearch(domain, fitness)
    solution: Solution = random_search.run()

## Resources

- Google Colab Notebooks:
  - [Implementing Random Search metaheuristic with MetaGen](https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/duc_rs.ipynb)
  - [Optimizing $f(x)=x+5$ function](https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p1.ipynb)
- [CoronaVirus Optimization Algorithm paper](https://www.liebertpub.com/doi/10.1089/big.2020.0051)
