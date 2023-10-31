![https://pypi.org/project/pymetagen-datalabupo/](https://img.shields.io/badge/python->=3.12-orange) ![https://img.shields.io/github/v/release/DataLabUPO/MetaGen](https://img.shields.io/github/v/release/DataLabUPO/MetaGen) [![view - Documentation](https://img.shields.io/badge/view-Documentation-blue)](https://pymetagen.readthedocs.io) [![CircleCI](https://circleci.com/gh/DataLabUPO/MetaGen.svg?style=svg&brach=master)](https://circleci.com/gh/DataLabUPO/MetaGen/?brach=master)

# MetaGen: A framework for metaheuristic development and hyperparameter optimization in machine and deep learning

Machine and deep learning have transformed the field of computing in recent decades, delivering impressive accuracy
results when processing large datasets. However, a common challenge arises when implementing these algorithms: setting
the hyperparameters. Many algorithms are sensitive to these adjustments, and the quality of the results heavily depends
on the choices made. Metaheuristics are a widely used strategy for finding optimal hyperparameter settings for a
specific algorithm.

**MetaGen** is a comprehensive and user-friendly metaheuristic development framework that provides tools to define and
solve hyperparameter optimization in machine and deep learning.

### Instalation

**MetaGen** only requires python (>=3.10) as the library has been built completely on Python.

For the installation, the easiest way is to use pip:

    pip install pymetagen-datalabupo

### API reference

The official documentation is available in: https://pymetagen.readthedocs.io.

### Development

New contributors from all experience levels are welcomed. To contribute, you can open an issue or sending a pull
request.

For testing the repository you just need to execute the following command:

    pytest test

## In this document:

1. [**MetaGen** Features](#metagen-features)
2. [**MetaGen** vs. other proposals](#metagen-vs-other-proposals)
3. [How to implement a metaheuristic with **MetaGen**](#how-to-implement-a-metaheuristic-with-metagen)
4. [How to perform a hyperparameter optimization with **MetaGen**](#how-to-perform-a-hyperparameter-optimization-with-metagen)
5. [Resources](#resources)

## **MetaGen** features

- **Metaheuristic development framework.**  

 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;It provides convenient solution management for the developer and isolates them 
from the intricacies of the search space.    

- **Deployment platform for metaheuristic execution.**   

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;It offers an effortless problem definition process that doesn't require advanced 
programming skills.  

- **Standard interface between metaheuristic developers and users.**  
  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Both developers and users can "speak the same language" through the **MetaGen** package.


- **Specialized tools for deep learning hyperparameter tuning.**  

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;It provides optimization capabilities not just at the layer level but also at the architecture level.

- **Dynamic deep learning architecture adjustment.**  
  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Users are not restricted to optimizing a fixed architecture (e.g., a fixed number of layers); they can also adjust
  specific hyperparameters per layer in a variable architecture.

- **Python type hints annotations.**  

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Implemented using Python type hints annotations, it provides developers and users with an efficient environment for
  coding, debugging, and maintenance.
 

- **Full compatibility with Python machine and deep learning packages.**
  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Thanks to its standard and flexible interface, it is compatible with all Python packages such
  as `scikit-learn`, `keras`, and `tensorflow`.

- **RS, GA and CVOA metaheuristic implementations.**  
  

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;It offers tow popular metaheuristic implementations, Random search and Genetic Algorithm optimization. Furthermore, it
  includes the implementation of CVOA, a metaheuristic inspired by the SARS-CoV-2 propagation model, the virus
  responsible for COVID-19. CVOA was initially used to optimize long-short-term memory (LSTM) networks for electricity
  demand forecasting, but its positive results have inspired its use for other machine and deep learning models.

## MetaGen vs. other proposals

|                                                                                                                                                  | MetaGen | kerastuner | optuna | chocolate | hyperopt and hyperas | sherpa | btb | talos | test-tube | advisor | ray-tune |
|--------------------------------------------------------------------------------------------------------------------------------------------------|:-------:|:----------:|:------:|:---------:|:--------------------:|:------:|:---:|:-----:|:---------:|:-------:|:--------:|
| A new framework for developing custom metaheuristics with a simplified coding process                                                            |   Yes   |     No     |  Yes   |    No     |          No          |  Yes   | No  |  No   |    No     |   No    |    No    |
| Representation of problems and solutions implementation, allowing metaheuristic developers to provide a standard and intuitive interface         |   Yes   |     No     |   No   |    No     |          No          |   No   | No  |  No   |    No     |   No    |    No    |
| Specific mechanisms for optimizing deep learning architectures and hyperparameters                                                               |   Yes   |    Yes     |   No   |    No     |          No          |   No   | No  |  No   |    No     |   No    |    No    |
| Dynamic changes to a deep learning model’s architecture allow the number of layers and hyperparameters to adjust during metaheuristic executions |   Yes   |     No     |   No   |    Yes    |          No          |   No   | No  |  No   |    No     |   No    |    No    |
| User-friendly and accessible to the general public with limited programming skills                                                               |   Yes   |     No     |   No   |    No     |          No          |   No   | No  |  No   |    No     |   No    |   Yes    |
| Python-type hints implementation to help third-party developers and ease debugging                                                               |   Yes   |     No     |   No   |    No     |          No          |   No   | No  |  No   |    No     |   No    |    No    |
| Mechanisms to improve metaheuristics execution across distributed systems                                                                        |   No    |    Yes     |  Yes   |    No     |         Yes          |  Yes   | No  |  Yes  |    Yes    |   No    |   Yes    |
| The package includes visualization tools to analyze the performance of metaheuristics                                                            |   No    |    Yes     |  Yes   |    No     |          No          |   No   | No  |  No   |    Yes    |   Yes   |    No    |

## How to implement a metaheuristic with **MetaGen**

The random search algorithm generates a search space with a specific number of potential solutions, then alters these
potential solutions a specified number of times. The potential solution with the lowest fitness function value after
each iteration is considered the global solution of the random search.

The [`Domain`](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain)
and [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) classes are required, so they are
imported from the [`metagen.framework`](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework)
package.

Finally, the `Callable` and `List` classes are imported for typing management, and the `deepcopy` method from the
standard copy package is used to preserve a consistent copy of the global solution for each iteration

    from copy import deepcopy
    from typing import Callable, List
    from metagen.framework import Domain, Solution

### Prototype

The `RandomSearch` metaheuristic function takes as input a problem definition, which is composed of
a [`Domain`](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain) object and a
fitness function that takes a [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) object as
input and returns a `float`.

The method also has two arguments to control the metaheuristic, the _search space size_ (default set to `30`) and the
_number of iterations_ (default set to `20`). The _search space size_ controls the number of potential solutions
generated, and the _number of iterations_ determine the number of times the search space will be altered.

The result of an `RandomSearch` run will be
a [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) object that assigns the variables of
the [`Domain`](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain) object in a way
that optimizes the function.

In order to encapsulate all these characteristics, a `RandomSearch` class is defined.

    class RandomSearch:

        def __init__(self, domain: Domain, fitness: Callable[[Solution], float], search_space_size: int = 30, iterations: int = 20) -> None:

            self.domain = domain
            self.fitness = fitness
            self.search_space_size = search_space_size
            self.iterations = iterations

### Search space building

The first step of the method involves constructing the search space, which consists of `search_space_size` potential
solutions or [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) objects.

Each new potential solution is randomly generated using
the [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html)'s `init` method, which creates
a [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) object from
a [`Domain`](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain).

The newly created [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) is then evaluated
using the `evaluate` method passing the fitness function, and all the potential solutions are stored in a `List`
of [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html). A copy of
the [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) with the minimum function value is
also kept.

    def run(self) -> Solution:

        search_space: List[Solution] = list()

        for _ in range(0, search_space_size):
            initial_solution:Solution = Solution()
            initial_solution.evaluate(self.fitness)
            search_space.append(initial_solution)

        global_solution: Solution = deepcopy(min(search_space))

### Altering the search space

The final step involves modifying the potential solutions in the search space over `iteration` iterations.
Each [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) is modified using the `mutate`
method, which modifies the variable values of
a [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) while taking into account
the [`Domain`](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain).

The method randomly selects a variable in
the [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) to modify and changes its value
randomly while also respecting
the [`Domain`](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain). If the
modified [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html) is better than the current
global [`Solution`](https://pymetagen.readthedocs.io/en/latest/solution/solution.html), the latter is updated with a
copy of the former.

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
- [Google Colab Notebook of _Implementing Random Search
  metaheuristic_](https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/duc_rs.ipynb)

## How to perform a hyperparameter optimization with **MetaGen**

In a typical machine learning regression problem. The goal is to find the hyperparameters that build
the best model for a training set. To do this, the [`Domain`](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain) 
object is constructed by defining a variable for each parameter to optimize.

### Defining the Domain.

In this case, three variables are defined: a $REAL$ variable called `alpha`, with values in the range of $[0.0001, 0.001]$, is defined using the `define_real` method, and an $INTEGER$ variable called `iterations`, with values in the range of $[5, 200]$, is defined using the `define_integer` method. Additionally, a $CATEGORICAL$ variable is defined using the `define_categorical` method, with the name `loss` and a list of unique values including `squared_error`, `huber`, and `epsilon_insensitive`.
    
    from metagen.framework import Domain
    regression_domain = Domain()
    regression_domain.define_real("alpha", 0.0001, 0.001)
    regression_domain.define_integer("iterations", 5, 200)
    regression_domain.define_categorical("loss", ["squared_error", "huber", "epsilon_insensitive"])

### Implementing the fitness function

The fitness function must then construct a regression model using the training dataset and the hyperparameters of the potential solution. In this case, the sklearn package is used for the machine learning operations.

A synthetic training dataset with $1000$ instances and $4$ features is generated using the `make_regression` method from the `sklearn.datasets` package, and it is loaded into two variables, the inputs `X` and the expected outputs `y`.

    from sklearn.datasets import make_regression
    X, y = make_regression(n_samples=1000, n_features=4)

The function `regression_fitness` is defined with a `Solution` object as an input parameter. The values of `loss`, `iterations`, and the hyperparameter `alpha` are obtained through the bracket `Python` operator.

A regression model using stochastic gradient descent is constructed using the `SGDRegressor` class from the `sklearn.linear_model` package and the obtained values. Cross-validation training is performed using the `cross_val_score` function from the `sklearn.model_selection` package by passing the configured model and the training dataset (`X` and `y`). The cross-validation process is set to return the negative value of the mean absolute percentage error (`mape`), which is specified in the scoring argument.

To find the solution with the least error (i.e., the smallest `mape`), the resulting `mape` value must be multiplied by $-1$.
    
    from metagen.framework import Solution
    from sklearn.linear_model import SGDRegressor
    from sklearn.model_selection import cross_val_score

    def regression_fitness(solution: Solution):
        loss = solution["loss"] # In this case, we get the builtin by getting the value property.
        iterations = solution["iterations"]
        alpha = solution["alpha"] 
        model = SGDRegressor(loss=loss, alpha=alpha, max_iter=iterations)
        mape = cross_val_score(model, X, y, scoring="neg_mean_absolute_percentage_error").mean()*-1
        return mape

To conclude, the `regression_domain` and `regression_fitness` elements are passed to the `RandomSearch` metaheuristic, obtaining a hyperparameter solution for this problem by calling the `run` method.

    regression_solution: Solution = RandomSearch(regression_domain, regression_fitness).run()

Finally, the `regression_solution` is printed.

    print(regression_solution)

### See also

- [Domain API](https://pymetagen.readthedocs.io/en/latest/domain/domain.html#metagen.framework.Domain)
- [Solution API](https://pymetagen.readthedocs.io/en/latest/solution/solution.html)
- [Google Colab Notebook of _Optimizing the hyperparameters of a regression model_](https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/duc_rs.ipynb)

## Resources

- Google Colab Notebooks:
    - [Implementing Random Search metaheuristic](https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/duc_rs.ipynb)
    - [Optimizing f(x) = x+5](https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p1.ipynb)
    - [Optimizing f(x) = x<sup>2</sup>](https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p2.ipynb)
    - [Optimizing the hyperparameters of a regression model](https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p3.ipynb)
    - [Optimizing a Deep Learning model](https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p4.ipynb)
- [CVOA (CoronaVirus Optimization Algorithm) paper](https://www.liebertpub.com/doi/10.1089/big.2020.0051)
