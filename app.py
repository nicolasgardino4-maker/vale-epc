"""
Sistema de Vales - EPC
----------------------
Backend Flask, pensado para vivir en la nube (Render) con una base de datos
Postgres gratuita (Neon), sin depender de que ninguna PC esté prendida.

Variables de entorno que usa (se configuran en el panel de Render, no acá):
  DATABASE_URL   -> cadena de conexión a Postgres (te la da Neon)
  USUARIO        -> usuario para entrar al sistema
  CONTRASENA     -> contraseña para entrar al sistema

Si DATABASE_URL no está configurada (por ejemplo, mientras probás en tu
propia PC), el sistema usa automáticamente un archivo SQLite local
(vales.db) para que puedas probarlo sin necesidad de Postgres.

Cómo correrlo en la nube: ver README.md.
Cómo probarlo en tu PC (opcional, solo para desarrollo):
    pip install -r requirements.txt
    python app.py
    -> http://localhost:5000/panel
"""

import os
import datetime
from pathlib import Path

from flask import Flask, request, jsonify, render_template, Response
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

BASE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Configuración (variables de entorno, con valores por defecto para probar
# localmente sin tener que configurar nada)
# ---------------------------------------------------------------------------

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USUARIO = os.environ.get("USUARIO", "epc")
CONTRASENA = os.environ.get("CONTRASENA", "vales2026")

USANDO_POSTGRES = bool(DATABASE_URL)

if USANDO_POSTGRES:
    # Render/Neon a veces dan la URL con "postgres://"; SQLAlchemy necesita
    # "postgresql://".
    url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(url, poolclass=NullPool)
    AUTOINCREMENT = "SERIAL PRIMARY KEY"
else:
    db_path = BASE_DIR / "vales.db"
    engine = create_engine(f"sqlite:///{db_path}")
    AUTOINCREMENT = "INTEGER PRIMARY KEY AUTOINCREMENT"

app = Flask(__name__)


@app.before_request
def proteger_todo():
    auth = request.authorization
    if not auth or auth.username != USUARIO or auth.password != CONTRASENA:
        return Response(
            "Acceso restringido. Ingresá el usuario y la contraseña del sistema de Vales.",
            401,
            {"WWW-Authenticate": 'Basic realm="Sistema de Vales EPC"'},
        )


# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------

def init_db():
    with engine.begin() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS vales (
                id {AUTOINCREMENT},
                n_vale TEXT,
                fecha TEXT,
                obra TEXT,
                apellido_nombre TEXT NOT NULL,
                dni_legajo TEXT,
                observaciones TEXT,
                firma_solicitante TEXT,
                firma_autorizante TEXT,
                estado TEXT NOT NULL DEFAULT 'pendiente',
                ingresado INTEGER NOT NULL DEFAULT 0,
                creado_en TEXT NOT NULL,
                autorizado_en TEXT
            )
        """))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS vale_items (
                id {AUTOINCREMENT},
                vale_id INTEGER NOT NULL,
                codigo TEXT,
                descripcion TEXT,
                cantidad TEXT,
                entregado TEXT
            )
        """))


def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fila_a_dict(fila):
    return dict(fila._mapping)


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("panel.html")


@app.route("/nuevo")
def pagina_nuevo():
    return render_template("nuevo.html")


@app.route("/panel")
def pagina_panel():
    return render_template("panel.html")


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route("/api/vales", methods=["POST"])
def crear_vale():
    data = request.get_json(force=True) or {}

    apellido_nombre = (data.get("apellido_nombre") or "").strip()
    if not apellido_nombre:
        return jsonify({"error": "Falta Apellido y Nombre"}), 400

    items = data.get("items") or []
    items = [it for it in items if (it.get("descripcion") or "").strip()]
    if not items:
        return jsonify({"error": "Cargá al menos un ítem con descripción"}), 400

    insert_vale_sql = (
        """
        INSERT INTO vales (n_vale, fecha, obra, apellido_nombre, dni_legajo,
                            observaciones, firma_solicitante, estado, ingresado, creado_en)
        VALUES (:n_vale, :fecha, :obra, :apellido_nombre, :dni_legajo,
                :observaciones, :firma_solicitante, 'pendiente', 0, :creado_en)
        RETURNING id
        """
        if USANDO_POSTGRES
        else """
        INSERT INTO vales (n_vale, fecha, obra, apellido_nombre, dni_legajo,
                            observaciones, firma_solicitante, estado, ingresado, creado_en)
        VALUES (:n_vale, :fecha, :obra, :apellido_nombre, :dni_legajo,
                :observaciones, :firma_solicitante, 'pendiente', 0, :creado_en)
        """
    )

    with engine.begin() as conn:
        resultado = conn.execute(
            text(insert_vale_sql),
            {
                "n_vale": data.get("n_vale", "").strip(),
                "fecha": data.get("fecha", "").strip(),
                "obra": data.get("obra", "").strip(),
                "apellido_nombre": apellido_nombre,
                "dni_legajo": data.get("dni_legajo", "").strip(),
                "observaciones": data.get("observaciones", "").strip(),
                "firma_solicitante": data.get("firma_solicitante", ""),
                "creado_en": now_iso(),
            },
        )

        vale_id = resultado.scalar_one() if USANDO_POSTGRES else resultado.lastrowid

        for it in items:
            conn.execute(
                text("""
                    INSERT INTO vale_items (vale_id, codigo, descripcion, cantidad, entregado)
                    VALUES (:vale_id, :codigo, :descripcion, :cantidad, :entregado)
                """),
                {
                    "vale_id": vale_id,
                    "codigo": (it.get("codigo") or "").strip(),
                    "descripcion": (it.get("descripcion") or "").strip(),
                    "cantidad": (it.get("cantidad") or "").strip(),
                    "entregado": (it.get("entregado") or "").strip(),
                },
            )

    return jsonify({"id": vale_id}), 201


@app.route("/api/vales", methods=["GET"])
def listar_vales():
    estado = request.args.get("estado")
    with engine.connect() as conn:
        if estado in ("pendiente", "autorizado"):
            filas = conn.execute(
                text("SELECT * FROM vales WHERE estado = :estado ORDER BY id DESC"),
                {"estado": estado},
            ).fetchall()
        else:
            filas = conn.execute(text("SELECT * FROM vales ORDER BY id DESC")).fetchall()
    return jsonify([fila_a_dict(f) for f in filas])


@app.route("/api/vales/<int:vale_id>", methods=["GET"])
def detalle_vale(vale_id):
    with engine.connect() as conn:
        vale = conn.execute(
            text("SELECT * FROM vales WHERE id = :id"), {"id": vale_id}
        ).fetchone()
        if vale is None:
            return jsonify({"error": "No existe ese vale"}), 404
        items = conn.execute(
            text("SELECT * FROM vale_items WHERE vale_id = :id ORDER BY id"),
            {"id": vale_id},
        ).fetchall()

    resultado = fila_a_dict(vale)
    resultado["items"] = [fila_a_dict(i) for i in items]
    return jsonify(resultado)


@app.route("/api/vales/<int:vale_id>/autorizar", methods=["POST"])
def autorizar_vale(vale_id):
    data = request.get_json(force=True) or {}
    firma = data.get("firma_autorizante")
    if not firma:
        return jsonify({"error": "Falta la firma del autorizante"}), 400

    with engine.begin() as conn:
        existe = conn.execute(
            text("SELECT id FROM vales WHERE id = :id"), {"id": vale_id}
        ).fetchone()
        if existe is None:
            return jsonify({"error": "No existe ese vale"}), 404

        conn.execute(
            text("""
                UPDATE vales
                SET firma_autorizante = :firma, estado = 'autorizado', autorizado_en = :ahora
                WHERE id = :id
            """),
            {"firma": firma, "ahora": now_iso(), "id": vale_id},
        )
    return jsonify({"ok": True})


@app.route("/api/vales/<int:vale_id>/ingresado", methods=["POST"])
def marcar_ingresado(vale_id):
    data = request.get_json(force=True) or {}
    valor = 1 if data.get("ingresado", True) else 0
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE vales SET ingresado = :valor WHERE id = :id"),
            {"valor": valor, "id": vale_id},
        )
    return jsonify({"ok": True})


init_db()

if __name__ == "__main__":
    modo = "Postgres (nube)" if USANDO_POSTGRES else "SQLite local (solo prueba)"
    print(f"Base de datos: {modo}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
