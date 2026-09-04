# MetaGen

Framework de desarrollo de metaheurísticas y optimización de hiperparámetros.
Paquete publicado como `pymetagen-datalabupo`. Autores: DataLabUPO (Universidad
Pablo de Olavide). Licencia: ver P-01 en `AUDIT.md` — hoy es contradictoria.

## Contexto de trabajo actual

Estamos aplicando los arreglos de una auditoría de código. **Lee AUDIT.md antes
de tocar nada**: contiene 48 hallazgos con identificadores estables (`F-01`…`F-25`
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
    rs/ ga/ sa/ ts/ tpe/ mm/ cvoa/    Una carpeta por algoritmo
    tools.py      random_exploration, local_search, local_search_with_tabu
  logging/        metagen_logger + TensorBoardLogger
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
subconjunto: `test/metaheuristics_test/behavior_test.py` tiene que ejecutarse.
Antes se usaba `pytest test/framework_test test/regression`, que lo dejaba fuera.

`test/metaheuristics_test/unit_test.py` depende de `ray` y `tensorflow` (extras
opcionales, este último importado de forma transitiva vía el dispatcher). Desde
P-04 se **salta limpiamente** cuando faltan, en vez de abortar la recolección de
toda la suite: es el `1 skipped` que verás en una instalación sin extras.

Ojo con `pytest-csv-params`: `framework_test/solution_test.py` lo necesita y no lo
declara ni `install_requires` ni ningún extra (ver P-08). Sin él, ese módulo ni
siquiera se recolecta.

## Integración continua

Desde P-06, `.github/workflows/ci.yml` corre en cada push y PR sobre `master` y
`dev`, con dos jobs:

- **`tests`** — matriz 3.10 / 3.11 / 3.12, **bloqueante**. Instala `pip install -e .`
  más `pytest` y `pytest-csv-params`, y ejecuta la suite que debe estar verde.
- **`types`** — `mypy src`, **informativo** (`continue-on-error: true`) mientras
  P-11 siga abierto. Hoy son 14 errores; diez pertenecen a hallazgos ya conocidos
  (F-01, F-05, A-11, familia F-14/A-10). Cuando el contador llegue a cero, quitar el
  `continue-on-error` y la comprobación pasa a bloquear.

El CI **no instala los extras a propósito**: un entorno sin Ray es el único donde
`F-24` es observable. Allí la suite da `123 passed, 1 skipped, 27 xfailed`; en una
máquina con Ray instalado, un xfail menos y un skip más.

## Cómo se prueban las metaheurísticas

Hay dos ficheros y conviene no confundirlos:

- `test/metaheuristics_test/unit_test.py` — el de siempre, dirigido por los CSV de
  `test/test_parameters/`. Exige Ray y TensorFlow, así que **casi nunca se ejecuta**.
- `test/metaheuristics_test/behavior_test.py` — desde P-05. **Sin dependencias
  opcionales**, así que corre siempre, también en el CI. Comprueba que cada
  algoritmo optimiza de verdad: historial monótono, el resultado es el mejor visto,
  mejora sobre su inicio, y **gana a muestrear al azar con sus mismas evaluaciones**.

Las estadísticas van sobre 10 semillas fijas con umbral de 7, no sobre una
ejecución suelta: un algoritmo sano queda en 8-10 y uno roto en 0-4. Hoy SA, GA y
SSGA suspenden las dos últimas propiedades y están marcados `xfail`, citando el
hallazgo culpable.

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
