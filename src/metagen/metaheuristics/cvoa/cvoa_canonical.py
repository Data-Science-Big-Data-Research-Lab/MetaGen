"""
    Copyright (C) 2023 David Gutierrez Avilés and Manuel Jesús Jiménez Navarro

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from typing import Callable

from metagen.framework import Domain
from metagen.framework.rng import get_rng
from metagen.framework.solution import Solution
from metagen.metaheuristics.cvoa.common_tools import PandemicState, SolutionSet, StrainProperties, infect
from metagen.metaheuristics.cvoa.cvoa_local import CVOA


class CanonicalCVOA(CVOA):
    """
    The CVOA of the paper, where MetaGen's CVOA departs from it.

    Martínez-Álvarez et al., *Coronavirus Optimization Algorithm: A Bioinspired
    Metaheuristic Based on the COVID-19 Propagation Model*, Big Data 8(4), 2020.
    Same strain, same launchers, same parameters and same pandemic state as CVOA;
    it runs in threads and on Ray like it. What changes is what the pseudocode says
    and CVOA does differently:

    - **Death and superspreading are drawn per individual** (Algorithms 2 and 4): every
      carrier dies with ``p_die`` and superspreads with ``p_superspreader``, each
      iteration. CVOA fills bounded sets in order of arrival and, once full, kills
      the best candidate and makes the worst a superspreader.
    - **The dead are drawn before spreading and the carriers recover after it**
      (Algorithm 1, lines 11 and 22). CVOA recovers them before.
    - **An isolated individual joins the recovered** (Algorithm 3, line 12), and only
      returns with ``p_re_infection``. In CVOA it is counted and the point stays
      open: on binary domains that searched better, which is why CVOA keeps it.
    - **Isolation and reinfection are drawn once per carrier** (Algorithm 3, lines 3
      and 4): all of a carrier's offspring share the two draws. CVOA draws per
      individual.

    What it does not inherit: the erratum of Algorithm 2, where the traveler and
    superspreader rates are crossed; the text is implemented, as in CVOA. Social
    distancing works as in CVOA too: isolation only applies from the
    ``social_distancing`` iteration on, and from then on every contagion is at
    distance one.

    **Code example**

    .. code-block:: python

        from metagen.framework import Domain, Solution
        from metagen.metaheuristics import cvoa_launcher
        from metagen.metaheuristics.cvoa import CanonicalCVOA, StrainProperties

        domain = Domain()
        domain.define_integer("x", 0, 10)

        def fitness_function(solution: Solution) -> float:
            return (solution["x"] - 3) ** 2

        strains = [StrainProperties("S1", pandemic_duration=10)]
        best = cvoa_launcher(strains, domain, fitness_function, strain_class=CanonicalCVOA)
    """

    def update_pandemic_global_state(self) -> None:
        """
        Algorithms 2 and 4: each carrier superspreads with p_superspreader and dies
        with p_die, by its own draw. The dead go to the strain's and the pandemic's
        dead sets; nobody recovers yet, that happens after spreading.
        """
        properties = self.strain_properties
        self.superspreaders = SolutionSet()
        for individual in self.infected:
            if get_rng().random() < properties.p_superspreader:
                self.superspreaders.add(individual)
            if get_rng().random() < properties.p_die:
                self.dead.add(individual)

            if individual.get_fitness() < self.global_state.get_best_individual().get_fitness():
                self.global_state.update_best_individual(individual)
                self.best_strain_solution_found = True
                self._log(f"New global best individual found at {self.time}! ({individual})")
            if individual.get_fitness() < self._best_of_strain().get_fitness():
                self.best_strain_solution = individual

        self.global_state.update_deaths(self.dead)
        self.global_state.update_recovered_with_deaths()

    def after_spreading(self) -> None:
        """Algorithm 1, line 22: the carriers recover once they have spread."""
        for individual in self.infected:
            self.global_state.recover_if_not_dead(individual)

    @classmethod
    def isolate(cls, state: PandemicState, individual: Solution) -> None:
        """Algorithm 3, line 12: the isolated individual joins the recovered."""
        state.isolate(individual)
        state.recover_if_not_dead(individual)

    @classmethod
    def infect_individuals_from(cls, state: PandemicState, fitness_function: Callable[[Solution], float],
                                strain_properties: StrainProperties, carrier: Solution, travel_distance: int,
                                n_infected: int, time: int) -> SolutionSet:
        """
        Algorithm 3: the reinfection and isolation draws, R3 and R4, are made once
        per carrier and shared by all of its offspring.
        """
        reinfection_draw = get_rng().random()
        isolation_draw = get_rng().random()
        distancing = time >= strain_properties.social_distancing
        infected_population: SolutionSet = SolutionSet()

        for _ in range(0, n_infected):
            new_infected_individual = infect(carrier, fitness_function, 1 if distancing else travel_distance)
            individual_state = state.get_individual_state(new_infected_individual)
            if individual_state.dead:
                continue
            if not individual_state.recovered:
                if distancing and isolation_draw <= strain_properties.p_isolation:
                    cls.isolate(state, new_infected_individual)
                else:
                    infected_population.add(new_infected_individual)
            elif reinfection_draw < strain_properties.p_re_infection:
                infected_population.add(new_infected_individual)
                state.get_infected_again(new_infected_individual)
        return infected_population
