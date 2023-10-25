![https://pypi.org/project/pymetagen-datalabupo/](https://img.shields.io/badge/python->=3.12-orange) ![https://img.shields.io/github/v/release/DataLabUPO/MetaGen](https://img.shields.io/github/v/release/DataLabUPO/MetaGen) [![view - Documentation](https://img.shields.io/badge/view-Documentation-blue)](https://pymetagen.readthedocs.io)

# MetaGen: A framework for metaheuristic development and hyperparameter optimization in machine and deep learning 

Machine and deep learning have transformed the field of computing in recent decades, delivering impressive accuracy results when processing large datasets. However, a common challenge arises when implementing these algorithms: setting the hyperparameters. Many algorithms are sensitive to these adjustments, and the quality of the results heavily depends on the choices made. Metaheuristics are a widely used strategy for finding optimal hyperparameter settings for a specific algorithm.

**MetaGen** is a comprehensive and user-friendly metaheuristic development framework that provides tools to define and solve hyperparameter optimization in machine and deep learning. 

### Instalation 
**MetaGen** only requires python (>=3.10) as the library has been built completely on Python.

For the instalation, the easiest way is to use pip:

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

* CoronaVirus Optimization Algorithm paper: https://www.liebertpub.com/doi/10.1089/big.2020.0051