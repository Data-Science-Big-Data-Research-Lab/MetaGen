import numpy as np

def sphere(x):
    """Sphere Function (Convex, Unimodal)"""
    return np.sum(x ** 2)

def rastrigin(x):
    """Rastrigin Function (Multimodal, Nonlinear)"""
    A = 10
    return A * len(x) + np.sum(x ** 2 - A * np.cos(2 * np.pi * x))

def rosenbrock(x):
    """Rosenbrock Function (Non-Convex, Unimodal)"""
    return np.sum(100 * (x[1:] - x[:-1]**2)**2 + (1 - x[:-1])**2)

def ackley(x):
    """Ackley Function (Multimodal)"""
    a = 20
    b = 0.2
    c = 2 * np.pi
    n = len(x)
    sum1 = np.sum(x ** 2)
    sum2 = np.sum(np.cos(c * x))
    return -a * np.exp(-b * np.sqrt(sum1 / n)) - np.exp(sum2 / n) + a + np.e

def griewank(x):
    """Griewank Function (Multimodal)"""
    sum_term = np.sum(x ** 2) / 4000
    prod_term = np.prod(np.cos(x / np.sqrt(np.arange(1, len(x) + 1))))
    return sum_term - prod_term + 1

def levy(x):
    """Levy Function (Multimodal)"""
    w = 1 + (x - 1) / 4
    term1 = (np.sin(np.pi * w[0]))**2
    term2 = np.sum((w[:-1] - 1)**2 * (1 + 10 * (np.sin(np.pi * w[:-1] + 1))**2))
    term3 = (w[-1] - 1)**2 * (1 + (np.sin(2 * np.pi * w[-1]))**2)
    return term1 + term2 + term3

def schwefel(x):
    """Schwefel Function (Multimodal)"""
    return 418.9829 * len(x) - np.sum(x * np.sin(np.sqrt(np.abs(x))))

def michalewicz(x):
    """Michalewicz Function (Multimodal)"""
    m = 10
    i = np.arange(1, len(x) + 1)
    return -np.sum(np.sin(x) * (np.sin(i * x ** 2 / np.pi)) ** (2 * m))

def zakharov(x):
    """Zakharov Function (Unimodal)"""
    sum1 = np.sum(x ** 2)
    sum2 = np.sum(0.5 * np.arange(1, len(x) + 1) * x)
    return sum1 + sum2 ** 2 + sum2 ** 4

BECHMARK_FUNCTIONS = {"sphere": sphere,
                "rastrigin": rastrigin,
                "rosenbrock": rosenbrock,
                "ackley": ackley,
                "griewank": griewank,
                "levy": levy,
                "schwefel": schwefel,
                "michalewicz": michalewicz,
                "zakharov": zakharov}

FUNCTION_RANGES = {
    "sphere": [-5.12, 5.12],
    "rastrigin": [-5.12, 5.12],
    "rosenbrock": [-2.048, 2.048],
    "ackley": [-32.768, 32.768],
    "griewank": [-600, 600],
    "levy": [-10, 10],
    "schwefel": [-500, 500],
    "michalewicz": [0, np.pi],
    "zakharov": [-5, 10]
}