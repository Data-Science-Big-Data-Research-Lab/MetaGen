# Auditoría de MetaGen

Revisión completa de `src/metagen` sobre el commit `74f104e` (2025-03-21).
56 hallazgos con identificadores estables: los 46 de la revisión inicial más
`P-11` (al montar el CI), `F-25` (al medir el comportamiento real de las
metaheurísticas para `P-05`), `F-26` (al verificar `F-04`) y `F-33` (al medir
`A-01`). Los marcados **(R)** se reprodujeron
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
| `F-14`…`F-33` | 20 | Importantes: fallan en casos concretos o desperdician cómputo |
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
| **`mypy src` a cero** | 170 errores, no los 8 que se creían; trabajo fichero a fichero | `P-11` |
| **Implementar una búsqueda tabú de verdad** | Lo que había no lo era y se renombró a `HillClimbing` (`A-02`). La tabú canónica es un algoritmo nuevo, no un arreglo | ver abajo |
| **Estructuras dinámicas en los genéticos** | El cruce para longitudes variables no existe; es funcionalidad, no arreglo | `F-31` |

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
conclusiones**: `HillClimbing` empata o gana al resto en cinco de las nueve funciones y
suma **70/90** contra el muestreo aleatorio, segundo solo tras el memético (75/90).

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
| ⬜ | `F-27` | `p_isolation` significa lo contrario de lo que dice su nombre |
| ⬜ | `F-28` | Tres parámetros de CVOA no son los que sugiere el artículo |
| ⬜ | `F-29` | CVOA no reproduce entre procesos: itera conjuntos de soluciones |
| ✅ | `F-30` | La temperatura de SA no llega a enfriarse: es un paseo aleatorio |
| ⬜ | `F-31` | Los genéticos no admiten estructuras dinámicas: el cruce no existe |
| ✅ | `F-32` | El `alteration_limit` por defecto es absoluto, no relativo al dominio |
| ✅ | `F-33` | El cruce es uniforme: sobre variables reales no crea ningún valor nuevo |
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
| ⬜ | `P-11` | `mypy src` no pasa limpio: 11 errores en 9 ficheros |

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

### [ ] F-27 (R) · `p_isolation` significa lo contrario de lo que dice su nombre
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

### [ ] F-28 · Tres parámetros por defecto de CVOA no son los que sugiere el artículo
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

### [ ] F-29 (R) · CVOA no reproduce entre procesos: itera conjuntos de soluciones
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

### [ ] F-31 (R) · Los genéticos no admiten estructuras dinámicas: el cruce no está implementado
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
  - **Sigue sin resolverse la concurrencia**: las cepas de CVOA local corren en hilos que comparten los generadores, y los workers de Ray arrancan con su propio estado. Ambas firmas lo advierten en su docstring. Cerrarlo del todo exige un generador por instancia, que es la propuesta original de este hallazgo.

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

  Los tests de SA, GA y SSGA nacen `xfail(strict=True)` citando el hallazgo culpable: al arreglar `F-20`, `F-04` o `A-05` saltarán a `XPASS` avisando de que ya se puede quitar el marcador. Se comprobó además que estos resultados **son idénticos antes de `A-06`**, ejecutando el código en `1016e8a`: no son un efecto del cambio de semilla, que solo los ha hecho medibles.
- **[x] P-06** No hay `.github/workflows`. Con `mypy` ya configurado en `setup.cfg` y una suite que corre en 3 s, un workflow mínimo con matriz 3.10–3.12 captura buena parte de lo anterior. *Cerrado*: `.github/workflows/ci.yml` con dos jobs, `tests` (matriz 3.10–3.12, bloqueante) y `types` (`mypy src`, informativo hasta que cierre `P-11`). Dos cosas salieron a la luz al montarlo: la suite necesita `pytest-csv-params`, que no declara ni `install_requires` ni ningún extra (ver `P-08`), y **el CI no instala los extras a propósito**. Aquello valía cuando el test de `F-24` se saltaba con Ray instalado; al cerrar ese hallazgo se reescribió para bloquear Ray en un subproceso y ahora corre en todas partes. El único test que sigue necesitando Ray de verdad es el de `F-21`.
- **[x] P-07** `.gitignore:14` excluye `*.csv` y `*.xlsx`, y los parámetros de test son CSV en `test/test_parameters/`. Cualquier fichero nuevo se queda fuera del commit sin aviso. *Arreglo*: `!test/test_parameters/**/*.csv`. *Cerrado tal cual.* Comprobado que los 25 CSV que ya estaban versionados siguen estándolo —una regla de `.gitignore` no desversiona nada— y que uno nuevo **ya aparece en `git status`**, donde antes no salía. Test: `test_p07_los_csv_de_parametros_no_estan_ignorados`, con `git check-ignore`.
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
  `pytest-csv-params` esté declarado en alguna parte.
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
