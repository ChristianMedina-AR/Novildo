"""Formateadores de salida para la interfaz de línea de comandos.
Transforma los modelos y resultados del core en texto legible y tabulado.
"""

from __future__ import annotations
from typing import List, Optional

from core.models import Memory, UserProfile
from core.services import TimelineEntry

MONTH_NAMES = [
    "",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]


def format_month(month: Optional[int]) -> str:
    """Devuelve el nombre del mes o '-' si no fue especificado."""
    if month is None:
        return "-"
    if 1 <= month <= 12:
        return MONTH_NAMES[month]
    return str(month)


def format_timeline(entries: List[TimelineEntry]) -> str:
    """Formatea la lista de recuerdos cronológicos en una tabla clara para la terminal."""
    if not entries:
        return (
            "No hay recuerdos registrados aún en tu línea de tiempo.\n"
            "Usa 'novildo add -y <AÑO> -d \"<TEXTO>\"' (o con --year y --description) para agregar uno."
        )

    headers = ("ID", "Año", "Mes", "Edad", "Descripción")
    
    # Preparamos las filas
    rows = []
    for entry in entries:
        id_str = entry.memory.id
        year_str = str(entry.memory.year)
        month_str = format_month(entry.memory.month)
        if entry.age is not None:
            age_str = f"{entry.age} años" if entry.age >= 0 else f"{entry.age} (previo)"
        else:
            age_str = "-"
        desc_str = entry.memory.description
        rows.append((id_str, year_str, month_str, age_str, desc_str))

    # Calculamos anchos de columnas
    w_id = max(len(headers[0]), max(len(r[0]) for r in rows))
    w_year = max(len(headers[1]), max(len(r[1]) for r in rows))
    w_month = max(len(headers[2]), max(len(r[2]) for r in rows))
    w_age = max(len(headers[3]), max(len(r[3]) for r in rows))
    w_desc = max(len(headers[4]), max(len(r[4]) for r in rows))

    col_format = f"{{:<{w_id}}}  {{:<{w_year}}}  {{:<{w_month}}}  {{:<{w_age}}}  {{}}"
    separator = f"{'-' * w_id}  {'-' * w_year}  {'-' * w_month}  {'-' * w_age}  {'-' * min(w_desc, 50)}"

    lines = [
        col_format.format(*headers),
        separator,
    ]
    for r in rows:
        lines.append(col_format.format(*r))

    return "\n".join(lines)


def format_memory_added(memory: Memory) -> str:
    """Mensaje amigable de confirmación al registrar un recuerdo."""
    lines = [
        "✓ Recuerdo registrado con éxito:",
        f"  - Año: {memory.year}",
    ]
    if memory.month is not None:
        lines.append(f"  - Mes: {format_month(memory.month)}")
    lines.extend([
        f"  - Descripción: {memory.description}",
        f"  - ID: {memory.id}",
    ])
    return "\n".join(lines)


def format_memory_updated(memory: Memory) -> str:
    """Mensaje amigable de confirmación al actualizar un recuerdo."""
    lines = [
        "✓ Recuerdo actualizado con éxito:",
        f"  - ID: {memory.id}",
        f"  - Año: {memory.year}",
    ]
    if memory.month is not None:
        lines.append(f"  - Mes: {format_month(memory.month)}")
    lines.append(f"  - Descripción: {memory.description}")
    return "\n".join(lines)


def format_memory_deleted(memory: Memory) -> str:
    """Mensaje amigable de confirmación al eliminar un recuerdo."""
    lines = [
        "✓ Recuerdo eliminado con éxito:",
        f"  - ID: {memory.id}",
        f"  - Año: {memory.year}",
    ]
    if memory.month is not None:
        lines.append(f"  - Mes: {format_month(memory.month)}")
    lines.append(f"  - Descripción: {memory.description}")
    return "\n".join(lines)


def format_profile(profile: UserProfile) -> str:
    """Formatea los datos del perfil actual."""
    if profile.birth_year is not None and profile.birth_month is not None:
        return f"Perfil de usuario: Fecha de nacimiento configurada en {format_month(profile.birth_month)} de {profile.birth_year}."
    elif profile.birth_year is not None:
        return f"Perfil de usuario: Año de nacimiento configurado en {profile.birth_year} (mes no especificado)."
    return "Perfil de usuario: Año de nacimiento no configurado. (Usa 'profile -b <AÑO> -m <MES>')"


def format_profile_updated(profile: UserProfile) -> str:
    """Mensaje amigable tras actualizar el perfil."""
    if profile.birth_year is not None and profile.birth_month is not None:
        return f"✓ Perfil actualizado: Fecha de nacimiento establecida en {format_month(profile.birth_month)} de {profile.birth_year}."
    elif profile.birth_year is not None:
        return f"✓ Perfil actualizado: Año de nacimiento establecido en {profile.birth_year}."
    return "✓ Perfil actualizado: Se ha eliminado el año de nacimiento."
