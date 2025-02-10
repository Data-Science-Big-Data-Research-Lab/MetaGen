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
import pathlib

from metagen.framework import Domain
from metagen.framework.solution.devsolution import DevSolution as Solution

def str_to_bool(value: str) -> bool:
    """Convierte una cadena a un valor booleano."""
    return value.lower() in ("true", "1", "yes")

def safe_int(value: str) -> int:
    """Convierte valores '-' o en blanco a un entero predeterminado."""
    return int(value) if value.strip() and value != '-' else 0

def safe_float(value: str) -> float:
    """Convierte valores '-' o en blanco a un flotante predeterminado."""
    return float(value) if value.strip() and value != '-' else 0.0

def safe_str(value: str) -> str:
    """Convierte valores '-' a una cadena vacía."""
    return value if value.strip() and value != '-' else ""

def safe_str_to_bool(value: str) -> bool:
    """Convierte valores '-' a False."""
    return str_to_bool(value) if value.strip() and value != '-' else False

def metaheuristic_parameters_resource_path(file_name: str) -> str:
    """Devuelve la ruta absoluta al archivo en la carpeta test_parameters."""
    return (pathlib.Path(__file__).parents[1] / "test" / "test_parameters" / "metaheuristic_parameters" / file_name).as_posix()

def framework_parameters_resource_path(file_name: str) -> str:
    """Devuelve la ruta absoluta al archivo en la carpeta test_parameters."""
    return (pathlib.Path(__file__).parents[1] / "test" / "test_parameters" / "framework_parameters" / file_name).as_posix()


domain: Domain = Domain()
domain.define_integer("I", 0, 100)
domain.define_real("R", 0.0, 1.0)
domain.define_categorical("C", ["C1", "C2", "C3", "C4"])
domain.define_group("L")
domain.define_integer_in_group("L", "EI", 0, 100)
domain.define_real_in_group("L", "ER", 0., 1.0)
domain.define_categorical_in_group("L", "EC", ["C1", "C2", "C3", "C4"])

domain.define_static_structure("SSI", 10)
domain.set_structure_to_integer("SSI", -5, 10)
domain.define_static_structure("SSR", 20)
domain.set_structure_to_real("SSR", 0.0, 1.)
domain.define_static_structure("SSC", 100)
domain.set_structure_to_categorical("SSC", ["V1", "V2", "V3"])
domain.define_static_structure("SSL", 2)
domain.define_group("L2")
domain.define_integer_in_group("L2", "EI2", 0, 100)
domain.define_real_in_group("L2", "ER2", 0., 1.0)
domain.define_categorical_in_group("L2", "EC2", ["C1", "C2", "C3", "C4"])
domain.set_structure_to_variable("SSL", "L2")

domain.define_dynamic_structure("DSI", 10, 100)
domain.set_structure_to_integer("DSI", 1, 10)
domain.define_dynamic_structure("DSR", 1, 10)
domain.set_structure_to_real("DSR", 0.0, 1.)
domain.define_dynamic_structure("DSC", 10, 15)
domain.set_structure_to_categorical("DSC", ["V1", "V2", "V3"])
domain.define_dynamic_structure("DSL", 2, 4)
domain.define_group("L2")
domain.define_integer_in_group("L2", "EI2", 0, 100)
domain.define_real_in_group("L2", "ER2", 0., 1.0)
domain.define_categorical_in_group("L2", "EC2", ["C1", "C2", "C3", "C4"])
domain.set_structure_to_variable("DSL", "L2")

solution = Solution(domain)