import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "universidad_horarios.db")

DIAS_ORDEN = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
BLOQUES_HORARIOS = [
    ("07:00", "09:00"),
    ("09:00", "11:00"),
    ("11:00", "13:00"),
    ("14:00", "16:00"),
    ("16:00", "18:00"),
    ("18:00", "20:00"),
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS facultades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS carreras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        facultad_id INTEGER NOT NULL,
        UNIQUE(nombre, facultad_id),
        FOREIGN KEY (facultad_id) REFERENCES facultades(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS salones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT NOT NULL UNIQUE,
        capacidad INTEGER DEFAULT 40,
        edificio TEXT DEFAULT 'Edificio Principal'
    );

    CREATE TABLE IF NOT EXISTS profesores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        cedula TEXT DEFAULT '',
        email TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS disponibilidades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profesor_id INTEGER NOT NULL,
        dia TEXT NOT NULL,
        hora_inicio TEXT NOT NULL,
        hora_fin TEXT NOT NULL,
        UNIQUE(profesor_id, dia, hora_inicio, hora_fin),
        FOREIGN KEY (profesor_id) REFERENCES profesores(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS materias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        codigo TEXT DEFAULT '',
        carrera_id INTEGER NOT NULL,
        semestre TEXT DEFAULT '1er Semestre',
        UNIQUE(nombre, carrera_id),
        FOREIGN KEY (carrera_id) REFERENCES carreras(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS carga_academica (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profesor_id INTEGER NOT NULL,
        materia_id INTEGER NOT NULL,
        seccion TEXT DEFAULT 'Sección A',
        bloques_semanales INTEGER DEFAULT 1,
        salon_preferido TEXT DEFAULT '',
        dia_fijo TEXT DEFAULT '',
        hora_inicio_fija TEXT DEFAULT '',
        hora_fin_fija TEXT DEFAULT '',
        UNIQUE(profesor_id, materia_id, seccion),
        FOREIGN KEY (profesor_id) REFERENCES profesores(id) ON DELETE CASCADE,
        FOREIGN KEY (materia_id) REFERENCES materias(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS asignaciones_horario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        carga_id INTEGER NOT NULL,
        profesor_id INTEGER NOT NULL,
        materia_id INTEGER NOT NULL,
        salon_id INTEGER NOT NULL,
        dia TEXT NOT NULL,
        hora_inicio TEXT NOT NULL,
        hora_fin TEXT NOT NULL,
        estado TEXT DEFAULT 'Confirmado',
        FOREIGN KEY (carga_id) REFERENCES carga_academica(id) ON DELETE CASCADE,
        FOREIGN KEY (profesor_id) REFERENCES profesores(id) ON DELETE CASCADE,
        FOREIGN KEY (materia_id) REFERENCES materias(id) ON DELETE CASCADE,
        FOREIGN KEY (salon_id) REFERENCES salones(id) ON DELETE CASCADE
    );
    """)

    # Insertar salones predeterminados si no hay ninguno
    cursor.execute("SELECT COUNT(*) as total FROM salones")
    if cursor.fetchone()["total"] == 0:
        salones_default = [
            ("Aula 101", 40, "Edificio A - Planta Baja"),
            ("Aula 102", 40, "Edificio A - Planta Baja"),
            ("Aula 103", 35, "Edificio A - Planta Baja"),
            ("Aula 201", 45, "Edificio A - Piso 1"),
            ("Aula 202", 45, "Edificio A - Piso 1"),
            ("Lab Computación 1", 30, "Edificio B - Laboratorios"),
            ("Lab Computación 2", 30, "Edificio B - Laboratorios"),
            ("Aula Magna 301", 80, "Edificio C - Ciencias"),
            ("Aula 302", 40, "Edificio C - Ciencias"),
            ("Aula 303", 40, "Edificio C - Ciencias"),
        ]
        cursor.executemany(
            "INSERT INTO salones (codigo, capacidad, edificio) VALUES (?, ?, ?)",
            salones_default
        )

    conn.commit()
    conn.close()


def clear_all_data(keep_salones=True):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM asignaciones_horario;")
    cursor.execute("DELETE FROM carga_academica;")
    cursor.execute("DELETE FROM disponibilidades;")
    cursor.execute("DELETE FROM materias;")
    cursor.execute("DELETE FROM profesores;")
    cursor.execute("DELETE FROM carreras;")
    cursor.execute("DELETE FROM facultades;")
    if not keep_salones:
        cursor.execute("DELETE FROM salones;")
    conn.commit()
    conn.close()


def get_or_create_facultad(cursor, nombre):
    nombre = nombre.strip() or "Facultad General"
    cursor.execute("SELECT id FROM facultades WHERE LOWER(nombre) = LOWER(?)", (nombre,))
    row = cursor.fetchone()
    if row:
        return row["id"]
    cursor.execute("INSERT INTO facultades (nombre) VALUES (?)", (nombre,))
    return cursor.lastrowid


def get_or_create_carrera(cursor, nombre, facultad_id):
    nombre = nombre.strip() or "Carrera General"
    cursor.execute(
        "SELECT id FROM carreras WHERE LOWER(nombre) = LOWER(?) AND facultad_id = ?",
        (nombre, facultad_id)
    )
    row = cursor.fetchone()
    if row:
        return row["id"]
    cursor.execute(
        "INSERT INTO carreras (nombre, facultad_id) VALUES (?, ?)",
        (nombre, facultad_id)
    )
    return cursor.lastrowid


def get_or_create_profesor(cursor, nombre, cedula="", email=""):
    nombre = nombre.strip()
    cursor.execute("SELECT id FROM profesores WHERE LOWER(nombre) = LOWER(?)", (nombre,))
    row = cursor.fetchone()
    if row:
        if cedula or email:
            cursor.execute(
                "UPDATE profesores SET cedula = COALESCE(NULLIF(?, ''), cedula), email = COALESCE(NULLIF(?, ''), email) WHERE id = ?",
                (cedula, email, row["id"])
            )
        return row["id"]
    cursor.execute(
        "INSERT INTO profesores (nombre, cedula, email) VALUES (?, ?, ?)",
        (nombre, cedula, email)
    )
    return cursor.lastrowid


def get_or_create_materia(cursor, nombre, carrera_id, codigo="", semestre="1er Semestre"):
    nombre = nombre.strip()
    cursor.execute(
        "SELECT id FROM materias WHERE LOWER(nombre) = LOWER(?) AND carrera_id = ?",
        (nombre, carrera_id)
    )
    row = cursor.fetchone()
    if row:
        return row["id"]
    cursor.execute(
        "INSERT INTO materias (nombre, codigo, carrera_id, semestre) VALUES (?, ?, ?, ?)",
        (nombre, codigo, carrera_id, semestre)
    )
    return cursor.lastrowid


def get_or_create_salon(cursor, codigo, capacidad=40, edificio="Edificio Principal"):
    codigo = codigo.strip()
    cursor.execute("SELECT id FROM salones WHERE LOWER(codigo) = LOWER(?)", (codigo,))
    row = cursor.fetchone()
    if row:
        return row["id"]
    cursor.execute(
        "INSERT INTO salones (codigo, capacidad, edificio) VALUES (?, ?, ?)",
        (codigo, capacidad, edificio)
    )
    return cursor.lastrowid
