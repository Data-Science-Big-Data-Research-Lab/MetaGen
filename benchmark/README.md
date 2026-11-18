# Benchmark

The material of the experimental section of the MetaGen article (Neurocomputing 637, 2025,
https://doi.org/10.1016/j.neucom.2025.130046), which compares MetaGen's `RandomSearch` and
`TPE` with Optuna and Hyperopt.

- `experimentation.ipynb` runs the comparison over the nine optimization functions defined in
  `functions.py`.
- `experimentation_ml.ipynb` runs it over two hyperparameter optimization problems.

They need the libraries they compare against, listed in `requirements-optional.txt` at the root
of the repository. Every run takes a `seed`, which is passed to each library.
