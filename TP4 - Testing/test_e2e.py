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
    status, cuerpo = pedir(url, "POST", RUTA, cuerpo=compra())

    assert status == 201
    assert type(cuerpo["id"]) is int
    assert cuerpo["subtotal"] == "24999.90"
    assert cuerpo["descuento"] == "0.00"
    assert cuerpo["envio"] == "2500.00"
    assert cuerpo["total"] == "27499.90"


def test_get_devuelve_pedido_completo_y_montos_como_texto(url):
    status_creacion, creado = pedir(url, "POST", RUTA, cuerpo=compra())
    assert status_creacion == 201

    status, cuerpo = pedir(url, "GET", f"{RUTA}/{creado['id']}")

    assert status == 200
    assert cuerpo["id"] == creado["id"]
    assert cuerpo["email"] == "ana@mail.com"
    assert cuerpo["zona"] == "CABA"
    assert cuerpo["subtotal"] == "24999.90"
    assert cuerpo["descuento"] == "0.00"
    assert cuerpo["envio"] == "2500.00"
    assert cuerpo["total"] == "27499.90"
    assert cuerpo["items"] == [
        {
            "producto": "buzo",
            "talle": "M",
            "cantidad": 1,
            "precio_unitario": "24999.90",
        }
    ]
