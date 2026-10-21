from datetime import date
from decimal import Decimal

import pytest

import pedidos
from checkout import CheckoutError, calcular_total

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


def test_pedido_completo_es_visible_desde_otra_conexion(con, ruta):
    carrito = [item(producto="remera", talle="M", cantidad=1)]
    pedido_id = pedidos.guardar_pedido(
        con, "ana@mail.com", carrito, "CABA", fecha=HOY_VIGENTE
    )

    otra_conexion = pedidos.conectar(ruta)
    try:
        guardado = pedidos.obtener_pedido(otra_conexion, pedido_id)
    finally:
        otra_conexion.close()

    assert guardado == {
        "id": pedido_id,
        "email": "ana@mail.com",
        "zona": "CABA",
        "cupon": None,
        "subtotal": Decimal("11999.50"),
        "descuento": Decimal("0.00"),
        "envio": Decimal("2500.00"),
        "total": Decimal("14499.50"),
        "items": [
            {
                "producto": "remera",
                "talle": "M",
                "cantidad": 1,
                "precio_unitario": Decimal("11999.50"),
            }
        ],
    }


def test_precio_unitario_guardado_sale_del_catalogo(con):
    carrito = [item(producto="remera", precio=Decimal("1.00"))]
    esperado = calcular_total(carrito, "CABA", fecha=HOY_VIGENTE)

    pedido_id = pedidos.guardar_pedido(
        con, "ana@mail.com", carrito, "CABA", fecha=HOY_VIGENTE
    )
    guardado = pedidos.obtener_pedido(con, pedido_id)

    assert guardado["subtotal"] == esperado["subtotal"]
    assert guardado["descuento"] == esperado["descuento"]
    assert guardado["envio"] == esperado["envio"]
    assert guardado["total"] == esperado["total"]
    assert guardado["items"][0]["precio_unitario"] == Decimal("11999.50")


def test_pedido_guarda_datos_normalizados(con):
    carrito = [item(producto="buzo", talle=" m ")]

    pedido_id = pedidos.guardar_pedido(
        con,
        " Ana@Mail.com ",
        carrito,
        " caba ",
        " bienvenida ",
        HOY_VIGENTE,
    )
    guardado = pedidos.obtener_pedido(con, pedido_id)

    assert guardado["email"] == "ana@mail.com"
    assert guardado["zona"] == "CABA"
    assert guardado["cupon"] == "BIENVENIDA"
    assert guardado["items"][0]["talle"] == "M"


def test_pedido_guarda_cupon_vacio_como_none(con):
    pedido_id = pedidos.guardar_pedido(
        con, "ana@mail.com", [item()], "CABA", "   ", HOY_VIGENTE
    )

    guardado = pedidos.obtener_pedido(con, pedido_id)

    assert guardado["cupon"] is None


def test_pedidos_de_normaliza_email_y_ordena_del_mas_reciente(con):
    primer_id = pedidos.guardar_pedido(
        con, " Ana@Mail.com ", [item(producto="remera")], "CABA", fecha=HOY_VIGENTE
    )
    segundo_id = pedidos.guardar_pedido(
        con, "ana@mail.com", [item(producto="buzo")], "GBA", fecha=HOY_VIGENTE
    )

    resultado = pedidos.pedidos_de(con, " ANA@MAIL.COM ")

    assert [pedido["id"] for pedido in resultado] == [segundo_id, primer_id]


def test_pedidos_de_trata_email_como_dato_literal(con):
    email_hostil = "' OR 1=1 --"
    pedido_legitimo_id = pedidos.guardar_pedido(
        con, "ana@mail.com", [item(producto="remera")], "CABA", fecha=HOY_VIGENTE
    )
    pedido_hostil_id = pedidos.guardar_pedido(
        con, email_hostil, [item(producto="buzo")], "CABA", fecha=HOY_VIGENTE
    )

    resultado = pedidos.pedidos_de(con, email_hostil)

    assert [pedido["id"] for pedido in resultado] == [pedido_hostil_id]
    assert pedido_hostil_id != pedido_legitimo_id


def test_montos_recuperados_conservan_precision_decimal(con):
    pedido_id = pedidos.guardar_pedido(
        con, "ana@mail.com", [item(producto="buzo")], "CABA", fecha=HOY_VIGENTE
    )

    guardado = pedidos.obtener_pedido(con, pedido_id)

    assert guardado["subtotal"] == Decimal("24999.90")
    assert guardado["descuento"] == Decimal("0.00")
    assert guardado["envio"] == Decimal("2500.00")
    assert guardado["total"] == Decimal("27499.90")
