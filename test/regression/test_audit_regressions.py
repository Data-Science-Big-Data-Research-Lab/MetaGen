"""Tests de regresión de la auditoría de código (commit 74f104e).

Cada test comprueba el comportamiento **correcto**, el que debería tener MetaGen
una vez arreglado el hallazgo, y está marcado ``xfail(strict=True)`` porque hoy
falla. El flujo de trabajo es:

1. Arreglas el hallazgo F-xx en ``src/``.
2. El test pasa a XPASS y, por el ``strict=True``, pytest lo reporta como fallo.
3. Quitas el marcador ``@pytest.mark.xfail`` de ese test.
4. ``pytest test/framework_test test/regression`` vuelve a verde, y a partir de
   ahí el test protege el arreglo.

Mientras no se arregle nada, la suite sigue en verde: los xfail cuentan como
esperados. Los detalles de cada hallazgo están en ``AUDIT.md``.
"""

import copy
import importlib.util
from importlib.metadata import requires
import os
import math
import pathlib
import random
import re
import subprocess
import sys
import threading

import pytest

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed


# --------------------------------------------------------------------------
# Dominio: tipos y definiciones
# --------------------------------------------------------------------------


def test_f01_un_real_con_step_cubre_todo_su_dominio():
    set_seed(0)
    dom = Domain()
    dom.define_real("x", -5.0, 5.0, 1.0)
    valores = {round(Solution(dom)["x"], 6) for _ in range(300)}
    assert min(valores) < 0.0, (
        f"un real en [-5, 5] con step 1 solo genera {sorted(valores)}: "
        "los valores negativos y el cero son inalcanzables"
    )


def test_f01_la_rejilla_de_step_arranca_en_el_minimo():
    """F-01, segunda mitad: la rejilla se anclaba en el cero absoluto.

    Redondear a multiplos absolutos de `step` deja fuera el propio minimo del
    dominio cuando este no es multiplo del paso: `[0.05, 0.55]` con `step=0.1`
    solo producia 0.1, 0.2... y nunca 0.05, que es un valor declarado valido.
    """
    set_seed(0)
    dom = Domain()
    dom.define_real("x", 0.05, 0.55, 0.1)
    valores = {round(Solution(dom)["x"], 10) for _ in range(400)}
    assert 0.05 in valores, (
        f"el minimo del dominio es inalcanzable; solo se generan {sorted(valores)}"
    )
    assert valores <= {0.05, 0.15, 0.25, 0.35, 0.45, 0.55}, (
        f"se han generado valores fuera de la rejilla: {sorted(valores)}"
    )


def test_f12_cada_domain_tiene_su_propio_conector():
    assert Domain().get_connector() is not Domain().get_connector()


def test_f12_registrar_un_tipo_no_afecta_a_los_demas_dominios():
    """Lo que de verdad dolia del conector compartido: el conector es el mecanismo
    de extension, y registrar en uno recableaba todos los demas."""
    from metagen.framework.domain import IntegerDefinition
    from metagen.framework.solution.types import Integer

    class EnteroPropio(Integer):
        pass

    con_extension = Domain()
    con_extension.get_connector().register(IntegerDefinition, EnteroPropio, int)

    assert Domain().get_connector().get_type(IntegerDefinition) is Integer


def test_f16_el_mensaje_de_variable_ya_definida_es_legible():
    dom = Domain()
    dom.define_integer("i", 0, 10)
    with pytest.raises(ValueError) as exc:
        dom.define_integer("i", 0, 5)
    mensaje = str(exc.value)
    assert "DEFINITION error" in mensaje, mensaje
    assert "already defined" in mensaje, mensaje


@pytest.mark.parametrize("modo,esperado", [
    ("d_a", "already defined"),
    ("d_n", "not defined"),
    ("d_g", "not a group"),
    ("d_s", "not a structure"),
])
def test_f16_los_cuatro_mensajes_de_definicion_son_legibles(modo, esperado):
    """Los cuatro modos caian en la rama muerta, no solo el de «ya definida»."""
    from metagen.framework.domain.preconditions import Messages

    assert Messages.definition("x", modo) == f"[DEFINITION error] The variable x is {esperado}."


def test_f16_el_mensaje_de_paso_cero_no_lleva_espacio_doble():
    """De la misma familia, senalado al cerrar F-19: `Messages.step_zero` producia
    «The  value must be greater than zero», con dos espacios."""
    from metagen.framework.domain.preconditions import Messages

    for modo in ("i", "r", "s"):
        assert "  " not in Messages.step_zero(modo)


def test_f17_las_categorias_duplicadas_se_rechazan():
    with pytest.raises(ValueError):
        Domain().define_categorical("c", ["a", "b", "a"])


def test_f17_una_sola_categoria_es_valida():
    dom = Domain()
    dom.define_categorical("c", ["solo"])
    assert Solution(dom)["c"] == "solo"


def test_f17_una_sola_categoria_se_puede_mutar():
    """Permitir longitud 1 obliga a proteger `Categorical.mutate`, que elegia entre
    las categorias distintas de la actual y con una sola haria `choice([])`."""
    set_seed(1)
    dom = Domain()
    dom.define_categorical("c", ["solo"])

    solucion = Solution(dom)
    for _ in range(5):
        solucion.mutate()
    assert solucion["c"] == "solo"


@pytest.mark.parametrize("categorias", [
    ["a", "b", "a", "b"],
    ["a", 1],
    [],
], ids=["duplicadas no adyacentes", "tipos mezclados", "lista vacia"])
def test_f17_otras_listas_de_categorias_invalidas_se_rechazan(categorias):
    with pytest.raises(ValueError):
        Domain().define_categorical("c", categorias)


def test_f18_una_estructura_estatica_se_identifica_como_static():
    dom = Domain()
    dom.define_static_structure("v", 3)
    dom.set_structure_to_integer("v", 0, 10)
    definicion = dom.get_core().get("v")
    assert definicion.get_type() == definicion.get_attributes()[0]


# --------------------------------------------------------------------------
# Solution
# --------------------------------------------------------------------------


def test_f14_el_centinela_de_mejor_fitness_es_menor_que_cualquier_objetivo():
    dom = Domain()
    dom.define_integer("i", 0, 10)
    assert Solution(dom, best=True).get_fitness() < -1e300


def test_f15_dos_soluciones_distintas_no_comparten_hash():
    dom = Domain()
    dom.define_integer("i", 0, 10)
    a, b = Solution(dom), Solution(dom)
    a.set("i", 1)
    b.set("i", 9)
    a.set_fitness(3.0)
    b.set_fitness(3.0)
    assert a != b
    assert hash(a) != hash(b)


def test_f15_dos_soluciones_iguales_comparten_hash():
    dom = Domain()
    dom.define_integer("i", 0, 10)
    a, b = Solution(dom), Solution(dom)
    a.set("i", 1)
    b.set("i", 1)
    a.set_fitness(1.0)
    b.set_fitness(2.0)
    assert a == b
    assert hash(a) == hash(b)


def test_f15_una_solucion_con_estructuras_y_grupos_se_puede_hashear():
    """El hash viejo esquivaba los valores por completo. Hashearlos de verdad obliga
    a bajar por listas (Structure) y por sub-soluciones (grupos), que no se hashean
    por si solas."""
    set_seed(2)
    dom = Domain()
    dom.define_static_structure("v", 3)
    dom.set_structure_to_integer("v", 0, 10)
    dom.define_dynamic_structure("w", 1, 4)
    dom.set_structure_to_real("w", -1.0, 1.0)
    dom.define_group("g")
    dom.define_integer_in_group("g", "a", 0, 5)

    solucion = Solution(dom)
    copia = copy.deepcopy(solucion)

    assert solucion == copia
    assert hash(solucion) == hash(copia)


def test_f15_la_lista_tabu_bloquea_una_solucion_ya_prohibida():
    """Donde el invariante roto se convierte en un fallo de verdad: `tools.py` mete la
    lista tabu en un `set` y pregunta `neighbor not in tabu_set`.

    Un vecino con las mismas variables que una solucion prohibida **es** esa solucion
    para `__eq__`, pero con el hash viejo caia en otro cubo si su fitness no coincidia,
    y el `in` respondia que no estaba. La lista tabu dejaba pasar lo que debia bloquear.
    """
    set_seed(3)
    dom = Domain()
    dom.define_integer("i", 0, 10)

    prohibida = Solution(dom)
    prohibida.set("i", 4)
    prohibida.set_fitness(1.0)

    vecino = Solution(dom)
    vecino.set("i", 4)             # las mismas variables
    vecino.set_fitness(5.0)        # distinto fitness

    assert vecino == prohibida
    assert vecino in {prohibida}


# --------------------------------------------------------------------------
# Structure
# --------------------------------------------------------------------------


def _estructura_estatica(longitud=3, semilla=4):
    set_seed(semilla)
    dom = Domain()
    dom.define_static_structure("v", longitud)
    dom.set_structure_to_integer("v", 0, 100)
    return Solution(dom).get("v")


def test_f05_asignar_un_elemento_conserva_el_valor():
    st = _estructura_estatica()
    st[0] = 42
    assert st[0] == 42


def test_f05_append_conserva_el_valor():
    st = _estructura_estatica()
    st.append(7)
    assert st[len(st) - 1] == 7


def test_f05_una_estructura_de_grupos_conserva_el_valor():
    """La vía del dict tenía el mismo _convert, y no la cubría ningún test."""
    set_seed(4)
    dom = Domain()
    dom.define_group("g")
    dom.define_integer_in_group("g", "a", 0, 100)
    dom.define_static_structure("v", 2)
    dom.set_structure_to_variable("v", "g")

    st = Solution(dom).get("v")
    st.append({"a": 33})
    assert st[len(st) - 1]["a"] == 33


def test_f05_un_tipo_no_soportado_no_entra_en_la_solucion():
    """El mismo `elif <clase>:` de _convert dejaba muerto el raise de Solution.set."""
    set_seed(4)
    dom = Domain()
    dom.define_integer("i", 0, 10)

    with pytest.raises(TypeError):
        Solution(dom).set("i", {1, 2})


def test_f06_set_admite_una_lista_de_builtins():
    st = _estructura_estatica()
    st.set([1, 2, 3])
    assert [st[i] for i in range(3)] == [1, 2, 3]


def test_f06_insert_inserta_en_la_lista():
    st = _estructura_estatica()
    longitud = len(st)
    st.insert(0, 5)
    assert len(st) == longitud + 1
    assert st[0] == 5


def test_f06_set_admite_una_lista_de_grupos():
    """set() tambien es la via del dict, y ahi nadie la probaba."""
    set_seed(4)
    dom = Domain()
    dom.define_group("g")
    dom.define_integer_in_group("g", "a", 0, 100)
    dom.define_static_structure("v", 2)
    dom.set_structure_to_variable("v", "g")

    st = Solution(dom).get("v")
    st.set([{"a": 11}, {"a": 22}])
    assert [st[i]["a"] for i in range(2)] == [11, 22]


def test_f19_una_estructura_dinamica_alcanza_su_longitud_maxima():
    set_seed(5)
    dom = Domain()
    dom.define_dynamic_structure("d", 2, 5)
    dom.set_structure_to_integer("d", 0, 10)
    longitudes = {len(Solution(dom).get("d")) for _ in range(300)}
    assert longitudes == {2, 3, 4, 5}, sorted(longitudes)


def test_f19_una_estructura_dinamica_admite_min_igual_a_max():
    dom = Domain()
    dom.define_dynamic_structure("d", 3, 3)
    dom.set_structure_to_integer("d", 0, 10)
    assert len(Solution(dom).get("d")) == 3


def test_f19_alterar_una_estructura_vacia_no_revienta():
    """Con longitud minima cero la estructura puede estar vacia, y _alterate
    hacia randint(1, 0)."""
    set_seed(5)
    dom = Domain()
    dom.define_dynamic_structure("d", 0, 4)
    dom.set_structure_to_integer("d", 0, 10)

    st = Solution(dom).get("d")
    st.set([])
    st.mutate()
    assert len(st) >= 0


@pytest.mark.parametrize(
    "definir",
    [
        lambda dom: dom.define_dynamic_structure("d", 9, 2),
        lambda dom: dom.define_dynamic_structure("d", -1, 5),
        lambda dom: dom.define_dynamic_structure("d", 1, 5, 0),
        lambda dom: dom.define_static_structure("s", -3),
        lambda dom: dom.define_static_structure("s", 0),
    ],
    ids=["min>max", "min negativo", "paso cero", "longitud negativa", "longitud cero"],
)
def test_f19_una_longitud_imposible_se_rechaza_al_definirla(definir):
    """Ninguna de las dos definiciones validaba sus longitudes."""
    with pytest.raises(ValueError):
        definir(Domain())


# --------------------------------------------------------------------------
# Metaheuristicas
# --------------------------------------------------------------------------


def _esfera_2d():
    dom = Domain()
    dom.define_real("x", -5.0, 5.0)
    dom.define_real("y", -5.0, 5.0)
    return dom, lambda s: (s["x"] - 1.0) ** 2 + (s["y"] + 2.0) ** 2


def test_f02_tpe_initialize_devuelve_la_mejor_solucion():
    from metagen.metaheuristics import TPE

    set_seed(1)
    dom = Domain()
    dom.define_real("x", -5.0, 5.0)
    tpe = TPE(
        dom,
        lambda s: (s["x"] - 1.0) ** 2,
        max_iterations=1,
        warmup_iterations=0,
        candidate_pool_size=3,
    )
    poblacion, mejor = tpe.initialize(10)
    assert mejor.get_fitness() == min(s.get_fitness() for s in poblacion)


def _dominio_tpe():
    from metagen.metaheuristics.tpe.tpe_tools import TPEConnector

    dominio = Domain(connector=TPEConnector())
    dominio.define_real("r", -5.0, 5.0)
    dominio.define_integer("n", 0, 10)
    dominio.define_categorical("c", ["a", "b", "c"])
    return dominio


def test_f22_el_remuestreo_de_tpe_no_sale_del_dominio():
    """F-22: la rama de reserva hacia `uniform(min_value, max_value + 1)`, con un +1
    que es de `integers()` de numpy, cuyo limite superior es exclusivo. Y el valor se
    asignaba con `self.value = ...`, saltandose `set()` y su `check()`.

    Se fuerza la rama igualando los valores de referencia, que es cuando sigma vale
    cero. En una ejecucion real de TPE sobre un dominio entero se alcanzaba en 141 de
    960 muestreos.
    """
    set_seed(3)
    dominio = _dominio_tpe()
    solucion = Solution(dominio, connector=dominio.get_connector())
    referencias = [Solution(dominio, connector=dominio.get_connector()) for _ in range(3)]

    for nombre in ("r", "n"):
        for referencia in referencias:
            referencia.set(nombre, solucion[nombre])       # sigma = 0
        _, minimo, maximo, _ = solucion.get(nombre).get_definition().get_attributes()

        for _ in range(200):
            valores = [referencia.get(nombre) for referencia in referencias]
            solucion.get(nombre).resample(valores, valores)
            assert minimo <= solucion[nombre] <= maximo, (
                f"{nombre} se ha ido a {solucion[nombre]}, fuera de "
                f"[{minimo}, {maximo}]"
            )


@pytest.mark.parametrize("nombre,tipo", [("r", float), ("n", int), ("c", str)])
def test_f22_el_remuestreo_devuelve_tipos_nativos(nombre, tipo):
    """`TPECategorical` devolvia escalares de numpy en vez de tipos nativos, que es
    lo que acaba viendo la funcion de fitness del usuario."""
    set_seed(3)
    dominio = _dominio_tpe()
    solucion = Solution(dominio, connector=dominio.get_connector())
    referencias = [Solution(dominio, connector=dominio.get_connector()) for _ in range(3)]

    valores = [referencia.get(nombre) for referencia in referencias]
    solucion.get(nombre).resample(valores, valores)

    assert type(solucion[nombre]) is tipo


def test_f22_la_guarda_de_none_no_revienta(monkeypatch):
    """`if np.isnan(value) or value is None` no podia atrapar un None: `np.isnan(None)`
    lanza TypeError antes de llegar a la segunda mitad."""
    import metagen.metaheuristics.tpe.tpe_tools as herramientas

    set_seed(3)
    dominio = _dominio_tpe()
    solucion = Solution(dominio, connector=dominio.get_connector())
    referencias = [Solution(dominio, connector=dominio.get_connector()) for _ in range(3)]

    monkeypatch.setattr(herramientas, "sample_from_values",
                        lambda tipo, mejores, peores: None)

    for nombre in ("r", "n"):
        valores = [referencia.get(nombre) for referencia in referencias]
        solucion.get(nombre).resample(valores, valores)   # no debe lanzar TypeError
        _, minimo, maximo, _ = solucion.get(nombre).get_definition().get_attributes()
        assert minimo <= solucion[nombre] <= maximo


def test_f13_tpe_no_modifica_el_dominio_del_usuario():
    from metagen.metaheuristics import TPE

    dom = Domain()
    dom.define_real("x", -5.0, 5.0)
    conector_original = dom.get_connector()
    TPE(dom, lambda s: s["x"], max_iterations=1, warmup_iterations=0)
    assert dom.get_connector() is conector_original


def test_f03_el_warmup_no_se_descarta():
    from metagen.metaheuristics import RandomSearch

    set_seed(2)
    dom, fitness = _esfera_2d()
    algoritmo = RandomSearch(dom, fitness, population_size=2, max_iterations=1)
    algoritmo.warmup_iterations = 10
    algoritmo._warmup()
    tras_warmup = algoritmo.best_solution.get_fitness()
    algoritmo._initialize()
    assert algoritmo.best_solution.get_fitness() <= tras_warmup, (
        f"el warmup habia encontrado {tras_warmup} y tras _initialize el mejor "
        f"es {algoritmo.best_solution.get_fitness()}"
    )


def test_f04_el_segundo_hijo_hereda_del_segundo_padre():
    from metagen.metaheuristics import GAConnector
    from metagen.metaheuristics.ga.ga_tools import GASolution

    set_seed(3)
    dom = Domain(connector=GAConnector())
    for nombre in ("a", "b", "c", "d"):
        dom.define_integer(nombre, 0, 1000)
    padre = GASolution(dom, connector=dom.get_connector())
    madre = GASolution(dom, connector=dom.get_connector())
    _, hijo2 = padre.crossover(madre)

    distintas = [k for k in padre if padre[k] != madre[k]]
    assert distintas, "los dos padres son identicos; cambia la semilla"
    heredadas = [k for k in distintas if hijo2[k] == madre[k]]
    assert heredadas, "el hijo 2 no hereda ninguna variable de la madre"


def test_f20_sa_no_evalua_una_poblacion_entera_al_inicializar():
    from metagen.metaheuristics import SA

    set_seed(6)
    dom = Domain()
    dom.define_real("x", -5.0, 5.0)
    evaluaciones = {"n": 0}

    def fitness(solucion):
        evaluaciones["n"] += 1
        return (solucion["x"] - 1.0) ** 2

    algoritmo = SA(
        dom,
        fitness,
        warmup_iterations=0,
        max_iterations=2,
        neighbor_population_size=1,
        log_dir="logs/test_SA",
    )
    algoritmo.run()
    assert evaluaciones["n"] <= 4, (
        f"2 iteraciones con 1 vecino deberian costar ~3 evaluaciones y han "
        f"costado {evaluaciones['n']}"
    )


def test_f25_sa_devuelve_el_mejor_vecino_no_el_ultimo():
    """F-25: `best_neighbor = neighbor` era un alias, no una copia, y el bucle
    seguia mutando ese mismo objeto. Si el mejor vecino resultaba ser el primero,
    `best_fitness` anunciaba su valor mientras `best_neighbor` apuntaba ya al ultimo
    generado, asi que SA devolvia algo que no era lo mejor que habia visto.
    """
    from metagen.metaheuristics import SA

    dominio, fitness = _dominio_y_fitness_de_prueba()

    for semilla in range(10):
        algoritmo = SA(dominio, fitness, max_iterations=15,
                       neighbor_population_size=5, seed=semilla)
        solucion = algoritmo.run()
        assert solucion.get_fitness() == pytest.approx(
            min(algoritmo.best_solution_fitnesses)), (
            f"semilla {semilla}: devuelve {solucion.get_fitness()} y su historial "
            f"llego a {min(algoritmo.best_solution_fitnesses)}"
        )


def test_f25_los_vecinos_salen_de_la_solucion_actual_no_en_cadena():
    """La otra mitad: cada vecino se generaba mutando el vecino anterior, asi que la
    serie se alejaba del punto explorado en vez de recorrer su vecindario. Con
    `alteration_limit=1.0` ningun vecino puede quedar a mas de 1.0 del punto actual.
    """
    from metagen.metaheuristics import SA

    dominio = Domain()
    dominio.define_real("x", -5.0, 5.0)

    vistos = []

    def fitness(solucion):
        vistos.append(solucion["x"])
        return abs(solucion["x"])

    algoritmo = SA(dominio, fitness, warmup_iterations=0, max_iterations=1,
                   neighbor_population_size=10, alteration_limit=1.0, seed=5)
    algoritmo.run()

    partida, vecinos = vistos[0], vistos[1:]
    fuera = [v for v in vecinos if abs(v - partida) > 1.0 + 1e-9]
    assert not fuera, (
        f"{len(fuera)} de {len(vecinos)} vecinos se salen del vecindario de "
        f"{partida:.4f}: {[round(v, 4) for v in fuera]}"
    )


@pytest.mark.parametrize("valor,esperado", [
    (1.5, True),
    (1, True),                      # un entero es un real perfectamente valido
    (3, True),
    (True, False),                  # bool es subclase de int, pero no es un numero aqui
    ("1.5", False),
    (None, False),
], ids=["float", "int", "otro int", "bool", "cadena", "None"])
def test_a08_una_definicion_real_acepta_enteros_y_rechaza_booleanos(valor, esperado):
    """A-08: `RealDefinition` exigia `isinstance(value, float)`, y `isinstance(1, float)`
    es False, asi que rechazaba 1 y cualquier float de numpy."""
    from metagen.framework.domain import RealDefinition

    assert RealDefinition(0.0, 10.0).check_value(valor) is esperado


@pytest.mark.parametrize("valor,esperado", [
    (3, True),
    (True, False),                  # el fallo que cita el hallazgo
    (3.0, False),                   # un real no es un entero
    ("3", False),
], ids=["int", "bool", "float", "cadena"])
def test_a08_una_definicion_entera_rechaza_booleanos(valor, esperado):
    from metagen.framework.domain import IntegerDefinition

    assert IntegerDefinition(0, 10).check_value(valor) is esperado


def test_a08_los_escalares_de_numpy_valen_y_se_normalizan():
    """La otra mitad: `np.float32` se rechazaba, y lo que quedaba guardado era el valor
    tal cual llegara. Ahora se acepta y lo que el usuario lee es un tipo nativo."""
    numpy = pytest.importorskip("numpy")

    dominio = Domain()
    dominio.define_real("x", 0.0, 10.0)
    dominio.define_integer("n", 0, 10)
    solucion = Solution(dominio)

    solucion.set("x", numpy.float32(1.5))
    assert type(solucion["x"]) is float and solucion["x"] == pytest.approx(1.5)

    solucion.set("n", numpy.int64(3))
    assert type(solucion["n"]) is int and solucion["n"] == 3

    # Y un entero en una variable real se guarda como real, no como entero.
    solucion.set("x", 1)
    assert type(solucion["x"]) is float and solucion["x"] == 1.0


def test_a08_un_booleano_se_rechaza_por_ser_booleano():
    """Antes tambien fallaba, pero por accidente y en otro sitio: el conector decia
    «The class True has not been registered», que no explica nada."""
    dominio = Domain()
    dominio.define_integer("n", 0, 10)

    with pytest.raises(Exception) as fallo:
        Solution(dominio).set("n", True)
    assert "registered" not in str(fallo.value)


def test_a10_la_clase_base_no_pierde_el_mejor_aunque_la_subclase_se_olvide():
    """A-10: `_iterate` hacia `self.best_solution = best_individual` sin comparar, asi
    que el elitismo dependia de que cada subclase se acordara.

    Hoy ninguna se olvida —medido: los siete algoritmos dan el mismo resultado antes y
    despues— asi que lo que se prueba es la proteccion, con una subclase que devuelve
    a proposito algo peor de lo que ya habia encontrado.
    """
    from metagen.metaheuristics.base import Metaheuristic

    dominio, fitness = _dominio_y_fitness_de_prueba()

    class Olvidadiza(Metaheuristic):
        def initialize(self, num_solutions=10):
            buena = Solution(dominio)
            buena.set_fitness(1.0)
            return [buena], buena

        def iterate(self, solutions):
            mala = Solution(dominio)
            mala.set_fitness(99.0)          # peor que la inicial, a proposito
            return [mala], mala

        def stopping_criterion(self) -> bool:
            return self.current_iteration >= 3

    algoritmo = Olvidadiza(dominio, fitness, warmup_iterations=0)
    mejor = algoritmo.run()

    assert mejor.get_fitness() == 1.0, (
        f"la clase base ha dejado que la subclase perdiera el mejor: {mejor.get_fitness()}"
    )
    assert algoritmo.best_solution_fitnesses == [1.0, 1.0, 1.0]


def test_a10_una_subclase_sin_criterio_de_parada_no_se_puede_instanciar():
    """La otra mitad: `stopping_criterion` devolvia False por defecto, asi que una
    subclase que se olvidara de implementarlo entraba en un bucle infinito sin decir
    por que. Ahora es abstracto y falla al construirse."""
    from metagen.metaheuristics.base import Metaheuristic

    dominio, fitness = _dominio_y_fitness_de_prueba()

    class SinParada(Metaheuristic):
        def initialize(self, num_solutions=10):
            s = Solution(dominio)
            return [s], s

        def iterate(self, solutions):
            return solutions, solutions[0]

    with pytest.raises(TypeError) as fallo:
        SinParada(dominio, fitness)
    assert "stopping_criterion" in str(fallo.value)


@pytest.mark.parametrize("nombre", ["GA", "SSGA", "Memetic"])
def test_a07_los_geneticos_explican_que_necesitan_el_conector(nombre):
    """A-07: con un `Domain()` normal los tres morian en la primera iteracion con
    `AttributeError: 'Solution' object has no attribute 'crossover'`, que no dice que
    hacer. Ahora fallan al construirse y con instrucciones."""
    import metagen.metaheuristics as paquete

    clase = getattr(paquete, nombre)
    dominio, fitness = _dominio_y_fitness_de_prueba()

    with pytest.raises(ValueError) as fallo:
        clase(dominio, fitness, population_size=4, max_iterations=2, seed=1)

    mensaje = str(fallo.value)
    assert "crossover" in mensaje
    assert "GAConnector" in mensaje


@pytest.mark.parametrize("nombre", ["GA", "SSGA", "Memetic"])
def test_a07_un_conector_propio_con_crossover_vale(nombre):
    """La comprobacion pregunta por la capacidad, no por la clase `GAConnector`: quien
    traiga su propio conector con su propio operador de cruce tiene que seguir
    pudiendo. El conector es el mecanismo de extension del framework."""
    import metagen.metaheuristics as paquete
    from metagen.framework import BaseConnector
    from metagen.framework.domain import (BaseDefinition, CategoricalDefinition,
                                          IntegerDefinition, RealDefinition,
                                          StaticStructureDefinition)
    from metagen.metaheuristics.ga.ga_tools import GASolution, GAStructure
    import metagen.framework.solution as tipos

    class CruceMio(GASolution):
        pass

    class ConectorMio(BaseConnector):
        def __init__(self):
            super().__init__()
            self.register(BaseDefinition, CruceMio, dict)
            self.register(IntegerDefinition, tipos.Integer, int)
            self.register(RealDefinition, tipos.Real, float)
            self.register(CategoricalDefinition, tipos.Categorical, str)
            self.register(StaticStructureDefinition, (GAStructure, "static"), list)

    clase = getattr(paquete, nombre)
    dominio = Domain(connector=ConectorMio())
    dominio.define_real("x", -5.0, 5.0)

    clase(dominio, lambda s: s["x"] ** 2, population_size=4, max_iterations=2, seed=1)


def test_a05_la_sustitucion_del_ssga_mete_a_los_dos_mejores():
    """A-05 quedo **refutado**: la version por valor daba el mismo resultado, porque
    `index()` rescanea la lista tras la primera sustitucion y encuentra al otro
    duplicado. Comprobado con 4096 casos exhaustivos y 200000 aleatorios.

    Este test **no distingue las dos versiones** —pasa con las dos— y esta aqui a
    proposito: fija la propiedad que el bloque debe cumplir, para que un refactor
    futuro que la rompa se vea. Es lo que motivo pasar a trabajar por indices.
    """
    import heapq

    from metagen.metaheuristics import GAConnector

    set_seed(1)
    dominio = Domain(connector=GAConnector())
    dominio.define_integer("n", 0, 9)
    tipo = dominio.get_connector().get_type(dominio.get_core())

    def individuo(valor, fitness):
        s = tipo(dominio, connector=dominio.get_connector())
        s.set("n", valor)
        s.set_fitness(fitness)
        return s

    # Los dos peores son iguales, y los dos hijos los mejoran.
    poblacion = [individuo(1, 1.0), individuo(9, 9.0), individuo(9, 9.0), individuo(2, 2.0)]
    hijos = [individuo(0, 0.1), individuo(3, 0.2)]

    peores = heapq.nlargest(2, range(len(poblacion)),
                            key=lambda i: poblacion[i].get_fitness())
    candidatos = [poblacion[i] for i in peores] + hijos
    mejores = heapq.nsmallest(2, candidatos, key=lambda s: s.get_fitness())
    for indice, reemplazo in zip(peores, mejores):
        poblacion[indice] = reemplazo

    valores = sorted(s["n"] for s in poblacion)
    assert valores == [0, 1, 2, 3], (
        f"los dos hijos deberian haber entrado y los dos peores salido; queda {valores}"
    )


def test_a04_random_search_descarta_el_peor_no_el_ultimo(monkeypatch):
    """A-04: `solutions[:-1]` descartaba el individuo de la ultima posicion, que no
    tiene por que ser el peor; la docstring dice que se preserva el mejor. Medido, la
    poblacion `[3.10, 12.19, 2.28, 18.28, 0.13]` perdia el 0.13 —el mejor— y conservaba
    el 18.28.

    Se anula `mutate` para que los fitness no cambien y se pueda ver quien sobrevive.
    """
    from metagen.metaheuristics import RandomSearch

    dominio, fitness = _dominio_y_fitness_de_prueba()
    algoritmo = RandomSearch(dominio, fitness, population_size=5, max_iterations=1,
                             seed=7)
    algoritmo.pre_execution()
    algoritmo._warmup()
    algoritmo._initialize()

    poblacion = list(algoritmo.current_solutions)
    valores = [s.get_fitness() for s in poblacion]
    peor = max(valores)

    monkeypatch.setattr(Solution, "mutate", lambda self, *a, **k: None)
    nuevas, _ = algoritmo.iterate(poblacion)

    assert len(nuevas) == len(poblacion)
    # El primero es la copia elite; los demas son la poblacion menos el peor.
    supervivientes = sorted(s.get_fitness() for s in nuevas[1:])
    esperado = sorted(v for v in valores if v != peor)
    assert supervivientes == esperado, (
        f"deberia haber descartado el peor ({peor}); poblacion {sorted(valores)}, "
        f"supervivientes {supervivientes}"
    )


def test_f20_la_temperatura_no_baja_de_t_min():
    """La otra mitad: `self.T_min = 1e-8` estaba asignado y no se leia en ningun
    sitio, asi que el enfriamiento tendia a cero y el criterio de Metropolis dejaba
    de aceptar empeoramientos sin que nadie lo dijera."""
    from metagen.metaheuristics import SA

    dominio, fitness = _dominio_y_fitness_de_prueba()
    algoritmo = SA(dominio, fitness, max_iterations=300, initial_temp=1.0,
                   cooling_rate=0.5, seed=1)
    algoritmo.run()

    assert algoritmo.current_temp == algoritmo.T_min


def test_f21_run_no_apaga_un_ray_que_no_arranco():
    """F-21: run() llamaba a ray.shutdown() siempre que Ray estuviera arrancado,
    lo hubiera arrancado el o no.

    Se salta sin Ray instalado, que es el caso del CI.
    """
    ray = pytest.importorskip("ray")
    from metagen.metaheuristics import RandomSearch

    dominio, fitness = _dominio_y_fitness_de_prueba()

    arrancado_aqui = not ray.is_initialized()
    if arrancado_aqui:
        ray.init(num_cpus=1, include_dashboard=False, ignore_reinit_error=True)
    try:
        RandomSearch(
            dominio, fitness, population_size=2, max_iterations=1,
            distributed=True, seed=7,
        ).run()
        assert ray.is_initialized(), (
            "run() ha apagado un runtime de Ray que no habia arrancado el"
        )
    finally:
        if arrancado_aqui and ray.is_initialized():
            ray.shutdown()


_GUION_F24 = """
import sys


class BloqueaRay:
    '''Hace que cualquier `import ray` falle, haya Ray instalado o no.'''

    @staticmethod
    def find_spec(nombre, ruta=None, destino=None):
        if nombre == "ray" or nombre.startswith("ray."):
            raise ModuleNotFoundError("No module named 'ray'", name="ray")
        return None


sys.meta_path.insert(0, BloqueaRay)

from metagen.framework import Domain, Solution
from metagen.metaheuristics import Memetic, GAConnector

dominio = Domain(connector=GAConnector())
dominio.define_real("x", -5.0, 5.0)
dominio.define_real("y", -5.0, 5.0)

memetico = Memetic(
    dominio, lambda s: s["x"] ** 2 + s["y"] ** 2,
    population_size=10, max_iterations=3, neighbor_population_size=3, seed=3,
)
memetico.run()
print("ok")
"""


def test_f11_la_busqueda_local_distribuida_reparte_la_poblacion():
    """F-11: `population[:count]` sin avanzar el cursor, asi que todos los workers
    recibian la misma porcion inicial. Con 9 individuos repartidos en 3, solo se
    buscaba sobre los 3 primeros y la poblacion volvia siendo tres copias de ellos.

    Necesita Ray de verdad, asi que se salta en el CI.
    """
    ray = pytest.importorskip("ray")
    from metagen.metaheuristics.mm.mm_distributed_tools import \
        distributed_population_local_search

    arrancado_aqui = not ray.is_initialized()
    if arrancado_aqui:
        ray.init(num_cpus=3, include_dashboard=False, ignore_reinit_error=True)
    try:
        set_seed(1)
        dominio = Domain()
        dominio.define_integer("id", 0, 100)

        # Identidades distinguibles, para saber quien vuelve.
        poblacion = []
        for i in range(9):
            individuo = Solution(dominio)
            individuo.set("id", i * 10)
            individuo.set_fitness(float(i))
            poblacion.append(individuo)

        entrada = {individuo["id"] for individuo in poblacion}

        # Sin vecinos ni alteracion, la busqueda local devuelve lo que recibe: lo
        # unico que se mide aqui es el reparto.
        salida = distributed_population_local_search(
            poblacion, lambda s: float(s["id"]), neighbor_population_size=0,
            alteration_limit=0.0, distribution_level=1)

        assert {individuo["id"] for individuo in salida} == entrada, (
            "la busqueda local distribuida ha perdido individuos por el camino"
        )
        assert len(salida) == len(poblacion)
    finally:
        if arrancado_aqui and ray.is_initialized():
            ray.shutdown()


def test_f24_el_memetico_no_necesita_ray():
    """F-24: mm_tools importaba ray a nivel de modulo, asi que `Memetic` no existia
    en una instalacion sin el extra distribuido, pese a que el README lo anuncia.

    Se bloquea `ray` en un subproceso en vez de saltar el test cuando esta
    instalado: asi la comprobacion corre en cualquier maquina, y no solo en un
    entorno sin extras como hacia antes.
    """
    resultado = subprocess.run(
        [sys.executable, "-c", _GUION_F24],
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, (
        "el memetico no se puede importar ni ejecutar sin Ray:\n"
        f"{resultado.stdout}{resultado.stderr}"
    )
    assert resultado.stdout.strip().endswith("ok")


def _raiz_del_repo() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2]


def test_p01_la_licencia_declarada_es_la_del_fichero_license():
    """P-01: `setup.cfg` clasificaba el paquete como MIT frente a un `LICENSE` GPL-3.0
    y 40 cabeceras GPLv3 en `src/`. PyPI anunciaba MIT desde la 0.2.0."""
    raiz = _raiz_del_repo()
    setup = (raiz / "setup.cfg").read_text()
    licencia = (raiz / "LICENSE").read_text()

    assert "GNU GENERAL PUBLIC LICENSE" in licencia
    assert "MIT" not in setup
    assert "license = GPL-3.0-or-later" in setup
    assert "GNU General Public License v3 or later (GPLv3+)" in setup
    assert "license_files = LICENSE" in setup


def test_p08_los_extras_declaran_un_requisito_por_linea():
    """P-08: los extras se separaban con ";", que PEP 508 lee como el comienzo de un
    marcador de entorno. En un `.cfg` setuptools parte por ahi y funciona de milagro,
    pero el mismo texto en un `pyproject.toml` perderia en silencio todo lo que vaya
    detras del primer requisito.

    Y comprueba lo que el diagnostico no listaba: que `pytest-csv-params`, que la
    suite necesita, este declarado en alguna parte.
    """
    from importlib.metadata import requires

    setup = (_raiz_del_repo() / "setup.cfg").read_text()
    seccion = setup[setup.index("[options.extras_require]"):]
    seccion = seccion.split("\n[")[0]
    lineas = [l for l in seccion.splitlines()
              if l.startswith("    ") and not l.strip().startswith("#")]
    assert lineas, "no se han encontrado requisitos en los extras"
    for linea in lineas:
        assert ";" not in linea, f"el extra sigue usando ';': {linea!r}"

    declarados = requires("pymetagen-datalabupo") or []
    assert any("pytest-csv-params" in r for r in declarados), (
        "pytest-csv-params, que la suite necesita, no lo declara ningun extra"
    )


def test_p02_la_version_minima_de_python_dice_lo_mismo_en_los_tres_sitios():
    """P-02: el badge del README decia >=3.12, el texto 3.10+ y `python_requires`
    >=3.10. El minimo real es 3.10, por `itertools.pairwise`."""
    raiz = _raiz_del_repo()
    readme = (raiz / "README.md").read_text()
    setup = (raiz / "setup.cfg").read_text()

    assert "python->=3.10" in readme
    assert "Python 3.10+" in readme
    assert "python_requires = >=3.10" in setup


def test_p03_nada_apunta_al_repositorio_antiguo():
    """P-03: badges, enlaces de Colab y las URLs de `setup.cfg` apuntaban a
    `DataLabUPO/MetaGen`; el repositorio vive en
    `Data-Science-Big-Data-Research-Lab/MetaGen`."""
    raiz = _raiz_del_repo()
    ficheros = [raiz / "README.md", raiz / "setup.cfg"]
    ficheros += list((raiz / "docs").rglob("*.rst"))

    culpables = [str(f.relative_to(raiz)) for f in ficheros
                 if "DataLabUPO/MetaGen" in f.read_text()]
    assert not culpables, f"siguen apuntando al repositorio antiguo: {culpables}"


def test_p07_los_csv_de_parametros_no_estan_ignorados():
    """P-07: `.gitignore` excluia `*.csv`, y los parametros de los tests son CSV, asi
    que cualquiera nuevo se quedaba fuera del commit sin que `git status` lo dijera."""
    raiz = _raiz_del_repo()
    candidato = "test/test_parameters/framework_parameters/nuevo_ejemplo.csv"

    resultado = subprocess.run(
        ["git", "check-ignore", "-q", candidato],
        cwd=raiz, capture_output=True, text=True,
    )
    # check-ignore devuelve 0 si el fichero esta ignorado, 1 si no.
    assert resultado.returncode == 1, (
        f"{candidato} sigue ignorado por .gitignore"
    )


def test_p09_el_paquete_lleva_el_marcador_py_typed():
    """P-09: sin el marcador de PEP 561, mypy trata `metagen` como `Any` desde fuera
    del paquete, pese a estar anotado de arriba abajo."""
    raiz = _raiz_del_repo()

    assert (raiz / "src" / "metagen" / "py.typed").is_file()
    # Y tiene que viajar en el paquete construido, no solo estar en el arbol.
    assert "metagen = py.typed" in (raiz / "setup.cfg").read_text()


def test_p04_la_suite_completa_se_recolecta_sin_los_extras_opcionales():
    """P-04: ``pytest test`` abortaba en la recoleccion porque
    ``test/metaheuristics_test/unit_test.py`` importa ``ray`` y, de forma
    transitiva via el dispatcher, ``tensorflow``. Sin esos extras opcionales el
    modulo debe saltarse limpiamente, no tumbar la recoleccion de toda la suite.
    """
    ray_presente = importlib.util.find_spec("ray") is not None
    tf_presente = importlib.util.find_spec("tensorflow") is not None
    if ray_presente and tf_presente:
        pytest.skip(
            "ray y tensorflow instalados: sin ningun extra ausente el fallo de "
            "recoleccion no se observa"
        )
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    resultado = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "test"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, (
        "la recoleccion de `pytest test` aborto sin los extras opcionales "
        f"(exit {resultado.returncode}):\n{resultado.stdout}{resultado.stderr}"
    )


_GUION_A11 = """
import logging

# Un logger que no es de MetaGen, creado antes de importar nada.
ajeno = logging.getLogger("la_aplicacion")
assert not hasattr(ajeno, "detailed_info"), "el logger ajeno ya traia detailed_info"

import metagen.logging.metagen_logger as m

# 1. El parcheo de logging.Logger repartia detailed_info a todo el proceso.
assert not hasattr(ajeno, "detailed_info"), "importar MetaGen ha parcheado logging.Logger"
assert not hasattr(logging.getLogger("otra_app"), "detailed_info")
assert hasattr(m.metagen_logger, "detailed_info"), "el logger de MetaGen lo ha perdido"

# 2. Al importar, una libreria solo debe instalar un NullHandler.
tipos = [type(h).__name__ for h in m.metagen_logger.handlers]
assert tipos == ["NullHandler"], tipos

# 3. get_remote_metagen_logger anadia un handler nuevo en cada llamada.
remoto = m.get_remote_metagen_logger()
for _ in range(19):
    m.get_remote_metagen_logger()
assert len(remoto.handlers) == 1, len(remoto.handlers)

# 4. set_metagen_logger_level hacia None.close() sin handler de consola, y dos
#    llamadas seguidas deben dejar uno solo.
m.set_metagen_logger_level(logging.INFO)
m.set_metagen_logger_level(m.DETAILED_INFO)
consolas = [h for h in m.metagen_logger.handlers if h.get_name() == "console"]
assert len(consolas) == 1, len(consolas)
assert m.metagen_logger.level == m.DETAILED_INFO

print("ok")
"""


def test_a11_el_logger_no_toca_el_logging_del_proceso():
    """A-11: el modulo parcheaba `logging.Logger`, instalaba un StreamHandler al
    importarse, acumulaba un handler por llamada a `get_remote_metagen_logger` y
    reventaba en `set_metagen_logger_level` si no habia handler de consola.

    Va en un subproceso porque las tres primeras se deciden en el momento de
    importar, y dentro de pytest el modulo ya esta importado.
    """
    resultado = subprocess.run(
        [sys.executable, "-c", _GUION_A11],
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, f"{resultado.stdout}{resultado.stderr}"
    assert resultado.stdout.strip().endswith("ok")


def test_a12_tensorboard_esta_apagado_por_defecto(tmp_path, monkeypatch):
    """A-12: TensorBoard se activaba por el mero hecho de estar instalado, sin
    forma de apagarlo, asi que un barrido de cientos de configuraciones dejaba
    cientos de directorios en `logs/`."""
    from metagen.metaheuristics import RandomSearch

    dominio, fitness = _dominio_y_fitness_de_prueba()

    monkeypatch.chdir(tmp_path)
    for semilla in range(5):
        algoritmo = RandomSearch(dominio, fitness, population_size=3,
                                 max_iterations=2, seed=semilla)
        assert algoritmo.logger is None
        algoritmo.run()

    escrito = list(tmp_path.iterdir())
    assert escrito == [], f"cinco ejecuciones por defecto han escrito {escrito}"


def test_a12_tensorboard_se_enciende_al_pedirlo(tmp_path, monkeypatch):
    """El apagado no puede llevarse por delante la funcionalidad: con `log_dir`
    explicito TensorBoard sigue registrando."""
    pytest.importorskip("tensorboard")
    from metagen.metaheuristics import RandomSearch

    dominio, fitness = _dominio_y_fitness_de_prueba()

    monkeypatch.chdir(tmp_path)
    algoritmo = RandomSearch(dominio, fitness, population_size=3, max_iterations=2,
                             seed=0, log_dir="mis_curvas")
    assert algoritmo.logger is not None
    algoritmo.run()

    assert (tmp_path / "mis_curvas").is_dir()


# --------------------------------------------------------------------------
# CVOA
# --------------------------------------------------------------------------


def test_f08_aislar_un_individuo_no_bloquea_la_hebra():
    """F-08: isolate_individual_conditional_state toma self.lock y dentro llama a
    get_individual_state, que lo vuelve a tomar. Un threading.Lock no es
    reentrante, asi que la hebra se bloqueaba contra si misma.

    Se ejecuta en una hebra demonio con espera limitada: si el fallo vuelve, el
    test falla en vez de colgar la suite entera.
    """
    from metagen.metaheuristics.cvoa.common_tools import IndividualState
    from metagen.metaheuristics.cvoa.local_tools import LocalPandemicState

    dominio, _ = _dominio_y_fitness_de_prueba()
    estado = LocalPandemicState(Solution(dominio))
    individuo = Solution(dominio)

    hilo = threading.Thread(
        target=estado.isolate_individual_conditional_state,
        args=(individuo, IndividualState(False, False, False)),
        daemon=True,
    )
    hilo.start()
    hilo.join(timeout=10)

    assert not hilo.is_alive(), (
        "isolate_individual_conditional_state se ha quedado bloqueada sobre su "
        "propio cerrojo"
    )
    # Y ademas hace su trabajo: el individuo cumple el estado pedido, luego se aisla.
    assert individuo in estado.isolated


def test_f09_insertar_en_el_conjunto_de_muertos_no_revienta():
    """F-09: la rama 'd' hacia bag.remove(best_dead) sin comprobar pertenencia,
    mientras que la de superspreaders si comprobaba. `best_dead` arranca siendo
    una solucion recien construida que nunca estuvo en ningun conjunto.
    """
    from metagen.metaheuristics.cvoa.common_tools import insert_into_set_strain

    set_seed(1)
    dominio, fitness = _dominio_y_fitness_de_prueba()

    # Tal como los inicializa CVOA: soluciones nuevas, ajenas a cualquier bolsa.
    peor_superspreader = Solution(dominio)
    mejor_muerto = Solution(dominio)
    candidato = Solution(dominio)
    candidato.evaluate(fitness)

    bolsa = set()
    # remaining=0 lleva a la rama del else, que es donde vive el fallo.
    _, _, insertado = insert_into_set_strain(
        peor_superspreader, mejor_muerto, bolsa, candidato, 0, "d")

    assert insertado
    assert candidato in bolsa


def test_f10_el_peor_superspreader_arranca_siendo_el_mejor():
    """F-10: el comentario dice «inicialmente la mejor solucion» pero el constructor
    por defecto creaba la peor, asi que `to_insert > worst_superspreader` no se
    cumplia nunca y el reemplazo del peor superspreader no se ejecutaba jamas.
    """
    from metagen.metaheuristics.cvoa.cvoa_local import CVOA
    from metagen.metaheuristics.cvoa.local_tools import LocalPandemicState

    set_seed(1)
    dominio, fitness = _dominio_y_fitness_de_prueba()
    cepa = CVOA(LocalPandemicState(Solution(dominio)), dominio, fitness)

    assert cepa.worst_superspreader.get_fitness() == -math.inf
    # Y su pareja simetrica sigue siendo la peor, que es lo correcto para ella.
    assert cepa.best_dead.get_fitness() == math.inf


def test_f10_el_reemplazo_del_peor_superspreader_se_ejecuta():
    """La consecuencia: con el conjunto lleno, un candidato peor que el peor
    superspreader tiene que poder sustituirlo. Es la diversificacion que el codigo
    documenta y que no llegaba a correr."""
    from metagen.metaheuristics.cvoa.common_tools import insert_into_set_strain
    from metagen.metaheuristics.cvoa.cvoa_local import CVOA
    from metagen.metaheuristics.cvoa.local_tools import LocalPandemicState

    set_seed(1)
    dominio, fitness = _dominio_y_fitness_de_prueba()
    cepa = CVOA(LocalPandemicState(Solution(dominio)), dominio, fitness)

    candidato = Solution(dominio)
    candidato.evaluate(fitness)

    bolsa = set()
    # remaining=0: el conjunto esta lleno, asi que toca reemplazar al peor.
    _, _, insertado = insert_into_set_strain(
        cepa.worst_superspreader, cepa.best_dead, bolsa, candidato, 0, "s")

    assert insertado
    assert candidato in bolsa


def test_f23_una_cepa_no_muere_al_encontrar_la_primera_mejora():
    """F-23: `third_condition = best_strain_solution_found and self.time > 1`, con
    una bandera que nadie reiniciaba, mataba la cepa en la iteracion siguiente a su
    primera mejora: se paraba justamente porque estaba funcionando.
    """
    from metagen.metaheuristics import cvoa_launcher
    from metagen.metaheuristics.cvoa import cvoa_local
    from metagen.metaheuristics.cvoa.common_tools import StrainProperties

    iteraciones = {}
    run_original = cvoa_local.CVOA.run

    def run_espia(self):
        resultado = run_original(self)
        iteraciones["hechas"] = self.time
        return resultado

    cvoa_local.CVOA.run = run_espia
    try:
        dominio, fitness = _dominio_y_fitness_de_prueba()
        cvoa_launcher([StrainProperties(strain_id="S1", pandemic_duration=4)],
                      dominio, fitness, seed=0)
    finally:
        cvoa_local.CVOA.run = run_original

    assert iteraciones["hechas"] > 4, (
        f"la cepa se detuvo en la iteracion {iteraciones['hechas']} de las 4 "
        "declaradas en pandemic_duration"
    )


def test_f23_el_estancamiento_si_detiene_la_cepa_cuando_se_pide():
    """La condicion no se elimina, se convierte en lo que decia ser: una parada por
    estancamiento, y ahora es opcional."""
    from metagen.metaheuristics.cvoa.common_tools import StrainProperties

    propiedades = StrainProperties()
    assert propiedades.max_iterations_without_improvement is None

    # Y se puede pedir sin romper la construccion posicional que ya existia.
    con_parada = StrainProperties(strain_id="S1", max_iterations_without_improvement=2)
    assert con_parada.max_iterations_without_improvement == 2
    assert con_parada.pandemic_duration == StrainProperties().pandemic_duration


def test_f23_el_tiempo_de_ejecucion_se_reporta_en_segundos():
    """La segunda mitad: `timedelta(milliseconds=t2 - t1)` sobre un `time()` que da
    segundos reportaba una duracion mil veces mas corta."""
    fuente = pathlib.Path(
        importlib.util.find_spec("metagen.metaheuristics.cvoa.local_launcher").origin
    ).read_text()
    fuente_distribuida = pathlib.Path(
        importlib.util.find_spec("metagen.metaheuristics.cvoa.distributed_launcher").origin
    ).read_text()

    for texto in (fuente, fuente_distribuida):
        assert "timedelta(seconds=t2 - t1)" in texto
        assert "timedelta(milliseconds=" not in texto


# --------------------------------------------------------------------------
# Duplicacion (A-09)
# --------------------------------------------------------------------------


def _fuente(modulo: str) -> str:
    return pathlib.Path(importlib.util.find_spec(modulo).origin).read_text()


def test_a09_hay_una_sola_implementacion_de_local_search():
    """A-09: `tools.py` y `mm_tools.py` llevaban la misma `local_search`, identica
    byte a byte. La de `tools.py` no la usaba nadie y la de `mm_tools.py` si, asi
    que la copia viva estaba en el modulo especifico del memetico."""
    from metagen.metaheuristics import tools
    from metagen.metaheuristics.mm import mm_tools

    assert mm_tools.local_search is tools.local_search


def test_a09_los_dos_cvoa_exponen_los_mismos_metodos():
    """A-09 sigue abierto: los dos CVOA siguen duplicados a proposito, y su
    reestructuracion se hara aislada. Mientras tanto, esto detecta que se le anada
    o se le quite un metodo a uno y no al otro.
    """
    import ast

    def metodos(modulo, clase):
        arbol = ast.parse(_fuente(modulo))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.ClassDef) and nodo.name == clase:
                return {m.name for m in nodo.body if isinstance(m, ast.FunctionDef)}
        raise AssertionError(f"no se encontro la clase {clase} en {modulo}")

    local = metodos("metagen.metaheuristics.cvoa.cvoa_local", "CVOA")
    distribuido = metodos("metagen.metaheuristics.cvoa.cvoa_distributed", "DistributedCVOA")

    assert local == distribuido, (
        f"solo en el local: {sorted(local - distribuido)}; "
        f"solo en el distribuido: {sorted(distribuido - local)}"
    )


def test_a09_los_dos_cvoa_informan_de_la_iteracion_una_sola_vez():
    """Una divergencia real que dejo la duplicacion: el gemelo distribuido imprimia
    el informe de iteracion dos veces. No era solo ruido: cada uno hace un `ray.get`
    entre procesos, y la f-string se evalua aunque el nivel de log lo descarte."""
    local = _fuente("metagen.metaheuristics.cvoa.cvoa_local").count("Iteration #")
    distribuido = _fuente("metagen.metaheuristics.cvoa.cvoa_distributed").count("Iteration #")

    assert local == distribuido == 1, (
        f"informes de iteracion: local {local}, distribuido {distribuido}"
    )


# --------------------------------------------------------------------------
# Documentacion
# --------------------------------------------------------------------------


def _bloque_de_codigo(modulo: str) -> str:
    """Extrae el `.. code-block:: python` de la docstring de clase de un modulo."""
    origen = pathlib.Path(importlib.util.find_spec(modulo).origin).read_text()
    inicio = origen.index(".. code-block:: python")
    inicio = origen.index("\n", inicio) + 1
    fin = origen.index('"""', inicio)
    lineas = [linea[8:] if linea.startswith(" " * 8) else linea
              for linea in origen[inicio:fin].splitlines()]
    return "\n".join(lineas)


@pytest.mark.parametrize("modulo", [
    "metagen.metaheuristics.rs.random_search",
    "metagen.metaheuristics.tpe.tpe",
    "metagen.metaheuristics.mm.memetic",
    "metagen.metaheuristics.cvoa.cvoa_local",
])
def test_p10_los_ejemplos_de_las_docstrings_usan_la_api_de_verdad(modulo, monkeypatch):
    """P-10: los ejemplos publicados llamaban a `domain.defineInteger(0, 1)`, que no
    existe —el metodo es `define_integer(nombre, min, max)`—, el de CVOA importaba
    `CVOA`, que no se exporta, y usaba `CVOA.initialize_pandemic(...)` de una version
    anterior. Son las paginas que publica readthedocs.

    Se ejecuta el ejemplo entero salvo la optimizacion: `run()` y `cvoa_launcher` se
    sustituyen por dobles. Correrlos de verdad son decenas de miles de evaluaciones
    (y minutos, en CVOA), y la busqueda en si no es donde estaban los fallos: lo que
    aqui se comprueba es que los imports resuelven, que los metodos del dominio
    existen y que los constructores aceptan lo que el ejemplo les pasa.
    """
    from metagen.metaheuristics import base as base_module

    monkeypatch.setattr(base_module.Metaheuristic, "run", lambda self: None)

    lanzamientos = []
    import metagen.metaheuristics as paquete
    monkeypatch.setattr(
        paquete, "cvoa_launcher",
        lambda strains, domain, fitness_function, **kwargs: lanzamientos.append(
            (strains, domain, fitness_function)))

    exec(compile(_bloque_de_codigo(modulo), f"<ejemplo de {modulo}>", "exec"), {})


def _dominio_y_fitness_de_prueba():
    """Dominio minimo con una variable real y una entera, y su fitness."""
    dominio = Domain()
    dominio.define_real("x", -5.0, 5.0)
    dominio.define_integer("n", 0, 100)
    return dominio, lambda solucion: (solucion["x"] - 1.234) ** 2 + abs(solucion["n"] - 42)


def test_a06_la_misma_semilla_reproduce_la_ejecucion():
    """A-06: sin control de semilla no se podia repetir una ejecucion.

    Se comprueban los dos generadores, porque MetaGen esta partido: TPE tira de
    NumPy y el resto de la libreria del `random` de la biblioteca estandar. Una
    sola semilla tiene que cubrir ambos.
    """
    from metagen.metaheuristics import RandomSearch, TPE

    dominio, fitness = _dominio_y_fitness_de_prueba()
    primera = RandomSearch(dominio, fitness, population_size=5, max_iterations=4, seed=7).run()
    segunda = RandomSearch(dominio, fitness, population_size=5, max_iterations=4, seed=7).run()
    assert primera.get_fitness() == segunda.get_fitness(), (
        "dos ejecuciones con la misma semilla han dado resultados distintos"
    )

    dominio, fitness = _dominio_y_fitness_de_prueba()
    una = TPE(dominio, fitness, max_iterations=3, warmup_iterations=2,
              candidate_pool_size=4, seed=5).run()
    otra = TPE(dominio, fitness, max_iterations=3, warmup_iterations=2,
               candidate_pool_size=4, seed=5).run()
    assert una.get_fitness() == otra.get_fitness(), (
        "TPE no es reproducible: la semilla no alcanza al generador de NumPy"
    )


def test_a06_semillas_distintas_dan_ejecuciones_distintas():
    """A-06: la semilla tiene que sembrar de verdad, no quedarse en un adorno."""
    from metagen.metaheuristics import RandomSearch

    dominio, fitness = _dominio_y_fitness_de_prueba()
    una = RandomSearch(dominio, fitness, population_size=5, max_iterations=4, seed=7).run()
    otra = RandomSearch(dominio, fitness, population_size=5, max_iterations=4, seed=99).run()
    assert una.get_fitness() != otra.get_fitness(), (
        "dos semillas distintas han dado el mismo resultado: la semilla no se aplica"
    )


_GUION_F07 = """
import sys

def hook_de_la_aplicacion(tipo, excepcion, traza):
    pass

sys.excepthook = hook_de_la_aplicacion

import metagen
import metagen.framework

print(sys.excepthook is hook_de_la_aplicacion)
"""


def test_f07_importar_metagen_no_toca_el_excepthook_del_proceso():
    """F-07: metagen/__init__.py instalaba su propio sys.excepthook al importarse.

    Hace falta un subproceso: dentro de la sesion de pytest el paquete ya esta
    importado y el hook ya estaria puesto.

    Se importa `metagen.framework`, no `metagen.metaheuristics`: ese arrastra Ray,
    que instala su propio excepthook. Eso es cosa de Ray, no de MetaGen.
    """
    resultado = subprocess.run(
        [sys.executable, "-c", _GUION_F07],
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, f"{resultado.stdout}{resultado.stderr}"
    assert resultado.stdout.strip() == "True", (
        "importar MetaGen ha reemplazado el sys.excepthook de quien lo importa"
    )


_GUION_F26 = """
from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed

set_seed(7)
dominio = Domain()
for nombre in ("a", "b", "c", "d", "e", "f"):
    dominio.define_real(nombre, -5.0, 5.0)
solucion = Solution(dominio)
for _ in range(5):
    solucion.mutate()
print([round(solucion[n], 6) for n in ("a", "b", "c", "d", "e", "f")])
"""


def test_f26_la_misma_semilla_reproduce_entre_procesos():
    """F-26: Solution.mutate recorria un `set` de nombres de variable.

    El orden de iteracion de un conjunto de cadenas sigue a sus hashes, que Python
    aleatoriza en cada arranque, y ese orden decide que sorteo le toca a cada
    variable. Por eso hay que cruzar la frontera del proceso para verlo: dentro de
    una misma ejecucion el fallo es invisible.

    Se fijan dos PYTHONHASHSEED distintos en vez de confiar en los aleatorios, para
    que el test sea determinista y no acierte o falle por suerte. Se comparan las
    variables una a una: un agregado como la suma no lo detecta, porque los valores
    sorteados son los mismos y lo unico que cambia es a quien le toca cada uno.
    """
    salidas = []
    for semilla_de_hash in ("0", "1"):
        entorno = dict(os.environ, PYTHONHASHSEED=semilla_de_hash)
        resultado = subprocess.run(
            [sys.executable, "-c", _GUION_F26],
            capture_output=True,
            text=True,
            env=entorno,
        )
        assert resultado.returncode == 0, (
            f"el subproceso con PYTHONHASHSEED={semilla_de_hash} fallo:\n"
            f"{resultado.stdout}{resultado.stderr}"
        )
        salidas.append(resultado.stdout.strip())

    assert salidas[0] == salidas[1], (
        "la misma semilla da resultados distintos en dos procesos:\n"
        f"  PYTHONHASHSEED=0 -> {salidas[0]}\n"
        f"  PYTHONHASHSEED=1 -> {salidas[1]}"
    )


def test_a06_metagen_no_toca_el_generador_global_del_usuario():
    """A-06: MetaGen usa sus propios generadores, no el `random` del proceso.

    Es la diferencia entre sembrar MetaGen y llamar a `random.seed()`: lo segundo
    reconfiguraria tambien el codigo de quien nos llama.
    """
    from metagen.metaheuristics import RandomSearch

    dominio, fitness = _dominio_y_fitness_de_prueba()

    random.seed(1234)
    esperado = [random.random() for _ in range(3)]

    random.seed(1234)
    RandomSearch(dominio, fitness, population_size=5, max_iterations=3, seed=7).run()
    obtenido = [random.random() for _ in range(3)]

    assert esperado == obtenido, (
        "ejecutar una metaheuristica ha alterado el estado del `random` global"
    )


def test_el_indice_de_audit_coincide_con_las_casillas():
    """El indice de AUDIT.md tiene que cubrir todos los hallazgos y estar al dia.

    No prueba codigo, protege el documento: el indice es una segunda copia del
    estado de cada hallazgo y se desincronizaria en cuanto alguien cierre uno y
    solo marque la casilla. Aqui salta en cuanto pasa.
    """
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    texto = (repo_root / "AUDIT.md").read_text(encoding="utf-8")

    indice = {
        m.group(2): m.group(1) == "✅"
        for m in re.finditer(r"^\| (✅|⬜) \| `([FAP]-\d\d)` \|", texto, re.M)
    }
    casillas = {}
    for m in re.finditer(r"^### \[([ x])\] (F-\d\d)", texto, re.M):
        casillas[m.group(2)] = m.group(1) == "x"
    for m in re.finditer(r"^- \*\*\[([ x])\] ([AP]-\d\d)", texto, re.M):
        casillas[m.group(2)] = m.group(1) == "x"

    assert casillas, "no se ha reconocido ninguna casilla en AUDIT.md"
    assert set(indice) == set(casillas), (
        f"faltan en el indice: {sorted(set(casillas) - set(indice))}; "
        f"sobran en el indice: {sorted(set(indice) - set(casillas))}"
    )
    desacuerdos = {k: (indice[k], casillas[k]) for k in indice if indice[k] != casillas[k]}
    assert not desacuerdos, (
        "el indice y las casillas discrepan (indice, casilla): "
        f"{desacuerdos}"
    )


def test_p06_el_workflow_de_ci_ejecuta_la_suite_que_debe_estar_verde():
    """P-06: no habia `.github/workflows`, asi que nada comprobaba la suite al
    subir cambios.

    Se comprueba el contenido del workflow, no solo su existencia. Tres cosas
    tienen que seguir siendo ciertas o el CI deja de servir para lo que se monto:

    - ejecuta la suite que debe estar verde;
    - acaba teniendo `pytest-csv-params`, sin el cual `solution_test.py` ni se
      recolecta. Desde P-08 lo declara el extra `test`, asi que vale con que el
      CI lo instale por su nombre o por el extra;
    - **no** instala los extras opcionales, porque un entorno sin Ray es el
      unico donde F-24 es observable.

    No se comprueba el `continue-on-error` del job de mypy a proposito: esa
    linea desaparece al cerrar P-11.
    """
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    workflow = repo_root / ".github" / "workflows" / "ci.yml"
    assert workflow.is_file(), f"no existe el workflow de CI en {workflow}"

    texto = workflow.read_text(encoding="utf-8")

    assert "pytest test" in texto, (
        "el workflow no ejecuta la suite que debe estar verde"
    )

    instalaciones = [
        linea.strip()
        for linea in texto.splitlines()
        if "pip install" in linea
    ]
    # Por su nombre, o por el extra que lo declara desde P-08. Lo que se protege
    # es que el CI acabe teniendolo, no como se escriba la linea.
    por_el_nombre = any("pytest-csv-params" in linea for linea in instalaciones)
    por_el_extra = any("[test]" in linea for linea in instalaciones) and any(
        "pytest-csv-params" in r for r in (requires("pymetagen-datalabupo") or []))
    assert por_el_nombre or por_el_extra, (
        "el CI no acaba con pytest-csv-params: framework_test/solution_test.py no "
        "se llegaria a recolectar"
    )

    extras = [
        linea
        for linea in instalaciones
        for extra in ("ray", "tensorflow", "[all]", "[distributed]")
        if extra in linea
    ]
    assert not extras, (
        "el CI instala extras opcionales y eso oculta F-24, que solo se observa "
        f"sin Ray: {extras}"
    )

    for version in ("3.10", "3.11", "3.12"):
        assert f'"{version}"' in texto, (
            f"la matriz del CI no cubre Python {version}, dentro del "
            "python_requires >=3.10 declarado en setup.cfg"
        )


# --------------------------------------------------------------------------------
# A-01 · Sin seleccion de padres: todos los cruces usan la misma pareja
# --------------------------------------------------------------------------------

def _dominio_ga():
    """Dominio de dos variables reales con el conector que sabe cruzar."""
    from metagen.metaheuristics import GAConnector

    dominio = Domain(connector=GAConnector())
    dominio.define_real("x", -5.12, 5.12)
    dominio.define_real("y", -5.12, 5.12)
    return dominio, lambda solucion: solucion["x"] ** 2 + solucion["y"] ** 2


def test_a01_el_torneo_no_es_seleccion_por_truncamiento():
    """A-01: coger siempre a los dos mejores es truncamiento con el corte mas
    agresivo posible. El torneo tiene que poder devolver a otro."""
    from metagen.framework.rng import set_seed
    from metagen.metaheuristics.ga.ga_tools import tournament_selection

    dominio, _ = _dominio_ga()
    poblacion = []
    for posicion in range(10):
        individuo = Solution(dominio)
        individuo.set_fitness(float(posicion))      # el 0 es el mejor
        poblacion.append(individuo)

    set_seed(0)
    elegidos = {tournament_selection(poblacion).get_fitness() for _ in range(50)}

    assert len(elegidos) > 1, (
        f"el torneo devuelve siempre al mismo individuo: {elegidos}"
    )
    assert max(elegidos) < 9.0, (
        "el torneo no ejerce ninguna presion: llega a devolver al peor de los diez"
    )


@pytest.mark.parametrize("nombre", ["GA", "Memetic"])
def test_a01_los_cruces_de_una_generacion_no_usan_la_misma_pareja(nombre, monkeypatch):
    """A-01: `best_parents` se calculaba fuera del bucle, asi que los cinco cruces de
    cada generacion se hacian entre los dos mismos individuos. Medido antes del
    arreglo: una sola pareja en las cinco, la poblacion pasaba de 10 puntos distintos
    a 2, y desde la segunda generacion los dos padres eran el mismo punto, con lo que
    el cruce devolvia al padre y dejaba de recombinar."""
    import metagen.metaheuristics.ga.ga as modulo_ga
    import metagen.metaheuristics.mm.memetic as modulo_mm
    from metagen.metaheuristics import GA, GAConnector, Memetic

    modulo = {"GA": modulo_ga, "Memetic": modulo_mm}[nombre]
    original = modulo.yield_two_children
    parejas = []

    def espia(padres, mutation_rate, fitness_function):
        parejas.append((id(padres[0]), id(padres[1])))
        return original(padres, mutation_rate, fitness_function)

    monkeypatch.setattr(modulo, "yield_two_children", espia)

    dominio, fitness = _dominio_ga()
    if nombre == "GA":
        algoritmo = GA(dominio, fitness, population_size=10, max_iterations=3, seed=0)
    else:
        algoritmo = Memetic(dominio, fitness, population_size=10, max_iterations=3,
                            neighbor_population_size=3, seed=0)
    algoritmo.run()

    primera_generacion = parejas[:5]          # population_size // 2 cruces
    assert len(set(primera_generacion)) > 1, (
        f"{nombre} cruza la misma pareja en los cinco cruces de una generacion: "
        f"{primera_generacion}"
    )
