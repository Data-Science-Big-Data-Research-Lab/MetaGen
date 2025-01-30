:orphan:

===============
Formal context
===============

The formal context of MetaGen is outlined in Equation 1. The *solver* defines a problem :math:`P` and uses the metaheuristic :math:`M`, created by the *developer*, to find an optimal solution :math:`S_{opt}` (Equation (1a)). A problem :math:`P` is composed of a domain :math:`D` and a fitness function :math:`F` (Equation (1b)). A domain is a set of variables and their corresponding value range, which the metaheuristic optimizes through the fitness function. A solution is an assignment of valid values to all variables within the domain. All potential solutions to a problem are part of the search space, and the metaheuristic explores, modifies, and evaluates the search space using the fitness function.

**Equation 1:**

.. math::

   M(P) = S_{opt} \qquad (1a)\\
   P = \langle D,F \rangle \qquad (1b)

.. toctree::
   :maxdepth: 1
   :hidden:

Domain and solution
---------------------

The formal definition of a domain :math:`D` is given by Equation (2a). It is a set of :math:`N` variable definitions, :math:`V_i \models Def^{T}`, where :math:`V_i` represents the name of the variable, and :math:`Def^{T}` is its definition of type :math:`T` as specified in Eq. (2b). There are six different types of variables, namely :math:`INTEGER` (:math:`I`), :math:`REAL` (:math:`R`), :math:`CATEGORICAL` (:math:`C`), :math:`GROUP` (:math:`G`), :math:`DYNAMIC` (:math:`D`) and, :math:`STATIC` (:math:`S`). The alias :math:`BASIC` (:math:`B`) is defined as the combination of :math:`INTEGER`, :math:`REAL`, and :math:`CATEGORICAL` in Eq. (2c).

**Equation 2:**

.. math::

   D =  \{Var_1 \models Def^{T}_1, Var_2 \models Def^{T}_2,...,Var_i \models Def^{T}_i,...,Var^{T}_{N} \models Def_{N}\} \qquad (2a)\\
   T  \epsilon  \{INTEGER(I), REAL(R), CATEGORICAL(C),\\
   , GROUP(G), DYNAMIC(D), STATIC(S)\} \qquad (2b)\\
   BASIC (B)  \epsilon  \{INTEGER(I), REAL(R), CATEGORICAL(C)\} \qquad (2c)

The MetaGen supported definitions are defined in Equation 3. The definitions of :math:`INTEGER` and :math:`REAL` represent a value in the range of integers :math:`\mathbb{Z}` and real numbers :math:`\mathbb{R}`, respectively, in the range :math:`[Min, Max]` as shown in Eq. (3a). The :math:`CATEGORICAL` definition represents a set of :math:`P` unique labels, as described in Eq. (3b). The :math:`GROUP` definition represents a set of :math:`Q` elements, each defined by a basic definition :math:`Def^B`, as given in Eq. (3c). The :math:`DYNAMIC` definition represents a sequence of :math:`BASIC` or :math:`GROUP` values of length in the range :math:`[LN_{min}, LN_{max}]` as specified in Eq. (3d). Finally, the :math:`STATIC` definition is a sequence of :math:`BASIC` or :math:`GROUP` values with a fixed length, :math:`LN` as specified in Eq. (3e).

**Equation 3:**

.. math::

   Def^{I|R} = \langle Min, Max \rangle \qquad (3a)\\
   Def^{C} = \{L_1, L_2,...,L_i,...,L_{P}\} \qquad (3b)\\
   Def^{G} = \{E_1 = Def^{B}_1, E_2 = Def^{B}_2,...,E_j = Def^{B}_j,...,E_{Q} = Def^{B}_{Q}\} \qquad (3c)\\
   Def^{D} = \langle LN_{min}, LN_{max}, Def^{B|G} \rangle  \qquad (3d)\\
   Def^{S} = \langle LN, Def^{B|G} \rangle \qquad (3e)

A collection of example problems can be found in the next table to support the formal definition. The problem :math:`P_1` is composed of a domain with an :math:`INTEGER` variable :math:`x` that moves within the interval :math:`[-10, 10]`, and the function to be optimized is :math:`f(x)=x+5`. Similarly, the problem :math:`P_2` has a domain consisting of a :math:`REAL` variable :math:`x` that moves within the interval :math:`[0.0, 1.0]`, and the objective function is :math:`f(x)=x^5`.

**Sample problems**

.. list-table:: Sample Problems
   :widths: 10 40 50
   :header-rows: 1

   * - :math:`P_{ID}`
     - Domain
     - Function
   * - :math:`P_1`
     - :math:`x \models Def^{I} = \langle -10, 10\rangle`
     - :math:`x+5`
   * - :math:`P_2`
     - :math:`x \models Def^{R} = \langle 0.0, 1.0\rangle`
     - :math:`x^2`
   * - :math:`P_3`
     - :math:`Alpha \models Def^{R} = \langle 0.0001, 0.001\rangle` :math:`Iterations \models Def^{I} = \langle 5, 200\rangle` :math:`Loss \models Def^{C} = \{squared\:error, huber, epsilon\:insensitive\}`
     - :math:`Regression(Alpha, Iterations, Loss)`
   * - :math:`P_4`
     - :math:`Learning\;rate \models Def^{R} = \langle 0.0, 0.000001\rangle` :math:`Ema \models Def^{C} = \{True, False\}` :math:`Arch \models Def^{D} = \langle 2,10,\,Def^{G} = \{Neurons \models Def^{I} = \langle 25, 300\rangle, Activation \models Def^{C} = \{relu, sigmoid, softmax, tanh\}, Dropout \models Def^{R} = \langle 0.0, 0.45\rangle\}\rangle`
     - :math:`LSTM(Learning\;rate, Ema, Arch)`

Problems :math:`P_3` and :math:`P_4` are examples of the target of the MetaGen framework, which is hyperparameter optimization for machine learning models. Problem :math:`P_3` illustrates the optimization of a linear regression model. The objective function is the performance of a model that has been trained with the :math:`Alpha`, :math:`Iterations`, and :math:`Loss` hyperparameters. :math:`Alpha` represents the regularization term that the model uses to prevent overfitting and is typically set to a value close to zero. The :math:`Iterations` hyperparameter controls the number of times the linear model should be re-calculated before reaching an error tolerance. Finally, the :math:`Loss` hyperparameter sets the function used during training to measure the performance of the linear model in each iteration. The domain of problem :math:`P_3` consists of the :math:`Alpha` variable, which is a :math:`REAL` value defined in the interval :math:`[0.0001, 0.001]`, the :math:`Iterations` variable, which is an :math:`INTEGER` defined in the interval :math:`[5, 200]`, and the :math:`Loss` variable, which is a :math:`CATEGORY` and can be set to :math:`squared\:error`, :math:`huber` or :math:`epsilon\:insensitive`.

The problem :math:`P_4` represents a hyperparameter optimization problem for a Long Short-Term Memory (LSTM) deep learning architecture. The objective is to determine the best configuration of the network in terms of the number of layers and the optimal hyperparameters for each layer. There are two common properties that apply to all layers of the architecture: the optimizer, which is stochastic gradient descent, and the control of the optimizer, which is through the learning rate and exponential moving average (EMA) parameters. The stochastic gradient descent is an iterative method used to optimize the network's performance, and the learning rate parameter mod