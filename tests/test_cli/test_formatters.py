"""Pruebas unitarias para los formateadores de la CLI.
"""

import unittest
from core.models import Memory, UserProfile
from core.services import TimelineEntry
from interfaces.cli.formatters import (
    format_month,
    format_timeline,
    format_memory_added,
    format_memory_updated,
    format_memory_deleted,
    format_profile,
    format_profile_updated,
)


class TestFormatters(unittest.TestCase):
    def test_format_month(self):
        self.assertEqual(format_month(None), "-")
        self.assertEqual(format_month(1), "Enero")
        self.assertEqual(format_month(12), "Diciembre")
        self.assertEqual(format_month(6), "Junio")

    def test_format_empty_timeline(self):
        output = format_timeline([])
        self.assertIn("No hay recuerdos registrados", output)

    def test_format_timeline_with_entries(self):
        m1 = Memory(year=2000, month=3, description="Nacimiento")
        m2 = Memory(year=2020, month=None, description="Pandemia")
        entries = [
            TimelineEntry(memory=m1, age=0),
            TimelineEntry(memory=m2, age=20),
        ]
        output = format_timeline(entries)
        self.assertIn("ID", output)
        self.assertIn("Año", output)
        self.assertIn("Mes", output)
        self.assertIn("Edad", output)
        self.assertIn("Descripción", output)
        self.assertIn(m1.id, output)
        self.assertIn(m2.id, output)
        self.assertIn("2000", output)
        self.assertIn("Marzo", output)
        self.assertIn("0 años", output)
        self.assertIn("Pandemia", output)

    def test_format_memory_added(self):
        mem = Memory(year=2024, month=1, description="Comienzo de nuevo proyecto")
        output = format_memory_added(mem)
        self.assertIn("  - Año: 2024\n  - Mes: Enero\n  - Descripción: Comienzo de nuevo proyecto", output)

    def test_format_memory_added_without_month(self):
        mem = Memory(year=2024, month=None, description="Sin mes")
        output = format_memory_added(mem)
        self.assertIn("  - Año: 2024\n  - Descripción: Sin mes", output)
        self.assertNotIn("Mes:", output)

    def test_format_memory_updated(self):
        mem = Memory(year=2024, month=2, description="Editado", id="11223344")
        output = format_memory_updated(mem)
        self.assertIn("✓ Recuerdo actualizado con éxito:", output)
        self.assertIn("  - ID: 11223344", output)
        self.assertIn("  - Año: 2024", output)
        self.assertIn("  - Mes: Febrero", output)
        self.assertIn("  - Descripción: Editado", output)

    def test_format_memory_deleted(self):
        mem = Memory(year=2024, month=None, description="Borrado", id="55667788")
        output = format_memory_deleted(mem)
        self.assertIn("✓ Recuerdo eliminado con éxito:", output)
        self.assertIn("  - ID: 55667788", output)
        self.assertIn("  - Descripción: Borrado", output)
        self.assertNotIn("Mes:", output)

    def test_format_profile(self):
        p1 = UserProfile(birth_year=1995)
        self.assertIn("1995", format_profile(p1))

        p2 = UserProfile(birth_year=None)
        self.assertIn("no configurado", format_profile(p2))

        p3 = UserProfile(birth_year=1994, birth_month=5)
        self.assertIn("Mayo de 1994", format_profile(p3))

    def test_format_profile_updated(self):
        p = UserProfile(birth_year=2001)
        self.assertIn("2001", format_profile_updated(p))

        p_month = UserProfile(birth_year=2001, birth_month=12)
        self.assertIn("Diciembre de 2001", format_profile_updated(p_month))

        p_empty = UserProfile(birth_year=None)
        self.assertIn("eliminado", format_profile_updated(p_empty))


if __name__ == "__main__":
    unittest.main()
