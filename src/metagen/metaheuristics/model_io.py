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
from typing import Any

# The saving of a model in the format of its library, out of tools.py (OF-12 of the
# independent audit); tools re-exports it.


def save_model(model: Any, path: str) -> str:
    """
    Write a trained model to a file in the format of the library it comes from: a model
    of Keras or TensorFlow with its own ``save``, to a ``.keras`` file; one of PyTorch with
    ``torch.save``; any other with ``joblib`` when it is installed, as scikit-learn
    recommends for its models, and with ``pickle`` otherwise. It is written aside and then
    renamed over, so a model that cannot be saved leaves no file behind and a file already
    there as it was.

    :param model: The model.
    :type model: Any
    :param path: The file. For Keras, ``.keras`` is added if it does not end so.
    :type path: str
    :return: The file written.
    :rtype: str
    :raises ValueError: if the model cannot be saved so, as one of a library none of those
        formats can hold.
    """
    import os
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    # From the classes it inherits from too: a network of PyTorch or of Keras is most often
    # a class of the user's own, built on torch.nn.Module or keras.Model.
    libraries = {cls.__module__.split(".")[0] for cls in type(model).__mro__}
    library = ("keras" if libraries & {"keras", "tensorflow", "tf_keras"} and hasattr(model, "save")
               else "torch" if "torch" in libraries else None)
    if library == "keras" and not path.endswith(".keras"):
        path += ".keras"
    root, extension = os.path.splitext(path)
    temporary = f"{root}.partial{extension}"
    how = {"keras": "its own save", "torch": "torch.save"}.get(library or "", "joblib")
    try:
        if library == "keras":
            model.save(temporary)
        elif library == "torch":
            import torch
            torch.save(model, temporary)
        else:
            try:
                import joblib
            except ImportError:
                import pickle
                how = "pickle"
                with open(temporary, "wb") as handle:
                    pickle.dump(model, handle)
            else:
                how = "joblib"
                joblib.dump(model, temporary)
    except Exception as error:
        if os.path.exists(temporary):
            os.remove(temporary)
        kind = f"{type(model).__module__}.{type(model).__qualname__}"
        raise ValueError(f"The model, a {kind}, cannot be saved with {how}: {error}. It is not lost: save it "
                         f"with the method of its library.") from error
    os.replace(temporary, path)
    return path
