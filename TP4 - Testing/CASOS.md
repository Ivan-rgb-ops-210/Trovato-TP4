# Parte 1 — Casos de caja negra

Casos derivados exclusivamente de `ESPECIFICACION.md`. Los importes se expresan como `Decimal` y con dos decimales cuando corresponde. En las tablas, cada fila representa una partición o un límite que debe comprobarse.

## R1 — Catálogo y precios

| Partición / límite | Entrada | Resultado esperado |
|---|---|---|
| Válida: cada producto del catálogo | Un ítem válido de `buzo`, `remera` o `campera`, cantidad 1 | Precios unitarios de catálogo: `24999.90`, `11999.50` y `47999.99`, respectivamente. |
| Válida: el cliente envía precio propio | `{"producto":"buzo","talle":"M","cantidad":1,"precio":1}` | El precio enviado se ignora; subtotal `24999.90`. |
| Inválida: producto fuera del catálogo | `{"producto":"gorra","talle":"M","cantidad":1}` | `CheckoutError` con código `PRODUCTO_INEXISTENTE`. |
| Límite de escritura exacta | `producto="BUZO"` | `PRODUCTO_INEXISTENTE`; el nombre debe coincidir exactamente en minúscula. |

## R2 — Talles

| Partición / límite | Entrada | Resultado esperado |
|---|---|---|
| Válida: cada talle permitido | Talle `XS`, `S`, `M`, `L`, `XL` o `XXL` en un ítem válido | Aceptado. |
| Válida: minúsculas y espacios externos | Talle `"  m "` | Aceptado; el carrito recibido debe permanecer sin modificaciones (R4). |
| Inválida: talle no listado | Talle `XXXL` | `CheckoutError` con código `TALLE_INVALIDO`. |
| Inválida: cadena vacía o solo espacios | Talle `""` o `"   "` | `TALLE_INVALIDO`. |

## R3 — Cantidad

| Partición / límite | Entrada | Resultado esperado |
|---|---|---|
| Límite inferior inválido | Cantidad `0` | `CheckoutError` con código `CANTIDAD_INVALIDA`. |
| Límite inferior válido | Cantidad `1` | Aceptada. |
| Interior válido | Cantidad `5` | Aceptada. |
| Límite superior válido | Cantidad `10` | Aceptada. |
| Límite superior excedido | Cantidad `11` | `CANTIDAD_INVALIDA`. |
| Inválida: no entero | Cantidad `1.5` | `CANTIDAD_INVALIDA`. |
| Inválida: tipo distinto de entero | Cantidad `"2"` | `CANTIDAD_INVALIDA`. |

## R4 — Carrito

| Partición / límite | Entrada | Resultado esperado |
|---|---|---|
| Carrito vacío | `[]` | `CheckoutError` con código `CARRITO_VACIO`. |
| Carrito con un ítem válido | Un buzo M, cantidad 1 | Aceptado. |
| Sin efectos laterales | Carrito con talle `"  m "` y cualquier cálculo válido | El objeto y sus ítems quedan exactamente iguales a como se recibieron. |

## R5 — Descuento por cantidad

| Partición / límite | Entrada | Resultado esperado |
|---|---|---|
| Debajo del umbral | Un ítem de buzo, cantidad total 4; subtotal `99999.60` | Descuento por cantidad `0.00`. |
| Umbral exacto | Un ítem de buzo, cantidad total 5; subtotal `124999.50` | Descuento `12499.95` (10%). |
| Sobre el umbral | Un ítem de remera, cantidad total 6; subtotal `71997.00` | Descuento `7199.70` (10%). |

## R6 — Cupones

| Partición / límite | Entrada | Resultado esperado |
|---|---|---|
| Sin cupón | `None`, `""` o `"   "` | No se aplica cupón ni se produce error. |
| Cupón porcentual válido, fecha anterior al vencimiento | Subtotal `11999.50`, cupón `EGRESADOS2026`, fecha `2026-11-29` | Descuento `1799.93`; el medio centavo redondea hacia arriba (R7). |
| Vencimiento inclusivo | Mismo subtotal y cupón, fecha `2026-11-30` | Cupón aceptado; descuento `1799.93`. |
| Después del vencimiento | Fecha `2026-12-01` | `CheckoutError` con código `CUPON_VENCIDO`. |
| Cupón fijo en el mínimo | Subtotal `20000.00`, cupón `BIENVENIDA` | Descuento `3000.00`. |
| Cupón fijo debajo del mínimo | Subtotal `19999.99`, cupón `BIENVENIDA` | `CheckoutError` con código `CUPON_MINIMO_NO_ALCANZADO`. |
| Normalización del código | Cupón `"  bienvenida "` | Se reconoce como `BIENVENIDA`; beneficio `3000.00` si cumple el mínimo. |
| Cupón desconocido | Cupón `"OTRO2026"` | `CheckoutError` con código `CUPON_INVALIDO`. |
| Cupón no acumulable con descuento por cantidad | Subtotal `100000.00`, prendas 5, cupón `EGRESADOS2026`, fecha vigente | Descuento final `15000.00`, el mayor entre `10000.00` y `15000.00`, no la suma. |
| Fecha omitida | No se pasa `fecha` | Se usa la fecha del día de la llamada para determinar la vigencia. |

En todos los casos válidos, el descuento no supera el subtotal: `EGRESADOS2026` descuenta 15%, y `BIENVENIDA` solo es válido desde un subtotal de `20000.00`, donde su beneficio fijo de `3000.00` es menor que el subtotal.

## R7 — Dinero y redondeo

| Partición / límite | Entrada | Resultado esperado |
|---|---|---|
| Tipos monetarios | Cálculo de subtotal, descuentos, envío y total | Todos los importes devueltos son `Decimal`; no hay importes `float`. |
| Redondeo comercial en medio centavo | Subtotal `11999.50`, 1 prenda, cupón `EGRESADOS2026`, fecha `2026-11-30` | 15% = `1799.925`; descuento `1799.93`. |
| Importe exacto al centavo | Subtotal `100.00`, descuento porcentual aplicable del 10% | Descuento `10.00`. |

## R8 — Envío

| Partición / límite | Entrada | Resultado esperado |
|---|---|---|
| Zonas válidas | Zona `CABA`, `GBA`, `INTERIOR` o `RETIRO`, subtotal descontado menor a `60000.00` | Envío `2500.00`, `4000.00`, `6500.00` o `0.00`, respectivamente. |
| Normalización de zona | Zona `" caba "`, subtotal descontado menor a `60000.00` | Se acepta; envío `2500.00`. |
| Justo debajo del envío gratis | Subtotal ya descontado `59999.99`, zona CABA | Envío `2500.00`. |
| Umbral exacto de envío gratis | Subtotal ya descontado `60000.00`, zona CABA | Envío `0.00`. |
| Por encima del umbral | Subtotal ya descontado `60000.01`, zona GBA | Envío `0.00`. |
| Zona inexistente | Zona `"PATAGONIA"` | `CheckoutError` con código `ZONA_INVALIDA`. |
| Base del umbral | Subtotal bruto `70000.00`, descuento `10000.00`, zona CABA | Se usa el subtotal descontado `60000.00`; envío gratis. |

## R9 — Total

| Partición / límite | Entrada | Resultado esperado |
|---|---|---|
| Compra del ejemplo contractual | Dos buzos M, zona CABA, sin cupón | Subtotal `49999.80`, descuento `0.00`, envío `2500.00`, total `52499.80`. |
| Total con descuento y envío gratis | Subtotal `70000.00`, descuento `10000.00`, zona CABA | Envío `0.00`; total `60000.00` (`subtotal - descuento + envío`). |
| Total con retiro | Un buzo M, cantidad 1, zona RETIRO, sin cupón | Subtotal `24999.90`, descuento `0.00`, envío `0.00`, total `24999.90`. |

## R10 — Persistencia

| Partición / límite | Entrada / acción | Resultado esperado |
|---|---|---|
| Error de negocio al guardar | Guardar un carrito vacío en una base inicializada | Se propaga `CheckoutError` y no queda ni pedido ni ítem guardado. |
| Commit completo visible desde otra conexión | Guardar un pedido válido y consultarlo abriendo otra conexión al mismo archivo | La otra conexión ve el pedido y todos sus ítems completos. |
| Montos sin pérdida | Guardar una remera de `11999.50` con cupón vigente y recuperar el pedido | Los campos monetarios siguen siendo `Decimal` con exactamente los valores calculados por checkout: subtotal `11999.50`, descuento `1799.93`, envío `2500.00`, total `12699.57`. |
| Precio del catálogo | Ítem de buzo con precio enviado `1` | `precio_unitario` persistido es `24999.90`. |
| Normalización | Email `" Ana@Mail.com "`, zona `" caba "`, talle `" m "`, cupón `" bienvenida "` y subtotal suficiente | Email `ana@mail.com`; zona, talle y cupón `CABA`, `M` y `BIENVENIDA`. |
| Cupón vacío | Guardar con cupón `"   "` | El campo cupón recuperado es `None`. |
| Identificador inexistente | Consultar id `999` cuando no existe | `obtener_pedido` devuelve `None`. |
| Búsqueda insensible a mayúsculas y espacios | Guardar con `ana@mail.com`, buscar con `" ANA@MAIL.COM "` | Se devuelven los pedidos de ese email. |
| Orden de búsqueda | Guardar dos pedidos del mismo email en ese orden y consultar | Se devuelve primero el más reciente. |
| Entrada de email no altera consulta | Buscar con un valor que contenga comillas o texto SQL, por ejemplo `x' OR 1=1 --` | La búsqueda se trata como dato literal; no altera ni amplía los resultados. |

## R11 — API HTTP

| Partición / límite | Request | Resultado esperado |
|---|---|---|
| Crear pedido válido | `POST /api/v1/pedidos` con email, zona y carrito válidos; cupones y fecha opcionales | `201`; respuesta con `id` y montos como textos, por ejemplo `"11999.50"`. |
| Consultar pedido existente | `GET /api/v1/pedidos/{id}` después de crear uno | `200`; pedido completo según R10 y todos los montos como texto JSON. |
| Ruta inexistente | Request a una ruta distinta de los endpoints definidos | `404`, cuerpo `{"error":{"code":"RUTA_INEXISTENTE", ...}}`. |
| Pedido inexistente | `GET /api/v1/pedidos/999` | `404`, código `PEDIDO_INEXISTENTE`. |
| Error de negocio | POST con ítem de talle `XXXL` | `422`, código `TALLE_INVALIDO` del `CheckoutError`. |
| JSON malformado | POST con cuerpo crudo que no sea JSON válido | `400`, código `JSON_INVALIDO`. |
| Datos obligatorios ausentes | POST sin email, zona o carrito | `400`, código `DATOS_INCOMPLETOS`. |
| Tipo inválido en datos obligatorios | POST con `email: 42`, o con `zona: 42`, o con `carrito: "buzo"` (probar cada campo por separado) | Cada request devuelve `400`, código `DATOS_INCOMPLETOS`. |
| Fecha con formato inválido | POST con fecha `30/11/2026` | `400`, código `FECHA_INVALIDA`. |
| Otros errores de negocio | POST, individualmente, con producto `gorra`, cantidad `0`, carrito vacío, cupón `OTRO2026`, cupón `EGRESADOS2026` con fecha `2026-12-01`, cupón `BIENVENIDA` con subtotal menor a `20000.00`, o zona `PATAGONIA` | En cada caso `422` y, respectivamente, `PRODUCTO_INEXISTENTE`, `CANTIDAD_INVALIDA`, `CARRITO_VACIO`, `CUPON_INVALIDO`, `CUPON_VENCIDO`, `CUPON_MINIMO_NO_ALCANZADO` o `ZONA_INVALIDA`. |
| Límite de errores | Cualquier request que provoque error de negocio, datos o recurso inexistente | Nunca devuelve `500`; el status y código corresponden a la tabla de R11. |
