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
import os
import pathlib
import random
import re
import subprocess
import sys

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

    assert "pytest test" in texto, (
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
