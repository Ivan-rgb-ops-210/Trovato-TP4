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
