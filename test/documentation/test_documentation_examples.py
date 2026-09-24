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


@pytest.fixture
def scratch(tmp_path, monkeypatch):
    """A scratch directory, and the process left as the page found it: the logging page
    turns MetaGen's logger on, and the pausing page installs a signal handler."""
    monkeypatch.chdir(tmp_path)
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


@pytest.mark.parametrize("page", [
    "domain/domain.rst",
    "metagen_in_action/working_with_solutions.rst",
    "choosing/index.rst",
])
def test_the_examples_of_the_page_run(page, scratch):
    blocks = _blocks((DOCS / page).read_text())
    assert blocks
    _run(blocks)


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


@pytest.mark.parametrize("method", ["set_structure_to_variables", "set_condition", "define_permutation"])
def test_the_examples_of_the_domain_docstrings_run(method, scratch):
    blocks = _blocks(getattr(Domain, method).__doc__.replace("\n        ", "\n"))
    assert blocks
    _run(blocks)
