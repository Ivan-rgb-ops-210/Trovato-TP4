# Parte 1 — Casos de caja negra

Casos derivados de `ESPECIFICACION.md`. Salvo indicación contraria, los demás datos son válidos. Los importes monetarios esperados son `Decimal` con dos decimales.

## R1 — Catálogo y precios

Particiones: productos válidos (`buzo`, `remera`, `campera`), inexistente y precio enviado por el cliente (ignorado). El nombre debe coincidir exactamente y estar en minúscula.

| Caso | Entrada | Resultado esperado |
|---|---|---|
| R1.1 | `buzo`, M, cantidad 1 | Subtotal `24999.90` |
| R1.2 | `remera`, M, cantidad 1, `precio: 1` | Subtotal `11999.50` |
| R1.3 | `campera`, M, cantidad 1 | Subtotal `47999.99` |
| R1.4 | `gorra`, M, cantidad 1 | `PRODUCTO_INEXISTENTE` |
| R1.5 | `Buzo`, M, cantidad 1 | `PRODUCTO_INEXISTENTE` |

## R2 — Talles

Particiones: XS, S, M, L, XL, XXL válidos sin distinguir mayúsculas ni espacios exteriores; otros valores inválidos. XS y XXL son los extremos válidos; no se ignoran espacios interiores.

| Caso | Entrada | Resultado esperado |
|---|---|---|
| R2.1 | talle `XS` | Válido |
| R2.2 | talle `xxl` | Válido |
| R2.3 | talle `  M ` | Válido |
| R2.4 | talle vacío | `TALLE_INVALIDO` |
| R2.5 | talle `XXXL` o `X XL` | `TALLE_INVALIDO` |

## R3 — Cantidad

Particiones: entero dentro del rango, menor, mayor y valor no entero. Límites: 1 y 10 son válidos; 0 y 11 son inválidos.

| Caso | Entrada | Resultado esperado |
|---|---|---|
| R3.1 | cantidad `1` | Válido |
| R3.2 | cantidad `10` | Válido |
| R3.3 | cantidad `0` o `11` | `CANTIDAD_INVALIDA` |
| R3.4 | cantidad `1.5`, `"2"` o `True` | `CANTIDAD_INVALIDA` |

## R4 — Carrito e inmutabilidad

Particiones: carrito vacío, con un ítem y con varios. Ninguna función modifica el objeto recibido, incluso al normalizar valores o ignorar claves adicionales. Límites: longitud 0 inválida; longitud 1 válida.

| Caso | Entrada | Resultado esperado |
|---|---|---|
| R4.1 | carrito `[]` | `CARRITO_VACIO` |
| R4.2 | un buzo M, cantidad 1 | Subtotal `24999.90` |
| R4.3 | un buzo M y una remera S, ambos cantidad 1 | Subtotal `36999.40` |
| R4.4 | talle `  m ` y `precio: 1` | Calcula con precio de catálogo y conserva exactamente el carrito original |

## R5 — Descuento por cantidad

Particiones: total de prendas menor que 5 o igual/mayor a 5; se suman las cantidades de todos los ítems. Límite: 4 no activa descuento; 5 activa el 10%.

| Caso | Entrada | Resultado esperado |
|---|---|---|
| R5.1 | 4 remeras | Descuento `0.00` |
| R5.2 | 5 remeras, subtotal `59997.50` | Descuento `5999.75` |
| R5.3 | 2 remeras y 3 buzos | Descuento del 10% del subtotal: `9899.87` |

## R6 — Cupones

Particiones: sin cupón; porcentaje vigente o vencido; cupón fijo que cumple o no el mínimo; código desconocido. Se ignoran mayúsculas y espacios exteriores. Límites: EGRESADOS2026 vence después del 30/11/2026 inclusive; BIENVENIDA requiere `20000.00`; descuento máximo igual al subtotal. Sin fecha se usa el día de la llamada. Se aplica el mayor entre cupón y descuento por cantidad, sin acumularlos.

| Caso | Entrada | Resultado esperado |
|---|---|---|
| R6.1 | cupón `None`, vacío o espacios | Sin descuento de cupón |
| R6.2 | `" egresados2026 "`, subtotal `11999.50`, fecha 30/11/2026 | Descuento `1799.93` |
| R6.3 | EGRESADOS2026, fecha 01/12/2026 | `CUPON_VENCIDO` |
| R6.4 | BIENVENIDA, subtotal `19999.99` | `CUPON_MINIMO_NO_ALCANZADO` |
| R6.5 | BIENVENIDA, subtotal `20000.00` | Descuento `3000.00` |
| R6.6 | código `DESCONOCIDO` | `CUPON_INVALIDO` |
| R6.7 | 5 prendas, descuento cantidad `5999.75`, BIENVENIDA | Descuento `5999.75`, no `8999.75` |

Con los únicos cupones definidos, ninguna entrada válida produce un descuento
mayor que el subtotal: el porcentaje es 15%, el descuento fijo requiere un
subtotal mínimo de `20000.00` y el descuento por cantidad es 10%. Por eso no
hay una entrada válida para una prueba de caja negra que fuerce el límite de
descuento de R6; se conserva como invariante a verificar al implementar.

## R7 — Dinero y redondeo

Particiones: importes exactos al centavo y porcentajes que producen fracciones de centavo. Todos los importes son `Decimal`, nunca `float`. El medio centavo redondea comercialmente hacia arriba.

| Caso | Entrada | Resultado esperado |
|---|---|---|
| R7.1 | 15% de `11999.50` | `1799.93` (`1799.925` redondea arriba) |
| R7.2 | 1 buzo M, envío CABA, sin cupón | `subtotal: Decimal("24999.90")`, `descuento: Decimal("0.00")`, `envio: Decimal("2500.00")`, `total: Decimal("27499.90")` |

## R8 — Envío

Particiones: zonas CABA, GBA, INTERIOR, RETIRO; zona inexistente; envío normal o gratis. Se ignoran mayúsculas y espacios exteriores. Límites: base descontada `59999.99` paga envío; `60000.00` lo hace gratuito.

| Caso | Entrada | Resultado esperado |
|---|---|---|
| R8.1 | `" caba "`, base `10000.00` | Envío `2500.00` |
| R8.2 | GBA, base `10000.00` | Envío `4000.00` |
| R8.3 | INTERIOR, base `10000.00` | Envío `6500.00` |
| R8.4 | RETIRO, base `10000.00` | Envío `0.00` |
| R8.5 | CABA, base `59999.99` | Envío `2500.00` |
| R8.6 | CABA, base `60000.00` | Envío `0.00` |
| R8.7 | zona SUR | `ZONA_INVALIDA` |

## R9 — Total y orden de validación

Particiones: compra válida y datos con errores múltiples. Orden: carrito vacío; por ítem y en orden producto, talle, cantidad; cupón; zona.

| Caso | Entrada | Resultado esperado |
|---|---|---|
| R9.1 | 2 buzos, CABA, sin cupón | Subtotal `49999.80`, descuento `0.00`, envío `2500.00`, total `52499.80` |
| R9.2 | carrito vacío, cupón y zona inválidos | `CARRITO_VACIO` |
| R9.3 | producto y talle inválidos en el mismo ítem | `PRODUCTO_INEXISTENTE` |
| R9.4 | segundo ítem con talle y cantidad inválidos | `TALLE_INVALIDO` |
| R9.5 | compra válida, cupón y zona inválidos | `CUPON_INVALIDO` |
| R9.6 | compra y cupón válidos, zona inválida | `ZONA_INVALIDA` |

## R10 — Persistencia SQLite

Particiones: pedido válido visible desde otra conexión; error sin escrituras; importes/precios exactos; normalización; id existente/ausente; búsqueda por email sin distinguir mayúsculas o espacios, ordenada; email hostil tratado como dato. Al fallar checkout deben quedar cero pedidos e ítems; los pedidos se devuelven del más reciente al más antiguo.

| Caso | Entrada | Resultado esperado |
|---|---|---|
| R10.1 | En archivo temporal, guardar email `ana@mail.com`, zona CABA y carrito `[remera M × 1]`; abrir segunda conexión y consultar id devuelto | La segunda conexión encuentra el pedido con su ítem y valores completos |
| R10.2 | Guardar carrito `[gorra M × 1]` | Propaga `CheckoutError` con `PRODUCTO_INEXISTENTE`; la base conserva 0 pedidos y 0 ítems |
| R10.3 | Guardar `[remera M × 1, precio: 1]` | precio unitario `Decimal("11999.50")`; subtotal, descuento, envío y total son Decimal idénticos a `calcular_total` |
| R10.4 | email `" Ana@Mail.com "`, zona `" caba "`, talle `" m "`, cupón `" bienvenida "` | email `ana@mail.com`; zona `CABA`, talle `M`, cupón `BIENVENIDA` |
| R10.5 | Guardar pedido con cupón `"  "` | El campo cupón devuelto es `None` |
| R10.6 | Consultar id `999` cuando no existe | Devuelve `None` |
| R10.7 | Guardar dos pedidos para `ana@mail.com` y `" ANA@MAIL.COM "`; llamar `pedidos_de(con, " Ana@Mail.com ")` | Devuelve ambos pedidos, primero el segundo que se guardó |
| R10.8 | Guardar pedido con email `' OR 1=1 --`; llamar `pedidos_de` con ese mismo email | Devuelve solo el pedido de ese email literal; no altera la consulta |

## R11 — API HTTP

Particiones: POST válido, GET existente, JSON inválido, campos faltantes o con tipo incorrecto, fecha inválida, error de negocio, pedido inexistente y ruta inexistente. Errores con `error.code` y `error.message`; nunca 500. Los importes viajan como texto. Límite de fecha: formato `AAAA-MM-DD`; vigencia del cupón inclusive hasta 30/11/2026.

| Caso | Entrada | Resultado esperado |
|---|---|---|
| R11.1 | POST `/api/v1/pedidos` con `{"email":"ana@mail.com","zona":"CABA","carrito":[{"producto":"remera","talle":"M","cantidad":1}]}` | 201; `id` numérico y `subtotal`, `descuento`, `envio`, `total` strings (`"11999.50"`, `"0.00"`, `"2500.00"`, `"14499.50"`) |
| R11.2 | GET `/api/v1/pedidos/{id}` usando el id devuelto por R11.1 | 200; pedido completo y todos los importes en texto |
| R11.3 | POST con cuerpo crudo `esto no es JSON` | 400, `JSON_INVALIDO`, con objeto `error` que contiene `code` y `message` |
| R11.4 | Tres POST separados, cada uno sin uno de `email`, `zona` o `carrito` | En cada caso 400, `DATOS_INCOMPLETOS` |
| R11.5 | POST con `email: 7`, `zona: 7` o `carrito: {}` (una variante por request) | En cada caso 400, `DATOS_INCOMPLETOS` |
| R11.6 | POST válido salvo fecha `30/11/2026` | 400, `FECHA_INVALIDA` |
| R11.7 | POST con carrito `[{"producto":"gorra","talle":"M","cantidad":1}]` | 422, `PRODUCTO_INEXISTENTE` |
| R11.8 | GET `/api/v1/pedidos/999` cuando ese id no existe | 404, `PEDIDO_INEXISTENTE` |
| R11.9 | GET `/api/v1/otra` y POST `/api/v1/otra` | Cada request devuelve 404, `RUTA_INEXISTENTE` |
| R11.10 | Cada error de R11.3–R11.9 | JSON con `error.code` y `error.message`; ningún caso devuelve 500 |
