"""Excepciones de dominio para Novildo.
"""


class NovildoError(Exception):
    """Excepción base para todos los errores de Novildo."""
    pass


class ValidationError(NovildoError):
    """Lanzada cuando la validación de un modelo o dato de entrada falla."""
    pass


class StorageError(NovildoError):
    """Lanzada cuando ocurre un error al persistir o cargar datos."""
    pass


class NotFoundError(NovildoError):
    """Lanzada cuando un recurso (por ejemplo, un recuerdo por su ID) no existe."""
    pass


class AmbiguousIdError(NovildoError):
    """Lanzada cuando un ID parcial/corto coincide con más de un recuerdo."""
    pass
