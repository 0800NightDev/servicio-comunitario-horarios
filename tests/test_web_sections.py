import os
import tempfile
import unittest

import database


class WebSectionsTests(unittest.TestCase):
    def setUp(self):
        self.previous_db_path = database.DB_PATH
        self.previous_database_url = database.DATABASE_URL
        self.temp_dir = tempfile.TemporaryDirectory()
        database.DB_PATH = os.path.join(self.temp_dir.name, "web-test.db")
        database.DATABASE_URL = ""
        database.init_db()

        import app as web_app

        self.web_app = web_app
        self.client = web_app.app.test_client()

    def tearDown(self):
        database.DB_PATH = self.previous_db_path
        database.DATABASE_URL = self.previous_database_url
        self.temp_dir.cleanup()

    def test_primary_sections_and_unesr_logo_render(self):
        for path in ("/", "/nueva-carga", "/horarios", "/ambientes", "/docentes", "/carreras"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                body = response.get_data(as_text=True)
                self.assertIn("Dashboard", body)
                self.assertIn("Nueva Carga", body)
                self.assertIn("Horarios", body)
                self.assertIn("Ambientes", body)
                self.assertIn("Docentes", body)
                self.assertIn("Carreras", body)

        logo = self.client.get("/logo-unesr.png")
        self.assertEqual(logo.status_code, 200)
        self.assertEqual(logo.mimetype, "image/png")
        self.assertTrue(logo.data.startswith(b"\x89PNG"))
        logo.close()

    def test_manual_teacher_form_saves_multiple_subjects_and_slots(self):
        response = self.client.post(
            "/agregar-manual",
            data={
                "tipo_carga": "ficha_docente",
                "docente": "Ana Docente Integracion",
                "cedula": "V-12345678",
                "correo": "ana.integration@example.edu",
                "condicion": "Ordinario/a",
                "materia": ["Materia Integracion A", "Materia Integracion B"],
                "carrera": ["Carrera Integracion A", "Carrera Integracion B"],
                "mencion": ["", ""],
                "ambiente": ["", ""],
                "codigo": ["INTA", "INTB"],
                "ciclo": ["1er Semestre", "2do Semestre"],
                "seccion": ["101", "102"],
                "unidad_credito": ["3", "4"],
                "compartidos": ["", ""],
                "disponibilidad": ["Lunes|07:00|07:45", "Martes|07:45|08:30"],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/oferta-general"))

        conn = database.get_connection()
        cursor = conn.cursor()
        subjects = cursor.execute(
            "SELECT COUNT(*) AS n FROM materias WHERE nombre LIKE 'MATERIA INTEGRACION%'"
        ).fetchone()["n"]
        slots = cursor.execute(
            """SELECT COUNT(*) AS n
               FROM disponibilidades d
               JOIN profesores p ON p.id = d.profesor_id
               WHERE p.nombre = 'ANA DOCENTE INTEGRACION'"""
        ).fetchone()["n"]
        conn.close()
        self.assertEqual(subjects, 2)
        self.assertEqual(slots, 2)


if __name__ == "__main__":
    unittest.main()
