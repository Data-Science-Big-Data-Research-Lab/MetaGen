from pycvoa.problem.domain import Domain
domain = Domain()

print("BASIC TYPES")
print("define_integer")
domain.define_integer("I", 1, 100, 20)
# These fail
domain.define_integer("I", 1, 100, 20)

print("define_real")
domain.define_real("R", 0.0, 1.0, 0.1)

print("define_categorical")
domain.define_categorical("CA", ["C1", "C2", "C3", "C4"])
domain.define_categorical("CB", [1, 2, 3, 4])
domain.define_categorical("CC", [0.1, 0.2, 0.3, 0.4])


print("\nLAYER TYPES")
print("define_layer")
domain.define_layer("L")

print("define_integer_element")
domain.define_integer_element("L", "EI", 0, 100, 20)
domain.define_real_element("L", "ER", 1.5, 3.0, 0.01)
domain.define_categorical_element("L", "EC", ["Lb1", "Lb2", "Lb3"])

print("\nBASIC VECTOR TYPES")
domain.define_vector("V", 2, 8, 1)

# print("define_vector - V_I")
# domain.define_vector("V_I", 4, 10, 1)
#
# print("define_components_as_integer")
# domain.define_components_as_integer("V_I", 1, 10, 2)
#
# print("define_vector - V_R")
# domain.define_vector("V_R", 1, 10, 1)
# #
# print("define_components_as_real")
# domain.define_components_as_real("V_R", 0.0, 0.1, 0.0001)
# #
# print("define_vector - V_C")
# domain.define_vector("V_C", 10, 20, 1)
# #
# print("define_components_as_categorical")
# domain.define_components_as_categorical("V_C", ["V1", "V2", "V3"])
# # print(str(domain))
# #
# # print("\nLAYER VECTOR TYPES")
# print("define_vector - V_L")
# domain.define_vector("V_L", 10, 20, 1)
# #
# print("define_components_as_layer")
# domain.define_components_as_layer("V_L")
# #
# print("define_layer_vector_integer_element")
# domain.define_layer_vector_integer_element("V_L", "el-1", 10, 20, 1)
# #
# print("define_layer_vector_real_element")
# domain.define_layer_vector_real_element("V_L", "el-2", 0.1, 0.5, 0.1)
# #
# print("define_layer_vector_categorical_element")
# domain.define_layer_vector_categorical_element("V_L", "el-3", [1, 2, 3])


print("\nDomain:\n\n"+str(domain))
