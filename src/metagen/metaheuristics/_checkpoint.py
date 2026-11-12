"""
    Copyright (C) 2023 David Gutierrez Avilés and Manuel Jesús Jiménez Navarro

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from __future__ import annotations

import os
import pickle
import warnings
from importlib import metadata
from typing import TYPE_CHECKING, Any, Dict, Optional, cast

from metagen.framework import Domain
from metagen.framework import rng as rng_state
from metagen.metaheuristics.import_helper import is_package_installed

if is_package_installed("tensorboard"):
    from metagen.logging.tensorboard_logger import TensorBoardLogger

if TYPE_CHECKING:
    from metagen.logging.tensorboard_logger import TensorBoardLogger as _Logger


#: What a checkpoint does not keep: the fitness function, which may be a lambda or a
#: nested function and cannot be pickled, the TensorBoard writer, and where and how
#: often to save, which the resumed run is given again.
_NOT_CHECKPOINTED = frozenset({"fitness_function", "logger", "checkpoint", "checkpoint_every",
                               "_stop_requested", "refit"})

#: What is not configuration: the state of a run, and where to write. A checkpoint keeps
#: a description of everything else, and a run with another configuration is not
#: continued from it.
_NOT_CONFIGURATION = _NOT_CHECKPOINTED | frozenset({
    "_configuration", "current_iteration", "best_solution", "current_solutions", "best_solution_fitnesses",
    "history", "_evaluations", "_steps", "_seconds", "best_model", "_best_model_value", "_step_count",
    "stop_reason", "log_dir", "history_file"})

def _package_version() -> str:
    try:
        return metadata.version("pymetagen-datalabupo")
    except metadata.PackageNotFoundError:
        return "unknown"


class _Checkpointing:
    """
    What a metaheuristic does to save its state to a checkpoint file and to come back to
    it: the private half of :py:meth:`~metagen.metaheuristics.Metaheuristic.resume` and of
    a ``run()`` with a ``checkpoint``. It is a part of :py:class:`~metagen.metaheuristics.Metaheuristic`
    and holds no state of its own: what it saves and restores are the attributes of the
    metaheuristic.
    """
    # Moved out of base.py, which held the whole life of a run in one class of 1200 lines
    # (O-04, metagen-auditoria/auditoria-independiente-2026-11/organizacion.md). The
    # bodies are as they were.

    checkpoint: Optional[str]
    checkpoint_every: int
    log_dir: Optional[str]
    logger: Optional["_Logger"]
    best_model: Any

    def _checkpoint_state(self) -> Dict[str, Any]:
        """
        What a checkpoint holds: the algorithm's attributes but the ones in
        ``_NOT_CHECKPOINTED``, the state of both generators, the class, the version of
        the package and the TensorBoard run, so that its curves continue in the same
        directory. A subclass whose state is not all in its attributes extends it.
        """
        attributes = {name: value for name, value in self.__dict__.items() if name not in _NOT_CHECKPOINTED}
        if self.best_model is not None:
            try:
                pickle.dumps(self.best_model)
            except Exception as error:
                # A model the checkpoint cannot hold is left out, not the checkpoint: a run
                # resumed from it keeps the best model it finds from then on.
                warnings.warn(f"The best model cannot be saved in the checkpoint ({error}); it is left out.",
                              RuntimeWarning, stacklevel=2)
                attributes["best_model"], attributes["_best_model_value"] = None, None
        return {
            "version": _package_version(),
            "class": type(self),
            "algorithm": attributes,
            "rng": rng_state.get_state(),
            "checkpoint_every": self.checkpoint_every,
            "tensorboard_run": self.logger.run_id if self.logger else None,
        }

    def _describe_configuration(self) -> Dict[str, str]:
        """
        The configuration of the run, as text: every attribute but the state of a run and
        where to write (``_NOT_CONFIGURATION``), the domain by its definitions and any
        other value by its representation, or by its type when that only says where it is
        in memory.
        """
        described: Dict[str, str] = {}
        for name, value in sorted(self.__dict__.items()):
            if name in _NOT_CONFIGURATION:
                continue
            text = str(value) if isinstance(value, Domain) else repr(value)
            described[name] = type(value).__qualname__ if " at 0x" in text else text
        return described

    def _check_configuration(self, state: Dict[str, Any]) -> None:
        """
        Refuse to continue, from a checkpoint, a run with another configuration than this
        one. A metaheuristic that already ran, or that :py:meth:`resume` rebuilt, holds
        the run of the checkpoint and is not checked; nor is a checkpoint that holds no
        description of its configuration.

        :raises ValueError: if the configurations differ, naming what differs.
        """
        # Only the class and the version were checked, and the attributes of the
        # checkpoint then replaced the domain, the seed and the parameters given: a new
        # experiment that found an old file at its path went on with the old one, and
        # returned a solution of another domain without a word (F-64).
        saved = state["algorithm"].get("_configuration")
        # A checkpoint of another class is refused by _restore, saying so.
        if saved is None or "_configuration" in self.__dict__ or state["class"] is not type(self):
            return
        current = self._describe_configuration()
        differ = sorted(name for name in saved.keys() | current.keys() if saved.get(name) != current.get(name))
        if differ:
            raise ValueError(f"The checkpoint {self.checkpoint} belongs to another run: {', '.join(differ)} "
                             f"differ. Remove it, or give this run another checkpoint file, to start this run; "
                             f"to continue the one it holds, use resume().")

    def _restore(self, state: Dict[str, Any]) -> None:
        """
        Put the algorithm back in the state of a checkpoint: the inverse of
        :py:meth:`_checkpoint_state`.
        """
        if state["class"] is not type(self):
            raise ValueError(f"The checkpoint {self.checkpoint} is of {state['class'].__name__}, "
                             f"not of {type(self).__name__}.")
        self.__dict__.update(state["algorithm"])
        rng_state.set_state(state["rng"])
        if self.log_dir is not None and is_package_installed("tensorboard"):
            if self.logger:
                self.logger.close()
            self.logger = TensorBoardLogger(log_dir=self.log_dir, run_id=state["tensorboard_run"])

    def _write_checkpoint(self) -> None:
        """
        Write the checkpoint atomically: to a temporary file in the same directory,
        synced to disk, then renamed over the previous one, so that a cut while
        writing leaves the previous checkpoint whole.
        """
        path = cast(str, self.checkpoint)
        directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(directory, exist_ok=True)
        temporary = path + ".tmp"
        with open(temporary, "wb") as handle:
            pickle.dump(self._checkpoint_state(), handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)

    @staticmethod
    def _read_checkpoint(path: str) -> Dict[str, Any]:
        with open(path, "rb") as handle:
            state: Dict[str, Any] = pickle.load(handle)
        if state.get("version") != _package_version():
            raise ValueError(f"The checkpoint {path} was written by version {state.get('version')} "
                             f"of the package and this is version {_package_version()}.")
        return state
