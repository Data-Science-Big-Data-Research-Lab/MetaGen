# MetaGen

Framework de desarrollo de metaheurísticas y optimización de hiperparámetros.
Paquete publicado como `pymetagen-datalabupo`. Autores: DataLabUPO (Universidad
Pablo de Olavide). Licencia: ver P-01 en `AUDIT.md` — hoy es contradictoria.

## Contexto de trabajo actual

Estamos aplicando los arreglos de una auditoría de código. **Lee AUDIT.md antes
de tocar nada**: contiene 47 hallazgos con identificadores estables (`F-01`…`F-24`
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

Dos ideas que conviene tener presentes:

- **Todo minimiza.** Menor fitness es mejor, en todo el código. Cualquier comparación
  que vaya en el otro sentido es sospechosa (así se detectó F-02).
- **El conector es el mecanismo de extensión.** GA y TPE registran sus propias
  subclases (`GAConnector`, `TPEConnector`). Un cambio en `BaseConnector` o en la
  jerarquía de tipos repercute en los dos.

## Comandos

```bash
pip install -e .                                # instalar en editable
pytest test/framework_test test/regression      # LA suite que debe estar verde
pytest test                                     # recolecta; salta unit_test.py sin ray/tensorflow
mypy src                                        # configurado en setup.cfg
```

Usa `pytest test/framework_test test/regression` para la suite que debe estar
verde. Desde P-04, `pytest test` ya recolecta: `test/metaheuristics_test/unit_test.py`
depende de `ray` y `tensorflow` (extras opcionales, este último importado de forma
transitiva vía el dispatcher) y se **salta limpiamente** cuando faltan, en vez de
abortar la recolección de toda la suite.

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
`F-24` es observable. Allí la suite da `102 passed, 21 xfailed`; en una máquina con
Ray instalado son 20 xfailed y 1 skipped.

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
- Docstrings en formato Sphinx (`:param x:` / `:type x:` / `:return:`), en inglés,
  como el resto del código. Los comentarios de `AUDIT.md` están en español pero el
  código y la documentación del repo van en inglés.
- No cambies la API pública de `Domain` ni de `Solution` sin decírmelo: hay
  notebooks y documentación publicada que dependen de ella.
- Un commit por hallazgo, citando el ID:
  `fix(domain): F-16 los mensajes de definición nunca se formateaban`
- Los ficheros bajo `src/metagen/metaheuristics/cvoa/` están duplicados entre la
  versión local y la distribuida (A-09): si arreglas algo ahí, comprueba si el
  mismo bug está en el gemelo.
