"""Pruebas unitarias para la capa de almacenamiento JSON.
"""

import unittest
from pathlib import Path
import tempfile
import shutil

from core.models import Memory, UserProfile
from core.storage import JSONStorage
from core.exceptions import StorageError


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


if __name__ == "__main__":
    unittest.main()
