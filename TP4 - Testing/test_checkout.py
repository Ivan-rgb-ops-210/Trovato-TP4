from datetime import date as Date
from decimal import Decimal

import pytest

import checkout
from checkout import (
    CheckoutError,
    calcular_descuento,
    calcular_envio,
    calcular_subtotal,
    calcular_total,
    validar_item,
)

HOY_VIGENTE = Date(2026, 10, 1)


def item(producto="buzo", talle="M", cantidad=1, **extra):
    return {"producto": producto, "talle": talle, "cantidad": cantidad, **extra}


def codigo_de_error(funcion, *args):
    with pytest.raises(CheckoutError) as error:
        funcion(*args)
    return error.value.code


def test_cantidad_cero_es_invalida():
    assert codigo_de_error(validar_item, item(cantidad=0)) == "CANTIDAD_INVALIDA"


def test_precio_enviado_se_ignora_y_se_usa_el_catalogo():
    carrito = [item(precio=1)]

    subtotal = calcular_subtotal(carrito)

    assert subtotal == Decimal("24999.90")


def test_producto_fuera_del_catalogo_es_rechazado():
    assert codigo_de_error(validar_item, item(producto="gorra")) == "PRODUCTO_INEXISTENTE"


def test_talle_se_normaliza_sin_modificar_el_carrito():
    carrito = [item(talle="  m ")]
    original = [item(talle="  m ")]

    subtotal = calcular_subtotal(carrito)

    assert subtotal == Decimal("24999.90")
    assert carrito == original


def test_cantidad_diez_es_valida():
    assert validar_item(item(cantidad=10)) is None


def test_cantidad_fraccionaria_y_boolean_no_son_enteros_validos():
    assert codigo_de_error(validar_item, item(cantidad=1.5)) == "CANTIDAD_INVALIDA"
    assert codigo_de_error(validar_item, item(cantidad=True)) == "CANTIDAD_INVALIDA"


def test_carrito_vacio_se_rechaza_antes_de_validar_cupon_y_zona():
    assert codigo_de_error(calcular_total, [], "ZONA_INVALIDA", "CUPON_INVALIDO") == "CARRITO_VACIO"


def test_descuento_por_cantidad_empieza_en_cinco_prendas():
    assert calcular_descuento(Decimal("124999.50"), 4) == Decimal("0.00")
    descuento = calcular_descuento(Decimal("124999.50"), 5)

    assert descuento == Decimal("12499.95")
    assert isinstance(descuento, Decimal)


def test_cupon_porcentual_redondea_el_medio_centavo_hacia_arriba():
    descuento = calcular_descuento(
        Decimal("11999.50"), 1, "EGRESADOS2026", Date(2026, 10, 1)
    )

    assert descuento == Decimal("1799.93")
    assert isinstance(descuento, Decimal)


def test_cupon_ignora_espacios_y_mayusculas_y_acepta_cupon_vacio():
    sin_cupon = calcular_descuento(Decimal("20000.00"), 1, "   ", HOY_VIGENTE)
    bienvenida = calcular_descuento(Decimal("20000.00"), 1, "  bienvenida ", HOY_VIGENTE)

    assert sin_cupon == Decimal("0.00")
    assert bienvenida == Decimal("3000.00")


def test_cupon_egresados_es_valido_hasta_el_30_de_noviembre_inclusive():
    descuento = calcular_descuento(
        Decimal("11999.50"), 1, "EGRESADOS2026", Date(2026, 11, 30)
    )

    assert descuento == Decimal("1799.93")


def test_cupon_y_descuento_por_cantidad_no_se_acumulan():
    descuento = calcular_descuento(
        Decimal("100000.00"), 5, "EGRESADOS2026", HOY_VIGENTE
    )

    assert descuento == Decimal("15000.00")


def test_solo_existen_los_dos_cupones_especificados():
    assert codigo_de_error(
        calcular_descuento, Decimal("100000.00"), 1, "DEBUG100", HOY_VIGENTE
    ) == "CUPON_INVALIDO"


def test_fecha_predeterminada_se_evalua_en_cada_llamada(monkeypatch):
    class FechaDelDiaSiguiente(Date):
        @classmethod
        def today(cls):
            return Date(2026, 12, 1)

    monkeypatch.setattr(checkout, "date", FechaDelDiaSiguiente)

    assert codigo_de_error(
        calcular_descuento, Decimal("11999.50"), 1, "EGRESADOS2026"
    ) == "CUPON_VENCIDO"


def test_calcular_total_usa_fecha_actual_si_no_recibe_fecha(monkeypatch):
    class FechaDelDiaSiguiente(Date):
        @classmethod
        def today(cls):
            return Date(2026, 12, 1)

    monkeypatch.setattr(checkout, "date", FechaDelDiaSiguiente)
    carrito = [item(producto="remera")]

    assert codigo_de_error(
        calcular_total, carrito, "CABA", "EGRESADOS2026"
    ) == "CUPON_VENCIDO"
