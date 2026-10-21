import json
import threading
import urllib.error
import urllib.request

import pytest

import api

RUTA = "/api/v1/pedidos"


@pytest.fixture
def url(tmp_path):
    servidor = api.crear_servidor(str(tmp_path / "tienda.db"), 0)
    threading.Thread(target=servidor.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    yield f"http://127.0.0.1:{servidor.server_address[1]}"
    servidor.shutdown()
    servidor.server_close()


def pedir(url, metodo, ruta, cuerpo=None, crudo=None):
    datos = crudo if crudo is not None else (json.dumps(cuerpo).encode() if cuerpo is not None else None)
    req = urllib.request.Request(url + ruta, data=datos, method=metodo,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def compra(**cambios):
    cuerpo = {"email": "ana@mail.com", "zona": "CABA",
              "carrito": [{"producto": "buzo", "talle": "M", "cantidad": 1}]}
    cuerpo.update(cambios)
    return cuerpo


def test_una_ruta_inexistente_devuelve_404(url):
    status, cuerpo = pedir(url, "GET", "/api/v1/otra")
    assert status == 404
    assert cuerpo["error"]["code"] == "RUTA_INEXISTENTE"


def test_post_crea_pedido_y_devuelve_montos_como_texto(url):
    carrito = [{"producto": "remera", "talle": "M", "cantidad": 1}]
    status, cuerpo = pedir(url, "POST", RUTA, cuerpo=compra(carrito=carrito))

    assert status == 201
    assert type(cuerpo["id"]) is int
    assert cuerpo["subtotal"] == "11999.50"
    assert cuerpo["descuento"] == "0.00"
    assert cuerpo["envio"] == "2500.00"
    assert cuerpo["total"] == "14499.50"


def test_get_devuelve_pedido_completo_y_montos_como_texto(url):
    carrito = [{"producto": "remera", "talle": "M", "cantidad": 1}]
    status_creacion, creado = pedir(url, "POST", RUTA, cuerpo=compra(carrito=carrito))
    assert status_creacion == 201

    status, cuerpo = pedir(url, "GET", f"{RUTA}/{creado['id']}")

    assert status == 200
    assert cuerpo["id"] == creado["id"]
    assert cuerpo["email"] == "ana@mail.com"
    assert cuerpo["zona"] == "CABA"
    assert cuerpo["cupon"] is None
    assert cuerpo["subtotal"] == "11999.50"
    assert cuerpo["descuento"] == "0.00"
    assert cuerpo["envio"] == "2500.00"
    assert cuerpo["total"] == "14499.50"
    assert cuerpo["items"] == [
        {
            "producto": "remera",
            "talle": "M",
            "cantidad": 1,
            "precio_unitario": "11999.50",
        }
    ]


def test_post_con_json_invalido_devuelve_400(url):
    status, cuerpo = pedir(url, "POST", RUTA, crudo=b"esto no es JSON")

    assert status == 400
    assert cuerpo["error"]["code"] == "JSON_INVALIDO"
    assert isinstance(cuerpo["error"]["message"], str)


@pytest.mark.parametrize("campo", ["email", "zona", "carrito"])
def test_post_sin_campo_obligatorio_devuelve_400(url, campo):
    datos = compra()
    del datos[campo]

    status, cuerpo = pedir(url, "POST", RUTA, cuerpo=datos)

    assert status == 400
    assert cuerpo["error"]["code"] == "DATOS_INCOMPLETOS"
    assert isinstance(cuerpo["error"]["message"], str)


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("email", 7), ("zona", 7), ("carrito", {})],
)
def test_post_con_tipo_incorrecto_devuelve_400(url, campo, valor):
    datos = compra(**{campo: valor})

    status, cuerpo = pedir(url, "POST", RUTA, cuerpo=datos)

    assert status == 400
    assert cuerpo["error"]["code"] == "DATOS_INCOMPLETOS"
    assert isinstance(cuerpo["error"]["message"], str)


def test_post_con_fecha_invalida_devuelve_400(url):
    status, cuerpo = pedir(url, "POST", RUTA, cuerpo=compra(fecha="30/11/2026"))

    assert status == 400
    assert cuerpo["error"]["code"] == "FECHA_INVALIDA"
    assert isinstance(cuerpo["error"]["message"], str)


def test_post_con_producto_inexistente_devuelve_422(url):
    status, cuerpo = pedir(
        url,
        "POST",
        RUTA,
        cuerpo=compra(carrito=[{"producto": "gorra", "talle": "M", "cantidad": 1}]),
    )

    assert status == 422
    assert cuerpo["error"]["code"] == "PRODUCTO_INEXISTENTE"
    assert isinstance(cuerpo["error"]["message"], str)


def test_get_pedido_inexistente_devuelve_404(url):
    status, cuerpo = pedir(url, "GET", f"{RUTA}/999")

    assert status == 404
    assert cuerpo["error"]["code"] == "PEDIDO_INEXISTENTE"
    assert isinstance(cuerpo["error"]["message"], str)


def test_post_a_ruta_inexistente_devuelve_404(url):
    status, cuerpo = pedir(url, "POST", "/api/v1/otra", cuerpo=compra())

    assert status == 404
    assert cuerpo["error"]["code"] == "RUTA_INEXISTENTE"
    assert isinstance(cuerpo["error"]["message"], str)


@pytest.mark.parametrize(
    ("metodo", "ruta", "datos", "crudo", "status_esperado", "codigo"),
    [
        ("POST", RUTA, None, b"esto no es JSON", 400, "JSON_INVALIDO"),
        ("POST", RUTA, {"zona": "CABA", "carrito": []}, None, 400, "DATOS_INCOMPLETOS"),
        ("POST", RUTA, {"email": "ana@mail.com", "carrito": []}, None, 400, "DATOS_INCOMPLETOS"),
        ("POST", RUTA, {"email": "ana@mail.com", "zona": "CABA"}, None, 400, "DATOS_INCOMPLETOS"),
        ("POST", RUTA, compra(email=7), None, 400, "DATOS_INCOMPLETOS"),
        ("POST", RUTA, compra(zona=7), None, 400, "DATOS_INCOMPLETOS"),
        ("POST", RUTA, compra(carrito={}), None, 400, "DATOS_INCOMPLETOS"),
        ("POST", RUTA, compra(fecha="30/11/2026"), None, 400, "FECHA_INVALIDA"),
        (
            "POST",
            RUTA,
            compra(carrito=[{"producto": "gorra", "talle": "M", "cantidad": 1}]),
            None,
            422,
            "PRODUCTO_INEXISTENTE",
        ),
        ("GET", f"{RUTA}/999", None, None, 404, "PEDIDO_INEXISTENTE"),
        ("GET", "/api/v1/otra", None, None, 404, "RUTA_INEXISTENTE"),
        ("POST", "/api/v1/otra", compra(), None, 404, "RUTA_INEXISTENTE"),
    ],
)
def test_todos_los_errores_tienen_formato_comun_y_no_son_500(
    url, metodo, ruta, datos, crudo, status_esperado, codigo
):
    status, cuerpo = pedir(url, metodo, ruta, cuerpo=datos, crudo=crudo)

    assert status == status_esperado
    assert status != 500
    assert "error" in cuerpo
    assert cuerpo["error"]["code"] == codigo
    assert isinstance(cuerpo["error"]["message"], str)
