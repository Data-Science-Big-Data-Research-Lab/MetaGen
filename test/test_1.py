from pycvoa.cvoa import *
from pycvoa.use_cases.dispatcher import problem_dispatcher

problem = problem_dispatcher("simple-2")

CVOA.initialize_pandemic(problem[0], problem[1])

strain_a = CVOA("Strain A")
# strain_b = CVOA("Strain B", 10)
# strain_c = CVOA("Strain C", 15)
# solution = cvoa_launcher([strain_a, strain_b, strain_c], verbose=True)

solution = strain_a.cvoa()

print("DONE!")
print("Solution: " + str(solution))
