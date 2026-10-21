from datetime import date
from decimal import Decimal, ROUND_HALF_UP


class CheckoutError(Exception):
    def __init__(self, code, mensaje):
        super().__init__(mensaje)
        self.code = code
        self.mensaje = mensaje


CATALOGO = {
    "buzo": Decimal("24999.90"),
    "remera": Decimal("11999.50"),
    "campera": Decimal("47999.99"),
}

TALLES = ["XS", "S", "M", "L", "XL", "XXL"]

CUPONES = {
    "EGRESADOS2026": {
        "tipo": "porcentaje",
        "valor": Decimal("0.15"),
        "vence": date(2026, 11, 30),
    },
    "BIENVENIDA": {"tipo": "fijo", "valor": Decimal("3000.00"), "minimo": Decimal("20000.00")},
}

ENVIOS = {
    "CABA": Decimal("2500.00"),
    "GBA": Decimal("4000.00"),
    "INTERIOR": Decimal("6500.00"),
    "RETIRO": Decimal("0.00"),
}

CENTAVO = Decimal("0.01")
DESCUENTO_CANTIDAD = Decimal("0.10")


def _redondear_dinero(importe):
    return importe.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def validar_item(item):
    if not isinstance(item, dict):
        raise CheckoutError("PRODUCTO_INEXISTENTE", "El producto no existe")

    producto = item.get("producto")
    if not isinstance(producto, str) or producto not in CATALOGO:
        raise CheckoutError("PRODUCTO_INEXISTENTE", f"Producto inexistente: {producto!r}")

    talle = item.get("talle")
    if not isinstance(talle, str) or talle.strip().upper() not in TALLES:
        raise CheckoutError("TALLE_INVALIDO", f"Talle inválido: {talle!r}")

    cantidad = item.get("cantidad")
    if type(cantidad) is not int or not (1 <= cantidad <= 10):
        raise CheckoutError("CANTIDAD_INVALIDA", "La cantidad debe ser un entero entre 1 y 10")


def calcular_subtotal(carrito):
    if not isinstance(carrito, list) or not carrito:
        raise CheckoutError("CARRITO_VACIO", "El carrito debe tener al menos un ítem")

    subtotal = Decimal("0.00")
    for item in carrito:
        validar_item(item)
        subtotal += CATALOGO[item["producto"]] * item["cantidad"]

    return _redondear_dinero(subtotal)


def calcular_descuento(subtotal, cantidad_prendas, cupon=None, fecha=None):
    descuento_cantidad = Decimal("0.00")
    if cantidad_prendas >= 5:
        descuento_cantidad = _redondear_dinero(subtotal * DESCUENTO_CANTIDAD)

    if cupon is None:
        return descuento_cantidad
    if not isinstance(cupon, str):
        raise CheckoutError("CUPON_INVALIDO", "El cupón no existe")

    codigo = cupon.strip().upper()
    if not codigo:
        return descuento_cantidad
    if codigo not in CUPONES:
        raise CheckoutError("CUPON_INVALIDO", "El cupón no existe")

    datos = CUPONES[codigo]
    descuento_cupon = Decimal("0.00")

    if datos["tipo"] == "porcentaje":
        fecha_actual = date.today() if fecha is None else fecha
        if not isinstance(fecha_actual, date):
            raise CheckoutError("CUPON_VENCIDO", "La fecha del cupón es inválida")
        if fecha_actual > datos["vence"]:
            raise CheckoutError("CUPON_VENCIDO", "El cupón está vencido")
        descuento_cupon = _redondear_dinero(subtotal * datos["valor"])
    elif datos["tipo"] == "fijo":
        if subtotal < datos["minimo"]:
            raise CheckoutError(
                "CUPON_MINIMO_NO_ALCANZADO",
                f"El cupón requiere una compra mínima de ${datos['minimo']}",
            )
        descuento_cupon = datos["valor"]

    return min(subtotal, max(descuento_cantidad, descuento_cupon))


def calcular_envio(subtotal_con_descuento, zona):
    if not isinstance(zona, str):
        raise CheckoutError("ZONA_INVALIDA", "La zona de envío no existe")

    zona_normalizada = zona.strip().upper()
    if zona_normalizada not in ENVIOS:
        opciones = ", ".join(ENVIOS)
        raise CheckoutError(
            "ZONA_INVALIDA",
            f"Zona inválida. Opciones: {opciones}",
        )

    if subtotal_con_descuento >= Decimal("60000.00"):
        return Decimal("0.00")

    return ENVIOS[zona_normalizada]


def calcular_total(carrito, zona, cupon=None, fecha=None):
    subtotal = calcular_subtotal(carrito)

    cantidad_prendas = sum(item["cantidad"] for item in carrito)
    descuento = calcular_descuento(subtotal, cantidad_prendas, cupon, fecha)
    envio = calcular_envio(subtotal - descuento, zona)
    total = _redondear_dinero(subtotal - descuento + envio)

    return {
        "subtotal": subtotal,
        "descuento": descuento,
        "envio": envio,
        "total": total,
    }
