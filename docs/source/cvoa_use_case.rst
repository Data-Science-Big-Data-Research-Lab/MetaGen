=============================
CVOA algorithm implementation
=============================

The *Coronavirus Optimization Algorithm* or *CVOA* is a bioinspired metaheuristic based on *COVID-19 Propagation Model*.
You can see a complete description of it in [1]_.

In this document how *MetaGen* supports the implementation of *CVOA* is discussed. Therefore, only the specific pieces
of code where *MetaGen* affects *CVOA* is commented.

.. Meter los enlaces al código fuente y la página de documentación del CVOA.

You can consult the complete information of the *CVOA* algotihm in the following sources:

- The description and analysis of the algorithm in [1]_.
- The source code in the *./src/metagen/metaheuristics/cvoa/cvoa.py* file.
- The documentation in the *./docs/metaheuristics/cvoa.rst* file.

Construction of potential solutions
===================================

*MetaGen* provides a mechanism to instantiate the `Solution` using the `BaseConnector` class, which can be obtained
using the `get_connector` method of the *Domain* class. Once instantiated, the *Developer* uses the standard `Solution`
class in the metaheuristic code (the *CVOA* algorithm).This action makes the metaheuristic work not only with the
*Domain* and the standard `Solution` classes but also with the custom `Solution` ones.

A high-level programmer can implement a custom Solution class by taking the following steps:

1. Extend the type classes that want to customize and redefine their methods or create new ones.

2. Extend the `Solution` class, redefine its methods or create new ones.

3. Extend the `BaseConnector` class to map the redefined type classes with the standard ones.

You can find several usages of this *MetaGen*'s feature in the following pieces of code in the `CVOA` class:

The `initialize_pandemic` method
--------------------------------

.. code-block:: python

        solution_type: type[SolutionClass] = problem_definition.get_connector().get_type(
            problem_definition.get_core())

        CVOA.__bestIndividual = solution_type(problem_definition, connector=problem_definition.get_connector())

The `__init__` method
---------------------

.. code-block:: python

    self.solution_type: type[SolutionClass] = CVOA.__problemDefinition
                                                    .get_connector()
                                                    .get_type(CVOA.__problemDefinition.get_core())

    self.__bestStrainIndividual = self.solution_type(CVOA.__problemDefinition,
                                                        connector=CVOA.__problemDefinition.get_connector())

The `run` method
----------------

.. code-block:: python

        self.__worstSuperSpreaderIndividualStrain = self.solution_type(
            CVOA.__problemDefinition, best=True, connector=CVOA.__problemDefinition.get_connector())

        self.__bestDeadIndividualStrain = self.solution_type(
            CVOA.__problemDefinition, connector=CVOA.__problemDefinition.get_connector())

The `__infect_pz` method
------------------------

.. code-block:: python

      patient_zero = self.solution_type(
            self.__problemDefinition, connector=self.__problemDefinition.get_connector())


Visualizing the variables of a potential solutions
==================================================

The *Solution* class provides a implementation of the ´__str__´ method to easily print the *Solution* variable values.

You can find several usages of this *MetaGen*'s feature in the following pieces of code in the `CVOA` class:

The `run` method
----------------
.. code-block:: python

 CVOA.__verbosity("Best individual: " +
                         str(self.__bestStrainIndividual))

The `propagate_disease` method
------------------------------
.. code-block:: python

    CVOA.__verbosity("\n" + str(threading.current_thread()) +
                         "\n[" + self.__strainID + "] - Iteration #" + str(self.__time + 1) +
                         "\n\tBest global individual: " +
                         str(CVOA.__bestIndividual)
                         + "\n\tBest strain individual: " +
                         str(self.__bestStrainIndividual)
                         + "\n" + self.__r0_report(len(new_infected_population)))

Initializing a potential solution
===================================

The *Solution* class provides the ´initialize´ method to easily initialize the *Solution* variable values.

You can find a usage of this *MetaGen*'s feature in the following piece of code in the `CVOA` class:

The `__infect_pz` method
------------------------
.. code-block:: python

        patient_zero.initialize()

Altering a potential solution
=============================

The *Solution* class provides the `mutate` method to easily change randomly the *Solution* variable values.

You can find a usage of this *MetaGen*'s feature in the following piece of code in the `CVOA` class:

The `__infect` method
------------------------
.. code-block:: python

    infected.mutate(travel_distance)

Manipulating a `Set` of potential solutions
==========================================

The *Solution* class provides a fitness value-based implementation of the `__eq__`, `__ne__`, `__hash__`, `__lt__`,
`__le__`, `__gt__` and `__ge__` methods, that enable `Python`, solution `Set` management.

The usage of sets of solutions is one of the key points of the *CVOA* algorithm, therefore, you can find several
`Solution` sets along the `CVOA` class code as the following:

- `__recovered`
- `__deaths`
- `__isolated`
- `__infectedStrain`
- `__superSpreaderStrain`
- `__infeted_strain_super_spreader_strain`
- `__deathStrain`

.. [1] Martínez-Álvarez F, Asencio-Cortés G, Torres JF, Gutiérrez-Avilés D, Melgar-García L, Pérez-Chacón R, Rubio-Escudero C, Riquelme JC, Troncoso A (2020) Coronavirus optimization algorithm: a bioinspired metaheuristic based on the COVID-19 propagation model. Big Data 8:4, 308–322, DOI: 10.1089/big.2020.0051.





























