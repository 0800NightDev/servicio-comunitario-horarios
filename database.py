import sqlite3
import os
import sys
import re
import unicodedata


def _normalizar_espacios(valor):
    try:
        texto = unicodedata.normalize("NFKC", str(valor or ""))
    except Exception:
        texto = str(valor or "")
    return re.sub(r"\s+", " ", texto).strip()


def validar_profesor_basico(nombre, cedula="", email="", requerir_cedula=True):
    """Valida los datos básicos de un docente y retorna una lista de errores."""
    errores = []
    nombre_norm = _normalizar_espacios(nombre).upper()
    cedula_norm = _normalizar_espacios(cedula).upper().replace(" ", "")
    email_norm = _normalizar_espacios(email).lower()

    if not nombre_norm:
        errores.append("Indique el nombre y apellido del docente.")
    else:
        if len(nombre_norm.split()) < 2:
            errores.append("Indique el nombre y el apellido del docente.")
        caracteres_validos = " -'’"
        if any(not (ch.isalpha() or ch in caracteres_validos) for ch in nombre_norm):
            errores.append("El nombre solo admite letras, espacios, guiones y apóstrofos.")

    if not cedula_norm:
        if requerir_cedula:
            errores.append("Indique la cédula del docente.")
    elif not re.fullmatch(r"(V|E)?-?\d{6,10}", cedula_norm):
        errores.append("La cédula debe tener entre 6 y 10 dígitos, con prefijo opcional V o E (por ejemplo: V-12345678).")

    if email_norm and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email_norm):
        errores.append("El correo electrónico no tiene un formato válido.")

    return errores


def obtener_ruta_base():
    """Retorna el directorio base correcto ya sea en script .py o empaquetado (.exe / binario)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = obtener_ruta_base()
DB_PATH = os.path.join(BASE_DIR, "universidad_horarios.db")

DIAS_ORDEN = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
BLOQUES_HORARIOS = [
    ("07:00", "09:00"),
    ("09:00", "11:00"),
    ("11:00", "13:00"),
    ("14:00", "16:00"),
    ("16:00", "18:00"),
    ("18:00", "20:00"),
]

# Inventario oficial de ambientes por piso. La numeración de los salones es
# global y consecutiva: P1-01..P1-08, P2-09..P2-22, P3-23..P3-27 y P4-28..P4-37.
PISOS_SALONES = {1: 8, 2: 14, 3: 5, 4: 10}
CAPACIDAD_DEFECTO = 45
AMBIENTES_ESPECIALES = [
    ("SATELITAL-01", 45, "Satelital 1"),
    ("SATELITAL-02", 45, "Satelital 2"),
    ("VIRTUAL-01", 100, "Campus Virtual"),
    ("VIRTUAL-02", 100, "Campus Virtual"),
]
SALONES_VERSION = "2"


def generar_codigos_pisos():
    """Genera los pares (piso, código) con numeración global consecutiva."""
    resultado = []
    numero = 0
    for piso, cantidad in PISOS_SALONES.items():
        for _ in range(cantidad):
            numero += 1
            resultado.append((piso, f"P{piso}-{numero:02d}"))
    return resultado


def salones_predeterminados():
    """Retorna [(codigo, capacidad, edificio), ...] con el inventario oficial."""
    return [
        (codigo, CAPACIDAD_DEFECTO, f"Piso {piso}")
        for piso, codigo in generar_codigos_pisos()
    ] + list(AMBIENTES_ESPECIALES)


def codigos_ambientes_predeterminados():
    return [codigo for codigo, _, _ in salones_predeterminados()]


def _salones_antiguos_predeterminados():
    """Códigos del inventario anterior (7 salones por piso + virtuales)."""
    return {
        f"P{p}-{n:02d}"
        for p in range(1, 5)
        for n in range(1, 8)
    } | {"VIRTUAL-01", "VIRTUAL-02"}


def _obtener_config(cursor, clave):
    cursor.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
    row = cursor.fetchone()
    return row["valor"] if row else None


def _guardar_config(cursor, clave, valor):
    cursor.execute(
        "INSERT INTO configuracion (clave, valor) VALUES (?, ?) "
        "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor",
        (clave, str(valor)),
    )


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def _migrar_salones(cursor):
    """Crea o actualiza el inventario de ambientes conservando la información existente."""
    if _obtener_config(cursor, "salones_version") == SALONES_VERSION:
        return

    predeterminados = salones_predeterminados()
    existentes = {
        row["codigo"].upper(): dict(row)
        for row in cursor.execute(
            "SELECT id, codigo, capacidad, edificio FROM salones"
        ).fetchall()
    }

    if not existentes:
        cursor.executemany(
            "INSERT INTO salones (codigo, capacidad, edificio) VALUES (?, ?, ?)",
            predeterminados,
        )
        _guardar_config(cursor, "salones_version", SALONES_VERSION)
        return

    antiguos = _salones_antiguos_predeterminados()

    # Verificar si alguno de los salones del inventario anterior está en uso.
    cursor.execute("SELECT COUNT(*) AS total FROM asignaciones_horario")
    hay_asignaciones = cursor.fetchone()["total"] > 0
    cursor.execute(
        "SELECT DISTINCT TRIM(salon_preferido) AS codigo FROM carga_academica "
        "WHERE salon_preferido IS NOT NULL AND TRIM(salon_preferido) <> ''"
    )
    cargas_en_uso = {
        row["codigo"].upper() for row in cursor.fetchall() if row["codigo"]
    }
    en_uso = hay_asignaciones or bool(cargas_en_uso & antiguos)

    if not en_uso:
        # Sin referencias: reemplazar el inventario viejo por el nuevo,
        # conservando la capacidad de los códigos que se mantienen iguales.
        cursor.executemany(
            "DELETE FROM salones WHERE UPPER(codigo) = ?",
            [(codigo,) for codigo in antiguos],
        )
        filas = []
        for codigo, capacidad, edificio in predeterminados:
            anterior = existentes.get(codigo)
            filas.append(
                (codigo, anterior["capacidad"] if anterior else capacidad, edificio)
            )
        cursor.executemany(
            "INSERT OR IGNORE INTO salones (codigo, capacidad, edificio) VALUES (?, ?, ?)",
            filas,
        )
    else:
        # Con referencias: renombrar los códigos antiguos a la nueva numeración
        # global (por posición dentro de cada piso) sin perder asignaciones y
        # luego completar los faltantes.
        nuevos_por_piso = {}
        for piso, codigo in generar_codigos_pisos():
            nuevos_por_piso.setdefault(piso, []).append(codigo)

        for piso in range(1, 5):
            nuevos = nuevos_por_piso.get(piso, [])
            for indice, n in enumerate(range(1, 8)):
                viejo = f"P{piso}-{n:02d}"
                if viejo not in existentes or indice >= len(nuevos):
                    continue
                nuevo = nuevos[indice]
                if viejo == nuevo or nuevo in existentes:
                    continue
                try:
                    cursor.execute(
                        "UPDATE salones SET codigo = ? WHERE UPPER(codigo) = ?",
                        (nuevo, viejo),
                    )
                    cursor.execute(
                        "UPDATE carga_academica SET salon_preferido = ? "
                        "WHERE UPPER(TRIM(salon_preferido)) = ?",
                        (nuevo, viejo),
                    )
                except sqlite3.IntegrityError:
                    pass

        existentes = {
            row["codigo"].upper()
            for row in cursor.execute("SELECT codigo FROM salones").fetchall()
        }
        for codigo, capacidad, edificio in predeterminados:
            if codigo not in existentes:
                cursor.execute(
                    "INSERT INTO salones (codigo, capacidad, edificio) VALUES (?, ?, ?)",
                    (codigo, capacidad, edificio),
                )

    _guardar_config(cursor, "salones_version", SALONES_VERSION)


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
        edificio TEXT DEFAULT 'Edificio Principal',
        es_camillas INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS profesores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        cedula TEXT DEFAULT '',
        email TEXT DEFAULT '',
        mencion TEXT DEFAULT ''
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
        unidad_credito INTEGER DEFAULT 0,
        mencion TEXT DEFAULT '',
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
        compartidos TEXT DEFAULT '',
        UNIQUE(profesor_id, materia_id, seccion),
        FOREIGN KEY (profesor_id) REFERENCES profesores(id) ON DELETE CASCADE,
        FOREIGN KEY (materia_id) REFERENCES materias(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS configuracion (
        clave TEXT PRIMARY KEY,
        valor TEXT
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

    CREATE INDEX IF NOT EXISTS idx_asignaciones_dia ON asignaciones_horario(dia);
    CREATE INDEX IF NOT EXISTS idx_asignaciones_profesor ON asignaciones_horario(profesor_id);
    CREATE INDEX IF NOT EXISTS idx_asignaciones_salon ON asignaciones_horario(salon_id);
    CREATE INDEX IF NOT EXISTS idx_asignaciones_materia ON asignaciones_horario(materia_id);
    CREATE INDEX IF NOT EXISTS idx_carga_profesor ON carga_academica(profesor_id);
    CREATE INDEX IF NOT EXISTS idx_materias_carrera ON materias(carrera_id);
    """);

    try:
        cursor.execute("ALTER TABLE profesores ADD COLUMN condicion TEXT DEFAULT 'Contratado/a'")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE salones ADD COLUMN es_camillas INTEGER DEFAULT 0")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE profesores ADD COLUMN mencion TEXT DEFAULT ''")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE materias ADD COLUMN unidad_credito INTEGER DEFAULT 0")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE materias ADD COLUMN mencion TEXT DEFAULT ''")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE carga_academica ADD COLUMN compartidos TEXT DEFAULT ''")
    except Exception:
        pass

    # Crear/migrar el inventario oficial de ambientes.
    _migrar_salones(cursor)

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


def get_or_create_profesor(cursor, nombre, cedula="", email="", condicion="Contratado/a", mencion=""):
    nombre = nombre.strip()
    mencion = str(mencion or "").strip()
    cursor.execute("SELECT id FROM profesores WHERE LOWER(nombre) = LOWER(?)", (nombre,))
    row = cursor.fetchone()
    if row:
        if cedula or email or condicion or mencion:
            cursor.execute(
                """UPDATE profesores 
                   SET cedula = COALESCE(NULLIF(?, ''), cedula), 
                       email = COALESCE(NULLIF(?, ''), email),
                       condicion = COALESCE(NULLIF(?, ''), condicion),
                       mencion = COALESCE(NULLIF(?, ''), mencion)
                   WHERE id = ?""",
                (cedula, email, condicion, mencion, row["id"])
            )
        return row["id"]
    cursor.execute(
        "INSERT INTO profesores (nombre, cedula, email, condicion, mencion) VALUES (?, ?, ?, ?, ?)",
        (nombre, cedula, email, condicion, mencion)
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


def get_or_create_salon(cursor, codigo, capacidad=CAPACIDAD_DEFECTO, edificio="Edificio Principal"):
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


def registrar_ficha_docente(datos):
    """Registra manualmente los datos de un docente y sus materias."""
    docente = _normalizar_espacios(datos.get("docente")).upper()
    cedula = _normalizar_espacios(datos.get("cedula")).upper().replace(" ", "")
    correo = _normalizar_espacios(datos.get("correo")).lower()
    condicion = str(datos.get("condicion") or "").strip()

    disponibilidades_guardadas = datos.get("disponibilidades") or []
    disponibilidades = list(dict.fromkeys(
        tuple(bloque) for bloque in disponibilidades_guardadas
    ))
    materias_input = datos.get("materias") or []

    codigos_existentes = {
        str(codigo or "").strip().upper()
        for codigo in obtener_codigos_materia()
    }

    materias = []
    seen = set()
    for indice, materia_input in enumerate(materias_input, 1):
        if not isinstance(materia_input, dict):
            continue

        materia = _normalizar_espacios(materia_input.get("materia")).upper()
        carrera = _normalizar_espacios(materia_input.get("carrera"))
        mencion = _normalizar_espacios(materia_input.get("mencion"))
        ambiente = _normalizar_espacios(materia_input.get("ambiente")).upper()
        codigo = _normalizar_espacios(materia_input.get("codigo")).upper().replace(" ", "")
        ciclo = _normalizar_espacios(materia_input.get("ciclo")).upper()
        seccion = _normalizar_espacios(materia_input.get("seccion"))
        unidad_credito = _normalizar_espacios(materia_input.get("unidad_credito"))
        compartidos = _normalizar_espacios(materia_input.get("compartidos"))

        if not any([materia, carrera, mencion, ambiente, codigo, ciclo, seccion, unidad_credito, compartidos]):
            continue
        if not materia:
            materias.append({"_error": f"Fila {indice}: indique el nombre de la materia."})
            continue
        if not carrera:
            materias.append({"_error": f"Materia '{materia}': seleccione la carrera."})
            continue
        if codigo and codigo not in codigos_existentes and not codigo.isalnum():
            materias.append({"_error": f"Materia '{materia}': el código solo admite letras y números."})
            continue
        if seccion and not seccion.isdigit():
            materias.append({"_error": f"Materia '{materia}': la sección solo admite números."})
            continue
        if unidad_credito and not unidad_credito.isdigit():
            materias.append({"_error": f"Materia '{materia}': la unidad de crédito solo admite números."})
            continue

        key = (materia, carrera.lower(), mencion.lower(), seccion)
        if key in seen:
            materias.append({"_error": f"Materia '{materia}' sección {seccion or 'única'} duplicada."})
            continue
        seen.add(key)
        materias.append({
            "materia": materia,
            "carrera": carrera,
            "mencion": mencion,
            "ambiente": ambiente,
            "codigo": codigo,
            "ciclo": ciclo,
            "seccion": seccion,
            "unidad_credito": unidad_credito,
            "compartidos": compartidos,
        })

    errores = validar_profesor_basico(docente, cedula, correo, requerir_cedula=True)
    errores.extend(materia["_error"] for materia in materias if "_error" in materia)
    materias_validas = [m for m in materias if "_error" not in m]
    if not materias_validas:
        errores.append("Indique al menos una materia.")
    if not disponibilidades:
        errores.append("Seleccione al menos una franja de disponibilidad.")
    for bloque in disponibilidades:
        if (
            len(bloque) != 3
            or bloque[0] not in DIAS_ORDEN
            or not all(
                isinstance(hora, str)
                and len(hora) == 5
                and hora[2] == ":"
                and hora[:2].isdigit()
                and hora[3:].isdigit()
                and 0 <= int(hora[:2]) <= 23
                and 0 <= int(hora[3:]) <= 59
                for hora in bloque[1:]
            )
            or bloque[1] >= bloque[2]
        ):
            errores.append("La disponibilidad contiene una franja inválida.")
            break
    if errores:
        return {"insertados": 0, "errores": errores}

    conn = get_connection()
    try:
        cursor = conn.cursor()
        facultad_admin = get_or_create_facultad(cursor, "Facultad de Administración")
        facultad_educacion = get_or_create_facultad(cursor, "Facultad de Educación")
        mencies = {item["mencion"] for item in materias_validas if item["mencion"]}
        mencion_unica = next(iter(mencies)) if len(mencies) == 1 else ""
        profesor_id = get_or_create_profesor(
            cursor, docente, cedula, correo,
            condicion=condicion, mencion=mencion_unica,
        )

        for ambiente in {item["ambiente"] for item in materias_validas if item["ambiente"]}:
            get_or_create_salon(cursor, ambiente)

        cursor.execute("DELETE FROM disponibilidades WHERE profesor_id = ?", (profesor_id,))
        cursor.executemany(
            """INSERT OR IGNORE INTO disponibilidades (profesor_id, dia, hora_inicio, hora_fin)
               VALUES (?, ?, ?, ?)""",
            [(profesor_id, dia, inicio, fin) for dia, inicio, fin in disponibilidades],
        )

        carreras_cache = {}
        for indice, item in enumerate(materias_validas, 1):
            carrera_full = item["carrera"]
            if item["mencion"]:
                carrera_full = f"{item['carrera']} - {item['mencion']}"
            criterio_carrera = ""
            admin_like = any(k in carrera_full.upper() for k in (
                "ADMINISTR", "RECURSOS HUMANOS", "RECURSOS MATERIALES", "MERCADEO",
                "INFORMÁTICA", "ORGANIZACIÓN Y SISTEMAS", "OYS",
            ))
            facultad_id = facultad_admin if admin_like else facultad_educacion
            if carrera_full not in carreras_cache:
                carreras_cache[carrera_full] = get_or_create_carrera(cursor, carrera_full, facultad_id)
            carrera_id = carreras_cache[carrera_full]
            codigo_materia = item["codigo"] or f"MAT-{indice:03d}"
            materia_id = get_or_create_materia(
                cursor, item["materia"], carrera_id,
                codigo=codigo_materia, semestre=item["ciclo"],
            )
            cursor.execute(
                """UPDATE materias
                   SET codigo = COALESCE(NULLIF(?, ''), codigo),
                       semestre = COALESCE(NULLIF(?, ''), semestre),
                       unidad_credito = ?, mencion = ?
                   WHERE id = ?""",
                (
                    item["codigo"],
                    item["ciclo"],
                    int(item["unidad_credito"]) if item["unidad_credito"] else 0,
                    item["mencion"],
                    materia_id,
                ),
            )
            seccion_final = item["seccion"] or str(10100 + indice)
            cursor.execute(
                """INSERT INTO carga_academica
                     (profesor_id, materia_id, seccion, bloques_semanales, salon_preferido,
                      dia_fijo, hora_inicio_fija, hora_fin_fija, compartidos)
                   VALUES (?, ?, ?, 1, ?, '', '', '', ?)
                   ON CONFLICT(profesor_id, materia_id, seccion) DO UPDATE SET
                       salon_preferido = excluded.salon_preferido,
                       compartidos = excluded.compartidos""",
                (profesor_id, materia_id, seccion_final, item["ambiente"], item["compartidos"]),
            )

        conn.commit()
        return {"insertados": len(materias_validas), "docente": docente, "errores": []}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def obtener_codigos_materia():
    """Retorna los códigos de materia registrados en la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT TRIM(codigo) AS codigo FROM materias "
        "WHERE TRIM(COALESCE(codigo, '')) <> '' ORDER BY UPPER(TRIM(codigo)) ASC"
    )
    codigos = [row["codigo"] for row in cursor.fetchall()]
    conn.close()
    return codigos


def obtener_secciones():
    """Retorna las secciones registradas en la base de datos, ordenadas numéricamente."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT TRIM(seccion) AS seccion FROM carga_academica "
        "WHERE TRIM(COALESCE(seccion, '')) <> '' "
        "ORDER BY LENGTH(TRIM(seccion)) ASC, CAST(TRIM(seccion) AS INTEGER) ASC, TRIM(seccion) ASC"
    )
    secciones = [row["seccion"] for row in cursor.fetchall()]
    conn.close()
    return secciones


def obtener_salones():
    """Retorna todos los ambientes registrados con su capacidad, edificio y tipo."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, codigo, capacidad, edificio, COALESCE(es_camillas, 0) AS es_camillas "
        "FROM salones ORDER BY id ASC"
    )
    salones = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return salones


def obtener_salon(codigo):
    """Retorna el ambiente indicado o None si no existe."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, codigo, capacidad, edificio, COALESCE(es_camillas, 0) AS es_camillas "
        "FROM salones WHERE UPPER(codigo) = UPPER(?)",
        (str(codigo).strip(),),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def obtener_capacidad_salon(codigo, por_defecto=CAPACIDAD_DEFECTO):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT capacidad FROM salones WHERE UPPER(codigo) = UPPER(?)",
        (str(codigo).strip(),),
    )
    row = cursor.fetchone()
    conn.close()
    return int(row["capacidad"]) if row and row["capacidad"] is not None else por_defecto


def actualizar_capacidad_salon(codigo, capacidad):
    """Actualiza la capacidad de un ambiente (funciona también para los manuales)."""
    return actualizar_datos_ambiente(codigo, capacidad=capacidad)


def actualizar_datos_ambiente(codigo, capacidad=None, es_camillas=None, edificio=None):
    """Actualiza capacidad, tipo de camillas y/o edificio de un ambiente."""
    campos = []
    valores = []

    if capacidad is not None:
        try:
            capacidad = int(capacidad)
        except (TypeError, ValueError):
            return False
        if capacidad <= 0:
            return False
        campos.append("capacidad = ?")
        valores.append(capacidad)

    if es_camillas is not None:
        campos.append("es_camillas = ?")
        valores.append(1 if es_camillas else 0)

    if edificio is not None:
        campos.append("edificio = ?")
        valores.append(str(edificio).strip())

    if not campos:
        return False

    valores.append(str(codigo).strip())
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE salones SET {', '.join(campos)} WHERE UPPER(codigo) = UPPER(?)",
        valores,
    )
    actualizados = cursor.rowcount
    conn.commit()
    conn.close()
    return actualizados > 0


def eliminar_salon(codigo):
    """Elimina un ambiente individualmente y libera las cargas que lo usaban."""
    codigo = str(codigo).strip().upper()
    if not codigo:
        return False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM salones WHERE UPPER(codigo) = UPPER(?)", (codigo,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    cursor.execute(
        "UPDATE carga_academica SET salon_preferido = '' "
        "WHERE UPPER(TRIM(salon_preferido)) = ?",
        (codigo,),
    )
    cursor.execute("DELETE FROM salones WHERE id = ?", (row["id"],))
    conn.commit()
    conn.close()
    return True


def obtener_profesores():
    """Retorna todos los docentes registrados con sus datos personales."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nombre, COALESCE(cedula, '') AS cedula, "
        "COALESCE(email, '') AS email, COALESCE(condicion, 'Contratado/a') AS condicion "
        "FROM profesores ORDER BY nombre ASC"
    )
    profesores = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return profesores


def _normalizar_materia(nombre):
    normalizado = unicodedata.normalize("NFD", str(nombre or "").strip().casefold())
    sin_acentos = "".join(
        caracter for caracter in normalizado
        if unicodedata.category(caracter) != "Mn"
    )
    return " ".join(sin_acentos.split())


def obtener_materias_profesor(nombre):
    """Devuelve las materias actualmente asignadas al docente, sin duplicados."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DISTINCT m.nombre
        FROM carga_academica ca
        JOIN profesores p ON p.id = ca.profesor_id
        JOIN materias m ON m.id = ca.materia_id
        WHERE LOWER(p.nombre) = LOWER(?)
        ORDER BY m.nombre COLLATE NOCASE
        """,
        (str(nombre).strip(),),
    )
    materias = [row["nombre"] for row in cursor.fetchall()]
    conn.close()
    return materias


def obtener_nombres_materias():
    """Retorna todos los nombres de materia registrados en la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT TRIM(nombre) AS nombre FROM materias "
        "WHERE TRIM(COALESCE(nombre, '')) <> '' ORDER BY nombre COLLATE NOCASE ASC"
    )
    nombres = [row["nombre"] for row in cursor.fetchall()]
    conn.close()
    return nombres


def obtener_cargas_docente(nombre):
    """Retorna detalle completo de las cargas académicas asociadas al docente."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            ca.id AS carga_id,
            ca.seccion,
            ca.salon_preferido,
            COALESCE(ca.compartidos, '') AS compartidos,
            ca.bloques_semanales,
            m.nombre AS materia,
            m.codigo,
            COALESCE(m.semestre, '') AS ciclo,
            COALESCE(m.unidad_credito, 0) AS unidad_credito,
            COALESCE(m.mencion, '') AS mencion,
            c.nombre AS carrera
        FROM carga_academica ca
        JOIN profesores p ON p.id = ca.profesor_id
        JOIN materias m ON m.id = ca.materia_id
        JOIN carreras c ON c.id = m.carrera_id
        WHERE LOWER(p.nombre) = LOWER(?)
        ORDER BY m.nombre COLLATE NOCASE, c.nombre COLLATE NOCASE
        """,
        (str(nombre).strip(),),
    )
    cargas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return cargas


def obtener_opciones_carga():
    """Opciones académicas disponibles, derivadas de la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    codigos = [
        row["codigo"].strip()
        for row in cursor.execute(
            "SELECT DISTINCT TRIM(codigo) AS codigo FROM materias "
            "WHERE TRIM(COALESCE(codigo, '')) <> '' ORDER BY UPPER(TRIM(codigo)) ASC"
        ).fetchall()
    ]
    secciones = [
        row["seccion"].strip()
        for row in cursor.execute(
            "SELECT DISTINCT TRIM(seccion) AS seccion FROM carga_academica "
            "WHERE TRIM(COALESCE(seccion, '')) <> '' "
            "ORDER BY LENGTH(TRIM(seccion)) ASC, CAST(TRIM(seccion) AS INTEGER) ASC, TRIM(seccion) ASC"
        ).fetchall()
    ]
    carreras = [
        row["nombre"].strip()
        for row in cursor.execute(
            "SELECT DISTINCT nombre FROM carreras WHERE TRIM(nombre) <> '' ORDER BY nombre COLLATE NOCASE ASC"
        ).fetchall()
    ]
    mencies = [
        row["mencion"].strip()
        for row in cursor.execute(
            "SELECT DISTINCT TRIM(mencion) AS mencion FROM materias "
            "WHERE TRIM(COALESCE(mencion, '')) <> '' ORDER BY mencion COLLATE NOCASE ASC"
        ).fetchall()
    ]
    ambientes = [
        row["codigo"].strip()
        for row in cursor.execute(
            "SELECT DISTINCT TRIM(salon_preferido) AS codigo FROM carga_academica "
            "WHERE TRIM(COALESCE(salon_preferido, '')) <> '' ORDER BY codigo COLLATE NOCASE ASC"
        ).fetchall()
    ]
    conn.close()
    return {
        "codigos": codigos,
        "secciones": secciones,
        "carreras": carreras,
        "menciones": mencies,
        "ambientes": ambientes,
    }


def actualizar_ficha_docente_completa(nombre_actual, datos):
    """Guarda todos los datos del docente y sus cargas académicas detalle por materia."""
    def normal_texto(valor):
        return str(valor or "").strip()

    docente_actual = normal_texto(nombre_actual)
    nombre_nuevo = _normalizar_espacios(datos.get("nuevo_nombre")).upper()
    cedula = _normalizar_espacios(datos.get("cedula")).upper().replace(" ", "")
    email = _normalizar_espacios(datos.get("email")).lower()
    if not docente_actual or not nombre_nuevo:
        return False, "Indique el nombre y apellido del docente."

    disponibilidades_guardadas = datos.get("disponibilidades", None)
    if disponibilidades_guardadas is not None:
        disponibilidades = list(dict.fromkeys(
            tuple(bloque) for bloque in disponibilidades_guardadas
        ))
    else:
        disponibilidades = None

    materias = list(datos.get("materias") or [])
    errores = validar_profesor_basico(nombre_nuevo, cedula, email, requerir_cedula=True)
    codigos_existentes = {
        str(codigo or "").strip().upper()
        for codigo in obtener_codigos_materia()
    }

    for indice, materia in enumerate(materias, 1):
        codigo = normal_texto(materia.get("codigo")).upper()
        seccion = normal_texto(materia.get("seccion"))
        uc = normal_texto(materia.get("unidad_credito"))
        if codigo and codigo not in codigos_existentes and not codigo.isalnum():
            errores.append(f"Materia {indice}: el código solo admite letras y números.")
        if seccion and not seccion.isdigit():
            errores.append(f"Materia {indice}: la sección solo admite números.")
        if uc and not uc.isdigit():
            errores.append(f"Materia {indice}: la unidad de crédito solo admite números.")
    if errores:
        return False, " ".join(errores)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM profesores WHERE LOWER(nombre) = LOWER(?)",
            (docente_actual,),
        )
        row = cursor.fetchone()
        if not row:
            return False, "No se encontró el docente indicado."
        docente_id = row["id"]

        cursor.execute(
            "SELECT id FROM profesores WHERE LOWER(nombre) = LOWER(?) AND id <> ?",
            (nombre_nuevo, docente_id),
        )
        if cursor.fetchone():
            return False, "Ya existe otro docente con ese nombre."

        cursor.execute(
            "UPDATE profesores SET nombre = ?, cedula = ?, email = ?, condicion = ?, mencion = ? WHERE id = ?",
            (
                nombre_nuevo,
                cedula,
                email,
                normal_texto(datos.get("condicion") or "Contratado/a"),
                normal_texto(datos.get("mencion")),
                docente_id,
            ),
        )

        if disponibilidades is not None:
            cursor.execute("DELETE FROM disponibilidades WHERE profesor_id = ?", (docente_id,))
            cursor.executemany(
                """
                INSERT OR IGNORE INTO disponibilidades (profesor_id, dia, hora_inicio, hora_fin)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (docente_id, bloque[0], bloque[1], bloque[2])
                    for bloque in disponibilidades
                    if len(bloque) == 3 and bloque[0] in DIAS_ORDEN and bloque[1] < bloque[2]
                ],
            )

        cargas_actuales = [
            dict(row_)
            for row_ in cursor.execute(
                "SELECT id, materia_id FROM carga_academica WHERE profesor_id = ?",
                (docente_id,),
            ).fetchall()
        ]
        ids_deseados = []

        for indice, materia in enumerate(materias, 1):
            nombre_materia = normal_texto(materia.get("materia"))
            carrera = normal_texto(materia.get("carrera"))
            mencion = normal_texto(materia.get("mencion"))
            if not nombre_materia or not carrera:
                continue

            carrera_full = f"{carrera} - {mencion}" if mencion else carrera
            clave_carrera = _normalizar_materia(carrera_full)
            admin_like = any(
                palabra in clave_carrera
                for palabra in (
                    "administracion", "recursos humanos", "recursos materiales",
                    "mercadeo", "informatica", "organizacion y sistemas", "oys",
                )
            )
            facultad = "Facultad de Administración" if admin_like else "Facultad de Educación"
            facultad_id = get_or_create_facultad(cursor, facultad)
            carrera_id = get_or_create_carrera(cursor, carrera_full, facultad_id)
            codigo = normal_texto(materia.get("codigo")).upper()
            ciclo = normal_texto(materia.get("ciclo")).upper()
            unidad_credito = normal_texto(materia.get("unidad_credito"))
            seccion = normal_texto(materia.get("seccion"))
            compartidos = normal_texto(materia.get("compartidos"))
            ambiente = normal_texto(materia.get("ambiente")).upper()
            materia_id = get_or_create_materia(
                cursor,
                nombre_materia,
                carrera_id,
                codigo=codigo,
                semestre=ciclo,
            )
            cursor.execute(
                """
                UPDATE materias
                SET codigo = COALESCE(NULLIF(?, ''), codigo),
                    semestre = COALESCE(NULLIF(?, ''), semestre),
                    mencion = COALESCE(NULLIF(?, ''), mencion),
                    unidad_credito = ?
                WHERE id = ?
                """,
                (codigo, ciclo, mencion, int(unidad_credito) if unidad_credito else 0, materia_id),
            )

            carga_id = materia.get("carga_id")
            if carga_id:
                cursor.execute(
                    """
                    UPDATE carga_academica
                    SET materia_id = ?, seccion = ?, salon_preferido = ?, compartidos = ?
                    WHERE id = ? AND profesor_id = ?
                    """,
                    (materia_id, seccion, ambiente, compartidos, carga_id, docente_id),
                )
                if cursor.rowcount == 0:
                    raise ValueError("No se encontró una carga académica para actualizar.")
            else:
                cursor.execute(
                    """
                    INSERT INTO carga_academica
                    (profesor_id, materia_id, seccion, bloques_semanales, salon_preferido,
                     dia_fijo, hora_inicio_fija, hora_fin_fija, compartidos)
                    VALUES (?, ?, ?, 1, ?, '', '', '', ?)
                    """,
                    (docente_id, materia_id, seccion or f"SIN-SECCION-{indice}", ambiente, compartidos),
                )
                row_carga = cursor.execute(
                    """
                    SELECT id FROM carga_academica
                    WHERE profesor_id = ? AND materia_id = ? AND seccion = ?
                    """,
                    (docente_id, materia_id, seccion or f"SIN-SECCION-{indice}"),
                ).fetchone()
                carga_id = row_carga["id"]
            ids_deseados.append(carga_id)

        ids_stale = [fila["id"] for fila in cargas_actuales if fila["id"] not in ids_deseados]
        if ids_stale:
            placeholders = ", ".join("?" for _ in ids_stale)
            cursor.execute(
                f"DELETE FROM asignaciones_horario WHERE carga_id IN ({placeholders})",
                ids_stale,
            )
            cursor.execute(
                f"DELETE FROM carga_academica WHERE id IN ({placeholders}) AND profesor_id = ?",
                ids_stale + [docente_id],
            )

        conn.commit()
        return True, ""
    except Exception as ex:
        conn.rollback()
        raise
    finally:
        conn.close()


def _actualizar_materias_profesor(cursor, profesor_id, nombres_materias):
    solicitadas = []
    normalizadas = set()
    for nombre in nombres_materias:
        nombre = str(nombre or "").strip()
        clave = _normalizar_materia(nombre)
        if nombre and clave and clave not in normalizadas:
            normalizadas.add(clave)
            solicitadas.append((nombre, clave))

    cursor.execute(
        """
        SELECT ca.id AS carga_id, ca.materia_id, m.nombre, m.carrera_id, m.semestre
        FROM carga_academica ca
        JOIN materias m ON m.id = ca.materia_id
        WHERE ca.profesor_id = ?
        """,
        (profesor_id,),
    )
    cargas_actuales = [dict(row) for row in cursor.fetchall()]
    por_nombre_actual = {}
    for carga in cargas_actuales:
        por_nombre_actual.setdefault(_normalizar_materia(carga["nombre"]), []).append(carga)

    carreras_actuales = list(dict.fromkeys(carga["carrera_id"] for carga in cargas_actuales))
    ids_materias_deseadas = set()

    for nombre, clave in solicitadas:
        cargas_misma_materia = por_nombre_actual.get(clave, [])
        if cargas_misma_materia:
            ids_materias_deseadas.update(carga["materia_id"] for carga in cargas_misma_materia)
            continue

        cursor.execute("SELECT id, carrera_id, nombre FROM materias")
        coincidencias = [
            dict(row) for row in cursor.fetchall()
            if _normalizar_materia(row["nombre"]) == clave
        ]
        en_carreras_actuales = [
            materia for materia in coincidencias
            if materia["carrera_id"] in carreras_actuales
        ]
        candidatas = en_carreras_actuales or coincidencias
        if len(candidatas) > 1:
            return f"La materia '{nombre}' existe en varias carreras; use el nombre exacto de una materia ya asignada."
        if candidatas:
            ids_materias_deseadas.add(candidatas[0]["id"])
        elif carreras_actuales:
            materia_id = get_or_create_materia(
                cursor,
                nombre,
                carreras_actuales[0],
                semestre=cargas_actuales[0].get("semestre") or "1er Semestre",
            )
            ids_materias_deseadas.add(materia_id)
        else:
            return (
                f"No se puede agregar '{nombre}' porque el docente no tiene una carrera "
                "asociada donde registrar la nueva materia."
            )

    cargas_a_eliminar = [
        carga["carga_id"] for carga in cargas_actuales
        if carga["materia_id"] not in ids_materias_deseadas
    ]
    if cargas_a_eliminar:
        placeholders = ",".join("?" for _ in cargas_a_eliminar)
        cursor.execute(
            f"DELETE FROM asignaciones_horario WHERE carga_id IN ({placeholders})",
            cargas_a_eliminar,
        )
        cursor.execute(
            f"DELETE FROM carga_academica WHERE id IN ({placeholders})",
            cargas_a_eliminar,
        )

    ids_actuales = {carga["materia_id"] for carga in cargas_actuales}
    for materia_id in ids_materias_deseadas - ids_actuales:
        cursor.execute(
            """
            INSERT INTO carga_academica
            (profesor_id, materia_id, seccion, bloques_semanales, salon_preferido,
             dia_fijo, hora_inicio_fija, hora_fin_fija)
            VALUES (?, ?, 'Sección A', 1, '', '', '', '')
            ON CONFLICT(profesor_id, materia_id, seccion) DO NOTHING
            """,
            (profesor_id, materia_id),
        )

    return None


def actualizar_profesor(
    nombre_actual,
    nuevo_nombre,
    cedula="",
    email="",
    condicion="Contratado/a",
    materias=None,
):
    """Actualiza los datos y, opcionalmente, la lista de materias del docente."""
    nombre_actual = str(nombre_actual).strip()
    nuevo_nombre = str(nuevo_nombre).strip()
    if not nombre_actual or not nuevo_nombre:
        return False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM profesores WHERE LOWER(nombre) = LOWER(?)",
        (nombre_actual,),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    cursor.execute(
        "SELECT id FROM profesores WHERE LOWER(nombre) = LOWER(?) AND id <> ?",
        (nuevo_nombre, row["id"]),
    )
    if cursor.fetchone():
        conn.close()
        return False

    cursor.execute(
        "UPDATE profesores SET nombre = ?, cedula = ?, email = ?, condicion = ? WHERE id = ?",
        (
            nuevo_nombre,
            str(cedula or "").strip(),
            str(email or "").strip(),
            str(condicion or "Contratado/a").strip(),
            row["id"],
        ),
    )
    actualizados = cursor.rowcount
    if materias is not None:
        error_materias = _actualizar_materias_profesor(cursor, row["id"], materias)
        if error_materias:
            conn.rollback()
            conn.close()
            return False
    conn.commit()
    conn.close()
    return actualizados > 0


def eliminar_profesor(nombre):
    """Elimina un docente y, en cascada, sus cargas, disponibilidades y asignaciones."""
    nombre = str(nombre).strip()
    if not nombre:
        return False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM profesores WHERE LOWER(nombre) = LOWER(?)", (nombre,))
    eliminados = cursor.rowcount
    conn.commit()
    conn.close()
    return eliminados > 0


def siguiente_numero_ambiente():
    """Siguiente número consecutivo global de los ambientes con código P(piso)-(nro)."""
    import re

    mayor = 0
    for salon in obtener_salones():
        coincidencia = re.match(r"^P\d+-(\d+)$", str(salon["codigo"]).strip().upper())
        if coincidencia:
            mayor = max(mayor, int(coincidencia.group(1)))
    return mayor + 1


def siguiente_codigo_ambiente(piso):
    """Sugiere el próximo código P(piso)-(nro) continuando el total global."""
    try:
        numero_piso = int(piso)
    except (TypeError, ValueError):
        numero_piso = 1
    return f"P{numero_piso}-{siguiente_numero_ambiente():02d}"


def crear_ambiente(codigo, capacidad=CAPACIDAD_DEFECTO, edificio="Ambiente Especial", es_camillas=False):
    """Crea o actualiza un ambiente conservando la nomenclatura indicada."""
    codigo = str(codigo).strip().upper()
    if not codigo:
        return None
    try:
        capacidad = int(capacidad)
    except (TypeError, ValueError):
        capacidad = CAPACIDAD_DEFECTO
    if capacidad <= 0:
        capacidad = CAPACIDAD_DEFECTO
    camillas = 1 if es_camillas else 0

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM salones WHERE UPPER(codigo) = UPPER(?)", (codigo,))
    row = cursor.fetchone()
    if row:
        cursor.execute(
            "UPDATE salones SET capacidad = ?, edificio = ?, es_camillas = ? WHERE id = ?",
            (capacidad, edificio, camillas, row["id"]),
        )
    else:
        cursor.execute(
            "INSERT INTO salones (codigo, capacidad, edificio, es_camillas) VALUES (?, ?, ?, ?)",
            (codigo, capacidad, edificio, camillas),
        )
    conn.commit()
    conn.close()
    return codigo


def actualizar_ambiente_por_docente_materia(profesor_nombre: str, materia_nombre: str, dia: str, nuevo_codigo_salon: str) -> bool:
    """Actualiza el ambiente (salón) de una clase asignada a un profesor específico de forma robusta e insensible a acentos."""
    import unicodedata, re

    def _norm(s):
        if not s:
            return ""
        s = unicodedata.normalize("NFD", str(s))
        s = "".join(c for c in s if unicodedata.category(c) != "Mn")
        return re.sub(r"[^\w\s]", "", s).strip().lower()

    conn = get_connection()
    cursor = conn.cursor()
    salon_id = get_or_create_salon(cursor, nuevo_codigo_salon.strip().upper())

    cursor.execute("""
        SELECT a.id, a.dia, p.nombre AS prof_nom, m.nombre AS mat_nom, a.carga_id
        FROM asignaciones_horario a
        JOIN profesores p ON a.profesor_id = p.id
        JOIN materias m ON a.materia_id = m.id
    """)
    todas = [dict(r) for r in cursor.fetchall()]
    target_prof = _norm(profesor_nombre)
    target_mat = _norm(materia_nombre)
    target_dia = _norm(dia)

    ids_a_actualizar = []
    cargas_a_actualizar = []
    for fila in todas:
        f_prof = _norm(fila["prof_nom"])
        f_mat = _norm(fila["mat_nom"])
        f_dia = _norm(fila["dia"])

        prof_ok = (target_prof in f_prof or f_prof in target_prof) if target_prof else True
        mat_ok = (target_mat in f_mat or f_mat in target_mat) if target_mat else True
        dia_ok = (target_dia == f_dia) if target_dia else True

        if prof_ok and mat_ok and dia_ok:
            ids_a_actualizar.append(fila["id"])
            if fila.get("carga_id"):
                cargas_a_actualizar.append(fila["carga_id"])

    # Si no hubo coincidencia exacta de día, buscar solo por profesor y materia
    if not ids_a_actualizar and target_prof and target_mat:
        for fila in todas:
            f_prof = _norm(fila["prof_nom"])
            f_mat = _norm(fila["mat_nom"])
            if (target_prof in f_prof or f_prof in target_prof) and (target_mat in f_mat or f_mat in target_mat):
                ids_a_actualizar.append(fila["id"])
                if fila.get("carga_id"):
                    cargas_a_actualizar.append(fila["carga_id"])

    if ids_a_actualizar:
        placeholders = ",".join(["?"] * len(ids_a_actualizar))
        cursor.execute(f"""
            UPDATE asignaciones_horario
            SET salon_id = ?
            WHERE id IN ({placeholders})
        """, [salon_id] + ids_a_actualizar)

    if cargas_a_actualizar:
        placeholders = ",".join(["?"] * len(cargas_a_actualizar))
        cursor.execute(f"""
            UPDATE carga_academica
            SET salon_preferido = ?
            WHERE id IN ({placeholders})
        """, [nuevo_codigo_salon.strip().upper()] + cargas_a_actualizar)

    conn.commit()
    conn.close()
    return len(ids_a_actualizar) > 0


def actualizar_ambiente_profesor(profesor_nombre: str, nuevo_codigo_salon: str) -> int:
    """Actualiza el ambiente de TODAS las clases asignadas a un profesor específico."""
    import unicodedata, re

    def _norm(s):
        if not s:
            return ""
        s = unicodedata.normalize("NFD", str(s))
        s = "".join(c for c in s if unicodedata.category(c) != "Mn")
        return re.sub(r"[^\w\s]", "", s).strip().lower()

    conn = get_connection()
    cursor = conn.cursor()
    salon_id = get_or_create_salon(cursor, nuevo_codigo_salon.strip().upper())

    cursor.execute("""
        SELECT a.id, p.nombre AS prof_nom, a.carga_id
        FROM asignaciones_horario a
        JOIN profesores p ON a.profesor_id = p.id
    """)
    todas = [dict(r) for r in cursor.fetchall()]
    target_prof = _norm(profesor_nombre)

    ids = [fila["id"] for fila in todas if (target_prof in _norm(fila["prof_nom"]) or _norm(fila["prof_nom"]) in target_prof)]
    cargas = [fila["carga_id"] for fila in todas if (target_prof in _norm(fila["prof_nom"]) or _norm(fila["prof_nom"]) in target_prof) and fila.get("carga_id")]

    if ids:
        placeholders = ",".join(["?"] * len(ids))
        cursor.execute(f"UPDATE asignaciones_horario SET salon_id = ? WHERE id IN ({placeholders})", [salon_id] + ids)
    if cargas:
        placeholders = ",".join(["?"] * len(cargas))
        cursor.execute(f"UPDATE carga_academica SET salon_preferido = ? WHERE id IN ({placeholders})", [nuevo_codigo_salon.strip().upper()] + cargas)

    conn.commit()
    conn.close()
    return len(ids)


def obtener_info_profesores_dict() -> dict:
    """Retorna un diccionario {nombre_profesor: {'cedula': ..., 'condicion': ..., 'email': ...}}."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, cedula, email, COALESCE(condicion, 'Contratado/a') AS condicion FROM profesores")
    res = {}
    for r in cursor.fetchall():
        res[r["nombre"].strip().upper()] = dict(r)
    conn.close()
    return res


def marcar_iniciar_en_blanco(activar: bool = True):
    """Marca o desmarca si el sistema debe iniciar en blanco (sin datos precargados)."""
    flag = os.path.join(BASE_DIR, ".iniciar_en_blanco")
    if activar:
        with open(flag, "w", encoding="utf-8") as f:
            f.write("1")
    else:
        if os.path.exists(flag):
            try:
                os.remove(flag)
            except Exception:
                pass


def esta_en_modo_blanco() -> bool:
    """Verifica si el sistema tiene activa la bandera de iniciar en blanco."""
    flag = os.path.join(BASE_DIR, ".iniciar_en_blanco")
    return os.path.exists(flag)
