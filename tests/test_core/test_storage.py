"""Pruebas unitarias para la capa de almacenamiento JSON.
"""

import unittest
from pathlib import Path
import tempfile
import shutil

from core.models import Memory, UserProfile, Tag, Person
from core.storage import JSONStorage, InMemoryStorage
from core.exceptions import StorageError, NotFoundError
import json


class TestJSONStorage(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.file_path = Path(self.test_dir) / "test_data.json"
        self.storage = JSONStorage(filepath=self.file_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_auto_initialization(self):
        self.assertFalse(self.file_path.exists())
        memories = self.storage.get_memories()
        self.assertEqual(memories, [])
        tags = self.storage.get_tags()
        self.assertEqual(tags, [])
        persons = self.storage.get_persons()
        self.assertEqual(persons, [])
        self.assertTrue(self.file_path.exists())

        profile = self.storage.get_profile()
        self.assertIsNone(profile.birth_year)

    def test_save_and_retrieve_memories(self):
        mem1 = Memory(year=2010, month=4, description="Primera memoria")
        mem2 = Memory(year=2012, month=None, description="Segunda memoria")

        self.storage.add_memory(mem1)
        self.storage.add_memory(mem2)

        retrieved = self.storage.get_memories()
        self.assertEqual(len(retrieved), 2)
        self.assertEqual(retrieved[0].description, "Primera memoria")
        self.assertEqual(retrieved[1].description, "Segunda memoria")

    def test_save_and_retrieve_profile(self):
        profile = UserProfile(birth_year=1985)
        self.storage.save_profile(profile)

        retrieved = self.storage.get_profile()
        self.assertEqual(retrieved.birth_year, 1985)

    def test_invalid_json_handling(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("corrupted json content {{{")

        with self.assertRaises(StorageError):
            self.storage.get_memories()

    def test_get_memory_by_id_and_prefix(self):
        m1 = Memory(year=2010, description="Test 1", id="abcd1111")
        m2 = Memory(year=2015, description="Test 2", id="abce2222")
        self.storage.add_memory(m1)
        self.storage.add_memory(m2)

        # Coincidencia exacta
        self.assertEqual(self.storage.get_memory_by_id("abcd1111").description, "Test 1")
        # Coincidencia por prefijo único
        self.assertEqual(self.storage.get_memory_by_id("abcd").description, "Test 1")
        self.assertEqual(self.storage.get_memory_by_id("abce").description, "Test 2")
        # Inexistente
        self.assertIsNone(self.storage.get_memory_by_id("xyz"))

    def test_update_and_delete_memory(self):
        m = Memory(year=2010, description="Original", id="12345678")
        self.storage.add_memory(m)

        m.description = "Actualizada"
        self.storage.update_memory(m)
        self.assertEqual(self.storage.get_memory_by_id("12345678").description, "Actualizada")

        # Eliminar
        self.assertTrue(self.storage.delete_memory("12345678"))
        self.assertIsNone(self.storage.get_memory_by_id("12345678"))

    def test_tag_storage_operations_and_cascade(self):
        tag1 = Tag(id=1, name="Estudios", emoji="🎓")
        tag2 = Tag(id=2, name="Trabajo", emoji="💼")
        self.storage.add_tag(tag1)
        self.storage.add_tag(tag2)

        tags = self.storage.get_tags()
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0].name, "Estudios")
        self.assertEqual(tags[1].emoji, "💼")

        self.assertEqual(self.storage.get_tag_by_id(1).name, "Estudios")
        self.assertIsNone(self.storage.get_tag_by_id(99))

        # Agregar recuerdo con tag_id=1
        m = Memory(year=2024, description="Graduación", tag_id=1)
        self.storage.add_memory(m)

        # Eliminar tag 1 -> debe eliminarse y el recuerdo debe quedar con tag_id=None
        self.assertTrue(self.storage.delete_tag(1))
        self.assertIsNone(self.storage.get_tag_by_id(1))
        self.assertEqual(len(self.storage.get_tags()), 1)

        updated_m = self.storage.get_memory_by_id(m.id)
        self.assertIsNone(updated_m.tag_id)

    def test_person_storage_operations_and_cascade(self):
        p1 = Person(id=1, name="Ana Gómez", birth_year=1992, birth_month=3)
        p2 = Person(id=2, name="Carlos Ruiz")
        self.storage.add_person(p1)
        self.storage.add_person(p2)

        persons = self.storage.get_persons()
        self.assertEqual(len(persons), 2)
        self.assertEqual(persons[0].name, "Ana Gómez")
        self.assertEqual(persons[1].name, "Carlos Ruiz")

        self.assertEqual(self.storage.get_person_by_id(1).name, "Ana Gómez")
        self.assertIsNone(self.storage.get_person_by_id(99))

        m = Memory(year=2024, description="Viaje grupal", person_ids=[1, 2])
        self.storage.add_memory(m)

        # Eliminar persona 1 -> m debe conservar solo persona 2
        self.assertTrue(self.storage.delete_person(1))
        self.assertIsNone(self.storage.get_person_by_id(1))
        self.assertEqual(len(self.storage.get_persons()), 1)

        updated_m = self.storage.get_memory_by_id(m.id)
        self.assertEqual(updated_m.person_ids, [2])

    def test_backward_compatibility_without_persons(self):
        old_data = {
            "profile": {"birth_year": 1990, "birth_month": 5},
            "memories": [
                {
                    "id": "old12345",
                    "year": 2020,
                    "month": 4,
                    "description": "Recuerdo antiguo",
                    "created_at": "2020-04-01T10:00:00+00:00"
                }
            ],
            "tags": []
        }
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(old_data, f)

        # Debe cargar correctamente sin fallar
        memories = self.storage.get_memories()
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0].person_ids, [])
        persons = self.storage.get_persons()
        self.assertEqual(persons, [])


class TestInMemoryStorage(unittest.TestCase):
    def test_in_memory_tag_operations(self):
        storage = InMemoryStorage()
        tag = Tag(id=1, name="Viajes", emoji="✈️")
        storage.add_tag(tag)

        self.assertEqual(len(storage.get_tags()), 1)
        self.assertEqual(storage.get_tag_by_id(1).emoji, "✈️")

        m = Memory(year=2023, description="Viaje a Japón", tag_id=1)
        storage.add_memory(m)

        storage.delete_tag(1)
        self.assertEqual(len(storage.get_tags()), 0)
        self.assertIsNone(storage.get_memory_by_id(m.id).tag_id)

    def test_in_memory_person_operations(self):
        storage = InMemoryStorage()
        person = Person(id=1, name="Lucía Solís", birth_year=2000)
        storage.add_person(person)

        self.assertEqual(len(storage.get_persons()), 1)
        self.assertEqual(storage.get_person_by_id(1).name, "Lucía Solís")

        m = Memory(year=2023, description="Recuerdo", person_ids=[1])
        storage.add_memory(m)

        storage.delete_person(1)
        self.assertEqual(len(storage.get_persons()), 0)
        self.assertEqual(storage.get_memory_by_id(m.id).person_ids, [])


if __name__ == "__main__":
    unittest.main()
