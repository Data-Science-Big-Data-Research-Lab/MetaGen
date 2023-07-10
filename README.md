![https://pypi.org/project/pymetagen-datalabupo/](https://img.shields.io/badge/python-3.12-orange) 
# Metagen 

## Introduction
Metagen is a simple python library for solving optimization problems by metaheuristics algorithms. The project provides a set of already defined metaheristics and provide the basic tools to allow the user redefine/build its own algorithms in a simple way.

This project is currently maintained by the David Gutierrez Áviles and Manuel Jesús Jiménez Navarro.

https://datalab.upo.es/

Link to the original paper: [Metagen](https://example.com)

## Instalation

Metagen only requires python (>=3.12) as the library has been built completely on python.

For the instalation, the easiest way is to use pip:

    pip install metagen


## Tutorial

In orfer to work metagen we first need to import the [Domain](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain) definition and an available [metaheuristic](https://pymetagen.readthedocs.io/en/latest/metaheuristics/index.html).  

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


## Development

New contributors from all experience levels are welcomed. To contribute, you can open an issue or sending a pull request.

For testing the repository you just need to execute the following command:

    pytest test

## API reference

The official documentation is available in: https://pymetagen.readthedocs.io.

## References

* cvoa: https://www.liebertpub.com/doi/10.1089/big.2020.0051