"""Modelos de datos del dominio de Novildo.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any
import uuid

from .exceptions import ValidationError


@dataclass
class Memory:
    """Representa un hito o recuerdo en la línea de tiempo."""
    year: int
    description: str
    month: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    tag_id: Optional[int] = None
    person_ids: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValidationError("El ID del recuerdo no puede estar vacío.")

        if not isinstance(self.year, int):
            raise ValidationError(f"El año debe ser un número entero, se recibió: {type(self.year).__name__}")
        
        if self.month is not None:
            if not isinstance(self.month, int) or self.month < 1 or self.month > 12:
                raise ValidationError(f"El mes debe ser un entero entre 1 y 12 o None, se recibió: {self.month}")

        if not isinstance(self.description, str) or not self.description.strip():
            raise ValidationError("La descripción del recuerdo no puede estar vacía.")

        if self.tag_id is not None:
            if not isinstance(self.tag_id, int) or self.tag_id < 1:
                raise ValidationError(f"El ID de etiqueta asociado debe ser un entero mayor o igual a 1, se recibió: {self.tag_id}")

        if not isinstance(self.person_ids, list):
            raise ValidationError("person_ids debe ser una lista de IDs de personas.")
        for pid in self.person_ids:
            if not isinstance(pid, int) or pid < 1:
                raise ValidationError(f"Cada ID de persona debe ser un entero mayor o igual a 1, se recibió: {pid}")

        # Evitar duplicados preservando el orden
        self.person_ids = list(dict.fromkeys(self.person_ids))

        if isinstance(self.created_at, str):
            try:
                self.created_at = datetime.fromisoformat(self.created_at)
            except ValueError as e:
                raise ValidationError(f"Formato inválido de created_at: {e}") from e

    def to_dict(self) -> dict[str, Any]:
        """Serializa la memoria a un diccionario compatible con JSON."""
        return {
            "id": self.id,
            "year": self.year,
            "month": self.month,
            "description": self.description.strip(),
            "created_at": self.created_at.isoformat(),
            "tag_id": self.tag_id,
            "person_ids": self.person_ids,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Memory:
        """Crea una instancia de Memory a partir de un diccionario."""
        try:
            raw_id = data.get("id")
            if raw_id is None or not str(raw_id).strip():
                clean_id = uuid.uuid4().hex[:8]
            else:
                clean_id = str(raw_id).strip()

            tag_id = data.get("tag_id")
            clean_tag_id = int(tag_id) if tag_id is not None else None

            raw_person_ids = data.get("person_ids", [])
            clean_person_ids = [int(p) for p in raw_person_ids] if isinstance(raw_person_ids, list) else []

            return cls(
                id=clean_id,
                year=int(data["year"]),
                month=int(data["month"]) if data.get("month") is not None else None,
                description=str(data["description"]),
                created_at=data.get("created_at", datetime.now(timezone.utc)),
                tag_id=clean_tag_id,
                person_ids=clean_person_ids,
            )
        except (KeyError, TypeError, ValueError) as err:
            raise ValidationError(f"Error al deserializar Memory: {err}") from err


@dataclass
class UserProfile:
    """Perfil del usuario para contextualizar la línea de tiempo."""
    birth_year: Optional[int] = None
    birth_month: Optional[int] = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if self.birth_year is not None:
            if not isinstance(self.birth_year, int):
                raise ValidationError(f"El año de nacimiento debe ser un entero, se recibió: {type(self.birth_year).__name__}")
            if self.birth_year < 1 or self.birth_year > 9999:
                raise ValidationError(f"El año de nacimiento ({self.birth_year}) está fuera del rango válido (1-9999).")

        if self.birth_month is not None:
            if not isinstance(self.birth_month, int) or self.birth_month < 1 or self.birth_month > 12:
                raise ValidationError(f"El mes de nacimiento debe ser un entero entre 1 y 12 o None, se recibió: {self.birth_month}")

    def to_dict(self) -> dict[str, Any]:
        """Serializa el perfil a un diccionario."""
        return {
            "birth_year": self.birth_year,
            "birth_month": self.birth_month,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserProfile:
        """Crea una instancia de UserProfile a partir de un diccionario."""
        birth_year = data.get("birth_year")
        birth_month = data.get("birth_month")
        return cls(
            birth_year=int(birth_year) if birth_year is not None else None,
            birth_month=int(birth_month) if birth_month is not None else None,
        )


@dataclass
class Tag:
    """Representa una etiqueta temática para clasificar recuerdos."""
    id: int
    name: str
    emoji: Optional[str] = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not isinstance(self.id, int) or self.id < 1:
            raise ValidationError(f"El ID de la etiqueta debe ser un número entero mayor o igual a 1, se recibió: {self.id}")

        if not isinstance(self.name, str) or not self.name.strip():
            raise ValidationError("El nombre de la etiqueta no puede estar vacío.")

        self.name = self.name.strip()

        if self.emoji is not None:
            if not isinstance(self.emoji, str) or not self.emoji.strip():
                raise ValidationError("El emote/emoji de la etiqueta no puede ser una cadena vacía.")
            self.emoji = self.emoji.strip()

    def to_dict(self) -> dict[str, Any]:
        """Serializa la etiqueta a un diccionario compatible con JSON."""
        return {
            "id": self.id,
            "name": self.name,
            "emoji": self.emoji,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Tag:
        """Crea una instancia de Tag a partir de un diccionario."""
        try:
            return cls(
                id=int(data["id"]),
                name=str(data["name"]),
                emoji=str(data["emoji"]) if data.get("emoji") is not None else None,
            )
        except (KeyError, TypeError, ValueError) as err:
            raise ValidationError(f"Error al deserializar Tag: {err}") from err


@dataclass
class Person:
    """Representa a una persona (amigo, familiar, etc.) para vincular a recuerdos."""
    id: int
    name: str
    birth_year: Optional[int] = None
    birth_month: Optional[int] = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not isinstance(self.id, int) or self.id < 1:
            raise ValidationError(f"El ID de la persona debe ser un número entero mayor o igual a 1, se recibió: {self.id}")

        if not isinstance(self.name, str) or not self.name.strip():
            raise ValidationError("El nombre de la persona no puede estar vacío.")

        self.name = self.name.strip()

        if self.birth_year is not None:
            if not isinstance(self.birth_year, int):
                raise ValidationError(f"El año de nacimiento debe ser un entero, se recibió: {type(self.birth_year).__name__}")
            if self.birth_year < 1 or self.birth_year > 9999:
                raise ValidationError(f"El año de nacimiento ({self.birth_year}) está fuera del rango válido (1-9999).")

        if self.birth_month is not None:
            if not isinstance(self.birth_month, int) or self.birth_month < 1 or self.birth_month > 12:
                raise ValidationError(f"El mes de nacimiento debe ser un entero entre 1 y 12 o None, se recibió: {self.birth_month}")

    def to_dict(self) -> dict[str, Any]:
        """Serializa la persona a un diccionario compatible con JSON."""
        return {
            "id": self.id,
            "name": self.name,
            "birth_year": self.birth_year,
            "birth_month": self.birth_month,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Person:
        """Crea una instancia de Person a partir de un diccionario."""
        try:
            return cls(
                id=int(data["id"]),
                name=str(data["name"]),
                birth_year=int(data["birth_year"]) if data.get("birth_year") is not None else None,
                birth_month=int(data["birth_month"]) if data.get("birth_month") is not None else None,
            )
        except (KeyError, TypeError, ValueError) as err:
            raise ValidationError(f"Error al deserializar Person: {err}") from err
