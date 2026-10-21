from datetime import date
from decimal import Decimal

import pytest

from checkout import (
    CheckoutError,
    calcular_descuento,
    calcular_envio,
    calcular_subtotal,
    calcular_total,
    validar_item,
)

HOY_VIGENTE = date(2026, 10, 1)


def item(producto="buzo", talle="M", cantidad=1, **extra):
    return {"producto": producto, "talle": talle, "cantidad": cantidad, **extra}


def codigo_de_error(funcion, *args):
    with pytest.raises(CheckoutError) as error:
        funcion(*args)
    return error.value.code


def test_cantidad_cero_es_invalida():
    assert codigo_de_error(validar_item, item(cantidad=0)) == "CANTIDAD_INVALIDA"


def test_cantidad_diez_es_valida():
    # Arrange
    entrada = item(cantidad=10)

    # Act
    resultado = validar_item(entrada)

    # Assert
    assert resultado is None


def test_cantidad_decimal_es_invalida():
    # Arrange
    entrada = item(cantidad=1.5)

    # Act / Assert
    assert codigo_de_error(validar_item, entrada) == "CANTIDAD_INVALIDA"


def test_validar_item_no_modifica_el_item():
    # Arrange
    entrada = item(talle="m")
    original = entrada.copy()

    # Act
    validar_item(entrada)

    # Assert
    assert entrada == original


def test_talle_ignora_espacios_exteriores():
    # Arrange
    entrada = item(talle="  M ")

    # Act
    resultado = validar_item(entrada)

    # Assert
    assert resultado is None


def test_descuento_por_cantidad_se_activa_con_cinco_prendas():
    # Arrange
    subtotal = Decimal("10000.00")

    # Act
    resultado = calcular_descuento(subtotal, 5, None, HOY_VIGENTE)

    # Assert
    assert resultado == Decimal("1000.00")


@pytest.mark.parametrize(
    ("producto", "precio"),
    [
        ("buzo", Decimal("24999.90")),
        ("remera", Decimal("11999.50")),
        ("campera", Decimal("47999.99")),
    ],
)
def test_subtotal_usa_precio_decimal_del_catalogo(producto, precio):
    # Arrange
    carrito = [item(producto=producto, precio=Decimal("0.01"))]

    # Act
    resultado = calcular_subtotal(carrito)

    # Assert
    assert resultado == precio
    assert isinstance(resultado, Decimal)


def test_producto_inexistente_lanza_error_especifico():
    # Arrange
    entrada = item(producto="gorra")

    # Act / Assert
    assert codigo_de_error(validar_item, entrada) == "PRODUCTO_INEXISTENTE"


def test_item_que_no_es_diccionario_lanza_error_de_producto():
    # Act / Assert
    assert codigo_de_error(validar_item, None) == "PRODUCTO_INEXISTENTE"


def test_producto_se_valida_antes_que_talle_y_cantidad():
    # Arrange
    entrada = item(producto="gorra", talle="XXXL", cantidad=0)

    # Act / Assert
    assert codigo_de_error(validar_item, entrada) == "PRODUCTO_INEXISTENTE"


@pytest.mark.parametrize("talle", ["", "XXXL", "X XL", None, 3])
def test_talle_invalido_lanza_error_especifico(talle):
    # Arrange
    entrada = item(talle=talle)

    # Act / Assert
    assert codigo_de_error(validar_item, entrada) == "TALLE_INVALIDO"


@pytest.mark.parametrize("cantidad", [11, "2", True, False])
def test_cantidad_fuera_de_rango_o_de_tipo_invalido(cantidad):
    # Arrange
    entrada = item(cantidad=cantidad)

    # Act / Assert
    assert codigo_de_error(validar_item, entrada) == "CANTIDAD_INVALIDA"


def test_calcular_subtotal_rechaza_carrito_vacio():
    # Act / Assert
    assert codigo_de_error(calcular_subtotal, []) == "CARRITO_VACIO"


def test_calcular_total_rechaza_carrito_vacio_antes_de_validar_zona():
    # Act / Assert
    assert codigo_de_error(calcular_total, [], "ZONA INVALIDA") == "CARRITO_VACIO"


def test_calcular_subtotal_no_modifica_el_carrito():
    # Arrange
    carrito = [item(talle="m", precio=Decimal("1.00"))]
    original = [carrito[0].copy()]

    # Act
    calcular_subtotal(carrito)

    # Assert
    assert carrito == original


@pytest.mark.parametrize(
    ("cantidad", "descuento"),
    [(4, Decimal("0.00")), (6, Decimal("1000.00"))],
)
def test_descuento_por_cantidad_respeta_el_umbral(cantidad, descuento):
    # Arrange
    subtotal = Decimal("10000.00")

    # Act
    resultado = calcular_descuento(subtotal, cantidad, fecha=HOY_VIGENTE)

    # Assert
    assert resultado == descuento
    assert isinstance(resultado, Decimal)


@pytest.mark.parametrize("cupon", [None, "", "   "])
def test_cupon_ausente_o_vacio_no_da_error(cupon):
    # Arrange
    subtotal = Decimal("10000.00")

    # Act
    resultado = calcular_descuento(subtotal, 1, cupon, HOY_VIGENTE)

    # Assert
    assert resultado == Decimal("0.00")


def test_cupon_porcentual_normaliza_mayusculas_y_redondea_comercialmente():
    # Arrange
    subtotal = Decimal("11999.50")

    # Act
    resultado = calcular_descuento(subtotal, 1, " egresados2026 ", HOY_VIGENTE)

    # Assert
    assert resultado == Decimal("1799.93")
    assert isinstance(resultado, Decimal)


def test_cupon_porcentual_es_valido_hasta_el_ultimo_dia_inclusive():
    # Arrange
    subtotal = Decimal("11999.50")
    ultimo_dia = date(2026, 11, 30)

    # Act
    resultado = calcular_descuento(subtotal, 1, "EGRESADOS2026", ultimo_dia)

    # Assert
    assert resultado == Decimal("1799.93")


def test_cupon_porcentual_vencido_lanza_error():
    # Arrange
    subtotal = Decimal("11999.50")
    dia_siguiente = date(2026, 12, 1)

    # Act / Assert
    assert codigo_de_error(
        calcular_descuento, subtotal, 1, "EGRESADOS2026", dia_siguiente
    ) == "CUPON_VENCIDO"


def test_cupon_fijo_no_alcanza_minimo_lanza_error():
    # Arrange
    subtotal = Decimal("19999.99")

    # Act / Assert
    assert codigo_de_error(
        calcular_descuento, subtotal, 1, "BIENVENIDA", HOY_VIGENTE
    ) == "CUPON_MINIMO_NO_ALCANZADO"


def test_cupon_fijo_aplica_en_el_minimo_exactamente():
    # Arrange
    subtotal = Decimal("20000.00")

    # Act
    resultado = calcular_descuento(subtotal, 1, "BIENVENIDA", HOY_VIGENTE)

    # Assert
    assert resultado == Decimal("3000.00")


def test_cupon_desconocido_lanza_error():
    # Act / Assert
    assert codigo_de_error(
        calcular_descuento, Decimal("10000.00"), 1, "NOEXISTE", HOY_VIGENTE
    ) == "CUPON_INVALIDO"


def test_cupon_que_no_es_texto_lanza_error():
    # Act / Assert
    assert codigo_de_error(
        calcular_descuento, Decimal("10000.00"), 1, 123, HOY_VIGENTE
    ) == "CUPON_INVALIDO"


def test_fecha_de_cupon_porcentual_que_no_es_date_lanza_error():
    # Act / Assert
    assert codigo_de_error(
        calcular_descuento, Decimal("10000.00"), 1, "EGRESADOS2026", "2026-10-01"
    ) == "CUPON_VENCIDO"


def test_descuento_por_cantidad_y_cupon_no_se_acumulan():
    # Arrange
    subtotal = Decimal("50000.00")

    # Act
    resultado = calcular_descuento(subtotal, 5, "BIENVENIDA", HOY_VIGENTE)

    # Assert
    assert resultado == Decimal("5000.00")


def test_cupon_aplica_el_mayor_descuento_disponible():
    # Arrange
    subtotal = Decimal("20000.00")

    # Act
    resultado = calcular_descuento(subtotal, 5, "BIENVENIDA", HOY_VIGENTE)

    # Assert
    assert resultado == Decimal("3000.00")


@pytest.mark.parametrize(
    ("zona", "costo"),
    [
        ("CABA", Decimal("2500.00")),
        ("GBA", Decimal("4000.00")),
        ("INTERIOR", Decimal("6500.00")),
        ("RETIRO", Decimal("0.00")),
    ],
)
def test_envio_devuelve_costo_decimal_por_zona(zona, costo):
    # Act
    resultado = calcular_envio(Decimal("10000.00"), zona)

    # Assert
    assert resultado == costo
    assert isinstance(resultado, Decimal)


def test_envio_normaliza_zona():
    # Act
    resultado = calcular_envio(Decimal("10000.00"), " caba ")

    # Assert
    assert resultado == Decimal("2500.00")


def test_zona_invalida_lanza_error_especifico():
    # Act / Assert
    assert codigo_de_error(calcular_envio, Decimal("10000.00"), "SUR") == "ZONA_INVALIDA"


def test_zona_que_no_es_texto_lanza_error():
    # Act / Assert
    assert codigo_de_error(calcular_envio, Decimal("10000.00"), None) == "ZONA_INVALIDA"


@pytest.mark.parametrize(
    ("subtotal", "envio"),
    [
        (Decimal("59999.99"), Decimal("2500.00")),
        (Decimal("60000.00"), Decimal("0.00")),
    ],
)
def test_envio_gratis_comienza_en_sesenta_mil(subtotal, envio):
    # Act
    resultado = calcular_envio(subtotal, "CABA")

    # Assert
    assert resultado == envio


def test_total_del_ejemplo_de_especificacion_y_tipos():
    # Arrange
    carrito = [item(cantidad=2)]

    # Act
    resultado = calcular_total(carrito, "CABA", fecha=HOY_VIGENTE)

    # Assert
    assert resultado == {
        "subtotal": Decimal("49999.80"),
        "descuento": Decimal("0.00"),
        "envio": Decimal("2500.00"),
        "total": Decimal("52499.80"),
    }
    assert all(isinstance(importe, Decimal) for importe in resultado.values())


def test_total_aplica_descuento_antes_de_resolver_envio():
    # Arrange
    carrito = [item(producto="remera", cantidad=5)]

    # Act
    resultado = calcular_total(carrito, "CABA", fecha=HOY_VIGENTE)

    # Assert
    assert resultado["subtotal"] == Decimal("59997.50")
    assert resultado["descuento"] == Decimal("5999.75")
    assert resultado["envio"] == Decimal("2500.00")
    assert resultado["total"] == Decimal("56497.75")


def test_total_rechaza_primero_el_primer_error_de_items():
    # Arrange
    carrito = [item(talle="M", cantidad=0), item(producto="gorra")]

    # Act / Assert
    assert codigo_de_error(calcular_total, carrito, "SUR") == "CANTIDAD_INVALIDA"


def test_total_valida_cupon_antes_que_zona():
    # Arrange
    carrito = [item()]

    # Act / Assert
    assert codigo_de_error(
        calcular_total, carrito, "SUR", "NOEXISTE", HOY_VIGENTE
    ) == "CUPON_INVALIDO"


def test_total_no_modifica_el_carrito():
    # Arrange
    carrito = [item(talle=" m ", cantidad=1, precio=Decimal("0.01"))]
    original = [carrito[0].copy()]

    # Act
    calcular_total(carrito, "CABA", fecha=HOY_VIGENTE)

    # Assert
    assert carrito == original
