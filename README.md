# MetaGen: A Framework for Metaheuristic Development and Hyperparameter Optimization

[![Python](https://img.shields.io/badge/python->=3.10-orange)](https://pypi.org/project/pymetagen-datalabupo/)
[![PyPI](https://img.shields.io/pypi/v/pymetagen-datalabupo)](https://pypi.org/project/pymetagen-datalabupo/)
[![Latest Release](https://img.shields.io/github/v/release/Data-Science-Big-Data-Research-Lab/MetaGen)](https://github.com/Data-Science-Big-Data-Research-Lab/MetaGen/releases)
[![CI](https://github.com/Data-Science-Big-Data-Research-Lab/MetaGen/actions/workflows/ci.yml/badge.svg)](https://github.com/Data-Science-Big-Data-Research-Lab/MetaGen/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/view-Documentation-blue)](https://pymetagen.readthedocs.io)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3+-green)](LICENSE)

## 🚀 Why MetaGen?

MetaGen simplifies the development of **metaheuristics** and the **optimization of hyperparameters** in **machine learning** and **deep learning**. Whether you're a **researcher**, **developer**, or **practitioner**, MetaGen provides a structured, flexible, and scalable framework.

### 🔹 Key Features

✔ **Metaheuristic Development Framework** – A base class with the run loop, elitism and callbacks; you write three methods.  
✔ **Hyperparameter Optimization Tools** – Search spaces with integers, reals, categoricals, groups and variable-length structures, for layer and architecture-level tuning.  
✔ **Standardized Interface** – Ensures compatibility between metaheuristic developers and end users.  
✔ **Dynamic Architecture Optimization** – Structures whose length the search itself changes.  
✔ **Seamless Integration** – Compatible with `scikit-learn`, `tensorflow`, `pytorch`, and other ML libraries.  
✔ **Built-in Metaheuristics** – Pre-implemented algorithms ready to use.  
✔ **Reproducible Runs** – A `seed` parameter controls every random draw, also across Ray workers.  
✔ **TensorBoard Integration** – Give a run a `log_dir` and follow how the algorithm evolves, graphically, in TensorBoard.  
✔ **Scalable and Distributed Execution** – With `distributed=True`, metaheuristics run across the CPUs of a [Ray](https://www.ray.io) cluster.  

### 📌 Built-in Metaheuristics

- **Random Search**
- **Hill Climbing**
- **Tabu Search**
- **Simulated Annealing**
- **Genetic Algorithm** and **Steady-State Genetic Algorithm**
- **Memetic Algorithm**
- **Tree-structured Parzen Estimator**: `TPE`, which evaluates a pool of candidates per iteration, and `KernelTPE`, which evaluates a single candidate per iteration, for expensive fitness functions
- **Coronavirus Optimization Algorithm (CVOA)**, with two strain classes, `CVOA` and `ProbabilisticCVOA`, that differ in how deaths, superspreaders and isolation are decided

The documentation has a [guide to choosing one](https://pymetagen.readthedocs.io/en/latest/choosing/index.html), with what each costs in evaluations.

## 📦 Installation

MetaGen requires **Python 3.10+** and can be installed with:

```bash
pip install pymetagen-datalabupo
```

Two features are optional and installed on demand:

```bash
pip install pymetagen-datalabupo[distributed]   # Ray, for distributed=True
pip install pymetagen-datalabupo[tensorboard]   # TensorBoard logging
pip install pymetagen-datalabupo[all]           # both
```

## 📖 Documentation

The official API reference and usage guides are available at: [MetaGen Documentation](https://pymetagen.readthedocs.io)

## 🤖 Example: Hyperparameter Optimization

Optimizing hyperparameters for a regression model:

```python
from metagen.framework import Domain, Solution
from metagen.metaheuristics import RandomSearch
from sklearn.datasets import make_regression
from sklearn.linear_model import SGDRegressor
from sklearn.model_selection import cross_val_score

# Generate synthetic dataset
X, y = make_regression(n_samples=1000, n_features=4, random_state=0)

# Define the search space
regression_domain = Domain()
regression_domain.define_real("alpha", 0.0001, 0.001)
regression_domain.define_integer("iterations", 5, 200)
regression_domain.define_categorical("loss", ["squared_error", "huber", "epsilon_insensitive"])

# Fitness function: MetaGen always minimizes
def regression_fitness(solution: Solution) -> float:
    model = SGDRegressor(
        loss=solution["loss"],
        alpha=solution["alpha"],
        max_iter=solution["iterations"]
    )
    mape = cross_val_score(model, X, y, scoring="neg_mean_absolute_percentage_error").mean() * -1
    return mape

# Run optimization; the seed makes the run reproducible
best_solution = RandomSearch(regression_domain, regression_fitness, seed=0).run()
print(best_solution)
```

Any other metaheuristic takes the same two arguments. To follow the run in TensorBoard, add `log_dir="logs/random_search"` and launch `tensorboard --logdir=logs`; to see progress on the console, call `set_metagen_logger_level()` from `metagen.logging.metagen_logger`.

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

A metaheuristic can also inherit from the `Metaheuristic` base class, which adds the run loop, elitism, `seed`, `log_dir` and distributed execution in exchange for three methods; see [Extending the Metaheuristic class](https://pymetagen.readthedocs.io/en/latest/advanced_topics/interface.html).

## 📝 Citing MetaGen

If you use MetaGen in your research, please cite:

> D. Gutiérrez-Avilés, M. J. Jiménez-Navarro, J. F. Torres, F. Martínez-Álvarez. *MetaGen: A framework for metaheuristic development and hyperparameter optimization in machine and deep learning.* Neurocomputing 637 (2025) 130046. https://doi.org/10.1016/j.neucom.2025.130046

```bibtex
@article{metagen2025,
  title   = {MetaGen: A framework for metaheuristic development and hyperparameter optimization in machine and deep learning},
  author  = {Guti{\'e}rrez-Avil{\'e}s, David and Jim{\'e}nez-Navarro, Manuel Jes{\'u}s and Torres, Jos{\'e} Francisco and Mart{\'i}nez-{\'A}lvarez, Francisco},
  journal = {Neurocomputing},
  volume  = {637},
  pages   = {130046},
  year    = {2025},
  doi     = {10.1016/j.neucom.2025.130046}
}
```

The article describes version 0.2.0, which remains available on PyPI and as a tagged release.

## 🤝 Contributing

We welcome contributions from developers of all experience levels! To contribute:

- Open an issue or submit a pull request.
- Install the package for development and run the tests:

  ```sh
  pip install -e .[test]
  pytest test
  mypy src
  ```

  Both must pass; the continuous integration runs them on Python 3.10 to 3.12.

## 📌 Resources

- [MetaGen paper](https://doi.org/10.1016/j.neucom.2025.130046) (Neurocomputing, open access)
- [CVOA paper](https://www.liebertpub.com/doi/10.1089/big.2020.0051)
- [Google Colab Notebooks](https://colab.research.google.com/github/Data-Science-Big-Data-Research-Lab/MetaGen)

## ⚖️ License

MetaGen is free software, distributed under the [GNU General Public License v3 or later](LICENSE).

---

**MetaGen** is an open-source project developed and maintained by:

- **David Gutiérrez-Avilés**  
- **Manuel Jesús Jiménez-Navarro**  
- **Francisco José Torres-Maldonado**  
- **Francisco Martínez-Álvarez**  

All authors are members of [DataLabUPO](https://github.com/Data-Science-Big-Data-Research-Lab), the Data Science & Big Data Research Lab at Pablo de Olavide University.
