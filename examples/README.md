# Examples

Scripts and problem catalogs to try MetaGen from a checkout of the repository. They are not
part of the installed package.

- `problems/` is a catalog of ready-made problems, each a domain and a fitness function:
  small synthetic ones (`dummy_catalog.py`), mathematical functions (`math_catalog.py`),
  scikit-learn models (`sklearn_catalog.py`) and TensorFlow networks (`tensorflow_catalog.py`).
  `dispatcher.py` returns one of them by name:

  ```python
  from examples.problems.dispatcher import problem_dispatcher

  domain, fitness = problem_dispatcher("dummy-3")
  ```

  The scikit-learn and TensorFlow problems need those libraries installed; the others do not.

- `cvoa/` runs the Coronavirus Optimization Algorithm over one of those problems, with the
  strains in threads (`run_local_cvoa.py`) or as Ray tasks (`run_distributed_cvoa.py`).

Run them from the root of the repository, so that `examples` is importable:

```sh
python -m examples.cvoa.run_local_cvoa
```
