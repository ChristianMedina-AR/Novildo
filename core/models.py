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

            return cls(
                id=clean_id,
                year=int(data["year"]),
                month=int(data["month"]) if data.get("month") is not None else None,
                description=str(data["description"]),
                created_at=data.get("created_at", datetime.now(timezone.utc)),
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
