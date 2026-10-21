import json
import re
from datetime import date
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pedidos
from checkout import CheckoutError

RUTA_PEDIDOS = "/api/v1/pedidos"
RUTA_PEDIDO = re.compile(r"/api/v1/pedidos/(\d+)")
FORMATO_FECHA = re.compile(r"\d{4}-\d{2}-\d{2}")


def _serializar_decimal(valor):
    if isinstance(valor, Decimal):
        return format(valor, ".2f")
    raise TypeError(f"Tipo no serializable: {type(valor).__name__}")


def _error(codigo, mensaje):
    return {"error": {"code": codigo, "message": mensaje}}


class _Manejador(BaseHTTPRequestHandler):
    ruta_db = None

    def log_message(self, *args):
        pass

    def _responder(self, status, cuerpo):
        datos = json.dumps(cuerpo, default=_serializar_decimal).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_POST(self):
        if self.path != RUTA_PEDIDOS:
            self._responder(404, _error("RUTA_INEXISTENTE", "La ruta no existe"))
            return

        try:
            largo = int(self.headers.get("Content-Length", 0))
            datos = json.loads(self.rfile.read(largo))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            self._responder(400, _error("JSON_INVALIDO", "El cuerpo debe contener JSON válido"))
            return

        if not isinstance(datos, dict):
            self._responder(400, _error("DATOS_INCOMPLETOS", "Se esperaba un objeto JSON"))
            return

        if (
            not isinstance(datos.get("email"), str)
            or not isinstance(datos.get("zona"), str)
            or not isinstance(datos.get("carrito"), list)
            or ("cupon" in datos and datos["cupon"] is not None and not isinstance(datos["cupon"], str))
        ):
            self._responder(
                400,
                _error("DATOS_INCOMPLETOS", "Email, zona y carrito deben tener formatos válidos"),
            )
            return

        fecha = None
        if "fecha" in datos and datos["fecha"] is not None:
            texto_fecha = datos["fecha"]
            if not isinstance(texto_fecha, str) or not FORMATO_FECHA.fullmatch(texto_fecha):
                self._responder(400, _error("FECHA_INVALIDA", "La fecha debe tener formato AAAA-MM-DD"))
                return
            try:
                fecha = date.fromisoformat(texto_fecha)
            except ValueError:
                self._responder(400, _error("FECHA_INVALIDA", "La fecha debe ser una fecha válida"))
                return

        con = pedidos.conectar(self.ruta_db)
        try:
            pedido_id = pedidos.guardar_pedido(
                con,
                datos["email"],
                datos["carrito"],
                datos["zona"],
                datos.get("cupon"),
                fecha,
            )
            con.commit()
            pedido = pedidos.obtener_pedido(con, pedido_id)
            self._responder(
                201,
                {
                    "id": pedido_id,
                    "subtotal": pedido["subtotal"],
                    "descuento": pedido["descuento"],
                    "envio": pedido["envio"],
                    "total": pedido["total"],
                },
            )
        except CheckoutError as error:
            con.rollback()
            self._responder(422, _error(error.code, error.mensaje))
        except Exception:
            con.rollback()
            self._responder(500, _error("ERROR_INTERNO", "Ocurrió un error interno"))
        finally:
            con.close()

    def do_GET(self):
        coincide = RUTA_PEDIDO.fullmatch(self.path)
        if not coincide:
            self._responder(404, _error("RUTA_INEXISTENTE", "La ruta no existe"))
            return

        con = pedidos.conectar(self.ruta_db)
        try:
            pedido = pedidos.obtener_pedido(con, int(coincide.group(1)))
            if pedido is None:
                self._responder(404, _error("PEDIDO_INEXISTENTE", "El pedido no existe"))
                return
            self._responder(200, pedido)
        except Exception:
            self._responder(500, _error("ERROR_INTERNO", "Ocurrió un error interno"))
        finally:
            con.close()


def crear_servidor(ruta_db, puerto=0):
    con = pedidos.conectar(ruta_db)
    pedidos.crear_esquema(con)
    con.close()
    manejador = type("Manejador", (_Manejador,), {"ruta_db": ruta_db})
    return ThreadingHTTPServer(("127.0.0.1", puerto), manejador)


if __name__ == "__main__":
    servidor = crear_servidor("tienda.db", 8000)
    print("Escuchando en http://127.0.0.1:8000")
    servidor.serve_forever()
