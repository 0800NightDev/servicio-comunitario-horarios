import os
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    Response,
)
from werkzeug.utils import secure_filename

from database import (
    init_db,
    get_connection,
    clear_all_data,
    get_or_create_facultad,
    get_or_create_carrera,
    get_or_create_profesor,
    get_or_create_materia,
    get_or_create_salon,
    DIAS_ORDEN,
    BLOQUES_HORARIOS,
)
from parsers import importar_excel, importar_docx, importar_txt, parsear_disponibilidad
from scheduler import generar_horarios_automaticos, validar_cambio_manual
from seed_demo import crear_archivos_ejemplo, cargar_demo_en_bd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = "servicio_comunitario_universidad_secret_key"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Inicializar base de datos y plantillas al arrancar
init_db()
crear_archivos_ejemplo(BASE_DIR)


@app.context_processor
def inject_global_profesores():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM profesores ORDER BY nombre ASC")
    lista_profesores = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"profesores_global": lista_profesores}



def obtener_estadisticas():
    conn = get_connection()
    cursor = conn.cursor()
    stats = {}
    for tabla, clave in [
        ("facultades", "facultades"),
        ("carreras", "carreras"),
        ("profesores", "profesores"),
        ("materias", "materias"),
        ("salones", "salones"),
        ("asignaciones_horario", "clases_programadas"),
    ]:
        cursor.execute(f"SELECT COUNT(*) AS total FROM {tabla}")
        stats[clave] = cursor.fetchone()["total"]
    conn.close()
    return stats


def consultar_oferta_academica(facultad_id=None, carrera_id=None, profesor_id=None, salon_id=None, dia=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            a.id AS asignacion_id,
            a.dia,
            a.hora_inicio,
            a.hora_fin,
            a.estado,
            p.id AS profesor_id,
            p.nombre AS profesor_nombre,
            p.cedula AS profesor_cedula,
            m.id AS materia_id,
            m.nombre AS materia_nombre,
            m.semestre,
            ca.seccion,
            c.id AS carrera_id,
            c.nombre AS carrera_nombre,
            f.id AS facultad_id,
            f.nombre AS facultad_nombre,
            s.id AS salon_id,
            s.codigo AS salon_codigo,
            s.edificio AS salon_edificio,
            s.capacidad AS salon_capacidad
        FROM asignaciones_horario a
        JOIN carga_academica ca ON ca.id = a.carga_id
        JOIN profesores p ON p.id = a.profesor_id
        JOIN materias m ON m.id = a.materia_id
        JOIN carreras c ON c.id = m.carrera_id
        JOIN facultades f ON f.id = c.facultad_id
        JOIN salones s ON s.id = a.salon_id
        WHERE 1=1
    """
    params = []
    if facultad_id:
        query += " AND f.id = ?"
        params.append(facultad_id)
    if carrera_id:
        query += " AND c.id = ?"
        params.append(carrera_id)
    if profesor_id:
        query += " AND p.id = ?"
        params.append(profesor_id)
    if salon_id:
        query += " AND s.id = ?"
        params.append(salon_id)
    if dia:
        query += " AND a.dia = ?"
        params.append(dia)

    cursor.execute(query, params)
    filas = [dict(r) for r in cursor.fetchall()]
    conn.close()

    orden_dia = {d: i for i, d in enumerate(DIAS_ORDEN)}
    # Ordenado por Facultad -> Profesor (alfabéticamente) -> Día -> Hora
    filas.sort(
        key=lambda x: (
            x["facultad_nombre"],
            x["profesor_nombre"],
            orden_dia.get(x["dia"], 99),
            x["hora_inicio"],
        )
    )
    return filas


def construir_matriz_calendario(asignaciones):
    """
    Construye una matriz [hora_rango][dia] -> lista de clases asignadas,
    ideal para mostrar el horario tipo calendario de un profesor o de un salón.
    """
    rangos_unicos = sorted({f"{a['hora_inicio']} - {a['hora_fin']}" for a in asignaciones})
    if rangos_unicos:
        rangos_horas = rangos_unicos
    else:
        rangos_horas = [f"{b[0]} - {b[1]}" for b in BLOQUES_HORARIOS]

    matriz = {r: {d: [] for d in DIAS_ORDEN} for r in rangos_horas}
    for a in asignaciones:
        r = f"{a['hora_inicio']} - {a['hora_fin']}"
        d = a["dia"]
        if r in matriz and d in matriz[r]:
            matriz[r][d].append(a)

    return rangos_horas, matriz


@app.route("/")
def index():
    stats = obtener_estadisticas()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nombre FROM facultades ORDER BY nombre ASC")
    facultades = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT id, nombre, facultad_id FROM carreras ORDER BY nombre ASC")
    carreras = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT id, nombre FROM profesores ORDER BY nombre ASC")
    profesores = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT id, codigo, edificio, capacidad FROM salones ORDER BY codigo ASC")
    salones = [dict(r) for r in cursor.fetchall()]

    conn.close()

    oferta_reciente = consultar_oferta_academica()[:12]
    return render_template(
        "index.html",
        stats=stats,
        facultades=facultades,
        carreras=carreras,
        profesores=profesores,
        salones=salones,
        oferta_reciente=oferta_reciente,
        dias_orden=DIAS_ORDEN,
        bloques_horarios=BLOQUES_HORARIOS,
    )


@app.route("/cargar-archivo", methods=["POST"])
def cargar_archivo():
    archivo = request.files.get("archivo")
    limpiar_previo = request.form.get("limpiar_previo") == "si"

    if not archivo or archivo.filename == "":
        flash("Por favor selecciona un archivo válido (.xlsx, .docx o .txt).", "warning")
        return redirect(url_for("index"))

    ext = os.path.splitext(archivo.filename)[1].lower()
    if ext not in (".xlsx", ".docx", ".txt", ".csv"):
        flash("Formato no soportado. Usa archivos Excel (.xlsx), Word (.docx) o Texto (.txt).", "danger")
        return redirect(url_for("index"))

    if limpiar_previo:
        clear_all_data(keep_salones=True)

    filename = secure_filename(archivo.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    archivo.save(filepath)

    try:
        if ext == ".xlsx":
            res = importar_excel(filepath)
        elif ext == ".docx":
            res = importar_docx(filepath)
        else:
            res = importar_txt(filepath)

        res_sched = generar_horarios_automaticos()

        msg = (
            f"Archivo '{filename}' procesado con éxito: {res['insertados']} cargas académicas leídas y "
            f"{res_sched['asignados']} bloques de horario organizados sin choques."
        )
        flash(msg, "success")

        for err in res.get("errores", [])[:5]:
            flash(err, "warning")
        for m in res_sched.get("mensajes", [])[:5]:
            flash(m, "warning")

    except Exception as e:
        flash(f"Error al procesar el archivo: {str(e)}", "danger")

    return redirect(url_for("oferta_general"))


@app.route("/cargar-demo", methods=["POST"])
def cargar_demo():
    clear_all_data(keep_salones=True)
    info = cargar_demo_en_bd(BASE_DIR)
    flash(
        f"Datos de demostración cargados correctamente: {info['importados']} materias registradas y "
        f"{info['asignados']} bloques de clases asignados automáticamente.",
        "success",
    )
    return redirect(url_for("oferta_general"))


@app.route("/limpiar-datos", methods=["POST"])
def limpiar_datos():
    clear_all_data(keep_salones=True)
    flash("Se han limpiado todos los registros académicos y horarios.", "info")
    return redirect(url_for("index"))


@app.route("/agregar-manual", methods=["POST"])
def agregar_manual():
    facultad_nom = request.form.get("facultad", "").strip()
    carrera_nom = request.form.get("carrera", "").strip()
    profesor_nom = request.form.get("profesor", "").strip()
    materia_nom = request.form.get("materia", "").strip()
    disponibilidad_str = request.form.get("disponibilidad", "").strip()
    salon_pref = request.form.get("salon_preferido", "").strip()
    seccion = request.form.get("seccion", "Sección A").strip() or "Sección A"
    semestre = request.form.get("semestre", "1er Semestre").strip() or "1er Semestre"
    bloques = int(request.form.get("bloques", 1) or 1)

    if not profesor_nom or not materia_nom or not carrera_nom or not facultad_nom:
        flash("Por favor completa Facultad, Carrera, Profesor y Materia.", "warning")
        return redirect(url_for("index"))

    conn = get_connection()
    cursor = conn.cursor()

    fac_id = get_or_create_facultad(cursor, facultad_nom)
    car_id = get_or_create_carrera(cursor, carrera_nom, fac_id)
    prof_id = get_or_create_profesor(cursor, profesor_nom)
    mat_id = get_or_create_materia(cursor, materia_nom, car_id, semestre=semestre)

    if salon_pref:
        get_or_create_salon(cursor, salon_pref)

    bloques_disp = parsear_disponibilidad(disponibilidad_str)
    if not bloques_disp:
        bloques_disp = [("Lunes", "07:00", "09:00"), ("Miércoles", "07:00", "09:00")]

    for d, hi, hf in bloques_disp:
        cursor.execute(
            "INSERT OR IGNORE INTO disponibilidades (profesor_id, dia, hora_inicio, hora_fin) VALUES (?, ?, ?, ?)",
            (prof_id, d, hi, hf),
        )

    cursor.execute(
        """
        INSERT INTO carga_academica (profesor_id, materia_id, seccion, bloques_semanales, salon_preferido)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(profesor_id, materia_id, seccion) DO UPDATE SET
            bloques_semanales = excluded.bloques_semanales,
            salon_preferido = excluded.salon_preferido
        """,
        (prof_id, mat_id, seccion, bloques, salon_pref),
    )

    conn.commit()
    conn.close()

    generar_horarios_automaticos()
    flash(f"Se agregó la materia '{materia_nom}' con el Prof. {profesor_nom} y se actualizaron los horarios.", "success")
    return redirect(url_for("oferta_general"))


@app.route("/agregar-salon", methods=["POST"])
def agregar_salon():
    codigo = request.form.get("codigo", "").strip()
    edificio = request.form.get("edificio", "Edificio Principal").strip()
    capacidad = int(request.form.get("capacidad", 40) or 40)
    if codigo:
        conn = get_connection()
        cursor = conn.cursor()
        get_or_create_salon(cursor, codigo, capacidad, edificio)
        conn.commit()
        conn.close()
        generar_horarios_automaticos()
        flash(f"Salón '{codigo}' registrado correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/reorganizar", methods=["POST"])
def reorganizar():
    res = generar_horarios_automaticos()
    flash(
        f"Horarios reorganizados: {res['asignados']} bloques asignados, {res['pendientes']} pendientes.",
        "success" if res["pendientes"] == 0 else "warning",
    )
    for m in res.get("mensajes", []):
        flash(m, "warning")
    return redirect(request.referrer or url_for("oferta_general"))


@app.route("/editar-asignacion", methods=["POST"])
def editar_asignacion():
    asignacion_id = int(request.form.get("asignacion_id"))
    salon_id = int(request.form.get("salon_id"))
    dia = request.form.get("dia")
    rango_hora = request.form.get("rango_hora", "07:00-09:00")
    partes = rango_hora.split("-")
    hora_inicio = partes[0].strip()
    hora_fin = partes[1].strip()

    valido, mensaje = validar_cambio_manual(asignacion_id, salon_id, dia, hora_inicio, hora_fin)
    if not valido:
        flash(f"No se pudo cambiar el horario: {mensaje}", "danger")
        return redirect(request.referrer or url_for("oferta_general"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE asignaciones_horario
        SET salon_id = ?, dia = ?, hora_inicio = ?, hora_fin = ?
        WHERE id = ?
        """,
        (salon_id, dia, hora_inicio, hora_fin, asignacion_id),
    )
    conn.commit()
    conn.close()
    flash("Horario actualizado manualmente sin choques.", "success")
    return redirect(request.referrer or url_for("oferta_general"))


@app.route("/oferta-general")
def oferta_general():
    facultad_id = request.args.get("facultad_id", type=int)
    carrera_id = request.args.get("carrera_id", type=int)
    profesor_id = request.args.get("profesor_id", type=int)
    salon_id = request.args.get("salon_id", type=int)
    dia = request.args.get("dia", default="")

    asignaciones = consultar_oferta_academica(
        facultad_id=facultad_id,
        carrera_id=carrera_id,
        profesor_id=profesor_id,
        salon_id=salon_id,
        dia=dia if dia else None,
    )

    # Agrupar por Facultad para visualización organizada
    por_facultad = {}
    for a in asignaciones:
        por_facultad.setdefault(a["facultad_nombre"], []).append(a)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM facultades ORDER BY nombre ASC")
    facultades = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT id, nombre, facultad_id FROM carreras ORDER BY nombre ASC")
    carreras = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT id, nombre FROM profesores ORDER BY nombre ASC")
    profesores = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT id, codigo, edificio FROM salones ORDER BY codigo ASC")
    salones = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return render_template(
        "oferta_general.html",
        asignaciones=asignaciones,
        por_facultad=por_facultad,
        facultades=facultades,
        carreras=carreras,
        profesores=profesores,
        salones=salones,
        filtros={
            "facultad_id": facultad_id,
            "carrera_id": carrera_id,
            "profesor_id": profesor_id,
            "salon_id": salon_id,
            "dia": dia,
        },
        dias_orden=DIAS_ORDEN,
        bloques_horarios=BLOQUES_HORARIOS,
    )


@app.route("/calendario-profesores")
def calendario_profesores():
    profesor_id = request.args.get("profesor_id", type=int)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, cedula, email FROM profesores ORDER BY nombre ASC")
    profesores = [dict(r) for r in cursor.fetchall()]

    if not profesor_id and profesores:
        profesor_id = profesores[0]["id"]

    profesor_actual = None
    disponibilidades = []
    if profesor_id:
        cursor.execute("SELECT id, nombre, cedula, email FROM profesores WHERE id = ?", (profesor_id,))
        row = cursor.fetchone()
        if row:
            profesor_actual = dict(row)
        cursor.execute(
            "SELECT dia, hora_inicio, hora_fin FROM disponibilidades WHERE profesor_id = ? ORDER BY hora_inicio",
            (profesor_id,),
        )
        disponibilidades = [dict(r) for r in cursor.fetchall()]

    conn.close()

    asignaciones = consultar_oferta_academica(profesor_id=profesor_id) if profesor_id else []
    rangos_horas, matriz = construir_matriz_calendario(asignaciones)

    # También construir todos los calendarios si el usuario quiere ver "Todos los profesores"
    mostrar_todos = request.args.get("todos") == "1"
    calendarios_todos = []
    if mostrar_todos:
        for p in profesores:
            asig_p = consultar_oferta_academica(profesor_id=p["id"])
            rh, mat = construir_matriz_calendario(asig_p)
            calendarios_todos.append({
                "profesor": p,
                "asignaciones": asig_p,
                "rangos_horas": rh,
                "matriz": mat,
            })

    return render_template(
        "calendario_profesores.html",
        profesores=profesores,
        profesor_actual=profesor_actual,
        disponibilidades=disponibilidades,
        asignaciones=asignaciones,
        rangos_horas=rangos_horas,
        matriz=matriz,
        dias_orden=DIAS_ORDEN,
        mostrar_todos=mostrar_todos,
        calendarios_todos=calendarios_todos,
    )


@app.route("/ocupacion-salones")
def ocupacion_salones():
    salon_id = request.args.get("salon_id", type=int)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, codigo, edificio, capacidad FROM salones ORDER BY codigo ASC")
    salones = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if not salon_id and salones:
        salon_id = salones[0]["id"]

    salon_actual = next((s for s in salones if s["id"] == salon_id), None)
    asignaciones = consultar_oferta_academica(salon_id=salon_id) if salon_id else []
    rangos_horas, matriz = construir_matriz_calendario(asignaciones)

    return render_template(
        "ocupacion_salones.html",
        salones=salones,
        salon_actual=salon_actual,
        asignaciones=asignaciones,
        rangos_horas=rangos_horas,
        matriz=matriz,
        dias_orden=DIAS_ORDEN,
    )


@app.route("/reporte-imprimible")
def reporte_imprimible():
    """
    Genera el reporte HTML autocontenido listo para imprimir / guardar como PDF,
    o lo descarga directamente como archivo .html si se pasa ?descargar=1.
    Soporta:
    - tipo=general (Oferta Académica General por Facultad)
    - tipo=profesor (Horario Tipo Calendario de un Profesor o de Todos)
    - tipo=completo (Oferta General + Calendarios de todos los Profesores)
    """
    tipo = request.args.get("tipo", "completo")
    facultad_id = request.args.get("facultad_id", type=int)
    profesor_id = request.args.get("profesor_id", type=int)
    descargar = request.args.get("descargar") == "1"
    auto_print = request.args.get("print") == "1"

    asignaciones = consultar_oferta_academica(facultad_id=facultad_id, profesor_id=profesor_id)
    por_facultad = {}
    for a in asignaciones:
        por_facultad.setdefault(a["facultad_nombre"], []).append(a)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, cedula, email FROM profesores ORDER BY nombre ASC")
    todos_profesores = [dict(r) for r in cursor.fetchall()]

    if profesor_id:
        profesores = [p for p in todos_profesores if p["id"] == profesor_id]
    else:
        profesores = todos_profesores
    conn.close()

    calendarios_profesores = []
    if tipo in ("profesor", "completo"):
        for p in profesores:
            asig_p = consultar_oferta_academica(facultad_id=facultad_id, profesor_id=p["id"])
            rh, mat = construir_matriz_calendario(asig_p)
            calendarios_profesores.append({
                "profesor": p,
                "asignaciones": asig_p,
                "rangos_horas": rh,
                "matriz": mat,
            })

    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")

    html_content = render_template(
        "reporte_imprimible.html",
        tipo=tipo,
        por_facultad=por_facultad,
        calendarios_profesores=calendarios_profesores,
        todos_profesores=todos_profesores,
        profesor_id_seleccionado=profesor_id,
        dias_orden=DIAS_ORDEN,
        fecha_actual=fecha_actual,
        auto_print=auto_print,
        es_descarga=descargar,
    )

    if descargar:
        nombre_archivo = f"Reporte_Horarios_Universidad_{tipo}.html"
        return Response(
            html_content,
            mimetype="text/html",
            headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"},
        )

    return html_content


@app.route("/descargar-plantilla/<formato>")
def descargar_plantilla(formato):
    rutas = crear_archivos_ejemplo(BASE_DIR)
    if formato not in rutas:
        flash("Formato de plantilla inválido.", "danger")
        return redirect(url_for("index"))
    return send_file(rutas[formato], as_attachment=True)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
