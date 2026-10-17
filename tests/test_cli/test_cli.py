"""Pruebas unitarias para los comandos de la CLI de Novildo.
"""

import unittest
from pathlib import Path
import tempfile
import shutil
import io
from contextlib import redirect_stdout, redirect_stderr

from interfaces.cli.main import cli_main


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_file = str(Path(self.test_dir) / "cli_test_data.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def run_cli(self, args: list[str]) -> tuple[int, str, str]:
        """Ejecuta cli_main inyectando --data-file para aislar las pruebas."""
        full_args = ["--data-file", self.data_file] + args
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli_main(full_args)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_help_no_command(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = cli_main([])
        self.assertEqual(code, 0)
        self.assertIn("Novildo - Línea de tiempo", stdout.getvalue())

    def test_profile_command(self):
        # 1. Consultar perfil vacío
        code, out, _ = self.run_cli(["profile"])
        self.assertEqual(code, 0)
        self.assertIn("no configurado", out)

        # 2. Configurar año y mes de nacimiento
        code, out, _ = self.run_cli(["profile", "-b", "1998", "-m", "5"])
        self.assertEqual(code, 0)
        self.assertIn("Mayo de 1998", out)

        # 3. Consultar perfil nuevamente
        code, out, _ = self.run_cli(["profile"])
        self.assertEqual(code, 0)
        self.assertIn("Mayo de 1998", out)

        # 4. Limpiar solo mes de nacimiento
        code, out, _ = self.run_cli(["profile", "--clear-birth-month"])
        self.assertEqual(code, 0)
        self.assertIn("1998", out)

        # 5. Limpiar fecha completa (usando alias -c)
        code, out, _ = self.run_cli(["profile", "-c"])
        self.assertEqual(code, 0)
        self.assertIn("eliminado", out)

        # 6. Error de validación con mes inválido
        code, _, err = self.run_cli(["profile", "-m", "15"])
        self.assertEqual(code, 1)
        self.assertIn("Error en Novildo", err)

    def test_add_and_list_command(self):
        # Configurar perfil
        self.run_cli(["profile", "-b", "2000"])

        # Agregar recuerdos con alias cortos (-y, -m, -d)
        code, out, _ = self.run_cli(["add", "-y", "2010", "-m", "5", "-d", "Aprendí a programar"])
        self.assertEqual(code, 0)
        self.assertIn("Recuerdo registrado con éxito", out)
        self.assertIn("  - Año: 2010\n  - Mes: Mayo\n  - Descripción: Aprendí a programar", out)

        # Agregar recuerdos con opciones largas (--year, --month, --description)
        code, out, _ = self.run_cli(["add", "--year", "2020", "--description", "Comienzo de la universidad"])
        self.assertEqual(code, 0)
        self.assertIn("  - Año: 2020\n  - Descripción: Comienzo de la universidad", out)
        self.assertNotIn("Mes:", out)

        # Listar recuerdos (orden normal)
        code, out, _ = self.run_cli(["list"])
        self.assertEqual(code, 0)
        self.assertIn("Aprendí a programar", out)
        self.assertIn("10 años", out)  # 2010 - 2000 = 10 años
        self.assertIn("Comienzo de la universidad", out)
        self.assertIn("20 años", out)  # 2020 - 2000 = 20 años

        # Listar recuerdos en orden descendente usando alias -d
        code, out_desc, _ = self.run_cli(["list", "-d"])
        self.assertEqual(code, 0)
        self.assertTrue(out_desc.index("2020") < out_desc.index("2010"))

        # Configurar mes de nacimiento en Agosto (mes 8)
        self.run_cli(["profile", "-m", "8"])
        # Mayo 2010 es anterior a Agosto 2010, por lo que la edad exacta es 9 años (no 10)
        code, out_exact, _ = self.run_cli(["list"])
        self.assertEqual(code, 0)
        self.assertIn("9 años", out_exact)

        # Filtrar por año usando alias corto (-y)
        code, out_2010, _ = self.run_cli(["list", "-y", "2010"])
        self.assertEqual(code, 0)
        self.assertIn("Aprendí a programar", out_2010)
        self.assertNotIn("Comienzo de la universidad", out_2010)

        # Filtrar por año usando argumento largo (--year)
        code, out_2020, _ = self.run_cli(["list", "--year", "2020"])
        self.assertEqual(code, 0)
        self.assertIn("Comienzo de la universidad", out_2020)
        self.assertNotIn("Aprendí a programar", out_2020)

        # Filtrar por año sin recuerdos registrados
        code, out_empty, _ = self.run_cli(["list", "-y", "1999"])
        self.assertEqual(code, 0)
        self.assertIn("No hay recuerdos registrados para el año 1999", out_empty)

    def test_validation_error_cli(self):
        # Mes inválido
        code, _, err = self.run_cli(["add", "-y", "2020", "-m", "15", "-d", "Inválido"])
        self.assertEqual(code, 1)
        self.assertIn("Error en Novildo", err)

    def test_edit_command(self):
        # 1. Agregar un recuerdo
        code, out, _ = self.run_cli(["add", "-y", "2015", "-m", "3", "-d", "Trabajo inicial"])
        self.assertEqual(code, 0)
        # Extraer ID (está al final de 'ID: <id>')
        mem_id = [line for line in out.splitlines() if "ID:" in line][0].split("ID:")[1].strip()

        # 2. Editar el recuerdo usando alias 'edit'
        code, out, _ = self.run_cli(["edit", mem_id, "-y", "2016", "-d", "Trabajo actualizado"])
        self.assertEqual(code, 0)
        self.assertIn("Recuerdo actualizado con éxito", out)
        self.assertIn("2016", out)
        self.assertIn("Trabajo actualizado", out)

        # 3. Editar usando alias 'update' y quitar el mes con --clear-month
        code, out, _ = self.run_cli(["update", mem_id, "--clear-month"])
        self.assertEqual(code, 0)
        self.assertNotIn("Mes:", out)

        # 4. Editar con ID inexistente
        code, _, err = self.run_cli(["edit", "nonexistent", "-d", "Nada"])
        self.assertEqual(code, 1)
        self.assertIn("Error en Novildo", err)

    def test_delete_command(self):
        # 1. Agregar recuerdos
        _, out1, _ = self.run_cli(["add", "-y", "2010", "-d", "Recuerdo a borrar 1"])
        _, out2, _ = self.run_cli(["add", "-y", "2020", "-d", "Recuerdo a borrar 2"])
        id1 = [line for line in out1.splitlines() if "ID:" in line][0].split("ID:")[1].strip()
        id2 = [line for line in out2.splitlines() if "ID:" in line][0].split("ID:")[1].strip()

        # 2. Borrar primero con 'delete'
        code, out, _ = self.run_cli(["delete", id1])
        self.assertEqual(code, 0)
        self.assertIn("Recuerdo eliminado con éxito", out)

        # 3. Borrar segundo con alias 'rm'
        code, out, _ = self.run_cli(["rm", id2])
        self.assertEqual(code, 0)
        self.assertIn("Recuerdo eliminado con éxito", out)

        # 4. Listar y verificar que esté vacío
        code, out, _ = self.run_cli(["list"])
        self.assertEqual(code, 0)
        self.assertIn("No hay recuerdos registrados", out)

    def test_version_commands(self):
        code, out, _ = self.run_cli(["version"])
        self.assertEqual(code, 0)
        self.assertIn("Novildo v0.2.0", out)

        code, out, _ = self.run_cli(["v"])
        self.assertEqual(code, 0)
        self.assertIn("Novildo v0.2.0", out)

    def test_help_commands(self):
        # Ayuda general con comando 'help'
        code, out, _ = self.run_cli(["help"])
        self.assertEqual(code, 0)
        self.assertIn("Novildo - Línea de tiempo", out)
        self.assertIn("-y, --year", out)
        self.assertIn("-m, --month", out)
        self.assertIn("-d, --description", out)

        # Ayuda general con alias 'h'
        code, out_h, _ = self.run_cli(["h"])
        self.assertEqual(code, 0)
        self.assertIn("Novildo - Línea de tiempo", out_h)

        # Ayuda para subcomando específico
        code, out_add, _ = self.run_cli(["help", "add"])
        self.assertEqual(code, 0)
        self.assertIn("add", out_add)
        self.assertIn("-y", out_add)

        code, out_list, _ = self.run_cli(["h", "list"])
        self.assertEqual(code, 0)
        self.assertIn("list", out_list)

        # Subcomando desconocido
        code, _, err = self.run_cli(["help", "inexistente"])
        self.assertEqual(code, 1)
        self.assertIn("Comando desconocido", err)

    def test_tag_commands(self):
        # 1. Crear etiqueta con comando 'tag add' y emote
        code, out1, _ = self.run_cli(["tag", "add", "Estudios", "-e", "🎓"])
        self.assertEqual(code, 0)
        self.assertIn("✓ Etiqueta creada con éxito:", out1)
        self.assertIn("ID: 1", out1)
        self.assertIn("Nombre: Estudios", out1)
        self.assertIn("Emote: 🎓", out1)

        # 2. Crear segunda etiqueta usando alias 't add'
        code, out2, _ = self.run_cli(["t", "add", "Trabajo", "-e", "💼"])
        self.assertEqual(code, 0)
        self.assertIn("ID: 2", out2)

        # 3. Crear tercera etiqueta con sintaxis directa 'tag <NOMBRE>'
        code, out3, _ = self.run_cli(["tag", "Personal"])
        self.assertEqual(code, 0)
        self.assertIn("ID: 3", out3)

        # 4. Listar etiquetas con 'tag list' y con alias 't'
        code, out_list, _ = self.run_cli(["tag", "list"])
        self.assertEqual(code, 0)
        self.assertIn("Estudios", out_list)
        self.assertIn("Trabajo", out_list)
        self.assertIn("Personal", out_list)
        self.assertIn("🎓", out_list)

        code, out_t, _ = self.run_cli(["t"])
        self.assertEqual(code, 0)
        self.assertIn("Estudios", out_t)

        # 5. Agregar recuerdos asociados a etiquetas usando -t / --tag
        code, out_add1, _ = self.run_cli(["add", "-y", "2024", "-m", "3", "-d", "Graduación", "-t", "1"])
        self.assertEqual(code, 0)
        self.assertIn("Etiqueta: 🎓 Estudios (ID: 1)", out_add1)
        id1 = [line for line in out_add1.splitlines() if line.strip().startswith("- ID:")][0].split("- ID:")[1].strip()

        code, out_add2, _ = self.run_cli(["add", "-y", "2024", "-m", "5", "-d", "Primer empleo", "--tag", "2"])
        self.assertEqual(code, 0)
        self.assertIn("Etiqueta: 💼 Trabajo (ID: 2)", out_add2)

        code, _, _ = self.run_cli(["add", "-y", "2024", "-m", "10", "-d", "Mudanza"])

        # 6. Listar recuerdos y verificar que la columna Etiqueta se muestre
        code, out_all, _ = self.run_cli(["list"])
        self.assertEqual(code, 0)
        self.assertIn("Etiqueta", out_all)
        self.assertIn("🎓 Estudios", out_all)
        self.assertIn("💼 Trabajo", out_all)

        # 7. Filtrar por etiqueta usando -t 1
        code, out_filter_t1, _ = self.run_cli(["list", "-t", "1"])
        self.assertEqual(code, 0)
        self.assertIn("Graduación", out_filter_t1)
        self.assertNotIn("Primer empleo", out_filter_t1)
        self.assertNotIn("Mudanza", out_filter_t1)

        # Filtrar por etiqueta usando --tag 2
        code, out_filter_t2, _ = self.run_cli(["list", "--tag", "2"])
        self.assertEqual(code, 0)
        self.assertIn("Primer empleo", out_filter_t2)
        self.assertNotIn("Graduación", out_filter_t2)

        # Filtrar por etiqueta 3 (Personal) que no tiene recuerdos
        code, out_filter_t3, _ = self.run_cli(["list", "-t", "3"])
        self.assertEqual(code, 0)
        self.assertIn("No hay recuerdos registrados con la etiqueta 'Personal' (ID 3)", out_filter_t3)

        # Filtrar por etiqueta inexistente
        code, _, err_filter = self.run_cli(["list", "-t", "99"])
        self.assertEqual(code, 1)
        self.assertIn("No existe ninguna etiqueta con el ID 99", err_filter)

        # 8. Modificar la etiqueta de un recuerdo con edit -t
        code, out_edit, _ = self.run_cli(["edit", id1, "-t", "2"])
        self.assertEqual(code, 0)
        self.assertIn("Etiqueta: 💼 Trabajo (ID: 2)", out_edit)

        # 9. Quitar la etiqueta de un recuerdo con edit --clear-tag
        code, out_clear_tag, _ = self.run_cli(["edit", id1, "--clear-tag"])
        self.assertEqual(code, 0)
        self.assertNotIn("Etiqueta:", out_clear_tag)

        # 10. Eliminar una etiqueta con 'tag delete' y con alias 'rm'
        code, out_del, _ = self.run_cli(["tag", "delete", "1"])
        self.assertEqual(code, 0)
        self.assertIn("Etiqueta eliminada con éxito:", out_del)
        self.assertIn("Estudios", out_del)

        code, out_del2, _ = self.run_cli(["tag", "rm", "2"])
        self.assertEqual(code, 0)
        self.assertIn("Trabajo", out_del2)

    def test_person_commands(self):
        # 1. Registrar persona con 'person add', año (-b) y mes (-m)
        code, out1, _ = self.run_cli(["person", "add", "Juan Pérez", "-b", "1990", "-m", "5"])
        self.assertEqual(code, 0)
        self.assertIn("✓ Persona registrada con éxito:", out1)
        self.assertIn("ID: 1", out1)
        self.assertIn("Nombre: Juan Pérez", out1)
        self.assertIn("Fecha de nacimiento: Mayo de 1990", out1)

        # 2. Registrar persona con alias 'p add' y año
        code, out2, _ = self.run_cli(["p", "add", "María López", "-b", "1995"])
        self.assertEqual(code, 0)
        self.assertIn("ID: 2", out2)
        self.assertIn("Año de nacimiento: 1995", out2)

        # 3. Registrar persona con sintaxis directa 'person <NOMBRE>' sin fecha
        code, out3, _ = self.run_cli(["person", "Carlos Ruiz"])
        self.assertEqual(code, 0)
        self.assertIn("ID: 3", out3)
        self.assertIn("Nombre: Carlos Ruiz", out3)

        # 4. Listar personas con 'person list', 'p' y 'person -l'
        code, out_list, _ = self.run_cli(["person", "list"])
        self.assertEqual(code, 0)
        self.assertIn("Juan Pérez", out_list)
        self.assertIn("Mayo de 1990", out_list)
        self.assertIn("María López", out_list)
        self.assertIn("Carlos Ruiz", out_list)

        code, out_p, _ = self.run_cli(["p"])
        self.assertEqual(code, 0)
        self.assertIn("Juan Pérez", out_p)

        # 5. Agregar recuerdos vinculando personas con -p
        # Juan nació en mayo 1990. Evento en abril 2020 -> 29 años
        code, out_add1, _ = self.run_cli(["add", "-y", "2020", "-m", "4", "-d", "Viaje con Juan", "-p", "1"])
        self.assertEqual(code, 0)
        self.assertIn("Personas: Juan Pérez (29 años)", out_add1)
        id1 = [line for line in out_add1.splitlines() if line.strip().startswith("- ID:")][0].split("- ID:")[1].strip()

        # Evento vinculando múltiples personas: -p 1 2
        # Juan en mayo 2020 cumple 30. Evento en junio 2020 -> Juan 30 años, María (nac 1995) 25 años
        code, out_add2, _ = self.run_cli(["add", "-y", "2020", "-m", "6", "-d", "Reunión de amigos", "-p", "1", "2"])
        self.assertEqual(code, 0)
        self.assertIn("Personas: Juan Pérez (30 años), María López (25 años)", out_add2)

        # Evento con comma-separated IDs: -p 2,3
        code, out_add3, _ = self.run_cli(["add", "-y", "2021", "-d", "Proyecto con María y Carlos", "-p", "2,3"])
        self.assertEqual(code, 0)
        self.assertIn("Personas: María López (26 años), Carlos Ruiz", out_add3)

        # 6. Listar recuerdos y verificar la columna 'Personas'
        code, out_all, _ = self.run_cli(["list"])
        self.assertEqual(code, 0)
        self.assertIn("Personas", out_all)
        self.assertIn("Juan Pérez (29 años)", out_all)
        self.assertIn("Juan Pérez (30 años), María López (25 años)", out_all)

        # 7. Filtrar por persona con -p 1
        code, out_filter_p1, _ = self.run_cli(["list", "-p", "1"])
        self.assertEqual(code, 0)
        self.assertIn("Viaje con Juan", out_filter_p1)
        self.assertIn("Reunión de amigos", out_filter_p1)
        self.assertNotIn("Proyecto con María y Carlos", out_filter_p1)

        # Filtrar por persona con --person 2
        code, out_filter_p2, _ = self.run_cli(["list", "--person", "2"])
        self.assertEqual(code, 0)
        self.assertIn("Reunión de amigos", out_filter_p2)
        self.assertIn("Proyecto con María y Carlos", out_filter_p2)
        self.assertNotIn("Viaje con Juan", out_filter_p2)

        # Filtrar por persona 3 (Carlos) que sólo está en Proyecto
        code, out_filter_p3, _ = self.run_cli(["list", "-p", "3"])
        self.assertEqual(code, 0)
        self.assertIn("Proyecto con María y Carlos", out_filter_p3)
        self.assertNotIn("Viaje con Juan", out_filter_p3)

        # Filtrar por persona inexistente -> Error
        code, _, err_p99 = self.run_cli(["list", "-p", "99"])
        self.assertEqual(code, 1)
        self.assertIn("No existe ninguna persona con el ID 99", err_p99)

        # 8. Modificar personas en un recuerdo con edit -p
        code, out_edit, _ = self.run_cli(["edit", id1, "-p", "3"])
        self.assertEqual(code, 0)
        self.assertIn("Personas: Carlos Ruiz", out_edit)
        self.assertNotIn("Juan Pérez", out_edit)

        # 9. Limpiar personas con edit --clear-people
        code, out_clear, _ = self.run_cli(["edit", id1, "--clear-people"])
        self.assertEqual(code, 0)
        self.assertNotIn("Personas:", out_clear)

        # 10. Eliminar persona con 'person delete'
        code, out_del, _ = self.run_cli(["person", "delete", "1"])
        self.assertEqual(code, 0)
        self.assertIn("✓ Persona eliminada con éxito:", out_del)
        self.assertIn("Juan Pérez", out_del)

        # Verificar que ya no aparece en 'person list'
        code, out_remaining, _ = self.run_cli(["person", "list"])
        self.assertEqual(code, 0)
        self.assertNotIn("Juan Pérez", out_remaining)
        self.assertIn("María López", out_remaining)


if __name__ == "__main__":
    unittest.main()
