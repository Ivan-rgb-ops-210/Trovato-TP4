import sqlite3
from decimal import Decimal

from checkout import CATALOGO, calcular_total

ESQUEMA = """
CREATE TABLE IF NOT EXISTS pedidos (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    email     TEXT NOT NULL,
    zona      TEXT NOT NULL,
    cupon     TEXT,
    subtotal  REAL NOT NULL DEFAULT 0,
    descuento REAL NOT NULL DEFAULT 0,
    envio     REAL NOT NULL DEFAULT 0,
    total     REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id       INTEGER NOT NULL REFERENCES pedidos(id),
    producto        TEXT NOT NULL,
    talle           TEXT NOT NULL,
    cantidad        INTEGER NOT NULL,
    precio_unitario REAL NOT NULL
);
"""

CENTAVO = Decimal("0.01")


def _decimal_de_sql(valor):
    return Decimal(str(valor)).quantize(CENTAVO)


def conectar(ruta):
    con = sqlite3.connect(ruta)
    con.row_factory = sqlite3.Row
    return con


def crear_esquema(con):
    con.executescript(ESQUEMA)


def guardar_pedido(con, email, carrito, zona, cupon=None, fecha=None):
    # Validar y calcular antes de abrir una transacción de escritura: si el
    # checkout falla, no debe quedar un pedido vacío en la base.
    resultado = calcular_total(carrito, zona, cupon, fecha)

    try:
        cursor = con.execute(
            "INSERT INTO pedidos (email, zona, cupon) VALUES (?, ?, ?)",
            (
                email.strip().lower(),
                zona.strip().upper(),
                cupon.strip().upper() if cupon and cupon.strip() else None,
            ),
        )
        pedido_id = cursor.lastrowid

        con.execute(
            "UPDATE pedidos SET subtotal = ?, descuento = ?, envio = ?, total = ? WHERE id = ?",
            (
                float(resultado["subtotal"]),
                float(resultado["descuento"]),
                float(resultado["envio"]),
                float(resultado["total"]),
                pedido_id,
            ),
        )

        for item in carrito:
            precio = CATALOGO[item["producto"]]
            con.execute(
                "INSERT INTO items (pedido_id, producto, talle, cantidad, precio_unitario)"
                " VALUES (?, ?, ?, ?, ?)",
                (pedido_id, item["producto"], item["talle"].strip().upper(), item["cantidad"], float(precio)),
            )

        con.commit()
        return pedido_id
    except Exception:
        con.rollback()
        raise


def obtener_pedido(con, pedido_id):
    fila = con.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if fila is None:
        return None

    items = con.execute(
        "SELECT * FROM items WHERE pedido_id = ? ORDER BY id", (pedido_id,)
    ).fetchall()

    return {
        "id": fila["id"],
        "email": fila["email"],
        "zona": fila["zona"],
        "cupon": fila["cupon"],
        "subtotal": _decimal_de_sql(fila["subtotal"]),
        "descuento": _decimal_de_sql(fila["descuento"]),
        "envio": _decimal_de_sql(fila["envio"]),
        "total": _decimal_de_sql(fila["total"]),
        "items": [
            {
                "producto": i["producto"],
                "talle": i["talle"],
                "cantidad": i["cantidad"],
                "precio_unitario": _decimal_de_sql(i["precio_unitario"]),
            }
            for i in items
        ],
    }


def pedidos_de(con, email):
    email = email.strip().lower()
    filas = con.execute(
        "SELECT id FROM pedidos WHERE email = ? ORDER BY id DESC", (email,)
    ).fetchall()
    return [obtener_pedido(con, f["id"]) for f in filas]
