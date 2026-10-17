"""Pruebas unitarias para los modelos del core (Memory, UserProfile).
"""

import unittest
from datetime import datetime, timezone
from core.models import Memory, UserProfile, Tag, Person
from core.exceptions import ValidationError


class TestMemoryModel(unittest.TestCase):
    def test_valid_memory(self):
        mem = Memory(year=2020, description="Nacimiento de mi sobrina", month=5)
        self.assertEqual(mem.year, 2020)
        self.assertEqual(mem.month, 5)
        self.assertEqual(mem.description, "Nacimiento de mi sobrina")
        self.assertIsInstance(mem.created_at, datetime)
        self.assertIsNotNone(mem.id)
        self.assertEqual(len(mem.id), 8)
        self.assertEqual(mem.person_ids, [])

    def test_memory_empty_id(self):
        with self.assertRaises(ValidationError):
            Memory(year=2020, description="Test", id="")
        with self.assertRaises(ValidationError):
            Memory(year=2020, description="Test", id="   ")

    def test_memory_optional_month(self):
        mem = Memory(year=1995, description="Primer viaje familiar")
        self.assertIsNone(mem.month)

    def test_memory_invalid_month(self):
        with self.assertRaises(ValidationError):
            Memory(year=2021, description="Mes inválido", month=13)
        with self.assertRaises(ValidationError):
            Memory(year=2021, description="Mes cero", month=0)
        with self.assertRaises(ValidationError):
            Memory(year=2021, description="Mes negativo", month=-1)

    def test_memory_empty_description(self):
        with self.assertRaises(ValidationError):
            Memory(year=2020, description="")
        with self.assertRaises(ValidationError):
            Memory(year=2020, description="   \n\t  ")

    def test_memory_invalid_year_type(self):
        with self.assertRaises(ValidationError):
            # Noinspection PyTypeChecker
            Memory(year="2020", description="Año string")  # type: ignore

    def test_memory_with_tag_id(self):
        mem = Memory(year=2024, description="Graduación", tag_id=1)
        self.assertEqual(mem.tag_id, 1)

    def test_memory_invalid_tag_id(self):
        with self.assertRaises(ValidationError):
            Memory(year=2024, description="Graduación", tag_id=0)
        with self.assertRaises(ValidationError):
            Memory(year=2024, description="Graduación", tag_id=-1)
        with self.assertRaises(ValidationError):
            Memory(year=2024, description="Graduación", tag_id="1")  # type: ignore

    def test_memory_with_person_ids(self):
        mem = Memory(year=2024, description="Cumpleaños", person_ids=[1, 2, 2, 3])
        self.assertEqual(mem.person_ids, [1, 2, 3])

    def test_memory_invalid_person_ids(self):
        with self.assertRaises(ValidationError):
            Memory(year=2024, description="Test", person_ids=[0])
        with self.assertRaises(ValidationError):
            Memory(year=2024, description="Test", person_ids=[-1])
        with self.assertRaises(ValidationError):
            Memory(year=2024, description="Test", person_ids=["1"])  # type: ignore
        with self.assertRaises(ValidationError):
            Memory(year=2024, description="Test", person_ids="not a list")  # type: ignore

    def test_serialization_roundtrip(self):
        original = Memory(year=2015, month=10, description="Graduación universitaria", tag_id=3, person_ids=[1, 2])
        data = original.to_dict()
        restored = Memory.from_dict(data)

        self.assertEqual(original.id, restored.id)
        self.assertEqual(original.year, restored.year)
        self.assertEqual(original.month, restored.month)
        self.assertEqual(original.description, restored.description)
        self.assertEqual(original.tag_id, restored.tag_id)
        self.assertEqual(original.person_ids, [1, 2])


class TestTagModel(unittest.TestCase):
    def test_valid_tag(self):
        tag = Tag(id=1, name="Estudios", emoji="🎓")
        self.assertEqual(tag.id, 1)
        self.assertEqual(tag.name, "Estudios")
        self.assertEqual(tag.emoji, "🎓")

    def test_tag_without_emoji(self):
        tag = Tag(id=2, name="Personal")
        self.assertEqual(tag.id, 2)
        self.assertEqual(tag.name, "Personal")
        self.assertIsNone(tag.emoji)

    def test_tag_invalid_id(self):
        with self.assertRaises(ValidationError):
            Tag(id=0, name="Inválido")
        with self.assertRaises(ValidationError):
            Tag(id=-1, name="Inválido")
        with self.assertRaises(ValidationError):
            Tag(id="1", name="Inválido")  # type: ignore

    def test_tag_empty_name(self):
        with self.assertRaises(ValidationError):
            Tag(id=1, name="")
        with self.assertRaises(ValidationError):
            Tag(id=1, name="   ")

    def test_tag_empty_emoji(self):
        with self.assertRaises(ValidationError):
            Tag(id=1, name="Test", emoji="")
        with self.assertRaises(ValidationError):
            Tag(id=1, name="Test", emoji="   ")

    def test_serialization_roundtrip(self):
        tag = Tag(id=5, name="Trabajo", emoji="💼")
        data = tag.to_dict()
        restored = Tag.from_dict(data)
        self.assertEqual(tag.id, restored.id)
        self.assertEqual(tag.name, restored.name)
        self.assertEqual(tag.emoji, restored.emoji)


class TestUserProfileModel(unittest.TestCase):
    def test_valid_profile_empty(self):
        profile = UserProfile()
        self.assertIsNone(profile.birth_year)

    def test_valid_profile_with_year(self):
        profile = UserProfile(birth_year=1990)
        self.assertEqual(profile.birth_year, 1990)

    def test_invalid_birth_year(self):
        with self.assertRaises(ValidationError):
            UserProfile(birth_year=-5)
        with self.assertRaises(ValidationError):
            UserProfile(birth_year=0)
        with self.assertRaises(ValidationError):
            UserProfile(birth_year="1990")  # type: ignore

    def test_valid_profile_with_year_and_month(self):
        profile = UserProfile(birth_year=1990, birth_month=5)
        self.assertEqual(profile.birth_year, 1990)
        self.assertEqual(profile.birth_month, 5)

    def test_invalid_birth_month(self):
        with self.assertRaises(ValidationError):
            UserProfile(birth_year=1990, birth_month=0)
        with self.assertRaises(ValidationError):
            UserProfile(birth_year=1990, birth_month=13)
        with self.assertRaises(ValidationError):
            UserProfile(birth_year=1990, birth_month=-1)
        with self.assertRaises(ValidationError):
            UserProfile(birth_year=1990, birth_month="5")  # type: ignore

    def test_serialization_roundtrip(self):
        profile = UserProfile(birth_year=1988, birth_month=10)
        data = profile.to_dict()
        restored = UserProfile.from_dict(data)
        self.assertEqual(profile.birth_year, restored.birth_year)
        self.assertEqual(profile.birth_month, restored.birth_month)


class TestPersonModel(unittest.TestCase):
    def test_valid_person(self):
        person = Person(id=1, name="Juan Pérez", birth_year=1990, birth_month=5)
        self.assertEqual(person.id, 1)
        self.assertEqual(person.name, "Juan Pérez")
        self.assertEqual(person.birth_year, 1990)
        self.assertEqual(person.birth_month, 5)

    def test_person_without_birth_date(self):
        person = Person(id=2, name="María López")
        self.assertEqual(person.id, 2)
        self.assertEqual(person.name, "María López")
        self.assertIsNone(person.birth_year)
        self.assertIsNone(person.birth_month)

    def test_person_invalid_id(self):
        with self.assertRaises(ValidationError):
            Person(id=0, name="Inválido")
        with self.assertRaises(ValidationError):
            Person(id=-1, name="Inválido")
        with self.assertRaises(ValidationError):
            Person(id="1", name="Inválido")  # type: ignore

    def test_person_empty_name(self):
        with self.assertRaises(ValidationError):
            Person(id=1, name="")
        with self.assertRaises(ValidationError):
            Person(id=1, name="   \t\n  ")

    def test_person_invalid_birth_year(self):
        with self.assertRaises(ValidationError):
            Person(id=1, name="Juan", birth_year=0)
        with self.assertRaises(ValidationError):
            Person(id=1, name="Juan", birth_year=-10)
        with self.assertRaises(ValidationError):
            Person(id=1, name="Juan", birth_year="1990")  # type: ignore

    def test_person_invalid_birth_month(self):
        with self.assertRaises(ValidationError):
            Person(id=1, name="Juan", birth_year=1990, birth_month=0)
        with self.assertRaises(ValidationError):
            Person(id=1, name="Juan", birth_year=1990, birth_month=13)
        with self.assertRaises(ValidationError):
            Person(id=1, name="Juan", birth_year=1990, birth_month="5")  # type: ignore

    def test_serialization_roundtrip(self):
        person = Person(id=3, name="Carlos Ruiz", birth_year=1985, birth_month=11)
        data = person.to_dict()
        restored = Person.from_dict(data)
        self.assertEqual(person.id, restored.id)
        self.assertEqual(person.name, restored.name)
        self.assertEqual(person.birth_year, restored.birth_year)
        self.assertEqual(person.birth_month, restored.birth_month)


if __name__ == "__main__":
    unittest.main()
