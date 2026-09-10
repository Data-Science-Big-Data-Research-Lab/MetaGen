# Auditoría de MetaGen

Revisión completa de `src/metagen` sobre el commit `74f104e` (2025-03-21).
64 hallazgos con identificadores estables: los 46 de la revisión inicial más
`P-11` (al montar el CI), `F-25` (al medir el comportamiento real de las
metaheurísticas para `P-05`), `F-26` (al verificar `F-04`), `F-33` (al medir `A-01`), `F-34` (al
tipar el conector para `P-11`), `F-35` (al diseñar `F-31`), `F-36` a `F-39` (al escribir los
tests de integración del framework), `F-40` (al escribir los tests con Ray) y `F-41` (al cerrar
`F-38`). Los marcados **(R)** se reprodujeron
ejecutando el paquete instalado en Python 3.11 sin Ray ni TensorFlow.

**CVOA va aparte.** Sus cuestiones abiertas, sus discrepancias con el artículo original
y el orden en que atacarlas están en `metagen-auditoria/CVOA-cuestiones.md`, para una
sesión dedicada. Aquí siguen sus hallazgos con su ficha, pero el contexto vive allí.

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
| `F-14`…`F-41` | 28 | Importantes: fallan en casos concretos o desperdician cómputo |
| `A-01`…`A-12` | 12 | Algoritmia y diseño: decisiones discutibles, no bugs |
| `P-01`…`P-11` | 11 | Empaquetado, tests y documentación |

Orden sugerido de ataque:

1. Red de seguridad: `A-06` (semilla), `P-04`, `P-05`, `P-06` (CI).
2. Los cinco que cambian resultados en silencio: `F-01`, `F-02`, `F-03`, `F-04`, `F-14`.
3. Dejar `Structure` utilizable: `F-05`, `F-06`, `F-19`, `F-18`.
4. Higiene de librería: `F-07`, `F-12`, `F-13`, `F-21`, `F-24`, `A-11`, `A-12`.
5. Revisión de CVOA: `F-08`, `F-09`, `F-10`, `F-23`, `A-09`, `P-10`.
6. Conversación de fondo: `A-01`, `A-02`, `A-03`.

## Trabajo aplazado, con su sitio propio

Cosas que **no son hallazgos que arreglar de una sentada** y se han apartado a
propósito, cada una con su motivo. No están en el índice porque no son hallazgos.

| Qué | Por qué está aparte | Dónde |
|---|---|---|
| **Revisión de CVOA** | El diseño es de Paco Martínez-Álvarez y el código es multihilo con Ray encima. `F-27`, `F-28`, `F-29`, `A-09` y seis discrepancias más con el artículo | `metagen-auditoria/CVOA-cuestiones.md` |
| **`mypy src` a cero** | 40 errores tras tres tandas, todos en los cuatro ficheros de CVOA | `P-11` |
| **Implementar una búsqueda tabú de verdad** | Lo que había no lo era y se renombró a `HillClimbing` (`A-02`). La tabú canónica es un algoritmo nuevo, no un arreglo | ver abajo |
| **Implementar un TPE canónico** | El de MetaGen funciona y no se toca; el canónico es otro algoritmo, con dos piezas que van juntas | ver abajo |

### Implementar `TabuSearch`

`A-02` renombró a `HillClimbing` lo que se llamaba `TabuSearch`, porque no lo era: no
acepta empeoramientos, así que su lista tabú no puede desviarlo de nada. **El algoritmo
canónico sigue sin existir en el paquete.** Lo que haría falta:

- Una `current_solution` separada del mejor histórico.
- Moverse al **mejor vecino no tabú aunque empeore**, que es la esencia del método.
- Un criterio de aspiración: aceptar un movimiento tabú si mejora el mejor histórico.
- Vecindario **alrededor de la solución actual**, no en cadena — al revés que en
  `HillClimbing`, donde encadenar es correcto y está medido (`A-03`).

**Cuidado con el nombre.** Si la clase nueva se llama `TabuSearch`, el código anterior
al renombrado volverá a importar bien pero **ejecutará otro algoritmo**. Eso solo es
seguro si llega en una versión **posterior** a la del renombrado, dejando una ventana en
la que el `ImportError` avisa.

**Y hay que medirla contra `HillClimbing` en el banco completo antes de sacar
conclusiones**: `HillClimbing` suma **89/100** contra el muestreo aleatorio sobre los
diez problemas, segundo solo tras el memético (91/100), y es **el que mejor resuelve el
problema de hiperparámetros**, con 8 de 10.

### Implementar un TPE canónico

**El TPE de MetaGen no se toca**, decisión de David del 8 de septiembre de 2026, y los
números la respaldan: sobre las nueve funciones matemáticas es el cuarto de siete, con
**70/100** contra el muestreo aleatorio, muy por encima de este. No está roto.

Lo que sigue está **medido y no se convierte en hallazgo**, porque no hay un defecto que
corregir sino una diferencia de diseño con el algoritmo publicado.

**Dónde se queda corto.** En el problema de hiperparámetros del banco —el único con un
dominio heterogéneo, que es para lo que TPE existe— saca **3 de 10** contra el azar,
por debajo del 4 de la propia `RandomSearch`, mientras `HillClimbing` saca 8. Y en diez
semillas **nunca alcanza el óptimo** que sí encuentran `RandomSearch`, GA, SSGA,
`HillClimbing` y el memético.

La señal de ese paisaje está casi entera en una variable: el 5 % mejor tiene
`min_samples_leaf` en torno a 7.5 frente a 20.7 en todo el espacio. Medida por tercios
de ejecución, la media que **evalúa** cada algoritmo:

| | 1er tercio | 2º tercio | último tercio |
|---|---|---|---|
| `HillClimbing` (206 evals) | 19.1 | 7.5 | **7.0** |
| Memetic (610 evals) | 15.4 | 8.7 | **7.7** |
| **TPE (480 evals)** | 19.6 | 17.2 | **16.3** |
| *RandomSearch* | *20.5* | *19.1* | *19.0* |

**TPE apenas concentra**: su modelo casi no dirige la búsqueda.

**El mecanismo, medido instrumentando `sample_from_values`.** De cada valor que TPE
propone:

```
de la gaussiana de las MEJORES soluciones    25.7 %
de la de las PEORES                          65.6 %
uniforme (sigma cero)                         8.7 %
```

**Dos de cada tres propuestas se muestrean de la distribución de las peores.** Eso se
aparta del algoritmo de Bergstra, donde se muestrean candidatos de ℓ(x) y se elige el
que maximiza ℓ(x)/g(x); de g(x) no se muestrea nunca. Y la regla se realimenta al revés:
la mezcla usa la densidad del valor *actual* bajo cada modelo, y como el conjunto de las
mejores es estrecho y el de las peores ancho, **cuanto mejor definida está la región
buena, menos veces la visita**.

**Las dos correcciones evidentes empeoran, y por eso esto no es un hallazgo:**

| variante de muestreo | total sobre los diez problemas |
|---|---|
| como está | **70/100** |
| solo de ℓ(x) | 63/100 |
| canónico: 24 candidatos de ℓ(x), el que maximiza ℓ/g | **26/100** |

El canónico se hunde porque el modelo es **una única gaussiana por variable**, mientras
que el de Bergstra es una **mezcla de núcleos** —uno por observación más un prior
ancho—. Con una sola gaussiana, elegir con avidez colapsa la búsqueda en una región
minúscula de la que no sale. Dicho de otro modo: **ese 65.6 % desde las peores está
haciendo de exploración**, y sostiene a un modelo demasiado simple.

**Qué haría falta**, si algún día se implementa, y son **dos piezas que van juntas**:

- el **modelo**: mezcla de núcleos, uno por observación, con anchura derivada de la
  separación entre vecinos, más un prior ancho;
- la **selección**: candidatos de ℓ(x) y quedarse con el que maximiza ℓ/g.

Poner solo la segunda sobre el modelo actual es lo que da 26/100.

**Cuidado con el nombre, igual que con `TabuSearch`:** TPE es **uno de los dos
algoritmos que evalúa el artículo publicado**, así que sustituir el existente cambiaría
resultados publicados. Un canónico tendría que llegar como clase nueva, al lado.

*Completar el banco de pruebas salió de aquí el 8 de septiembre de 2026: ver `P-05`.*

---

## Índice

Qué es cada código, para no tener que buscarlo. ✅ cerrado, ⬜ abierto. **Al cerrar un
hallazgo hay que actualizar su fila aquí, además de su casilla más abajo.**

| | Código | Qué es |
|---|---|---|
| ✅ | `F-01` | Un real con `step` deja inalcanzable medio dominio |
| ✅ | `F-02` | TPE toma la peor solución como mejor inicial |
| ✅ | `F-03` | La fase de warmup se calcula y se tira |
| ✅ | `F-04` | El cruce del GA devolvía un hijo copia exacta del padre 1 |
| ✅ | `F-05` | `Structure` descarta el valor que se le asigna |
| ✅ | `F-06` | `Structure.set` e `insert` fallan con datos válidos |
| ✅ | `F-07` | Importar MetaGen secuestra el `excepthook` del proceso |
| ✅ | `F-08` | Interbloqueo en CVOA con `update_isolated=True` |
| ✅ | `F-09` | `insert_into_set_strain` puede reventar con `KeyError` |
| ✅ | `F-10` | El «peor superspreader» de CVOA se inicializa al revés |
| ✅ | `F-11` | La búsqueda local distribuida manda la misma porción a todos los workers |
| ✅ | `F-12` | Todos los `Domain` comparten el mismo conector por defecto |
| ✅ | `F-13` | TPE modifica el `Domain` que le pasa el usuario |
| ✅ | `F-14` | `sys.float_info.min` no es «menos infinito» |
| ✅ | `F-15` | `Solution.__hash__` no mira las variables |
| ✅ | `F-16` | Los mensajes de error de `Domain` salen mal formados |
| ✅ | `F-17` | Categorías duplicadas aceptadas, categoría única rechazada |
| ✅ | `F-18` | Una estructura estática se identifica como dinámica |
| ✅ | `F-19` | Estructuras dinámicas: nunca alcanzan el máximo, revientan si min = max |
| ✅ | `F-20` | SA evalúa veinte soluciones iniciales para usar una, y no la mejor |
| ✅ | `F-21` | `run()` apaga Ray aunque no lo haya arrancado él |
| ✅ | `F-22` | TPE escribe valores fuera del dominio saltándose la validación |
| ✅ | `F-23` | CVOA se detiene en la primera mejora y reporta mal el tiempo |
| ✅ | `F-24` | El memético exige Ray aunque no se distribuya |
| ✅ | `F-25` | SA se queda con el último vecino, no con el mejor |
| ✅ | `F-26` | La semilla no reproducía entre procesos: `mutate` recorría un conjunto |
| ✅ | `F-27` | `p_isolation` significa lo contrario de lo que dice su nombre |
| ✅ | `F-28` | Tres parámetros de CVOA no son los que sugiere el artículo |
| ✅ | `F-29` | CVOA no reproduce entre procesos: itera conjuntos de soluciones |
| ✅ | `F-30` | La temperatura de SA no llega a enfriarse: es un paseo aleatorio |
| ✅ | `F-31` | Los genéticos no admiten estructuras dinámicas: el cruce no existe |
| ✅ | `F-32` | El `alteration_limit` por defecto es absoluto, no relativo al dominio |
| ✅ | `F-33` | El cruce es uniforme: sobre variables reales no crea ningún valor nuevo |
| ✅ | `F-34` | `get_builtin` del conector falla con cualquier estructura |
| ✅ | `F-35` | TPE registra la estructura dinámica y revienta al usarla |
| ✅ | `F-36` | `get_definition` del conector falla con una instancia de estructura |
| ✅ | `F-37` | El valor de un grupo o de una estructura no es builtin más allá del primer nivel |
| ✅ | `F-38` | Una estructura acepta cualquier longitud: nadie comprueba el recuento |
| ✅ | `F-39` | El cruce de una estructura dinámica de grupos comparte los grupos con los padres |
| ✅ | `F-40` | En distribuido, el estado propio del algoritmo se actualiza en una copia y se pierde |
| ✅ | `F-41` | `check_length` de la estructura dinámica ignora el paso de longitud |
| ✅ | `A-01` | Sin selección de padres: todos los cruces usan la misma pareja |
| ✅ | `A-02` | La búsqueda tabú es en realidad hill climbing |
| ✅ | `A-03` | El vecindario tabú se genera en cadena, no alrededor de la solución |
| ✅ | `A-04` | Random Search descarta el último individuo, no el peor |
| ✅ | `A-05` | SSGA sustituye por igualdad de valor, no por identidad |
| ✅ | `A-06` | No había forma de fijar la semilla |
| ✅ | `A-07` | GA, SSGA y memético no validan que el dominio use `GAConnector` |
| ✅ | `A-08` | Los reales rechazan enteros y los enteros aceptan booleanos |
| ⬜ | `A-09` | CVOA y las herramientas están duplicados, y ya divergen |
| ✅ | `A-10` | El elitismo depende de que cada subclase se acuerde |
| ✅ | `A-11` | El logger parchea `logging` globalmente y acumula handlers |
| ✅ | `A-12` | TensorBoard se activa solo por estar instalado, sin poder apagarlo |
| ✅ | `P-01` | Licencia contradictoria: MIT en PyPI frente a GPLv3 en el código |
| ✅ | `P-02` | La versión mínima de Python se contradice en tres sitios |
| ✅ | `P-03` | Enlaces y badges apuntan al repositorio antiguo |
| ✅ | `P-04` | `pytest test` no llegaba a recolectar sin los extras opcionales |
| ✅ | `P-05` | Los tests de metaheurísticas no comprobaban nada útil |
| ✅ | `P-06` | No había integración continua |
| ✅ | `P-07` | `.gitignore` excluye los CSV de parámetros de test |
| ✅ | `P-08` | Los extras de `setup.cfg` usan `;`, que PEP 508 lee como otra cosa |
| ✅ | `P-09` | Falta `py.typed`: mypy trata `metagen` como `Any` desde fuera |
| ✅ | `P-10` | Los ejemplos de las docstrings usan una API que no existe |
| ⬜ | `P-11` | `mypy src` no pasa limpio: 40 errores, todos en CVOA |

---

## Críticos

### [x] F-01 (R) · `_closest_number` deja inalcanzable medio dominio cuando hay `step`
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

*Cerrado.* `_closest_number` pasa a ser un redondeo a rejilla con origen:
`origin + round((value - origin) / step) * step`, sin suelo. `_generate_numerical`
recibe ese origen y lo usa para recortar **al punto de rejilla más externo que quepa**
en el intervalo, en vez de recortar al extremo, que devolvería un valor fuera de
rejilla. Y `Real.initialize` delega en `_generate_numerical` en lugar de redondear por
su cuenta, con lo que hereda el recorte que le faltaba.

**El matiz que no estaba en el diagnóstico:** `Real.mutate` estrecha el intervalo con
`alteration_limit`, así que anclar la rejilla en el extremo recibido la habría movido
en cada mutación. El origen se captura **antes** de estrechar, de modo que la rejilla
es siempre la del dominio. Comprobado: mutando 300 veces con límite 1.5 en `[-5, 5]`
con paso 1, todos los valores caen en la rejilla.

`Integer` no se ve afectado: usa `randrange(min, max + 1, step)`, que ya está anclado
en el mínimo. `Structure._resize` sí pasa por aquí, y su origen por defecto —el
extremo izquierdo, que es el tamaño mínimo— es el correcto.

Se añadió `test_f01_la_rejilla_de_step_arranca_en_el_minimo` para la segunda mitad del
hallazgo, que no tenía test: el existente solo cubría el suelo.

Sobre la rama de reserva de `_generate_numerical`, para cuando el intervalo no contiene
ningún punto de rejilla: **no es código muerto**. Se alcanza si el usuario fija a mano
un valor fuera de rejilla y luego muta con un `alteration_limit` pequeño; ahí se
recorta al intervalo, que es lo mejor disponible.

### [x] F-02 (R) · TPE toma la peor solución como mejor inicial
`src/metagen/metaheuristics/tpe/tpe.py:111` · test: `test_f02_tpe_initialize_devuelve_la_mejor_solucion`

```python
if best_solution is None or best_solution.get_fitness() < solution.get_fitness():
    best_solution = solution   # comparación invertida; el framework minimiza
```

Con fitness `[0.18, 2.06, 0.35, 11.60, 4.61, 5.52, 7.66, 0.03]`, `initialize` devuelve `11.60`.
Ese valor entra en `self.best_solution` y contamina el `min(...)` de cada iteración.

**Arreglo** Invertir el operador, o reutilizar `random_exploration` como el resto de metaheurísticas.

*Cerrado* invirtiendo el operador, no reutilizando `random_exploration`: ese ayudante
no alimenta `self.solution_history`, que TPE necesita para su muestreo. Se comprobó que
era la **única** comparación invertida del paquete; las otras quince comparan
`candidato < mejor`, coherentes con minimizar.

**El resultado final de TPE no cambia**, y conviene decirlo: media 0.0137 y 8 de 10
victorias sobre el muestreo aleatorio, idénticas antes y después. La razón es que el
`min(...)` de la primera iteración descarta enseguida esa peor solución, así que la
contaminación es transitoria en cuanto el algoritmo mejora algo.

Donde sí cambia es en **el historial de convergencia que se reporta**, porque su primer
valor era el de la peor solución inicial en vez de la mejor:

```
semilla 2, sin arreglar:  el historial arranca en 1.7664
semilla 2, arreglado:     arranca en 0.8576   (y ambos acaban en 0.0166)
```

Es decir, `best_solution_fitnesses[0]`, las curvas de TensorBoard y **cualquier métrica
derivada del historial** —como una tasa de convergencia— partían de un punto peor que
el real, lo que exagera la mejora aparente.

### [x] F-03 (R) · La fase de warmup se calcula y se tira
`src/metagen/metaheuristics/base.py:290-292` · test: `test_f03_el_warmup_no_se_descarta`

`run()` llama a `_warmup()` y justo después a `_initialize()`, que sobrescribe
`current_solutions` y `best_solution` sin comparar. SA lleva `warmup_iterations=5`
por defecto y TPE `10`: son ~100 evaluaciones de fitness tiradas antes de empezar.
En distribuido hay un efecto añadido: como el warmup deja `current_solutions` con
longitud igual al número de warmups, `_launch_distributed_method` reparte carga
para ese tamaño y no para `population_size` (`base.py:99-100`).

**Arreglo** En `_initialize`, fusionar en vez de sustituir.

*Cerrado con la variante conservadora.* `_initialize` ya no asigna `best_solution`,
lo fusiona: solo lo reemplaza si el suyo es mejor que el que dejó el warmup. Y el
reparto distribuido usa `population_size` durante la inicialización, en vez de leer
`len(current_solutions)`, que tras el warmup vale una entrada por ronda y no tiene
nada que ver con la población que se está construyendo.

**No se fusiona la población**, solo el mejor, aunque la propuesta original permitía
ambas cosas. El motivo: las soluciones del warmup son las mejores de cada ronda y
acabarían al principio de la lista, y como *SA usa `solutions[0]`, la primera, no la
mejor* (`F-20`), esa primera pasaría a ser buena por casualidad y taparía `F-20` sin
arreglarlo. Cuando `F-20` esté cerrado, fusionar la población es seguro.

**El efecto en SA es enorme y conviene entenderlo bien:**

| | Antes | Después |
|---|---|---|
| Fitness medio | 1.9112 | **0.1478** |
| Gana al muestreo aleatorio | 1/10 | 6/10 |
| Mejora sobre su propio inicio | 3/10 | **0/10** |

Trece veces mejor, pero **no porque el recocido funcione ahora**: es que SA hace 5
rondas de warmup sobre una población de 20, o sea unas 100 evaluaciones aleatorias que
antes se tiraban enteras. Ahora se conserva la mejor de todas ellas.

Lo dice la última fila: **SA ya no mejora nunca sobre su punto de partida**, cero de
diez. Todo lo que reporta lo encontró el warmup; su fase de recocido no aporta nada
encima. Es un diagnóstico más duro que el anterior, no más suave, y apunta a `F-20` y
`F-25`.

Ojo: SA queda en 6/10 frente al umbral de 7 de `behavior_test.py`. El margen es de
uno, así que su `xfail` podría saltar a `XPASS` con cualquier cambio pequeño. Si pasa,
es la alarma haciendo su trabajo: hay que mirar por qué, no subir el umbral.

### [x] F-04 (R) · El cruce del GA devuelve un hijo que es copia exacta del padre 1
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

*Cerrado.* Se hicieron explícitas las dos ramas, `self.get(...)` para un hijo y
`other.get(...)` para el otro, en vez de reutilizar `variable_value`: esa variable
del bucle venía de `self` y era justo lo que inducía el error. Hay una sola
implementación del cruce, sin gemelo distribuido, compartida por GA, SSGA y el
memético.

**No se tocó** `randint(1, len(basic_variables) - 1)` de la línea 107, que la
auditoría señala «de paso». Intercambiar *todas* las variables produce
`hijo1 = padre2` e `hijo2 = padre1`, es decir, los padres otra vez y ningún material
genético nuevo; excluir ese caso es defendible. Si se quiere permitir, es cambiar
`- 1` por nada, pero como decisión de algoritmia, no como arreglo de este hallazgo.

**El GA sigue sin ganar a la búsqueda aleatoria** después de este arreglo (3/10, media
0.4602 frente a 0.1683). No es que el arreglo falle: es que `A-01` domina el
resultado. Mientras `best_parents` se calcule fuera del bucle y los cinco cruces de
cada generación usen la misma pareja, arreglar el clon no aporta diversidad. Los
`xfail` de GA en `behavior_test.py` siguen justificados y ahora citan solo `A-01`.

### [x] F-05 (R) · `Structure` descarta el valor que se le asigna
`src/metagen/framework/solution/types/structure.py:197-208` · tests: `test_f05_*`

`_convert` construye el tipo a partir de la definición —lo que lo inicializa al azar—
y nunca copia el valor de entrada: `st[0] = 42` guarda un entero aleatorio, `append(7)`
también. La rama `elif BaseType:` (línea 202) es siempre cierta porque es una clase,
no una instancia, así que el `else` con el `ValueError` es código muerto; el mismo
patrón está en `base_solution.py:149`.

**Arreglo** Crear la instancia y llamar a `.set(value)`; cambiar `elif BaseType:` por
`elif isinstance(value, BaseType):`.

*Cerrado, con dos correcciones sobre el arreglo propuesto.*

**`isinstance(value, BaseType)` a secas habría roto las estructuras de grupos.**
`Solution` **no hereda de `BaseType`** —su MRO es `['Solution', 'object']`— y una
estructura sí puede contener sub-soluciones, vía `set_structure_to_variable`. Con la
comprobación literal, esos elementos ya construidos caerían en el `else` y el
`ValueError` saltaría con datos válidos, cambiando un bug por otro. Va
`isinstance(value, (BaseType, Solution))`.

**Aplicar el valor no es un `.set(value)` uniforme.** `Solution.set` toma
`(variable, value)`, así que la rama del `dict` se recorre clave a clave. Y no se
vacía la sub-solución antes, a diferencia de `_set_sub_solution`: con un `dict`
parcial, las variables no mencionadas conservan su inicialización aleatoria en vez
de desaparecer, que dejaría un elemento incompleto dentro de la estructura.

La vía del `dict` tenía el mismo fallo y no la cubría ningún test: `append({'a': 3})`
sobre una estructura de grupos guardaba `{'a': 1}`. Test nuevo,
`test_f05_una_estructura_de_grupos_conserva_el_valor`.

**El gemelo de `base_solution.py:149` también se arregló**, porque el `elif` muerto
allí no es cosmético: `Solution.set('i', {1, 2})` metía un `set` de Python dentro de
una variable entera sin decir nada, en vez de lanzar el `TypeError` que el código ya
tenía escrito. Test nuevo, `test_f05_un_tipo_no_soportado_no_entra_en_la_solucion`.
Necesita la misma pareja `(BaseType, Solution)` por el mismo motivo.

Cierra el error de mypy `structure.py:202` de la tabla de `P-11`.

### [x] F-06 (R) · `Structure.set` y `Structure.insert` lanzan excepción con datos válidos
`structure.py:286` y `structure.py:268` · tests: `test_f06_*`

```
st.set([1, 2, 3])   → TypeError: object of type 'int' has no len()
st.insert(0, 5)     → AttributeError: 'Integer' object has no attribute 'insert'
```

`set` pide el tipo con `get_type(self.get_definition())`, que devuelve `Structure`.
`insert` llama a `insert` sobre el elemento, no sobre la lista.

**Arreglo** `get_type(self.get_definition().get_base())` y `current_values.insert(index, ...)`.

*Cerrado.* `insert` es literalmente el arreglo propuesto. `set` va un paso más allá:
en vez de pedir el tipo con la definición correcta y repetir ahí la conversión, cada
elemento pasa por `_convert`, que es lo que ya usan `append` e `__setitem__`. Los dos
caminos estaban duplicados y solo uno se arregló en `F-05`; ahora hay uno.

Como efecto, `set` hereda del arreglo de `F-05` el caso del `dict`, que su propia
copia no soportaba: `Solution.set` toma `(variable, value)`, así que
`st.set([{'a': 11}, {'a': 22}])` habría fallado igual tras aplicar solo el arreglo
literal. Test nuevo, `test_f06_set_admite_una_lista_de_grupos`.

`BaseTypeClass` deja de importarse: era el único uso, y con él se va el bloque
`TYPE_CHECKING` del módulo.

### [x] F-07 (R) · `import metagen` secuestra el `excepthook` del proceso
`src/metagen/__init__.py:19-30`

Una librería no debe tocar estado global del intérprete. Quien importe MetaGen dentro
de una aplicación mayor se lleva un cambio silencioso en cómo se reportan todas las
excepciones no capturadas.

**Arreglo** Borrar el hook, o exponerlo como función explícita.

*Cerrado borrándolo*, la primera opción. No se expone como función porque nadie la
usaba —`DEBUGGING` y `exception_handler` no aparecen en `src/`, ni en `test/`, ni en la
documentación— y dejar una función instalable sin usar es código muerto. Quien quiera
ese comportamiento lo escribe en dos líneas. `metagen/__init__.py` se queda con la
cabecera de licencia y nada más.

**El daño era mayor de lo que sugiere el diagnóstico.** Con `DEBUGGING = True`, que es
el valor por defecto, el hook delega en el que había y no se nota. Pero basta un
`metagen.DEBUGGING = False` en cualquier punto del proceso para que **todas** las
excepciones no capturadas pierdan su traza, también las del código de la aplicación:

```
RuntimeError: algo se rompio en el codigo de la aplicacion
```

Eso es todo lo que se imprime. Sin traza, sin fichero, sin línea.

**Ojo, hay un segundo culpable que no es MetaGen:** `import metagen.metaheuristics`
sigue cambiando el `excepthook`, porque arrastra Ray y **Ray instala el suyo**
(`ray._private.worker.custom_excepthook`). No es algo que se pueda arreglar aquí; el
test de este hallazgo importa `metagen.framework` a propósito, y lo dice en su
docstring. Se notará menos cuando `F-24` deje de importar Ray sin necesidad.

Test: `test_f07_importar_metagen_no_toca_el_excepthook_del_proceso`, que cruza la
frontera del proceso porque dentro de pytest el paquete ya está importado.

### [x] F-08 (R) · Interbloqueo en CVOA con `update_isolated=True`
`src/metagen/metaheuristics/cvoa/local_tools.py:55-59`

`isolate_individual_conditional_state` adquiere `self.lock` y dentro llama a
`get_individual_state`, que vuelve a adquirirlo. `threading.Lock` no es reentrante:
la hebra se bloquea contra sí misma.

**Arreglo** `threading.RLock()`, o un `_get_individual_state_unlocked` privado.

*Cerrado con `RLock`*, y el argumento que decide entre las dos opciones no es la
elegancia: **con un `Lock` normal, el precio de equivocarse al anidar es un cuelgue
silencioso**, que es el peor fallo posible y justamente este hallazgo. Con `RLock` ese
mismo despiste funciona. El ayudante privado sería más explícito sobre qué código
asume el cerrojo tomado, pero deja intacta la trampa.

**La rama no es fácil de alcanzar, y la primera comprobación se me quedó corta.** Un
CVOA con `update_isolated=True` y `pandemic_duration=4` **termina igual**, sin
arreglar: la llamada solo ocurre pasadas `social_distancing` iteraciones (7 por
defecto) y cuando el sorteo cae del lado del aislamiento. Forzando la rama con
`social_distancing=1` y `p_isolation=0.0`:

```
sin el arreglo -> SE COLGO (interbloqueo)
con el arreglo -> CVOA con update_isolated=True -> 2.75007
```

Conviene retenerlo: **un hallazgo de concurrencia puede no reproducirse con los
parámetros por defecto**, y no reproducirlo no significa que no esté.

El gemelo distribuido, `distributed_tools.py:50`, tiene el mismo anidamiento pero
**no el mismo bug**: es un actor de Ray y no usa cerrojo ninguno.

**Un dato suelto que apunta a `F-23`:** el fitness sale `2.75007` en las dos
configuraciones, que son muy distintas entre sí. Que el resultado no se mueva encaja
con que la cepa muera en la iteración siguiente a la primera mejora.

Test: `test_f08_aislar_un_individuo_no_bloquea_la_hebra`, en hebra demonio con espera
limitada, para que un cuelgue sea un fallo y no deje la suite colgada.

### [x] F-09 (R) · `insert_into_set_strain` puede reventar con `KeyError`
`src/metagen/metaheuristics/cvoa/common_tools.py:126-133`

La rama `'d'` hace `bag.remove(best_dead)` sin comprobar pertenencia; la rama simétrica
de superspreaders (línea 116) sí comprueba. `best_dead` arranca siendo una solución
aleatoria sin evaluar que nunca estuvo en el conjunto.

**Arreglo** Misma guarda de pertenencia y `bag.discard()`.

*Cerrado.* Reproducido con las dos ramas una al lado de la otra, que es donde se ve la
asimetría:

```
rama 's' -> sin error          (tiene la guarda)
rama 'd' -> KeyError: F = inf  {x = 3.4743373693723267}
```

**Las dos ramas pasan a usar `discard`**, no solo la rota. La `'s'` hacía
`if x in bag: bag.remove(x)`, que es correcto pero verboso, y tener dos formas
distintas de escribir lo mismo pegadas la una a la otra es precisamente lo que dejó
esconderse a la asimetría.

**Se retiraron tres `metagen_logger.debug` de la rama `'d'`**, uno de ellos
literalmente `"contains?: %s"`. Son el fósil de alguien depurando este mismo fallo:
la pregunta que imprimían es la que ahora responde el código. Con ellos se va el
`import` de `metagen_logger`, que era el único uso en el módulo.

**Hay una sola implementación**, en `common_tools.py`, compartida por la versión local
y la distribuida: aquí no hay gemelo que revisar.

**Un dato que apunta directamente a `F-10`:** en la misma reproducción, la rama `'s'`
devuelve `insertado=False`. `worst_superspreader` arranca con fitness `inf` —el peor—,
así que `to_insert > worst_superspreader` nunca se cumple y el mecanismo de reemplazo
no llega a ejecutarse jamás. Es el hallazgo siguiente, visto desde aquí.

Test: `test_f09_insertar_en_el_conjunto_de_muertos_no_revienta`.

### [x] F-10 (R) · El «peor superspreader» de CVOA se inicializa al revés
`src/metagen/metaheuristics/cvoa/cvoa_local.py:138-139`

El comentario dice «inicialmente la mejor solución» pero el constructor por defecto crea
la peor. `if to_insert > worst_superspreader` nunca se cumple, así que el mecanismo de
reemplazo del peor superspreader —la diversificación que el código documenta— nunca se
ejecuta.

**Arreglo** `best=True` en el constructor, junto con F-14.

*Cerrado en los dos gemelos*, `cvoa_local.py` y `cvoa_distributed.py`, que tenían la
línea idéntica. `best_dead` **no se toca**: su comentario dice «inicialmente la peor
solución» y `inf` es justamente eso, así que ese estaba bien.

Medido en el mecanismo:

```
como estaba (best=False): fitness inicial = +inf  -> reemplaza? False
arreglado   (best=True) : fitness inicial = -inf  -> reemplaza? True
```

Y contando dentro de una pandemia real, la rama de reemplazo se alcanza 12 veces:
**antes reemplazaba 0 de esas 12, ahora reemplaza 2.**

**El resultado de CVOA no cambia ni un dígito**, y hay que decirlo: cinco semillas,
`[4.058812, 2.883657, 3.021229, 16.083051, 20.669185]`, idénticas antes y después.
Es el mismo patrón que `F-04` con `A-01`: **el arreglo es correcto y otro hallazgo lo
tapa.** El culpable aquí es `F-23`, medido de paso:

```
iteraciones ejecutadas: {'S1': 2}   de un pandemic_duration de 8
```

La cepa muere en la segunda iteración de las ocho declaradas, mucho antes de que la
diversificación de superspreaders pueda influir en nada. Hasta que `F-23` esté
cerrado, este arreglo no se verá en los resultados.

De paso, esto explica el `2.75007` idéntico que salió al verificar `F-08` con dos
configuraciones muy distintas.

Tests: `test_f10_el_peor_superspreader_arranca_siendo_el_mejor` y
`test_f10_el_reemplazo_del_peor_superspreader_se_ejecuta`. El segundo comprueba la
consecuencia, no solo el valor inicial.

### [x] F-11 (R) · La búsqueda local distribuida manda la misma porción a todos los workers
`src/metagen/metaheuristics/mm/mm_distributed_tools.py:57` (estaba en `mm_tools.py:65-68`
hasta que `F-24` separó los dos módulos)

`population[:count]` sin avanzar el cursor. Compárese con `base.py:114-115`, donde sí avanza.

**Arreglo** `population = population[count:]` dentro del bucle.

*Cerrado tal cual*, una línea. Reproducido con una ejecución distribuida real, dando a
cada individuo una identidad para saber cuál vuelve:

```
reparto de carga: [3, 3, 3]
ids de entrada  : [0, 10, 20, 30, 40, 50, 60, 70, 80]
ids de salida   : [0, 0, 0, 10, 10, 10, 20, 20, 20]     <- sin arreglar
ids de salida   : [0, 10, 20, 30, 40, 50, 60, 70, 80]   <- arreglado
```

**Es peor que «desperdicia cómputo»**, que es como lo clasifica la auditoría. Con 9
individuos repartidos entre 3 workers, seis **nunca se buscan** y, como el resultado se
concatena, **la población vuelve siendo tres copias de su primer tercio**. El memético
distribuido perdía dos tercios de su población en cada búsqueda local de nivel 1, en
silencio y con el tamaño correcto.

Comprobado que es **el único sitio** con ese patrón: los otros dos `[:count]` de `src/`
están en `base.py:133-134`, que sí avanza.

Test: `test_f11_la_busqueda_local_distribuida_reparte_la_poblacion`, que **necesita Ray
de verdad** y por tanto se salta en el CI. Es el tercero en esa situación, junto a los de
`F-21` y `F-24`... salvo que el de `F-24` ya no lo necesita.

### [x] F-12 (R) · Todos los `Domain` comparten el mismo conector por defecto
`src/metagen/framework/facades.py:59` · test: `test_f12_cada_domain_tiene_su_propio_conector`

```python
def __init__(self, connector: BaseConnector = BaseConnector()):
```

Argumento por defecto mutable: se evalúa una vez, al importar.
`Domain().get_connector() is Domain().get_connector()` → `True`.

**Arreglo** `connector: BaseConnector | None = None` y `connector or BaseConnector()`.

*Cerrado*, con `is None` en vez de `or`: un `or` trataría como ausente cualquier
conector que resultara falsy, y aquí el valor legítimo y el centinela deben
distinguirse por identidad, no por verdad.

**Lo caro no era el `is`, era el estado compartido.** `BaseConnector` guarda cuatro
diccionarios que `register` muta, y el conector es **el mecanismo de extensión** que
documenta el artículo. Con un solo conector para todo el proceso, registrar un tipo
propio en un dominio recableaba los demás, incluidos los creados después:

```
a.get_connector().register(IntegerDefinition, MiEntero, int)
b.get_connector().get_type(IntegerDefinition)     -> MiEntero    # b es otro Domain
Domain().get_connector().get_type(IntegerDefinition) -> MiEntero # creado despues
```

Test nuevo para eso, `test_f12_registrar_un_tipo_no_afecta_a_los_demas_dominios`; el
que ya existía solo comprobaba la identidad.

**Cambia la firma de `Domain.__init__`**, de `BaseConnector` a `BaseConnector | None`.
Ninguna forma de llamada se rompe: `Domain()`, `Domain(mi_conector)` y
`Domain(connector=mi_conector)` siguen funcionando igual.

Comprobado además que este era **el único argumento por defecto mutable de `src/`**.

### [x] F-13 (R) · TPE modifica el `Domain` que le pasa el usuario
`src/metagen/metaheuristics/tpe/tpe.py:89` · test: `test_f13_tpe_no_modifica_el_dominio_del_usuario`

`self.domain._connector = TPEConnector()` deja el dominio del usuario modificado para
siempre. Comparar varias metaheurísticas en un bucle da resultados dependientes del orden.

**Arreglo** Trabajar sobre una copia, o exigir `Domain(connector=TPEConnector())` y validarlo.

*Cerrado con la copia*, no con la exigencia. Exigir `Domain(connector=TPEConnector())`
sería más coherente con GA —que ya funciona así, aunque sin validarlo: ese es `A-07`—
pero **rompería todos los guiones existentes**: `TPE(domain, fitness)` sobre un
`Domain()` normal es la forma que documentan el artículo y los cuadernos, y TPE es una
de las dos metaheurísticas evaluadas allí. No es un precio que pague este hallazgo.

El `deepcopy` va **antes** del `super().__init__`, no después: así `self.domain` nace
ya siendo la copia y no hay un instante en que la clase base apunte al dominio del
usuario.

La contaminación ocurría en el **constructor**, no en `run()`: bastaba con crear un TPE
para que el dominio quedara con `TPEConnector` para siempre.

**Los resultados de TPE no cambian ni un dígito**, y conviene dejarlo dicho: ni
`deepcopy` ni construir el conector consumen sorteos. Comprobado sobre la esfera 2D con
las diez semillas, comparando valores y no veredictos:

```
antes:   [0.0011548337, 0.0249535054, 0.0044897437, ..., 0.0064106984]
despues: [0.0011548337, 0.0249535054, 0.0044897437, ..., 0.0064106984]
```

Queda una incoherencia de fondo para `A-07`: GA espera que el usuario traiga el
conector y TPE se lo monta él. Una de las dos convenciones sobra.

---

## Importantes

### [x] F-14 (R) · `sys.float_info.min` no es «menos infinito»
`src/metagen/framework/solution/base_solution.py:98` · test: `test_f14_el_centinela_de_mejor_fitness_es_menor_que_cualquier_objetivo`

Es `+2.2250738585072014e-308`. Cualquier objetivo que pueda ser negativo ya es «peor»
que el centinela «mejor posible». Las docstrings de `base_solution.py:65` y
`devsolution.py:40` afirman que vale `0.0`, que tampoco es cierto. Causa de fondo de F-10.

**Arreglo** `-math.inf` / `math.inf`, y corregir las dos docstrings.

*Cerrado.* El centinela vive en un único sitio, `base_solution.py:98`, así que el
cambio es esa línea más las docstrings. Estas afirmaban `0.0` para el mejor y
`1.7976931348623157e+308` para el peor; ninguno de los dos valores era cierto y ahora
son `-inf` e `inf`. Se corrigieron **seis** líneas de docstring, no dos: `base_solution.py`
y `devsolution.py` repiten el ejemplo tres veces cada una.

**Un test ajeno a la auditoría también codificaba el valor viejo:**
`framework_test/alteration_test.py:44` comprobaba
`solution.fitness == sys.float_info.max`. Se actualizó a `math.inf`: su intención
—una solución recién creada arranca con el peor fitness posible— es la misma, solo
tenía el número escrito a mano.

Esto es la causa de fondo de `F-10` (*el «peor superspreader» de CVOA se inicializa al
revés*), que sigue abierto: ahora `Solution(best=True)` sí devuelve algo menor que
cualquier objetivo real, que es lo que aquel mecanismo necesitaba para funcionar.

### [x] F-15 (R) · `Solution.__hash__` no mira las variables
`base_solution.py:444` · tests: `test_f15_*`

`hash((self.get_variables().__hash__, self.fitness))`: `dict.__hash__` es `None`, así que
el hash depende solo del fitness. Dos soluciones iguales con distinto fitness rompen el
invariante `a == b ⇒ hash(a) == hash(b)`. Duele en CVOA (cuatro `set` de soluciones) y
en la lista tabú (`tools.py:44`).

**Arreglo** Hashear una representación canónica de las variables y no incluir el fitness.

*Cerrado tal cual*, pero la representación canónica tiene más trabajo del que sugiere la
frase: los valores de un `Solution` pueden ser una **lista** (`Structure`) o **otra
solución** (un grupo), y ninguna de las dos se hashea por sí sola. El hash viejo las
esquivaba todas porque nunca llegaba a mirarlas. Hay un ayudante, `_hashable`, que baja
recursivamente y convierte listas en tuplas y sub-soluciones en tuplas ordenadas.

**Donde el invariante roto se convierte en un fallo de verdad es en la lista tabú**, y
el diagnóstico no lo dice: `local_search_with_tabu` mete la lista en un `set` y pregunta
`neighbor not in tabu_set`. Un vecino con las mismas variables que una solución
prohibida **es** esa solución para `__eq__`, pero con el hash viejo caía en otro cubo si
su fitness no coincidía, y el `in` respondía que no estaba. **La lista tabú dejaba pasar
justo lo que debía bloquear.** Test:
`test_f15_la_lista_tabu_bloquea_una_solucion_ya_prohibida`.

**Lo que no arregla, y conviene no vender de más.** Se esperaba que acelerase CVOA
bastante, porque el hash viejo metía en un solo cubo a todas las soluciones de igual
fitness. Medido sobre la esfera 2D: **3.6 s → 3.1 s**, un 14 %. En un problema continuo
casi ningún fitness se repite, así que apenas había colisiones. El escenario en que sí
dolería es la **codificación binaria** del artículo de CVOA, donde muchísimos individuos
comparten fitness; no se ha medido.

**Y destapó `F-29`**, que es más importante: al cambiar el hash cambia el orden de
iteración de los conjuntos, y CVOA itera conjuntos de soluciones.


### [x] F-16 (R) · Los mensajes de error de `Domain` salen mal formados
`domain/preconditions.py:107` · test: `test_f16_el_mensaje_de_variable_ya_definida_es_legible`

`elif mode == ("d_a", "d_g")` compara un str con una tupla. Redefinir una variable produce
`[STRUCTURE definition error] The variable i is length.`

**Arreglo** `elif mode in ("d_a", "d_n", "d_g", "d_s"):` con las cuatro asignaciones anidadas.

*Cerrado tal cual.* **Los cuatro modos caían en la rama muerta, no solo el de «ya
definida»** que recoge el diagnóstico: `d_n`, `d_g` y `d_s` salían igual de rotos, y
los cuatro se usan (`facades.py:42, 47, 53` y `core.py:312`).

```
antes:   [STRUCTURE definition error] The variable i is length.
después: [DEFINITION error] The variable i is already defined.
```

**Se arregló también el espacio doble de `Messages.step_zero`**, que quedó señalado al
cerrar `F-19` como perteneciente a esta familia: producía «The  value must be greater
than zero». Afectaba a `Integer`, `Real` y `Structure`.

**Un problema distinto que salió al verificar, y que no es de este hallazgo:**
`link_variable_to_group('nada', 'x')` sobre un grupo inexistente lanza `KeyError:
'nada'`, no el mensaje de `d_n`. Es decir, hay rutas de la fachada que no llegan a
pasar por la precondición. No lo cubre `F-16`, que es sobre el formato del mensaje, no
sobre dónde falta comprobarlo.

Tests: el que ya existía, más `test_f16_los_cuatro_mensajes_de_definicion_son_legibles`
(parametrizado por los cuatro modos) y
`test_f16_el_mensaje_de_paso_cero_no_lleva_espacio_doble`.

### [x] F-17 (R) · Categorías duplicadas aceptadas, categoría única rechazada
`domain/preconditions.py:32-39` · tests: `test_f17_*`

`pairwise` solo compara adyacentes: `["a", "b", "a"]` se acepta. Y `len(value) >= 2`
impide fijar un hiperparámetro a un único valor.

**Arreglo** `len(set(value)) == len(value)` y un solo tipo; permitir longitud 1
(protegiendo `Categorical.mutate`, que haría `random.choice([])`).

*Cerrado tal cual.* `is_categories_value` se reescribió entera en vez de parchear la
condición: comprueba por separado que sea una lista no vacía, que todo sean valores
básicos, que compartan tipo y que no haya repetidos.

`pairwise` era peor de lo que sugiere el diagnóstico: no solo pasaba `["a", "b", "a"]`,
también **`["a", "b", "a", "b"]`**, donde la mitad de las categorías están repetidas.
Basta con que no haya dos iguales *seguidas*.

`Categorical.mutate` quedó protegido, y la guarda es **volver sin tocar nada**, no
elegir entre la lista completa: con una sola categoría no hay a qué mutar, e inventar
un cambio sería mentir sobre lo que hizo. Comprobado con cinco mutaciones seguidas
sobre un dominio de una categoría.

`pairwise` sigue importándose: lo usa `is_basic_vector_sequence_value`, que es otra
función.

Tests: los dos que ya existían, más `test_f17_una_sola_categoria_se_puede_mutar` y
`test_f17_otras_listas_de_categorias_invalidas_se_rechazan`, parametrizado sobre los
tres casos que el diagnóstico no cubría.

### [x] F-18 (R) · Una estructura estática se identifica como `DYNAMIC`
`domain/core.py:695` · test: `test_f18_una_estructura_estatica_se_identifica_como_static`

`Base.__init__(self, D)` mientras `get_attributes()` devuelve `S`.

**Arreglo** `Base.__init__(self, S)`.

*Cerrado*, y es literalmente esa línea. Antes de tocarla se comprobó que el bug no
sostenía nada: `_meta_type` solo llega a `get_type()`, y `get_type()` en `src/` se usa
únicamente dentro de los `__str__`. Quien distingue estructuras estáticas de dinámicas
—`Structure.initialize`, `Structure.mutate`— lo hace con `isinstance` sobre la clase de
la definición, no con el meta-tipo. Así que el único efecto observable era que una
estructura estática se imprimía como `s: [DYNAMIC]` mientras sus atributos decían
`STATIC`.

### [x] F-19 (R) · Estructuras dinámicas: nunca alcanzan el máximo y revientan si min = max
`types/structure.py:87` · tests: `test_f19_*`

`randrange(min_size, max_size, step or 1)` excluye el máximo, incoherente con
`check_length` y con `_resize`. `min == max` lanza `ValueError`. `_alterate` hace
`random.randint(1, current_size)` y peta con una estructura vacía. Ni
`DynamicStructureDefinition` ni `StaticStructureDefinition` validan sus longitudes.

**Arreglo** `randrange(min_size, max_size + 1, step)`, guardar `min == max`, proteger
`_alterate` y añadir precondiciones de longitud.

*Cerrado, las cuatro mitades.* Las dos primeras son la misma línea: con
`max_size + 1`, `randrange(3, 4, 1)` devuelve 3 y el caso `min == max` deja de ser un
error, así que no hace falta guarda aparte. Comprobado que ahora sí salen las cuatro
longitudes: `[2, 3, 4, 5]` en 300 inicializaciones de una `dynamic(2, 5)`, donde antes
salían `[2, 3, 4]`.

`_alterate` **no se protege con un `max(1, ...)`**, que inventaría un cambio donde no
hay nada que cambiar: si la estructura está vacía, no hay nada que alterar y se
vuelve. Solo es alcanzable con longitud mínima cero, que ahora es legal.

Las precondiciones son nuevas, `Preconditions.Structure`, junto a las de `Integer` y
`Real`, con dos reglas distintas para cada definición:

| Definición | Regla |
|---|---|
| dinámica | `min >= 0`, `min <= max`, paso positivo |
| estática | `longitud >= 1` |

**`min == max` se permite a propósito**, al revés que en `Integer` y `Real`, que
exigen `min < max`: en una estructura declara una longitud fija, y `check_length` ya
la aceptaba como `min <= longitud <= max`. Por eso los mensajes son propios y no
reutilizan `Messages.min_max`, que dice «must be less than».

Antes de esto, `define_static_structure('s', -3)` se aceptaba y producía una
estructura de longitud 0 cuyo `check_length` exigía −3: ningún valor podía ser válido.

Ningún test existente usaba una longitud imposible, así que las precondiciones nuevas
no rompen nada.

**De paso, sin arreglar:** `Messages.step_zero` tiene un espacio doble —«The  length
must be greater than zero»— que afecta también a `Integer` y `Real`. Es de la familia
de `F-16`, y allí debería cerrarse.

### [x] F-20 (R) · SA evalúa veinte soluciones iniciales para usar una
`sa/sa.py:117` · test: `test_f20_sa_no_evalua_una_poblacion_entera_al_inicializar`

No pasa `population_size` al `super().__init__`, así que hereda 20 aunque `iterate` solo
use `solutions[0]` (y no el mejor de los veinte, sino el primero). `self.T_min = 1e-8`
(línea 124) no se usa en ningún sitio.

**Arreglo** `population_size=1` y aplicar `T_min` como suelo del enfriamiento.

*Cerrado, las dos mitades.* El presupuesto de SA pasa de **135 evaluaciones a 21**:

| | Antes | Después |
|---|---|---|
| Evaluaciones | 135 | **21** |
| Mejora sobre su inicio | 0/10 | **3/10** |
| Gana al azar | 6/10 | 5/10 |
| Fitness medio | 0.1478 | 2.2720 |
| Azar, mismo presupuesto | 0.2070 | 0.9169 |

**El fitness absoluto empeora y hay que explicarlo bien**, porque parece un retroceso y
no lo es: SA recibía **100 evaluaciones de búsqueda aleatoria disfrazadas de warmup**
(5 rondas × 20 de población heredada) más 20 de inicialización, de las que usaba una.
Ahora gasta 15 de sus 21 evaluaciones en recocer, no en tirar dados. La fila que lo
demuestra es la segunda: **de 0/10 a 3/10 en «mejora sobre su inicio»**, que era la que
delataba que todo lo bueno venía del warmup.

`T_min` estaba asignado y **no se leía en ningún sitio**, así que el enfriamiento tendía
a cero sin suelo. Ahora `current_temp = max(current_temp * cooling_rate, T_min)`.

**Lo que sigue sin funcionar, y ahora se ve limpio: `F-30`.** Con `initial_temp=50` y
`cooling_rate=0.99`, tras 20 iteraciones la temperatura sigue en 40.9 y un
empeoramiento de 5.0 se acepta con probabilidad 0.89. SA acepta casi todo: es un paseo
aleatorio, no un enfriamiento.

Tests: el que ya existía, más `test_f20_la_temperatura_no_baja_de_t_min`.

### [x] F-21 (R) · `run()` apaga Ray aunque no lo haya arrancado
`metaheuristics/base.py:307-308`

Si el usuario conectó a un clúster existente, o compara varias metaheurísticas en un
script, la primera que termina se lleva el runtime de las demás.

**Arreglo** Recordar en un flag si fue `run()` quien llamó a `ray.init()`.

*Cerrado* con el flag, tal cual. La condición de apagado deja de mirar
`self.distributed and IS_RAY_INSTALLED`: si `started_ray` es cierto, esas dos ya lo
eran, y repetirlas invita a que se desincronicen.

Se revisaron los gemelos: el único otro `ray.init()` del paquete está en
`cvoa/distributed_launcher.py:57` y **no tiene `shutdown`**, así que ahí no está el
bug. Es el desequilibrio contrario, y no lo toca este hallazgo.

**Queda un cabo suelto del mismo asunto, sin arreglar:** el `shutdown` está en la ruta
normal de `run()`, no en un `finally`. Si el bucle lanza, el runtime que arrancó
`run()` se queda vivo. Es la mitad simétrica de este hallazgo y pide una decisión
aparte sobre el manejo de errores de `run()`.

Test: `test_f21_run_no_apaga_un_ray_que_no_arranco`, que **necesita Ray de verdad** y
por tanto se salta en el CI, que no instala los extras a propósito (ver `P-06`). Es el
segundo test en esa situación, junto al de `F-24`.

### [x] F-22 (R) · TPE escribe valores fuera del dominio saltándose la validación
`tpe/tpe_tools.py:30, 51-56, 71-75`

`np.random.uniform(min_value, max_value + 1)` (el `+1` es de enteros);
`if np.isnan(value) or value is None` (si fuera `None`, `np.isnan(None)` ya habría
lanzado `TypeError`); y `self.value = value`, que salta `set()` y `check()`. Los tres se
refuerzan: un valor fuera de rango llega intacto a la función de fitness del usuario.
`TPECategorical` devuelve además escalares NumPy en vez de tipos nativos.

**Arreglo** `max_value` a secas, invertir el `if`, usar `self.set(value)` y `.item()`.

*Cerrado, los cuatro.* **El `+1` no sobra en todas partes**, y el diagnóstico no lo
distingue: en `get_numpy_rng().integers(min_value, max_value + 1)` es **correcto**,
porque el límite superior de `integers()` de NumPy es exclusivo. Solo sobra en las dos
llamadas a `uniform()`, cuyo límite sí es inclusivo. Quitarlo de la de enteros habría
hecho inalcanzable el valor máximo, cambiando un bug por otro.

**Y se alcanza en ejecuciones normales**, no solo forzándolo. Instrumentando una
ejecución real de TPE sobre un dominio de dos enteros y una categórica —que es el caso
de uso de TPE, optimización de hiperparámetros—:

```
sin arreglar: 960 muestreos, 141 fuera de rango   (15 %)
arreglado   : 960 muestreos,   0 fuera de rango
```

La rama de reserva se toma cuando la desviación de los valores de referencia es cero, es
decir, **cuando coinciden**: raro en un problema continuo, muy común en uno discreto.

**Los resultados de TPE sobre la esfera 2D no cambian ni un dígito**, y conviene decirlo
para que nadie lo interprete como que el arreglo no hace nada: ahí las variables son
reales y esa rama casi no se toma.

`self.set(...)` en vez de `self.value = ...` es lo que hace que el `check()` del dominio
vuelva a correr. Con la asignación directa, un valor fuera de rango llegaba intacto a la
función de fitness del usuario.

Tests: `test_f22_el_remuestreo_de_tpe_no_sale_del_dominio`,
`test_f22_el_remuestreo_devuelve_tipos_nativos` (parametrizado) y
`test_f22_la_guarda_de_none_no_revienta`.

### [x] F-23 (R) · CVOA se detiene al encontrar una mejora y reporta el tiempo mil veces más corto
`cvoa_local.py:333` y `local_launcher.py:45`

`third_condition = self.best_strain_solution_found and self.time > 1`: la bandera nunca
se reinicia, así que la cepa muere en la iteración siguiente a la primera mejora.
`timedelta(milliseconds=t2 - t1)` con `time()` en segundos.

**Arreglo** Contador de iteraciones sin mejora, y `timedelta(seconds=...)`.

*Cerrado, y es el arreglo que más ha movido un resultado en toda la auditoría.*
Con `pandemic_duration=8`, cinco semillas:

| | Sin arreglar | Arreglado |
|---|---|---|
| Iteraciones ejecutadas | 2 de 8 | 9 de 8 |
| Fitness medio | **9.343187** | **0.000293** |
| Valores | `[4.06, 2.88, 3.02, 16.08, 20.67]` | `[0.0006, 0.0006, 0.000005, 0.00004, 0.0002]` |

La cepa se moría en su segunda iteración **porque había encontrado una mejora**. Es
decir: cuanto antes funcionaba CVOA, antes lo apagaban.

**La condición no se borra, se convierte en lo que decía ser.** La bandera pasa a
alimentar un contador de iteraciones sin mejora, que se reinicia cuando hay una, y el
umbral es una propiedad nueva de la cepa:

```python
max_iterations_without_improvement: Optional[int] = None
```

**Va al final de `StrainProperties` a propósito**, para no desplazar los campos que ya
había y no romper ninguna construcción posicional existente. Y **por defecto es `None`,
que no detiene nada**: así la cepa agota su `pandemic_duration`, que es el presupuesto
que el usuario declaró, en vez de que el arreglo invente un número mágico. Quien quiera
la salida temprana la pide.

**Efecto secundario que hay que saber: CVOA ahora tarda.** Antes hacía 2 iteraciones y
terminaba al instante; ahora corre las que se le pidan, y la población de infectados
crece en cada una. Con `pandemic_duration=8` un lanzamiento pasa de instantáneo a
decenas de segundos. No es una regresión: es el algoritmo ejecutándose.

**Esto destapa `F-10`**, que estaba tapado por este. Con la cepa muriendo en la
iteración 2, la diversificación de superspreaders no tenía ocasión de influir; ahora
sí. No se ha medido la contribución aislada de `F-10` con `F-23` ya cerrado: el
experimento ahora es lento y no cambiaba ninguna decisión.

La segunda mitad, `timedelta(milliseconds=t2 - t1)` sobre un `time()` que devuelve
segundos, estaba **en los dos lanzadores**, no solo en el local: reportaban duraciones
mil veces más cortas.

Tests: `test_f23_una_cepa_no_muere_al_encontrar_la_primera_mejora`,
`test_f23_el_estancamiento_si_detiene_la_cepa_cuando_se_pide` y
`test_f23_el_tiempo_de_ejecucion_se_reporta_en_segundos`.

### [x] F-24 (R) · El algoritmo memético exige Ray aunque no se distribuya
`mm/mm_tools.py:5-8` · test: `test_f24_el_memetico_no_necesita_ray`

La importación es de módulo, no de la rama distribuida. En una instalación estándar
`Memetic` no existe en `metagen.metaheuristics`, pese a que el README lo anuncia.

**Arreglo** Separar `mm_tools` (sin Ray) de `mm_distributed_tools` (con Ray).

*Cerrado tal cual.* `mm_tools` se queda con las tres funciones que no distribuyen
—`local_search_of_two_children`, `population_local_search` y `local_search`— y
`mm_distributed_tools` (nuevo) con las cuatro que sí. Los dos puntos donde el
despachador salta a la rama distribuida importan el módulo **dentro de la función**,
no arriba, que es lo que hacía falta para que una ejecución sin distribuir no toque
Ray. No hay importación circular: el módulo distribuido sí importa de `mm_tools` a
nivel de módulo, y solo en esa dirección.

`metagen/metaheuristics/__init__.py` **exporta `Memetic` siempre**, sin la guarda
`if is_package_installed("ray")`. Era la consecuencia visible del hallazgo: el README
anunciaba un algoritmo que no existía en una instalación estándar.

**El test se ha reescrito, y es una mejora aparte del arreglo.** El anterior se
*saltaba* cuando Ray estaba instalado, así que en la máquina de desarrollo no corría
nunca y solo el CI lo ejercitaba. El nuevo **bloquea `ray` en un subproceso** con un
buscador en `sys.meta_path`, de modo que la comprobación es la misma en todas partes,
y además ya no se limita a importar: construye un memético y lo ejecuta.

Como efecto, **desaparece el «solo observable sin Ray»** que arrastraban `P-06` y las
notas del proyecto, y la suite pasa de `2 skipped` a `1 skipped` en esta máquina.

**`Memetic` entra en `behavior_test.py`**, como dejaba anotado `P-05`. Medido con el
mismo protocolo que el resto y **pasa las cuatro propiedades sin `xfail`**:

| Algoritmo | Evals | Gana al azar | Mejora sobre su inicio | Fitness medio | Azar |
|---|---|---|---|---|---|
| Memetic | 610 | **10/10** | **10/10** | **0.0002** | 0.0425 |

Es, con diferencia, el mejor resultado del módulo; también el que más evaluaciones
gasta. Nótese que el memético **sí hace búsqueda local de verdad** —cada vecino parte
de `deepcopy(solution)`, no en cadena— al revés que la tabú (`A-03`) y que SA (`F-25`).

**Ojo, `F-11` se ha mudado de fichero**: *la búsqueda local distribuida manda la misma
porción a todos los workers* vivía en `mm_tools.py:65-68` y ahora está en
`mm_distributed_tools.py:57`. El bug se ha trasladado intacto, sin arreglar, porque es
otro hallazgo.

### [x] F-25 (R) · SA se queda con el último vecino, no con el mejor
`src/metagen/metaheuristics/sa/sa.py:161` · tests: `test_f25_*`

```python
best_neighbor = neighbor          # alias, no una copia
best_fitness  = neighbor.get_fitness()

for _ in range(self.neighbor_population_size - 1):
    neighbor.mutate(...)          # muta EL MISMO objeto
    neighbor.evaluate(...)
    if neighbor.get_fitness() < best_fitness:
        best_neighbor = deepcopy(neighbor)   # aquí sí se copia
```

`best_neighbor` referencia el mismo objeto que el bucle sigue mutando, así que si el
mejor vecino resulta ser **el primero**, `best_neighbor` acaba apuntando al último
generado mientras `best_fitness` sigue anunciando el valor del primero. Reproducido
aislando el patrón: SA acepta como mejora una solución creyendo que vale `7.7253`
cuando su valor real es `24.7073`.

Hay un segundo problema en el mismo bucle: los vecinos se generan **en cadena**,
mutando acumulativamente el mismo objeto en vez de partir cada vez de
`current_solution`. Es el mismo patrón que `A-03` reprocha a la búsqueda tabú, y se
aleja del punto actual en lugar de explorar su vecindario.

Con `neighbor_population_size=1`, el valor por defecto, el bucle no llega a
ejecutarse y nada de esto se observa: por eso no aparece en las mediciones de `P-05`.

**Arreglo** `best_neighbor = deepcopy(neighbor)` en la línea 161, y generar cada
vecino desde `deepcopy(current_solution)` dentro del bucle.

*Cerrado, las dos mitades.* Medido con `neighbor_population_size=5`, diez semillas y el
**mismo presupuesto de 81 evaluaciones** en ambos casos:

| | Sin arreglar | Arreglado |
|---|---|---|
| Gana al azar | 4/10 | **9/10** |
| Fitness medio | 0.9252 | **0.0196** |
| Devuelve algo que no es su mejor | **2/10** | 0/10 |

La última fila es la huella directa del alias: en dos de diez semillas SA devolvía una
solución que **no era la mejor de su propio historial**.

**Con el valor por defecto, `neighbor_population_size=1`, no cambia nada**, porque el
bucle no llega a ejecutarse. Comprobado: 2.2720 antes y después.

**Y eso destapa algo que conviene decidir: el valor por defecto deja a SA sin selección
ninguna.** Con un solo vecino no hay entre qué elegir, así que SA queda como un paseo
aleatorio con aceptación de Metropolis —que además acepta casi todo, ver `F-30`—. Con
cinco vecinos **gana al azar 9 de 10 veces**. Subir el valor por defecto es decisión de
algoritmia, no de auditoría, pero la diferencia es grande y está medida.

El test de la cadena es determinista y no estadístico: con `alteration_limit=1.0`
ningún vecino puede quedar a más de 1.0 del punto actual. Sin arreglar, **9 de 10
vecinos se salían**, llegando a 2.09 de distancia.

Tests: `test_f25_sa_devuelve_el_mejor_vecino_no_el_ultimo` y
`test_f25_los_vecinos_salen_de_la_solucion_actual_no_en_cadena`.

### [x] F-26 (R) · La semilla no reproduce entre procesos: `mutate` recorre un conjunto
`src/metagen/framework/solution/base_solution.py:279` · test: `test_f26_la_misma_semilla_reproduce_entre_procesos`

```python
altered_variables = set(get_rng().sample(list(variables), alterations_number))

for variable in altered_variables:      # <- se itera un CONJUNTO de cadenas
    value = self.get(variable)
    value.mutate(alteration_limit=alteration_limit)
```

`random.sample` ya devuelve elementos **únicos y en orden determinista**, así que el
`set(...)` no aporta nada y sí quita: el orden de iteración de un conjunto de cadenas
depende de sus hashes, y Python los **aleatoriza en cada arranque del intérprete**
(PEP 456). Como cada variable consume sorteos al mutar, el orden decide qué valor le
toca a cada una.

Reproducido con el mismo `seed=7` y seis variables reales, variando solo
`PYTHONHASHSEED`:

```
HASHSEED=0 -> [-3.557449, 1.306259, -2.103907, -4.534173, -3.822078,  3.584685]
HASHSEED=1 -> [-2.103907, 1.306259, -3.557449, -4.534173,  3.584685, -3.822078]
```

Son los mismos valores permutados entre variables. Nótese que un estadístico agregado
—una suma, una media— no lo detecta: hay que comparar variable a variable.

**Esto invalida la garantía de `A-06`**: `seed=42` reproduce dentro del mismo proceso,
pero **no entre ejecuciones distintas**, que es la reproducibilidad que importa para un
experimento. Afecta a todo lo que llame a `Solution.mutate`, es decir, a todas las
metaheurísticas. El artículo afirma promediar sobre 10 semillas; esas medias son
correctas como medias, pero cada ejecución individual no es repetible.

**Arreglo** Quitar el `set(...)` e iterar la lista que devuelve `sample`.

*Cerrado.* Una línea. El test cruza la frontera del proceso a propósito —dentro de una
misma ejecución el fallo es invisible— y fija dos `PYTHONHASHSEED` concretos en vez de
confiar en los aleatorios, para que sea determinista y no acierte por suerte. Con esto
la garantía de `A-06` se sostiene también entre ejecuciones.

### [x] F-27 (R) · `p_isolation` significa lo contrario de lo que dice su nombre
`src/metagen/metaheuristics/cvoa/cvoa_local.py:290` y su gemelo · descubierto al leer el artículo de CVOA

```python
if get_rng().random() < self.strain_properties.p_isolation:
    self.update_new_infected_population(infected_population, new_infected_individual)   # se CONTAGIA
else:
    ...                                                                                  # se aísla
```

Con `random() < p_isolation` el individuo **se contagia**, y solo se aísla en la rama
contraria. Es decir, `p_isolation` es la probabilidad de **no** aislarse. Medido, con
la rama de distanciamiento realmente alcanzada (`social_distancing=2`):

```
p_isolation=0.1  ->  14, 54, 22, 12, 4, 2, 1, 1, 1      la pandemia se apaga
p_isolation=0.5  ->  14, 54, 112, 163, ..., 2143        crece
p_isolation=0.9  ->  14, 54, 180, 548, ..., 124343      explota
```

**Más aislamiento, más contagios.** Y no es solo la dirección: el umbral en que la
pandemia deja de crecer está entre `p_isolation` 0.20 y 0.30, y el artículo sitúa
`R0 = 1` en `P_ISOLATION ≈ 0.65-0.70` (Figura 5). `1 − 0.30 = 0.70` y `1 − 0.20 = 0.80`:
**el parámetro de MetaGen es el complementario del del artículo**, con los números
cuadrando.

**El código es fiel al pseudocódigo publicado**, Algoritmo 3, línea 9:
`if R4 < P_ISOLATION then newInfected ← i`. Pero ese pseudocódigo **contradice a su
propio artículo**: el texto dice que un individuo aislado pasa a recuperados, y la
Figura 5 muestra `R0` decreciendo cuando `P_ISOLATION` crece. Texto y figura coinciden
entre sí; el pseudocódigo es el que discrepa.

**Consecuencia práctica.** El artículo vende como ventaja n.º 2 que «CVOA puede detener
la exploración tras varias iteraciones, sin necesidad de configurarlo», porque la
población de infectados decrece hasta vaciarse (Figura 2). **En MetaGen no decrece
nunca** con los valores por defecto: crece de forma exponencial. Es la causa de fondo
de que CVOA tarde minutos desde que `F-23` dejó que las cepas se ejecuten enteras.

**Arreglo** Invertir la comparación en los dos gemelos, de forma que `p_isolation` sea
la probabilidad de aislarse.

**Criterio de David, 7 de septiembre de 2026: la errata está en el pseudocódigo y el
texto es lo correcto.** El arreglo va, por tanto, en la dirección del texto. **No se
aplica todavía**: CVOA se ataca en una sesión dedicada, porque el diseño del algoritmo
es de Paco Martínez-Álvarez, primer autor, y una errata en su pseudocódigo no se
corrige desde el código sin hablarlo.

Refuerza el criterio que **el mismo patrón aparece dos veces más** en el Algoritmo 2:
`if R2 < P_SUPERSPREADER` usa la tasa *ordinaria* y `if R1 < P_TRAVEL` la distancia
*ordinaria*, ambas al revés de lo que dice el texto. MetaGen **no** hereda esas dos.

Detalle completo y orden de ataque en
`metagen-auditoria/CVOA-cuestiones.md`.

*Cerrado el 10 de septiembre de 2026, segundo paso de la sesión de CVOA, decisión de
David con la medición delante.* Se intercambian las dos ramas en los tres sitios —los dos
gemelos y `distributed_tools`—, con el mismo sorteo único, así que el número de tiradas
no cambia. **Con `p_isolation = 0.5` las dos semánticas son estadísticamente la misma**,
porque `1 − 0.5 = 0.5`; lo que cambia es el significado de los demás valores.

**La medición que decidió, ya con `F-29` cerrado y por tanto reproducible.** Invertir
equivale exactamente a usar `1 − p`, así que se midió sin tocar el código. Infectados por
iteración, una cepa, `seed=0`:

Dominio binario de 10 bits, el del artículo, con sus parámetros (duración 30,
distanciamiento 7):

| semántica | `p_isolation` | curva |
|---|---|---|
| actual | 0.5 | 8, 11, 19, 27, 39, 43, 42, 25, 17, 4 … se apaga |
| actual | 0.7 | 8, 11, 19, 27, 39, 43, 42, 29, 22, 23, 19, 12, 15, 15 … más despacio |
| **invertida** | 0.7 | 8, 11, 19, 27, 39, 43, 42, **14, 8, 4** … |
| **invertida** | 0.8 | 8, 11, 19, 27, 39, 43, 42, **14, 4, 2** … |

La curva de la Figura 2 —pico hacia la séptima iteración y decaimiento— aparece con las
dos semánticas, porque en 1024 individuos posibles los recuperados y los muertos frenan
solos la pandemia. Pero **la dirección del parámetro solo es la del artículo con la
invertida**: más aislamiento, antes se apaga. Con la actual, subir `p_isolation` la
prolonga.

Dominio continuo 2D, distanciamiento a 2 para que la rama entre pronto, tope de 20 000:

| semántica | `p_isolation` | curva | tiempo |
|---|---|---|---|
| actual | 0.5 | 14, 57, 111, … 14 991, 24 914, tope | 14 s |
| actual | 0.7 | 14, 57, 136, 277, 675, … 44 723, tope | 13 s |
| **invertida** | 0.7 | 14, 57, 67, 48, 33, 40, 50 … **meseta en ~55** | **0.4 s** |
| **invertida** | 0.8 | 14, 57, 49, 30, 21, 21, 12 … **4** | **0.1 s** |

Con la semántica actual, el 0.7 que recomienda el artículo hace **explotar antes** la
pandemia; con la invertida la estabiliza, y 0.8 la apaga. **CVOA vuelve a terminar solo y
a tardar décimas de segundo**, que es la ventaja n.º 2 del artículo, recuperada.

**Una trampa de método que costó una tanda de mediciones inútiles**, y que el documento
de CVOA ya avisaba: la primera medición, con el distanciamiento del artículo (7) sobre el
dominio continuo, dio **seis curvas idénticas** para las dos semánticas y tres valores de
`p_isolation`. No porque no importara, sino porque a la sexta iteración ya había 23 000
infectados y la rama del aislamiento **no había llegado a ejecutarse**. En un dominio
continuo cada infectado es un individuo nuevo y nada frena el crecimiento antes del
distanciamiento; el artículo trabaja con 10 a 50 bits. Comprobar que la rama se ejecuta,
antes de dar por bueno lo que se mide sobre ella.

Las ejecuciones que explotan dan mejor fitness en estas tablas por una razón que no es
mérito suyo: evalúan veinte mil individuos frente a mil. Con presupuesto igualado no está
medido, y lo que el banco pide es que se compare así.

**Queda para David: avisar a Paco de la errata del pseudocódigo**, que es su diseño.

Tests: `test_f27_aislar_con_certeza_deja_solo_al_mejor` —con `p_isolation = 1` y
distanciamiento desde la primera iteración solo queda el mejor de la cepa; con el código
anterior la misma configuración dejaba **1971** infectados— y
`test_f27_sin_aislamiento_la_pandemia_crece`.

### [x] F-28 · Tres parámetros por defecto de CVOA no son los que sugiere el artículo
`src/metagen/metaheuristics/cvoa/common_tools.py:9-21` · descubierto al leer el artículo de CVOA

El artículo dedica una sección entera, *Suggested parameters setup*, a fijar los
valores, y presenta como ventaja n.º 1 que «los parámetros de entrada ya están
fijados según las estadísticas de la enfermedad, evitando que el investigador los
inicialice con valores arbitrarios». Siete de los diez coinciden; tres no:

| Parámetro | Artículo | MetaGen |
|---|---|---|
| `p_re_infection` | 0.02 | **0.001** (20 veces menor) |
| `p_isolation` | ≥ 0.7 | **0.5** (y ver `F-27`) |
| `pandemic_duration` | 30 | **10** |

`pandemic_duration=10` con `social_distancing=7` deja solo **tres** iteraciones con
medidas de distanciamiento; en el artículo son 22 de 30. Esa es la fase en que la
pandemia decrece, así que con los valores de MetaGen no llega a ocurrir.

**Arreglo** Alinear los tres valores con la sección *Suggested parameters setup*, o
documentar por qué se apartan. Entrelazado con `F-27`: mientras `p_isolation` signifique
lo contrario, subirlo a 0.7 empeora las cosas en vez de mejorarlas.

Se ataca en la sesión dedicada a CVOA, después de `F-27`: ver
`metagen-auditoria/CVOA-cuestiones.md`.

*Cerrado el 10 de septiembre de 2026 con los tres valores del artículo, decisión de
David.* `pandemic_duration` 30, `p_isolation` 0.7 y `p_re_infection` 0.02; los otros
siete ya coincidían. **Las docstrings de los dos gemelos discrepaban del código en cuatro
valores** —decían `p_isolation` 0.7, `p_re_infection` 0.0014, `social_distancing` 10 y
`spreading_rate` 6 donde el código traía 0.5, 0.001, 7 y 5—, lo que apunta a que los
defaults del código eran restos de otra variante, o de acortar las pruebas cuando la cepa
moría enseguida por `F-23`. Ahora las docstrings dicen lo que hace el código.

Medido antes y después, una cepa, `seed=0`, ya con `F-27` y `F-29` cerrados:

**Dominio binario de 10 bits, el del artículo.** Infectados por iteración y mejor fitness
(OneMax, óptimo 0):

| defaults | curva | fitness | tiempo |
|---|---|---|---|
| MetaGen (0.5, 10, 0.001) | 8, 11, 19, 27, 39, 43, 42, 21, 14, 10, 2 — se corta a las 10 | **1** | 0.2 s |
| **artículo (0.7, 30, 0.02)** | 8, 11, 19, 27, 41, 54, **73**, 19, 9, 8, 2 … 3, 4 | **0** | 0.3 s |

Con los del artículo la pandemia sube, pica hacia la séptima iteración, cae y se queda
latente con la reinfección, que es la curva de la Figura 2, y **alcanza el óptimo**; con
los de MetaGen se corta antes de llegar.

**Dominio continuo 2D, y aquí hay que decir lo que no arregla.**

| defaults | curva | fitness | tiempo |
|---|---|---|---|
| MetaGen | 14, 57, 193, 669, 2123, 7077, 23 623, 39 002, 64 361, 105 682, **174 516** | 2.65e-05 | 94 s |
| artículo | 14, 57, 193, 669, 2123, 7077, 23 623, 23 434, 23 235 … **17 146** a las 30 | 2.65e-05 | 183 s |

Las siete iteraciones sin distanciamiento son las mismas en los dos casos y ya dejan
23 000 infectados; con `p_isolation` 0.7 la población **decrece, pero un 2 % por
iteración**, y treinta iteraciones cuestan tres minutos. Es el algoritmo sobre un dominio
donde cada infectado es un individuo nuevo: en 10 bits, los recuperados y los muertos
saturan el espacio y frenan solos la pandemia; en un continuo no hay nada que la frene
hasta el distanciamiento. **El artículo es binario, y sus parámetros están pensados para
eso.** Queda como observación de diseño en el documento de CVOA, punto 3.7, no como
hallazgo: no hay un defecto que corregir, sino un algoritmo cuyo coste en dominios
continuos depende de `social_distancing` y del `spreading_rate` mucho más que de
`p_isolation`.

Ningún test ejecuta una pandemia con la duración por defecto; los que construyen cepas
fijan `pandemic_duration` a 4, y la suite no se mueve.

Test: `test_f28_los_valores_por_defecto_son_los_del_articulo`, que compara los diez
contra la tabla del artículo.

### [x] F-29 (R) · CVOA no reproduce entre procesos: itera conjuntos de soluciones
`src/metagen/metaheuristics/cvoa/cvoa_local.py:178` y su gemelo · descubierto al cerrar `F-15`

`for individual in self.infected:` recorre un `Set[Solution]`. El orden de iteración de
un conjunto sigue a los hashes de sus elementos, y como cada individuo consume sorteos al
contagiar, **el orden decide el resultado**. Es el mismo mecanismo que `F-26`, por otro
canal: allí era un conjunto de nombres de variable, aquí uno de soluciones.

Medido con la misma semilla (`seed=0`) y variando solo el proceso:

| | Mismo `PYTHONHASHSEED` | Distinto `PYTHONHASHSEED` |
|---|---|---|
| Antes de `F-15` | **no reproduce** | no reproduce |
| Después de `F-15` | reproduce | **no reproduce** |

Con el hash viejo eran **5 valores distintos en 6 procesos**, y ni siquiera dependían de
`PYTHONHASHSEED`: el hash era `hash((None, fitness))`, y `hash(None)` sale de la
dirección de memoria, que cambia en cada arranque por el ASLR. **Era una aleatoriedad
que no se podía fijar de ninguna manera.**

Tras `F-15` el hash depende de los nombres de variable, que son cadenas: Python
aleatoriza su hash en cada arranque (PEP 456), pero eso **sí** se fija con
`PYTHONHASHSEED`. O sea, `F-15` convierte una aleatoriedad incontrolable en una
controlable, sin llegar a eliminarla.

**Arreglo** Recorrer los conjuntos en un orden determinista dentro de CVOA —una lista, o
`sorted(...)` por una clave estable— en vez de depender del orden del `set`. Afecta a los
dos gemelos.

**Se ataca en la sesión dedicada a CVOA**, no aquí: ver
`metagen-auditoria/CVOA-cuestiones.md`. Nótese que **invalida cualquier medición de CVOA
tomada hasta ahora**, incluidas las de `F-23` y `F-10` de este documento, que se hicieron
en procesos distintos.

*Cerrado el 10 de septiembre de 2026, primer paso de la sesión de CVOA.* Reproducido
antes de tocar nada, una cepa, `seed=0`, `pandemic_duration=6`, `social_distancing=2`:

```
PYTHONHASHSEED=0  fitness=0.0014786023  infectados por iteracion=[14, 45, 110, 159, 255, 445, 731]
PYTHONHASHSEED=0  fitness=0.0014786023  (repetido: identico)
PYTHONHASHSEED=1  fitness=0.0192076125  infectados por iteracion=[14, 56, 104, 156, 268, 471, 787]
PYTHONHASHSEED=2  fitness=0.0096488992  infectados por iteracion=[14, 50, 112, 159, 274, 475, 808]
```

**La forma del arreglo es un conjunto con orden de inserción, no un `sorted`.** Ordenar
exige una clave total sobre soluciones, y el fitness empata —en codificación discreta,
constantemente— mientras que las variables son de tipos mixtos. Un conjunto respaldado
por un `dict`, `SolutionSet` en `common_tools.py`, conserva la deduplicación que el
artículo recomienda y recorre en el orden en que se añadió cada individuo, que solo
depende de los sorteos. Sustituye a `Set[Solution]` en los dos gemelos, en los dos
estados compartidos y en las herramientas distribuidas: todos los conjuntos de
soluciones de CVOA, no solo los que se recorren hoy.

Después, los tres `PYTHONHASHSEED` dan lo mismo, `fitness=0.0051186325` y
`[14, 57, 111, 156, 253, 446, 748]`. **Es otro valor que cualquiera de los de antes**,
como tenía que ser: el orden de recorrido cambia y con él la pandemia. Desde aquí las
mediciones de CVOA sí son comparables entre sí, y las anteriores no lo son con estas.

El gemelo distribuido corre sobre Ray con el conjunto nuevo. **Lo que sigue sin fijarse
es el entrelazado de varias cepas**, que es hilos y no conjuntos: residuo de `A-06`,
punto 3.6 del documento de CVOA. La garantía es para una cepa.

Test: `test_f29_cvoa_reproduce_entre_procesos`, en dos subprocesos con `PYTHONHASHSEED`
0 y 1; comprobado que falla con el código anterior, con `0.1634` frente a `0.3129`.

### [x] F-30 (R) · La temperatura de SA no llega a enfriarse: es un paseo aleatorio
`src/metagen/metaheuristics/sa/sa.py:92-93` · descubierto al cerrar `F-20`

Los valores por defecto son `initial_temp=50.0`, `cooling_rate=0.99` y
`max_iterations=20`. Con ellos la temperatura **no baja lo suficiente para que el
criterio de Metropolis discrimine nada**:

```
  15 iteraciones -> T = 43.00
  20 iteraciones -> T = 40.90
 100 iteraciones -> T = 18.30
```

Y a esas temperaturas se acepta casi cualquier empeoramiento:

| T | Empeoramiento | Se acepta con probabilidad |
|---|---|---|
| 50 | 1.0 | 0.980 |
| 43 | 1.0 | 0.977 |
| 43 | **5.0** | **0.890** |
| 1.0 | 1.0 | 0.368 |
| 0.1 | 1.0 | 0.000 |

**Con los valores por defecto, SA acepta casi todo lo que genera.** Eso no es recocido
simulado: es un paseo aleatorio con pasos de tamaño `alteration_limit`. Llegar a `T=0.1`
con `cooling_rate=0.99` exige unas **618 iteraciones**, treinta veces el
`max_iterations` por defecto.

Es la causa que queda de que SA no mejore sobre su propio inicio (3/10) ni gane al azar
(5/10) tras cerrar `F-03` y `F-20`.

**Arreglo** Ligar el enfriamiento al presupuesto en vez de fijar una tasa suelta: por
ejemplo, derivar `cooling_rate` de `initial_temp`, `T_min` y `max_iterations` de modo
que la temperatura recorra su rango completo en las iteraciones disponibles. Alternativa
más conservadora: dejar los tres parámetros como están pero documentar la relación y
avisar cuando no cuadren.

**Nota:** el `initial_temp` adecuado depende de la escala del fitness del problema, que
el framework no conoce. Una temperatura absoluta por defecto es discutible para
cualquier problema; puede tener más sentido una relativa a la dispersión observada en
el warmup. Es decisión de algoritmia, no de auditoría.

*Cerrado con la primera opción, ligar el enfriamiento al presupuesto.* `cooling_rate`
pasa a ser `Optional[float] = None`, y cuando no se da se deriva de modo que la
temperatura recorra su rango entero en las iteraciones disponibles:

```python
self.cooling_rate = (self.T_min / self.initial_temp) ** (1 / max(1, self.max_iterations))
```

Quien pase su propia tasa sigue mandando, así que nada escrito antes cambia de
comportamiento.

**El diagnóstico se queda corto: hay una segunda mitad que es peor que la primera.**
Que la temperatura no baje es solo la mitad. Medido sobre las nueve funciones, con la
misma `T=43` en todas:

| función | \|Δ\| medio | P(aceptar un empeoramiento) |
|---|---|---|
| Michalewicz | 0.20 | **0.9958** |
| Ackley | 0.92 | 0.9810 |
| Sphere | 5.28 | 0.8973 |
| Rosenbrock | 133.4 | 0.3423 |
| **Schwefel** | 334.4 | **0.0877** |

`initial_temp=50` es **absoluto** frente a un fitness cuya escala fija el problema, así
que con la misma configuración SA va de **paseo aleatorio puro** en Michalewicz a **hill
climbing codicioso** en Schwefel, y el usuario no tiene forma de saber cuál le toca. Es
la misma enfermedad que `F-32`, en el eje de la temperatura.

**La nota que este hallazgo dejaba fuera de la auditoría —derivar `initial_temp` de la
dispersión del warmup— se probó y NO sale a cuenta.** Es la opción por la que yo
apostaba. Con inicialización por tasa de aceptación (`T₀` para aceptar un
empeoramiento típico con probabilidad 0.8, `T_min` con 0.01), 30 semillas:

| variante | gana al azar | mejora sobre su inicio | evals |
|---|---|---|---|
| antes | 134/270 | 168/270 | 21 |
| **tasa desde el presupuesto** | **161/270** | **195/270** | 21 |
| tasa + temperatura del warmup | 138/270 | **161/270** | 21 |

Empeora «mejora sobre su inicio», que es la propiedad que delata si el algoritmo aporta
algo sobre su punto de partida. El motivo está en la trayectoria: con la tasa derivada
la temperatura cae a `0.57` en tres iteraciones y SA pasa el **80 % del presupuesto
escalando**; con la del warmup se queda en el mismo orden de magnitud toda la ejecución
—a mitad de camino aún acepta el 71 % de los empeoramientos— y deambula. Con 15
iteraciones, escalar gana. **La escala del fitness sigue siendo un problema abierto de
diseño; lo que queda descartado es esta forma concreta de resolverlo.**

**Segundo bug, del mismo hallazgo y sin diagnosticar:** `current_temp` solo se fijaba en
el constructor, así que un segundo `run()` continuaba donde lo dejó el primero —50 → 43
→ 36.99—. No se notaba mientras el enfriamiento apenas se movía; con una temperatura que
llega al suelo **rompe la garantía de `A-06`** de que una semilla reproduce una
ejecución. Se reinicia en `pre_execution()`.

**Lo que sigue faltándole a SA no es de este hallazgo.** Con la tasa arreglada queda en
161/270, todavía por debajo del muestreo aleatorio. El que pesa el doble es
`neighbor_population_size=1`, la nota que dejó abierta `F-25`: con un solo vecino no hay
entre qué elegir. Medido, sube a **214/270**.

*Aplicado en el commit siguiente*, decisión de David: el valor por defecto pasa de 1 a
**5**. Con las dos cosas, SA pasa de **31/90 a 71/90** en la tabla de `P-05` y **deja de
ser el peor del paquete para ser el tercero**, por delante de TPE. **Mejora sobre su
propio inicio en las nueve funciones**, que es la propiedad que llevaba toda la
auditoría delatándolo. Diez `xfail` se retiran de golpe.

**El precio hay que decirlo: el presupuesto de SA pasa de 21 evaluaciones a 81.** No es
gratis, y quien tenga una función de fitness cara lo va a notar; se compara siempre
contra el azar con ese mismo presupuesto, así que la mejora no viene de gastar más.
Las cuatro funciones que sigue sin ganar son las más duras del conjunto para un solo
punto que camina: Rastrigin, Rosenbrock, Schwefel y Michalewicz.

Un `xfail` se retira (`Zakharov-SA`, mejora sobre su inicio) y se añade otro
(`Rastrigin-SA`, gana al azar): es una celda al borde que baja de 7 a 5 mientras el
agregado sube 27 puntos sobre 270.

Tests: `test_f30_la_temperatura_recorre_su_rango_en_las_iteraciones_disponibles`,
`test_f30_una_tasa_de_enfriamiento_dada_a_mano_se_respeta` y
`test_f30_cada_run_arranca_a_la_misma_temperatura`.

### [x] F-31 (R) · Los genéticos no admiten estructuras dinámicas: el cruce no está implementado
`src/metagen/metaheuristics/ga/ga_tools.py:62` y `:160` · descubierto al plantear `A-07`

Con `GAConnector`, **ni siquiera se puede declarar** una estructura dinámica. Falla al
definir el dominio, antes de lanzar nada:

```python
Domain(connector=GAConnector()).define_dynamic_structure("v", 2, 4)
#   -> ValueError: (GAStructure, 'dynamic') has not been registered in the connector

Domain().define_dynamic_structure("v", 2, 4)
#   -> ok
```

`GAConnector` es el único de los tres que no registra la variante dinámica:

| Conector | Estáticas | Dinámicas |
|---|---|---|
| `BaseConnector` | sí | sí |
| `TPEConnector` | sí | sí |
| **`GAConnector`** | sí | **no** |

**Pero no es un registro que falte por descuido.** `GAStructure.crossover` tiene la rama
dinámica escrita así:

```python
if isinstance(self.get_definition(), DynamicStructureDefinition):
    raise NotImplementedError()
```

y su docstring lo documenta (`:raises NotImplementedError:`). Es decir, la ausencia del
registro es **coherente** con que el operador de cruce no exista para longitudes
variables. Añadir la línea del registro cambiaría un `ValueError` al definir el dominio
por un `NotImplementedError` en mitad de la primera generación: peor, no mejor.

Afecta a **GA, SSGA y el memético**, los tres que usan `GAConnector`. Las estructuras de
longitud variable son una de las capacidades que el framework destaca, así que la
combinación «genético + estructura dinámica» simplemente no existe hoy.

**Arreglo** No es un arreglo de auditoría sino una funcionalidad a implementar:
un operador de cruce para estructuras de longitud variable —cruce en un punto sobre la
longitud mínima y decisión sobre la cola sobrante, o cruce que también recombine las
longitudes— y después registrar la variante dinámica en `GAConnector`. **David quiere
hacerlo más adelante** (7 de septiembre de 2026).

Mientras tanto, lo que sí cabe en la auditoría es que el fallo se explique: hoy son un
`ValueError` sobre el conector y un `NotImplementedError` sin mensaje, y ninguno de los
dos dice «los genéticos no admiten estructuras dinámicas todavía». Ver `A-07`.

*Cerrado el 9 de septiembre de 2026, como funcionalidad y con el operador elegido por
medición.* `GAConnector` registra la variante dinámica y `GAStructure.crossover` deja de
lanzar `NotImplementedError`. La pregunta de diseño era **qué recombina el cruce donde
las longitudes difieren**, y se implementaron los dos candidatos para medirlos:

- **Prefijo común y colas intercambiadas**: sobre `min(len1, len2)` la regla de `F-33`,
  y cada hijo se lleva la cola de un padre al azar. Longitudes siempre válidas, pero
  **el cruce nunca crea una longitud nueva**.
- **Corte y empalme** (Goldberg): cada padre se corta por un punto propio y se cruzan
  las mitades, `hijo1 = p1[:c1] + p2[c2:]`. Los cortes se sortean solo entre los pares
  que dan a los dos hijos una longitud válida **y en la rejilla del paso**; si no hay
  ninguno, se cae al primero. Sobre la región común, la regla de `F-33`.

**Hacía falta un problema con estructura dinámica para medirlo**, porque el banco no
tenía ninguno: entra el **ajuste polinómico de grado variable** —una estructura de
reales como coeficientes, de 1 a 8, contra un cúbico objetivo en 21 puntos más 0.001
por término—, que tiene una longitud correcta (4) y unos valores correctos que
encontrar. Aritmética pura, así que `reproducible=True`. Es el undécimo problema.

30 semillas, presupuesto igualado:

| operador | GA | SSGA | Memetic |
|---|---|---|---|
| prefijo + colas | 19/30, media 0.194, **len 2.5** | 20/30, 0.430, len 3.1 | 28/30, 0.033, len 4.4 |
| **corte y empalme** | **24/30**, 0.145, **len 3.6** | 21/30, 0.316, len 3.0 | 28/30, 0.045, len 4.6 |

**Gana corte y empalme, y donde se ve es en la columna de la longitud**: con el operador
que no crea longitudes el GA se queda en 2.5 de media, lejos del 4 correcto, porque solo
la mutación puede alargarlo; con corte y empalme llega a 3.6. **Es la lección de `F-33`
otra vez, para las longitudes en vez de para los valores.** El memético empata en
victorias y pierde algo de media: su búsqueda local ya recombina por su cuenta. Prefijo
y colas se conserva **como reserva** de corte y empalme para cuando ningún par de cortes
da longitudes válidas, que es su uso real; su docstring recoge la medición.

Los hijos se construyen enteros con `set(elementos)`, porque un hijo dinámico nace con
longitud aleatoria y escribir en él posición a posición se saldría del final. Y nacen
válidos **por construcción**, que hace falta: `Structure.set` no valida la longitud y
`check_length` ignora el paso.

Tabla del problema nuevo, diez semillas:

| | evals | gana al azar | mejora | media | len |
|---|---|---|---|---|---|
| RandomSearch | 145 | 6/10 | 9/10 | 0.199 | 2.4 |
| SA | 81 | 5/10 | 10/10 | 0.253 | 5.7 |
| HillClimbing | 177 | **9/10** | 10/10 | 0.055 | 3.7 |
| GA | 160 | **8/10** | 10/10 | 0.146 | 3.3 |
| SSGA | 40 | 5/10 | 9/10 | 0.390 | 3.4 |
| TPE | — | revienta | | | (`F-35`) |
| **Memetic** | 610 | **9/10** | 10/10 | 0.054 | 4.6 |

Dos `xfail` nuevos, SA y SSGA en «gana al azar», con motivo medido; los siete pasan las
dos propiedades estructurales, salvo TPE, que **revienta** y salió como `F-35`. Para
eso el arnés aprendió a **registrar que un par revienta** en vez de tirar el módulo
entero: la excepción se guarda y las cuatro propiedades del par fallan sobre ella bajo
un `xfail` que cita el hallazgo.

**Ninguna cifra del resto del banco se movió**, aunque el cruce estático se
refactorizó por el camino —`_recombine_prefix` es ahora común a los dos casos—: el
orden de los sorteos se conservó a propósito.

Tests: `test_f31_los_geneticos_admiten_una_estructura_dinamica` y
`test_f31_el_cruce_de_longitud_variable_crea_longitudes_nuevas_y_validas`; los dos
fallan con el código anterior, que no dejaba ni definir el dominio.

### [x] F-32 (R) · El `alteration_limit` por defecto es absoluto, no relativo al dominio
`hc/hill_climbing.py:50`, `mm/memetic.py:72`, `sa/sa.py:92` · descubierto al ampliar el banco de pruebas

Los tres algoritmos con búsqueda local traen `alteration_limit=1.0` por defecto, un
valor **absoluto**. Cuánto significa depende por completo de lo ancho que sea el dominio
del problema, que el framework conoce y no mira.

Medido con presupuesto igualado sobre las seis funciones clásicas del campo, con sus
dominios canónicos: **cuántas de 10 semillas gana cada algoritmo al muestreo aleatorio.**

| | Sphere | Rastrigin | Rosenbrock | Ackley | Griewank | Schwefel |
|---|---|---|---|---|---|---|
| *anchura del dominio* | *±5.12* | *±5.12* | *±2.05* | *±32.8* | *±600* | *±500* |
| RandomSearch | 8 | 5 | 3 | 8 | 7 | 6 |
| SA | 4 | 3 | 5 | 3 | 3 | 2 |
| **HillClimbing** | **10** | **10** | 7 | **10** | **3** | **4** |
| GA | 4 | 5 | 1 | 4 | 4 | 4 |
| SSGA | 3 | 5 | 2 | 2 | 2 | 5 |
| TPE | **10** | 6 | 6 | **10** | **8** | 5 |
| **Memetic** | **10** | **10** | **10** | 8 | **2** | 4 |

`HillClimbing` y el memético son imbatibles en las cuatro primeras y **caen por debajo
del azar en las dos últimas**. El patrón **no es multimodal contra unimodal**: Rastrigin
y Ackley también son multimodales y ahí arrasan. Lo que las separa es **la anchura del
dominio**: en Griewank (`±600`) un vecino se mueve como mucho un **0.1 % del rango**, así
que la búsqueda local no llega a ninguna parte.

**TPE es el más robusto del conjunto**, un dato que con la esfera sola no se veía:
allí `HillClimbing` parecía dominar.

**Arreglo** Hacer que el límite por defecto sea **relativo**: derivarlo de la anchura del
dominio —por ejemplo una fracción del rango de cada variable— en vez de fijar un 1.0 que
solo tiene sentido para dominios de unas pocas unidades. Alternativa conservadora:
dejarlo como está y avisar en la documentación de que hay que ajustarlo al problema,
que es peor porque el framework sí conoce el dominio.

**Ojo:** cambiar el valor por defecto **mueve los resultados de tres algoritmos**, así
que debería hacerse midiendo antes y después sobre las nueve funciones, no a ojo.

*Cerrado con la primera opción: el límite por defecto pasa a ser relativo.* Y el
diagnóstico se queda corto en algo que decidió el diseño: **`alteration_limit` es un
solo número que `Solution.mutate` reparte a todas las variables**, así que derivarlo del
dominio en los tres algoritmos —que era lo más contenido— arregla el banco de pruebas,
que es homogéneo, y deja roto el caso de uso que vende el paquete. Medido sobre un
dominio de hiperparámetros con el 1.0 de entonces:

```
learning_rate  rango    1    salto maximo   0.4997  =  49.97 % de su rango
n_estimators   rango  999    salto maximo        1  =   0.10 % de su rango
```

En la misma llamada, una variable se resortea entera y la otra está congelada. **Ningún
número único puede arreglar eso.**

Va una clase, `metagen.framework.RelativeAlteration`, que expresa el vecindario como
**fracción del rango de cada variable**, y son `Real.mutate` e `Integer.mutate` quienes
la resuelven contra su propia definición. **Un número sigue significando un límite
absoluto y `None` sigue siendo el dominio entero**, así que nada escrito contra el
comportamiento anterior cambia; lo único que cambia es el valor por defecto de
`HillClimbing`, `Memetic` y `SA`, que pasa de `1.0` a `RelativeAlteration(0.2)`.

**La fracción se eligió midiendo, y el proceso importa más que el número.** Cuántas de
10 semillas gana cada algoritmo al azar, sumando las nueve funciones:

| | 1.0 (antes) | 10 % | 15 % | 20 % | 35 % | 50 % | 100 % |
|---|---|---|---|---|---|---|---|
| HillClimbing | 70 | 79 | 75 | **79** | 73 | 71 | 73 |
| Memetic | 75 | 83 | **88** | 86 | 85 | 78 | 73 |

**Hay punto de inflexión**, que era la comprobación que había que hacer: si «cuanto más
grande, mejor» se hubiera cumplido, el arreglo no sería un vecindario relativo sino
renunciar a la búsqueda local. Entre el 10 % y el 20 % **la diferencia es ruido**:
el memético en Rosenbrock parecía caer de 9/10 a 5/10 con el 10 %, y con **30** semillas
resulta ser 22/30 frente a 18/30 con la misma media (0.0476 y 0.0458). Se eligió el
20 % por los agregados —204/270 y 228/270 en las dos propiedades, frente a 199 y 218 del
10 %— y porque deja la suite más limpia: una celda nueva marcada como fallo esperado en
vez de cuatro.

**El argumento de «el 10 % conserva el comportamiento actual» no se sostenía**, y hubo
que retirarlo: el `1.0` de antes vale entre el **0.083 %** del rango en Griewank y el
**32 %** en Michalewicz. No hay fracción que reproduzca lo de hoy en todas partes.

Resultado, presupuesto igualado, diez semillas, las nueve funciones:

| | Sph | Ras | Ros | Ack | Gri | Sch | Levy | Mich | Zak | total |
|---|---|---|---|---|---|---|---|---|---|---|
| HillClimbing, antes | 10 | 10 | 7 | 10 | 3 | 4 | 10 | 6 | 10 | 70/90 |
| **HillClimbing, ahora** | 10 | 10 | 8 | 10 | **9** | **6** | 9 | **7** | 10 | **79/90** |
| Memetic, antes | 10 | 10 | 9 | 10 | 6 | 2 | 10 | 8 | 10 | 75/90 |
| **Memetic, ahora** | 10 | 10 | 9 | 10 | **9** | **10** | 10 | 8 | 10 | **86/90** |

El memético pasa a ser el mejor o a empatar **en las nueve**. SA sube de 31/90 a 39/90 y
**sigue por debajo del muestreo aleatorio**, que empata consigo mismo en 50/90: ahí manda
`F-30` y este arreglo no lo toca.

Se retiran **seis** `xfail` —Griewank y Michalewicz de `HillClimbing`, Griewank y
Schwefel del memético, Rastrigin y Schwefel de SA— y se añade uno, `Michalewicz-SA`,
citando `F-30` junto a los seis que ese hallazgo ya tenía.

**Las docstrings decían que era una proporción**, literalmente *«Maximum proportion of
solution to alter»* en los tres algoritmos, y era falso. Corregidas. La documentación
publicada además lo declara con otro valor: `docs/source/metagen_in_action/duc/sa.rst`
usa `alteration_limit: float = 0.1` mientras el paquete traía `1.0`. Es un tutorial de
«escribe tu propia metaheurística», no la API, así que se deja como está.

Cierra dos errores de mypy, que baja de 170 a 168: las anotaciones eran demasiado
estrechas.

Tests: `test_f32_el_vecindario_por_defecto_escala_con_el_dominio`,
`test_f32_cada_variable_resuelve_el_limite_con_su_propio_rango` y
`test_f32_un_numero_sigue_significando_un_limite_absoluto`, este último para proteger lo
que **no** debe cambiar.

### [x] F-33 (R) · El cruce es uniforme: sobre variables reales no crea ningún valor nuevo
`src/metagen/metaheuristics/ga/ga_tools.py:112-127` · descubierto al medir `A-01`

`GASolution.crossover` reparte variables enteras entre los hijos, y cada rama del bucle
**copia el valor de uno de los dos padres**:

```python
child1.set(variable_name, copy(other.get(variable_name)))   # valor del padre 2
child2.set(variable_name, copy(self.get(variable_name)))    # valor del padre 1
```

Eso es cruce **uniforme**, el operador natural de una codificación discreta. Sobre
variables reales significa que el cruce **solo baraja coordenadas que ya existían**: la
descendencia vive siempre en la rejilla que forman los valores de la población inicial,
y todo valor nuevo tiene que venir de la mutación, que dispara con probabilidad 0.1.

Medido sobre la esfera, 15 generaciones de 10 individuos:

```
valores de x en la poblacion inicial:        10
valores de x vistos en las 15 generaciones:  19   (9 nuevos, todos de mutaciones)
```

**Con una sola variable el cruce degenera en devolver los padres.** La guarda
`if len(basic_variables) > 1` deja `variables_to_exchange = []`, así que `hijo1 = padre1`
e `hijo2 = padre2`, las 200 veces de 200 que se probó. No es un error del código —con una
variable ningún operador de cruce puede inventar nada, e intercambiarla daría los padres
otra vez— pero **el ejemplo de la docstring del memético usa exactamente un dominio de
una variable**, así que lo publicado enseña un genético cuyo cruce no hace nada.

Es la causa que queda de que el GA no llegue al umbral en seis de las nueve funciones
después de cerrar `A-01`, y la razón de fondo de que al memético le rentara tanto
intensificar: si el cruce no aporta material nuevo, la búsqueda local es su única fuente
de novedad.

**Arreglo** No es un bug sino un operador que no encaja con el tipo de variable, así que
es funcionalidad: registrar para `RealDefinition` un cruce de codificación real —BLX-α,
SBX o aritmético, que **interpolan** entre los padres y sí producen coordenadas nuevas—
dejando el uniforme para enteras, categóricas y estructuras. Encaja con el mecanismo del
conector, que ya elige el tipo por definición. **Debe medirse antes y después sobre las
nueve funciones**, como `F-32`, porque mueve los resultados de los tres genéticos.

*Cerrado con BLX-α y α = 0.5, y con más alcance del que propone el arreglo.* `GAReal` y
`GAInteger` se registran en `GAConnector` junto a `GAStructure`, y `GASolution.crossover`
pasa a **preguntar por la capacidad en vez de por el builtin**: quien sabe cruzarse se
cruza, quien no —la categórica— se intercambia como antes. El mecanismo es el conector,
así que quien prefiera SBX registra su propia clase.

**Los enteros entran, aunque el hallazgo solo cite los reales.** Tienen el mismo problema
y pesan en el caso de uso que vende el paquete, lleno de `n_estimators` y `max_depth`. No
se puede medir con el banco actual, que es todo real; va sostenido por el argumento.

**La primera propuesta fue repartir los dos niveles**, idea de David: unas variables
heredadas de un padre —conserva combinaciones— y otras mezcladas —aporta valores nuevos—.
El razonamiento es bueno y la medición lo tumbó. En el banco de dos variables da 575/810
frente a 581 de mezclarlo todo, pero ese banco no puede juzgarlo: con dos variables no
hay combinaciones que conservar. Repetido **en diez variables**, incluida una Zakharov
que las acopla y es el mejor caso posible para el argumento:

| reparto | Sphere-10 | Rastrigin-10 | Zakharov-10 | total |
|---|---|---|---|---|
| todo heredado | 30/30 | 28/30 | 16/30 | 74/90 |
| mezcla 50 % | 30/30 | 30/30 | 28/30 | 88/90 |
| **todo mezclado** | 30/30 | 30/30 | **30/30** | **90/90** |

**La premisa que yo había trasladado era mala:** BLX no destruye la combinación de los
padres, la **muestrea alrededor**, porque el intervalo está centrado en sus dos valores.
El bloque no se pierde, se perturba. Y hay un motivo formal para no hacer las dos cosas
sobre la misma variable: **BLX es simétrico**, así que si se mezcla, intercambiar deja de
significar nada.

**α = 0.5 es el valor del artículo original de Eshelman y Schaffer.** Medido sobre las
nueve funciones y 30 semillas, 0.25, 0.5 y 0.75 son indistinguibles —576, 576 y 590 sobre
810—, así que se elige el de la literatura por no tener que defender un número propio.

**Las estructuras delegan en sus elementos**, misma regla que un nivel más arriba: un
vector de reales se mezcla componente a componente, que es como BLX está definido para un
vector. **Esto no se puede medir con el banco actual**, que no tiene ninguna estructura, y
así consta.

Resultado sobre las nueve funciones, presupuesto igualado:

| | Sph | Ras | Ros | Ack | Gri | Sch | Levy | Mich | Zak | total |
|---|---|---|---|---|---|---|---|---|---|---|
| GA, antes | 7 | 4 | 3 | 7 | 4 | 4 | 7 | 4 | 0 | 40/90 |
| **GA, ahora** | **9** | **7** | 5 | **9** | **7** | **6** | 7 | **7** | **5** | **62/90** |
| SSGA, antes | 3 | 5 | 5 | 3 | 3 | 6 | 6 | 5 | 2 | 38/90 |
| **SSGA, ahora** | **5** | **8** | 6 | **6** | **6** | 4 | 6 | **7** | 3 | **51/90** |
| Memetic, antes | 10 | 10 | 9 | 10 | 9 | 10 | 10 | 8 | 10 | 86/90 |
| **Memetic, ahora** | 10 | 10 | 9 | 10 | 9 | 9 | 10 | **10** | 10 | **87/90** |

**Con esto los siete algoritmos alcanzan o superan al muestreo aleatorio**, que empata
consigo mismo en 50/90. Once `xfail` se retiran, y en «mejora sobre su inicio» **solo
queda TPE**: los otros seis mejoran sobre su punto de partida en las nueve funciones.

**Hubo que reformular un test de regresión de un hallazgo cerrado**, `F-04`, con permiso
de David. Comprobaba que alguna variable del hijo 2 valiera *exactamente* lo que vale en
la madre, que era como el cruce uniforme trasladaba la herencia: copiando. Con BLX el
valor se sortea del intervalo de los dos padres, lleva información de ambos y no coincide
con ninguno, así que el test daba un falso positivo. Ahora comprueba la propiedad —el
hijo 2 no es copia del padre, cambia si cambia la madre, y sus valores caen dentro del
intervalo— y **se verificó reintroduciendo el bug de `F-04`**: dos de las tres aserciones
fallan con él.

Cierra un error de mypy, que baja de 168 a **167**. Los `cast` de `GAReal` y `GAInteger`
son deliberados: `BaseType.get_definition()` está declarado como la unión entera de
definiciones, que es deuda de `P-11`.

**Queda algo vivo, sin medir:** dentro de una `GAStructure` los elementos ya se mezclan,
pero un vector de **categóricas** sigue solo barajando posiciones, que es lo correcto para
ese tipo. Y el `randint(1, len - 1)` que excluía intercambiar *todas* las variables ahora
solo se aplica cuando ninguna se mezcla, porque su premisa —que intercambiarlas todas
devuelve a los padres— deja de valer en cuanto algo se mezcla.

Tests: `test_f33_el_cruce_produce_valores_que_no_tenia_ningun_padre`,
`test_f33_la_categorica_se_sigue_intercambiando_entera` y
`test_f33_el_cruce_no_se_sale_del_dominio`.

### [x] F-34 (R) · `BaseConnector.get_builtin` falla con cualquier estructura
`src/metagen/framework/connector/connector.py:158-180` · descubierto al tipar el conector para `P-11`

El registro guarda las estructuras con un discriminador, porque un `list` mapea a la
definición estática **y** a la dinámica:

```python
self.register(definitions.DynamicStructureDefinition, (types.Structure, 'dynamic'), list)
self.register(definitions.StaticStructureDefinition,  (types.Structure, 'static'),  list)
```

Pero `get_builtin`, cuando recibe una **instancia**, construye la clave con la clase
pelada, `type(solution_type)`, que no está en el registro:

```
get_builtin(una estructura)            -> ValueError
get_builtin((una estructura, 'static')) -> list
```

`get_type` y `get_definition` no tienen el problema: la primera entra por la definición,
que sí distingue estática de dinámica, y la segunda acepta la tupla.

**Reproducido antes de tocar nada**: falla igual en el código anterior a la primera
tanda de `P-11`, así que no es una regresión de ese trabajo. Con los `TypeVar` sin ligar
todo era `Any` y mypy no podía verlo; salió al ponerle tipos de verdad al conector, que
es lo que `P-11` anunciaba.

**Hoy no lo llama nadie en `src/`.** Su único llamante era `GASolution.crossover`, que lo
sorteaba envolviendo la estructura a mano:

```python
if isinstance(variable_value, GAStructure):
    variable_value = (variable_value, "static")     # 'static' fijo, tambien para dinamicas
if self.connector.get_builtin(variable_value) in [int, float, str]:
```

**`F-33` eliminó esa llamada** al sustituir la pregunta por el builtin por la pregunta
por la capacidad (`hasattr(valor, "crossover")`). Así que el bug queda solo en la
superficie pública: `BaseConnector` es el punto de extensión del framework y quien
escriba un conector propio puede toparse con él.

Nótese que el apaño hardcodeaba `'static'` incluso para una estructura dinámica. No
hacía daño porque las dos devuelven `list`, pero era casualidad.

**Arreglo** Que `get_builtin` resuelva el discriminador como hace el registro: si la
clase pelada no está, probar las variantes con discriminador; o, mejor, guardar el
builtin bajo la clase sin discriminador, ya que las dos estructuras devuelven `list` y el
discriminador no aporta nada en ese diccionario concreto. Hay que decidir cuál, y
comprobar que ningún conector propio dependa de la forma actual de las claves.

*Cerrado con la primera opción, arreglando la búsqueda y no el registro.* `register` es
la API de extensión y la forma de sus claves es lo que un conector propio puede haber
imitado, así que no se toca. Cuando la clave pelada no está, `get_builtin` consulta las
entradas registradas bajo un discriminador para esa clase: si todas dan el mismo
builtin, lo devuelve; si dan varios distintos, lanza un `ValueError` que pide la clase
con su discriminador. **No asume los nombres `'static'` y `'dynamic'`**, así que vale
para cualquier conector.

Acepta instancia, clase o tupla, que es lo que ya aceptaba en la práctica y la firma
no decía: declaraba `types.BaseType` a secas.

Comprobado el caso ambiguo registrando a propósito la variante dinámica con `tuple`
como builtin: `get_builtin(Structure)` pasa a lanzar
*«registered under discriminators that map to different builtins, ['list', 'tuple']:
pass the class paired with its discriminator»*, que es lo que debe.

El ejemplo publicado de `docs/advanced_topics/extending_framework.rst`, que usa
`get_builtin` con el patrón antiguo del cruce, deja de tropezar con las estructuras
sin cambiarlo.

Test: `test_f34_get_builtin_acepta_una_estructura`, ampliado a la clase pelada.

### [x] F-35 (R) · TPE registra la estructura dinámica y revienta al usarla
`src/metagen/metaheuristics/tpe/tpe_tools.py:117-121` · descubierto al diseñar `F-31`

`TPEConnector` es el único conector, junto al base, que registra la variante dinámica
(`(TPEStructure, 'dynamic')`). Pero `TPEStructure.resample` da por hecho que todas las
soluciones de referencia miden lo mismo que ella:

```python
for i in range(len(self)):
    self.get(i).resample([val.get(i) for val in best_values], [val.get(i) for val in worst_values])
```

Con una estructura dinámica, las mejores y las peores soluciones tienen longitudes
distintas, y `val.get(i)` sobre una más corta que `self` es un `IndexError`. Reproducido
con un dominio de una sola estructura dinámica de reales, longitud 1 a 6:

```
RandomSearch  con estructura dinamica -> ok
HillClimbing  con estructura dinamica -> ok
SA            con estructura dinamica -> ok
TPE           con estructura dinamica -> IndexError: list index out of range
```

Es decir: **TPE es el único que dice admitirla y el único que no la admite.** Los tres
que no la registran de forma especial la manejan sin problema, porque `Structure.mutate`
ya sabe redimensionar (`F-19`).

**Arreglo** Que `resample` trabaje sobre las posiciones que existen en cada solución de
referencia —filtrar las que sean más cortas, o remuestrear solo hasta la longitud
mínima común—, y decidir aparte cómo se remuestrea la **longitud**, que hoy TPE no
modela en absoluto: una estructura dinámica en TPE conservaría la longitud con la que
nació. Es la misma decisión que `F-31` toma para el cruce.

~~**Queda abierto**, con test en `xfail`, por decisión de David: TPE no se toca de
pasada.~~ Nótese que no es una diferencia de diseño con el TPE canónico, como lo del
trabajo aplazado, sino un fallo que se reproduce con cualquier estructura dinámica.

*Cerrado el 9 de septiembre de 2026 con la primera mitad sola.* `TPEStructure.resample`
remuestrea cada posición **solo con las referencias que la tienen**; una posición a la
que no llega ninguna se queda con el valor con que nació. La longitud no se remuestrea:
la estructura nueva conserva la que le dio `initialize()`, uniforme en su rango.

**La segunda mitad se prototipó y se midió, y no se aplica.** Modelar la longitud con la
propia regla de mezcla de TPE —ajustar dos normales a las longitudes de las mejores y las
peores referencias, como hace `sample_from_values` con un escalar— sobre el problema
polinómico, 20 semillas:

| variante | gana al azar | mejora | media | len |
|---|---|---|---|---|
| solo valores | 16/20 | 15/20 | 0.0809 | 3.8 |
| valores + longitud | 17/20 | 17/20 | 0.0702 | 3.2 |

**Es ruido**, y la segunda obliga a reproducir la regla de muestreo de TPE para un valor
más, que es justo lo que se decidió no tocar. Se queda la primera, y la medición en la
docstring.

Con la corrección, **TPE pasa las cuatro propiedades del banco en el polinómico**
—8/10 contra el azar y 8/10 en mejora sobre su inicio, con diez semillas—, mejor de lo
que hace en el problema de hiperparámetros. El par deja de estar en `_CRASHES`, que
queda vacío pero se conserva: la fixture no debe volver a dejar que un par tire el
módulo. Cinco `xfail` menos —los cuatro del par y el del test de regresión—.

Test: `test_f35_tpe_acepta_una_estructura_dinamica`, ya sin marcador.

### [x] F-36 (R) · `get_definition` del conector falla con una instancia de estructura
`src/metagen/framework/connector/connector.py:126-152` · descubierto al escribir `test/framework/test_connector.py` · test: `test_f36_get_definition_acepta_una_instancia_de_estructura`

Es el hermano de `F-34`, que arregló `get_builtin` y dio por bueno `get_definition`
porque «acepta la tupla». Con la tupla sí; con una **instancia** no:

```
get_definition((Structure, 'static'))   -> StaticStructureDefinition
get_definition(una estructura)          -> ValueError: The object ['7', '4', '10', ...]
                                           has not been registered in the connector.
```

La clave se construye con la clase pelada, `type(instancia)`, que no está en el
registro porque las estructuras se registran con discriminador. Y el mensaje imprime
los **valores** de la estructura en vez de la clave, el mismo detalle que `F-34`
corrigió en el otro método.

**Se diferencia de `F-34` en algo que decide el arreglo.** Allí las dos entradas de
estructura responden `list`, así que consultarlas sin discriminador da una única
respuesta. Aquí responden `StaticStructureDefinition` y `DynamicStructureDefinition`:
dos, y la clase pelada no puede elegir. **La instancia sí puede**: lleva su propia
definición, `instancia.get_definition()`, que es de una de las dos clases.

**Nadie en `src/` lo llama con una instancia** —la fachada pasa siempre clases—, así
que es superficie pública sin llamante interno, como quedó `F-34`.

**Arreglo** Cuando llegue una instancia cuya clase pelada no sea clave, resolver por
la definición que la instancia lleva: entre las entradas registradas con
discriminador para esa clase, la que apunte a `type(instancia.get_definition())`. Y
que el mensaje de error nombre la clave, no el objeto.

*Cerrado el 9 de septiembre de 2026, con el arreglo propuesto y la misma forma que
`F-34`.* `get_definition` acepta instancia, clase o tupla. Si la clave pelada no está,
consulta las entradas discriminadas de esa clase: **con una instancia, responde la que
coincide con `type(instancia.get_definition())`**; con una clase pelada y una sola
entrada, esa; con varias, `ValueError` pidiendo el discriminador o una instancia, que es
la novedad respecto a `get_builtin`, donde todas las entradas daban lo mismo y no hacía
falta elegir. El mensaje de «no registrado» nombra la clave.

```
get_definition(estructura estatica)   -> StaticStructureDefinition
get_definition(estructura dinamica)   -> DynamicStructureDefinition
get_definition(Structure)             -> ValueError: ... registered under discriminators
                                         that map to different definitions ...
```

`register` no se toca, por el mismo motivo que en `F-34`. `test_connector.py` pide ahora
a la instancia de estructura las dos cosas, `get_builtin` y `get_definition`, en los
tres conectores. mypy se queda en 40: `inspect.isclass` no estrecha, y la instancia va
con un `cast` que dice lo que esa comprobación ya garantiza.

Test: `test_f36_get_definition_acepta_una_instancia_de_estructura`, ya sin marcador.

### [x] F-37 (R) · El valor de un grupo o de una estructura no es builtin más allá del primer nivel
`src/metagen/framework/solution/base_solution.py:441` (`__getitem__`), `types/structure.py:164` (`get`) y `:280` (`__getitem__`) · descubierto al escribir `test/framework/test_integration.py` · test: `test_f37_el_valor_de_un_grupo_o_estructura_es_builtin_hasta_el_fondo`

`Solution.__getitem__` promete `:rtype: InputValue` y `Structure.get` «the builtin
value». Solo desenvuelven **un nivel**:

| acceso | tipo que devuelve |
|---|---|
| `solucion["I"]` | `int` |
| `solucion["L"]` | `dict` de **`Integer`, `Real`, `Categorical`** |
| `solucion["SSI"]` | `list` de **`Integer`** |
| `solucion["SSL"]` | `list` de **`Solution`** |
| `solucion.get("SSI").get()` | `list` de **`Integer`** |

Los objetos se comparan iguales a sus builtins y se imprimen igual, por eso no se
nota a simple vista. Se nota en cuanto algo mira el tipo:

- **El propio dominio rechaza lo que su solución devuelve.** `check("L", solucion["L"])`
  y `check("SSI", solucion["SSI"])` dan `False` con valores válidos, porque
  `IntegerDefinition.check_value` pide un entero y recibe un `Integer`.
- `json.dumps(solucion["SSI"])`: *Object of type Integer is not JSON serializable*.
- **La propia auditoría ya lo esquivaba sin nombrarlo**: el test de `F-35` escribe
  `x.get() ** 2 for x in solucion["v"]`, y el banco del polinomio también.

Y `Structure.__getitem__` documenta `:rtype: BaseType` cuando devuelve `.value`: las
docstrings de los tres accesores se contradicen entre sí.

**Arreglo** Que los accesores desenvuelvan **recursivamente**: `solucion[nombre]`
builtin a cualquier profundidad, igual que ya lo es en el primer nivel, y las
docstrings diciendo lo mismo. **Es un cambio visible en la API pública de `Solution`
y de `Structure`**, aunque el código que hoy compara con `==` siga funcionando —los
objetos ya se comparan iguales a sus builtins—; el que rompe es el que hace
`.get()` sobre un elemento, como el test de `F-35`. Decisión de David. Lo que no es un
arreglo es enseñar a `check_value` a aceptar objetos: las definiciones son el
contrato sobre valores, y es la solución la que no lo cumple.

Mientras tanto, `test_integration.py` desenvuelve a mano con un ayudante que cita
este hallazgo; cuando se cierre, el ayudante es la identidad y sobra.

*Cerrado el 9 de septiembre de 2026 con la primera opción, decisión de David tras
medir a quién rompía.* **Nadie en `src/` ni en la documentación publicada dependía de
que salieran objetos**: el único ejemplo que recorre una estructura, el de TensorFlow,
hace `layer["neurons"]` sobre cada elemento, que funciona igual con un objeto que con un
diccionario. Los únicos rotos eran cuatro `.get()` de tests escritos esa misma semana
—el banco del polinomio y los tests de `F-31` y `F-35`—, adaptados.

**La regla que queda, y que es la que ya tenía `Solution`:** `[]` da el valor puro y
`get` da el objeto. `solucion["L"]` devuelve `{"EI": 5, "ER": 0.25, "EC": "C4"}` y
`solucion["SSS"]` devuelve `[[2, 3, 0], [2, 2, 5]]`, valores de Python a cualquier
profundidad, que el `check` del dominio acepta y `json` serializa; `solucion.get("L")`
sigue devolviendo la `Solution` y `estructura.get(i)` el objeto de la posición. **Se
apartó de lo propuesto en una cosa: `Structure.get()` no cambia.** Es el accesor de
objetos que usa todo el código interno —`resample` de TPE, el cruce, `_alterate`—, y
hacer que devolviera valores puros habría obligado a reescribir una decena de sitios
para acabar con dos accesores de valores puros y ninguno de objetos. Lo que sí cambia es
su docstring, que decía «builtin» y mentía; la de `Structure.__getitem__` decía
`BaseType` y también.

Un ayudante, `builtin_value`, en `base_solution.py`, que `Solution.__getitem__` y
`Structure.__getitem__` comparten. Ni una cifra se mueve: leer no consume sorteos, y la
sonda de `F-38` da lo mismo valor a valor.

El ayudante `_builtin` de `test_integration.py` desaparece, como estaba previsto, y
`test_solution.py` compara ahora un grupo leído con el diccionario que se le dio.

**De paso, sin arreglar:** `docs/source/metagen_in_action/suc/tensorflow.rst:85` hace
`solution["ema"].value` sobre una categórica de primer nivel, que ya devolvía un
valor puro antes de este hallazgo: esa línea no ha funcionado nunca. Y ese mismo
ejemplo declara la categórica con `[True, False]`, booleanos, que no son valores
básicos de categoría. Son de la documentación, no de este hallazgo.

Test: `test_f37_el_valor_de_un_grupo_o_estructura_es_builtin_hasta_el_fondo`, ya sin
marcador.

### [x] F-38 (R) · Una estructura acepta cualquier longitud: `set`, `append`, `insert` y `del` no la comprueban
`src/metagen/framework/solution/types/structure.py:347` (`set`), `:334` (`append`), `:317` (`insert`), `:291` (`__delitem__`) · descubierto al escribir `test/framework/test_integration.py` · tests: `test_f38_*`

`Structure.check` (línea 76) existe, y lanza con una longitud inválida. **No lo llama
nadie de los cuatro.** `set` pasa cada elemento por `_convert`, que valida su valor
contra la definición base, así que un valor fuera de rango se rechaza; el **recuento**
no lo mira nadie. Medido por la vía pública, `Solution.set`:

| operación | definición | resultado |
|---|---|---|
| `set([1, 2, 3])` | estática de **10** enteros | aceptado, longitud 3 |
| `set([1] * 200)` | dinámica de **10 a 100** | aceptado, longitud 200 |
| `set(cinco grupos)` | dinámica de **2 a 4** grupos | aceptado |
| `append` × 15 | dinámica de **1 a 10** reales | longitud 17 |
| `insert(0, 3)` | estática de **10** | longitud 11 |
| `del s[0]` × 2 | estática de **10** | longitud 9 |
| `set([1, 2, 3, 4])` en una interna | anidada, máximo **3** | aceptado |

Un valor fuera de rango en la misma lista —`101` en un entero de 0 a 100, `1.5` en un
real de 0 a 1— **sí** se rechaza: la validación es por elemento y nunca por conjunto.

La consecuencia es que una solución puede dejar de ser válida para su dominio sin que
nada lo diga, y llegar así a la función de fitness del usuario. `mutate` no lo
provoca —`_resize` respeta los límites, comprobado en 10 semillas × 20 mutaciones
sobre el dominio completo—, pero cualquier `set` del usuario, o de un operador que
construya la estructura entera como hace el cruce de `F-31`, puede.

**Arreglo** `set` comprueba la longitud contra la definición antes de sustituir el
contenido; `append`, `insert` y `__delitem__` comprueban la longitud resultante con
`check_length` y lanzan `ValueError` dejando la estructura como estaba. `Structure.check`
ya sabe hacerlo; es cuestión de llamarlo.

*Cerrado el 9 de septiembre de 2026.* **Con una corrección al diagnóstico de arriba:**
`Structure.check` **no** sabe de longitudes. Valida **un elemento** contra la definición
base, y con una lista lanzaba porque una lista no es un entero válido, no por su
recuento; su docstring decía además «a valid Real value». Quien sabe de longitudes es
`check_length` de la definición, que nadie llamaba desde `Structure`.

**Lo que decidió la forma del arreglo no estaba en la ficha:** `initialize` y `_resize`
construían la estructura **elemento a elemento**, con `set([])` y un `append` por
elemento, y `_resize` encogía con un `del` por elemento. Cualquier comprobación en
`set` o en `append` habría rechazado el primer paso de la propia inicialización. Los
dos construyen ahora su lista aparte y la entregan entera con un solo `set`, **con la
misma secuencia de sorteos**: cada elemento nuevo se inicializa dos veces como antes
—en su constructor y en `_resize`— y cada borrado sortea su índice sobre la lista que
va encogiendo. Comprobado valor a valor: 10 semillas × 20 mutaciones sobre el dominio
completo y cinco algoritmos sobre él, idénticos antes y después.

Con eso, `set` comprueba la longitud con `check_length` **antes de convertir**, para que
una lista rechazada no cueste sorteos ni cambie nada; y `append`, `insert`,
`__setitem__` y `__delitem__` trabajan sobre **una copia** y la entregan a `set`. Hacía
falta la copia: `get()` devuelve la lista interna, así que el `append` anterior ya la
había alargado cuando llegaba al `set` que ahora podría rechazarla.

**Tres tests de regresión de hallazgos cerrados hacían crecer una estática**, y se
reformularon con permiso de David: `test_f05_append_conserva_el_valor`,
`test_f05_una_estructura_de_grupos_conserva_el_valor` y
`test_f06_insert_inserta_en_la_lista` metían un cuarto elemento en una estática de
tres, que solo pasaba porque nadie lo comprobaba. Van sobre una dinámica con margen,
con las mismas aserciones: lo que protegen —que el valor añadido sea el dado, que
`insert` inserte en la lista y no en el elemento— no tiene que ver con la longitud. Las
estáticas siguen cubiertas por los otros cuatro tests de F-05 y F-06, por los de este
hallazgo y por el dominio completo de los tests, que tiene cinco.

`check_length` pasa a declarar `Sized` en vez de `StrVal`: solo usa `len()`, y ahora
recibe también listas de elementos ya construidos. mypy se queda en 40.

**Queda fuera, y anotado:** `check_length` de la dinámica **ignora el paso** —acepta
cualquier longitud entre el mínimo y el máximo— mientras `initialize` y el cruce de
`F-31` sí respetan la rejilla. Es una regla del dominio, no de la estructura, y
cambiarla es decisión aparte.

Tests: `test_f38_set_rechaza_una_lista_de_longitud_invalida`, parametrizado en seis
casos, y `test_f38_crecer_o_encoger_fuera_de_los_limites_se_rechaza`.

### [x] F-39 (R) · El cruce de una estructura dinámica de grupos comparte los grupos con los padres
`src/metagen/metaheuristics/ga/ga_tools.py:264` (`cut_and_splice`) y `:236` (`prefix_and_tails`) · descubierto al escribir `test/framework/test_integration.py` · tests: `test_f39_*`

**Lo introdujo `F-31`, el 9 de septiembre de 2026, y hay que decirlo.** El cruce de
longitud variable copia las colas que no se recombinan con `copy()`:

```python
tail1 = [copy(second.get(i)) for i in range(cut2, length2)]
```

`copy` es superficial. Para un `Integer`, un `Real` o una `Categorical` da igual, su
valor es inmutable. Para un **grupo**, que es una `Solution`, la copia comparte el
diccionario de variables con el original: hijo y padre son dos objetos con **las
mismas variables dentro**. El prefijo compartido y todo el camino estático pasan por
`_recombine_prefix`, que para grupos y estructuras recursa por `crossover` y crea
objetos nuevos; por eso solo lo sufren las colas, y solo cuando el elemento es un grupo.

Medido sobre el dominio completo de los tests, 10 semillas, contando contenedores
internos con la misma identidad entre hijos y padres tras un cruce:

| estructura | contenedores compartidos |
|---|---|
| `SSL`, estática de grupos | 0 |
| `SSS`, estática de estructuras | 0 |
| **`DSL`, dinámica de grupos** | **38** |

Y mutando después a los hijos, **los padres cambian en 9 de 20**.

**La consecuencia que lo hizo visible: el GA devuelve un mejor que no vale lo que
dice.** El mejor registrado sigue en la población; sus hijos comparten con él sus
grupos; al mutar los hijos cambian **sus** variables, y el fitness almacenado no se
recalcula:

```
semilla 2: fitness almacenado 373.543   fitness real de sus variables 410.543
semilla 3: fitness almacenado 370.833   fitness real de sus variables 374.833
```

2 de 10 semillas en el GA; 0 de 10 en SSGA y en el memético con el mismo dominio,
que no conservan al mejor dentro de la población de la misma manera; 0 de 10 en el
banco de nueve funciones, que no tiene estructuras. **Ninguna de las cuatro
propiedades del banco lo detecta**: comparan fitness almacenados entre sí, nunca
contra una reevaluación. Es exactamente para lo que se pidieron los tests de
integración.

`GASolution.crossover` y `_recombine_prefix` copian también con `copy()` las variables
que se intercambian enteras. Hoy solo es la categórica, cuyo valor es una cadena, así
que no hace daño; es la misma trampa esperando a un tipo con estado.

**Arreglo** `deepcopy` en todo lo que el cruce copia entero: las colas de
`cut_and_splice` y `prefix_and_tails`, y las ramas de intercambio de
`_recombine_prefix` y `GASolution.crossover`. Y volver a medir el banco, porque
cambia el flujo de sorteos en cero sitios pero conviene comprobarlo.

*Cerrado el 9 de septiembre de 2026, el mismo día que se anotó.* `deepcopy` en los doce
sitios donde el cruce copiaba con `copy()`: las colas y los tramos propios de
`cut_and_splice` y `prefix_and_tails`, las ramas de intercambio de `_recombine_prefix`
y las cuatro de `GASolution.crossover`. **Ninguna cifra del banco se mueve**, como se
esperaba: copiar no consume sorteos. Comprobado con la suite entera, sin ningún `XPASS`
en las tablas de `test_behavior.py`, y valor a valor: el GA devuelve **el mismo fitness
semilla a semilla** en la esfera y en el dominio completo, también en las dos semillas
que estaban desfasadas. Lo que cambia no es el número que reporta, sino que ahora sus
variables valen ese número.

Se retiran los tres marcadores: los dos tests de regresión y el del GA en
`test_integration.py`, que vuelve a exigir a los siete algoritmos que el mejor que
devuelven valga lo que dice su fitness.

Tests: `test_f39_el_cruce_no_comparte_grupos_entre_padres_e_hijos` y
`test_f39_el_ga_devuelve_un_fitness_que_es_el_de_sus_variables`.

### [x] F-41 (R) · `check_length` de la estructura dinámica ignora el paso de longitud
`src/metagen/framework/domain/core.py:653` · descubierto al cerrar `F-38` · test: `test_f41_check_length_respeta_el_paso_de_longitud`

Una estructura dinámica se declara con mínimo, máximo y **paso** de longitud, igual que
un entero con paso: `define_dynamic_structure("v", 2, 8, 2)` declara las longitudes
2, 4, 6 y 8. Medido con esa definición:

| quién | longitudes |
|---|---|
| `initialize` y `mutate`, 200 soluciones × 5 mutaciones | solo 2, 4, 6, 8 |
| el cruce de `F-31` | solo cortes en la rejilla, por `_valid_length` |
| **`check_length`** | acepta **3** |

Quien genera respetaba la rejilla y quien valida no. Con `F-38` eso pasó a importar:
`set` hace cumplir `check_length`, así que `set("v", [1, 2, 3])` se aceptaba y dejaba
una longitud que el propio dominio nunca produce. Y el cruce había tenido que
**reescribir la regla por su cuenta** en `_valid_length`, porque la del dominio no
servía: la misma regla en dos sitios, que es como acaban discrepando.

**Arreglo** Que `check_length` de la dinámica exija además `(longitud − mínimo) % paso
== 0`, y que `_valid_length` delegue en ella.

*Cerrado el mismo día, tal cual, decisión de David.* `_valid_length` pasa a ser una
línea que llama a `check_length` con un `range` de la longitud pedida. Ninguna cifra
se mueve: el banco no tiene ninguna estructura con paso de longitud, y la regla del
cruce ya era esta. La estática no cambia: su longitud es una.

### [x] F-40 (R) · En distribuido, el estado propio del algoritmo se actualiza en una copia y se pierde
`src/metagen/metaheuristics/base.py:102-140` (`_launch_distributed_method`), `tpe/tpe.py:118` y `:137`, `hc/hill_climbing.py:115` · descubierto al escribir `test/metaheuristics/test_extras.py` · tests: `test_f40_*`, que necesitan Ray y se saltan donde no esté

`_launch_distributed_method` manda a Ray el método ligado, `self.initialize` o
`self.iterate`, y Ray **serializa el objeto entero** para cada tarea: el worker trabaja
sobre **una copia** del algoritmo. Lo que el método devuelve vuelve al driver; lo que
guarde en `self` se queda en el worker y se tira con él.

Dos algoritmos guardan estado en `self` dentro de esos métodos, y a los dos les pasa:

| algoritmo | estado que toca dentro de `iterate` / `initialize` | en distribuido |
|---|---|---|
| **TPE** | `solution_history`, que es su modelo | **revienta**: `ZeroDivisionError` en `gamma_sample_based`, con cualquier `warmup_iterations` |
| **`HillClimbing`** | `tabu_list` | corre, pero la lista acaba con **0** entradas donde en secuencial acaba con 3 |

TPE **nunca ha funcionado en distribuido**: el historial se rellena en la copia del
worker durante `initialize`, el del driver sigue vacío, y la primera `iterate` divide
por su longitud. SA no lo sufre porque enfría en `post_iteration`, que corre en el
driver; RS, GA, SSGA y el memético no guardan nada entre iteraciones fuera de la
población, que sí vuelve.

Los tests de metaheurísticas nunca lo vieron porque el banco no distribuye y el CI no
instala Ray. `test_extras.py` marca a TPE como fallo esperado citando esto.

**Arreglo** El estado que un algoritmo mantiene entre iteraciones tiene que
**volver** del worker o **construirse en el driver** a partir de lo que vuelve. Para
TPE basta con alimentar `solution_history` en el driver con la población que devuelve
cada tarea; para `HillClimbing`, con añadir a la lista tabú en `post_iteration` en vez
de en `iterate`. Y conviene dejar escrito en `Metaheuristic` que `initialize` e
`iterate` **no deben mutar `self`**, porque en distribuido no se conserva.

*Cerrado el 9 de septiembre de 2026 con las tres piezas.* El contrato está escrito en
las docstrings de `initialize` e `iterate` de la clase base: **lo que el algoritmo
necesite después tiene que estar en lo que devuelve**, y el estado que deba
persistir se reconstruye en el driver, en `post_iteration`.

**TPE: la población es el historial.** `iterate` ya devolvía `list(solution_history)`
como población, así que lo que recibe en la iteración siguiente **es** su historial.
Pasa a leerlo del argumento `solutions` y `self.solution_history` desaparece —nadie lo
leía fuera de `tpe.py`, ni en tests ni en documentación—. En secuencial no cambia
nada, comprobado valor a valor sobre la esfera con el presupuesto por defecto, con
uno corto y sobre el dominio completo: fitness e historial idénticos en las 30
ejecuciones. **En distribuido cada worker modela sobre el trozo de población que
recibe** y devuelve ese trozo más su candidato; es la primera vez que TPE distribuido
termina, así que no hay un comportamiento anterior que conservar, y así queda dicho.

**`HillClimbing`: la lista tabú se alimenta en `post_iteration`.** Con el mismo
elemento que antes: `local_search_with_tabu` nunca devuelve algo peor que su punto de
partida (`A-02`), así que el mejor de la iteración o mejora al histórico y pasa a
serlo, o es el histórico mismo; en los dos casos es lo que `_best_so_far()` devuelve
en `post_iteration`. Idéntico valor a valor, también el tamaño de la lista al
terminar, en 20 ejecuciones secuenciales.

Distribuido sobre Ray, después: TPE termina y devuelve el mejor que vio, y la lista
tabú de `HillClimbing` acaba llena. `test_extras.py` deja de marcar a TPE como fallo
esperado.

**Lo que sigue sin poderse afirmar es que distribuir no cambia el resultado**, y no es
de este hallazgo: cada worker de Ray arranca con su propio estado de generador
(`A-06`), así que ningún test puede comparar la búsqueda secuencial con la
distribuida valor a valor hasta que se repartan semillas derivadas a los workers.

De paso, la fitness del dominio completo de los tests se muda de
`test_integration.py` a `conftest.py`, junto al dominio: el test de `F-39` la
importaba por el nombre del módulo, y ejecutando solo `regression/` ese nombre
resolvía a un paquete instalado que se llama igual.

Tests: `test_f40_tpe_funciona_en_distribuido` y
`test_f40_hill_climbing_conserva_su_lista_tabu_en_distribuido`, sin marcador; los dos
necesitan Ray.

---

## Algoritmia y diseño

Aquí el código hace lo que dice hacer; lo discutible es qué dice hacer.

- **[x] A-01 (R)** `ga/ga.py:71-79`, `mm/memetic.py:111-119` — **sin selección de padres**: `best_parents` se calcula fuera del bucle y los `n/2` cruces usan siempre la misma pareja. No hay torneo, ruleta ni ranking. *Propuesta*: función de selección intercambiable, torneo binario por defecto.

  *Arreglado en GA y en el memético con un torneo de tamaño configurable.* Se descartó
  la «función de selección intercambiable» de la propuesta: el punto de extensión que
  documenta el framework es **el conector**, y añadir un segundo mecanismo solo para
  esto no se paga. `tournament_size: int = 2` da la palanca que de verdad importa —la
  presión selectiva— sin pedirle a nadie que escriba una función.

  **El hallazgo se queda corto en el diagnóstico, y conviene ver el mecanismo entero.**
  Medido sobre la esfera, con `population_size=10`:

  ```
  gen 0: padres (-0.239647, 0.853832) x (0.115453, -0.973474)   poblacion: 10 puntos distintos de 10
  gen 1: padres ( 0.115453, 0.853832) x (0.115453,  0.853832)   poblacion:  5 puntos distintos de 10
  gen 4: padres ( 0.115453, 0.853832) x (0.115453,  0.853832)   poblacion:  2 puntos distintos de 10
  ```

  No es solo que la pareja no cambie dentro de la generación. Es que **eso se
  realimenta**: el cruce de dos variables reales intercambia exactamente una, así que
  de una pareja fija salen dos hijos posibles; la población se llena de copias de esos
  dos puntos; y **desde la generación 1 los dos mejores son el mismo punto**, con lo
  que cruzar X con X devuelve X y el cruce deja de recombinar nada. Los dos padres
  nunca son el mismo *objeto* —`nsmallest(2)` devuelve dos entradas distintas de la
  lista—, pero sí el mismo *valor*.

  **Resultado, presupuesto igualado y diez semillas.** El GA mejora en 10 de las 12
  medidas:

  | | Sphere | Rastrigin | Rosenbrock | Ackley | Griewank | Schwefel |
  |---|---|---|---|---|---|---|
  | gana al azar | 4 → **7** | 5 → 4 | 1 → 3 | 4 → **7** | 4 → 4 | 4 → 4 |
  | mejora sobre su inicio | 6 → **8** | 9 → 9 | 8 → 8 | 7 → 7 | 6 → **10** | 5 → 6 |

  Sumando las seis, **de 22/60 a 29/60** contra el muestreo aleatorio. Cuatro `xfail`
  de `behavior_test.py` pasan a `XPASS` y se retiran: Sphere y Griewank en «mejora
  sobre su inicio», Sphere y Ackley en «gana al azar».

  **El GA sigue sin llegar al umbral en cuatro funciones, y la causa ya no es esta.**
  Es `F-33`: el cruce uniforme solo baraja coordenadas que ya existían, así que todo
  valor nuevo tiene que venir de una mutación al 0.1. Medido: 15 generaciones de 10
  individuos ven 19 valores distintos de `x` frente a los 10 de partida.

  **En el memético el arreglo es un intercambio, no una mejora limpia**, y hay que
  decirlo. Media sobre **30** semillas, no diez —con diez, la caída de Rastrigin
  parecía de 4.6× y es de un 24 %—:

  | | Sphere | Rastrigin | Rosenbrock | Ackley | Griewank | Schwefel |
  |---|---|---|---|---|---|---|
  | dos mejores | **0.0002** | **0.1883** | **0.0291** | 3.5553 | 3.5188 | **120.46** |
  | torneo | 0.0006 | 0.2344 | 0.0476 | **1.8352** | **1.8157** | 143.31 |

  Empeora en cuatro y mejora a la mitad en dos; contra el azar sube de 44/60 a 47/60.
  El patrón se explica: coger siempre a los dos mejores **intensifica**, y eso rinde
  donde la búsqueda local llega al óptimo; el torneo **explora**, y eso es lo que
  salva a Ackley y Griewank, que son los dominios anchos donde `F-32` deja inútil a
  la búsqueda local. **Decisión de David: mantenerlo**, con la tabla completa a la
  vista. Cuando se cierre `F-32` este equilibrio se moverá y habrá que volver a medir.

  **SSGA se incluyó aunque el hallazgo no lo cita**, decisión de David tras medirlo.
  Solo hace un cruce por iteración, así que lo de «los cinco cruces usan la misma
  pareja» no le aplica; lo que hacía era coger siempre al mejor y al segundo, que es
  truncamiento con el corte más agresivo posible. **Desde la tercera iteración los dos
  padres eran el mismo punto y ahí se quedaba**, 13 de 15 cruces, con lo que la guarda
  `if child1 != child2` descartaba la iteración entera el **62 %** de las veces: SSGA
  evaluaba 150 cruces para aprovechar 47.

  | SSGA, diez semillas | dos mejores | torneo |
  |---|---|---|
  | iteraciones descartadas | 62 % | **26 %** |
  | mejora sobre su inicio, sumando las seis | 23/60 | **36/60** |
  | gana al azar, sumando las seis | 19/60 | **25/60** |

  Mejora en las seis funciones y en las tres medidas; dos `xfail` más se retiran,
  Rastrigin y Schwefel en «mejora sobre su inicio». **El reemplazo *steady state* no se
  toca**, que era la duda razonable: lo que hace steady state a este algoritmo es que
  solo se sustituyan los dos peores, no cómo se eligen los padres. De hecho el steady
  state canónico —el GENITOR de Whitley— **sí lleva selección**, por ranking, así que
  el torneo lo acerca al modelo publicado en vez de alejarlo.

  Tests: `test_a01_el_torneo_no_es_seleccion_por_truncamiento`,
  `test_a01_los_cruces_de_una_generacion_no_usan_la_misma_pareja` (parametrizado por GA
  y memético) y `test_a01_ssga_no_cruza_un_punto_consigo_mismo_casi_siempre`.
- **[x] A-02 (R)** `ts/tabu.py:123-124`, `tools.py:45` — **tabú es hill climbing**: se explora siempre desde `self.best_solution` y `local_search_with_tabu` nunca devuelve algo peor que el punto de partida, así que la lista tabú no puede desviar al algoritmo de nada. *Propuesta*: `current_solution` separada del mejor histórico, moverse al mejor vecino no tabú aunque empeore, criterio de aspiración.

  *Cerrado renombrando, no reescribiendo.* Decisión de David: **el algoritmo es bueno y
  no hay motivo para tirarlo**; lo que estaba mal era el nombre. `TabuSearch` pasa a
  llamarse **`HillClimbing`**, que es lo que hace: muestrea vecinos alrededor del mejor
  y se mueve al mejor de ellos si mejora, sin aceptar nunca un empeoramiento.

  **Sin alias de compatibilidad**, también decisión suya, y el argumento es bueno: quien
  tenga `from metagen.metaheuristics import TabuSearch` se lleva un `ImportError` al
  importar, que es la mejor clase de rotura —ruidosa, inmediata y de una palabra— y un
  alias dejaría para siempre en la API un nombre que sabemos que miente. Renombrar no
  toca nada publicado: `TabuSearch` **no aparece en el README ni en la documentación**, y
  el artículo solo evalúa Random Search y TPE.

  **Antes de renombrar se comprobó que el algoritmo no es un artefacto de la esfera**,
  que era la sospecha razonable. En Rastrigin, con decenas de óptimos locales, aguanta:

  | Función | `HillClimbing` | TPE |
  |---|---|---|
  | Esfera | **10/10**, media 0.0005 (azar 0.1587) | 8/10, 0.0137 |
  | Rastrigin | **9/10**, media 0.6173 (azar 3.2867) | 5/10, 2.0579 |

  Es el mejor del paquete en las dos. La explicación probable es el
  `alteration_limit=1.0` por defecto sobre un dominio `[-5.12, 5.12]`: cada «vecino»
  puede saltar hasta un 10 % del rango, así que escapa de óptimos locales sin necesitar
  el mecanismo tabú.

  **La lista tabú se conserva**, pero documentada por lo que es: memoria de soluciones ya
  vistas que no merece la pena volver a evaluar, no un mecanismo que desvíe la búsqueda.

  **Cuidado para el futuro**: el día que exista una tabú de verdad y se llame
  `TabuSearch`, el código antiguo volvería a importar bien pero **ejecutaría otro
  algoritmo**, que sí es una rotura silenciosa. Se evita si la tabú nueva llega en una
  versión posterior a este renombrado, dejando una ventana en la que el `ImportError`
  avisa.
- **[x] A-03 (R)** `tools.py:49` — el vecindario tabú se genera **en cadena** (`deepcopy(best_neighbor)`), no alrededor de la solución. `mm_tools.py:135` hace lo contrario: las dos implementaciones hermanas discrepan.

  ### Se disuelve con el renombrado de `A-02`, y además el arreglo empeoraba.

  Encadenar es un defecto **para una búsqueda tabú**, que necesita un vecindario
  alrededor del punto actual para elegir el mejor movimiento no tabú. **Para hill
  climbing es el algoritmo**: dar un paso y, si mejora, seguir desde ahí.

  Medido en las dos direcciones, con el mismo presupuesto:

  | | En cadena (como está) | Desde la solución |
  |---|---|---|
  | Esfera | **0.0005** | 0.0025 |
  | Rastrigin | **0.6173** | 0.7778 |

  Aplicar el arreglo propuesto lo empeora **cinco veces en la esfera** y un 26 % en
  Rastrigin. Se revirtió y se dejó un comentario en `tools.py` explicando por qué la
  discrepancia con `mm_tools.py` es deliberada, para que nadie la «unifique».

  **La diferencia con `F-25`, donde encadenar sí era un fallo, merece retenerse:** allí
  la base se movía **en cada mutación, pasara lo que pasara**, así que los vecinos se
  alejaban del punto contra el que el criterio de Metropolis los comparaba. Aquí la base
  **solo se mueve cuando mejora**. El mismo patrón sintáctico, correcto en un sitio e
  incorrecto en el otro.
- **[x] A-04** `rs/random_search.py:110` — `solutions[:-1]` descarta siempre el último individuo, que no tiene por qué ser el peor; la docstring dice que se preserva el mejor.

  *Cerrado.* La copia élite ocupa un hueco, así que alguien tiene que salir; ahora sale
  **el peor**, en vez del que estuviera en la última posición. Ejemplo medido:

  ```
  poblacion: [3.103, 12.191, 2.278, 18.281, 0.129]
  descartaba el 0.129  <- el MEJOR;  conservaba el 18.281 <- el peor
  ```

  Con el mismo presupuesto de 145 evaluaciones, diez semillas: **de 7/10 a 8/10** contra
  el muestreo aleatorio, y la media **de 0.3166 a 0.1613**.

  El test anula `mutate` para que los fitness no cambien y se pueda ver quién sobrevive:
  `test_a04_random_search_descarta_el_peor_no_el_ultimo`.
- **[x] A-05 (R)** `ga/ssga.py:84-86` — `solutions.index(worst)` sustituye por igualdad de valor, no por identidad: con duplicados las dos sustituciones caen en la misma posición.

  ### Refutado. No es un bug.

  **La colisión existe**: medida sobre un dominio entero pequeño, los dos peores son
  iguales en **73 de 130** sustituciones. **Pero no hace daño**, y la razón es sutil:
  `solutions.index(worst)` **rescanea la lista ya modificada**. Cuando la primera
  sustitución quita una copia del duplicado, la segunda búsqueda encuentra la otra. Y en
  el único caso donde la primera deja el duplicado en su sitio —cuando ningún hijo mejora
  al peor, y entonces `best_two = [peor, peor]`— escribir el peor donde ya estaba no
  cambia nada.

  Comprobado de tres formas, porque el razonamiento solo no bastaba:

  | Prueba | Diferencias |
  |---|---|
  | Poblaciones finales de SSGA, 3 semillas, dominio entero | **0** |
  | 4096 casos exhaustivos | **0** |
  | 200 000 casos aleatorios con muchos duplicados | **0** |

  Antes se verificó que el intercambio de implementaciones funcionaba de verdad, para no
  estar midiendo dos veces el mismo código.

  **El código se cambió igualmente**, a trabajar por índices, por decisión de David: *«para
  que sea más compatible con terceros»*. No arregla nada, pero la corrección de la versión
  por valor es **accidental** —depende de que `index()` rescanee— y un refactor razonable,
  como construir una lista nueva en vez de modificar la existente, la rompería sin aviso.
  De paso desaparece el `if worst in solutions`, que nunca es falso.

  Test: `test_a05_la_sustitucion_del_ssga_mete_a_los_dos_mejores`, que **pasa con las dos
  versiones** a propósito: fija la propiedad, no la implementación.

  **Lección de método:** esto salió porque el arreglo **no movió ningún número**, ni en
  continuo ni en discreto. En `F-25` y `F-22` esa misma señal tenía explicación (una rama
  que no se ejecuta con los valores por defecto); aquí no la tenía, y tirar del hilo dio
  la vuelta al hallazgo. Cuando un arreglo correcto no cambia nada, o **está tapado** o
  **no había nada que arreglar**.
- **[x] A-06** transversal — **sin control de semilla**. Todo usa el `random` global (y `np.random` en TPE); no hay parámetro `seed` ni `rng`. En distribuido cada worker de Ray arranca con su propio estado. *Propuesta*: `seed: int | None` en `Metaheuristic.__init__` que construya un `random.Random` y un `np.random.Generator` propios, propagados a `Solution` y a los tipos; en distribuido, `SeedSequence.spawn()`.

  *Cerrado con una variante de la propuesta.* Propagar el generador hasta `Solution` y los tipos exigía tocar sus constructores, que son el punto de extensión que el artículo documenta (caso *Extended Metaheuristic*), así que se descartó por romper la API pública. En su lugar, `metagen/framework/rng.py` guarda **dos generadores propios del paquete** —un `random.Random` y un `np.random.Generator`, porque TPE tira de NumPy y el resto de la biblioteca estándar— y las 38 llamadas al RNG global de `src/` pasan por ellos. `seed` es ahora un parámetro de `Metaheuristic.__init__` (heredado por las siete metaheurísticas) y de los dos lanzadores de CVOA; se aplica en `run()`, no en el constructor, para que cada `run()` arranque del mismo estado.

  Consecuencias que conviene tener presentes:

  - **Sembrar MetaGen ya no toca el `random` del proceso**, ni al revés. Es la ventaja sobre un `random.seed()` global, y hay un test que lo protege.
  - **La garantía solo valía dentro del mismo proceso hasta cerrar `F-26`.** Los tests de este hallazgo comprobaban dos ejecuciones seguidas en la misma sesión de Python, y ahí el fallo era invisible: `Solution.mutate` recorría un `set` de nombres de variable, cuyo orden depende de hashes que Python aleatoriza en cada arranque. Reproducibilidad entre ejecuciones distintas: ver `F-26`.
  - **Los siete helpers de la suite de regresión sembraban con `random.seed()`** y dejaron de ser deterministas al hacer este cambio: `test_f05_append_conserva_el_valor` llegó a pasar por azar (el entero aleatorio salió 7). Ahora siembran con `set_seed()`.
  - **NumPy cambia de algoritmo**: `default_rng()` (PCG64) en vez del Mersenne Twister de `np.random`. La secuencia de TPE ya no es la de la `0.2.0` publicada.
  - **Sigue sin resolverse la concurrencia**: las cepas de CVOA local corren en hilos que comparten los generadores, y los workers de Ray arrancan con su propio estado. Ambas firmas lo advierten en su docstring. Cerrarlo del todo exige un generador por instancia, que es la propuesta original de este hallazgo. *Consecuencia para los tests, vista al cerrar `F-40` el 9 de septiembre de 2026:* `test_extras.py` ejecuta los siete algoritmos sobre Ray y comprueba que cada uno devuelve el mejor que vio, pero **no puede afirmar que distribuir no cambia el resultado**, porque sin semillas derivadas para los workers la búsqueda distribuida no es reproducible. Es lo que falta para ese test.

  Tests: `test_a06_la_misma_semilla_reproduce_la_ejecucion`, `test_a06_semillas_distintas_dan_ejecuciones_distintas`, `test_a06_metagen_no_toca_el_generador_global_del_usuario`.
- **[x] A-07 (R)** `ga`, `ssga`, `mm` — no validan que el dominio use `GAConnector`: con un `Domain()` normal mueren en la primera iteración con `AttributeError: 'Solution' object has no attribute 'crossover'`.

  *Cerrado validando y explicando*, no montando el conector por dentro. **La primera
  propuesta fue lo segundo** —imitar a `F-13`, donde TPE se copia el dominio y le pone su
  conector— y **David señaló por qué no vale**: GA, SSGA y el memético necesitan una
  `Solution` especial porque necesitan **cruzar**, y `GAConnector` es el punto de
  extensión que documenta el framework. Alguien puede traer su propia subclase de
  `GASolution` con otro operador de cruce, y montárselo por dentro se la pisaría. TPE
  puede permitírselo porque `TPEConnector` sustituye tipos internos que nadie extiende.

  Al mirarlo salió el reparto exacto de lo que aporta `GAConnector`, que es menos de lo
  que parece:

  | Definición | Normal | Con `GAConnector` |
  |---|---|---|
  | `BaseDefinition` | `Solution` | **`GASolution`** |
  | `StaticStructureDefinition` | `Structure` | **`GAStructure`** |
  | Integer, Real, Categorical | iguales | iguales |
  | `DynamicStructureDefinition` | `Structure` | **sin registrar** (ver `F-31`) |

  Y esas dos clases añaden **un solo método, `crossover`**. `mutate` está en la clase
  base: cualquier `Solution` sabe mutar.

  **La comprobación pregunta por la capacidad, no por la clase**: `hasattr(tipo,
  "crossover")` en vez de `isinstance(conector, GAConnector)`. Así un conector propio con
  su propio cruce sigue valiendo, que es justo lo que el mecanismo de extensión promete.
  Hay un test que lo protege.

  El mensaje pasa de `AttributeError: 'Solution' object has no attribute 'crossover'` en
  mitad de la primera iteración a un `ValueError` al construir el algoritmo, con las dos
  líneas que hay que escribir.

  Tests: `test_a07_los_geneticos_explican_que_necesitan_el_conector` y
  `test_a07_un_conector_propio_con_crossover_vale`, los dos parametrizados por los tres
  algoritmos.
- **[x] A-08 (R)** `domain/core.py:219, 140` — `RealDefinition` exige `isinstance(value, float)` (rechaza `1` y `np.float32`) y `IntegerDefinition` acepta `bool`. *Propuesta*: `numbers.Real` excluyendo `bool`, normalizando al tipo nativo.

  *Cerrado con la propuesta*, pero hizo falta más que las dos `check_value`, porque
  arreglarlas solas **no se nota desde fuera**.

  **Lo que decía el diagnóstico, comprobado a nivel de definición:**

  | | Antes | Después |
  |---|---|---|
  | `RealDefinition.check_value(1)` | False | **True** |
  | `RealDefinition.check_value(np.float32(1.5))` | False | **True** |
  | `IntegerDefinition.check_value(True)` | **True** | False |
  | `IntegerDefinition.check_value(np.int64(3))` | False | **True** |

  **Un matiz que cambia la lectura:** `Solution.set("n", True)` **ya fallaba** antes, pero
  no por la validación sino por accidente, en el conector: *«The class True has not been
  registered»*. El bug de la definición estaba ahí, tapado por un error que no explica
  nada. Hay un test que comprueba que ahora se rechaza **por ser booleano**.

  **Las dos piezas que faltaban para que se note:**

  1. **`Solution.set` decide el tipo por la definición, no por el valor.** Pedía
     `get_type(value)`, así que meter `1` en una variable real construía un `Integer`
     con una `RealDefinition`, y un escalar de numpy ni llegaba: `bool`, `np.int64` y
     compañía no están registrados como builtins.
  2. **`Integer.set` y `Real.set` normalizan.** Lo que el usuario lee siempre es un
     `int` o un `float` nativo, no lo que entrara.

  Resultado por la vía que usa el usuario:

  ```
  x.set(1)                 -> 1.0  (float)      antes: rechazado
  x.set(np.float32(1.5))   -> 1.5  (float)      antes: rechazado
  n.set(np.int64(3))       -> 3    (int)        antes: rechazado
  n.set(True)              -> TypeError         antes: ValueError del conector
  n.set(3.5)               -> ValueError        igual que antes
  ```

  **Ningún algoritmo cambia de resultado**: los siete dan el mismo fitness medio sobre la
  esfera 2D antes y después. Es un cambio en qué acepta la API, no en cómo busca.

  De paso, `check_value` **convierte antes de comparar** (`int(value) < min`), lo que
  además evita dos errores de mypy: `numbers.Integral` y `numbers.Real` no declaran
  orden.
- **[ ] A-09** `cvoa_local.py` ↔ `cvoa_distributed.py` (372 vs 352 líneas) y `tools.py` ↔ `mm_tools.py` — **código duplicado y ya divergente**. *Propuesta*: una clase por algoritmo y la estrategia de ejecución (secuencial / Ray) como objeto inyectado.

  **Sigue abierto a propósito.** Se hizo solo la parte de riesgo cero y se aplaza la
  reestructuración de CVOA a un trabajo aislado. Decisión de David, 7 de septiembre
  de 2026, con un motivo que no está en el código: **CVOA fue de las partes más duras
  de desarrollar**, porque el algoritmo es multihilo por naturaleza y encima llevaba
  Ray encima. Refactorizarlo de pasada, dentro de una tanda de arreglos, es
  exactamente lo que no conviene.

  **Lo que se midió**, en vez de estimarlo. Los dos CVOA tienen **los mismos métodos**
  y difieren en tres ejes, todos de fontanería:

  | Eje | Local | Distribuido |
  |---|---|---|
  | Logger | `metagen_logger` | `self.remote_logger` |
  | Estado global | `self.global_state.x(...)` | `ray.get(self.global_state.x.remote(...))` |
  | Paso de contagio | un bucle | `distributed_cvoa_new_infected_population(...)` |

  `stopping_criterion` y `__str__` son idénticos; el resto difiere entre 2 y 12 líneas.

  **La divergencia que denuncia el hallazgo existe y se arregló:** el gemelo
  distribuido **imprimía el informe de iteración dos veces**, líneas 171 y 185. No era
  solo ruido: cada uno hace un `ray.get` de ida y vuelta entre procesos, y la f-string
  se evalúa aunque el nivel de log la descarte.

  **`local_search` estaba duplicada byte a byte** en `tools.py` y `mm_tools.py`. Se
  unificó, y con un matiz que no se ve de lejos: **a la de `tools.py` no la usaba
  nadie** y la viva era la del módulo del memético. Se conserva la de `tools.py`, que
  es el módulo genérico y el que documenta `DEVELOPMENT.md`, y `mm_tools` y
  `mm_distributed_tools` la importan de allí.

  **Si algún día se aborda, mejor una clase base con tres puntos de extensión** —los
  tres ejes de la tabla— que la «estrategia de ejecución inyectada» de la propuesta:
  no hace falta inventar una abstracción para dos únicos casos.

  Tests, que no cierran el hallazgo pero **detectan que vuelva a divergir**:
  `test_a09_hay_una_sola_implementacion_de_local_search`,
  `test_a09_los_dos_cvoa_exponen_los_mismos_metodos` (avisa si se le añade un método
  a un gemelo y no al otro) y
  `test_a09_los_dos_cvoa_informan_de_la_iteracion_una_sola_vez`.
- **[x] A-10 (R)** `base.py:196, 247` — `_iterate` hace `self.best_solution = best_individual` sin comparar, así que el elitismo depende de que cada subclase se acuerde; y `stopping_criterion()` devuelve `False` por defecto (bucle infinito si una subclase lo olvida).

  *Cerrado, las dos mitades.* `_iterate` fusiona en vez de asignar, igual que
  `_initialize` desde `F-03`, y `stopping_criterion` pasa a ser `@abstractmethod`. Los
  nueve algoritmos concretos ya lo implementaban, así que no rompe ninguno.

  **No cambia ningún resultado, y conviene decirlo**: medidos los siete algoritmos sobre
  la esfera 2D con diez semillas, dan exactamente el mismo fitness medio antes y después.
  **Hoy ninguna subclase se olvida.** Es una protección, no un arreglo de comportamiento,
  que es como lo plantea el propio hallazgo.

  Por eso el test no mide algoritmos reales sino que **construye una subclase olvidadiza
  a propósito**, que devuelve algo peor de lo que ya había encontrado, y comprueba que la
  clase base no la deja perder el mejor:
  `test_a10_la_clase_base_no_pierde_el_mejor_aunque_la_subclase_se_olvide`. El otro,
  `test_a10_una_subclase_sin_criterio_de_parada_no_se_puede_instanciar`, comprueba que
  olvidarse del criterio de parada ahora es un `TypeError` al construir y no un bucle
  infinito.

  El caso más cercano a ocurrir de verdad es `ssga.py:102`, que devuelve
  `heapq.nsmallest(1, solutions, ...)[0]`, o sea el mejor de la **población actual**, que
  puede ser peor que el mejor histórico. Hoy no pasa porque el elitismo de la propia SSGA
  lo evita; si ese elitismo cambiara, la clase base ya lo cubre.
- **[x] A-11 (R)** `logging/metagen_logger.py:29, 84, 90` — parchea `logging.Logger` globalmente, instala un `StreamHandler` al importar, y añade un handler nuevo en cada llamada a `get_remote_metagen_logger()`. `set_metagen_logger_level` haría `None.close()` si no hay handler de consola. *Propuesta*: solo `NullHandler` al importar y una función de configuración idempotente.

  *Cerrado, los cuatro problemas.* Medidos antes de tocar nada:

  | | Antes | Después |
  |---|---|---|
  | Un logger ajeno gana `detailed_info` | sí | no |
  | Handlers al importar | `['console']` | `['NullHandler']` |
  | Handlers tras 20 `get_remote_metagen_logger()` | 20 | 1 |
  | `set_metagen_logger_level` sin consola | `AttributeError` | funciona |

  **El tercero es el que más dolía**: `mm_distributed_tools` y `cvoa_distributed`
  llaman a `get_remote_metagen_logger()` dentro de bucles, así que cada línea se
  imprimía tantas veces como llamadas se hubieran hecho.

  **La pieza que la propuesta no mencionaba** es qué hacer con el parcheo. Se
  sustituye por una subclase `MetaGenLogger(logging.Logger)` construida con el
  idioma estándar de `setLoggerClass`, acotado a la llamada y restaurado después.
  Se comprobó que `detailed_info` solo se invoca sobre los dos loggers de MetaGen
  —`metagen_logger` y el remoto de CVOA—, así que nadie pierde nada. `addLevelName`
  sí se mantiene: es la forma documentada de dar nombre a un nivel y es inocua.

  `add_file_handler` **también se hizo idempotente**, aunque el hallazgo no lo cita:
  tenía el mismo problema y encima abría un fichero con marca de tiempo nueva en cada
  llamada. Con eso `logger_has_filehandler`, que estaba definida y sin usar, pasa a
  tener uso.

  **Consecuencia asumida**: importar MetaGen ya no imprime nada hasta llamar a
  `set_metagen_logger_level()`. En la práctica no cambia gran cosa, porque el nivel
  por defecto ya era `CRITICAL`.

  Cierra los tres errores de mypy que `P-11` le atribuía: el contador local baja de
  11 a 8. Test: `test_a11_el_logger_no_toca_el_logging_del_proceso`, en subproceso
  porque las tres primeras mitades se deciden al importar.
- **[x] A-12 (R)** `base.py:83` — TensorBoard se activa por el mero hecho de estar instalado, sin forma de desactivarlo: un barrido de cientos de configuraciones escribe cientos de directorios en `logs/`. *Propuesta*: `log_dir: str | None = None` con `None` = desactivado.

  *Cerrado con la propuesta tal cual*, elegida sobre la alternativa de dejar el valor
  por defecto en `"logs"` y usar `None` solo para apagar. El argumento: una librería
  no debería escribir en disco sin que se lo pidan, y quien de verdad usa TensorBoard
  ya suele pasar su propio directorio.

  **Cambia el comportamiento por defecto y hay que decirlo**: con TensorBoard
  instalado, quien antes iba a mirar sus curvas después de una ejecución ya no las
  tendrá salvo que pase `log_dir="logs/GA"` o lo que prefiera. A cambio, esto:

  ```
  5 ejecuciones de RandomSearch por defecto  ->  antes: 5 directorios,  ahora: 0
  ```

  `log_dir` pasa a `Optional[str] = None` en `Metaheuristic` y en las siete
  metaheurísticas, más los dos lanzadores de CVOA; se pierden los valores propios de
  cada algoritmo (`"logs/GA"`, `"logs/TPE"`…), que ahora los elige quien enciende el
  registro. Doce `:param log_dir:` y doce `:type log_dir:` actualizados, que
  anunciaban los valores viejos.

  **Un efecto colateral que destapó mypy:** el worker remoto `run_strain` de
  `distributed_launcher.py` estaba anotado `log_dir: str` y ahora puede recibir
  `None`; se anotó `Optional[str]`. Sin mypy habría pasado desapercibido hasta una
  ejecución distribuida de CVOA.

  Tests: `test_a12_tensorboard_esta_apagado_por_defecto` y
  `test_a12_tensorboard_se_enciende_al_pedirlo`. El segundo importa: apagar por
  defecto no puede llevarse por delante la funcionalidad.

---

## Empaquetado, tests y documentación

- **[x] P-01** `setup.cfg:14` — clasificador `MIT License` frente a un `LICENSE` GPL-3.0 y 55 cabeceras GPLv3. PyPI anuncia MIT. *Arreglo*: unificar y añadir `license` / `license_files`.

  *Cerrado como **GPLv3**, decisión de David: «la licencia es la del fichero LICENSE».*
  La evidencia estaba muy desequilibrada —el `LICENSE` completo y **40** cabeceras en
  `src/` (no 55; ese número incluye ficheros fuera de `src/`) frente a una sola línea de
  clasificador—, pero la dirección no era cosa de la auditoría: **PyPI llevaba
  anunciando MIT desde la 0.2.0**, y si la intención hubiera sido esa, lo que habría que
  cambiar son las otras 41 ubicaciones.

  Es `GPL-3.0-or-later`, no `GPL-3.0-only`: las cabeceras dicen «either version 3 of the
  License, or (at your option) any later version».

  Se añaden `license` y `license_files`, que faltaban: sin el segundo, el fichero
  `LICENSE` no viaja en la distribución. Verificado sobre el paquete instalado:

  ```
  License: GPL-3.0-or-later
  Classifier: License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)
  ```

  Test: `test_p01_la_licencia_declarada_es_la_del_fichero_license`.
- **[x] P-02** README badge `>=3.12` vs texto `3.10+` vs `python_requires >=3.10`. El mínimo real es 3.10 (`itertools.pairwise`). *Cerrado*: el badge pasa a `>=3.10`, que es lo que dicen los otros dos sitios y lo que exige el código. Test: `test_p02_la_version_minima_de_python_dice_lo_mismo_en_los_tres_sitios`.
- **[x] P-03** `setup.cfg:8-10`, badges y enlace de Colab apuntan a `DataLabUPO/MetaGen`; el repo vive en `Data-Science-Big-Data-Research-Lab/MetaGen`. El badge de release no resuelve. *Cerrado*, y había **cuatro sitios más de los que lista el diagnóstico**: `docs/source/metagen_in_action/` tiene cuatro páginas con enlaces de Colab al repositorio antiguo. Son las que publica readthedocs, así que sus cuadernos tampoco abrían. Test: `test_p03_nada_apunta_al_repositorio_antiguo`, que barre README, `setup.cfg` y todos los `.rst`.
- **[x] P-04 (R)** `pytest test` —el comando del README— **no llega a recolectar**: `test/metaheuristics_test/unit_test.py` importa `ray` y `tensorflow`, que son extras opcionales. Solo corren los 101 tests de `framework_test`. *Arreglo*: `pytest.importorskip("ray")` y `pytest.importorskip("tensorflow")` a nivel de módulo en `unit_test.py` (tensorflow se importa de forma transitiva vía el dispatcher, así que un `@pytest.mark.skipif` por test no basta: el fallo ocurre en tiempo de importación). Test: `test_p04_la_suite_completa_se_recolecta_sin_los_extras_opcionales`.
- **[x] P-05** Los tests de metaheurísticas solo comprueban `assert solution is not None`. Los cuatro bugs críticos pasan la suite. *Arreglo*: con semilla fija (A-06), tres aserciones por algoritmo: fitness final ≤ mejor inicial; mejor que una búsqueda aleatoria del mismo presupuesto; `best_solution_fitnesses` monótona no creciente.

  *Cerrado.* El diagnóstico se quedaba corto: los tests sí tenían una cuarta aserción, `assert solution.fitness <= initial_best`, pero `initial_best = float('inf')` y no se actualizaba nunca, así que era una tautología con aspecto de comprobación. Corregida en los ocho tests de `unit_test.py` para comparar contra `best_solution_fitnesses[0]`.

  Lo importante está en `test/metaheuristics_test/behavior_test.py`, nuevo y **sin dependencia de Ray ni TensorFlow**, así que sí se ejecuta en el CI —los de `unit_test.py` no llegan a correr casi nunca—. Cuatro propiedades sobre la esfera 2D, con 10 semillas fijas y umbral de 7 de 10 en las estadísticas.

  Como consecuencia, **la suite verde pasa a ser `pytest test`** (el árbol completo, 4 s), en vez de `pytest test/framework_test test/regression`, que dejaba fuera el directorio de metaheurísticas. El workflow del CI y el test de `P-06` se actualizan en consecuencia.

  Medición con presupuesto igualado —cada algoritmo contra muestreo aleatorio con **sus mismas evaluaciones**—, que es lo que da sentido a la comparación:

  | Algoritmo | Evals | Gana al azar | Fitness medio | Azar |
  |---|---|---|---|---|
  | TabuSearch | 210 | 10/10 | 0.0016 | 0.1150 |
  | TPE | 480 | 8/10 | 0.0137 | 0.0582 |
  | RandomSearch | 145 | 5/10 | 0.1961 | 0.1707 |
  | SSGA | 40 | 4/10 | 0.7562 | 0.6642 |
  | GA | 160 | 4/10 | 0.4588 | 0.1707 |
  | SA | 135 | **0/10** | **2.0045** | 0.1707 |

  - **SA no optimiza**: con el mismo presupuesto saca 2.00 donde tirar dados saca 0.17. De sus 135 evaluaciones, unas 15 buscan algo; el resto las tiran `F-20` y `F-03`.
  - **GA y SSGA** quedan por debajo del azar. En GA se ve en el código: `best_parents` se calcula fuera del bucle, así que los cinco cruces de cada generación usan la misma pareja (`A-01`), y encima la mitad de los hijos son clones (`F-04`).
  - **RandomSearch queda excluida** de esa comprobación: es muestreo aleatorio, empatar consigo misma es lo correcto.
  - **Memetic quedaba fuera** de todo el módulo porque no se podía importar sin Ray (`F-24`). Entró al cerrarlo, y pasa las cuatro propiedades: 10/10 contra el azar con 610 evaluaciones, media 0.0002 frente a 0.0425.

  **Ampliado el 7 de septiembre de 2026 a seis funciones**, a petición de David: las
  clásicas del campo con sus dominios canónicos (Sphere, Rastrigin, Rosenbrock, Ackley,
  Griewank y Schwefel). De 27 casos de prueba a 162, y la suite completa pasa de 15 s a
  28 s. Lo que se gana:

  - **Las dos propiedades estructurales pasan en las 42 combinaciones.** Ningún
    algoritmo reporta un historial que mejora y devuelve otra cosa, en ninguna función.
    Es la comprobación más fuerte del módulo y con una sola función no se sabía.
  - **`F-32` salió de aquí**: `HillClimbing` y el memético dominan las cuatro funciones
    de dominio estrecho y caen por debajo del azar en las dos anchas.
  - **TPE resulta ser el más robusto del conjunto**, cosa que con la esfera sola no se
    veía: allí `HillClimbing` parecía dominar.

  La tabla de `xfail` va **por propiedad**, no compartida: hay pares que fallan «gana al
  azar» y pasan «mejora sobre su inicio», y una tabla común los convertiría en
  `XPASS(strict)`.

  **Completado el 8 de septiembre de 2026 a las nueve del artículo**, añadiendo Levy
  `[−10, 10]`, Michalewicz `[0, π]` y Zakharov `[−5, 10]` con sus dominios canónicos.
  `behavior_test.py` es ya **exactamente el conjunto de la Sección 5.1**. De 162 casos
  de prueba a 243, y la suite completa de 28 s a 34 s.

  **Michalewicz rompe la suposición de que todas tienen el óptimo en 0**: el suyo es
  **−1.8013** en 2D. No hubo que cambiar nada, porque las cuatro propiedades son
  relativas —cada ejecución se compara con su propio inicio o con el azar a su mismo
  presupuesto—, pero ahora el módulo lo dice, para que nadie añada después una
  comprobación que lo dé por supuesto.

  **Las dos propiedades estructurales siguen pasando en las 63 combinaciones**, sin
  excepciones.

  Cuántas de 10 semillas gana cada algoritmo al muestreo aleatorio con **su mismo
  presupuesto**. Es la tabla de referencia del módulo y se actualiza al cerrar cada
  hallazgo que mueva resultados; esta es de después de `F-30`, con entre paréntesis lo
  que daba al abrir la sesión del 8 de septiembre de 2026:

  | | Sph | Ras | Ros | Ack | Gri | Sch | Levy | Mich | Zak | total |
  |---|---|---|---|---|---|---|---|---|---|---|
  | RandomSearch | 8 | 5 | 3 | 8 | 7 | 6 | 5 | 3 | 5 | 50/90 |
  | SA | 10 | 6 | 6 | 10 | 10 | 4 | 10 | 6 | 9 | **71/90** (31) |
  | HillClimbing | 10 | 10 | 8 | 10 | 9 | 6 | 9 | 7 | 10 | **79/90** (70) |
  | GA | 9 | 7 | 5 | 9 | 7 | 6 | 7 | 7 | 5 | **62/90** (40) |
  | SSGA | 5 | 8 | 6 | 6 | 6 | 4 | 6 | 7 | 3 | **51/90** (38) |
  | TPE | 10 | 6 | 6 | 10 | 8 | 5 | 8 | 6 | 8 | 67/90 |
  | **Memetic** | 10 | 10 | 9 | 10 | 9 | 9 | 10 | 10 | 10 | **87/90** (75) |

  Tres cosas que las seis funciones no dejaban ver:

  - **El memético es el mejor del paquete, no `HillClimbing`.** Empata o gana en las
    nueve. `HillClimbing` va segundo, SA tercero desde `F-30` y TPE cuarto. Con la
    esfera sola parecía que dominaba `HillClimbing`; con seis, que el más robusto era
    TPE. Ninguna de las dos lecturas se sostiene con las nueve.
  - **Los siete alcanzan o superan al muestreo aleatorio**, que suma 50/90 empatando
    consigo mismo. No era así al abrir la sesión del 8 de septiembre de 2026: SA estaba
    en 31/90, GA en 40 y SSGA en 38. Los sacaron `A-01`, `F-30`, `F-32` y `F-33`.
  - **Michalewicz derrota a seis de los siete, y la culpa es de la función.** Medido
    sobre una rejilla de 1200×1200, la mediana del paisaje es **−0.015** frente a un
    óptimo de −1.8013, y solo el **0.43 %** del dominio baja de −1.5. Es un pajar con
    una aguja: sin estructura que explotar, todos **empatan** con el azar en vez de
    perder, con recuentos de 4 a 6 alrededor del umbral de 7. Solo el memético lo pasa,
    con cuatro veces el presupuesto de cualquier otro.
  - **Zakharov es el peor resultado del GA en las nueve: 0 de 10.** Acopla las variables
    mediante una suma ponderada elevada a la cuarta, así que lo que hace buena a una
    solución es la **combinación**; intercambiar una coordenada entre padres, que es
    todo lo que el cruce uniforme de `F-33` sabe hacer, la destruye.

  **Ampliado el 8 de septiembre de 2026 con un problema de hiperparámetros**, a
  petición de David: nueve funciones de dos variables reales no dicen nada del caso de
  uso que vende el paquete. El décimo problema afina un árbol de decisión de
  scikit-learn sobre un dominio **heterogéneo de verdad** —dos enteros, una categórica
  y un real, de anchuras muy distintas—, que es donde muerden `F-32` y `F-33` y donde
  el banco era ciego.

  **`scikit-learn` entra en el extra `test`**, así que el CI lo instala y el problema
  se mide en todas partes. Sigue sin instalar `ray` ni `tensorflow`, que es lo que
  `P-06` protege.

  **El coste obligó a apartarse del ejemplo publicado.** El tutorial del repo afina un
  Random Forest de 100 árboles con validación cruzada de 10 pliegues: **543 ms por
  evaluación**, y el banco gasta unas 34 000 evaluaciones por problema entre los
  algoritmos y su línea base. Serían **dos horas**. Un árbol único sobre una partición
  fija cuesta 1.2 ms y cabe en 30 s. La suite completa pasa de 35 s a **66 s**.

  **La métrica se cambió de exactitud a log-loss, y el motivo es una lección de
  método:** con exactitud, `RandomSearch` sacaba **9 de 10 contra sí mismo**. La
  comprobación es `<=`, la exactitud sobre 90 muestras solo toma **17 valores
  distintos** en mil configuraciones, y el 14 % de las parejas empatan: los empates
  contaban como victorias y la propiedad había dejado de medir nada. La log-loss da
  **154 valores distintos** y diez veces más rango. **La fila de `RandomSearch` es la
  calibración del banco**: si se aleja de 5 de 10, la comparación está rota.

  **De paso se arregló el muestreo de referencia**, que creaba **dos soluciones por
  punto** y tomaba la `x` de una y la `y` de otra. Estadísticamente daba lo mismo
  —siguen siendo puntos uniformes independientes— pero consumía el doble de sorteos, y
  con un dominio que no tiene `x` ni `y` no se sostenía. **Cambia el flujo de números
  aleatorios**, así que las celdas al borde se movieron y la tabla de `xfail` se
  recalibró entera. Michalewicz es la que más se mueve, y hay motivo: solo el 0.43 %
  de su dominio baja de −1.5, así que los dos lados de la comparación dependen de
  sorteos afortunados.

  Tabla de referencia con los diez problemas, tras `F-33`:

  | | Sph | Ras | Ros | Ack | Gri | Sch | Levy | Mich | Zak | **Árbol** | total |
  |---|---|---|---|---|---|---|---|---|---|---|---|
  | RandomSearch | 8 | 4 | 4 | 7 | 6 | 6 | 5 | 6 | 6 | 4 | 56/100 |
  | SA | 10 | 9 | 4 | 10 | 9 | 6 | 9 | 7 | 10 | 3 | 77/100 |
  | HillClimbing | 10 | 10 | 8 | 10 | 8 | 6 | 9 | 10 | 10 | **8** | 89/100 |
  | GA | 6 | 9 | 5 | 7 | 7 | 5 | 6 | 8 | 4 | 5 | 62/100 |
  | SSGA | 5 | 6 | 3 | 5 | 5 | 5 | 7 | 10 | 4 | 4 | 54/100 |
  | TPE | 8 | 5 | 5 | 9 | 9 | 6 | 8 | 7 | 10 | **3** | 70/100 |
  | **Memetic** | 10 | 10 | 6 | 10 | 10 | 9 | 10 | 10 | 10 | 6 | **91/100** |

  **Lo que el problema nuevo destapa, y merece mirarse:** el dominio heterogéneo separa
  a los algoritmos de otra manera. `HillClimbing` lo gana con 8 de 10 y el memético con
  6, mientras que **TPE se queda en 3, por debajo del muestreo aleatorio** — y la
  búsqueda de hiperparámetros es exactamente para lo que existe TPE, además de ser uno
  de los dos algoritmos que evalúa el artículo. No se convierte en hallazgo sin
  investigarlo, pero queda anotado.

  **En «mejora sobre su inicio» solo queda TPE** con marcador, en Rosenbrock y
  Schwefel. Los otros seis, `RandomSearch` incluida, mejoran sobre su punto de partida
  en todos los problemas.

  **Al problema del árbol solo se le exigen las dos propiedades estructurales, y el
  motivo es una lección que costó un CI en rojo.** Los números de arriba están medidos
  aquí; el CI corre en Linux x86 con numpy 2.4 y la última scikit-learn, frente a
  macOS arm64 con numpy 1.26 y scikit-learn 1.5. **Entrenar un modelo no es
  aritmética**: el árbol ajusta cortes ligeramente distintos, la log-loss de cada
  configuración cambia, y el paisaje no es el mismo. `Memetic` da 6/10 aquí y ≥7 allí,
  y como estaba anotado `xfail(strict=True)` —«se espera que no llegue»— el CI lo
  reportó como error.

  Y no hay forma de anotarlo bien: **cualquier umbral fijo será correcto en una máquina
  e incorrecto en la otra**. Con el marcador, rojo en el CI; sin él, rojo aquí. Dos de
  las seis celdas del problema están a un solo punto del umbral, así que basta un
  desplazamiento mínimo del paisaje.

  Las dos propiedades **estructurales** sí se exigen, y en las siete combinaciones:
  miran la contabilidad interna del algoritmo —que el historial no empeore, que
  devuelva lo mejor que vio— y no cuánto vale el fitness, así que dan igual en
  cualquier máquina. Son además las comprobaciones más fuertes del módulo. Lo que se
  pierde es afirmar un umbral estadístico sobre ese problema; lo que se conserva es
  **recorrer un dominio heterogéneo de punta a punta con los siete algoritmos**, que
  era lo que faltaba. Las estadísticas se siguen pudiendo medir a mano: así salió lo
  de TPE.

  `_Problem` gana una bandera `reproducible` que documenta la distinción; las nueve
  funciones la tienen a cierto porque son aritmética pura.

  Los tests de SA, GA y SSGA nacen `xfail(strict=True)` citando el hallazgo culpable: al arreglar `F-20`, `F-04` o `A-05` saltarán a `XPASS` avisando de que ya se puede quitar el marcador. Se comprobó además que estos resultados **son idénticos antes de `A-06`**, ejecutando el código en `1016e8a`: no son un efecto del cambio de semilla, que solo los ha hecho medibles.
- **[x] P-06** No hay `.github/workflows`. Con `mypy` ya configurado en `setup.cfg` y una suite que corre en 3 s, un workflow mínimo con matriz 3.10–3.12 captura buena parte de lo anterior. *Cerrado*: `.github/workflows/ci.yml` con dos jobs, `tests` (matriz 3.10–3.12, bloqueante) y `types` (`mypy src`, informativo hasta que cierre `P-11`). Dos cosas salieron a la luz al montarlo: la suite necesita `pytest-csv-params`, que no declara ni `install_requires` ni ningún extra (ver `P-08`), y **el CI no instala los extras a propósito**. Aquello valía cuando el test de `F-24` se saltaba con Ray instalado; al cerrar ese hallazgo se reescribió para bloquear Ray en un subproceso y ahora corre en todas partes. El único test que sigue necesitando Ray de verdad es el de `F-21`. *Desde el 9 de septiembre de 2026 `pytest-csv-params` ya no existe*: los tests dirigidos por CSV se reescribieron en línea al reorganizar `test/`, y el CI instala el extra `test`, que hoy declara `pytest` y `scikit-learn`. Su test comprueba eso.
- **[x] P-07** `.gitignore:14` excluye `*.csv` y `*.xlsx`, y los parámetros de test son CSV en `test/test_parameters/`. Cualquier fichero nuevo se queda fuera del commit sin aviso. *Arreglo*: `!test/test_parameters/**/*.csv`. *Cerrado tal cual.* Comprobado que los 25 CSV que ya estaban versionados siguen estándolo —una regla de `.gitignore` no desversiona nada— y que uno nuevo **ya aparece en `git status`**, donde antes no salía. Test: `test_p07_los_csv_de_parametros_no_estan_ignorados`, con `git check-ignore`. *El 9 de septiembre de 2026 desapareció `test/test_parameters/`*, al reescribir en línea los tests que leían esos CSV; la excepción pasa a `!test/**/*.csv`, que cubre cualquier dato de test en CSV esté donde esté, y el test apunta a una ruta bajo `test/framework/`.
- **[x] P-08** Los extras de `setup.cfg` usan `;`, que en PEP 508 es el separador de **marcadores de entorno**, no de requisitos: `tensorboard = tensorboard; tensorboardX` se lee como «tensorboard, si el marcador tensorboardX». Comprobar qué instala `pip install pymetagen-datalabupo[all]`. Además hay tres `requirements*.txt` con criterios solapados. *Arreglo*: un requisito por línea y migrar la metadata a `pyproject.toml`.

  **Dos partes del diagnóstico son falsas, y se comprobó antes de arreglar nada.** La
  auditoría manda comprobar qué instalan los extras; hecho, sobre el paquete instalado:

  ```
  tensorboard;  extra == "tensorboard"
  tensorboardX; extra == "tensorboard"
  ```

  **Los extras funcionaban**: setuptools parte por `;` los valores de lista en un
  fichero `.cfg`, así que las dos dependencias entraban. Y donde el documento dice «tres
  `requirements*.txt`», solo había **uno**.

  **Lo que sí es cierto es el riesgo, y está justo en la migración que el propio
  documento propone**: ese `;` funciona por una particularidad del formato `.cfg`. En un
  `pyproject.toml`, donde el valor es una lista TOML, el mismo texto se leería como manda
  PEP 508 y **`tensorboardX` desaparecería en silencio**.

  *Cerrado con la variante conservadora, decisión de David:* un requisito por línea, sin
  migrar a `pyproject.toml`. La migración queda como trabajo aparte, para cuando se
  publique una versión nueva y se pueda probar contra TestPyPI.

  Además:

  - **Extra `test` nuevo**, con `pytest` y `pytest-csv-params`. Este último lo necesita
    `framework_test/solution_test.py` y **no lo declaraba nada**; salió al montar el CI
    (`P-06`) y el documento no lo lista. El workflow pasa a instalar `.[test]` en vez de
    nombrar las herramientas a mano, que es lo que mantiene honesta la declaración.
  - **`all` fija `ray>=2.40.0`**, como `distributed`. Antes llevaba `ray` a secas: los
    dos extras podían instalar versiones distintas.
  - **`requirements.txt` se parte en dos.** Mezclaba dependencias de ejecución, de
    documentación, de test, extras opcionales y las del *benchmark* del artículo, todo
    en un fichero con secciones en comentarios. Ahora queda con lo de ejecutar,
    documentar y probar, y `requirements-optional.txt` con lo demás.

  Test: `test_p08_los_extras_declaran_un_requisito_por_linea`, que además comprueba que
  el extra `test` declare lo que la suite necesita. Fue `pytest-csv-params` hasta el 9 de
  septiembre de 2026, cuando los tests dirigidos por CSV se reescribieron en línea; hoy es
  `scikit-learn`, por el problema de hiperparámetros del banco (`P-05`). **Y se lee de
  `setup.cfg`, no de la metadata instalada**: esta refleja la última `pip install -e .`,
  no el árbol, y con ella el test daba por buena una declaración que ya no estaba.
- **[x] P-09** Falta `src/metagen/py.typed`: el paquete está anotado de arriba abajo pero sin el marcador PEP 561 mypy trata `metagen` como `Any`. *Cerrado*, con el fichero y su declaración en `[options.package_data]`, sin la cual no viajaría en la distribución. **La comprobación evidente no sirve**: con el paquete instalado en modo editable, mypy lee las fuentes igual y el marcador no cambia nada, así que probarlo así da un falso positivo en las dos direcciones. Se verificó construyendo una rueda y mirando dentro. Test: `test_p09_el_paquete_lleva_el_marcador_py_typed`.
- **[x] P-10 (R)** Los ejemplos de las docstrings usan una API que no existe: `domain.defineInteger(0, 1)` en RS, TPE, Memetic y CVOA (el método es `define_integer(name, min, max)`), y el ejemplo de CVOA usa `CVOA.initialize_pandemic(...)` y `cvoa_launcher(strains)`, de una versión anterior. Son las páginas que publica readthedocs. *Arreglo*: actualizarlos y añadirlos como doctests.

  *Cerrado.* **Había dos errores más de los que lista el diagnóstico**, y los dos
  aparecieron al ejecutar los ejemplos en vez de leerlos:

  - El de CVOA hace `from metagen.metaheuristics import CVOA, cvoa_launcher`, y
    **`CVOA` no se exporta**: solo `cvoa_launcher`. El ejemplo fallaba en su tercera
    línea, antes de llegar al `defineInteger`.
  - El del memético usaba `fitness_function = lambda x: sum(x)`, que revienta: iterar
    una `Solution` devuelve **nombres de variable**, no valores.

  Y una tercera cosa que el ejemplo del memético callaba: necesita
  `Domain(connector=GAConnector())`. Con un `Domain()` normal muere en la primera
  iteración (es `A-07`). Ahora el ejemplo lo pasa y explica por qué.

  **En vez de doctests, un test que ejecuta los ejemplos.** Extrae el
  `.. code-block:: python` de las cuatro docstrings y lo ejecuta entero **salvo la
  optimización**: `run()` y `cvoa_launcher` se sustituyen por dobles. Correrlos de
  verdad son decenas de miles de evaluaciones, y minutos en CVOA desde que `F-23`
  dejó que las cepas se ejecuten. Lo que se comprueba es exactamente donde estaban
  los fallos: que los imports resuelven, que los métodos del dominio existen y que
  los constructores aceptan lo que el ejemplo les pasa. Comprobado que el test falla
  con los cuatro ejemplos viejos, cada uno por su motivo.

  Test: `test_p10_los_ejemplos_de_las_docstrings_usan_la_api_de_verdad`,
  parametrizado por módulo.
- **[ ] P-11** `mypy src` **no pasa limpio**. El contador que llevaba este hallazgo —14 al abrirlo, 8 tras cerrar `F-01`, `F-05` y `A-11`— **estaba medido con mypy ciego a los tipos del propio paquete**, y hay que rehacerlo. Ver abajo.

  ## El contador estaba mal medido

  `mypy src` sobre un proyecto con disposición `src/` y sin `mypy_path` comprueba los
  ficheros pero resuelve `from metagen.framework import ...` contra el paquete
  **instalado**; con `ignore_missing_imports = True` eso se convierte en `Any`. Es
  decir, **no se comprobaba ni un solo uso entre módulos**. Verificado con una sonda:
  con la configuración vieja no se revelaba ningún tipo; con la nueva,
  `Revealed type is "metagen.framework.facades.Domain"`.

  Al añadir `py.typed` (`P-09`) el montaje deja de funcionar directamente —
  *«Source file found twice under different module names»* — y hay que declarar
  `mypy_path = src` y `explicit_package_bases = True`, que es la configuración estándar
  para esta disposición. Con ella, mypy comprueba el paquete de verdad:

  | Configuración | Errores |
  |---|---|
  | La original, sin `py.typed` | **8** |
  | `mypy_path = src` + `explicit_package_bases`, con o sin `py.typed` | **170** |

  Comprobado que el salto **no lo causa `py.typed`**: con la configuración nueva salen
  170 con el marcador y sin él. Lo causa que mypy pase a resolver los imports internos
  contra las fuentes en vez de contra `Any`.

  ## Qué son esos 170

  Reparto por fichero y por categoría:

  | Fichero | Errores |
  |---|---|
  | `framework/facades.py` | 26 |
  | `solution/types/structure.py` | 23 |
  | `cvoa/cvoa_distributed.py` | 21 |
  | `solution/types/integer.py` | 14 |
  | `framework/connector/connector.py` | 14 |
  | `solution/base_solution.py` | 11 |
  | resto (14 ficheros) | 61 |

  `misc` 60, `valid-type` 26, `attr-defined` 20, `arg-type` 20, `assignment` 15,
  `return-value` 12, `union-attr` 7, `var-annotated` 3.

  **Son errores reales, no ruido de configuración.** Muestreados, salen cosas como
  `Argument 1 to "local_search_with_tabu" has incompatible type "Optional[Solution]"`
  (familia `F-14`/`A-10`) o `List item 1 has incompatible type "Solution"; expected
  "GASolution"` en el memético.

  **Pero conviene no exagerar: no todos son bugs latentes.** Por ejemplo,
  `integer.py:68: Too many values to unpack (4 expected, 5 provided)` suena a fallo de
  ejecución y no lo es: `Base.get_attributes()` está declarado como una unión que
  incluye la variante de cinco elementos de las estructuras, mientras que en ejecución
  un `Integer` siempre lleva un `IntegerDefinition`, que devuelve cuatro. El error está
  en que el tipo declarado es demasiado ancho, no en el código.

  ## Qué falta decidir

  Esto pasa de «arreglar cuatro cosas» a un trabajo de su propio tamaño, y la decisión
  es del equipo. **El job `types` del CI sigue siendo informativo**
  (`continue-on-error: true`), así que nada se rompe mientras tanto.

  *Arreglo*: **sesión dedicada, fichero a fichero**, decisión de David del 7 de
  septiembre de 2026. Mismo trato que CVOA. Empezar por `facades.py`, `structure.py` y
  `cvoa_distributed.py`, que suman 70 de los 170. Cuando `mypy src` salga a cero, quitar
  el `continue-on-error` del job `types` para que la comprobación pase a bloquear.

  ### Primera tanda: `facades.py` y `connector.py` a cero

  **167 → 136**, 8 de septiembre de 2026. Los dos ficheros quedan limpios y la suite no
  se mueve. **El recuento por fichero que traía este hallazgo estaba inflado**: contaba
  también las líneas `note:` de mypy, así que `facades.py` figuraba con 52 y sus errores
  reales eran 26.

  **Una sola equivocación explicaba los 26 de `facades.py` y 6 de `connector.py`.**
  `domain/bounds.py` y `solution/bounds.py` definen `TypeVar`s —`BaseClass`,
  `BaseTypeClass`, `IntegerDefinitionClass`…— que el código usa **como si fueran
  alias de las clases base**. Un `TypeVar` que aparece solo en el retorno no se puede
  resolver: queda «sin ligar», mypy lo trata como `Any` y **todo lo que viene detrás
  deja de comprobarse**. De ahí los mensajes en cascada, «type variable is unbound» y
  «cannot instantiate».

  Sin bug de ejecución: en `facades.py` la variable local guarda la clase que devuelve
  el conector y el `TypeVar` solo la anota, así que nunca se le llama.

  **Lo que los `TypeVar` estaban tapando sí importaba.** Al ponerles el tipo de verdad
  apareció que **los cuatro diccionarios del conector están anotados como si guardaran
  instancias** cuando lo que guardan son **clases**, y que `get_type` puede devolver una
  `Solution`, que **no es un `BaseType`** (lo que ya enseñó `F-05`): su retorno declarado
  era falso. Con `Any` no se veía ninguna de las dos cosas.

  Cambios, todos de anotación salvo lo que se dice:

  - `connector.py`: alias con nombre `SolutionEntry` y `BuiltinType` para lo que el
    registro guarda de verdad —la clase, o la clase con un discriminador, porque un
    `list` mapea a la estructura estática **y** a la dinámica—; los cuatro diccionarios
    pasan a `Dict[type[...], ...]`; `get_type` declara `type[BaseType | Solution]`; y las
    tres funciones dejan de **reasignar su propio parámetro** a un tipo distinto, que es
    lo que confundía a mypy, usando una local.
  - Un ayudante privado, `_solution_class`, quita el discriminador. **Con él, dos pares
    de ramas de `get_type` pasaron a ser idénticas y se fusionaron**: la de estructuras
    con la de definiciones, y la de `list` con la de los demás builtins. Es la única
    simplificación de lógica, y es equivalente.
  - `facades.py`: las trece locales anotadas con un `TypeVar` pasan a un `cast` a su
    clase concreta. El `cast` es honesto: el código **sabe** qué tipo ha pedido al
    conector y mypy no puede seguir un registro de tiempo de ejecución.

  **Cambia una anotación de la API pública**: `BaseConnector.get_type` pasa de declarar
  `type[BaseTypeClass]` —que resolvía a `Any`— a `type[BaseType | Solution]`. No cambia
  el comportamiento y dice más, no menos, pero `BaseConnector` es el punto de extensión
  del framework y conviene que conste.

  **Y destapó un bug de verdad, que es lo que este hallazgo anunciaba**: ver `F-34`.

  ### Segunda tanda: `framework/` entero a cero

  **136 → 71**, el mismo día. Toda la capa `framework/` queda limpia y lo que resta está
  en `metaheuristics/`. Otra vez **una causa raíz por familia**, no sesenta problemas
  distintos.

  **Los tipos simples: 32 errores de un solo patrón.** `BaseType.get_definition()`
  devuelve `Base`, cuyo `get_attributes()` es la unión de tuplas de dos a cinco
  elementos, así que **ningún desempaquetado concreto podía comprobarse**. `Integer`,
  `Real` y `Categorical` tienen una única clase de definición, así que basta
  **estrechar `get_definition()` una vez por clase** —un `cast`— y todos sus
  desempaquetados quedan bien. Es la familia que la ficha ya citaba con
  `integer.py:68`.

  **`Structure`, 22 errores y cuatro causas.** Su definición sí puede ser estática o
  dinámica de verdad, con tuplas de tres y de cinco, así que en vez de un `cast` se
  **guarda la definición en una local** y `isinstance` estrecha por sí solo. Además:
  su constructor declaraba `BaseStructureDefinition`, que **no es un `Base`** y por
  tanto no es lo que `BaseType` acepta; un ayudante nuevo, `_new_element`, concentra la
  construcción de elementos, que sale de un registro que mypy no puede seguir; y la
  firma de `_convert` seguía sin admitir los `BaseType` que **acepta desde `F-05`**.

  **`base_solution.py`, 11.** Los mismos `TypeVar` sin ligar que `facades.py`, más
  `alterations_number: int = None`, más el diccionario de variables, que puede guardar
  una sub-`Solution`.

  **Cambian tres anotaciones de la API pública de `Solution`**, y es la decisión de
  fondo de esta tanda:

  | método | antes | ahora |
  |---|---|---|
  | `get_variables()` | `Dict[str, BaseType]` | `Dict[str, Union[BaseType, Solution]]` |
  | `get(variable)` | `BaseType` | `Union[BaseType, Solution]` |
  | `set(variable, value)` | `InputValue \| BaseType` | `Union[InputValue, BaseType, Solution]` |

  **Las de antes eran falsas:** con una variable de grupo, `get()` devuelve una
  `Solution`, que **no es un `BaseType`** —su MRO es `['Solution', 'object']`—. Es
  exactamente la mentira que en `F-05` habría roto las estructuras de grupos si se
  hubiera aplicado el arreglo literal que proponía la auditoría.

  **No rompe nada en ejecución**: las anotaciones son metadatos y el programa de un
  usuario corre idéntico; comprobado ejecutando código de usuario que incluye las líneas
  que mypy señala, más una optimización completa. Solo cambia lo que dice **mypy**, y
  solo a quien lo ejecute sobre su propio código.

  **Y hoy no lo ve nadie**: `master`, que es lo publicado, **no lleva `py.typed`**; lo
  añadió `P-09` en esta auditoría y está sin publicar. Sin ese marcador mypy trata el
  paquete entero como `Any` desde fuera. Es decir, **las anotaciones se harán visibles
  todas de golpe en la primera versión tipada, y ese es el mejor momento posible para
  que sean ciertas**.

  **La molestia para quien no use grupos, medida y no supuesta.** De cinco usos típicos:

  | uso | ¿le afecta? |
  |---|---|
  | `solucion["x"]`, el acceso de los tutoriales | no |
  | `solucion.get("x").mutate()` | no |
  | recorrer `get_variables()` y mutar | no |
  | `variable: BaseType = solucion.get("x")` | **sí** |
  | `solucion.get("x").get()` | **sí** |

  Los dos que fallan **son los que asumen que no hay grupos**, así que mypy tiene razón;
  se resuelven con un `isinstance` o un `cast` en el código del usuario. **Mejora futura
  posible**, que sería añadir API y no toca a una tanda de tipado: un accesor aparte
  —`get_group(nombre) -> Solution`— que daría cero fricción sin que la firma mienta.

  **Dos trampas de este trabajo que conviene retener:**

  - `types.BaseType | 'Solution'` **revienta en ejecución** con
    `TypeError: unsupported operand type(s) for |: 'ABCMeta' and 'str'`, porque la firma
    de un método se evalúa al definirlo. Dentro de la propia clase `Solution` la
    referencia adelantada tiene que ir en `Union[...]`. Tiró la recolección de tres
    ficheros de test.
  - `cast` **evalúa su primer argumento**, así que un tipo importado solo bajo
    `TYPE_CHECKING` hay que citarlo entre comillas.

  ### Tercera tanda: todo lo que no es CVOA, a cero

  **71 → 40**, 9 de septiembre de 2026. Los 40 que quedan viven en los cuatro ficheros
  de CVOA, que van a su sesión. La suite no se mueve.

  **La mitad de los 31 era una sola cosa:** `Metaheuristic.best_solution` está declarado
  `Optional[Solution]`, y es cierto —vale `None` hasta `_initialize()`—, pero **no en
  ningún punto desde el que lo lee una subclase**: `iterate()` y los *callbacks* solo
  corren después de inicializar. Catorce errores en ocho ficheros. Va un accesor
  privado, `_best_so_far()`, que estrecha con un `RuntimeError` que dice qué pasa, en
  vez de catorce `cast`; leerlo antes de tiempo daba un `AttributeError` sobre `None`
  sin pista de la causa.

  **Cuatro sitios pedían al conector «la clase del núcleo» con la misma línea**, y
  con `get_type` declarando `BaseType | Solution` desde la primera tanda los cuatro
  fallaban igual. Ahora es una función, `tools.solution_class(domain)`, el único sitio
  que afirma que el núcleo —una `BaseDefinition`— se corresponde con una clase de
  `Solution`. TPE la estrecha además a `TPESolution`, que es lo que su conector
  instala (`F-13`).

  **Un `Protocol`, `Crossable`, para la capacidad de cruzar.** `GASolution.crossover`
  pregunta con `hasattr` desde `F-33`, y eso es lo correcto —el conector es el punto de
  extensión, un tipo propio con su operador vale (`A-07`)— pero mypy no estrecha por
  `hasattr`. El protocolo es lo que significa haber pasado la comprobación.

  **`Memetic.iterate` declaraba `List[GASolution]`** donde la clase base declara
  `List[Solution]`, una violación de Liskov que además era innecesaria: los padres ya
  se convierten con `cast` al salir del torneo.

  **`BaseType.get_connector()` estrecha con error.** El conector es opcional en el
  constructor —un tipo simple puede construirse sin él y no necesitarlo nunca— pero
  una estructura no puede, porque construye sus elementos a través del registro.
  Leerlo sin conector fallaba una línea más tarde, sobre el `None`.

  **Y un intento equivocado que conviene dejar escrito.** Los dos errores de las
  estructuras en `core.py` venían de que `DymAttr`/`StaAttr` declaran la base como
  `Union[BaseAttr, DefAttr, None]` —básico o grupo— mientras `get_base()` devuelve
  `Base`. Mi primer arreglo fue **estrechar `get_base()`** con un alias que afirmaba
  «una estructura nunca contiene otra estructura». **Era falso**, y solo lo supe porque
  lo probé antes de darlo por bueno: `set_structure_to_variable` acepta cualquier
  variable ya definida, y una estructura de estructuras **se inicializa, muta y
  reporta** `('STATIC', 3, ('STATIC', 2, ('REAL', …)))`. Revertido. Lo estrecho de
  verdad eran los literales, que ahora son recursivos —`Optional["Attributes"]`—, como
  ya lo era `DefAttr`. **Anidar estructuras es una capacidad real del paquete** y no
  está documentada más que en la docstring de ese método.

  De paso, `TPE.initialize` con cero soluciones devolvía `None` en silencio y fallaba
  en la primera comparación; ahora es un `ValueError` que dice qué falta.
