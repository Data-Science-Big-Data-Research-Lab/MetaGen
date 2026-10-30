"""
The report of a run: an HTML page with everything in it, or a PDF, made from what the run
recorded. Needs matplotlib, the ``report`` extra.
"""
import re
import sys

import pytest

pytest.importorskip("matplotlib")

from metagen.framework import Domain  # noqa: E402
from metagen.metaheuristics import GA, TPE, GAConnector, RandomSearch  # noqa: E402
from metagen.reporting import report  # noqa: E402


def _domain(connector=None) -> Domain:
    domain = Domain(connector) if connector is not None else Domain()
    domain.define_real("rate", 0.01, 10.0, log=True)
    domain.define_integer("n", 1, 20)
    domain.define_categorical("kind", ["a", "b", "c"])
    domain.define_categorical("limited", ["no", "yes"])
    domain.define_integer("depth", 2, 12)
    domain.set_condition("depth", "limited", ["yes"])
    return domain


def _fitness(solution) -> float:
    depth = 0 if solution["limited"] == "no" else abs(solution["depth"] - 5) / 10
    return (solution["rate"] - 1) ** 2 + abs(solution["n"] - 7) / 5 + (0 if solution["kind"] == "b" else 0.3) + depth


def _ga(seed=0):
    run = GA(_domain(GAConnector()), _fitness, population_size=8, max_iterations=5, seed=seed)
    run.run()
    return run


def test_the_report_of_a_run_holds_the_run_the_domain_the_best_solution_and_three_figures(tmp_path):
    run = _ga()
    path = run.report(str(tmp_path / "run.html"))
    page = open(path, encoding="utf-8").read()
    assert page.startswith("<!doctype html>") and "<title>GA</title>" in page
    for text in ("population_size", "criterion", "logarithmic scale", "only when limited is yes",
                 f"{run.history[-1]['best']:.6g}"):
        assert text in page
    for name, value in run.history[-1]["best_solution"].items():
        assert name in page
    # The convergence, the trajectory of the best solution and the cost of each iteration
    assert page.count("<svg") == 3 and page.count("<figure>") == 3
    # Self-contained: nothing loaded from elsewhere
    assert not re.search(r"<(script|link|img)[^>]*(src|href)=", page)


def test_a_conditional_variable_never_active_is_named_and_not_plotted(tmp_path):
    run = _ga()
    if any(record["best_solution"]["depth"] is not None for record in run.history):
        pytest.skip("this run activated the conditional variable")
    page = open(run.report(str(tmp_path / "run.html")), encoding="utf-8").read()
    assert "never active in it, so not shown: depth" in page


def test_several_runs_are_compared_and_each_reported(tmp_path):
    first, second = _ga(0), _ga(1)
    tpe = TPE(_domain(), _fitness, warmup_iterations=1, population_size=8, candidate_pool_size=4, max_iterations=5,
              seed=0)
    tpe.run()
    page = open(report([first, second, tpe], str(tmp_path / "runs.html"), title="Three runs"),
                encoding="utf-8").read()
    assert "<title>Three runs</title>" in page and "<h2>Runs</h2>" in page
    for label in ("GA 1", "GA 2", "TPE"):
        assert f"<h2>{label}</h2>" in page
    assert page.count("<svg") == 1 + 3 * 3
    labelled = open(report([first, tpe], str(tmp_path / "labelled.html"), labels=["mine", "theirs"]),
                    encoding="utf-8").read()
    assert "<h2>mine</h2>" in labelled and "<h2>theirs</h2>" in labelled


def test_the_report_can_be_a_pdf(tmp_path):
    path = report([_ga(0), _ga(1)], str(tmp_path / "runs.pdf"))
    content = open(path, "rb").read()
    assert content.startswith(b"%PDF") and content.count(b"/Type /Page") - content.count(b"/Type /Pages") >= 3


def test_a_run_stopped_before_its_first_iteration_is_reported_without_figures(tmp_path):
    run = RandomSearch(_domain(), _fitness, population_size=10, max_evaluations=5, seed=0)
    run.run()
    assert run.history == [] and run.stop_reason == "max_evaluations"
    page = open(run.report(str(tmp_path / "run.html")), encoding="utf-8").read()
    assert "max_evaluations" in page and "<svg" not in page


@pytest.mark.parametrize("problem, message", [("not run", "has not run"), ("extension", ".html or a .pdf"),
                                              ("labels", "one label per run")])
def test_what_cannot_be_reported_is_refused(tmp_path, problem, message):
    run = _ga() if problem != "not run" else GA(_domain(GAConnector()), _fitness, max_iterations=2, seed=0)
    with pytest.raises(ValueError, match=message):
        if problem == "labels":
            report([run], str(tmp_path / "run.html"), labels=["a", "b"])
        else:
            report(run, str(tmp_path / ("run.txt" if problem == "extension" else "run.html")))


def test_without_matplotlib_the_report_says_how_to_get_it(tmp_path, monkeypatch):
    run = _ga()
    monkeypatch.setitem(sys.modules, "matplotlib", None)
    with pytest.raises(ImportError, match=r"pymetagen-datalabupo\[report\]"):
        run.report(str(tmp_path / "run.html"))
