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
import pathlib
import random
import subprocess
import sys

import pytest

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed


# --------------------------------------------------------------------------
# Dominio: tipos y definiciones
# --------------------------------------------------------------------------


@pytest.mark.xfail(
    reason="F-01: el suelo `if result < step` de _closest_number hace inalcanzable "
    "todo valor por debajo de step",
    strict=True,
)
def test_f01_un_real_con_step_cubre_todo_su_dominio():
    set_seed(0)
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
    set_seed(semilla)
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
    set_seed(5)
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


@pytest.mark.xfail(
    reason="F-04: la rama else de GASolution.crossover usa variable_value (de "
    "self) para el hijo 2 en lugar de other.get(...)",
    strict=True,
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


@pytest.mark.xfail(
    reason="F-20: SA hereda population_size=20 de la clase base aunque solo use "
    "solutions[0]",
    strict=True,
)
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


@pytest.mark.xfail(
    reason="F-24: mm_tools importa ray a nivel de modulo, asi que Memetic no "
    "existe en una instalacion sin el extra distributed",
    strict=True,
)
def test_f24_el_memetico_no_necesita_ray():
    if importlib.util.find_spec("ray") is not None:
        pytest.skip("Ray esta instalado: el fallo solo se observa sin Ray")
    import metagen.metaheuristics.mm.mm_tools  # noqa: F401


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


def test_p06_el_workflow_de_ci_ejecuta_la_suite_que_debe_estar_verde():
    """P-06: no habia `.github/workflows`, asi que nada comprobaba la suite al
    subir cambios.

    Se comprueba el contenido del workflow, no solo su existencia. Tres cosas
    tienen que seguir siendo ciertas o el CI deja de servir para lo que se monto:

    - ejecuta la suite que debe estar verde;
    - instala `pytest-csv-params`, que no declara ni `install_requires` ni
      ningun extra (P-08) y sin el cual `solution_test.py` ni se recolecta;
    - **no** instala los extras opcionales, porque un entorno sin Ray es el
      unico donde F-24 es observable.

    No se comprueba el `continue-on-error` del job de mypy a proposito: esa
    linea desaparece al cerrar P-11.
    """
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    workflow = repo_root / ".github" / "workflows" / "ci.yml"
    assert workflow.is_file(), f"no existe el workflow de CI en {workflow}"

    texto = workflow.read_text(encoding="utf-8")

    assert "pytest test/framework_test test/regression" in texto, (
        "el workflow no ejecuta la suite que debe estar verde"
    )

    instalaciones = [
        linea.strip()
        for linea in texto.splitlines()
        if "pip install" in linea
    ]
    assert any("pytest-csv-params" in linea for linea in instalaciones), (
        "el CI no instala pytest-csv-params: framework_test/solution_test.py no "
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
