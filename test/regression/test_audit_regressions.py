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
