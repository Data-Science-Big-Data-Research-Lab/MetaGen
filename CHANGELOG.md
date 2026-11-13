# Changelog

## Unreleased

### Changes

- **A search of TriGen does not evaluate again a child equal to an individual it has
  already evaluated**: the child takes its fitness, so a search makes fewer evaluations
  and finds the same triclusters. `TriGenGA.evaluated` keeps the best triclusters
  evaluated, one more than the triclusters found before the search, which is what TriGen
  chooses from, instead of all of them.
- **Runs with a seed in several threads at once**, as in a comparison spread over a
  `ThreadPoolExecutor`, each give what they give alone: on a thread other than the main one, a
  run with a seed draws from generators of its own. On the main thread nothing changes.
- **A budget for CVOA.** `cvoa_launcher` and `distributed_cvoa_launcher` take
  `max_evaluations` and `timeout` for the whole pandemic, shared by all its strains and
  checked before every evaluation: once it is spent, nothing more is evaluated and every
  strain stops at the end of the iteration in course. Without them, runs give the same
  results.
- **Domains are validated further.** The bounds of a real are finite numbers, and the bounds
  and the step of an integer are integers. With a step, only the values on its grid from the
  minimum are valid, and a NaN never is: setting one of them raises a `ValueError` that names
  the grid.
- **The parameters of the metaheuristics are checked when they are built.** A value outside
  the ones a parameter takes, such as `tournament_size=0`, `cooling_rate=1.5`, a negative
  `alteration_limit` or a `max_iterations` that is not an integer, raises a `ValueError` that
  names the parameter. A fitness function that returns something that is not a number, such as
  `None`, raises a `TypeError` that names the function.
- **Setting part of a group**, as `solution["g"] = {"a": 2}`, changes the variables given and
  keeps the others, and an initial solution that gives part of a group draws the rest. A group
  given something other than a `dict` raises a `ValueError`.
- **A dynamic structure** keeps its elements within the alteration limit in every mutation,
  also when the mutation changes its length, so its seeded runs under a neighborhood give
  different results.
- **`TPE` and `KernelTPE` with `max_evaluations`** and no `warmup_iterations` shorten their
  warmup so that it and the initial population take at most a quarter of the budget, and
  their model has evaluations left to work with. A `warmup_iterations` given is kept, and runs
  without `max_evaluations` give the same results.
- **`KernelTPE` on a dynamic structure** draws the length of each candidate from a model of
  the lengths of the best solutions, and scores it, before drawing its elements, so its
  proposals follow the lengths that work. Seeded runs over dynamic structures give different
  results.
- **`DistributedCVOA` without Ray** raises an `ImportError` that says how to install it, as a
  distributed run and the distributed launcher of CVOA do.

## 1.6.0

MetaGen 1.6.0 gives the package a public API: the names a program imports, from a few
packages, with the version of the package among them. The documentation imports from them
and its API reference shows every parameter of each metaheuristic.

### New

- **A public API**: what a program needs is imported from `metagen.framework`,
  `metagen.framework.domain`, `metagen.framework.solution`, `metagen.metaheuristics`,
  `metagen.triclustering`, `metagen.triclustering.data`, `metagen.reporting` and
  `metagen.logging`, and the names in their `__all__` are the public API. Among the names they
  add are `Metaheuristic`, `CVOA`, `DistributedCVOA`, `GammaConfig`, `random_exploration`,
  `local_search`, `solution_class` and the types of the genetic algorithms in
  `metagen.metaheuristics`, and `set_seed`, `get_rng` and `get_numpy_rng` in
  `metagen.framework`. The documentation imports from them, and its API reference documents
  each name where it is public. The import paths of earlier releases keep working.
- **`metagen.__version__`** is the version of the installed package.

### Changes

- **The API reference of each metaheuristic** lists all of its parameters, the options of a
  run that every metaheuristic takes among them, each one once.
- **A distributed run without Ray** raises an `ImportError` that says how to install it,
  `pip install pymetagen-datalabupo[distributed]`, the same for every metaheuristic and for
  the distributed launcher of CVOA.

## 1.5.0

MetaGen 1.5.0 makes runs more robust and faster: a fitness that returns NaN, a checkpoint of
another run and a second `run()` of the same object are handled, variables with a step stay on
their grid and move under every neighborhood, and the configuration of a run is in its report.
Several algorithms run faster, with the same results.

### New

- **`Metaheuristic.parameters()`** returns the arguments of the constructor of a metaheuristic
  with the values it holds, the configuration of a run. The report of a run lists them all,
  such as the mutation rate and the tournament size of a genetic algorithm or the tabu size of
  hill climbing. `Memetic` keeps its `max_iterations` under that name; `max_generations` still
  reads it.

### Changes

- **A fitness function that returns NaN**: the value counts as the worst one, infinity, so
  it never stays as the best solution or the best model of a run, and the first one is logged
  as a warning.
- **A checkpoint of another run** is refused: `run()` continues from a checkpoint only when it
  was written with the same configuration, the domain, the seed and the parameters, and
  otherwise raises a `ValueError` naming what differs.
- **A second `run()`** of the same metaheuristic is a new run: it starts from no best
  solution, no population and an empty curve of bests, and hill climbing from an empty tabu
  list, so it gives what a new object with the same seed gives.
- **A real with a step** draws every point of its grid with the same probability, when it is
  created and when it mutates, so runs over such variables give different results.
- **A real with a step** mutates by at least one step when its alteration limit is narrower
  than the step, as an integer does, so that it moves under `RelativeAlteration(0.2)`, the
  default neighborhood of hill climbing, tabu search, simulated annealing and the memetic
  algorithm and the mutation of GA and SSGA, whatever its step.
- **`TPE`** evaluates and returns only points of the grid of an integer or a real with a step:
  the value its model draws goes to the nearest point of the grid. Variables without a step
  give the same results.
- **`KernelTPE`** proposes only points of the grid of a variable with a step, also when the
  step does not divide the range, as in `define_integer("i", 0, 11, 4)`.
- **Simulated annealing** begins its walk from the best solution evaluated before it, the
  warmup's included, as `warmup_iterations` says, so its seeded runs give different results.
- **Hill climbing** draws `population_size` neighbors every iteration, also on a discrete
  domain where neighbors repeat visited solutions, so its seeded runs on such domains give
  different results.
- **A CVOA strain** runs exactly `pandemic_duration` iterations, as in the original
  implementation of the algorithm. Seeded runs give different results; a run that should
  search as much as before asks for one iteration more.
- **`RandomSearch`** needs a population of at least two, as the genetic algorithms do, and a
  `ValueError` says so when it is given one.

### Performance

The results of a seeded run are the same.

- **Copying a solution** shares its domain definition and its connector with the original
  instead of copying them, as its variables already did. Hill climbing, tabu search,
  simulated annealing, the memetic algorithm and CVOA run faster on a cheap fitness, and what
  a distributed run sends to its workers and a checkpoint writes is smaller.
- **`TPE`** fits its model once per iteration instead of once per candidate, and computes the
  normal density with the operations of SciPy without its generic machinery.
- **`KernelTPE`** scores its candidates in one step per variable, and draws its kernels from a
  cumulative table built once per model.
- **CVOA** keeps the recovered, the dead and the isolated of a pandemic by a key of their
  values rather than as whole solutions, since it only asks whether one is there and how many:
  a long pandemic takes less memory and less time.
- **Log messages** are built only when the log level emits them: with the log off, the
  default, a run spends no time formatting its population every iteration, and CVOA does not
  read the state of the pandemic for a report nobody sees.
- **The crossover of the genetic algorithms** does not copy the children it has just built.

## 1.4.0

MetaGen 1.4.0 adds TriGen and a triclustering package, reports of a run as an HTML page or a PDF,
and keeping and saving the best model a run trained.

### New

- **TriGen**, a genetic algorithm that finds triclusters, blocks of a three-dimensional
  dataset whose values behave alike, one after another, each with a search of its own and
  what it found shaping the searches that follow. `TriGen(cube, ...)` takes the fitness,
  `TriclusterFitness`, as a weighted mean of a quality and of size and overlap terms or,
  with `scoring="significance"`, as how unlikely the coherence of a tricluster is among
  random ones of its size. Each tricluster found grows, gene, condition or time at a
  time, while its fitness does not rise. It also offers:
  - `ordered`, for dimensions whose positions have an order, where a tricluster holds a
    window of consecutive positions;
  - `shape="prism"`, for series of images: a surface of the plane, one piece through its
    neighbors, held along a window of the times, bounded by `pixels`;
  - `stop="coverage"`, to go on until the triclusters hold a share of the genes or of the
    pixels, with `noise_rule` to leave out what is no better than noise and `patience`;
  - `disjoint=True`, triclusters that share no gene or, with prisms, no pixel, which
    segment the plane;
  - `shuffle_genes`, `hierarchy` and `overlap`, for the order of the genes and how what
    was found counts;
  - `save`, a self-describing JSON file that `TriGenResult` reads back, checks against
    the data and runs again, and `report`, an HTML page or a PDF of the run, with the
    biological enrichment of its triclusters when an engine is given.
- **`metagen.triclustering`**, the data and measures of a triclustering, usable on their
  own:
  - `Cube` and `Tricluster`, a set of cells that most often makes up a cube;
  - reading and writing cubes in NetCDF, reading long tables, a matrix per time and GEO
    DataSets, downloading those with `fetch_gds`, and `check` and helpers to prepare
    expression data;
  - the measures MSR3D, LSL and MSL and the qualities GRQ, PEQ, SPQ and TRIQ;
  - the biological quality BIOQ and the functional purity of an enrichment analysis, with
    g:Profiler (`GProfiler`) or a local Gene Ontology (`LocalGO`);
  - synthetic cubes with planted triclusters (`plant`) and prisms (`plant_prisms`), and
    similarities, `recovery` and `relevance` to measure what a search found;
  - `stability`, how much the triclusters of several runs recur, against `null_cube`, a
    cube with nothing to find.
- **Reports of a run**: `report(path)` on any metaheuristic, and
  `metagen.reporting.report` for several runs side by side, write an HTML page or a PDF
  with its parameters, domain, budget, best solution, convergence and cost.
- **The best trained model of a run**: a fitness function may return its value and the
  model it trained, and the run keeps the model of its best evaluation in `best_model`;
  `refit` trains the model of the best solution when the run ends, and `save_best_model`
  writes it in the format of its library.
- **New extras**: `netcdf` (xarray and netCDF4, for NetCDF-4 files) and `report`
  (matplotlib, for the reports).

### Changes

- **GA and SSGA mutate one child in two by default**: `mutation_rate` is 0.5. The memetic
  algorithm keeps 0.1.
- **KernelTPE draws a subset from the model of the best solutions and leaves it out of the
  ratio that ranks its candidates**, which the other variables decide. A domain without
  subsets gives the same results.
- **Distributed slices large enough to work on**: GA and Memetic make slices of at least
  four individuals, SSGA of at least three and RandomSearch of at least two, and a
  population too small for its CPUs is split into fewer slices. Under the global model,
  GA and Memetic return every child they bred, for the driver to select among.
- **TPE under the global model** shares its whole candidate pool among the slices, so an
  iteration costs what it costs sequentially whenever the pool holds at least as many
  candidates as there are CPUs.
- **SA on Ray cools on the driver**: every iteration of a distributed run starts from the
  temperature the run has reached. A sequential run gives the same results.
- **Several strains of CVOA on threads** draw from generators of their own, so what a
  strain draws does not depend on the order the threads run in. A single strain gives the
  same results.
- **CVOA evaluates an infected individual once it enters the population**: the isolated
  and the individuals the pandemic already knows are not evaluated, and every individual
  evaluated, the last generation included, competes for the best. A run follows the same
  pandemic with fewer evaluations, and its best is never worse.
- **A dynamic structure that changes its length** draws every length allowed with the
  same probability, as it does when it is created, so the mutation of a structure gives
  different results.

## 1.3.0

MetaGen 1.3.0 adds a budget of evaluations or seconds to every run, racing to stop the
evaluation of candidates worse than the population, a logarithmic scale for integers and
reals, and starting a run from known solutions.

### New

- **A budget for any run**: every metaheuristic but CVOA takes `max_evaluations`, the
  evaluations of the fitness function a run may make, warmup included, and `timeout`, the
  seconds it may last. Without `max_iterations`, a budget is what stops the run, and the
  metaheuristics that plan over their iterations (SA, TPE, KernelTPE, and HillClimbing with
  a gamma schedule) plan over the iterations `max_evaluations` buys; with both, the first
  reached stops it. The limits are checked between the rounds of the warmup and between
  iterations, so a run goes past one by at most a round of the warmup, the initial
  population or one iteration.
  `evaluations`, `seconds` and `stop_reason` say what a run spent and what stopped it, and
  a run resumed from a checkpoint carries on with what it had spent.
- **Racing**: a fitness function can yield the value of each of its steps, such as the folds
  of a cross-validation, and with `racing=Racing()` every metaheuristic but CVOA stops
  evaluating a candidate as soon as a Friedman test, followed by Conover's comparison, finds
  it significantly worse than the population its iteration started from, as F-race and irace
  do. A candidate stopped early is marked and is never the best of a run, and
  `max_evaluations` counts the steps taken.
- **Logarithmic scale**: `define_real`, `define_integer`, their group variants and
  `set_structure_to_real` / `set_structure_to_integer` take `log=True` for a variable that
  spans orders of magnitude. The solution holds the value itself; the metaheuristics draw,
  mutate, cross and model it on its logarithm. It needs a positive minimum and takes no step.
- **Starting from known solutions**: every metaheuristic but CVOA takes `initial_solutions`,
  mappings from variable names to values, with any variable left out drawn at random. They
  take the place of as many solutions of the initial population, so the cost of a run does
  not change.
- **Distributed runs count the evaluations of their workers**: the history of a run on Ray
  records them, as a sequential run does.

### Changes

- **KernelTPE models on its whole warmup**: every solution its warmup evaluates joins the
  history its model is built on, so a run with a warmup gives different results.
- **HillClimbing with a gamma schedule** evaluates, each iteration, the share of
  `population_size` the schedule gives, split among the slices of a distributed run.

## 1.2.0

MetaGen 1.2.0 adds subsets to the search spaces: a selection of some of a set of elements,
between a minimum and a maximum number of them.

### New

- **Subsets**: `Domain.define_subset(name, elements, min_size=1, max_size=None)` defines
  a selection of some of a set of distinct elements, between a minimum and a maximum
  number of them, read as a list in the order of the elements and settable from a list,
  a tuple or a set. Mutations add, remove or change one element at a time, drawn among
  the steps the sizes allow; a limit counts steps, and a relative limit is a fraction of
  the maximum size. The genetic algorithms cross subsets at one point: both parents are
  cut at the same share of their length and each child takes the head of one and the
  tail of the other. TPE and KernelTPE model a subset by the probability that each
  element is in. Structures can hold subsets.

### Changes

- **Reading a list value gives a copy**: `solution[name]` on a permutation or a subset returns a new
  list, so changing what was read leaves the solution, and the fitness it carries, as
  they were.

## 1.1.1

MetaGen 1.1.1 imports from any working directory.

### Changes

- **Optional packages are detected by their files**: a directory with the name of an
  optional package and nothing to import, such as the `ray` folder Ray leaves in the
  temporary directory, does not count as the package being installed, so
  `metagen.metaheuristics` imports from any working directory.

## 1.1.0

MetaGen 1.1.0 adds permutations, conditional variables and structures with a range per
position to the search spaces, lets a run be paused and resumed from a checkpoint, and keeps
a history of every run.

### New

- **Permutations**: `Domain.define_permutation(name, elements)` defines an ordering of
  distinct elements, each exactly once, read as a list. Mutations swap positions (a
  limit counts swaps), the genetic algorithms use the order crossover, and TPE and
  KernelTPE resample it from the orderings of the best solutions.
- **Conditional variables**: `Domain.set_condition(name, variable, values)` makes a
  variable active only when another one, an integer or a categorical one, takes one of
  the given values. While inactive, `solution[name]` is `None`, a printed solution shows
  it as `None (inactive)` and `Solution.is_active(name)` is `False`; the metaheuristics
  do not mutate it, two solutions that differ only in it are equal, and TPE and
  KernelTPE model it only from the solutions in which it was active.
- **Structures with a definition per position**: `Domain.set_structure_to_variables(name,
  variables)` gives each position of a static or dynamic structure its own definition,
  taken from already defined variables, one per position. Every position is drawn,
  mutated, checked and recombined against its own definition, and a dynamic structure
  grows and shrinks at its end. All the metaheuristics support it.
- **Pausing and resuming a run**: every metaheuristic but CVOA takes `checkpoint` and
  `checkpoint_every`, saves its state to that file every so many iterations, and
  continues from it when `run()` starts; `resume(path, fitness_function)` rebuilds it in
  another process, and `request_stop()` ends a run after the iteration in progress,
  saving it. A continued run reaches the result of an uninterrupted one.
- **Run history**: every metaheuristic keeps one record per iteration in `history`
  (evaluations, seconds, best so far, best, mean, standard deviation and worst of the
  population, its size and the best solution), and the `history` parameter writes them
  to a JSON Lines file as the run goes.
- **`infection_alteration_limit`** in `StrainProperties`: how far a CVOA infection moves
  each variable it changes, as a `RelativeAlteration`, an absolute amount or `None` (the
  default, which draws the variable over its whole domain).

### Changes

- **Integer neighborhoods**: an integer mutated within a limit, absolute or
  `RelativeAlteration`, draws from the grid points on both sides of its value alike,
  and reaches at least one step, so a two-valued integer always flips and a narrow
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
