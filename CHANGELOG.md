# Changelog

## Unreleased

### New

- **Structures with a definition per position**: `Domain.set_structure_to_variables(name,
  variables)` gives each position of a static or dynamic structure its own definition,
  taken from already defined variables, one per position. Every position is drawn,
  mutated, checked and recombined against its own definition, and a dynamic structure
  grows and shrinks at its end. All the metaheuristics support it.
- **Conditional variables**: `Domain.set_condition(name, variable, values)` makes a
  variable active only when another one, an integer or a categorical one, takes one of
  the given values. While inactive, `solution[name]` is `None` and
  `Solution.is_active(name)` is `False`; the metaheuristics do not mutate it, two
  solutions that differ only in it are equal, and TPE and KernelTPE model it only from
  the solutions in which it was active.
- **`infection_alteration_limit`** in `StrainProperties`: how far a CVOA infection moves
  each variable it changes, as a `RelativeAlteration`, an absolute amount or `None` (the
  default, which draws the variable over its whole domain).

### Changes

- **Integer neighborhoods**: an integer mutated within a limit, absolute or
  `RelativeAlteration`, now draws from the grid points on both sides of its value alike,
  and always reaches at least one step, so a two-valued integer always flips and a narrow
  range always moves.
- **Modules are named after their algorithm**: `metagen.metaheuristics.random_search`,
  `hill_climbing`, `tabu_search`, `simulated_annealing`, `genetic` and `memetic`, and
  within `cvoa`, `cvoa`, `probabilistic_cvoa`, `distributed_cvoa`, `local_state` and
  `ray_tools`. Imports from `metagen.metaheuristics` do not change. The earlier module
  paths (`metagen.metaheuristics.ga`, `...rs`, `...cvoa.cvoa_local` and the rest) still
  import, return the same modules and emit a `DeprecationWarning` with the current path.

## 1.0.0

MetaGen 1.0.0 adds new algorithms, reproducible runs, a second distribution model, type
information and a continuous integration suite.

### New

- **`seed`** parameter on every metaheuristic and launcher. The package keeps its own
  random generators, apart from the process-wide `random` and `numpy.random`. The same
  seed reproduces a run, across processes and across Ray workers on the same number of
  CPUs.
- **`HillClimbing`**, `metagen.metaheuristics.hc`: stochastic hill climbing with a short
  memory of visited solutions.
- **`KernelTPE`**: a Tree-structured Parzen Estimator that models each variable with a
  mixture of kernels and evaluates one candidate per iteration, for fitness functions
  that are expensive to evaluate. `TPE` evaluates a pool of candidates per iteration.
- **`ProbabilisticCVOA`**: a CVOA strain class in which deaths, superspreading and
  isolation are drawn per individual. The launchers take `strain_class=`.
  `StrainProperties` is exported from `metagen.metaheuristics`.
- **Two distribution models**, `distribution_model="global"` (default) and `"islands"`.
  Under the global model the population is shuffled before being split across CPUs and
  the next population is selected among the individuals of every worker, so the budget
  of an iteration does not grow with the number of CPUs.
- **`RelativeAlteration`**, `metagen.framework`: a mutation limit expressed as a fraction
  of each variable's range. It is the default `alteration_limit` of `HillClimbing`,
  `TabuSearch`, `SA` and `Memetic`, and the default `mutation_alteration_limit` of `GA`
  and `SSGA`; a plain number is an absolute limit.
- **Genetic algorithms accept dynamic structures**, with a cut-and-splice crossover that
  recombines lengths as well as values, a blend (BLX-alpha) crossover for real and integer
  variables, and tournament parent selection (`tournament_size`).
- **`TPE` exposes `population_size`**, and its documentation gives the cost of a run in
  evaluations.
- **`StrainProperties.max_iterations_without_improvement`** for an early stop.
- **Type information**: the package ships `py.typed`.
- `Memetic` needs Ray only under `distributed=True`.

### Changes that may require updating your code

- **`TabuSearch`** moves to the best non-tabu neighbor even when it is worse and applies
  an aspiration criterion, with a relative `tabu_radius` for continuous variables. For a
  search that only accepts improving moves, use `HillClimbing`.
- **TensorBoard logging is enabled with `log_dir`**, which defaults to `None` in every
  metaheuristic and in the CVOA launchers; pass a directory to write the logs.
- **Console output is enabled with `set_metagen_logger_level()`.** Importing the package
  leaves the logging configuration of the process untouched.
- **`solution["name"]` returns plain Python values at any depth**: a `dict` for a group
  and a `list` for a structure. `solution.get("name")` returns the objects.
- **Structures check their length** against the definition on `set`, `append`, `insert`
  and `del`, including the length step of a dynamic structure.
- **CVOA**: the defaults of `StrainProperties` follow the setup suggested in the CVOA
  paper (`pandemic_duration` 30, `p_isolation` 0.7, `p_re_infection` 0.02), and a strain
  runs its whole `pandemic_duration` unless `max_iterations_without_improvement` is set.
- **`GA`, `SSGA` and `Memetic` check at construction** that the domain was created with a
  connector whose solutions can cross over, such as `GAConnector`.
- **Defaults**: `SA` evaluates five neighbors per iteration and derives its cooling rate
  from `max_iterations` when none is given; `GA` and `SSGA` mutate a child within a fifth
  of each variable's range (`mutation_alteration_limit=None` redraws it over its whole
  domain).
- MetaGen is distributed under the GNU General Public License v3 or later.

### Project

- Continuous integration on GitHub Actions: tests on Python 3.10 to 3.12, `mypy`, and a
  job with Ray.
- The test suite is `pytest test`: a behavioral benchmark on nine optimization functions
  and two applied problems, framework integration tests and regression tests.
- Documentation: a guide to choosing a metaheuristic, pages for every algorithm and for
  the two distribution models, and code examples that are run as part of the checks.

## 0.2.0

The version described in the MetaGen article (Neurocomputing 637, 2025).
