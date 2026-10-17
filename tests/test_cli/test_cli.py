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


if __name__ == "__main__":
    unittest.main()
