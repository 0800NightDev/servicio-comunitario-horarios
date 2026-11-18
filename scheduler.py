from database import get_connection, DIAS_ORDEN, BLOQUES_HORARIOS


def hay_solapamiento(h_ini1, h_fin1, h_ini2, h_fin2):
    """Verifica si dos rangos de hora HH:MM se solapan."""
    return max(h_ini1, h_ini2) < min(h_fin1, h_fin2)


def es_ambiente_compartible(codigo_salon):
    """
    Ambientes virtuales o coordinaciones permiten múltiples cursos simultáneos sin choque físico.
    """
    c = (codigo_salon or "").upper()
    return any(k in c for k in ["VIRTUAL", "COORDINAC", "ONLINE", "CANCHA", "AUDITORIO"])


def generar_horarios_automaticos():
    """
    Algoritmo inteligente de planificación universitaria:
    - Si la carga académica ya trae día y hora específicos desde el Excel oficial (dia_fijo, hora_inicio_fija),
      prioriza asignarla exactamente en ese día, hora y ambiente indicado (permitiendo cursos compartidos entre
      carreras/menciones del mismo profesor o ambientes virtuales).
    - Si es una carga basada en disponibilidad general, asigna los bloques semanales evitando choques de
      profesor y salón.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Limpiar asignaciones automáticas previas
    cursor.execute("DELETE FROM asignaciones_horario;")

    # Obtener todos los salones disponibles
    cursor.execute("SELECT id, codigo, capacidad, edificio FROM salones ORDER BY id ASC")
    salones = [dict(r) for r in cursor.fetchall()]
    if not salones:
        conn.close()
        return {"asignados": 0, "pendientes": 0, "mensajes": ["No hay salones registrados en el sistema."]}

    mapa_salones_codigo = {s["codigo"].lower(): s["id"] for s in salones}
    mapa_salones_id_codigo = {s["id"]: s["codigo"] for s in salones}

    # Obtener disponibilidades por profesor
    cursor.execute("SELECT profesor_id, dia, hora_inicio, hora_fin FROM disponibilidades")
    disp_por_profesor = {}
    for r in cursor.fetchall():
        pid = r["profesor_id"]
        disp_por_profesor.setdefault(pid, []).append(
            (r["dia"], r["hora_inicio"], r["hora_fin"])
        )

    orden_dia_idx = {d: i for i, d in enumerate(DIAS_ORDEN)}
    for pid in disp_por_profesor:
        disp_por_profesor[pid].sort(
            key=lambda x: (orden_dia_idx.get(x[0], 99), x[1])
        )

    # Obtener todas las cargas académicas con datos de profesor, materia, carrera y facultad
    cursor.execute("""
        SELECT
            ca.id AS carga_id,
            ca.profesor_id,
            p.nombre AS profesor_nombre,
            ca.materia_id,
            m.nombre AS materia_nombre,
            c.nombre AS carrera_nombre,
            f.nombre AS facultad_nombre,
            ca.seccion,
            ca.bloques_semanales,
            ca.salon_preferido,
            ca.dia_fijo,
            ca.hora_inicio_fija,
            ca.hora_fin_fija
        FROM carga_academica ca
        JOIN profesores p ON p.id = ca.profesor_id
        JOIN materias m ON m.id = ca.materia_id
        JOIN carreras c ON c.id = m.carrera_id
        JOIN facultades f ON f.id = c.facultad_id
        ORDER BY p.nombre ASC, f.nombre ASC, c.nombre ASC, m.nombre ASC
    """)
    cargas = [dict(r) for r in cursor.fetchall()]

    # Priorizar las cargas que tienen horario fijo del archivo oficial, y luego por MRV
    cargas.sort(
        key=lambda c: (
            0 if c["dia_fijo"] else 1,
            len(disp_por_profesor.get(c["profesor_id"], [])),
            c["profesor_nombre"],
        )
    )

    # ocupado_profesor[profesor_id] = lista de (dia, h_ini, h_fin, salon_id)
    ocupado_profesor = {}
    # ocupado_salon[salon_id] = lista de (dia, h_ini, h_fin, profesor_id)
    ocupado_salon = {}

    asignados = 0
    pendientes = 0
    mensajes = []

    for carga in cargas:
        cid = carga["carga_id"]
        pid = carga["profesor_id"]
        mid = carga["materia_id"]
        bloques_req = carga["bloques_semanales"] or 1
        salon_pref_str = (carga["salon_preferido"] or "").strip().lower()
        salon_pref_id = mapa_salones_codigo.get(salon_pref_str)

        # Caso 1: La fila del archivo ya traía su Día y Hora exactos (ej. Excel de oferta de universidad)
        if carga["dia_fijo"] and carga["hora_inicio_fija"] and carga["hora_fin_fija"]:
            dia_f = carga["dia_fijo"]
            hi_f = carga["hora_inicio_fija"]
            hf_f = carga["hora_fin_fija"]
            prof_choque = any(
                d == dia_f and hay_solapamiento(hi_f, hf_f, oi, of)
                for d, oi, of, _ in ocupado_profesor.get(pid, [])
            )
            salon_elegido = None
            if not prof_choque:
                salones_candidatos = list(salones)
                if salon_pref_id:
                    salones_candidatos.sort(key=lambda s: 0 if s["id"] == salon_pref_id else 1)

                for salon in salones_candidatos:
                    sid = salon["id"]
                    salon_choque = any(
                        d == dia_f and hay_solapamiento(hi_f, hf_f, oi, of)
                        for d, oi, of, _ in ocupado_salon.get(sid, [])
                    )
                    if es_ambiente_compartible(salon["codigo"]) or not salon_choque:
                        salon_elegido = sid
                        break

            if salon_elegido is not None:
                cursor.execute(
                    """
                    INSERT INTO asignaciones_horario
                    (carga_id, profesor_id, materia_id, salon_id, dia, hora_inicio, hora_fin, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'Confirmado')
                    """,
                    (cid, pid, mid, salon_elegido, dia_f, hi_f, hf_f)
                )
                ocupado_profesor.setdefault(pid, []).append((dia_f, hi_f, hf_f, salon_elegido))
                ocupado_salon.setdefault(salon_elegido, []).append((dia_f, hi_f, hf_f, pid))
                asignados += 1
            else:
                pendientes += 1
                causa = "docente" if prof_choque else "ambiente"
                mensajes.append(
                    f"Conflicto de {causa}: '{carga['materia_nombre']}' "
                    f"({carga['carrera_nombre']}) con el Prof. {carga['profesor_nombre']} "
                    f"no pudo asignarse en {dia_f} de {hi_f} a {hf_f}."
                )
            continue

        # Caso 2: Asignación automática buscando entre la disponibilidad del profesor
        disponibles_prof = disp_por_profesor.get(pid, [])
        if not disponibles_prof:
            pendientes += bloques_req
            mensajes.append(
                f"Sin disponibilidad registrada: '{carga['materia_nombre']}' "
                f"({carga['carrera_nombre']}) con el Prof. {carga['profesor_nombre']} "
                f"no tiene bloques horarios para asignar."
            )
            continue

        bloques_logrados = 0
        dias_usados_en_materia = set()

        salones_candidatos = list(salones)
        if salon_pref_id:
            salones_candidatos.sort(key=lambda s: 0 if s["id"] == salon_pref_id else 1)

        for pasada in (1, 2):
            if bloques_logrados >= bloques_req:
                break

            for dia, h_ini, h_fin in disponibles_prof:
                if bloques_logrados >= bloques_req:
                    break

                if pasada == 1 and dia in dias_usados_en_materia:
                    continue

                prof_choque = any(
                    d == dia and hay_solapamiento(h_ini, h_fin, oi, of)
                    for d, oi, of, _ in ocupado_profesor.get(pid, [])
                )
                if prof_choque:
                    continue

                salon_elegido = None
                for s in salones_candidatos:
                    sid = s["id"]
                    if es_ambiente_compartible(s["codigo"]):
                        salon_elegido = sid
                        break
                    salon_choque = any(
                        d == dia and hay_solapamiento(h_ini, h_fin, oi, of)
                        for d, oi, of, _ in ocupado_salon.get(sid, [])
                    )
                    if not salon_choque:
                        salon_elegido = sid
                        break

                if salon_elegido is not None:
                    cursor.execute(
                        """
                        INSERT INTO asignaciones_horario
                        (carga_id, profesor_id, materia_id, salon_id, dia, hora_inicio, hora_fin, estado)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'Confirmado')
                        """,
                        (cid, pid, mid, salon_elegido, dia, h_ini, h_fin)
                    )
                    ocupado_profesor.setdefault(pid, []).append((dia, h_ini, h_fin, salon_elegido))
                    ocupado_salon.setdefault(salon_elegido, []).append((dia, h_ini, h_fin, pid))
                    dias_usados_en_materia.add(dia)
                    bloques_logrados += 1
                    asignados += 1

        if bloques_logrados < bloques_req:
            faltantes = bloques_req - bloques_logrados
            pendientes += faltantes
            mensajes.append(
                f"Conflicto de disponibilidad/salón: A '{carga['materia_nombre']}' "
                f"({carga['carrera_nombre']}) con el Prof. {carga['profesor_nombre']} "
                f"le faltaron {faltantes} bloque(s) por asignar."
            )

    conn.commit()
    conn.close()
    return {
        "asignados": asignados,
        "pendientes": pendientes,
        "mensajes": mensajes,
    }


def autoasignar_ambientes_libres():
    """Reubica clases con choque de ambiente sin cambiar día ni horario."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """SELECT a.id, a.profesor_id, a.salon_id, a.dia, a.hora_inicio, a.hora_fin,
                      s.codigo AS salon_codigo, ca.salon_preferido
               FROM asignaciones_horario a
               JOIN salones s ON s.id = a.salon_id
               LEFT JOIN carga_academica ca ON ca.id = a.carga_id
               ORDER BY a.dia, a.hora_inicio, a.hora_fin, a.id"""
        )
        asignaciones = [dict(row) for row in cursor.fetchall()]
        cursor.execute("SELECT id, codigo FROM salones ORDER BY id")
        salones = [dict(row) for row in cursor.fetchall()]
        if not asignaciones or not salones:
            return {
                "reasignados": 0,
                "conflictos_ambiente": 0,
                "conflictos_docente": 0,
                "mensajes": [],
            }

        mapa_salon_codigo = {salon["id"]: salon["codigo"] for salon in salones}
        for asignacion in asignaciones:
            asignacion["salon_id_final"] = asignacion["salon_id"]

        for _ in range(len(asignaciones) + 1):
            hubo_cambio = False
            por_salon = {}
            for asignacion in asignaciones:
                por_salon.setdefault(asignacion["salon_id_final"], []).append(asignacion)

            for asignacion in asignaciones:
                salon_id_actual = asignacion["salon_id_final"]
                codigo_actual = mapa_salon_codigo.get(salon_id_actual, asignacion["salon_codigo"])
                if es_ambiente_compartible(codigo_actual):
                    continue

                colisionada = any(
                    otra["id"] != asignacion["id"]
                    and otra["id"] < asignacion["id"]
                    and otra["dia"] == asignacion["dia"]
                    and hay_solapamiento(
                        asignacion["hora_inicio"],
                        asignacion["hora_fin"],
                        otra["hora_inicio"],
                        otra["hora_fin"],
                    )
                    for otra in por_salon.get(salon_id_actual, [])
                )
                if not colisionada:
                    continue

                preferido = (asignacion["salon_preferido"] or "").strip().casefold()
                candidatos = sorted(
                    (salon for salon in salones if salon["id"] != salon_id_actual),
                    key=lambda salon: (
                        0 if salon["codigo"].casefold() == preferido and preferido else 1,
                        1 if es_ambiente_compartible(salon["codigo"]) else 0,
                        salon["id"],
                    ),
                )

                nuevo_salon_id = None
                for candidato in candidatos:
                    if es_ambiente_compartible(candidato["codigo"]):
                        libre = True
                    else:
                        libre = not any(
                            otra["id"] != asignacion["id"]
                            and otra["dia"] == asignacion["dia"]
                            and hay_solapamiento(
                                asignacion["hora_inicio"],
                                asignacion["hora_fin"],
                                otra["hora_inicio"],
                                otra["hora_fin"],
                            )
                            for otra in por_salon.get(candidato["id"], [])
                        )
                    if libre:
                        nuevo_salon_id = candidato["id"]
                        break

                if nuevo_salon_id is not None:
                    if asignacion in por_salon.get(salon_id_actual, []):
                        por_salon[salon_id_actual].remove(asignacion)
                    asignacion["salon_id_final"] = nuevo_salon_id
                    por_salon.setdefault(nuevo_salon_id, []).append(asignacion)
                    hubo_cambio = True

            if not hubo_cambio:
                break

        disponibilidad_profesor = {}
        cursor.execute(
            "SELECT profesor_id, dia, hora_inicio, hora_fin FROM disponibilidades"
        )
        for fila in cursor.fetchall():
            disponibilidad_profesor.setdefault(fila["profesor_id"], []).append(
                (fila["dia"], fila["hora_inicio"], fila["hora_fin"])
            )

        horarios_candidatos = [
            (dia, inicio, fin)
            for dia in DIAS_ORDEN
            for inicio, fin in BLOQUES_HORARIOS
        ]

        por_salon_final = {}
        for item in asignaciones:
            por_salon_final.setdefault(item["salon_id_final"], []).append(item)

        ids_horario_modificado = set()
        ids_salon_modificado = set()

        for indice, asignacion in enumerate(asignaciones):
            for otra in asignaciones[indice + 1:]:
                if (
                    asignacion["profesor_id"] != otra["profesor_id"]
                    or asignacion["dia"] != otra["dia"]
                    or not hay_solapamiento(
                        asignacion["hora_inicio"],
                        asignacion["hora_fin"],
                        otra["hora_inicio"],
                        otra["hora_fin"],
                    )
                ):
                    continue

                # Intentar mover `otra`; si no encuentra horario/ambiente libre, intentar mover `asignacion`
                for target, fijada in [(otra, asignacion), (asignacion, otra)]:
                    duracion_actual = (
                        int(target["hora_fin"][:2]) * 60 + int(target["hora_fin"][3:])
                        - int(target["hora_inicio"][:2]) * 60
                        - int(target["hora_inicio"][3:])
                    )
                    disponibles = disponibilidad_profesor.get(target["profesor_id"], [])
                    candidatos_horario = list(disponibles)
                    for h in horarios_candidatos:
                        if h not in candidatos_horario:
                            candidatos_horario.append(h)

                    # Priorizar mismo día y bloques de disponibilidad registrada
                    candidatos_horario.sort(
                        key=lambda x: (
                            0 if x[0] == target["dia"] else 1,
                            0 if x in disponibles else 1,
                        )
                    )

                    nuevo_horario = None
                    for dia, inicio, fin in candidatos_horario:
                        ini_min = int(inicio[:2]) * 60 + int(inicio[3:])
                        fin_min = int(fin[:2]) * 60 + int(fin[3:])
                        fin_candidato = f"{(ini_min + duracion_actual) // 60:02d}:{(ini_min + duracion_actual) % 60:02d}"
                        if fin_min > ini_min and fin_min - ini_min < duracion_actual:
                            continue

                        choque_profesor = any(
                            item["id"] != target["id"]
                            and item["dia"] == dia
                            and hay_solapamiento(inicio, fin_candidato, item["hora_inicio"], item["hora_fin"])
                            for item in asignaciones
                            if item["profesor_id"] == target["profesor_id"]
                        )
                        if choque_profesor:
                            continue

                        # Buscar ambiente libre para este horario
                        salon_elegido_id = None
                        s_act = target["salon_id_final"]
                        cod_act = mapa_salon_codigo.get(s_act, "")
                        if es_ambiente_compartible(cod_act):
                            salon_elegido_id = s_act
                        else:
                            ocupado_act = any(
                                item["id"] != target["id"]
                                and item["dia"] == dia
                                and hay_solapamiento(inicio, fin_candidato, item["hora_inicio"], item["hora_fin"])
                                for item in por_salon_final.get(s_act, [])
                            )
                            if not ocupado_act:
                                salon_elegido_id = s_act

                        # Si el ambiente actual está ocupado en ese horario, probar otros salones registrados
                        if salon_elegido_id is None:
                            for s in salones:
                                sid = s["id"]
                                if sid == s_act:
                                    continue
                                if es_ambiente_compartible(s["codigo"]):
                                    salon_elegido_id = sid
                                    break
                                ocupado_s = any(
                                    item["id"] != target["id"]
                                    and item["dia"] == dia
                                    and hay_solapamiento(inicio, fin_candidato, item["hora_inicio"], item["hora_fin"])
                                    for item in por_salon_final.get(sid, [])
                                )
                                if not ocupado_s:
                                    salon_elegido_id = sid
                                    break

                        if salon_elegido_id is not None:
                            nuevo_horario = (dia, inicio, fin_candidato, salon_elegido_id)
                            break

                    if nuevo_horario:
                        dia_n, ini_n, fin_n, sal_n = nuevo_horario
                        if target in por_salon_final.get(target["salon_id_final"], []):
                            por_salon_final[target["salon_id_final"]].remove(target)
                        target["dia"] = dia_n
                        target["hora_inicio"] = ini_n
                        target["hora_fin"] = fin_n
                        if target["salon_id_final"] != sal_n:
                            target["salon_id_final"] = sal_n
                            ids_salon_modificado.add(target["id"])
                        por_salon_final.setdefault(sal_n, []).append(target)
                        ids_horario_modificado.add(target["id"])
                        break

        # Persistir reubicaciones de ambiente
        cambios_salones = [
            (asignacion["salon_id_final"], asignacion["id"])
            for asignacion in asignaciones
            if asignacion["salon_id_final"] != asignacion["salon_id"]
        ]
        if cambios_salones:
            cursor.executemany(
                "UPDATE asignaciones_horario SET salon_id = ? WHERE id = ?",
                cambios_salones,
            )

        # Persistir reubicaciones de horario
        if ids_horario_modificado:
            cursor.executemany(
                """UPDATE asignaciones_horario
                   SET dia = ?, hora_inicio = ?, hora_fin = ?
                   WHERE id = ?""",
                [
                    (item["dia"], item["hora_inicio"], item["hora_fin"], item["id"])
                    for item in asignaciones
                    if item["id"] in ids_horario_modificado
                ],
            )

        conflictos_ambiente = 0
        conflictos_docente = 0
        for indice, asignacion in enumerate(asignaciones):
            for otra in asignaciones[indice + 1:]:
                if asignacion["dia"] != otra["dia"] or not hay_solapamiento(
                    asignacion["hora_inicio"],
                    asignacion["hora_fin"],
                    otra["hora_inicio"],
                    otra["hora_fin"],
                ):
                    continue
                if asignacion["profesor_id"] == otra["profesor_id"]:
                    conflictos_docente += 1
                mismo_salon = (
                    asignacion["salon_id_final"] == otra["salon_id_final"]
                )
                codigo_salon = mapa_salon_codigo.get(
                    asignacion["salon_id_final"],
                    asignacion["salon_codigo"],
                )
                if (
                    mismo_salon
                    and not es_ambiente_compartible(codigo_salon)
                ):
                    conflictos_ambiente += 1

        conn.commit()
        mensajes = []
        if conflictos_ambiente:
            mensajes.append(
                f"Quedaron {conflictos_ambiente} colisión(es) de ambiente sin resolver: "
                "no hay suficientes ambientes libres en esos horarios."
            )
        if conflictos_docente:
            mensajes.append(
                f"Quedaron {conflictos_docente} colisión(es) de docente; "
                "se conserva el horario porque cambiar de ambiente no las resuelve."
            )
        total_reasignados = len(set([cid for _, cid in cambios_salones] + list(ids_horario_modificado)))
        return {
            "reasignados": total_reasignados,
            "conflictos_ambiente": conflictos_ambiente,
            "conflictos_docente": conflictos_docente,
            "mensajes": mensajes,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def validar_cambio_manual(asignacion_id, salon_id, dia, hora_inicio, hora_fin):
    """
    Verifica que al editar manualmente un horario no choque ni el profesor ni el salón.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT profesor_id FROM asignaciones_horario WHERE id = ?", (asignacion_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "La asignación no existe."

    profesor_id = row["profesor_id"]

    cursor.execute("""
        SELECT a.hora_inicio, a.hora_fin, m.nombre AS materia
        FROM asignaciones_horario a
        JOIN materias m ON m.id = a.materia_id
        WHERE a.profesor_id = ? AND a.dia = ? AND a.id != ?
    """, (profesor_id, dia, asignacion_id))
    for r in cursor.fetchall():
        if hay_solapamiento(hora_inicio, hora_fin, r["hora_inicio"], r["hora_fin"]):
            conn.close()
            return False, f"El profesor ya dicta '{r['materia']}' el {dia} de {r['hora_inicio']} a {r['hora_fin']}."

    cursor.execute("SELECT codigo FROM salones WHERE id = ?", (salon_id,))
    salon_row = cursor.fetchone()
    if salon_row and not es_ambiente_compartible(salon_row["codigo"]):
        cursor.execute("""
            SELECT a.hora_inicio, a.hora_fin, m.nombre AS materia, p.nombre AS profesor
            FROM asignaciones_horario a
            JOIN materias m ON m.id = a.materia_id
            JOIN profesores p ON p.id = a.profesor_id
            WHERE a.salon_id = ? AND a.dia = ? AND a.id != ?
        """, (salon_id, dia, asignacion_id))
        for r in cursor.fetchall():
            if hay_solapamiento(hora_inicio, hora_fin, r["hora_inicio"], r["hora_fin"]):
                conn.close()
                return False, (
                    f"El salón seleccionado ya está ocupado el {dia} de {r['hora_inicio']} a {r['hora_fin']} "
                    f"por '{r['materia']}' (Prof. {r['profesor']})."
                )

    conn.close()
    return True, "OK"
