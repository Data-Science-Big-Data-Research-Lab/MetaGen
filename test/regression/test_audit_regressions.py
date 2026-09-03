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

import importlib.util
import random

import pytest

from metagen.framework import Domain, Solution


# --------------------------------------------------------------------------
# Dominio: tipos y definiciones
# --------------------------------------------------------------------------


@pytest.mark.xfail(
    reason="F-01: el suelo `if result < step` de _closest_number hace inalcanzable "
    "todo valor por debajo de step",
    strict=True,
)
def test_f01_un_real_con_step_cubre_todo_su_dominio():
    random.seed(0)
    dom = Domain()
    dom.define_real("x", -5.0, 5.0, 1.0)
    valores = {round(Solution(dom)["x"], 6) for _ in range(300)}
    assert min(valores) < 0.0, (
        f"un real en [-5, 5] con step 1 solo genera {sorted(valores)}: "
        "los valores negativos y el cero son inalcanzables"
    )


@pytest.mark.xfail(
    reason="F-12: el conector por defecto es un argumento por defecto mutable, "
    "evaluado una sola vez al importar",
    strict=True,
)
def test_f12_cada_domain_tiene_su_propio_conector():
    assert Domain().get_connector() is not Domain().get_connector()


@pytest.mark.xfail(
    reason="F-16: `elif mode == ('d_a', 'd_g')` compara un str con una tupla, "
    "asi que ninguna rama de mensajes de definicion se ejecuta",
    strict=True,
)
def test_f16_el_mensaje_de_variable_ya_definida_es_legible():
    dom = Domain()
    dom.define_integer("i", 0, 10)
    with pytest.raises(ValueError) as exc:
        dom.define_integer("i", 0, 5)
    mensaje = str(exc.value)
    assert "DEFINITION error" in mensaje, mensaje
    assert "already defined" in mensaje, mensaje


@pytest.mark.xfail(
    reason="F-17: is_categories_value usa pairwise, que solo compara elementos "
    "adyacentes",
    strict=True,
)
def test_f17_las_categorias_duplicadas_se_rechazan():
    with pytest.raises(ValueError):
        Domain().define_categorical("c", ["a", "b", "a"])


@pytest.mark.xfail(
    reason="F-17: `len(value) >= 2` impide declarar un hiperparametro fijado a "
    "un unico valor",
    strict=True,
)
def test_f17_una_sola_categoria_es_valida():
    dom = Domain()
    dom.define_categorical("c", ["solo"])
    assert Solution(dom)["c"] == "solo"


@pytest.mark.xfail(
    reason="F-18: StaticStructureDefinition se construye con meta-tipo D mientras "
    "get_attributes devuelve S",
    strict=True,
)
def test_f18_una_estructura_estatica_se_identifica_como_static():
    dom = Domain()
    dom.define_static_structure("v", 3)
    dom.set_structure_to_integer("v", 0, 10)
    definicion = dom.get_core().get("v")
    assert definicion.get_type() == definicion.get_attributes()[0]


# --------------------------------------------------------------------------
# Solution
# --------------------------------------------------------------------------


@pytest.mark.xfail(
    reason="F-14: sys.float_info.min es +2.2e-308, no menos infinito",
    strict=True,
)
def test_f14_el_centinela_de_mejor_fitness_es_menor_que_cualquier_objetivo():
    dom = Domain()
    dom.define_integer("i", 0, 10)
    assert Solution(dom, best=True).get_fitness() < -1e300


@pytest.mark.xfail(
    reason="F-15: __hash__ usa dict.__hash__ (que es None), asi que solo depende "
    "del fitness",
    strict=True,
)
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


@pytest.mark.xfail(
    reason="F-15: el fitness entra en el hash, asi que dos soluciones iguales "
    "con distinto fitness rompen el invariante a == b => hash(a) == hash(b)",
    strict=True,
)
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


# --------------------------------------------------------------------------
# Structure
# --------------------------------------------------------------------------


def _estructura_estatica(longitud=3, semilla=4):
    random.seed(semilla)
    dom = Domain()
    dom.define_static_structure("v", longitud)
    dom.set_structure_to_integer("v", 0, 100)
    return Solution(dom).get("v")


@pytest.mark.xfail(
    reason="F-05: Structure._convert crea una instancia nueva con valor aleatorio "
    "y descarta el valor de entrada",
    strict=True,
)
def test_f05_asignar_un_elemento_conserva_el_valor():
    st = _estructura_estatica()
    st[0] = 42
    assert st[0] == 42


@pytest.mark.xfail(
    reason="F-05: mismo _convert, por la via de append",
    strict=True,
)
def test_f05_append_conserva_el_valor():
    st = _estructura_estatica()
    st.append(7)
    assert st[len(st) - 1] == 7


@pytest.mark.xfail(
    reason="F-06: Structure.set pide el tipo con get_type(definition) en vez de "
    "get_type(definition.get_base())",
    strict=True,
)
def test_f06_set_admite_una_lista_de_builtins():
    st = _estructura_estatica()
    st.set([1, 2, 3])
    assert [st[i] for i in range(3)] == [1, 2, 3]


@pytest.mark.xfail(
    reason="F-06: Structure.insert llama a insert sobre el elemento, no sobre la "
    "lista",
    strict=True,
)
def test_f06_insert_inserta_en_la_lista():
    st = _estructura_estatica()
    longitud = len(st)
    st.insert(0, 5)
    assert len(st) == longitud + 1
    assert st[0] == 5


@pytest.mark.xfail(
    reason="F-19: randrange(min, max) excluye el extremo superior, mientras que "
    "check_length acepta min <= len <= max",
    strict=True,
)
def test_f19_una_estructura_dinamica_alcanza_su_longitud_maxima():
    random.seed(5)
    dom = Domain()
    dom.define_dynamic_structure("d", 2, 5)
    dom.set_structure_to_integer("d", 0, 10)
    longitudes = {len(Solution(dom).get("d")) for _ in range(300)}
    assert longitudes == {2, 3, 4, 5}, sorted(longitudes)


@pytest.mark.xfail(
    reason="F-19: randrange(n, n) lanza ValueError con una longitud fija",
    strict=True,
)
def test_f19_una_estructura_dinamica_admite_min_igual_a_max():
    dom = Domain()
    dom.define_dynamic_structure("d", 3, 3)
    dom.set_structure_to_integer("d", 0, 10)
    assert len(Solution(dom).get("d")) == 3


# --------------------------------------------------------------------------
# Metaheuristicas
# --------------------------------------------------------------------------


def _esfera_2d():
    dom = Domain()
    dom.define_real("x", -5.0, 5.0)
    dom.define_real("y", -5.0, 5.0)
    return dom, lambda s: (s["x"] - 1.0) ** 2 + (s["y"] + 2.0) ** 2


@pytest.mark.xfail(
    reason="F-02: la comparacion de TPE.initialize esta invertida y devuelve la "
    "peor solucion",
    strict=True,
)
def test_f02_tpe_initialize_devuelve_la_mejor_solucion():
    from metagen.metaheuristics import TPE

    random.seed(1)
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


@pytest.mark.xfail(
    reason="F-13: TPE reasigna domain._connector y deja el dominio del usuario "
    "modificado",
    strict=True,
)
def test_f13_tpe_no_modifica_el_dominio_del_usuario():
    from metagen.metaheuristics import TPE

    dom = Domain()
    dom.define_real("x", -5.0, 5.0)
    conector_original = dom.get_connector()
    TPE(dom, lambda s: s["x"], max_iterations=1, warmup_iterations=0)
    assert dom.get_connector() is conector_original


@pytest.mark.xfail(
    reason="F-03: _initialize sobrescribe self.best_solution sin comparar con el "
    "resultado del warmup",
    strict=True,
)
def test_f03_el_warmup_no_se_descarta():
    from metagen.metaheuristics import RandomSearch

    random.seed(2)
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


@pytest.mark.xfail(
    reason="F-04: la rama else de GASolution.crossover usa variable_value (de "
    "self) para el hijo 2 en lugar de other.get(...)",
    strict=True,
)
def test_f04_el_segundo_hijo_hereda_del_segundo_padre():
    from metagen.metaheuristics import GAConnector
    from metagen.metaheuristics.ga.ga_tools import GASolution

    random.seed(3)
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


@pytest.mark.xfail(
    reason="F-20: SA hereda population_size=20 de la clase base aunque solo use "
    "solutions[0]",
    strict=True,
)
def test_f20_sa_no_evalua_una_poblacion_entera_al_inicializar():
    from metagen.metaheuristics import SA

    random.seed(6)
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


@pytest.mark.xfail(
    reason="F-24: mm_tools importa ray a nivel de modulo, asi que Memetic no "
    "existe en una instalacion sin el extra distributed",
    strict=True,
)
def test_f24_el_memetico_no_necesita_ray():
    if importlib.util.find_spec("ray") is not None:
        pytest.skip("Ray esta instalado: el fallo solo se observa sin Ray")
    import metagen.metaheuristics.mm.mm_tools  # noqa: F401
