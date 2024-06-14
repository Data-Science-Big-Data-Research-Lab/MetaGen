=============================
CVOA algorithm implementation
=============================
.. Meter la referencia al paper de CVOA.

The *Coronavirus Optimization Algorithm* or *CVOA* is a bioinspired metaheuristic based on *COVID-19 Propagation Model*.
You can see a complete description of it in [CVA paper reference].

In this document how *MetaGen* supports the implementation of *CVOA* is discussed. Therefore, only the specific pieces
of code where *MetaGen* affects *CVOA* is commented.

.. Meter la referencia al paper de CVOA y los enlaces al código fuente y la página de documentación del CVOA.

You can consult the complete information of the *CVOA* algotihm in the following sources:

- The description and analysis of the algorithm in *[CVA paper reference]*.
- The source code in the *./src/metagen/metaheuristics/cvoa/cvoa.py* file
- The documentation in the *./docs/metaheuristics/cvoa.rst* file.


Construction of potential solutions
===================================


The `initialize_pandemic` method
--------------------------------

.. code-block:: python

        solution_type: type[SolutionClass] = problem_definition.get_connector().get_type(
            problem_definition.get_core())
        CVOA.__bestIndividual = solution_type(problem_definition, connector=problem_definition.get_connector())

The `__init__` method
---------------------
The CVOA constructor (the `__init__` method) receives several control parameters that controls the metaheuristic
process. Besides, this method includes

.. code-block:: python

    self.solution_type: type[SolutionClass] = CVOA.__problemDefinition
                                                    .get_connector()
                                                    .get_type(CVOA.__problemDefinition.get_core())

    self.__bestStrainIndividual = self.solution_type(CVOA.__problemDefinition,
                                                        connector=CVOA.__problemDefinition.get_connector())

The `run` method
----------------

.. code-block:: python

        # The worst strain-specific superspreader individual will initially be the best solution.
        self.__worstSuperSpreaderIndividualStrain = self.solution_type(
            CVOA.__problemDefinition, best=True, connector=CVOA.__problemDefinition.get_connector())
        # The best strain-specific death individual will initially be the worst solution.
        self.__bestDeadIndividualStrain = self.solution_type(
            CVOA.__problemDefinition, connector=CVOA.__problemDefinition.get_connector())

        CVOA.__verbosity("Best individual: " +
                         str(self.__bestStrainIndividual))


Visualizing the variables of a potential solutions
==================================================
The `propagate_disease` method
==============================

.. code-block:: python

    CVOA.__verbosity("\n" + str(threading.current_thread()) +
                         "\n[" + self.__strainID + "] - Iteration #" + str(self.__time + 1) +
                         "\n\tBest global individual: " +
                         str(CVOA.__bestIndividual)
                         + "\n\tBest strain individual: " +
                         str(self.__bestStrainIndividual)
                         + "\n" + self.__r0_report(len(new_infected_population)))



The `__infect_pz` method
========================

.. code-block:: python

      patient_zero = self.solution_type(
            self.__problemDefinition, connector=self.__problemDefinition.get_connector())
        patient_zero.initialize()

        patient_zero.fitness = CVOA.__fitnessFunction(patient_zero)


The `__infect` method
=====================

.. code-block:: python

         infected.mutate(travel_distance)
         # Compute the fitness function of the new individual.
         infected.fitness = CVOA.__fitnessFunction(infected)
































