# import argparse
# from dispatcher import example_dispacher
#
# parser = argparse.ArgumentParser(description="Test the PyCVOA package.",
#                                  epilog="See the official documentation.")
#
# parser.add_argument("run",
#                     nargs=1,
#                     type=str,
#                     choices=["dummy-1", "dummy-2", "dummy-3", "simple-1", "simple-2", "rd-c", "rd-r", "knn-c", "knn-r",
#                              "svm-c", "svm-r", "sgd-c", "sgd-r"],
#                     default="simple-1")
#
#
# def main():
#     parameters = parser.parse_args()
#     run = vars(parameters)["run"][0]
#     example_dispacher(run)
