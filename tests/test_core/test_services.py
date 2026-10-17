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

    def test_get_timeline_filtered_by_year(self):
        self.service.register_memory(year=2015, description="Memoria 2015")
        self.service.register_memory(year=2020, month=3, description="Memoria Marzo 2020")
        self.service.register_memory(year=2020, month=8, description="Memoria Agosto 2020")
        self.service.register_memory(year=2024, description="Memoria 2024")

        # Filtrar por año 2020
        timeline_2020 = self.service.get_timeline(year=2020)
        self.assertEqual(len(timeline_2020), 2)
        self.assertTrue(all(e.memory.year == 2020 for e in timeline_2020))
        self.assertEqual(timeline_2020[0].memory.description, "Memoria Marzo 2020")
        self.assertEqual(timeline_2020[1].memory.description, "Memoria Agosto 2020")

        # Filtrar por año sin recuerdos
        timeline_empty = self.service.get_timeline(year=1999)
        self.assertEqual(timeline_empty, [])

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

    def test_tag_lifecycle_and_auto_increment(self):
        # Primer tag debe tener ID 1
        t1 = self.service.register_tag("Estudios", emoji="🎓")
        self.assertEqual(t1.id, 1)
        self.assertEqual(t1.name, "Estudios")
        self.assertEqual(t1.emoji, "🎓")

        # Segundo tag debe tener ID 2
        t2 = self.service.register_tag("Trabajo", emoji="💼")
        self.assertEqual(t2.id, 2)

        # Tercer tag debe tener ID 3
        t3 = self.service.register_tag("Personal")
        self.assertEqual(t3.id, 3)
        self.assertIsNone(t3.emoji)

        tags = self.service.get_tags()
        self.assertEqual(len(tags), 3)
        self.assertEqual([t.id for t in tags], [1, 2, 3])

        # Obtener por ID
        self.assertEqual(self.service.get_tag(1).name, "Estudios")
        with self.assertRaises(NotFoundError):
            self.service.get_tag(999)

    def test_tag_duplicate_name_rejected(self):
        self.service.register_tag("Estudios", emoji="🎓")
        with self.assertRaises(ValidationError):
            self.service.register_tag("estudios")
        with self.assertRaises(ValidationError):
            self.service.register_tag("  Estudios  ")

    def test_tag_empty_name_rejected(self):
        with self.assertRaises(ValidationError):
            self.service.register_tag("")
        with self.assertRaises(ValidationError):
            self.service.register_tag("   ")

    def test_register_memory_with_tag(self):
        tag = self.service.register_tag("Estudios", emoji="🎓")
        mem = self.service.register_memory(year=2024, description="Graduación", tag_id=tag.id)
        self.assertEqual(mem.tag_id, 1)

        # Tag inexistente
        with self.assertRaises(NotFoundError):
            self.service.register_memory(year=2024, description="Falla", tag_id=99)

    def test_update_memory_tag_and_clear_tag(self):
        t1 = self.service.register_tag("Estudios", emoji="🎓")
        t2 = self.service.register_tag("Trabajo", emoji="💼")
        mem = self.service.register_memory(year=2024, description="Inicio", tag_id=t1.id)

        # Cambiar a t2
        updated = self.service.update_memory(mem.id, tag_id=t2.id)
        self.assertEqual(updated.tag_id, t2.id)

        # Limpiar tag
        cleared = self.service.update_memory(mem.id, clear_tag=True)
        self.assertIsNone(cleared.tag_id)

    def test_get_timeline_filtered_by_tag(self):
        t1 = self.service.register_tag("Estudios", emoji="🎓")
        t2 = self.service.register_tag("Viajes", emoji="✈️")

        self.service.register_memory(year=2018, description="Primaria", tag_id=t1.id)
        self.service.register_memory(year=2019, description="Viaje a Bariloche", tag_id=t2.id)
        self.service.register_memory(year=2022, description="Secundaria", tag_id=t1.id)
        self.service.register_memory(year=2023, description="Sin tag")

        # Filtrar por tag 1 (Estudios)
        timeline_t1 = self.service.get_timeline(tag_id=t1.id)
        self.assertEqual(len(timeline_t1), 2)
        self.assertEqual(timeline_t1[0].memory.description, "Primaria")
        self.assertIsNotNone(timeline_t1[0].tag)
        self.assertEqual(timeline_t1[0].tag.name, "Estudios")
        self.assertEqual(timeline_t1[1].memory.description, "Secundaria")

        # Filtrar por tag 2 (Viajes)
        timeline_t2 = self.service.get_timeline(tag_id=t2.id)
        self.assertEqual(len(timeline_t2), 1)
        self.assertEqual(timeline_t2[0].memory.description, "Viaje a Bariloche")

    def test_delete_tag_cascade_unsets_memory_tag_id(self):
        t = self.service.register_tag("Hobbies", emoji="🎨")
        m = self.service.register_memory(year=2021, description="Pintura", tag_id=t.id)

        deleted = self.service.delete_tag(t.id)
        self.assertEqual(deleted.id, t.id)
        with self.assertRaises(NotFoundError):
            self.service.get_tag(t.id)

        reloaded_m = self.service.get_memory(m.id)
        self.assertIsNone(reloaded_m.tag_id)

    def test_person_crud(self):
        p1 = self.service.register_person("Ana Gómez", birth_year=1995, birth_month=4)
        p2 = self.service.register_person("Carlos Ruiz")

        self.assertEqual(p1.id, 1)
        self.assertEqual(p2.id, 2)

        persons = self.service.get_persons()
        self.assertEqual(len(persons), 2)
        self.assertEqual(persons[0].name, "Ana Gómez")
        self.assertEqual(persons[1].name, "Carlos Ruiz")

        retrieved = self.service.get_person(1)
        self.assertEqual(retrieved.name, "Ana Gómez")

        with self.assertRaises(NotFoundError):
            self.service.get_person(999)

    def test_person_validation(self):
        self.service.register_person("Martín Silva")
        with self.assertRaises(ValidationError):
            self.service.register_person("martín silva")
        with self.assertRaises(ValidationError):
            self.service.register_person("   ")

    def test_register_memory_with_persons(self):
        p1 = self.service.register_person("Juan Pérez", birth_year=1990, birth_month=5)
        p2 = self.service.register_person("María López", birth_year=1995, birth_month=10)

        mem = self.service.register_memory(
            year=2020,
            month=6,
            description="Viaje juntos",
            person_ids=[p1.id, p2.id],
        )
        self.assertEqual(mem.person_ids, [1, 2])

        # Persona inexistente
        with self.assertRaises(NotFoundError):
            self.service.register_memory(year=2020, description="Error", person_ids=[99])

    def test_get_timeline_person_age_calculation(self):
        # Juan: nacido en Mayo (5) de 1990
        p1 = self.service.register_person("Juan Pérez", birth_year=1990, birth_month=5)
        # María: sin fecha de nacimiento
        p2 = self.service.register_person("María López")

        # Evento en Abril (4) de 2020 (antes de su cumpleaños en mayo) -> Juan tiene 29 años
        mem1 = self.service.register_memory(
            year=2020,
            month=4,
            description="Concierto",
            person_ids=[p1.id, p2.id],
        )
        # Evento en Junio (6) de 2020 (después de su cumpleaños en mayo) -> Juan tiene 30 años
        mem2 = self.service.register_memory(
            year=2020,
            month=6,
            description="Fiesta",
            person_ids=[p1.id],
        )

        timeline = self.service.get_timeline(ascending=True)
        self.assertEqual(len(timeline), 2)

        # Primer recuerdo: Juan tiene 29, María tiene None
        entry1 = timeline[0]
        self.assertEqual(len(entry1.people), 2)
        self.assertEqual(entry1.people[0].person.name, "Juan Pérez")
        self.assertEqual(entry1.people[0].age, 29)
        self.assertEqual(entry1.people[1].person.name, "María López")
        self.assertIsNone(entry1.people[1].age)

        # Segundo recuerdo: Juan tiene 30
        entry2 = timeline[1]
        self.assertEqual(len(entry2.people), 1)
        self.assertEqual(entry2.people[0].person.name, "Juan Pérez")
        self.assertEqual(entry2.people[0].age, 30)

    def test_get_timeline_filtered_by_person(self):
        p1 = self.service.register_person("Persona 1")
        p2 = self.service.register_person("Persona 2")

        self.service.register_memory(year=2018, description="Solo con P1", person_ids=[p1.id])
        self.service.register_memory(year=2019, description="Con ambos", person_ids=[p1.id, p2.id])
        self.service.register_memory(year=2020, description="Solo con P2", person_ids=[p2.id])
        self.service.register_memory(year=2021, description="Sin personas")

        # Filtrar por p1
        t_p1 = self.service.get_timeline(person_id=p1.id)
        self.assertEqual(len(t_p1), 2)
        self.assertEqual(t_p1[0].memory.description, "Solo con P1")
        self.assertEqual(t_p1[1].memory.description, "Con ambos")

        # Filtrar por p2
        t_p2 = self.service.get_timeline(person_id=p2.id)
        self.assertEqual(len(t_p2), 2)
        self.assertEqual(t_p2[0].memory.description, "Con ambos")
        self.assertEqual(t_p2[1].memory.description, "Solo con P2")

    def test_update_memory_persons_and_clear_people(self):
        p1 = self.service.register_person("Persona 1")
        p2 = self.service.register_person("Persona 2")
        mem = self.service.register_memory(year=2024, description="Reunión", person_ids=[p1.id])

        # Actualizar personas
        updated = self.service.update_memory(mem.id, person_ids=[p2.id])
        self.assertEqual(updated.person_ids, [p2.id])

        # Limpiar personas
        cleared = self.service.update_memory(mem.id, clear_people=True)
        self.assertEqual(cleared.person_ids, [])

    def test_delete_person_cascade(self):
        p = self.service.register_person("Amigo")
        m = self.service.register_memory(year=2022, description="Salida", person_ids=[p.id])

        deleted = self.service.delete_person(p.id)
        self.assertEqual(deleted.id, p.id)
        with self.assertRaises(NotFoundError):
            self.service.get_person(p.id)

        reloaded = self.service.get_memory(m.id)
        self.assertEqual(reloaded.person_ids, [])

    def test_get_people_in_memory(self):
        p = self.service.register_person("Laura", birth_year=1990, birth_month=1)
        m = self.service.register_memory(year=2010, month=1, description="Evento", person_ids=[p.id])
        people = self.service.get_people_in_memory(m)
        self.assertEqual(len(people), 1)
        self.assertEqual(people[0].person.name, "Laura")
        self.assertEqual(people[0].age, 20)


if __name__ == "__main__":
    unittest.main()
