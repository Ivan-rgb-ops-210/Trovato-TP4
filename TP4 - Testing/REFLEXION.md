# Reflexión

## 1. Cantidad y proporción de tests

En total se ejecutan 96 tests: 61 unitarios (53 en `test_checkout.py` y 8 de la suite de IA), 9 de integración y 26 E2E. Si cuento solo los unitarios que escribí para la Parte 3, son 53. Hay más unitarios porque las reglas de `checkout.py` se pueden comprobar por separado con muchos casos pequeños y rápidos. Los tests de integración se concentran en interacciones con una base SQLite real, y los E2E verifican endpoints HTTP completos y sus errores. Por ejemplo, la integración comprueba que el precio guardado venga del catálogo, mientras que E2E comprueba que los importes lleguen como texto en el JSON.

## 2. Falla de persistencia fuera de los tests unitarios

Un test unitario de `checkout.py` no podía detectar la inyección SQL de `pedidos_de`, porque esa falla estaba en la consulta de `pedidos.py`, no en el cálculo de las reglas de compra. La función armaba el SQL interpolando directamente el email recibido. En la prueba de integración guardé un pedido con el email literal `' OR 1=1 --` y consulté usando ese mismo valor. La consulta vulnerable alteraba su condición y podía devolver pedidos de otros emails. Para encontrarlo hacía falta probar la persistencia real con SQLite y una entrada hostil.

## 3. Falla en el paso entre API y cliente

El checkout producía importes como `Decimal`, pero la API los serializaba con `default=float`. Como resultado, el JSON enviaba números como `24999.9` en lugar de textos con dos decimales como `"24999.90"`. El cliente recibía un tipo distinto del que establece el contrato y podía perder el formato decimal esperado. El test E2E detectó esta diferencia haciendo un POST real y revisando el cuerpo JSON. La conversión entre el tipo interno del backend y el formato público debía resolverla la capa API.

## 4. Falla más costosa en producción

La falla que considero más costosa sería la inyección SQL en la búsqueda por email. Un usuario podía construir un email que cambiara la condición de la consulta, como ocurrió con `' OR 1=1 --` en el caso de integración. En un sistema real, eso podría exponer pedidos asociados a otras personas. El impacto no sería solo un resultado incorrecto: también comprometería la privacidad y la confianza de los clientes. Por eso el riesgo sería mayor que un error de formato visible en una respuesta.

## 5. Cobertura, mutación e inyección de fallas

La cobertura mide qué líneas o ramas del código ejecuta la suite, pero no confirma que los asserts detecten resultados equivocados. En este TP, el reporte de `checkout.py` mostró 99% de cobertura de líneas y 37 de 38 ramas cubiertas. La mutación modifica deliberadamente partes del código y mide cuántas de esas versiones alteradas hacen fallar los tests; la suite inicial de IA mató 17 de 29 mutantes (58,6%), mientras que la suite corregida mató 41 de 41. La inyección de fallas introduce o fuerza problemas controlados en componentes o en el entorno y observa si el sistema los detecta y responde de forma segura. En nuestros casos, enviar JSON inválido permitió comprobar cómo responde la API ante una entrada dañada, aunque no hicimos una campaña formal de fallas de infraestructura, como desconectar SQLite. Las tres mediciones responden preguntas distintas: ejecución del código, capacidad de los tests para detectar cambios incorrectos y comportamiento del sistema frente a fallas inducidas.

## 6. Qué podría faltar en tests escritos por una IA

Una IA podría cubrir la respuesta feliz y aun así omitir efectos persistentes que no aparecen en el cuerpo HTTP. Por ejemplo, el test con una segunda conexión a SQLite encontró que un checkout fallido dejaba un pedido vacío, algo que un test limitado al status de respuesta no habría visto. También podría no probar emails hostiles ni verificar que los importes viajen como texto. Para comprobarlo, contrastaría cada test con los casos R10 y R11 y ejecutaría las pruebas contra una base temporal real y requests HTTP reales, sin mocks. En este TP, las primeras ejecuciones mostraron 500 ante JSON inválido y la consulta SQL devolvía pedidos ajenos, ejemplos concretos de fallas que una suite superficial podría dejar pasar.
