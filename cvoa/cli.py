import argparse

from cvoa.core import *
from cvoa.individual import *

parser = argparse.ArgumentParser(description="Coronavirus Optimization Algorithm.")
parser.add_argument("-t", "--test", help="Test cvoa")
parser.add_argument("-vR", "--varR", help="Definition of a Real component of the individuals", nargs=4,
                    action="append")
parser.add_argument("-vI", "--varI", help="Definition of an Integer component of the individuals", nargs=4,
                    action="append")
parser.add_argument("-vC", "--varC", help="Definition of a Categorical component of the individuals", nargs="*",
                    action="append")
parser.add_argument("-f", "--fitnessFunction", help="Fitness function Pyhton code")
parser.add_argument("-s", "--strain", help="Strain definition", nargs="*",
                    action="append")


def user_defined_run(args):
    # Building definition
    idef = ProblemDefinition()
    for av in args.varR:
        idef.register_numeric_variable(REAL, av[0], float(av[1]), float(av[2]), float(av[3]))
    for av in args.varI:
        idef.register_numeric_variable(INTEGER, av[0], int(av[1]), int(av[2]), int(av[3]))
    for av in args.varC:
        idef.register_categorical_variable(av[0], av[1:len(av)])
    print(idef)

    # Building fitness function
    with open(args.fitnessFunction, "r") as file:
        code = file.read()
    codeObject = compile(code, "fitness_function_code", "exec")
    exec(codeObject, globals())
    fitness_function = globals()["fitness_function"]
    print(str(fitness_function))

    # Building strains
    strains = list()
    for av in args.strain:
        kw = {}
        for pa in av[2:len(av)]:
            la = pa.split("=")
            kw[la[0]] = float(la[1])
        st = CVOA(av[0], int(av[1]), **kw)
        strains.append(st)

    for s in strains: print(str(s))

    # Initialize pandemic
    CVOA.initialize_pandemic(idef, fitness_function)

    # Run multi-threading pandemic
    solution = cvoa_launcher(strains, verbose=True)

    print("DONE!")
    print("Solution: " + str(solution))


def test_run(test):
    idef = ProblemDefinition()
    idef.register_numeric_variable(REAL, "X", 0.0, 1000.0, 0.05)
    print(idef)
    fitness_function = getattr(sys.modules["cvoa.functions"], test)
    print(str(fitness_function))
    s = CVOA("Test", 10)
    print(str(s))
    CVOA.initialize_pandemic(idef, fitness_function)
    solution = cvoa_launcher([s], verbose=True)
    print("DONE!")
    print("Solution: " + str(solution))


def cvoa_cli(args=None):
    args = parser.parse_args(sys.argv[1:])
    # args = parser.parse_args("-vR R1 350.0 10000.0 0.5 "
    #                          "-vI I1 1 10 2 "
    #                          "-vC C1 l1 l2 l3 "
    #                          "-s strA 5 "
    #                          "-s strB 10 "
    #                          "-f /Users/davgutavi/Desktop/test.py".split())

    if args.test is not None:
        test_run(args.test)
    else:
        user_defined_run(args)
