import unittest
import os
import tempfile

import database
import seed_demo


class SqliteBehaviorTests(unittest.TestCase):
    def test_fresh_schema_and_get_or_create_helpers(self):
        previous_db_path = database.DB_PATH
        previous_database_url = database.DATABASE_URL
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                database.DATABASE_URL = ""
                database.DB_PATH = os.path.join(temp_dir, "test.db")
                database.init_db()
                conn = database.get_connection()
                cursor = conn.cursor()

                faculty_id = database.get_or_create_facultad(cursor, "Facultad de prueba")
                self.assertEqual(
                    faculty_id,
                    database.get_or_create_facultad(cursor, "Facultad de prueba"),
                )
                career_id = database.get_or_create_carrera(cursor, "Carrera de prueba", faculty_id)
                self.assertEqual(
                    career_id,
                    database.get_or_create_carrera(cursor, "Carrera de prueba", faculty_id),
                )
                self.assertEqual(
                    database.get_or_create_profesor(cursor, "Docente de prueba"),
                    database.get_or_create_profesor(cursor, "Docente de prueba"),
                )
                self.assertEqual(
                    database.get_or_create_materia(cursor, "Materia de prueba", career_id),
                    database.get_or_create_materia(cursor, "Materia de prueba", career_id),
                )
                self.assertEqual(
                    database.get_or_create_salon(cursor, "PRUEBA-01"),
                    database.get_or_create_salon(cursor, "PRUEBA-01"),
                )
                conn.commit()
                self.assertEqual(
                    cursor.execute("SELECT COUNT(*) AS n FROM salones").fetchone()["n"],
                    len(database.salones_predeterminados()) + 1,
                )
                conn.close()
            finally:
                database.DB_PATH = previous_db_path
                database.DATABASE_URL = previous_database_url


class ExampleTemplateTests(unittest.TestCase):
    def test_existing_template_files_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            examples_dir = os.path.join(temp_dir, "ejemplos")
            os.makedirs(examples_dir)
            expected = {
                "plantilla_profesores.xlsx": b"existing xlsx",
                "plantilla_profesores.docx": b"existing docx",
                "plantilla_profesores.txt": b"existing text",
            }
            for name, content in expected.items():
                with open(os.path.join(examples_dir, name), "wb") as template:
                    template.write(content)

            paths = seed_demo.crear_archivos_ejemplo(temp_dir)

            for file_path in paths.values():
                with open(file_path, "rb") as template:
                    self.assertEqual(template.read(), expected[os.path.basename(file_path)])


class PostgresCompatibilityTests(unittest.TestCase):
    def test_sqlite_insert_ignore_and_placeholders_are_translated(self):
        sql = database._postgres_sql(
            "INSERT OR IGNORE INTO disponibilidad (profesor_id, dia) VALUES (?, ?)"
        )
        self.assertEqual(
            sql,
            "INSERT INTO disponibilidad (profesor_id, dia) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        )

    def test_sqlite_schema_and_collation_are_translated(self):
        sql = database._postgres_sql(
            "CREATE TABLE ejemplo (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT); "
            "SELECT nombre FROM ejemplo ORDER BY nombre COLLATE NOCASE"
        )
        self.assertIn("id SERIAL PRIMARY KEY", sql)
        self.assertNotIn("COLLATE NOCASE", sql)

    def test_postgres_migrations_ignore_existing_columns(self):
        sql = database._postgres_sql(
            "ALTER TABLE profesores ADD COLUMN condicion TEXT DEFAULT 'Contratado/a'"
        )
        self.assertIn("ADD COLUMN IF NOT EXISTS condicion", sql)

    def test_postgres_row_supports_sqlite_row_access_patterns(self):
        row = database.PostgresRow({"id": 12, "nombre": "Docente"})
        self.assertEqual(row["nombre"], "Docente")
        self.assertEqual(row[0], 12)
        self.assertEqual(dict(row), {"id": 12, "nombre": "Docente"})


class PostgresIntegrationTests(unittest.TestCase):
    @unittest.skipUnless(
        os.environ.get("TEST_DATABASE_URL"),
        "TEST_DATABASE_URL not set; PostgreSQL integration test skipped",
    )
    def test_schema_and_writes_on_postgres(self):
        previous_database_url = database.DATABASE_URL
        database.DATABASE_URL = os.environ["TEST_DATABASE_URL"]
        conn = None
        try:
            database.init_db()
            conn = database.get_connection()
            cursor = conn.cursor()

            faculty_id = database.get_or_create_facultad(cursor, "Facultad de prueba CI")
            self.assertEqual(
                faculty_id,
                database.get_or_create_facultad(cursor, "Facultad de prueba CI"),
            )
            career_id = database.get_or_create_carrera(cursor, "Carrera de prueba CI", faculty_id)
            professor_id = database.get_or_create_profesor(cursor, "Docente de prueba CI")

            for _ in range(2):
                cursor.execute(
                    """INSERT OR IGNORE INTO disponibilidades
                       (profesor_id, dia, hora_inicio, hora_fin)
                       VALUES (?, ?, ?, ?)""",
                    (professor_id, "Lunes", "07:00", "09:00"),
                )
            count = cursor.execute(
                "SELECT COUNT(*) AS n FROM disponibilidades WHERE profesor_id = ?",
                (professor_id,),
            ).fetchone()["n"]
            self.assertEqual(count, 1)

            materia_id = database.get_or_create_materia(cursor, "Materia de prueba CI", career_id)
            self.assertEqual(
                materia_id,
                database.get_or_create_materia(cursor, "Materia de prueba CI", career_id),
            )
            conn.commit()
        finally:
            if conn is not None:
                conn.close()
            database.DATABASE_URL = previous_database_url


if __name__ == "__main__":
    unittest.main()
