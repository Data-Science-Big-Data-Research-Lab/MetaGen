# MetaGen

Framework de desarrollo de metaheurísticas y optimización de hiperparámetros.
Paquete publicado como `pymetagen-datalabupo`. Autores: DataLabUPO (Universidad
Pablo de Olavide). Licencia: ver P-01 en `AUDIT.md` — hoy es contradictoria.

## Contexto de trabajo actual

Estamos aplicando los arreglos de una auditoría de código. **Lee AUDIT.md antes
de tocar nada**: contiene 51 hallazgos con identificadores estables (`F-01`…`F-28`
críticos e importantes, `A-01`…`A-12` de diseño, `P-01`…`P-11` de proyecto), cada
uno con fichero:línea, diagnóstico y arreglo propuesto.

## Arquitectura

```
src/metagen/
  framework/
    domain/       Definiciones del espacio de búsqueda (Integer, Real, Categorical,
                  Static/DynamicStructure, BaseDefinition). core.py + preconditions.py
    solution/     Solution y los tipos que la componen (types/base.py es la clase
                  madre de Integer, Real, Categorical y Structure)
    connector/    BaseConnector: mapea definición de dominio ↔ tipo de solución ↔
                  builtin. Es el punto de extensión del framework
    facades.py    Domain, la API pública que usa el usuario final
  metaheuristics/
    base.py       Metaheuristic (ABC): run() = pre_execution → _warmup → _initialize
                  → bucle (pre_iteration → _iterate → post_iteration) → post_execution
    rs/ ga/ sa/ hc/ tpe/ mm/ cvoa/   Una carpeta por algoritmo. `hc/` era `ts/`:
                  lo que había implementado no era una búsqueda tabú sino hill
                  climbing, y se renombró en A-02 en vez de reescribirlo
    tools.py      random_exploration, local_search, local_search_with_tabu
  logging/        metagen_logger + TensorBoardLogger. Desde A-11 el paquete solo
                  instala un NullHandler al importarse: para ver algo por consola
                  hay que llamar a set_metagen_logger_level(). Desde A-12
                  TensorBoard es opcional: log_dir=None (el valor por defecto) no
                  escribe nada, y cualquier ruta lo enciende
```

Tres ideas que conviene tener presentes:

- **Todo minimiza.** Menor fitness es mejor, en todo el código. Cualquier comparación
  que vaya en el otro sentido es sospechosa (así se detectó F-02).
- **El conector es el mecanismo de extensión.** GA y TPE registran sus propias
  subclases (`GAConnector`, `TPEConnector`). Un cambio en `BaseConnector` o en la
  jerarquía de tipos repercute en los dos.
- **Nada en `src/` usa el RNG global.** Desde A-06, todo sorteo pasa por
  `framework/rng.py`, que guarda dos generadores propios del paquete: un
  `random.Random` y un `np.random.Generator` (TPE tira de NumPy, el resto de la
  biblioteca estándar). Un `random.x(...)` nuevo en `src/` es un bug: usa
  `get_rng()` o `get_numpy_rng()`. Para sembrar, `Metaheuristic(..., seed=N)` o
  `set_seed(N)` directamente; en los tests, **nunca `random.seed()`**, que ya no
  controla nada de la librería.

## Comandos

```bash
pip install -e .        # instalar en editable
pytest test             # LA suite que debe estar verde (~4 s)
mypy src                # configurado en setup.cfg
```

Desde P-05 la suite verde es **el árbol completo**, `pytest test`, y no un
subconjunto: `test/metaheuristics/test_behavior.py` tiene que ejecutarse.
Antes se usaba `pytest test/framework_test test/regression`, que lo dejaba fuera.

`test/metaheuristics/test_extras.py` es el único módulo que depende de `ray` y
`tensorflow` (extras opcionales) y se **salta limpiamente** cuando faltan, en vez
de abortar la recolección de toda la suite, que es lo que `P-04` protege.

Ojo con `pytest-csv-params`: `framework_test/solution_test.py` lo necesita y no lo
declara ni `install_requires` ni ningún extra (ver P-08). Sin él, ese módulo ni
siquiera se recolecta.

## Integración continua

Desde P-06, `.github/workflows/ci.yml` corre en cada push y PR sobre `master` y
`dev`, con dos jobs:

- **`tests`** — matriz 3.10 / 3.11 / 3.12, **bloqueante**. Instala `pip install -e .`
  más `pytest` y `pytest-csv-params`, y ejecuta la suite que debe estar verde.
- **`types`** — `mypy src`, **informativo** (`continue-on-error: true`) mientras
  P-11 siga abierto. De 14 al abrir la auditoría van 7 en el CI, tras cerrar F-01, F-05
  y A-11; el resto pertenece a la familia F-14/A-10 y a deuda propia de P-11. Cuando el
  contador llegue a cero, quitar el `continue-on-error` y la comprobación pasa a
  bloquear. **En local pueden salir 8**: `mypy 1.1.1` da un error en `connector.py:91`
  que la versión del CI no da.

El CI **no instala los extras a propósito**. Hasta cerrar `F-24` era el único sitio
donde ese hallazgo se observaba; hoy su test bloquea Ray en un subproceso y corre en
todas partes. El único que sigue necesitando Ray instalado es el de `F-21`, que se
salta en el CI: es el `1 skipped` que se ve allí, junto al de `unit_test.py`.

## Cómo se prueban las metaheurísticas

La carpeta `test/` se reorganizó el 9 de septiembre de 2026:

```
test/
  conftest.py            configuración compartida
  framework/             test_domain, test_solution, test_alteration, y desde la
                         reorganización test_connector y test_integration
  metaheuristics/        test_behavior (el banco) y test_extras (opcional: Ray y TensorFlow)
  regression/            test_audit_regressions, un test por hallazgo
examples/                catálogos de problemas (scikit-learn, TensorFlow, dummies) y
                         los scripts de CVOA: no son tests
benchmark/               el material del artículo contra Optuna, Hyperopt y Ray Tune
```

El antiguo `unit_test.py`, dirigido por CSV y que exigía Ray **y** TensorFlow, se
retiró: no corría ni en el CI y no comprobaba nada que el banco no compruebe mejor.

`test/metaheuristics/test_behavior.py` es el banco, desde P-05. **Sin dependencias
opcionales**, así que corre siempre, también en el CI. Comprueba que cada
algoritmo optimiza de verdad: historial monótono, el resultado es el mejor visto,
mejora sobre su inicio, y **gana a muestrear al azar con sus mismas evaluaciones**.

Las estadísticas van sobre 10 semillas fijas con umbral de 7, no sobre una
ejecución suelta: un algoritmo sano queda en 8-10 y uno roto en 0-4.

Desde `F-32` el banco son **seis funciones**, las clásicas del campo, cada una con
su dominio canónico: Sphere, Rastrigin, Rosenbrock, Ackley, Griewank y Schwefel.
Los dominios **no se normalizan a propósito** — es lo que destapó `F-32`, porque
`alteration_limit=1.0` significa algo muy distinto en `[-2.048, 2.048]` que en
`[-600, 600]`.

Las dos primeras propiedades son estructurales y se exigen a **las 42
combinaciones**, sin excepciones: hoy pasan todas. Las dos estadísticas llevan una
tabla de `xfail` por propiedad, medida y no supuesta, donde cada par que falla cita
lo que lo explica. Ojo: la tabla va **por propiedad**, porque hay pares que fallan
una y pasan la otra.

## Cómo funcionan los tests de regresión

`test/regression/test_audit_regressions.py` tiene un test por hallazgo
reproducible. Cada uno comprueba el comportamiento **correcto** y está marcado
`@pytest.mark.xfail(reason="F-xx: …", strict=True)`, así que hoy la suite está en
verde. En cuanto arreglas el hallazgo el test pasa a `XPASS(strict)`, que pytest
reporta como fallo: entonces **quitas el marcador** y la suite vuelve a verde con
un test de verdad protegiendo el arreglo.

No borres ni relajes un test para que pase. Si un test de regresión te parece
incorrecto, dilo antes de tocarlo.

## Convenciones

- Python ≥ 3.10. Anotaciones de tipo en toda firma nueva.
- Cabecera GPLv3 en cada fichero nuevo de `src/` (copia la de cualquier módulo).
- Docstrings en formato Sphinx (`:param x:` / `:type x:` / `:return:`). **Todo el
  código del paquete va en inglés americano**: identificadores, comentarios y
  docstrings, en `src/` y en `test/`. `AUDIT.md` y este documento son de proceso
  interno y siguen en español, igual que los nombres de
  `test/regression/test_audit_regressions.py`.
- No cambies la API pública de `Domain` ni de `Solution` sin decírmelo: hay
  notebooks y documentación publicada que dependen de ella.
- Un commit por hallazgo, citando el ID, **con el mensaje en inglés**:
  `fix(domain): F-16 format the definition error messages`
- Los ficheros bajo `src/metagen/metaheuristics/cvoa/` están duplicados entre la
  versión local y la distribuida (A-09): si arreglas algo ahí, comprueba si el
  mismo bug está en el gemelo.
- Desde F-24, `mm/` sigue el mismo patrón que el resto del paquete: `mm_tools.py`
  no toca Ray y `mm_distributed_tools.py` sí. El despachador importa el segundo
  **dentro de la función**, no arriba. Un `import ray` nuevo en `mm_tools.py`
  devolvería el bug.
