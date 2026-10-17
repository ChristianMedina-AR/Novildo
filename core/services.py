"""Casos de uso y lógica de negocio para Novildo.
No contiene dependencias de terminal ni UI.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from .models import Memory, UserProfile
from .storage import StorageRepository, JSONStorage
from .exceptions import ValidationError, NotFoundError, AmbiguousIdError


@dataclass
class TimelineEntry:
    """Entrada en la línea de tiempo que combina un recuerdo con la edad relativa calculada."""
    memory: Memory
    age: Optional[int]


class TimelineService:
    """Servicio que coordina la lógica de negocio de la línea de tiempo."""

    def __init__(self, repository: Optional[StorageRepository] = None) -> None:
        self.repository = repository if repository is not None else JSONStorage()

    @staticmethod
    def calculate_age(
        event_year: int,
        birth_year: Optional[int],
        event_month: Optional[int] = None,
        birth_month: Optional[int] = None,
    ) -> Optional[int]:
        """Calcula la edad según las reglas del negocio:
        - Si no hay birth_year configurado, retorna None.
        - Si están configurados el mes del evento y el mes de nacimiento,
          se calcula la edad exacta considerando si el cumpleaños ya ocurrió en ese año.
        - En caso contrario, retorna la estimación event_year - birth_year.
        """
        if birth_year is None:
            return None

        age = event_year - birth_year
        if birth_month is not None and event_month is not None:
            if event_month < birth_month:
                age -= 1
        return age

    def register_memory(self, year: int, description: str, month: Optional[int] = None) -> Memory:
        """Registra un nuevo recuerdo en el almacenamiento."""
        memory = Memory(year=year, month=month, description=description)
        return self.repository.add_memory(memory)

    def get_timeline(self, ascending: bool = True) -> List[TimelineEntry]:
        """Retorna todos los recuerdos ordenados cronológicamente con la edad calculada.
        
        Criterio de ordenamiento:
        1. Año (ascendente)
        2. Mes (ascendente; mes None se ubica al final del año: valor 13)
        3. Fecha de creación (para desempates deterministas)
        """
        memories = self.repository.get_memories()
        profile = self.repository.get_profile()

        # Clave de ordenamiento: (año, mes si existe o 13 para ir al final del año, timestamp de creación)
        sorted_memories = sorted(
            memories,
            key=lambda m: (m.year, m.month if m.month is not None else 13, m.created_at),
            reverse=not ascending
        )

        entries = [
            TimelineEntry(
                memory=m,
                age=self.calculate_age(
                    event_year=m.year,
                    birth_year=profile.birth_year,
                    event_month=m.month,
                    birth_month=profile.birth_month,
                )
            )
            for m in sorted_memories
        ]
        return entries

    def get_profile(self) -> UserProfile:
        """Obtiene el perfil actual del usuario."""
        return self.repository.get_profile()

    def update_profile(
        self,
        birth_year: Optional[int] = None,
        birth_month: Optional[int] = None,
        clear_birth_month: bool = False,
        clear_birth_year: bool = False,
    ) -> UserProfile:
        """Actualiza el año y/o mes de nacimiento del usuario."""
        current = self.repository.get_profile()

        new_year = current.birth_year
        new_month = current.birth_month

        if clear_birth_year:
            new_year = None
            new_month = None
        else:
            if birth_year is not None:
                new_year = birth_year

            if clear_birth_month:
                new_month = None
            elif birth_month is not None:
                new_month = birth_month

        profile = UserProfile(birth_year=new_year, birth_month=new_month)
        self.repository.save_profile(profile)
        return profile

    def update_birth_year(self, birth_year: Optional[int]) -> UserProfile:
        """Actualiza el año de nacimiento del usuario."""
        return self.update_profile(
            birth_year=birth_year,
            clear_birth_year=(birth_year is None),
        )

    def get_memory(self, memory_id: str) -> Memory:
        """Obtiene un recuerdo por su ID o prefijo único. Lanza NotFoundError si no existe."""
        memory = self.repository.get_memory_by_id(memory_id)
        if memory is None:
            raise NotFoundError(f"No se encontró ningún recuerdo con el ID '{memory_id}'.")
        return memory

    def update_memory(
        self,
        memory_id: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        description: Optional[str] = None,
        clear_month: bool = False,
    ) -> Memory:
        """Edita los campos especificados de un recuerdo existente."""
        memory = self.get_memory(memory_id)

        if year is None and month is None and description is None and not clear_month:
            raise ValidationError("No se proporcionó ningún cambio para actualizar el recuerdo. Usa -y, -m, -d o --clear-month.")

        if year is not None:
            memory.year = year

        if clear_month:
            memory.month = None
        elif month is not None:
            memory.month = month

        if description is not None:
            memory.description = description

        # Re-validar las reglas del modelo
        memory._validate()

        return self.repository.update_memory(memory)

    def delete_memory(self, memory_id: str) -> Memory:
        """Elimina un recuerdo existente por su ID o prefijo único y lo retorna."""
        memory = self.get_memory(memory_id)
        self.repository.delete_memory(memory.id)
        return memory

