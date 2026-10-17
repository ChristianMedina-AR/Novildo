"""Módulo core de Novildo.
Contiene la lógica de dominio, modelos, servicios y almacenamiento independiente de la interfaz.
"""

from .models import Memory, UserProfile, Tag, Person
from .services import TimelineService, TimelineEntry
from .storage import StorageRepository, JSONStorage
from .exceptions import NovildoError, ValidationError, StorageError

__version__ = "0.2.0"

__all__ = [
    "__version__",
    "Memory",
    "UserProfile",
    "Tag",
    "Person",
    "TimelineService",
    "TimelineEntry",
    "StorageRepository",
    "JSONStorage",
    "NovildoError",
    "ValidationError",
    "StorageError",
]
