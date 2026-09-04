# Auditoría de MetaGen

Revisión completa de `src/metagen` sobre el commit `74f104e` (2025-03-21).
47 hallazgos con identificadores estables: los 46 de la revisión inicial más
`P-11`, añadido al montar el CI. Los marcados **(R)** se reprodujeron ejecutando el
paquete instalado en Python 3.11 sin Ray ni TensorFlow.

## Cómo se usa este documento

Cada hallazgo tiene un ID (`F-01`, `A-03`, `P-07`…) que no cambia nunca. Los
hallazgos con test viven en `test/regression/test_audit_regressions.py`, marcados
`xfail(strict=True)`: comprueban el comportamiento **correcto**, hoy fallan, y
cuentan como esperados, así que la suite arranca en verde.

Ciclo de trabajo para cada arreglo:

```
1. Arreglar el hallazgo en src/
2. pytest test/framework_test test/regression   → el test da XPASS(strict) = fallo
3. Quitar el marcador @pytest.mark.xfail de ese test
4. pytest test/framework_test test/regression   → verde
5. Commit citando el ID:  fix(domain): F-16 mensajes de definición mal formados
```

Marcar aquí el hallazgo como `[x]` al cerrarlo.

## Resumen

| Bloque | Cantidad | Qué son |
|---|---|---|
| `F-01`…`F-13` | 13 | Críticos: corrompen resultados o bloquean la ejecución |
| `F-14`…`F-24` | 11 | Importantes: fallan en casos concretos o desperdician cómputo |
| `A-01`…`A-12` | 12 | Algoritmia y diseño: decisiones discutibles, no bugs |
| `P-01`…`P-11` | 11 | Empaquetado, tests y documentación |

Orden sugerido de ataque:

1. Red de seguridad: `A-06` (semilla), `P-04`, `P-05`, `P-06` (CI).
2. Los cinco que cambian resultados en silencio: `F-01`, `F-02`, `F-03`, `F-04`, `F-14`.
3. Dejar `Structure` utilizable: `F-05`, `F-06`, `F-19`, `F-18`.
4. Higiene de librería: `F-07`, `F-12`, `F-13`, `F-21`, `F-24`, `A-11`, `A-12`.
5. Revisión de CVOA: `F-08`, `F-09`, `F-10`, `F-23`, `A-09`, `P-10`.
6. Conversación de fondo: `A-01`, `A-02`, `A-03`.

---

## Críticos

### [ ] F-01 (R) · `_closest_number` deja inalcanzable medio dominio cuando hay `step`
`src/metagen/framework/solution/types/base.py:121` · test: `test_f01_un_real_con_step_cubre_todo_su_dominio`

```python
if result < step:
    result = step   # cualquier valor por debajo de step se convierte en step
```

Un real en `[-5, 5]` con `step=1` solo produce `1, 2, 3, 4, 5` en 50 inicializaciones.
Además el redondeo va a múltiplos absolutos de `step`, no a la rejilla que arranca en
`min_value`, así que `[0.05, 0.55]` con `step=0.1` nunca visita `0.05`. Afecta a
`Real.initialize`, `Real.mutate` y `Structure._resize`.

**Arreglo** Eliminar el suelo y anclar la rejilla al mínimo:
`min_value + round((v - min_value) / step) * step`, recortando a `[min_value, max_value]`.
`Real.initialize` tampoco recorta hoy y puede generar un valor que su propio `check()` rechaza.

### [ ] F-02 (R) · TPE toma la peor solución como mejor inicial
`src/metagen/metaheuristics/tpe/tpe.py:111` · test: `test_f02_tpe_initialize_devuelve_la_mejor_solucion`

```python
if best_solution is None or best_solution.get_fitness() < solution.get_fitness():
    best_solution = solution   # comparación invertida; el framework minimiza
```

Con fitness `[0.18, 2.06, 0.35, 11.60, 4.61, 5.52, 7.66, 0.03]`, `initialize` devuelve `11.60`.
Ese valor entra en `self.best_solution` y contamina el `min(...)` de cada iteración.

**Arreglo** Invertir el operador, o reutilizar `random_exploration` como el resto de metaheurísticas.

### [ ] F-03 (R) · La fase de warmup se calcula y se tira
`src/metagen/metaheuristics/base.py:290-292` · test: `test_f03_el_warmup_no_se_descarta`

`run()` llama a `_warmup()` y justo después a `_initialize()`, que sobrescribe
`current_solutions` y `best_solution` sin comparar. SA lleva `warmup_iterations=5`
por defecto y TPE `10`: son ~100 evaluaciones de fitness tiradas antes de empezar.
En distribuido hay un efecto añadido: como el warmup deja `current_solutions` con
longitud igual al número de warmups, `_launch_distributed_method` reparte carga
para ese tamaño y no para `population_size` (`base.py:99-100`).

**Arreglo** En `_initialize`, fusionar en vez de sustituir.

### [ ] F-04 (R) · El cruce del GA devuelve un hijo que es copia exacta del padre 1
`src/metagen/metaheuristics/ga/ga_tools.py:130` · test: `test_f04_el_segundo_hijo_hereda_del_segundo_padre`

```python
else:  # variable que NO se intercambia
    child1.set(variable_name, copy(self.get(variable_name)))
    child2.set(variable_name, copy(variable_value))   # variable_value es de self
```

Padre1 `{a:75, b:5, c:31}`, padre2 `{a:19, b:4, c:0}` → hijo2 `{a:75, b:5, c:31}`.
De paso, `random.randint(1, len(basic_variables) - 1)` (línea 107) impide que se
intercambien todas las variables.

**Arreglo** `child2.set(variable_name, copy(other.get(variable_name)))`.

### [ ] F-05 (R) · `Structure` descarta el valor que se le asigna
`src/metagen/framework/solution/types/structure.py:197-208` · tests: `test_f05_*`

`_convert` construye el tipo a partir de la definición —lo que lo inicializa al azar—
y nunca copia el valor de entrada: `st[0] = 42` guarda un entero aleatorio, `append(7)`
también. La rama `elif BaseType:` (línea 202) es siempre cierta porque es una clase,
no una instancia, así que el `else` con el `ValueError` es código muerto; el mismo
patrón está en `base_solution.py:149`.

**Arreglo** Crear la instancia y llamar a `.set(value)`; cambiar `elif BaseType:` por
`elif isinstance(value, BaseType):`.

### [ ] F-06 (R) · `Structure.set` y `Structure.insert` lanzan excepción con datos válidos
`structure.py:286` y `structure.py:268` · tests: `test_f06_*`

```
st.set([1, 2, 3])   → TypeError: object of type 'int' has no len()
st.insert(0, 5)     → AttributeError: 'Integer' object has no attribute 'insert'
```

`set` pide el tipo con `get_type(self.get_definition())`, que devuelve `Structure`.
`insert` llama a `insert` sobre el elemento, no sobre la lista.

**Arreglo** `get_type(self.get_definition().get_base())` y `current_values.insert(index, ...)`.

### [ ] F-07 · `import metagen` secuestra el `excepthook` del proceso
`src/metagen/__init__.py:19-30`

Una librería no debe tocar estado global del intérprete. Quien importe MetaGen dentro
de una aplicación mayor se lleva un cambio silencioso en cómo se reportan todas las
excepciones no capturadas.

**Arreglo** Borrar el hook, o exponerlo como función explícita.

### [ ] F-08 · Interbloqueo en CVOA con `update_isolated=True`
`src/metagen/metaheuristics/cvoa/local_tools.py:55-59`

`isolate_individual_conditional_state` adquiere `self.lock` y dentro llama a
`get_individual_state`, que vuelve a adquirirlo. `threading.Lock` no es reentrante:
la hebra se bloquea contra sí misma.

**Arreglo** `threading.RLock()`, o un `_get_individual_state_unlocked` privado.

### [ ] F-09 · `insert_into_set_strain` puede reventar con `KeyError`
`src/metagen/metaheuristics/cvoa/common_tools.py:126-133`

La rama `'d'` hace `bag.remove(best_dead)` sin comprobar pertenencia; la rama simétrica
de superspreaders (línea 116) sí comprueba. `best_dead` arranca siendo una solución
aleatoria sin evaluar que nunca estuvo en el conjunto.

**Arreglo** Misma guarda de pertenencia y `bag.discard()`.

### [ ] F-10 · El «peor superspreader» de CVOA se inicializa al revés
`src/metagen/metaheuristics/cvoa/cvoa_local.py:138-139`

El comentario dice «inicialmente la mejor solución» pero el constructor por defecto crea
la peor. `if to_insert > worst_superspreader` nunca se cumple, así que el mecanismo de
reemplazo del peor superspreader —la diversificación que el código documenta— nunca se
ejecuta.

**Arreglo** `best=True` en el constructor, junto con F-14.

### [ ] F-11 · La búsqueda local distribuida manda la misma porción a todos los workers
`src/metagen/metaheuristics/mm/mm_tools.py:65-68`

`population[:count]` sin avanzar el cursor. Compárese con `base.py:114-115`, donde sí avanza.

**Arreglo** `population = population[count:]` dentro del bucle.

### [ ] F-12 (R) · Todos los `Domain` comparten el mismo conector por defecto
`src/metagen/framework/facades.py:59` · test: `test_f12_cada_domain_tiene_su_propio_conector`

```python
def __init__(self, connector: BaseConnector = BaseConnector()):
```

Argumento por defecto mutable: se evalúa una vez, al importar.
`Domain().get_connector() is Domain().get_connector()` → `True`.

**Arreglo** `connector: BaseConnector | None = None` y `connector or BaseConnector()`.

### [ ] F-13 (R) · TPE modifica el `Domain` que le pasa el usuario
`src/metagen/metaheuristics/tpe/tpe.py:89` · test: `test_f13_tpe_no_modifica_el_dominio_del_usuario`

`self.domain._connector = TPEConnector()` deja el dominio del usuario modificado para
siempre. Comparar varias metaheurísticas en un bucle da resultados dependientes del orden.

**Arreglo** Trabajar sobre una copia, o exigir `Domain(connector=TPEConnector())` y validarlo.

---

## Importantes

### [ ] F-14 (R) · `sys.float_info.min` no es «menos infinito»
`src/metagen/framework/solution/base_solution.py:98` · test: `test_f14_el_centinela_de_mejor_fitness_es_menor_que_cualquier_objetivo`

Es `+2.2250738585072014e-308`. Cualquier objetivo que pueda ser negativo ya es «peor»
que el centinela «mejor posible». Las docstrings de `base_solution.py:65` y
`devsolution.py:40` afirman que vale `0.0`, que tampoco es cierto. Causa de fondo de F-10.

**Arreglo** `-math.inf` / `math.inf`, y corregir las dos docstrings.

### [ ] F-15 (R) · `Solution.__hash__` no mira las variables
`base_solution.py:444` · tests: `test_f15_*`

`hash((self.get_variables().__hash__, self.fitness))`: `dict.__hash__` es `None`, así que
el hash depende solo del fitness. Dos soluciones iguales con distinto fitness rompen el
invariante `a == b ⇒ hash(a) == hash(b)`. Duele en CVOA (cuatro `set` de soluciones) y
en la lista tabú (`tools.py:44`).

**Arreglo** Hashear una representación canónica de las variables y no incluir el fitness.

### [ ] F-16 (R) · Los mensajes de error de `Domain` salen mal formados
`domain/preconditions.py:107` · test: `test_f16_el_mensaje_de_variable_ya_definida_es_legible`

`elif mode == ("d_a", "d_g")` compara un str con una tupla. Redefinir una variable produce
`[STRUCTURE definition error] The variable i is length.`

**Arreglo** `elif mode in ("d_a", "d_n", "d_g", "d_s"):` con las cuatro asignaciones anidadas.

### [ ] F-17 (R) · Categorías duplicadas aceptadas, categoría única rechazada
`domain/preconditions.py:32-39` · tests: `test_f17_*`

`pairwise` solo compara adyacentes: `["a", "b", "a"]` se acepta. Y `len(value) >= 2`
impide fijar un hiperparámetro a un único valor.

**Arreglo** `len(set(value)) == len(value)` y un solo tipo; permitir longitud 1
(protegiendo `Categorical.mutate`, que haría `random.choice([])`).

### [ ] F-18 (R) · Una estructura estática se identifica como `DYNAMIC`
`domain/core.py:695` · test: `test_f18_una_estructura_estatica_se_identifica_como_static`

`Base.__init__(self, D)` mientras `get_attributes()` devuelve `S`.

**Arreglo** `Base.__init__(self, S)`.

### [ ] F-19 (R) · Estructuras dinámicas: nunca alcanzan el máximo y revientan si min = max
`types/structure.py:87` · tests: `test_f19_*`

`randrange(min_size, max_size, step or 1)` excluye el máximo, incoherente con
`check_length` y con `_resize`. `min == max` lanza `ValueError`. `_alterate` hace
`random.randint(1, current_size)` y peta con una estructura vacía. Ni
`DynamicStructureDefinition` ni `StaticStructureDefinition` validan sus longitudes.

**Arreglo** `randrange(min_size, max_size + 1, step)`, guardar `min == max`, proteger
`_alterate` y añadir precondiciones de longitud.

### [ ] F-20 (R) · SA evalúa veinte soluciones iniciales para usar una
`sa/sa.py:117` · test: `test_f20_sa_no_evalua_una_poblacion_entera_al_inicializar`

No pasa `population_size` al `super().__init__`, así que hereda 20 aunque `iterate` solo
use `solutions[0]` (y no el mejor de los veinte, sino el primero). `self.T_min = 1e-8`
(línea 124) no se usa en ningún sitio.

**Arreglo** `population_size=1` y aplicar `T_min` como suelo del enfriamiento.

### [ ] F-21 · `run()` apaga Ray aunque no lo haya arrancado
`metaheuristics/base.py:307-308`

Si el usuario conectó a un clúster existente, o compara varias metaheurísticas en un
script, la primera que termina se lleva el runtime de las demás.

**Arreglo** Recordar en un flag si fue `run()` quien llamó a `ray.init()`.

### [ ] F-22 · TPE escribe valores fuera del dominio saltándose la validación
`tpe/tpe_tools.py:30, 51-56, 71-75`

`np.random.uniform(min_value, max_value + 1)` (el `+1` es de enteros);
`if np.isnan(value) or value is None` (si fuera `None`, `np.isnan(None)` ya habría
lanzado `TypeError`); y `self.value = value`, que salta `set()` y `check()`. Los tres se
refuerzan: un valor fuera de rango llega intacto a la función de fitness del usuario.
`TPECategorical` devuelve además escalares NumPy en vez de tipos nativos.

**Arreglo** `max_value` a secas, invertir el `if`, usar `self.set(value)` y `.item()`.

### [ ] F-23 · CVOA se detiene al encontrar una mejora y reporta el tiempo mil veces más corto
`cvoa_local.py:333` y `local_launcher.py:45`

`third_condition = self.best_strain_solution_found and self.time > 1`: la bandera nunca
se reinicia, así que la cepa muere en la iteración siguiente a la primera mejora.
`timedelta(milliseconds=t2 - t1)` con `time()` en segundos.

**Arreglo** Contador de iteraciones sin mejora, y `timedelta(seconds=...)`.

### [ ] F-24 (R) · El algoritmo memético exige Ray aunque no se distribuya
`mm/mm_tools.py:5-8` · test: `test_f24_el_memetico_no_necesita_ray`

La importación es de módulo, no de la rama distribuida. En una instalación estándar
`Memetic` no existe en `metagen.metaheuristics`, pese a que el README lo anuncia.

**Arreglo** Separar `mm_tools` (sin Ray) de `mm_distributed_tools` (con Ray).

---

## Algoritmia y diseño

Aquí el código hace lo que dice hacer; lo discutible es qué dice hacer.

- **[ ] A-01** `ga/ga.py:71-79`, `mm/memetic.py:111-119` — **sin selección de padres**: `best_parents` se calcula fuera del bucle y los `n/2` cruces usan siempre la misma pareja. No hay torneo, ruleta ni ranking. *Propuesta*: función de selección intercambiable, torneo binario por defecto.
- **[ ] A-02** `ts/tabu.py:123-124`, `tools.py:45` — **tabú es hill climbing**: se explora siempre desde `self.best_solution` y `local_search_with_tabu` nunca devuelve algo peor que el punto de partida, así que la lista tabú no puede desviar al algoritmo de nada. *Propuesta*: `current_solution` separada del mejor histórico, moverse al mejor vecino no tabú aunque empeore, criterio de aspiración.
- **[ ] A-03** `tools.py:49` — el vecindario tabú se genera **en cadena** (`deepcopy(best_neighbor)`), no alrededor de la solución. `mm_tools.py:135` hace lo contrario: las dos implementaciones hermanas discrepan.
- **[ ] A-04** `rs/random_search.py:110` — `solutions[:-1]` descarta siempre el último individuo, que no tiene por qué ser el peor; la docstring dice que se preserva el mejor.
- **[ ] A-05** `ga/ssga.py:84-86` — `solutions.index(worst)` sustituye por igualdad de valor, no por identidad: con duplicados las dos sustituciones caen en la misma posición.
- **[x] A-06** transversal — **sin control de semilla**. Todo usa el `random` global (y `np.random` en TPE); no hay parámetro `seed` ni `rng`. En distribuido cada worker de Ray arranca con su propio estado. *Propuesta*: `seed: int | None` en `Metaheuristic.__init__` que construya un `random.Random` y un `np.random.Generator` propios, propagados a `Solution` y a los tipos; en distribuido, `SeedSequence.spawn()`.

  *Cerrado con una variante de la propuesta.* Propagar el generador hasta `Solution` y los tipos exigía tocar sus constructores, que son el punto de extensión que el artículo documenta (caso *Extended Metaheuristic*), así que se descartó por romper la API pública. En su lugar, `metagen/framework/rng.py` guarda **dos generadores propios del paquete** —un `random.Random` y un `np.random.Generator`, porque TPE tira de NumPy y el resto de la biblioteca estándar— y las 38 llamadas al RNG global de `src/` pasan por ellos. `seed` es ahora un parámetro de `Metaheuristic.__init__` (heredado por las siete metaheurísticas) y de los dos lanzadores de CVOA; se aplica en `run()`, no en el constructor, para que cada `run()` arranque del mismo estado.

  Consecuencias que conviene tener presentes:

  - **Sembrar MetaGen ya no toca el `random` del proceso**, ni al revés. Es la ventaja sobre un `random.seed()` global, y hay un test que lo protege.
  - **Los siete helpers de la suite de regresión sembraban con `random.seed()`** y dejaron de ser deterministas al hacer este cambio: `test_f05_append_conserva_el_valor` llegó a pasar por azar (el entero aleatorio salió 7). Ahora siembran con `set_seed()`.
  - **NumPy cambia de algoritmo**: `default_rng()` (PCG64) en vez del Mersenne Twister de `np.random`. La secuencia de TPE ya no es la de la `0.2.0` publicada.
  - **Sigue sin resolverse la concurrencia**: las cepas de CVOA local corren en hilos que comparten los generadores, y los workers de Ray arrancan con su propio estado. Ambas firmas lo advierten en su docstring. Cerrarlo del todo exige un generador por instancia, que es la propuesta original de este hallazgo.

  Tests: `test_a06_la_misma_semilla_reproduce_la_ejecucion`, `test_a06_semillas_distintas_dan_ejecuciones_distintas`, `test_a06_metagen_no_toca_el_generador_global_del_usuario`.
- **[ ] A-07** `ga`, `ssga`, `mm` — no validan que el dominio use `GAConnector`: con un `Domain()` normal mueren en la primera iteración con `AttributeError: 'Solution' object has no attribute 'crossover'`.
- **[ ] A-08** `domain/core.py:219, 140` — `RealDefinition` exige `isinstance(value, float)` (rechaza `1` y `np.float32`) y `IntegerDefinition` acepta `bool`. *Propuesta*: `numbers.Real` excluyendo `bool`, normalizando al tipo nativo.
- **[ ] A-09** `cvoa_local.py` ↔ `cvoa_distributed.py` (372 vs 352 líneas) y `tools.py` ↔ `mm_tools.py` — **código duplicado y ya divergente**. *Propuesta*: una clase por algoritmo y la estrategia de ejecución (secuencial / Ray) como objeto inyectado.
- **[ ] A-10** `base.py:196, 247` — `_iterate` hace `self.best_solution = best_individual` sin comparar, así que el elitismo depende de que cada subclase se acuerde; y `stopping_criterion()` devuelve `False` por defecto (bucle infinito si una subclase lo olvida).
- **[ ] A-11** `logging/metagen_logger.py:29, 84, 90` — parchea `logging.Logger` globalmente, instala un `StreamHandler` al importar, y añade un handler nuevo en cada llamada a `get_remote_metagen_logger()`. `set_metagen_logger_level` haría `None.close()` si no hay handler de consola. *Propuesta*: solo `NullHandler` al importar y una función de configuración idempotente.
- **[ ] A-12** `base.py:83` — TensorBoard se activa por el mero hecho de estar instalado, sin forma de desactivarlo: un barrido de cientos de configuraciones escribe cientos de directorios en `logs/`. *Propuesta*: `log_dir: str | None = None` con `None` = desactivado.

---

## Empaquetado, tests y documentación

- **[ ] P-01** `setup.cfg:14` — clasificador `MIT License` frente a un `LICENSE` GPL-3.0 y 55 cabeceras GPLv3. PyPI anuncia MIT. *Arreglo*: unificar y añadir `license` / `license_files`.
- **[ ] P-02** README badge `>=3.12` vs texto `3.10+` vs `python_requires >=3.10`. El mínimo real es 3.10 (`itertools.pairwise`).
- **[ ] P-03** `setup.cfg:8-10`, badges y enlace de Colab apuntan a `DataLabUPO/MetaGen`; el repo vive en `Data-Science-Big-Data-Research-Lab/MetaGen`. El badge de release no resuelve.
- **[x] P-04 (R)** `pytest test` —el comando del README— **no llega a recolectar**: `test/metaheuristics_test/unit_test.py` importa `ray` y `tensorflow`, que son extras opcionales. Solo corren los 101 tests de `framework_test`. *Arreglo*: `pytest.importorskip("ray")` y `pytest.importorskip("tensorflow")` a nivel de módulo en `unit_test.py` (tensorflow se importa de forma transitiva vía el dispatcher, así que un `@pytest.mark.skipif` por test no basta: el fallo ocurre en tiempo de importación). Test: `test_p04_la_suite_completa_se_recolecta_sin_los_extras_opcionales`.
- **[ ] P-05** Los tests de metaheurísticas solo comprueban `assert solution is not None`. Los cuatro bugs críticos pasan la suite. *Arreglo*: con semilla fija (A-06), tres aserciones por algoritmo: fitness final ≤ mejor inicial; mejor que una búsqueda aleatoria del mismo presupuesto; `best_solution_fitnesses` monótona no creciente.
- **[x] P-06** No hay `.github/workflows`. Con `mypy` ya configurado en `setup.cfg` y una suite que corre en 3 s, un workflow mínimo con matriz 3.10–3.12 captura buena parte de lo anterior. *Cerrado*: `.github/workflows/ci.yml` con dos jobs, `tests` (matriz 3.10–3.12, bloqueante) y `types` (`mypy src`, informativo hasta que cierre `P-11`). Dos cosas salieron a la luz al montarlo: la suite necesita `pytest-csv-params`, que no declara ni `install_requires` ni ningún extra (ver `P-08`), y **el CI no instala los extras a propósito**, porque un entorno sin Ray es el único donde `F-24` es observable — en esta máquina su test se salta y por eso salen 20 xfailed en vez de 21.
- **[ ] P-07** `.gitignore:14` excluye `*.csv` y `*.xlsx`, y los parámetros de test son CSV en `test/test_parameters/`. Cualquier fichero nuevo se queda fuera del commit sin aviso. *Arreglo*: `!test/test_parameters/**/*.csv`.
- **[ ] P-08** Los extras de `setup.cfg` usan `;`, que en PEP 508 es el separador de **marcadores de entorno**, no de requisitos: `tensorboard = tensorboard; tensorboardX` se lee como «tensorboard, si el marcador tensorboardX». Comprobar qué instala `pip install pymetagen-datalabupo[all]`. Además hay tres `requirements*.txt` con criterios solapados. *Arreglo*: un requisito por línea y migrar la metadata a `pyproject.toml`.
- **[ ] P-09** Falta `src/metagen/py.typed`: el paquete está anotado de arriba abajo pero sin el marcador PEP 561 mypy trata `metagen` como `Any`.
- **[ ] P-10** Los ejemplos de las docstrings usan una API que no existe: `domain.defineInteger(0, 1)` en RS, TPE, Memetic y CVOA (el método es `define_integer(name, min, max)`), y el ejemplo de CVOA usa `CVOA.initialize_pandemic(...)` y `cvoa_launcher(strains)`, de una versión anterior. Son las páginas que publica readthedocs. *Arreglo*: actualizarlos y añadirlos como doctests.
- **[ ] P-11** `mypy src` **no pasa limpio**: 14 errores en 10 ficheros, pese a que el proyecto se desarrolló con la condición de usar tipos. Por eso el job `types` del CI nace informativo (`continue-on-error: true`). Diez de los catorce no son deuda nueva, sino los mismos bugs que ya recoge la auditoría vistos por otra ventana:

  | Causa | Errores | Se cierra con |
  |---|---|---|
  | `logging/metagen_logger.py:29, 69, 70` — parcheo de `Logger` y `Handler \| None` sin comprobar | 3 | `A-11` |
  | `solution/types/base.py:117, 119, 122` — `int \| float` asignado a un `int` en `_closest_number` | 3 | `F-01` |
  | `solution/types/structure.py:202` — `Function "BaseType" could always be true` | 1 | `F-05` |
  | `metaheuristics/base.py:256`, `cvoa_local.py:259`, `cvoa_distributed.py:238` — `.get_fitness()` sobre `Any \| None` | 3 | Familia `F-14` / `A-10` |
  | `base_solution.py:265`, `real.py:61`, `integer.py:62` — `Optional` implícito: `= None` en un parámetro no opcional | 3 | Propio de `P-11` |
  | `tpe/tpe.py:88` — falta anotar `solution_history` | 1 | Propio de `P-11` |

  *Arreglo*: cerrar los hallazgos de la tabla, resolver los cuatro restantes (`x: int \| None = None` y una anotación en TPE) y, cuando `mypy src` salga a cero, **quitar el `continue-on-error: true` del job `types`** para que la comprobación pase a bloquear. Conviene hacerlo junto con `P-09` (`py.typed`), que hoy hace que mypy trate `metagen` como `Any` desde fuera del paquete.
