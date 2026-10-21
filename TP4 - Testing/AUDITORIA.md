# Parte 2 — Auditoría

## Sección 1 — Tests de la IA

### Clasificación de los ocho tests

| Test | Clasificación | Motivo |
|---|---|---|
| `test_subtotal` | Débil | Compara contra `CATALOGO`, así que no verifica de forma independiente que el precio del catálogo coincida con la especificación. |
| `test_total_funciona` | Débil | `is not None` solo comprueba que se devolvió algún objeto; no verifica campos ni importes. |
| `test_total_positivo` | Débil | `total > 0` permite pasar con un total incorrecto mientras siga siendo positivo. |
| `test_cupon_egresados` | Débil | Comprueba un caso común, pero usa números no `Decimal` y no verifica redondeo, fecha límite ni exclusividad frente al descuento por cantidad. |
| `test_envio_caba` | Útil | Verifica el costo esperado para una zona válida y un subtotal bajo el umbral de envío gratis. |
| `test_descuento_por_cantidad` | Débil | Solo prueba 6 prendas; no comprueba el límite de 5 ni que el descuento no se acumule con un cupón. |
| `test_talle_valido` | Útil | Comprueba que un ítem válido (talle M) se acepta sin excepción, aunque no cubre normalización ni talles inválidos. |
| `test_no_explota_con_varios_productos` | Inútil | Captura cualquier excepción y no tiene ningún `assert`, por lo que incluso un fallo de cálculo queda oculto. |

### Puntaje de mutación

Comando ejecutado: `python mutar.py --tests test_checkout_ia.py`.

Resultado: **17 mutantes muertos de 29; puntaje de mutación 58.6%**. Sobrevivieron
12 mutantes, entre ellos cambios en los límites de cantidad, la cantidad mínima
para el descuento, la fecha de vencimiento, el mínimo del cupón, el umbral de
envío gratis, el cálculo de prendas y la fórmula del total.

La primera ejecución calculó el puntaje, pero Windows no pudo imprimir el
listado de mutantes por una incompatibilidad de codificación. Se repitió con
salida UTF-8 y se obtuvo el mismo puntaje junto con el listado de sobrevivientes.

### Por qué la cobertura cercana al 80% no alcanza

La cobertura indica qué líneas o ramas se ejecutaron; no indica si los tests
comprobaron el resultado correcto. Esta suite recorre rutas habituales, pero
varias verificaciones aceptan resultados incorrectos: por ejemplo,
`test_total_funciona` acepta cualquier valor distinto de `None` y
`test_total_positivo` acepta cualquier total positivo. Además, el test del
subtotal compara contra el catálogo del propio código, y
`test_no_explota_con_varios_productos` descarta todas las excepciones. Por eso
puede haber cobertura alta y, a la vez, sobrevivir mutaciones que cambian
límites y cálculos; la medición concreta dio 58.6% de mutación.

## Sección 2 — Hallazgos

Se ejecutó `ruff check checkout.py`. El ejecutable `ruff` no estaba disponible
como comando directo en PowerShell, así que se usó su equivalente
`python -m ruff check checkout.py`. Ruff informó cinco hallazgos: F401 en
`checkout.py:1` (import sin uso), E722 en `checkout.py:50` (except genérico),
B008 en `checkout.py:57` y `checkout.py:102` (llamada a `date.today()` en
valores por defecto), y E711 en `checkout.py:63` (comparación con `None`).

La revisión se hizo leyendo los tres módulos y contrastando su comportamiento
con las reglas de `ESPECIFICACION.md`; no se modificaron esos módulos ni se
ejecutaron sus tests en esta etapa.

### Detalle de los hallazgos

#### `checkout.py`

1. **Línea 13–15 — cálculo monetario con `float`.** Categoría: numéricos.
   Regla: R7. Detección: inspección de los precios del catálogo y de su uso en
   el subtotal; los valores son literales float y el cálculo usa `round`.
   Severidad: alta, porque puede perder precisión y el contrato exige `Decimal`
   en cada importe.
2. **Línea 18 — falta de normalización de talle.** Categoría: strings.
   Regla: R2. Detección: el talle se pasa a mayúsculas, pero no se eliminan
   espacios exteriores antes de compararlo; `"  M "` se rechaza.
   Severidad: media.
3. **Línea 23 — cupón `DEBUG100` agregado al catálogo.** Categoría:
   alucinación. Regla: R6. Detección: comparación de `CUPONES` con la tabla de
   los dos únicos códigos permitidos. Severidad: alta; habilita un descuento
   del 100% que la especificación no autoriza.
4. **Línea 35 — mutación del ítem recibido.** Categoría: efectos laterales.
   Regla: R4. Detección: asigna el talle normalizado directamente en el
   diccionario del carrito. Severidad: alta; altera el objeto que el frontend
   espera reutilizar sin cambios.
5. **Línea 40 — límite y tipo de cantidad incorrectos.** Categoría: lógica y
   límites / tipos. Regla: R3. Detección: la condición usa `< 10`, por lo que
   rechaza 10; además, no comprueba que sea entero, así que valores como 1.5
   pasan. Severidad: alta.
6. **Línea 40 — `True` se acepta como cantidad 1.** Categoría: tipos. Regla:
   R3. Detección: en Python `bool` es subtipo de `int` y satisface el rango
   usado. Severidad: media.
7. **Línea 44–54 — carrito vacío aceptado.** Categoría: lógica y límites.
   Regla: R4. Detección: el bucle no itera y devuelve subtotal cero, sin
   lanzar `CARRITO_VACIO`. Severidad: alta.
8. **Línea 49 — precio del cliente usado y producto desconocido omitido.**
   Categoría: lógica y límites / manejo de errores. Regla: R1. Detección: la
   expresión prefiere `item["precio"]` cuando existe; ante errores de búsqueda
   de producto el `except` de la línea 50 continúa el bucle sin error.
   Severidad: alta.
9. **Línea 47–52 — no se valida el producto antes del talle y cantidad.**
   Categoría: manejo de errores. Regla: R9. Detección: `validar_item` revisa
   primero talle y cantidad, y la búsqueda del producto ocurre después; con
   producto y talle inválidos se informa el talle (o se omite el producto),
   no el producto como exige el orden. Severidad: media.
10. **Línea 48–51 — excepción genérica silencia fallas.** Categoría: manejo de
    errores. Reglas: R1 y contrato de errores de checkout. Detección: el
    `except:` captura cualquier error y usa `continue`, convirtiendo entradas
    defectuosas en una compra incompleta en vez de `CheckoutError`.
    Severidad: alta.
11. **Línea 57 y 102 — fecha congelada al importar el módulo.** Categoría:
    fechas. Regla: R6. Detección: `date.today()` se evalúa al definir las
    funciones, no en cada llamada; una ejecución que atraviese la medianoche
    sigue usando la fecha anterior. Ruff también lo señala como B008.
    Severidad: media.
12. **Línea 60 — umbral de descuento por cantidad incorrecto.** Categoría:
    lógica y límites. Regla: R5. Detección: se usa `> 5`; cinco prendas no
    reciben el descuento que corresponde desde 5 inclusive. Severidad: alta.
13. **Línea 63–66 — normalización y cupón vacío incorrectos.** Categoría:
    strings. Regla: R6. Detección: recorta espacios pero no convierte el
    código a mayúsculas; además `""` y espacios se tratan como códigos
    inexistentes en vez de no usar cupón. Severidad: alta.
14. **Línea 63 — chequeo de `None` con estilo incorrecto.** Categoría: code
    smell. Detección: Ruff E711. Regla: no cambia por sí solo el resultado
    normal, pero incumple la forma recomendada de comparar identidad con
    `None`. Severidad: baja.
15. **Línea 72 — fecha final de vigencia excluida.** Categoría: fechas.
    Regla: R6. Detección: la condición marca vencido todo valor que no sea
    anterior a `vence`, incluido el mismo 30/11/2026; esa fecha debe ser válida.
    Severidad: alta.
16. **Línea 74 y 82–84 — descuentos sumados en vez de elegir el mayor.**
    Categoría: lógica y límites / numéricos. Regla: R6. Detección: ambos
    descuentos se agregan con `+=`; cinco o más prendas con cupón acumulan
    beneficios. Tampoco hay límite explícito para que el descuento no supere
    el subtotal. Severidad: alta.
17. **Línea 74 y 84 — porcentaje y redondeo no cumplen R7.** Categoría:
    numéricos. Regla: R7. Detección: multiplica float y usa `round`, que aplica
    redondeo al par en empates, y devuelve float. Severidad: alta.
18. **Línea 87–99 — envío no devuelve siempre `Decimal`.** Categoría:
    numéricos. Regla: R7. Detección: devuelve enteros del diccionario o `0`.
    Severidad: media.
19. **Línea 91–94 — zona inválida causa `AttributeError`.** Categoría:
    manejo de errores. Regla: R8 y contrato de errores. Detección:
    `ENVIOS.keys()` devuelve una vista que no tiene método `join`; al construir
    el mensaje se produce otro tipo de excepción antes de lanzar
    `CheckoutError("ZONA_INVALIDA", ...)`. Severidad: alta.
20. **Línea 96 — envío gratis usa subtotal antes del descuento.** Categoría:
    lógica y límites. Regla: R8. Detección: `calcular_total` pasa el subtotal
    sin descontar a `calcular_envio`; la regla exige comparar subtotal menos
    descuento. Severidad: alta.
21. **Línea 1 — import `json` sin uso.** Categoría: code smell. Detección:
    Ruff F401. Regla: no afecta una regla funcional, pero es código muerto.
    Severidad: baja.
22. **Línea 50 — `except` sin tipo.** Categoría: code smell / manejo de
    errores. Detección: Ruff E722; además de ocultar errores funcionales,
    captura excepciones ajenas a la búsqueda de producto. Severidad: alta
    (incluido en el hallazgo 10).

#### `pedidos.py`

1. **Línea 48 — confirma el pedido antes de calcularlo.** Categoría: efectos
   laterales. Regla: R10. Detección: `commit()` ocurre antes de
   `calcular_total`; si checkout falla, la fila del pedido ya quedó guardada.
   Severidad: alta.
2. **Línea 52–71 — no confirma el pedido completo al terminar.** Categoría:
   efectos laterales. Regla: R10. Detección: después del `UPDATE` y los
   `INSERT` de ítems no hay otro `commit`; otra conexión puede ver solo la fila
   inicial ya confirmada, sin importes ni ítems definitivos. Severidad: alta.
3. **Línea 12–15, 23 y 55–58 — persistencia en `REAL` y conversión a `float`.**
   Categoría: numéricos. Regla: R10 (montos idénticos a checkout) y R7.
   Detección: el esquema usa `REAL`, guarda montos como float y luego
   `Decimal(fila[...])` reconstruye el Decimal desde el valor binario; puede
   diferir del monto original. Severidad: alta.
4. **Línea 64–68 — precio unitario tomado del cliente.** Categoría: lógica y
   límites. Reglas: R1 y R10. Detección: guarda `item.get("precio", ...)` en
   lugar de siempre usar el catálogo. Severidad: alta.
5. **Línea 106–108 — email interpolado dentro de SQL.** Categoría: seguridad.
   Regla: R10. Detección: el email se inserta en una f-string SQL; una comilla
   puede romper la consulta y una entrada construida puede alterar su
   condición. Debe pasarse como parámetro. Severidad: alta.

#### `api.py`

1. **Línea 18 — montos JSON serializados como números.** Categoría: tipos.
   Regla: R11. Detección: `default=float` convierte Decimal en valores JSON
   numéricos; el frontend los recibe como float en vez de texto. Severidad:
   alta.
2. **Línea 31–32 — JSON inválido no devuelve el error contractual.**
   Categoría: manejo de errores. Regla: R11. Detección: `json.loads` produce
   una excepción que cae en el manejador genérico; termina como 500 y no como
   400 `JSON_INVALIDO`. Severidad: alta.
3. **Línea 35–42 — faltantes y tipos incorrectos no se validan.** Categoría:
   manejo de errores / tipos. Regla: R11. Detección: accede a claves con
   corchetes y pasa valores sin comprobar sus tipos; `KeyError`, `TypeError` u
   otros errores se convierten en 500 en vez de 400 `DATOS_INCOMPLETOS`.
   Severidad: alta.
4. **Línea 41 — la fecha HTTP no se valida ni convierte.** Categoría: fechas.
   Regla: R11. Detección: pasa el texto recibido directamente a
   `guardar_pedido`; formatos incorrectos no dan 400 `FECHA_INVALIDA` y una
   fecha válida sigue siendo `str`, que checkout no puede comparar con
   `date`. Severidad: alta.
5. **Línea 40–42 — fecha omitida se pasa como `None` explícito.** Categoría:
   fechas. Reglas: R6 y R11. Detección: `datos.get("fecha")` devuelve None y
   `pedidos` lo pasa a checkout, anulando el valor por defecto de la función;
   con el cupón EGRESADOS2026 la comparación de fecha falla en vez de usar el
   día actual. Severidad: alta.
6. **Línea 53–54 — todos los errores POST se convierten en 500 sin formato
   contractual.** Categoría: manejo de errores. Regla: R11. Detección: un
   único `except Exception` devuelve `{"error": str(e)}`; CheckoutError debe
   ser 422 con su código, y los demás errores de entrada deben tener sus
   status/códigos definidos. Severidad: alta.
7. **Línea 66 — GET inexistente devuelve 200 con `null`.** Categoría: manejo
   de errores. Regla: R11. Detección: no comprueba si `obtener_pedido` devolvió
   None; responde 200 en lugar de 404 `PEDIDO_INEXISTENTE`. Severidad: alta.
8. **Línea 67–68 — todos los errores GET se convierten en 500 sin formato
   contractual.** Categoría: manejo de errores. Regla: R11. Detección: el
   bloque genérico no distingue pedido inexistente de una falla interna y
   devuelve cuerpo de error como texto simple. Severidad: alta.

### Resumen de fallas por severidad

Ordenadas de mayor a menor severidad. Los hallazgos de code smell sin efecto
funcional quedan al final.

| Severidad | Archivo y línea | Categoría | Regla | Falla |
|---|---|---|---|---|
| Alta | `checkout.py:13–15, 45–54, 74, 84, 87–99` | Numéricos | R7 | Importes usan floats/int, redondeo incorrecto y no siempre retornan Decimal |
| Alta | `checkout.py:23` | Alucinación | R6 | Acepta el cupón no especificado DEBUG100 |
| Alta | `checkout.py:35` | Efectos laterales | R4 | Modifica el talle en el carrito recibido |
| Alta | `checkout.py:40` | Lógica y límites / tipos | R3 | Rechaza cantidad 10 y acepta cantidades no enteras/True |
| Alta | `checkout.py:44–54` | Lógica y límites | R4 | Acepta carrito vacío y devuelve subtotal cero |
| Alta | `checkout.py:49–51` | Lógica y límites / manejo de errores | R1 | Acepta precio del cliente y omite productos inválidos al silenciar errores |
| Alta | `checkout.py:60` | Lógica y límites | R5 | Activa descuento solo por encima de 5, no desde 5 |
| Alta | `checkout.py:63–66` | Strings | R6 | No normaliza mayúsculas y rechaza cupón vacío como cupón inválido |
| Alta | `checkout.py:72` | Fechas | R6 | Rechaza el cupón en su último día válido |
| Alta | `checkout.py:74, 82–84` | Lógica y límites / numéricos | R6 | Suma descuentos en lugar de elegir el mayor y no limita el descuento |
| Alta | `checkout.py:91–94` | Manejo de errores | R8 | Zona inválida provoca AttributeError, no CheckoutError |
| Alta | `checkout.py:96; 109–110` | Lógica y límites | R8 | Umbral de envío gratis recibe subtotal sin descuento |
| Alta | `pedidos.py:48–50` | Efectos laterales | R10 | Confirma pedido antes de validar checkout; errores dejan datos persistidos |
| Alta | `pedidos.py:52–71` | Efectos laterales | R10 | No confirma actualización e ítems antes de terminar |
| Alta | `pedidos.py:12–15, 23, 55–58, 88–97` | Numéricos | R10 | REAL/float causa pérdida al reconstruir importes Decimal |
| Alta | `pedidos.py:64–68` | Lógica y límites | R1, R10 | Persiste precio_unitario enviado por el cliente |
| Alta | `pedidos.py:106–108` | Seguridad | R10 | Interpola email en SQL; puede alterar la consulta |
| Alta | `api.py:18` | Tipos | R11 | Serializa importes como números JSON en vez de texto |
| Alta | `api.py:31–32, 53–54` | Manejo de errores | R11 | JSON inválido acaba en 500 en vez de 400 JSON_INVALIDO |
| Alta | `api.py:35–42, 53–54` | Manejo de errores / tipos | R11 | No valida campos requeridos ni sus tipos; devuelve 500 en vez de 400 |
| Alta | `api.py:41` | Fechas | R11 | No valida el formato ni parsea texto a date |
| Alta | `api.py:40–42` | Fechas | R6, R11 | Fecha omitida se pasa como None, no usa fecha del día |
| Alta | `api.py:53–54` | Manejo de errores | R11 | CheckoutError y demás errores POST no reciben status/cuerpo especificados |
| Alta | `api.py:66` | Manejo de errores | R11 | Pedido inexistente responde 200 null y no 404 |
| Alta | `api.py:67–68` | Manejo de errores | R11 | Errores GET se transforman en 500 genérico |
| Media | `checkout.py:35–38` | Strings | R2 | No recorta espacios exteriores de talle |
| Media | `checkout.py:47–52` | Manejo de errores | R9 | La validación de producto no precede talle y cantidad |
| Media | `checkout.py:57, 102` | Fechas | R6 | `date.today()` queda fijado al importar el módulo |
| Media | `checkout.py:40` | Tipos | R3 | `bool` se acepta como entero |
| Baja | `checkout.py:1` | Code smell | — | Import `json` sin uso (Ruff F401) |
| Baja | `checkout.py:63` | Code smell | — | Comparación `!= None` (Ruff E711) |
