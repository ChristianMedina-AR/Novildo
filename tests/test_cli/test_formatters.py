"""Pruebas unitarias para los formateadores de la CLI.
"""

import unittest
from core.models import Memory, UserProfile, Tag, Person
from core.services import TimelineEntry, PersonInEvent
from interfaces.cli.formatters import (
    format_month,
    format_timeline,
    format_memory_added,
    format_memory_updated,
    format_memory_deleted,
    format_tags,
    format_tag_added,
    format_tag_deleted,
    format_persons,
    format_person_added,
    format_person_deleted,
    format_profile,
    format_profile_updated,
    format_version,
    format_help_guide,
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

    def test_format_empty_timeline_with_year_filter(self):
        output = format_timeline([], year=1999)
        self.assertEqual(output, "No hay recuerdos registrados para el año 1999.")

    def test_format_empty_timeline_with_tag_filter(self):
        tag = Tag(id=1, name="Estudios", emoji="🎓")
        output = format_timeline([], tag=tag)
        self.assertIn("No hay recuerdos registrados con la etiqueta '🎓 Estudios' (ID 1).", output)

        output_id_only = format_timeline([], tag_id=2)
        self.assertIn("No hay recuerdos registrados con la etiqueta ID 2.", output_id_only)

    def test_format_timeline_with_entries(self):
        tag1 = Tag(id=1, name="Estudios", emoji="🎓")
        m1 = Memory(year=2000, month=3, description="Nacimiento", tag_id=1)
        m2 = Memory(year=2020, month=None, description="Pandemia")
        entries = [
            TimelineEntry(memory=m1, age=0, tag=tag1),
            TimelineEntry(memory=m2, age=20, tag=None),
        ]
        output = format_timeline(entries)
        self.assertIn("ID", output)
        self.assertIn("Año", output)
        self.assertIn("Mes", output)
        self.assertIn("Edad", output)
        self.assertIn("Etiqueta", output)
        self.assertIn("Descripción", output)
        self.assertIn(m1.id, output)
        self.assertIn(m2.id, output)
        self.assertIn("2000", output)
        self.assertIn("Marzo", output)
        self.assertIn("0 años", output)
        self.assertIn("🎓 Estudios", output)
        self.assertIn("Pandemia", output)

    def test_format_memory_added(self):
        mem = Memory(year=2024, month=1, description="Comienzo de nuevo proyecto")
        output = format_memory_added(mem)
        self.assertIn("  - Año: 2024\n  - Mes: Enero\n  - Descripción: Comienzo de nuevo proyecto", output)

    def test_format_memory_added_with_tag(self):
        tag = Tag(id=1, name="Estudios", emoji="🎓")
        mem = Memory(year=2024, month=1, description="Comienzo de carrera", tag_id=1)
        output = format_memory_added(mem, tag=tag)
        self.assertIn("  - Etiqueta: 🎓 Estudios (ID: 1)", output)

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

    def test_format_memory_updated_with_tag(self):
        tag = Tag(id=2, name="Trabajo", emoji="💼")
        mem = Memory(year=2024, month=2, description="Ascenso", id="11223344", tag_id=2)
        output = format_memory_updated(mem, tag=tag)
        self.assertIn("  - Etiqueta: 💼 Trabajo (ID: 2)", output)

    def test_format_memory_deleted(self):
        mem = Memory(year=2024, month=None, description="Borrado", id="55667788")
        output = format_memory_deleted(mem)
        self.assertIn("✓ Recuerdo eliminado con éxito:", output)
        self.assertIn("  - ID: 55667788", output)
        self.assertIn("  - Descripción: Borrado", output)
        self.assertNotIn("Mes:", output)

    def test_format_tags(self):
        empty_out = format_tags([])
        self.assertIn("No hay etiquetas registradas aún", empty_out)

        t1 = Tag(id=1, name="Estudios", emoji="🎓")
        t2 = Tag(id=2, name="Familia")
        tags_out = format_tags([t1, t2])
        self.assertIn("ID", tags_out)
        self.assertIn("Emote", tags_out)
        self.assertIn("Nombre", tags_out)
        self.assertIn("🎓", tags_out)
        self.assertIn("Estudios", tags_out)
        self.assertIn("Familia", tags_out)

    def test_format_tag_added_and_deleted(self):
        t = Tag(id=1, name="Estudios", emoji="🎓")
        added_out = format_tag_added(t)
        self.assertIn("✓ Etiqueta creada con éxito:", added_out)
        self.assertIn("ID: 1", added_out)
        self.assertIn("Nombre: Estudios", added_out)
        self.assertIn("Emote: 🎓", added_out)

        deleted_out = format_tag_deleted(t)
        self.assertIn("✓ Etiqueta eliminada con éxito:", deleted_out)
        self.assertIn("ID: 1", deleted_out)

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

    def test_format_empty_timeline_with_person_filter(self):
        person = Person(id=1, name="Juan Pérez")
        output = format_timeline([], person=person)
        self.assertIn("No hay recuerdos registrados con la persona 'Juan Pérez' (ID 1).", output)

        output_id_only = format_timeline([], person_id=2)
        self.assertIn("No hay recuerdos registrados con la persona ID 2.", output_id_only)

        output_year_person = format_timeline([], year=2020, person_id=1)
        self.assertIn("No hay recuerdos registrados para el año 2020 con la persona ID 1.", output_year_person)

    def test_format_timeline_with_people(self):
        p1 = Person(id=1, name="Juan", birth_year=1990)
        p2 = Person(id=2, name="María")
        m = Memory(year=2020, description="Viaje", person_ids=[1, 2])
        entry = TimelineEntry(
            memory=m,
            age=25,
            tag=None,
            people=[PersonInEvent(person=p1, age=30), PersonInEvent(person=p2, age=None)],
        )
        output = format_timeline([entry])
        self.assertIn("Personas", output)
        self.assertIn("Juan (30 años), María", output)

    def test_format_memory_added_and_updated_with_people(self):
        p = Person(id=1, name="Laura", birth_year=2000)
        people = [PersonInEvent(person=p, age=24)]
        mem = Memory(year=2024, description="Cumpleaños", person_ids=[1])

        out_add = format_memory_added(mem, people=people)
        self.assertIn("  - Personas: Laura (24 años)", out_add)

        out_upd = format_memory_updated(mem, people=people)
        self.assertIn("  - Personas: Laura (24 años)", out_upd)

    def test_format_persons(self):
        empty_out = format_persons([])
        self.assertIn("No hay personas registradas aún en Novildo", empty_out)

        p1 = Person(id=1, name="Carlos Gómez", birth_year=1990, birth_month=5)
        p2 = Person(id=2, name="Lucía Solís", birth_year=1995)
        p3 = Person(id=3, name="Marcos Ruiz")

        output = format_persons([p1, p2, p3])
        self.assertIn("ID", output)
        self.assertIn("Nombre", output)
        self.assertIn("Fecha de nacimiento", output)
        self.assertIn("Carlos Gómez", output)
        self.assertIn("Mayo de 1990", output)
        self.assertIn("Lucía Solís", output)
        self.assertIn("1995", output)
        self.assertIn("Marcos Ruiz", output)

    def test_format_person_added_and_deleted(self):
        p = Person(id=1, name="Juan Pérez", birth_year=1990, birth_month=5)
        added_out = format_person_added(p)
        self.assertIn("✓ Persona registrada con éxito:", added_out)
        self.assertIn("  - ID: 1", added_out)
        self.assertIn("  - Nombre: Juan Pérez", added_out)
        self.assertIn("  - Fecha de nacimiento: Mayo de 1990", added_out)

        deleted_out = format_person_deleted(p)
        self.assertIn("✓ Persona eliminada con éxito:", deleted_out)
        self.assertIn("  - ID: 1", deleted_out)
        self.assertIn("  - Nombre: Juan Pérez", deleted_out)

    def test_format_version(self):
        output = format_version("0.2.0")
        self.assertEqual(output, "Novildo v0.2.0")

    def test_format_help_guide(self):
        output = format_help_guide("0.2.0")
        self.assertIn("Novildo - Línea de tiempo y memoria personal", output)
        self.assertIn("-y, --year", output)
        self.assertIn("-m, --month", output)
        self.assertIn("-d, --description", output)
        self.assertIn("-t, --tag", output)
        self.assertIn("tag (alias: t)", output)
        self.assertIn("-p, --person, --people", output)
        self.assertIn("person (alias: p)", output)
        self.assertIn("-v, --version", output)
        self.assertIn("help", output)


if __name__ == "__main__":
    unittest.main()
