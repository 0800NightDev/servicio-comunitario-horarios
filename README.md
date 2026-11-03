# Universidad Simón Rodríguez (UNESR) — Sistema de Oferta Académica y Gestión de Horarios (Núcleo Palo Verde)

Sistema interactivo de escritorio desarrollado en **Python (Flet + SQLite)** para la **Universidad Nacional Experimental Simón Rodríguez (UNESR / USR) — Núcleo Palo Verde**, diseñado para organizar la oferta académica universitaria por carrera/facultad, asignar horarios y ambientes sin conflictos de forma automática, e importar cargas académicas desde archivos **Excel (`.xlsx`)**, **Word (`.docx`)** y **Texto (`.txt` / `.csv`)**.

---

## Características Principales

1. **Interfaz Interactiva en Flet (Modo Oscuro Institucional)**
   - **Dashboard**: Estadísticas en tiempo real de cursos activos, ambientes ocupados/disponibles, docentes activos y verificación de `0 Conflictos`.
   - **Nueva Carga**: Registro individual con asignación automática de día, franja horaria y ambiente libre, además de importación masiva desde documentos `.xlsx`, `.docx` y `.txt`.
   - **Horarios (1. Oferta Académica General)**: Consulta filtrable por carrera, día y docente (ordenados alfabéticamente), con exportación a HTML/PDF imprimible.
   - **Ambientes**: Monitoreo visual de ocupación y capacidad de cada aula y laboratorio (`P1-01` a `P4-07`, `PB`, `VIRTUAL`).
   - **Docentes (2. Horario Tipo Calendario de cada Profesor + 3. Impresión PDF/HTML)**:
     - Visualizador interactivo del horario semanal tipo calendario (`Lunes` a `Sábado` por bloque horario) para cada docente.
     - Generador de reportes imprimibles HTML/PDF con opción de elegir **todos los profesores registrados** o **un (1) solo profesor** de la lista.
   - **Carreras**: Panel de carreras registradas y su pensum de materias.

2. **Base de Datos SQL Ligera y Persistente (`SQLite`)**
   - Almacenamiento automático en `universidad_horarios.db` ([`database.py`](database.py)).

---

## Requisitos e Instalación

1. Crear y activar el entorno virtual (Python 3.10+):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
2. Instalar las dependencias:
   ```powershell
   pip install -r requirements.txt
   ```
3. Ejecutar la aplicación:
   ```powershell
   python SGHU_Universidad.py
   ```
   *(En Windows también puedes iniciar haciendo doble clic en `iniciar_sistema.bat`).*
