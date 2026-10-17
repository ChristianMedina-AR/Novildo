"""Pruebas unitarias para la lógica de negocio y servicios del core.
"""

import unittest
from core.models import Memory, UserProfile
from core.services import TimelineService
from core.storage import InMemoryStorage
from core.exceptions import ValidationError, NotFoundError


class TestTimelineService(unittest.TestCase):
    def setUp(self):
        self.storage = InMemoryStorage()
        self.service = TimelineService(repository=self.storage)

    def test_calculate_age_without_birth_year(self):
        age = self.service.calculate_age(event_year=2020, birth_year=None)
        self.assertIsNone(age)

    def test_calculate_age_with_birth_year(self):
        age = self.service.calculate_age(event_year=2020, birth_year=1995)
        self.assertEqual(age, 25)

    def test_calculate_age_with_months(self):
        # Nacimiento: Mayo 2000 (mes 5)
        # 1. Evento previo al mes de cumpleaños en el mismo año (Febrero 2020 -> 19 años)
        age_before = self.service.calculate_age(event_year=2020, birth_year=2000, event_month=2, birth_month=5)
        self.assertEqual(age_before, 19)

        # 2. Evento en el mes de cumpleaños (Mayo 2020 -> 20 años)
        age_exact = self.service.calculate_age(event_year=2020, birth_year=2000, event_month=5, birth_month=5)
        self.assertEqual(age_exact, 20)

        # 3. Evento posterior al mes de cumpleaños (Octubre 2020 -> 20 años)
        age_after = self.service.calculate_age(event_year=2020, birth_year=2000, event_month=10, birth_month=5)
        self.assertEqual(age_after, 20)

        # 4. Evento sin mes especificado (retorna estimación directa: 2020 - 2000 = 20)
        age_no_month = self.service.calculate_age(event_year=2020, birth_year=2000, event_month=None, birth_month=5)
        self.assertEqual(age_no_month, 20)

    def test_calculate_age_event_before_birth(self):
        age = self.service.calculate_age(event_year=1990, birth_year=1995)
        self.assertEqual(age, -5)

    def test_register_memory(self):
        mem = self.service.register_memory(year=2010, description="Primer empleo", month=3)
        self.assertEqual(mem.year, 2010)
        self.assertEqual(mem.month, 3)
        self.assertEqual(mem.description, "Primer empleo")
        
        all_mems = self.storage.get_memories()
        self.assertEqual(len(all_mems), 1)
        self.assertEqual(all_mems[0].description, "Primer empleo")

    def test_get_timeline_sorting(self):
        # Insert memories out of order
        self.service.register_memory(year=2020, month=12, description="Fin de año 2020")
        self.service.register_memory(year=2015, month=None, description="Año sabático 2015")
        self.service.register_memory(year=2020, month=1, description="Año nuevo 2020")
        self.service.register_memory(year=2015, month=6, description="Mitad de año 2015")

        timeline = self.service.get_timeline(ascending=True)
        self.assertEqual(len(timeline), 4)

        # En 2015: mes 6 (Junio) va antes de mes None (fin de año).
        # En 2020: mes 1 va antes de mes 12.
        self.assertEqual(timeline[0].memory.year, 2015)
        self.assertEqual(timeline[0].memory.month, 6)

        self.assertEqual(timeline[1].memory.year, 2015)
        self.assertIsNone(timeline[1].memory.month)

        self.assertEqual(timeline[2].memory.year, 2020)
        self.assertEqual(timeline[2].memory.month, 1)

        self.assertEqual(timeline[3].memory.year, 2020)
        self.assertEqual(timeline[3].memory.month, 12)

    def test_sorting_same_year_none_month_placed_last_for_coherent_age(self):
        # Nacimiento: Mayo 1994 (mes 5)
        self.service.update_profile(birth_year=1994, birth_month=5)

        # En el año 2020:
        # - Febrero (mes 2): 25 años
        # - Sin mes (None -> fin de año): 26 años
        # - Noviembre (mes 11): 26 años
        self.service.register_memory(year=2020, month=None, description="Evento general del 2020")
        self.service.register_memory(year=2020, month=2, description="Evento de Febrero")
        self.service.register_memory(year=2020, month=11, description="Evento de Noviembre")

        timeline = self.service.get_timeline(ascending=True)
        # Orden esperado: Febrero (mes 2, 25 años) -> Noviembre (mes 11, 26 años) -> Sin mes (al final del 2020, 26 años)
        self.assertEqual(timeline[0].memory.description, "Evento de Febrero")
        self.assertEqual(timeline[0].age, 25)

        self.assertEqual(timeline[1].memory.description, "Evento de Noviembre")
        self.assertEqual(timeline[1].age, 26)

        self.assertEqual(timeline[2].memory.description, "Evento general del 2020")
        self.assertIsNone(timeline[2].memory.month)
        self.assertEqual(timeline[2].age, 26)

    def test_get_timeline_with_calculated_age(self):
        # Nacimiento: Julio 2000 (mes 7)
        self.service.update_profile(birth_year=2000, birth_month=7)
        self.service.register_memory(year=2018, month=3, description="Antes de cumplir 18") # Marzo < Julio -> 17 años
        self.service.register_memory(year=2018, month=8, description="Cumpleaños 18 ya pasado") # Agosto >= Julio -> 18 años
        self.service.register_memory(year=2025, month=None, description="Viaje a Japón") # Sin mes -> 25 años

        timeline = self.service.get_timeline()
        self.assertEqual(timeline[0].age, 17)
        self.assertEqual(timeline[1].age, 18)
        self.assertEqual(timeline[2].age, 25)

    def test_update_and_get_profile(self):
        self.service.update_profile(birth_year=1992, birth_month=8)
        profile = self.service.get_profile()
        self.assertEqual(profile.birth_year, 1992)
        self.assertEqual(profile.birth_month, 8)

        # Limpiar mes manteniendo el año
        self.service.update_profile(clear_birth_month=True)
        profile_cleared_month = self.service.get_profile()
        self.assertEqual(profile_cleared_month.birth_year, 1992)
        self.assertIsNone(profile_cleared_month.birth_month)

    def test_update_memory(self):
        mem = self.service.register_memory(year=2015, month=3, description="Viaje inicial")
        updated = self.service.update_memory(
            memory_id=mem.id,
            year=2016,
            month=4,
            description="Viaje actualizado",
        )
        self.assertEqual(updated.year, 2016)
        self.assertEqual(updated.month, 4)
        self.assertEqual(updated.description, "Viaje actualizado")

        # Probar limpiar mes
        cleared = self.service.update_memory(memory_id=mem.id, clear_month=True)
        self.assertIsNone(cleared.month)

    def test_update_memory_no_changes(self):
        mem = self.service.register_memory(year=2015, description="Sin cambios")
        with self.assertRaises(ValidationError):
            self.service.update_memory(memory_id=mem.id)

    def test_update_nonexistent_memory(self):
        with self.assertRaises(NotFoundError):
            self.service.update_memory(memory_id="99999999", year=2020)

    def test_delete_memory(self):
        mem = self.service.register_memory(year=2018, description="Para borrar")
        deleted = self.service.delete_memory(mem.id)
        self.assertEqual(deleted.id, mem.id)
        with self.assertRaises(NotFoundError):
            self.service.get_memory(mem.id)


if __name__ == "__main__":
    unittest.main()
