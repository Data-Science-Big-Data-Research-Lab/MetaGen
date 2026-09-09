"""Behavioral tests: every metaheuristic must actually optimize.

The rest of the metaheuristic suite only checks that a run returns something. An
algorithm can be thoroughly broken and still satisfy that, which is what P-05
objects to. These tests check the properties that make an optimizer an optimizer:

1. the best-fitness history never gets worse;
2. the returned solution is the best one the run ever saw;
3. the run ends better than it started;
4. it beats spending the very same number of fitness evaluations on random
   sampling.

Every run is seeded, so the outcome is fixed rather than a coin toss, and the
verdicts below are ratios over ten seeds instead of single runs.

The problems are the nine of Section 5.1 of the MetaGen paper, the classics of
continuous optimization on their canonical domains, a tenth that tunes a
scikit-learn model, and an eleventh that fits a polynomial of variable degree.
The tenth is there because nine functions of two real variables say nothing
about the case the package is sold on: a hyperparameter domain mixes integers,
categoricals and reals of quite different widths, and findings like F-32 and
F-33 are invisible without one. The eleventh is the only domain with a dynamic
structure, which is what F-31 gave the genetic algorithms a crossover for and
what F-35 found TPE crashes on. Keeping the canonical
domains rather than normalizing them is deliberate, and it is what turned up
F-32: an absolute alteration_limit of 1.0 means something quite different on
[-2.048, 2.048] than on [-600, 600], and the algorithms built around local search
fell below random sampling on the wide domains for exactly that reason. The
default is a fraction of each variable's own range since that finding closed.

Michalewicz has a negative global minimum, about -1.8013 in two dimensions. That
is deliberate too: every property here is relative, so nothing may assume the
optimum sits at zero.

Properties 1 and 2 are structural, and are asked of every algorithm on every
problem: an optimizer that reports an improving history and then hands back
something else is broken whatever the problem, and whatever machine it runs on.
Properties 3 and 4 are statistical -- they compare a count against a fixed
threshold -- and are asked only of the problems whose objective returns the same
number everywhere. That leaves the hyperparameter problem out of them: training a
model is not arithmetic, so its landscape shifts a little with the scikit-learn
version and the processor, and a threshold measured on one machine is a
prediction that only holds there. The pairs that fail them carry an xfail naming
what is responsible.

A pair that crashes outright, rather than scoring badly, fails all four
properties on the crash, under an xfail naming the finding responsible, and the
fixture records the exception instead of letting it take the module down.

Property 4 is not asked of RandomSearch: it *is* random sampling, so tying with
the baseline is the correct outcome and not a defect. Watch its row anyway: it is
the calibration. RandomSearch scoring far from five of ten against itself means
the comparison has stopped measuring, which is what happened when the
hyperparameter objective was accuracy -- 17 distinct values over a thousand
configurations, so ties, which count as wins under <=, carried it to nine.

The whole file takes about a minute, most of it the hyperparameter problem: the
seven algorithms spend some 17000 evaluations per problem and the baseline spends
as many again, so it fits about 34000 model fits into 30 seconds.
"""

import math

import pytest

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed
from metagen.metaheuristics import (GA, SA, SSGA, TPE, GAConnector, HillClimbing,
                                    Memetic, RandomSearch)

SEEDS = tuple(range(10))

# Out of len(SEEDS). Not unanimity: these are stochastic algorithms and an
# occasional bad seed is legitimate. A healthy algorithm sits at 8-10 and a
# broken one at 0-4, so anything in between is a signal rather than noise.
REQUIRED_WINS = 7

ALGORITHMS = ("RandomSearch", "SA", "HillClimbing", "GA", "SSGA", "TPE", "Memetic")


def _sphere(x: float, y: float) -> float:
    return x ** 2 + y ** 2


def _rastrigin(x: float, y: float) -> float:
    return 20 + sum(v ** 2 - 10 * math.cos(2 * math.pi * v) for v in (x, y))


def _rosenbrock(x: float, y: float) -> float:
    return 100 * (y - x ** 2) ** 2 + (1 - x) ** 2


def _ackley(x: float, y: float) -> float:
    return (-20 * math.exp(-0.2 * math.sqrt(0.5 * (x ** 2 + y ** 2)))
            - math.exp(0.5 * (math.cos(2 * math.pi * x) + math.cos(2 * math.pi * y)))
            + math.e + 20)


def _griewank(x: float, y: float) -> float:
    return 1 + (x ** 2 + y ** 2) / 4000 - math.cos(x) * math.cos(y / math.sqrt(2))


def _schwefel(x: float, y: float) -> float:
    return 418.9829 * 2 - sum(v * math.sin(math.sqrt(abs(v))) for v in (x, y))


def _levy(x: float, y: float) -> float:
    w = [1 + (v - 1) / 4 for v in (x, y)]
    return (math.sin(math.pi * w[0]) ** 2
            + (w[0] - 1) ** 2 * (1 + 10 * math.sin(math.pi * w[0] + 1) ** 2)
            + (w[1] - 1) ** 2 * (1 + math.sin(2 * math.pi * w[1]) ** 2))


def _michalewicz(x: float, y: float) -> float:
    # Steepness m = 20 in the exponent, that is the usual m = 10 doubled.
    #
    # A needle in a haystack, and the noisiest column of the benchmark because of
    # it: measured on a 1200x1200 grid the median of the landscape is -0.015 against
    # an optimum of -1.8013, and only 0.43 % of the domain sits below -1.5. Both
    # sides of the random-sampling comparison come down to lucky draws, so its
    # counts swing further between measurements than any other problem's.
    return -sum(math.sin(v) * math.sin((i + 1) * v ** 2 / math.pi) ** 20
                for i, v in enumerate((x, y)))


def _zakharov(x: float, y: float) -> float:
    weighted = 0.5 * 1 * x + 0.5 * 2 * y
    return x ** 2 + y ** 2 + weighted ** 2 + weighted ** 4


class _Problem:
    """A domain to search and an objective to minimize over it.

    A problem carries its own domain rather than the benchmark assuming one, which
    is what lets the hyperparameter problem below sit next to the nine functions:
    its domain mixes integers, a categorical and a real, and none of them is called
    x or y.

    ``reproducible`` says whether the objective returns the same number on every
    machine. The nine functions do: they are arithmetic. Training a model does not
    -- scikit-learn's algorithms change between versions and the arithmetic rounds
    differently on another processor -- so its landscape is not quite the same
    landscape, and the statistical properties, which compare a measured count
    against a fixed threshold, cannot be asserted on it. The structural properties
    can: they look at the algorithm's own bookkeeping, not at what the fitness is
    worth.
    """

    def __init__(self, build_domain, objective, reproducible: bool = True) -> None:
        self.build_domain = build_domain
        self.objective = objective
        self.reproducible = reproducible

    def domain(self, connector=None) -> Domain:
        return self.build_domain(connector)


def _polynomial_fit() -> _Problem:
    """A polynomial of variable degree fitted to a cubic: the dynamic-structure problem.

    The one problem whose domain holds a dynamic structure, which is what F-31 gave
    the genetic algorithms a crossover for. The variable is the list of coefficients,
    between one and eight of them, and the objective is the squared error against a
    fixed cubic on a grid of points plus a small charge per coefficient, so both the
    right length -- four -- and the right values have to be found. Pure arithmetic, so
    it is reproducible on any machine.
    """
    target = [1.0, 0.3, -1.0, 0.5]                    # 1 + 0.3x - x^2 + 0.5x^3
    grid = [-1.0 + 0.1 * i for i in range(21)]
    wanted = [sum(c * x ** k for k, c in enumerate(target)) for x in grid]

    def build_domain(connector):
        domain = Domain(connector=connector) if connector is not None else Domain()
        domain.define_dynamic_structure("coefficients", 1, 8)
        domain.set_structure_to_real("coefficients", -3.0, 3.0)
        return domain

    def objective(solution) -> float:
        coefficients = [c.get() for c in solution["coefficients"]]
        error = sum((sum(c * x ** k for k, c in enumerate(coefficients)) - y) ** 2
                    for x, y in zip(grid, wanted)) / len(grid)
        return error + 0.001 * len(coefficients)

    return _Problem(build_domain, objective)


def _two_reals(low: float, high: float, objective) -> _Problem:
    """A problem over two real variables on the same interval, x and y."""

    def build_domain(connector):
        domain = Domain(connector=connector) if connector is not None else Domain()
        domain.define_real("x", low, high)
        domain.define_real("y", low, high)
        return domain

    return _Problem(build_domain, lambda solution: objective(solution["x"], solution["y"]))


def _decision_tree():
    """Tuning a decision tree, which is what the package is actually for.

    Nine functions of two real variables cannot say anything about the case MetaGen
    is sold on: a hyperparameter domain mixes integers, categoricals and reals, of
    quite different widths, and several findings only bite there. F-32's absolute
    alteration limit and F-33's integer crossover are both invisible on a domain
    that holds nothing but two reals of the same range.

    Deliberately cheap. The published example tunes a 100-tree random forest with
    ten-fold cross validation, which costs 543 ms per evaluation: the benchmark
    spends about 14000 of them per problem, so that would be two hours. A single
    tree on one split costs 1.2 ms and the whole problem fits in about 17 seconds.

    The objective is the log loss, not the accuracy. Accuracy on 90 held-out samples
    takes 17 distinct values over a thousand random configurations, so 14 % of random
    pairs tie -- and since property 4 compares with <=, ties count as wins and
    RandomSearch scored 9 of 10 against itself, which means the property had stopped
    measuring anything. Log loss gives 154 distinct values over a ten times wider
    range, and it already minimizes, which is the direction MetaGen works in.

    Only the structural properties are asked of it, because its landscape is not the
    same landscape on another machine: see _Problem.reproducible. What the statistical
    ones measured here, on 2026-09-08, is worth writing down even though it is no
    longer asserted. Wins against random sampling on the same budget, out of ten
    seeds: HillClimbing 8, Memetic 6, GA 5, RandomSearch 4 against itself, SSGA 4,
    SA 3, TPE 3. The heterogeneous domain sorts the algorithms differently from the
    nine functions, and the signal of this landscape is almost entirely in one
    variable: the best 5 % has min_samples_leaf averaging 7.5 against 20.7 over the
    whole space, while max_depth barely matters. What separates them is whether they
    learn that. Measured by thirds of each run, HillClimbing takes min_samples_leaf
    from 19.1 to 7.0 and the memetic algorithm from 15.4 to 7.7, while TPE only
    reaches 16.3 on more than twice HillClimbing's budget -- and hyperparameter
    search is what TPE exists for.
    """
    from sklearn.datasets import make_classification
    from sklearn.metrics import log_loss
    from sklearn.model_selection import train_test_split
    from sklearn.tree import DecisionTreeClassifier

    features, labels = make_classification(
        n_samples=300, n_features=6, n_informative=4, n_redundant=0,
        random_state=0, shuffle=False)
    train_x, test_x, train_y, test_y = train_test_split(
        features, labels, test_size=0.3, random_state=0)

    def build_domain(connector):
        domain = Domain(connector=connector) if connector is not None else Domain()
        domain.define_integer("max_depth", 1, 20)
        domain.define_integer("min_samples_leaf", 1, 40)
        domain.define_categorical("criterion", ["gini", "entropy", "log_loss"])
        domain.define_real("ccp_alpha", 0.0, 0.05)
        return domain

    def objective(solution) -> float:
        tree = DecisionTreeClassifier(
            max_depth=solution["max_depth"],
            min_samples_leaf=solution["min_samples_leaf"],
            criterion=solution["criterion"],
            ccp_alpha=solution["ccp_alpha"],
            random_state=0)
        tree.fit(train_x, train_y)
        return log_loss(test_y, tree.predict_proba(test_x), labels=[0, 1])

    return _Problem(build_domain, objective, reproducible=False)


# The nine of Section 5.1 of the MetaGen paper, taken from Molga and Smutnicki, on
# their canonical domains. Eight have their global minimum at 0; MICHALEWICZ DOES
# NOT, its minimum is about -1.8013 at (2.20, 1.57) in two dimensions. Nothing here
# assumes a zero optimum -- every property is relative, comparing a run against its
# own start or against random sampling on the same budget -- but anything added
# later must not start assuming it either.
PROBLEMS = {
    "Sphere": _two_reals(-5.12, 5.12, _sphere),
    "Rastrigin": _two_reals(-5.12, 5.12, _rastrigin),
    "Rosenbrock": _two_reals(-2.048, 2.048, _rosenbrock),
    "Ackley": _two_reals(-32.768, 32.768, _ackley),
    "Griewank": _two_reals(-600.0, 600.0, _griewank),
    "Schwefel": _two_reals(-500.0, 500.0, _schwefel),
    "Levy": _two_reals(-10.0, 10.0, _levy),
    "Michalewicz": _two_reals(0.0, math.pi, _michalewicz),
    "Zakharov": _two_reals(-5.0, 10.0, _zakharov),
    "DecisionTree": _decision_tree(),
    "Polynomial": _polynomial_fit(),
}


class _CountingFitness:
    """The objective, counting calls so every algorithm can be charged its own budget."""

    def __init__(self, problem: _Problem) -> None:
        self.problem = problem
        self.evaluations = 0

    def __call__(self, solution) -> float:
        self.evaluations += 1
        return self.problem.objective(solution)


def _build(name: str, problem: _Problem, fitness, seed: int, log_dir: str):
    if name == "RandomSearch":
        return RandomSearch(problem.domain(), fitness, population_size=10,
                            max_iterations=15, seed=seed, log_dir=log_dir)
    if name == "SA":
        return SA(problem.domain(), fitness, max_iterations=15, seed=seed, log_dir=log_dir)
    if name == "HillClimbing":
        return HillClimbing(problem.domain(), fitness, population_size=10,
                            max_iterations=15, seed=seed, log_dir=log_dir)
    if name == "GA":
        return GA(problem.domain(GAConnector()), fitness, population_size=10,
                  max_iterations=15, seed=seed, log_dir=log_dir)
    if name == "SSGA":
        return SSGA(problem.domain(GAConnector()), fitness, population_size=10,
                    max_iterations=15, seed=seed, log_dir=log_dir)
    if name == "TPE":
        return TPE(problem.domain(), fitness, max_iterations=15,
                   warmup_iterations=5, seed=seed, log_dir=log_dir)
    if name == "Memetic":
        return Memetic(problem.domain(GAConnector()), fitness, population_size=10,
                       max_iterations=15, neighbor_population_size=3, seed=seed,
                       log_dir=log_dir)
    raise ValueError(f"unknown algorithm: {name}")


def _best_of_random_sampling(problem: _Problem, evaluations: int, seed: int) -> float:
    """Best of `evaluations` solutions drawn at random: the baseline to beat.

    One solution per point. It was two for a while -- x taken from one and y from
    another -- which drew twice the random numbers for the same distribution. That
    came in when the benchmark widened to six functions and the objectives changed
    from taking a Solution to taking (x, y): the baseline was adapted by calling
    Solution(domain) twice instead of binding it once. Comparisons made against it
    were still fair, since every algorithm faced the same baseline, but the stream
    differed, so undoing it moved the borderline cells and the xfail table was
    recalibrated.
    """
    set_seed(100_000 + seed)
    domain = problem.domain()
    return min(problem.objective(Solution(domain)) for _ in range(evaluations))


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    """Run every algorithm on every function once per seed, and reuse that."""
    log_dir = str(tmp_path_factory.mktemp("behavior"))
    measured = {}
    for function_name, problem in PROBLEMS.items():
        for name in ALGORITHMS:
            rows = []
            for seed in SEEDS:
                fitness = _CountingFitness(problem)
                algorithm = _build(name, problem, fitness, seed, log_dir)
                try:
                    solution = algorithm.run()
                except Exception as error:  # noqa: BLE001 - recorded, asserted below
                    # One pair blowing up must not take the whole module down with
                    # it: the crash is kept and every property of that pair fails
                    # on it, under an xfail naming the finding responsible.
                    rows.append({"error": error})
                    continue
                rows.append({
                    "final": solution.get_fitness(),
                    "history": list(algorithm.best_solution_fitnesses),
                    "evaluations": fitness.evaluations,
                    "random_baseline": _best_of_random_sampling(
                        problem, fitness.evaluations, seed),
                })
            measured[(function_name, name)] = rows
    return measured


# --------------------------------------------------------------------------
# The (function, algorithm) pairs expected to fail a statistical property.
# --------------------------------------------------------------------------

_SA = ("SA is third of the seven overall since F-30 tied the cooling schedule to the "
       "budget and the default neighborhood went from one candidate to five. What it "
       "misses is what a single walking point on 81 evaluations misses: Rosenbrock's "
       "curved valley, deceptive Schwefel, and a hyperparameter domain it cannot walk "
       "smoothly because two of its four variables are integers and one is categorical")

_GA = ("GA clears random sampling overall since F-33 gave its numeric types a "
       "real-coded crossover, but it has no local search, so a valley it must walk "
       "rather than sample defeats it: Rosenbrock, Zakharov's weighted sum and "
       "deceptive Schwefel. On 160 evaluations, blind recombination does not find one")

_SSGA = ("A-01 gave it parent selection and F-33 a crossover that produces new values, "
         "which took it past random sampling overall. What is left is the budget: two "
         "evaluations per iteration make 40 in all, a quarter of GA's and a fifteenth "
         "of the memetic algorithm's. A-05, which used to be blamed here, was refuted")

_DECEPTIVE = ("Schwefel is deceptive: its global optimum sits near the corner of the "
              "domain, at (420.97, 420.97), with a wide field of better-looking local "
              "optima between it and the middle, so a climber that only ever moves "
              "uphill is led away from it. It scores exactly what RandomSearch scores, "
              "6 of 10, which is a tie rather than a defeat. F-32 was blamed here and "
              "is closed; only the memetic algorithm, on 610 evaluations, clears it")

_ZAKHAROV = ("Zakharov couples the variables through a weighted sum raised to the "
             "fourth power, so what makes a solution good is the combination, not "
             "either coordinate on its own. F-33 produced its largest single jump "
             "here, and it still falls short: recombining is not how a coupled valley "
             "gets walked")

_POLYNOMIAL_SA = ("SA walks one point whose structure resizes freely under mutation, "
                  "so on the polynomial problem it drifts through lengths -- 5.7 on "
                  "average against the right 4 -- and 81 evaluations do not settle "
                  "both a length and its coefficients: 5 of 10 against random sampling")

_POLYNOMIAL_SSGA = ("Forty evaluations, the smallest budget of the seven, on a problem "
                    "where a length and its coefficients have to be found together: "
                    "5 of 10 against random sampling")

_TPE = ("TPE models each variable on its own, which suits a separable bowl. Rosenbrock "
        "couples x and y along a curved valley, Rastrigin oscillates faster than the "
        "model resolves and Schwefel is deceptive: 15 iterations of an independent "
        "model beat dice on none of the three")

# Measured, not guessed, and kept per property: a pair can fail one and pass the
# other, so a single shared table would turn the passes into XPASS(strict).
# Only TPE is left here. Every other algorithm, RandomSearch included, improves on
# its own starting point on every problem, which was true of none of them when P-05
# opened.
_IMPROVES_ON_ITS_START = {
    ("Rosenbrock", "TPE"): _TPE,
    ("Schwefel", "TPE"): _TPE,
}

_BEATS_RANDOM = {
    **{("Sphere", n): r for n, r in (("GA", _GA), ("SSGA", _SSGA))},
    **{("Rastrigin", n): r for n, r in (("SSGA", _SSGA), ("TPE", _TPE))},
    **{("Rosenbrock", n): r for n, r in (("SA", _SA), ("GA", _GA), ("SSGA", _SSGA),
                                         ("TPE", _TPE), ("Memetic", _DECEPTIVE))},
    **{("Ackley", n): r for n, r in (("SSGA", _SSGA),)},
    **{("Griewank", n): r for n, r in (("SSGA", _SSGA),)},
    **{("Schwefel", n): r for n, r in (("SA", _SA), ("GA", _GA), ("SSGA", _SSGA),
                                       ("TPE", _TPE), ("HillClimbing", _DECEPTIVE))},
    **{("Levy", n): r for n, r in (("GA", _GA),)},
    **{("Zakharov", n): r for n, r in (("GA", _ZAKHAROV), ("SSGA", _SSGA))},
    **{("Polynomial", n): r for n, r in (("SA", _POLYNOMIAL_SA), ("SSGA", _POLYNOMIAL_SSGA))},
}


_F35 = ("F-35: TPE registers the dynamic structure and crashes on it, IndexError "
        "in TPEStructure.resample, which asks val.get(i) of reference solutions that "
        "may be shorter than itself")

# Pairs known to crash rather than to score badly. They fail every property, so
# they are merged into every table.
_CRASHES = {("Polynomial", "TPE"): _F35}


def _crashed(rows, name, function_name):
    errors = [row["error"] for row in rows if "error" in row]
    assert not errors, f"{name} on {function_name} crashed: {errors[0]!r}"


def _pairs(expected=None, exclude=(), reproducible_only=False):
    """Build the (problem, algorithm) parameter list, marking the known failures.

    ``reproducible_only`` leaves out the problems whose objective is not the same
    number on every machine. It is asked for by the two statistical properties,
    which assert a count against a fixed threshold: a threshold measured here would
    be a prediction that only holds here, and a pair sitting one win from it -- two
    of the six do on the hyperparameter problem -- flips on another machine. Marking
    it either way then breaks one of the two: with the xfail the CI goes red, and
    without it this machine does.
    """
    expected = {**_CRASHES, **(expected or {})}
    parameters = []
    for function_name, problem in PROBLEMS.items():
        if reproducible_only and not problem.reproducible:
            continue
        for name in ALGORITHMS:
            if name in exclude:
                continue
            reason = expected.get((function_name, name))
            marks = [pytest.mark.xfail(reason=reason, strict=True)] if reason else []
            parameters.append(pytest.param(function_name, name, marks=marks,
                                           id=f"{function_name}-{name}"))
    return parameters


@pytest.mark.parametrize("function_name,name", _pairs())
def test_the_best_fitness_history_never_gets_worse(runs, function_name, name):
    """The record of the best solution so far can only improve or stay put."""
    _crashed(runs[(function_name, name)], name, function_name)
    for seed, row in zip(SEEDS, runs[(function_name, name)]):
        history = row["history"]
        worsening = [(i, history[i], history[i + 1])
                     for i in range(len(history) - 1)
                     if history[i + 1] > history[i]]
        assert not worsening, (
            f"{name} on {function_name}, seed {seed}: the best fitness got worse "
            f"at {worsening}"
        )


@pytest.mark.parametrize("function_name,name", _pairs())
def test_the_returned_solution_is_the_best_one_seen(runs, function_name, name):
    """Whatever run() hands back must be the best point of the whole history."""
    _crashed(runs[(function_name, name)], name, function_name)
    for seed, row in zip(SEEDS, runs[(function_name, name)]):
        assert row["final"] == pytest.approx(min(row["history"])), (
            f"{name} on {function_name}, seed {seed}: returned {row['final']} while "
            f"the history reached {min(row['history'])}"
        )


@pytest.mark.parametrize("function_name,name",
                         _pairs(_IMPROVES_ON_ITS_START, reproducible_only=True))
def test_the_run_ends_better_than_it_started(runs, function_name, name):
    """Searching has to pay off: the end of the history beats its beginning."""
    rows = runs[(function_name, name)]
    _crashed(rows, name, function_name)
    improved = sum(1 for row in rows
                   if len(row["history"]) > 1 and row["history"][-1] < row["history"][0])
    assert improved >= REQUIRED_WINS, (
        f"{name} on {function_name} improved on its own starting point in only "
        f"{improved} of {len(SEEDS)} seeds"
    )


@pytest.mark.parametrize("function_name,name",
                         _pairs(_BEATS_RANDOM, exclude=("RandomSearch",),
                                reproducible_only=True))
def test_it_beats_random_sampling_on_the_same_budget(runs, function_name, name):
    """An optimizer must do better than spending its evaluations on dice rolls."""
    rows = runs[(function_name, name)]
    _crashed(rows, name, function_name)
    wins = sum(1 for row in rows if row["final"] <= row["random_baseline"])
    mean = sum(row["final"] for row in rows) / len(SEEDS)
    mean_baseline = sum(row["random_baseline"] for row in rows) / len(SEEDS)
    assert wins >= REQUIRED_WINS, (
        f"{name} on {function_name} beat random sampling in only {wins} of "
        f"{len(SEEDS)} seeds (mean fitness {mean:.4f} against {mean_baseline:.4f} for "
        f"random sampling, on {rows[0]['evaluations']} evaluations)"
    )
