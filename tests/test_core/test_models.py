"""Pruebas unitarias para los modelos del core (Memory, UserProfile).
"""

import unittest
from datetime import datetime, timezone
from core.models import Memory, UserProfile
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

    def test_serialization_roundtrip(self):
        original = Memory(year=2015, month=10, description="Graduación universitaria")
        data = original.to_dict()
        restored = Memory.from_dict(data)

        self.assertEqual(original.id, restored.id)
        self.assertEqual(original.year, restored.year)
        self.assertEqual(original.month, restored.month)
        self.assertEqual(original.description, restored.description)


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


if __name__ == "__main__":
    unittest.main()
