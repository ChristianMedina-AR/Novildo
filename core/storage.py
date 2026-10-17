"""Capa de persistencia desacoplada para Novildo.
Permite almacenar recuerdos y el perfil de usuario sin acoplarse a ninguna interfaz.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Union, List

from .models import Memory, UserProfile, Tag, Person
from .exceptions import StorageError, NotFoundError, AmbiguousIdError


class StorageRepository(ABC):
    """Interfaz base para repositorios de persistencia en Novildo."""

    @abstractmethod
    def get_memories(self) -> List[Memory]:
        """Obtiene todos los recuerdos almacenados."""
        pass

    @abstractmethod
    def get_memory_by_id(self, memory_id: str) -> Optional[Memory]:
        """Obtiene un recuerdo por su ID o prefijo único."""
        pass

    @abstractmethod
    def add_memory(self, memory: Memory) -> Memory:
        """Guarda un nuevo recuerdo y lo retorna."""
        pass

    @abstractmethod
    def update_memory(self, memory: Memory) -> Memory:
        """Actualiza un recuerdo existente en el repositorio."""
        pass

    @abstractmethod
    def delete_memory(self, memory_id: str) -> bool:
        """Elimina un recuerdo existente por su ID."""
        pass

    @abstractmethod
    def get_profile(self) -> UserProfile:
        """Obtiene el perfil del usuario."""
        pass

    @abstractmethod
    def save_profile(self, profile: UserProfile) -> None:
        """Guarda o actualiza el perfil del usuario."""
        pass

    @abstractmethod
    def get_tags(self) -> List[Tag]:
        """Obtiene todas las etiquetas almacenadas."""
        pass

    @abstractmethod
    def get_tag_by_id(self, tag_id: int) -> Optional[Tag]:
        """Obtiene una etiqueta por su ID numérico."""
        pass

    @abstractmethod
    def add_tag(self, tag: Tag) -> Tag:
        """Guarda una nueva etiqueta y la retorna."""
        pass

    @abstractmethod
    def delete_tag(self, tag_id: int) -> bool:
        """Elimina una etiqueta por su ID numérico."""
        pass

    @abstractmethod
    def get_persons(self) -> List[Person]:
        """Obtiene todas las personas almacenadas."""
        pass

    @abstractmethod
    def get_person_by_id(self, person_id: int) -> Optional[Person]:
        """Obtiene una persona por su ID numérico."""
        pass

    @abstractmethod
    def add_person(self, person: Person) -> Person:
        """Guarda una nueva persona y la retorna."""
        pass

    @abstractmethod
    def delete_person(self, person_id: int) -> bool:
        """Elimina una persona por su ID numérico."""
        pass


def find_matching_memory(memories: List[Memory], memory_id: str) -> Optional[Memory]:
    """Busca un recuerdo por su ID exacto o por coincidencia de prefijo único."""
    target = memory_id.strip()
    if not target:
        return None

    # 1. Coincidencia exacta
    for m in memories:
        if m.id == target:
            return m

    # 2. Coincidencia exacta insensible a mayúsculas
    for m in memories:
        if m.id.lower() == target.lower():
            return m

    # 3. Coincidencia por prefijo único
    matches = [m for m in memories if m.id.lower().startswith(target.lower())]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        matched_ids = ", ".join(m.id for m in matches)
        raise AmbiguousIdError(f"El ID '{target}' es ambiguo: coincide con varios recuerdos ({matched_ids}).")

    return None


class JSONStorage(StorageRepository):
    """Implementación de almacenamiento persistente en archivo JSON."""

    def __init__(self, filepath: Union[str, Path] = "novildo_data.json") -> None:
        self.filepath = Path(filepath)

    def _ensure_file(self) -> None:
        """Crea el archivo con estructura vacía si no existe."""
        if not self.filepath.exists():
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            initial_data = {
                "profile": UserProfile().to_dict(),
                "memories": [],
                "tags": [],
                "persons": [],
            }
            self._write_raw(initial_data)

    def _read_raw(self) -> dict:
        """Lee el contenido JSON del archivo."""
        self._ensure_file()
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise StorageError(f"Error al leer el archivo de datos {self.filepath}: {e}") from e

    def _write_raw(self, data: dict) -> None:
        """Escribe datos atómicamente en el archivo JSON."""
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            # Escritura atómica mediante archivo temporal en el mismo directorio
            temp_dir = self.filepath.parent if self.filepath.parent.name else Path(".")
            with NamedTemporaryFile("w", dir=temp_dir, delete=False, encoding="utf-8") as tf:
                json.dump(data, tf, indent=2, ensure_ascii=False)
                temp_name = tf.name
            os.replace(temp_name, self.filepath)
        except OSError as e:
            raise StorageError(f"Error al escribir en el archivo de datos {self.filepath}: {e}") from e

    def get_memories(self) -> List[Memory]:
        data = self._read_raw()
        raw_memories = data.get("memories", [])
        return [Memory.from_dict(m) for m in raw_memories]

    def get_memory_by_id(self, memory_id: str) -> Optional[Memory]:
        memories = self.get_memories()
        return find_matching_memory(memories, memory_id)

    def add_memory(self, memory: Memory) -> Memory:
        data = self._read_raw()
        if "memories" not in data or not isinstance(data["memories"], list):
            data["memories"] = []
        data["memories"].append(memory.to_dict())
        self._write_raw(data)
        return memory

    def update_memory(self, memory: Memory) -> Memory:
        data = self._read_raw()
        raw_memories = data.get("memories", [])
        found_idx = None
        for idx, m_dict in enumerate(raw_memories):
            if m_dict.get("id") == memory.id:
                found_idx = idx
                break

        if found_idx is None:
            raise NotFoundError(f"No se encontró ningún recuerdo con ID '{memory.id}'.")

        raw_memories[found_idx] = memory.to_dict()
        data["memories"] = raw_memories
        self._write_raw(data)
        return memory

    def delete_memory(self, memory_id: str) -> bool:
        data = self._read_raw()
        raw_memories = data.get("memories", [])
        target_memory = self.get_memory_by_id(memory_id)
        if target_memory is None:
            raise NotFoundError(f"No se encontró ningún recuerdo con ID '{memory_id}'.")

        data["memories"] = [m for m in raw_memories if m.get("id") != target_memory.id]
        self._write_raw(data)
        return True

    def get_profile(self) -> UserProfile:
        data = self._read_raw()
        profile_data = data.get("profile", {})
        return UserProfile.from_dict(profile_data)

    def save_profile(self, profile: UserProfile) -> None:
        data = self._read_raw()
        data["profile"] = profile.to_dict()
        self._write_raw(data)

    def get_tags(self) -> List[Tag]:
        data = self._read_raw()
        raw_tags = data.get("tags", [])
        return [Tag.from_dict(t) for t in raw_tags]

    def get_tag_by_id(self, tag_id: int) -> Optional[Tag]:
        tags = self.get_tags()
        for t in tags:
            if t.id == tag_id:
                return t
        return None

    def add_tag(self, tag: Tag) -> Tag:
        data = self._read_raw()
        if "tags" not in data or not isinstance(data["tags"], list):
            data["tags"] = []
        data["tags"].append(tag.to_dict())
        self._write_raw(data)
        return tag

    def delete_tag(self, tag_id: int) -> bool:
        data = self._read_raw()
        raw_tags = data.get("tags", [])
        target_tag = self.get_tag_by_id(tag_id)
        if target_tag is None:
            raise NotFoundError(f"No se encontró ninguna etiqueta con ID {tag_id}.")

        data["tags"] = [t for t in raw_tags if t.get("id") != target_tag.id]

        # Desasociar la etiqueta de los recuerdos que la contenían
        raw_memories = data.get("memories", [])
        for m in raw_memories:
            if m.get("tag_id") == target_tag.id:
                m["tag_id"] = None
        data["memories"] = raw_memories

        self._write_raw(data)
        return True

    def get_persons(self) -> List[Person]:
        data = self._read_raw()
        raw_persons = data.get("persons", [])
        return [Person.from_dict(p) for p in raw_persons]

    def get_person_by_id(self, person_id: int) -> Optional[Person]:
        persons = self.get_persons()
        for p in persons:
            if p.id == person_id:
                return p
        return None

    def add_person(self, person: Person) -> Person:
        data = self._read_raw()
        if "persons" not in data or not isinstance(data["persons"], list):
            data["persons"] = []
        data["persons"].append(person.to_dict())
        self._write_raw(data)
        return person

    def delete_person(self, person_id: int) -> bool:
        data = self._read_raw()
        raw_persons = data.get("persons", [])
        target_person = self.get_person_by_id(person_id)
        if target_person is None:
            raise NotFoundError(f"No se encontró ninguna persona con ID {person_id}.")

        data["persons"] = [p for p in raw_persons if p.get("id") != target_person.id]

        # Desvincular a la persona de todos los recuerdos que la contenían
        raw_memories = data.get("memories", [])
        for m in raw_memories:
            if "person_ids" in m and isinstance(m["person_ids"], list):
                m["person_ids"] = [pid for pid in m["person_ids"] if pid != target_person.id]
        data["memories"] = raw_memories

        self._write_raw(data)
        return True


class InMemoryStorage(StorageRepository):
    """Almacenamiento en memoria volátil, ideal para pruebas unitarias."""

    def __init__(
        self,
        profile: UserProfile | None = None,
        memories: List[Memory] | None = None,
        tags: List[Tag] | None = None,
        persons: List[Person] | None = None,
    ) -> None:
        self._profile = profile or UserProfile()
        self._memories: List[Memory] = list(memories) if memories else []
        self._tags: List[Tag] = list(tags) if tags else []
        self._persons: List[Person] = list(persons) if persons else []

    def get_memories(self) -> List[Memory]:
        return list(self._memories)

    def get_memory_by_id(self, memory_id: str) -> Optional[Memory]:
        return find_matching_memory(self._memories, memory_id)

    def add_memory(self, memory: Memory) -> Memory:
        self._memories.append(memory)
        return memory

    def update_memory(self, memory: Memory) -> Memory:
        for idx, m in enumerate(self._memories):
            if m.id == memory.id:
                self._memories[idx] = memory
                return memory
        raise NotFoundError(f"No se encontró ningún recuerdo con ID '{memory.id}'.")

    def delete_memory(self, memory_id: str) -> bool:
        target = self.get_memory_by_id(memory_id)
        if target is None:
            raise NotFoundError(f"No se encontró ningún recuerdo con ID '{memory_id}'.")
        self._memories = [m for m in self._memories if m.id != target.id]
        return True

    def get_profile(self) -> UserProfile:
        return self._profile

    def save_profile(self, profile: UserProfile) -> None:
        self._profile = profile

    def get_tags(self) -> List[Tag]:
        return list(self._tags)

    def get_tag_by_id(self, tag_id: int) -> Optional[Tag]:
        for t in self._tags:
            if t.id == tag_id:
                return t
        return None

    def add_tag(self, tag: Tag) -> Tag:
        self._tags.append(tag)
        return tag

    def delete_tag(self, tag_id: int) -> bool:
        target = self.get_tag_by_id(tag_id)
        if target is None:
            raise NotFoundError(f"No se encontró ninguna etiqueta con ID {tag_id}.")
        self._tags = [t for t in self._tags if t.id != target.id]
        for m in self._memories:
            if m.tag_id == target.id:
                m.tag_id = None
        return True

    def get_persons(self) -> List[Person]:
        return list(self._persons)

    def get_person_by_id(self, person_id: int) -> Optional[Person]:
        for p in self._persons:
            if p.id == person_id:
                return p
        return None

    def add_person(self, person: Person) -> Person:
        self._persons.append(person)
        return person

    def delete_person(self, person_id: int) -> bool:
        target = self.get_person_by_id(person_id)
        if target is None:
            raise NotFoundError(f"No se encontró ninguna persona con ID {person_id}.")
        self._persons = [p for p in self._persons if p.id != target.id]
        for m in self._memories:
            if target.id in m.person_ids:
                m.person_ids = [pid for pid in m.person_ids if pid != target.id]
        return True

