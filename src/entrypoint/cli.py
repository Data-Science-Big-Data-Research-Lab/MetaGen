import argparse
import sys
from pycvoa import *

"""
    This 

"""

parser = argparse.ArgumentParser(description="Coronavirus Optimization Algorithm.")
parser.add_argument("-t", "--test", help="Test pycvoa")
parser.add_argument("-vR", "--varR", help="Definition of a Real component of the individuals", nargs=4,
                    action="append")
parser.add_argument("-vI", "--varI", help="Definition of an Integer component of the individuals", nargs=4,
                    action="append")
parser.add_argument("-vC", "--varC", help="Definition of a Categorical component of the individuals", nargs="*",
                    action="append")
parser.add_argument("-f", "--fitnessFunction", help="Fitness function Python code")
parser.add_argument("-s", "--strain", help="Strain definition", nargs="*",
                    action="append")

def cvoa_cli():
    args = parser.parse_args(sys.argv[1:])
    # args = parser.parse_args("-vR R1 350.0 10000.0 0.5 "
    #                          "-vI I1 1 10 2 "
    #                          "-vC C1 l1 l2 l3 "
    #                          "-s strA 5 "
    #                          "-s strB 10 "
    #                          "-f /Users/davgutavi/Desktop/test.py".split())
    # Building definition
    idef = ProblemDefinition()
    for av in args.varR:
        idef.register_real_variable(av[0], float(av[1]), float(av[2]), float(av[3]))
    for av in args.varI:
        idef.register_integer_variable(av[0], int(av[1]), int(av[2]), int(av[3]))
    for av in args.varC:
        idef.register_categorical_variable(av[0], av[1:len(av)])
    print(idef)

    # Building fitness function
    with open(args.fitnessFunction, "r") as file:
        code = file.read()
    code_object = compile(code, "fitness_function_code", "exec")
    exec(code_object, globals())
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

    for s in strains:
        print(str(s))

    # Initialize pandemic
    CVOA.initialize_pandemic(idef, fitness_function)

    # Run multi-threading pandemic
    solution = cvoa_launcher(strains, verbose=True)

    print("DONE!")
    print("Solution: " + str(solution))
