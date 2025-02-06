import numpy as np
import math
from typing import Optional, NamedTuple, Dict, Callable

from metagen.logging.metagen_logger import metagen_logger


class GammaConfig(NamedTuple):
    """
    Configuration for gamma scheduling.

    :param gamma_function: Name of the gamma function to use.
    :param minimum: Minimum value of gamma (used in some functions).
    :param maximum: Maximum value of gamma (used in some functions).
    :param alpha: Exponential decay rate (only for the exponential function).
    """
    gamma_function: str  # Name of the function to use
    minimum: float = 0.1
    maximum: float = 0.3
    alpha: float = 5.0  # Only used for exponential decay

def gamma_linear(iteration: int, max_iterations: int, minimum: float, maximum: float) -> float:
    """
    Linearly decreasing gamma function.

    :param iteration: Current iteration.
    :param max_iterations: Maximum number of iterations.
    :param minimum: Minimum gamma value.
    :param maximum: Maximum gamma value.
    :return: Computed gamma value.
    """
    progress = iteration / max_iterations
    gamma = minimum + (maximum - minimum) * (1 - progress)
    metagen_logger.debug(f"Linear gamma: iteration={iteration}, progress={progress}, gamma={gamma}")
    return gamma

def gamma_exponential(iteration: int, max_iterations: int, minimum: float, maximum: float, alpha: float) -> float:
    """
    Exponential decay gamma function for faster transition from exploration to exploitation.

    :param iteration: Current iteration.
    :param max_iterations: Maximum number of iterations.
    :param minimum: Minimum gamma value.
    :param maximum: Maximum gamma value.
    :param alpha: Decay factor.
    :return: Computed gamma value.
    """
    progress = iteration / max_iterations
    gamma = minimum + (maximum - minimum) * math.exp(-alpha * progress)
    metagen_logger.debug(f"Exponential gamma: iteration={iteration}, progress={progress}, alpha={alpha}, gamma={gamma}")
    return gamma

def gamma_sample_based(num_solutions: int) -> float:
    """
    Sample-based gamma computation (inspired by Optuna's `default_gamma(x)`).

    :param num_solutions: Number of solutions available.
    :return: Computed gamma value.
    """
    gamma = min(int(np.ceil(0.1 * num_solutions)), 25) / num_solutions
    metagen_logger.debug(f"Sample-based gamma: num_solutions={num_solutions}, gamma={gamma}")
    return gamma

def gamma_sqrt(num_solutions: int) -> float:
    """
    Square-root-based gamma computation (similar to Hyperopt's approach).

    :param num_solutions: Number of solutions available.
    :return: Computed gamma value.
    """
    gamma = min(int(np.ceil(0.25 * np.sqrt(num_solutions))), 25) / num_solutions
    metagen_logger.debug(f"Sqrt gamma: num_solutions={num_solutions}, gamma={gamma}")
    return gamma

# Dictionary of available gamma functions
GAMMA_FUNCTIONS: Dict[str, Callable] = {
    "linear": gamma_linear,
    "exponential": gamma_exponential,
    "sampled_based": gamma_sample_based,
    "sqrt": gamma_sqrt
}

def compute_gamma(config: GammaConfig, iteration: Optional[int] = None, max_iterations: Optional[int] = None,
                  num_solutions: Optional[int] = None) -> float:
    """
    Computes the gamma value by calling the appropriate function.

    :param config: Gamma configuration containing the function name and parameters.
    :param iteration: Current iteration (if applicable).
    :param max_iterations: Maximum number of iterations (if applicable).
    :param num_solutions: Number of solutions (if applicable).
    :return: Computed gamma value.
    :raises ValueError: If required parameters are missing.
    """
    gamma_function = GAMMA_FUNCTIONS.get(config.gamma_function)

    if not gamma_function:
        raise ValueError(f"Gamma function '{config.gamma_function}' is not defined.")

    # Prepare common parameters with correct argument names
    params = {
        "iteration": iteration,
        "max_iterations": max_iterations,
        "minimum": config.minimum,  # Corrected from gamma_min
        "maximum": config.maximum,  # Corrected from gamma_max
    }

    # Add alpha only if it's required
    if config.gamma_function == "exponential":
        params["alpha"] = config.alpha

    # Ensure required parameters are present
    if config.gamma_function in ["linear", "exponential"]:
        if iteration is None or max_iterations is None:
            raise ValueError(f"Gamma function '{config.gamma_function}' requires iteration and max_iterations.")
        return gamma_function(**params)

    if config.gamma_function in ["sampled_based", "sqrt"]:
        if num_solutions is None:
            raise ValueError(f"Gamma function '{config.gamma_function}' requires num_solutions.")
        return gamma_function(num_solutions)

    raise ValueError(f"Unsupported gamma function: {config.gamma_function}")