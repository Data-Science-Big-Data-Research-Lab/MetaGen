# MetaGen

Framework de desarrollo de metaheurísticas y optimización de hiperparámetros.
Paquete publicado como `pymetagen-datalabupo`. Autores: DataLabUPO (Universidad
Pablo de Olavide). Licencia: ver P-01 en `AUDIT.md` — hoy es contradictoria.

## Contexto de trabajo actual

Estamos aplicando los arreglos de una auditoría de código. **Lee AUDIT.md antes
de tocar nada**: contiene 64 hallazgos con identificadores estables (`F-01`…`F-41`
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
- **`initialize` e `iterate` no guardan estado en `self`.** En distribuido Ray los
  ejecuta sobre una copia serializada del algoritmo, y lo que escriban en `self` se
  queda en el worker (`F-40`): el estado que deba persistir va en lo que devuelven o
  se reconstruye en `post_iteration`, que corre en el driver. Así lo hacen TPE, cuyo
  historial es su propia población, y `HillClimbing` con su lista tabú.
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

La suite no necesita nada que el paquete no declare: el extra `test` lleva
`pytest` y `scikit-learn` (para el problema de hiperparámetros del banco). Los
tests dirigidos por CSV, y con ellos `pytest-csv-params`, se reescribieron en
línea el 9 de septiembre de 2026.

## Integración continua

Desde P-06, `.github/workflows/ci.yml` corre en cada push y PR sobre `master` y
`dev`, con dos jobs:

- **`tests`** — matriz 3.10 / 3.11 / 3.12, **bloqueante**. Instala
  `pip install -e .[test]` y ejecuta la suite que debe estar verde.
- **`types`** — `mypy src`, **informativo** (`continue-on-error: true`) mientras
  P-11 siga abierto. El contador va por **40 en local**, desde los 167 con que empezó a
  medirse bien, y **los 40 están en los cuatro ficheros de CVOA**, que tienen sesión
  propia: todo lo demás está a cero. Cuando llegue a cero, quitar el
  `continue-on-error` y la comprobación pasa a bloquear.

  Dos ayudantes que existen para que el tipado sea honesto, y que conviene usar en
  código nuevo: `Metaheuristic._best_so_far()` en vez de leer `self.best_solution`
  desde `iterate()` (es `Optional` solo antes de inicializar), y
  `tools.solution_class(domain)` en vez de `get_connector().get_type(get_core())`.

  **El CI da unos pocos menos que el local**, porque
  ejecuta una versión de mypy más nueva que la 1.1.1 de esta máquina; no es una
  discrepancia del código y no hay que perseguirla.

  Dos trampas al tipar, las dos vividas: `A | 'B'` en la firma de un método **revienta
  al importar** (la firma se evalúa al definirla), así que una referencia adelantada va
  en `Union[...]`; y `cast` evalúa su primer argumento, así que un tipo importado solo
  bajo `TYPE_CHECKING` hay que citarlo entre comillas.

El CI **no instala los extras a propósito**. Hasta cerrar `F-24` era el único sitio
donde ese hallazgo se observaba; hoy su test bloquea Ray en un subproceso y corre en
todas partes. El único que sigue necesitando Ray instalado es el de `F-21`, que se
salta en el CI, igual que los de `F-11` y `F-40` y que todo `test_extras.py`: son
los `skipped` que se ven allí. En una máquina con Ray solo se salta el problema de
TensorFlow de `test_extras.py`.

## Cómo se prueban las metaheurísticas

La carpeta `test/` se reorganizó el 9 de septiembre de 2026:

```
test/
  conftest.py            configuración compartida
  framework/             test_domain y test_solution, con los valores que antes vivían
                         en CSV escritos en línea; test_connector, los tres conectores
                         en las dos direcciones; test_integration, el framework de punta
                         a punta sobre el dominio «con una de cada cosa», que es
                         `build_full_domain` en conftest y anida estructuras a propósito
  metaheuristics/        test_behavior (el banco) y test_extras: los siete algoritmos
                         con distributed=True sobre Ray, y el problema de TensorFlow
                         de examples/, cada uno saltándose donde falte su extra
  regression/            test_audit_regressions, un test por hallazgo
examples/                catálogos de problemas (scikit-learn, TensorFlow, dummies) y
                         los scripts de CVOA: no son tests
benchmark/               el material del artículo contra Optuna, Hyperopt y Ray Tune
```

El antiguo `unit_test.py`, dirigido por CSV y que exigía Ray **y** TensorFlow, se
retiró: no corría ni en el CI y no comprobaba nada que el banco no compruebe mejor.

Los tests de integración destaparon cuatro hallazgos el día que se escribieron, `F-36`
a `F-39`, y uno de ellos —`F-39`, el cruce que comparte grupos entre padres e hijos—
lo había introducido `F-31` esa misma semana sin que el banco lo viera: **el banco
compara fitness almacenados entre sí, nunca contra una reevaluación**. Por eso
`test_integration.py` reevalúa el resultado de cada algoritmo. Hasta que `F-37` se
cierre, el ayudante `_builtin` de ese módulo desenvuelve a mano lo que `solucion[nombre]`
devuelve como objetos.

`test/metaheuristics/test_behavior.py` es el banco, desde P-05. **Sin dependencias
opcionales**, así que corre siempre, también en el CI. Comprueba que cada
algoritmo optimiza de verdad: historial monótono, el resultado es el mejor visto,
mejora sobre su inicio, y **gana a muestrear al azar con sus mismas evaluaciones**.

Las estadísticas van sobre 10 semillas fijas con umbral de 7, no sobre una
ejecución suelta: un algoritmo sano queda en 8-10 y uno roto en 0-4.

El banco son **las nueve funciones de la Sección 5.1 del artículo** con su dominio
canónico —Sphere, Rastrigin, Rosenbrock, Ackley, Griewank, Schwefel, Levy,
Michalewicz y Zakharov—, **un décimo problema que afina un árbol de decisión de
scikit-learn** sobre un dominio heterogéneo (dos enteros, una categórica y un real),
y **un undécimo, el ajuste polinómico de grado variable**, el único con una
estructura dinámica (`F-31`). Un par que reviente se registra en la fixture
(`_CRASHES`) y falla sus cuatro propiedades bajo `xfail`, sin tirar el módulo; hoy
la tabla está vacía, desde que `F-35` cerró. Ese décimo es el único que mide el caso de uso que vende el paquete, y por
él `scikit-learn` está en el extra `test`. Su objetivo es la **log-loss**, no la
exactitud: la exactitud solo toma 17 valores distintos, así que los empates
—que cuentan como victoria bajo `<=`— descalibraban la comparación.

**La fila de `RandomSearch` es la calibración**: compite contra sí misma, así que
debe salir cerca de 5 de 10. Si se aleja, la comparación está rota, no el
algoritmo.

**Al problema del árbol solo se le exigen las dos propiedades estructurales.** Las
dos estadísticas comparan un recuento con un umbral fijo, y entrenar un modelo no
es aritmética: el CI corre en Linux con numpy 2 y la última scikit-learn, así que
el árbol ajusta cortes distintos y el paisaje no es el mismo. Un umbral medido en
una máquina es una predicción que solo vale allí — costó un CI en rojo. Lo marca
la bandera `reproducible` de `_Problem`. **Cualquier problema nuevo cuyo fitness
no sea aritmética pura debe declararse `reproducible=False`.**

Cada problema trae **su propio dominio y su propia función de fitness** (`_Problem`
en `behavior_test.py`), así que añadir uno nuevo no exige que tenga una `x` y una
`y`. La suite completa tarda ~66 s, la mitad el problema del árbol. Los dominios **no se normalizan a propósito** — es lo
que destapó `F-32`, porque un `alteration_limit` absoluto significa algo muy
distinto en `[-2.048, 2.048]` que en `[-600, 600]`. Desde que `F-32` está cerrado, el
defecto de `HillClimbing`, `Memetic` y `SA` es `RelativeAlteration(0.2)`: **una
fracción del rango de cada variable, resuelta por la variable misma** en `Real.mutate`
e `Integer.mutate`. Un número sigue siendo un límite absoluto y `None` sigue siendo el
dominio entero.

**Michalewicz tiene el mínimo negativo** (≈ −1.8013 en 2D). Ninguna propiedad
supone que el óptimo esté en 0 —todas son relativas—, y lo que se añada después
tampoco debe suponerlo.

Las dos primeras propiedades son estructurales y se exigen a **las 63
combinaciones**, sin excepciones: hoy pasan todas. Las dos estadísticas llevan una
tabla de `xfail` por propiedad, medida y no supuesta, donde cada par que falla cita
lo que lo explica. Ojo: la tabla va **por propiedad**, porque hay pares que fallan
una y pasan la otra.

Con los diez problemas, **el mejor del paquete es el memético** (91/100 contra el
azar), seguido de `HillClimbing` (89), SA (77), TPE (70), GA (62), `RandomSearch`
(56, que es la línea base) y SSGA (54). **Los siete alcanzan o superan al muestreo
aleatorio**; no era así antes de cerrar `A-01`, `F-30`, `F-32` y `F-33`. En el
problema del árbol el orden cambia: `HillClimbing` 8/10 y **TPE 3/10**, por debajo
del azar, pese a ser el algoritmo pensado para hiperparámetros.

En una estructura dinámica el cruce es **corte y empalme** desde `F-31`, elegido
por medición sobre prefijo-común-con-colas (que queda de reserva): recombina las
longitudes, no solo los valores, y los hijos nacen con longitud válida y en la
rejilla del paso por construcción — hace falta, porque `Structure.set` no valida la
longitud. El cruce de los genéticos es **BLX-α con α = 0.5** desde `F-33`, no el
intercambio uniforme: `GAReal` y `GAInteger` lo traen y se registran en `GAConnector`, y
`GASolution.crossover` pregunta por la capacidad (`hasattr(valor, "crossover")`) en vez
de por el builtin. Las categóricas se siguen intercambiando enteras, que es lo correcto.

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
  mismo bug está en el gemelo. Sus poblaciones son `SolutionSet`, un conjunto con
  orden de inserción (`common_tools.py`): un `set()` nuevo de soluciones en CVOA
  devuelve `F-29`, la pandemia que cambia con `PYTHONHASHSEED`.
- Desde F-24, `mm/` sigue el mismo patrón que el resto del paquete: `mm_tools.py`
  no toca Ray y `mm_distributed_tools.py` sí. El despachador importa el segundo
  **dentro de la función**, no arriba. Un `import ray` nuevo en `mm_tools.py`
  devolvería el bug.
