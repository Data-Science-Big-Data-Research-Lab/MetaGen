# MetaGen: A Framework for Metaheuristic Development and Hyperparameter Optimization

[![Python](https://img.shields.io/badge/python->=3.12-orange)](https://pypi.org/project/pymetagen-datalabupo/) 
[![Latest Release](https://img.shields.io/github/v/release/DataLabUPO/MetaGen)](https://github.com/DataLabUPO/MetaGen/releases) 
[![Documentation](https://img.shields.io/badge/view-Documentation-blue)](https://pymetagen.readthedocs.io) 

## 🚀 Why MetaGen?

MetaGen simplifies the development of **metaheuristics** and the **optimization of hyperparameters** in **machine learning** and **deep learning**. Whether you're a **researcher**, **developer**, or **practitioner**, MetaGen provides a structured, flexible, and scalable framework.

### 🔹 Key Features

✔ **Metaheuristic Development Framework** – Simplifies the creation of custom metaheuristics.  
✔ **Hyperparameter Optimization Tools** – Supports both layer and architecture-level tuning in deep learning.  
✔ **Standardized Interface** – Ensures compatibility between metaheuristic developers and end users.  
✔ **Dynamic Architecture Optimization** – Adapts model structures dynamically during execution.  
✔ **Seamless Integration** – Compatible with `scikit-learn`, `tensorflow`, `pytorch`, and other ML libraries.  
✔ **Built-in Metaheuristics** – Pre-implemented algorithms ready to use.  
✔ **Performance Analysis Tools** – Integrated visualization tools for analyzing metaheuristic performance.  
✔ **Scalable and Distributed Execution** – Metaheuristics can run efficiently across multiple nodes.  

### 📌 Built-in Metaheuristics

MetaGen includes a collection of powerful metaheuristics:

- **Random Search**
- **Tabu Search**
- **Simulated Annealing**
- **Tree-Parzen Estimator**
- **Memetic Algorithm**
- **Genetic Algorithm**
- **Steady-State Genetic Algorithm**
- **Coronavirus Optimization Algorithm (CVOA)**

## 📦 Installation

MetaGen requires **Python 3.10+** and can be installed with:

```bash
pip install pymetagen-datalabupo
```

## 📖 Documentation

The official API reference and usage guides are available at: [MetaGen Documentation](https://pymetagen.readthedocs.io)

## 🛠 Example: Developing a Metaheuristic

Creating a simple **Random Search** metaheuristic:

```python
from copy import deepcopy
from typing import Callable, List
from metagen.framework import Domain, Solution

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
```

## 🤖 Example: Hyperparameter Optimization

Optimizing hyperparameters for a regression model:

```python
from metagen.framework import Domain, Solution
from metagen.metaheuristics.rs import RandomSearch
from sklearn.datasets import make_regression
from sklearn.linear_model import SGDRegressor
from sklearn.model_selection import cross_val_score

# Generate synthetic dataset
X, y = make_regression(n_samples=1000, n_features=4)

# Define the search space
regression_domain = Domain()
regression_domain.define_real("alpha", 0.0001, 0.001)
regression_domain.define_integer("iterations", 5, 200)
regression_domain.define_categorical("loss", ["squared_error", "huber", "epsilon_insensitive"])

# Fitness function
def regression_fitness(solution: Solution):
    model = SGDRegressor(
        loss=solution["loss"],
        alpha=solution["alpha"],
        max_iter=solution["iterations"]
    )
    mape = cross_val_score(model, X, y, scoring="neg_mean_absolute_percentage_error").mean() * -1
    return mape

# Run optimization
best_solution = RandomSearch(regression_domain, regression_fitness).run()
print(best_solution)
```

## 🤝 Contributing

We welcome contributions from developers of all experience levels! To contribute:

- Open an issue or submit a pull request.
- Run tests using:

  ```sh
  pytest test
  ```

## 📌 Resources

- [CVOA Paper](https://www.liebertpub.com/doi/10.1089/big.2020.0051)
- [Google Colab Notebooks](https://colab.research.google.com/github/DataLabUPO/MetaGen)

---

**MetaGen** is an open-source project developed and maintained by:

- **David Gutiérrez-Avilés**  
- **Manuel Jesús Jiménez-Navarro**  
- **Francisco José Torres-Maldonado**  
- **Francisco Martínez-Álvarez**  

All authors are members of [DataLabUPO](https://github.com/Data-Science-Big-Data-Research-Lab), the Data Science & Big Data Research Lab at Pablo de Olavide University.































