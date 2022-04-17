from pycvoa.problem.domain import Domain

# ==================== 1. Building a new domain ====================
domain_1 = Domain()

# ==================== 2. Defining variables ====================

# %%%%%%%%%% 2.1 Defining INTEGER variables %%%%%%%%%%

# If the minimum value is greater or equal than the maximum one, raise a definition error
# domain_1.define_integer("I",100,0,3)
# domain_1.define_integer("I",100,100,3)

# If the step value is greater than (maximum value - minimum value) / 2, raise a definition error
# domain_1.define_integer("I",0,100,55)

domain_1.define_integer("I", 0, 100, 50)
# print(str(domain_1))

# %%%%%%%%%% 2.2 Defining REAL variables %%%%%%%%%%

# If the minimum value is greater or equal than the maximum one, raise a definition error
# domain_1.define_real("R",1.0,0.0,3)
# domain_1.define_real("R",1.0,1.0,3)

# If the step value is greater than (maximum value - minimum value) / 2, raise a definition error
# domain_1.define_real("R",0.0,1.0,0.7)

domain_1.define_real("R",0.0,1.0,0.1)
# print(str(domain_1))

# %%%%%%%%%% 2.3. Defining CATEGORICAL variables %%%%%%%%%%
# The categories must be provided in a list. These categories can be str, int or float.
domain_1.define_categorical("C_A",["C1","C2","C3","C4"])
domain_1.define_categorical("C_B",[1,2,3,4])
domain_1.define_categorical("C_C",[0.1,0.2,0.3,0.4])
# print(str(domain_1))

# %%%%%%%%%% 2.4. Defining LAYER variables %%%%%%%%%%

# ***** 2.4.1. Define the layer variable *****
domain_1.define_layer("L")

# ***** 2.4.2. Define the elements of the layer *****

# ** Defining INTEGER elements

# If the minimum value is greater or equal than the maximum one, raise a definition error
# domain_1.define_integer_element("L","L_I",100,0,5)
# domain_1.define_integer_element("L","L_I",100,100,5)

# If the step value is greater than (maximum value - minimum value) / 2, raise a definition error
# domain_1.define_integer_element("L","L_I",0,100,55)

domain_1.define_integer_element("L","L_I",0,100,20)
print(str(domain_1))










# ********** 3. General considerations **********
# If a new variable is defined with an already used name, raise a definition error
# domain_1.define_integer("v1",1,100,40)
# domain_1.define_real("v1",1,100,40)