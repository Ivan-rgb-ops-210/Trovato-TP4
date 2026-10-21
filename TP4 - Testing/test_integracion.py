from datetime import date
from decimal import Decimal

import pytest

import pedidos
from checkout import CheckoutError

HOY_VIGENTE = date(2026, 10, 1)


@pytest.fixture
def ruta(tmp_path):
    return str(tmp_path / "tienda.db")


@pytest.fixture
def con(ruta):
    conexion = pedidos.conectar(ruta)
    pedidos.crear_esquema(conexion)
    yield conexion
    conexion.close()


def item(producto="buzo", talle="M", cantidad=1, **extra):
    return {"producto": producto, "talle": talle, "cantidad": cantidad, **extra}


def contar(ruta, tabla):
    assert tabla in ("pedidos", "items")
    otra = pedidos.conectar(ruta)
    try:
        return otra.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    finally:
        otra.close()


def test_un_id_inexistente_devuelve_none(con):
    assert pedidos.obtener_pedido(con, 999) is None


def test_error_de_checkout_no_deja_pedido_ni_items(con, ruta):
    carrito = [item(producto="gorra")]

    with pytest.raises(CheckoutError) as error:
        pedidos.guardar_pedido(
            con, "ana@mail.com", carrito, "CABA", fecha=HOY_VIGENTE
        )

    assert error.value.code == "PRODUCTO_INEXISTENTE"
    assert contar(ruta, "pedidos") == 0
    assert contar(ruta, "items") == 0
