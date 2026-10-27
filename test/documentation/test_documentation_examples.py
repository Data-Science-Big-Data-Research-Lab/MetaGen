"""The examples of the documentation run as written. Each page's code blocks run in order
in one namespace, since a page builds on its earlier blocks, in a scratch directory. A line
the page marks with a ``# ValueError`` comment has to raise it."""
import re
import signal
import textwrap
from pathlib import Path

import pytest

from metagen.framework import Domain

DOCS = Path(__file__).resolve().parents[2] / "docs" / "source"


def _blocks(text: str):
    return [textwrap.dedent(match.group(1)).strip("\n")
            for match in re.finditer(r"\.\. code-block:: python\n((?:\n|[ \t]+.*\n)+)", text)]


def _expecting_errors(code: str) -> str:
    """Turn every line marked ``# ValueError`` into a check that it raises it."""
    lines = []
    for line in code.splitlines():
        if re.search(r"#\s*ValueError", line):
            indent = line[:len(line) - len(line.lstrip())]
            statement = line.split("#")[0].strip()
            lines += [f"{indent}try:", f"{indent}    {statement}",
                      f"{indent}except ValueError:", f"{indent}    pass",
                      f"{indent}else:", f"{indent}    raise AssertionError({statement!r} + ' did not raise')"]
        else:
            lines.append(line)
    return "\n".join(lines)


def _run(blocks, before=None):
    namespace = {}
    for index, code in enumerate(blocks):
        if before and index in before:
            before[index](namespace)
        exec(compile(_expecting_errors(code), f"block {index}", "exec"), namespace)
    return namespace


GPROFILER_ANSWERS = Path(__file__).parent.parent / "triclustering" / "data" / "gprofiler_answers.json"


def _answer_gprofiler_from_records(monkeypatch):
    """The examples that ask g:Profiler get the answer it gave when they were written, so
    they run without a connection and print the same.

    To record them again, after changing an example or to refresh the annotations, run
    ``METAGEN_RECORD_GPROFILER=1 pytest test/documentation -k triclustering_page`` with a
    connection: it asks g:Profiler for real and rewrites the file of answers. Then update
    the output written in the comments of the example to what it prints.
    """
    import hashlib
    import json
    import os
    import metagen.triclustering.enrichment as enrichment
    answers = json.loads(GPROFILER_ANSWERS.read_text())
    real = enrichment._post

    def recorded(url, body, timeout):
        key = hashlib.sha256(body).hexdigest()
        if os.environ.get("METAGEN_RECORD_GPROFILER"):
            answer = real(url, body, timeout)
            answers.clear()
            answers[key] = {"result": [{field: result[field] for field in
                                        ("native", "name", "p_value", "intersection_size", "term_size")}
                                       for result in answer["result"]],
                            "meta": {"version": answer["meta"]["version"]}}
            GPROFILER_ANSWERS.write_text(json.dumps(answers, indent=1))
        assert key in answers, ("An example asks g:Profiler something not recorded: record its answer "
                                "(see _answer_gprofiler_from_records).")
        return answers[key]

    monkeypatch.setattr(enrichment, "_post", recorded)


def _serve_gds_from_a_small_copy(monkeypatch):
    """The examples that download a GEO DataSet get a small copy with its factors, so they
    run without a connection."""
    import gzip
    import metagen.triclustering.data as data

    def download(url, path, timeout):
        samples = [f"GSM{index}" for index in range(32)]
        lines = ["^DATASET = GDS4510"]
        groups = [("genotype/variation", "wild type", samples[:16]), ("genotype/variation", "rd1", samples[16:])]
        groups += [("age", f"postnatal day {day}", [s for i, s in enumerate(samples) if (i % 16) // 4 == step])
                   for step, day in enumerate((2, 4, 6, 8))]
        for index, (kind, description, members) in enumerate(groups):
            lines += [f"^SUBSET = GDS4510_{index}", f"!subset_description = {description}",
                      "!subset_sample_id = " + ",".join(members), f"!subset_type = {kind}"]
        lines += ["!dataset_table_begin", "\t".join(["ID_REF", "IDENTIFIER"] + samples)]
        lines += ["\t".join([f"{g}_at", f"Gene{g}"] + ["1.0"] * 32) for g in range(3)] + ["!dataset_table_end"]
        with gzip.open(path, "wt") as handle:
            handle.write("\n".join(lines) + "\n")

    monkeypatch.setattr(data, "_download", download)


@pytest.fixture
def scratch(tmp_path, monkeypatch):
    """A scratch directory, and the process left as the page found it: the logging page
    turns MetaGen's logger on, and the pausing page installs a signal handler."""
    monkeypatch.chdir(tmp_path)
    _answer_gprofiler_from_records(monkeypatch)
    _serve_gds_from_a_small_copy(monkeypatch)
    # MetaGen's own logger, not logging.getLogger("metagen_logger"): asked for by name
    # before MetaGen creates it, logging would hand MetaGen a plain Logger.
    from metagen.logging.metagen_logger import metagen_logger as logger
    level, handlers = logger.level, list(logger.handlers)
    user_signal = signal.getsignal(signal.SIGUSR1) if hasattr(signal, "SIGUSR1") else None
    yield tmp_path
    for handler in list(logger.handlers):
        if handler not in handlers:
            logger.removeHandler(handler)
            handler.close()
    logger.setLevel(level)
    if user_signal is not None:
        signal.signal(signal.SIGUSR1, user_signal)


@pytest.fixture
def short_searches(monkeypatch):
    """The examples that tune a model run with the smallest budget a random search takes:
    what is checked is that their code runs, not what it finds."""
    import metagen.metaheuristics as metaheuristics

    class ShortRandomSearch(metaheuristics.RandomSearch):
        def __init__(self, *args, **kwargs):
            kwargs.setdefault("population_size", 2)
            kwargs.setdefault("max_iterations", 1)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(metaheuristics, "RandomSearch", ShortRandomSearch)


@pytest.mark.parametrize("page", [
    "domain/domain.rst",
    "metagen_in_action/working_with_solutions.rst",
    "choosing/index.rst",
    "triclustering/index.rst",
    "index.rst",
    "advanced_topics/interface.rst",
    "metaheuristics/tpe.rst",
    "metagen_in_action/duc/rs.rst",
    "metagen_in_action/duc/sa.rst",
    "metagen_in_action/suc/index.rst",
])
def test_the_examples_of_the_page_run(page, scratch):
    blocks = _blocks((DOCS / page).read_text())
    assert blocks
    _run(blocks)


@pytest.mark.parametrize("page", ["advanced_topics/extending_framework.rst", "advanced_topics/framework.rst"])
def test_the_pages_written_as_one_script_run_as_one(page, scratch):
    # Their first block holds the imports of the whole page, `from __future__ import
    # annotations` among them, which only reaches the code compiled with it.
    blocks = _blocks((DOCS / page).read_text())
    assert blocks
    exec(compile("\n\n".join(blocks), page, "exec"), {})


def test_the_metaheuristic_types_page_prints_what_it_says(scratch):
    namespace = {}
    for code in _blocks((DOCS / "advanced_topics" / "metaheuristic_types.rst").read_text()):
        _printed_as_commented(code, namespace)


@pytest.mark.parametrize("page, needs", [("metagen_in_action/suc/scikit-learn.rst", "sklearn"),
                                         ("metagen_in_action/suc/tensorflow.rst", "tensorflow")])
def test_the_examples_that_tune_a_model_run(page, needs, scratch, short_searches):
    pytest.importorskip(needs)
    _run(_blocks((DOCS / page).read_text()))


def _import_the_distributed_launcher_with(ray: str):
    """Import the launcher in a new process, with ``sys.modules["ray"]`` set to ``ray``."""
    import subprocess
    import sys
    code = textwrap.dedent(f"""
        import importlib.machinery, sys, types
        sys.modules["ray"] = {ray}
        from metagen.metaheuristics.cvoa.distributed_launcher import distributed_cvoa_launcher
        print(bool(distributed_cvoa_launcher.__doc__))
    """)
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)


def test_the_reference_documents_the_distributed_launcher_with_ray_mocked():
    # The documentation is built with Ray mocked: a module with no file, as Sphinx makes it
    done = _import_the_distributed_launcher_with(
        'types.ModuleType("ray"); sys.modules["ray"].remote = lambda f: f; '
        'sys.modules["ray"].__spec__ = importlib.machinery.ModuleSpec("ray", None)')
    assert done.returncode == 0 and done.stdout.strip() == "True", done.stderr


def test_without_ray_the_distributed_launcher_says_so():
    done = _import_the_distributed_launcher_with("None")
    assert done.returncode != 0 and "Ray is not installed" in done.stderr


@pytest.mark.parametrize("page", ["distributed_execution/distributed.rst", "distributed_execution/special.rst"])
def test_the_distributed_pages_run_on_ray(page, scratch):
    pytest.importorskip("ray")
    _run(_blocks((DOCS / page).read_text()))


def test_the_performance_tracking_examples_run(scratch):
    pytest.importorskip("pandas")
    blocks = _blocks((DOCS / "performance_tracking" / "index.rst").read_text())
    namespace = _run(blocks)
    assert list(namespace["table"]["iteration"]) == list(range(len(namespace["algorithm"].history)))


def test_the_pausing_and_resuming_examples_run(scratch):
    if not hasattr(signal, "SIGUSR1"):
        pytest.skip("the example uses a POSIX signal")
    blocks = _blocks((DOCS / "pausing_and_resuming" / "index.rst").read_text())

    def stop_a_run_to_resume(namespace):
        # The resume example continues a run that was stopped: stop one here.
        algorithm = namespace["GA"](namespace["domain"], namespace["fitness_function"],
                                    max_iterations=50, seed=0, checkpoint="runs/ga.ckpt")
        fitness = namespace["fitness_function"]

        def stopping(solution):
            if algorithm.current_iteration >= 3:
                algorithm.request_stop()
            return fitness(solution)

        algorithm.fitness_function = stopping
        algorithm.run()

    namespace = _run(blocks, before={1: stop_a_run_to_resume})
    assert namespace["best_solution"].get_fitness() < 1e-3


@pytest.mark.parametrize("method", ["set_structure_to_variables", "set_condition", "define_permutation",
                                    "define_subset"])
def test_the_examples_of_the_domain_docstrings_run(method, scratch):
    blocks = _blocks(getattr(Domain, method).__doc__.replace("\n        ", "\n"))
    assert blocks
    _run(blocks)


def _printed_as_commented(code: str, namespace: dict) -> None:
    """Run the code and check that every ``print(...)  # value`` prints that value."""
    import contextlib
    import io
    expected = [line.split("#", 1)[1].strip() for line in code.splitlines()
                if line.lstrip().startswith("print(") and "#" in line]
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(compile(code, "example", "exec"), namespace)
    printed = output.getvalue().splitlines()
    assert [line for line, _ in zip(printed, expected)] == expected[:len(printed)]
    assert len(printed) >= len(expected)


@pytest.mark.parametrize("name", ["Cube", "Cube.without_missing", "Cube.from_netcdf", "data.read_long", "data.read_slices", "data.drop_genes", "data.collapse_genes", "data.rename_genes", "data.check", "data.read_gds", "data.fetch_gds", "Tricluster", "msr3d", "msl", "lsl",
                                  "grq", "peq", "spq", "triq", "bioq", "purity", "cell_jaccard", "recovery",
                                  "plant", "null_cube", "stability"])
def test_the_examples_of_the_triclustering_docstrings_run_and_print_what_they_say(name, scratch):
    import metagen.triclustering as triclustering
    target = triclustering
    for part in name.split("."):
        target = getattr(target, part)
    blocks = _blocks(textwrap.dedent("\n".join(target.__doc__.splitlines()[1:])))
    assert blocks
    for code in blocks:
        _printed_as_commented(code, {})


@pytest.mark.parametrize("name", ["TriGen", "TriGenResult", "TriclusterFitness"])
def test_the_examples_of_the_trigen_docstrings_run_and_print_what_they_say(name, scratch):
    import metagen.metaheuristics as metaheuristics
    blocks = _blocks(textwrap.dedent("\n".join(getattr(metaheuristics, name).__doc__.splitlines()[1:])))
    assert blocks
    for code in blocks:
        _printed_as_commented(code, {})


def test_the_trigen_page_prints_what_it_says(scratch):
    for code in _blocks((DOCS / "metaheuristics" / "trigen.rst").read_text()):
        _printed_as_commented(code, {})


def test_the_triclustering_page_prints_what_it_says(scratch):
    for code in _blocks((DOCS / "triclustering" / "index.rst").read_text()):
        _printed_as_commented(code, {})
