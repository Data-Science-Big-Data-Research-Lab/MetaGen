# Auditoría de MetaGen

Revisión completa de `src/metagen` sobre el commit `74f104e` (2025-03-21).
53 hallazgos con identificadores estables: los 46 de la revisión inicial más
`P-11` (al montar el CI), `F-25` (al medir el comportamiento real de las
metaheurísticas para `P-05`) y `F-26` (al verificar `F-04`). Los marcados **(R)** se reprodujeron
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
| `F-14`…`F-30` | 17 | Importantes: fallan en casos concretos o desperdician cómputo |
| `A-01`…`A-12` | 12 | Algoritmia y diseño: decisiones discutibles, no bugs |
| `P-01`…`P-11` | 11 | Empaquetado, tests y documentación |

Orden sugerido de ataque:

1. Red de seguridad: `A-06` (semilla), `P-04`, `P-05`, `P-06` (CI).
2. Los cinco que cambian resultados en silencio: `F-01`, `F-02`, `F-03`, `F-04`, `F-14`.
3. Dejar `Structure` utilizable: `F-05`, `F-06`, `F-19`, `F-18`.
4. Higiene de librería: `F-07`, `F-12`, `F-13`, `F-21`, `F-24`, `A-11`, `A-12`.
5. Revisión de CVOA: `F-08`, `F-09`, `F-10`, `F-23`, `A-09`, `P-10`.
6. Conversación de fondo: `A-01`, `A-02`, `A-03`.

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
| ⬜ | `F-30` | La temperatura de SA no llega a enfriarse: es un paseo aleatorio |
| ⬜ | `A-01` | Sin selección de padres: todos los cruces usan la misma pareja |
| ⬜ | `A-02` | La búsqueda tabú es en realidad hill climbing |
| ⬜ | `A-03` | El vecindario tabú se genera en cadena, no alrededor de la solución |
| ⬜ | `A-04` | Random Search descarta el último individuo, no el peor |
| ⬜ | `A-05` | SSGA sustituye por igualdad de valor, no por identidad |
| ✅ | `A-06` | No había forma de fijar la semilla |
| ⬜ | `A-07` | GA, SSGA y memético no validan que el dominio use `GAConnector` |
| ⬜ | `A-08` | Los reales rechazan enteros y los enteros aceptan booleanos |
| ⬜ | `A-09` | CVOA y las herramientas están duplicados, y ya divergen |
| ⬜ | `A-10` | El elitismo depende de que cada subclase se acuerde |
| ✅ | `A-11` | El logger parchea `logging` globalmente y acumula handlers |
| ✅ | `A-12` | TensorBoard se activa solo por estar instalado, sin poder apagarlo |
| ⬜ | `P-01` | Licencia contradictoria: MIT en PyPI frente a GPLv3 en el código |
| ✅ | `P-02` | La versión mínima de Python se contradice en tres sitios |
| ✅ | `P-03` | Enlaces y badges apuntan al repositorio antiguo |
| ✅ | `P-04` | `pytest test` no llegaba a recolectar sin los extras opcionales |
| ✅ | `P-05` | Los tests de metaheurísticas no comprobaban nada útil |
| ✅ | `P-06` | No había integración continua |
| ✅ | `P-07` | `.gitignore` excluye los CSV de parámetros de test |
| ⬜ | `P-08` | Los extras de `setup.cfg` usan `;`, que PEP 508 lee como otra cosa |
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

### [ ] F-30 (R) · La temperatura de SA no llega a enfriarse: es un paseo aleatorio
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
  - **La garantía solo valía dentro del mismo proceso hasta cerrar `F-26`.** Los tests de este hallazgo comprobaban dos ejecuciones seguidas en la misma sesión de Python, y ahí el fallo era invisible: `Solution.mutate` recorría un `set` de nombres de variable, cuyo orden depende de hashes que Python aleatoriza en cada arranque. Reproducibilidad entre ejecuciones distintas: ver `F-26`.
  - **Los siete helpers de la suite de regresión sembraban con `random.seed()`** y dejaron de ser deterministas al hacer este cambio: `test_f05_append_conserva_el_valor` llegó a pasar por azar (el entero aleatorio salió 7). Ahora siembran con `set_seed()`.
  - **NumPy cambia de algoritmo**: `default_rng()` (PCG64) en vez del Mersenne Twister de `np.random`. La secuencia de TPE ya no es la de la `0.2.0` publicada.
  - **Sigue sin resolverse la concurrencia**: las cepas de CVOA local corren en hilos que comparten los generadores, y los workers de Ray arrancan con su propio estado. Ambas firmas lo advierten en su docstring. Cerrarlo del todo exige un generador por instancia, que es la propuesta original de este hallazgo.

  Tests: `test_a06_la_misma_semilla_reproduce_la_ejecucion`, `test_a06_semillas_distintas_dan_ejecuciones_distintas`, `test_a06_metagen_no_toca_el_generador_global_del_usuario`.
- **[ ] A-07** `ga`, `ssga`, `mm` — no validan que el dominio use `GAConnector`: con un `Domain()` normal mueren en la primera iteración con `AttributeError: 'Solution' object has no attribute 'crossover'`.
- **[ ] A-08** `domain/core.py:219, 140` — `RealDefinition` exige `isinstance(value, float)` (rechaza `1` y `np.float32`) y `IntegerDefinition` acepta `bool`. *Propuesta*: `numbers.Real` excluyendo `bool`, normalizando al tipo nativo.
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
- **[ ] A-10** `base.py:196, 247` — `_iterate` hace `self.best_solution = best_individual` sin comparar, así que el elitismo depende de que cada subclase se acuerde; y `stopping_criterion()` devuelve `False` por defecto (bucle infinito si una subclase lo olvida).
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

- **[ ] P-01** `setup.cfg:14` — clasificador `MIT License` frente a un `LICENSE` GPL-3.0 y 55 cabeceras GPLv3. PyPI anuncia MIT. *Arreglo*: unificar y añadir `license` / `license_files`.
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

  Los tests de SA, GA y SSGA nacen `xfail(strict=True)` citando el hallazgo culpable: al arreglar `F-20`, `F-04` o `A-05` saltarán a `XPASS` avisando de que ya se puede quitar el marcador. Se comprobó además que estos resultados **son idénticos antes de `A-06`**, ejecutando el código en `1016e8a`: no son un efecto del cambio de semilla, que solo los ha hecho medibles.
- **[x] P-06** No hay `.github/workflows`. Con `mypy` ya configurado en `setup.cfg` y una suite que corre en 3 s, un workflow mínimo con matriz 3.10–3.12 captura buena parte de lo anterior. *Cerrado*: `.github/workflows/ci.yml` con dos jobs, `tests` (matriz 3.10–3.12, bloqueante) y `types` (`mypy src`, informativo hasta que cierre `P-11`). Dos cosas salieron a la luz al montarlo: la suite necesita `pytest-csv-params`, que no declara ni `install_requires` ni ningún extra (ver `P-08`), y **el CI no instala los extras a propósito**. Aquello valía cuando el test de `F-24` se saltaba con Ray instalado; al cerrar ese hallazgo se reescribió para bloquear Ray en un subproceso y ahora corre en todas partes. El único test que sigue necesitando Ray de verdad es el de `F-21`.
- **[x] P-07** `.gitignore:14` excluye `*.csv` y `*.xlsx`, y los parámetros de test son CSV en `test/test_parameters/`. Cualquier fichero nuevo se queda fuera del commit sin aviso. *Arreglo*: `!test/test_parameters/**/*.csv`. *Cerrado tal cual.* Comprobado que los 25 CSV que ya estaban versionados siguen estándolo —una regla de `.gitignore` no desversiona nada— y que uno nuevo **ya aparece en `git status`**, donde antes no salía. Test: `test_p07_los_csv_de_parametros_no_estan_ignorados`, con `git check-ignore`.
- **[ ] P-08** Los extras de `setup.cfg` usan `;`, que en PEP 508 es el separador de **marcadores de entorno**, no de requisitos: `tensorboard = tensorboard; tensorboardX` se lee como «tensorboard, si el marcador tensorboardX». Comprobar qué instala `pip install pymetagen-datalabupo[all]`. Además hay tres `requirements*.txt` con criterios solapados. *Arreglo*: un requisito por línea y migrar la metadata a `pyproject.toml`.
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
- **[ ] P-11** `mypy src` **no pasa limpio**: 8 errores en 8 ficheros con `mypy 1.1.1`, 7 con la versión que instala el CI. Eran 14 al abrir el hallazgo. El proyecto se desarrolló con la condición de usar tipos, así que esto es deuda declarada, no higiene opcional; por eso el job `types` del CI nace informativo (`continue-on-error: true`).

  **El contador es la barra de progreso de la auditoría**, y va bajando solo al cerrar
  otros hallazgos:

  | Al cerrar | Errores que se lleva | Contador |
  |---|---|---|
  | — (apertura) | | 14 |
  | `F-01` | `types/base.py:117, 119, 122` | 11 |
  | `F-05` | `types/structure.py:202` | 10 |
  | `A-11` | `metagen_logger.py:29, 69, 70` | 7 |

  Lo que queda, y de quién es:

  | Causa | Errores | Se cierra con |
  |---|---|---|
  | `metaheuristics/base.py`, `cvoa_local.py`, `cvoa_distributed.py` — `.get_fitness()` sobre `Any \| None` | 3 | Familia `F-14` / `A-10` |
  | `base_solution.py`, `real.py`, `integer.py` — `Optional` implícito: `= None` en un parámetro no opcional | 3 | Propio de `P-11` |
  | `tpe/tpe.py` — falta anotar `solution_history` | 1 | Propio de `P-11` |
  | `connector/connector.py:91` — asignación incompatible en `get_type` | 1 | Propio de `P-11`, **solo con mypy 1.1.1** |

  **Ojo con ese último**: no lo da la versión de mypy que instala el CI, así que el
  contador local y el del CI difieren en uno. No es una discrepancia del código.

  *Arreglo*: cerrar los hallazgos de la tabla, resolver los cuatro o cinco restantes
  (`x: int | None = None` y una anotación en TPE) y, cuando `mypy src` salga a cero,
  **quitar el `continue-on-error: true` del job `types`** para que la comprobación
  pase a bloquear. Conviene hacerlo junto con `P-09` (`py.typed`), que hoy hace que
  mypy trate `metagen` como `Any` desde fuera del paquete.
