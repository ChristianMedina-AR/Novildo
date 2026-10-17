"""Formateadores de salida para la interfaz de línea de comandos.
Transforma los modelos y resultados del core en texto legible y tabulado.
"""

from __future__ import annotations
from typing import List, Optional

from core.models import Memory, UserProfile, Tag, Person
from core.services import TimelineEntry, PersonInEvent

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


def format_timeline(
    entries: List[TimelineEntry],
    year: Optional[int] = None,
    tag: Optional[Tag] = None,
    tag_id: Optional[int] = None,
    person: Optional[Person] = None,
    person_id: Optional[int] = None,
) -> str:
    """Formatea la lista de recuerdos cronológicos en una tabla clara para la terminal."""
    if not entries:
        if year is not None and tag_id is not None:
            return f"No hay recuerdos registrados para el año {year} con la etiqueta ID {tag_id}."
        if year is not None and person_id is not None:
            return f"No hay recuerdos registrados para el año {year} con la persona ID {person_id}."
        if person is not None:
            return f"No hay recuerdos registrados con la persona '{person.name}' (ID {person.id})."
        if person_id is not None:
            return f"No hay recuerdos registrados con la persona ID {person_id}."
        if year is not None:
            return f"No hay recuerdos registrados para el año {year}."
        if tag is not None:
            tag_display = f"{tag.emoji} {tag.name}" if tag.emoji else tag.name
            return f"No hay recuerdos registrados con la etiqueta '{tag_display}' (ID {tag.id})."
        if tag_id is not None:
            return f"No hay recuerdos registrados con la etiqueta ID {tag_id}."
        return (
            "No hay recuerdos registrados aún en tu línea de tiempo.\n"
            "Usa 'novildo add -y <AÑO> -d \"<TEXTO>\"' (o con --year y --description) para agregar uno."
        )

    headers = ("ID", "Año", "Mes", "Edad", "Etiqueta", "Personas", "Descripción")
    
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

        if entry.tag is not None:
            tag_str = f"{entry.tag.emoji} {entry.tag.name}" if entry.tag.emoji else entry.tag.name
        else:
            tag_str = "-"

        if entry.people:
            people_str = ", ".join(
                f"{p.person.name} ({p.age} años)" if p.age is not None else p.person.name
                for p in entry.people
            )
        else:
            people_str = "-"

        desc_str = entry.memory.description
        rows.append((id_str, year_str, month_str, age_str, tag_str, people_str, desc_str))

    # Calculamos anchos de columnas
    w_id = max(len(headers[0]), max(len(r[0]) for r in rows))
    w_year = max(len(headers[1]), max(len(r[1]) for r in rows))
    w_month = max(len(headers[2]), max(len(r[2]) for r in rows))
    w_age = max(len(headers[3]), max(len(r[3]) for r in rows))
    w_tag = max(len(headers[4]), max(len(r[4]) for r in rows))
    w_people = max(len(headers[5]), max(len(r[5]) for r in rows))
    w_desc = max(len(headers[6]), max(len(r[6]) for r in rows))

    col_format = f"{{:<{w_id}}}  {{:<{w_year}}}  {{:<{w_month}}}  {{:<{w_age}}}  {{:<{w_tag}}}  {{:<{w_people}}}  {{}}"
    separator = f"{'-' * w_id}  {'-' * w_year}  {'-' * w_month}  {'-' * w_age}  {'-' * w_tag}  {'-' * w_people}  {'-' * min(w_desc, 50)}"

    lines = [
        col_format.format(*headers),
        separator,
    ]
    for r in rows:
        lines.append(col_format.format(*r))

    return "\n".join(lines)


def format_memory_added(
    memory: Memory,
    tag: Optional[Tag] = None,
    people: Optional[List[PersonInEvent]] = None,
) -> str:
    """Mensaje amigable de confirmación al registrar un recuerdo."""
    lines = [
        "✓ Recuerdo registrado con éxito:",
        f"  - Año: {memory.year}",
    ]
    if memory.month is not None:
        lines.append(f"  - Mes: {format_month(memory.month)}")
    lines.append(f"  - Descripción: {memory.description}")
    if tag is not None:
        tag_display = f"{tag.emoji} {tag.name}" if tag.emoji else tag.name
        lines.append(f"  - Etiqueta: {tag_display} (ID: {tag.id})")
    if people:
        people_str = ", ".join(
            f"{p.person.name} ({p.age} años)" if p.age is not None else p.person.name
            for p in people
        )
        lines.append(f"  - Personas: {people_str}")
    lines.append(f"  - ID: {memory.id}")
    return "\n".join(lines)


def format_memory_updated(
    memory: Memory,
    tag: Optional[Tag] = None,
    people: Optional[List[PersonInEvent]] = None,
) -> str:
    """Mensaje amigable de confirmación al actualizar un recuerdo."""
    lines = [
        "✓ Recuerdo actualizado con éxito:",
        f"  - ID: {memory.id}",
        f"  - Año: {memory.year}",
    ]
    if memory.month is not None:
        lines.append(f"  - Mes: {format_month(memory.month)}")
    lines.append(f"  - Descripción: {memory.description}")
    if tag is not None:
        tag_display = f"{tag.emoji} {tag.name}" if tag.emoji else tag.name
        lines.append(f"  - Etiqueta: {tag_display} (ID: {tag.id})")
    if people:
        people_str = ", ".join(
            f"{p.person.name} ({p.age} años)" if p.age is not None else p.person.name
            for p in people
        )
        lines.append(f"  - Personas: {people_str}")
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


def format_tags(tags: List[Tag]) -> str:
    """Formatea la lista de etiquetas registradas en una tabla para la terminal."""
    if not tags:
        return (
            "No hay etiquetas registradas aún en Novildo.\n"
            "Usa 'novildo tag add <NOMBRE> [-e <EMOTE>]' (o 'novildo t add') para crear una."
        )

    headers = ("ID", "Emote", "Nombre")
    rows = []
    for t in tags:
        emote_str = t.emoji if t.emoji else "-"
        rows.append((str(t.id), emote_str, t.name))

    w_id = max(len(headers[0]), max(len(r[0]) for r in rows))
    w_emote = max(len(headers[1]), max(len(r[1]) for r in rows))
    w_name = max(len(headers[2]), max(len(r[2]) for r in rows))

    col_format = f"{{:<{w_id}}}  {{:<{w_emote}}}  {{}}"
    separator = f"{'-' * w_id}  {'-' * w_emote}  {'-' * max(w_name, 10)}"

    lines = [
        col_format.format(*headers),
        separator,
    ]
    for r in rows:
        lines.append(col_format.format(*r))

    return "\n".join(lines)


def format_tag_added(tag: Tag) -> str:
    """Mensaje amigable de confirmación al registrar una etiqueta."""
    lines = [
        "✓ Etiqueta creada con éxito:",
        f"  - ID: {tag.id}",
        f"  - Nombre: {tag.name}",
    ]
    if tag.emoji:
        lines.append(f"  - Emote: {tag.emoji}")
    return "\n".join(lines)


def format_tag_deleted(tag: Tag) -> str:
    """Mensaje amigable de confirmación al eliminar una etiqueta."""
    lines = [
        "✓ Etiqueta eliminada con éxito:",
        f"  - ID: {tag.id}",
        f"  - Nombre: {tag.name}",
    ]
    if tag.emoji:
        lines.append(f"  - Emote: {tag.emoji}")
    return "\n".join(lines)


def format_persons(persons: List[Person]) -> str:
    """Formatea la lista de personas registradas en una tabla para la terminal."""
    if not persons:
        return (
            "No hay personas registradas aún en Novildo.\n"
            "Usa 'novildo person add \"<NOMBRE>\" [-b <AÑO>] [-m <MES>]' (o 'novildo p add') para registrar una."
        )

    headers = ("ID", "Nombre", "Fecha de nacimiento")
    rows = []
    for p in persons:
        if p.birth_year is not None and p.birth_month is not None:
            birth_str = f"{format_month(p.birth_month)} de {p.birth_year}"
        elif p.birth_year is not None:
            birth_str = str(p.birth_year)
        else:
            birth_str = "-"
        rows.append((str(p.id), p.name, birth_str))

    w_id = max(len(headers[0]), max(len(r[0]) for r in rows))
    w_name = max(len(headers[1]), max(len(r[1]) for r in rows))
    w_birth = max(len(headers[2]), max(len(r[2]) for r in rows))

    col_format = f"{{:<{w_id}}}  {{:<{w_name}}}  {{}}"
    separator = f"{'-' * w_id}  {'-' * w_name}  {'-' * max(w_birth, 19)}"

    lines = [
        col_format.format(*headers),
        separator,
    ]
    for r in rows:
        lines.append(col_format.format(*r))

    return "\n".join(lines)


def format_person_added(person: Person) -> str:
    """Mensaje amigable de confirmación al registrar una persona."""
    lines = [
        "✓ Persona registrada con éxito:",
        f"  - ID: {person.id}",
        f"  - Nombre: {person.name}",
    ]
    if person.birth_year is not None and person.birth_month is not None:
        lines.append(f"  - Fecha de nacimiento: {format_month(person.birth_month)} de {person.birth_year}")
    elif person.birth_year is not None:
        lines.append(f"  - Año de nacimiento: {person.birth_year}")
    return "\n".join(lines)


def format_person_deleted(person: Person) -> str:
    """Mensaje amigable de confirmación al eliminar una persona."""
    lines = [
        "✓ Persona eliminada con éxito:",
        f"  - ID: {person.id}",
        f"  - Nombre: {person.name}",
    ]
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


def format_version(version: str) -> str:
    """Devuelve la versión actual formateada."""
    return f"Novildo v{version}"


def format_help_guide(version: str) -> str:
    """Devuelve una guía descriptiva completa de todos los comandos y argumentos disponibles."""
    return (
        f"Novildo - Línea de tiempo y memoria personal (v{version}).\n\n"
        "Uso general:\n"
        "  novildo [opciones_globales] <comando> [argumentos]\n\n"
        "Opciones globales:\n"
        "  -h, --help                          Muestra esta ayuda y descripción de argumentos.\n"
        "  -v, --version                       Muestra la versión actual de Novildo.\n"
        "  --data-file <RUTA>                  Ruta al archivo JSON de persistencia (por defecto: novildo_data.json).\n\n"
        "Comandos disponibles y sus argumentos:\n\n"
        "  add\n"
        "    Registra un nuevo recuerdo en la línea de tiempo.\n"
        "    Argumentos:\n"
        "      -y, --year <AÑO>                Año del suceso (obligatorio).\n"
        "      -m, --month <MES>               Mes del suceso (opcional, 1 a 12).\n"
        "      -d, --description <TEXTO>       Descripción del recuerdo (obligatorio).\n"
        "      -t, --tag <ID>                  ID numérico de la etiqueta a asociar al recuerdo (opcional).\n"
        "      -p, --person, --people <ID...>  ID(s) de personas vinculadas al recuerdo (opcional).\n\n"
        "  list\n"
        "    Muestra la línea de tiempo cronológica con ID y edad calculada.\n"
        "    Argumentos:\n"
        "      -y, --year <AÑO>                Filtrar recuerdos para ver solo un año específico.\n"
        "      -t, --tag <ID>                  Filtrar recuerdos asociados a una etiqueta por su ID.\n"
        "      -p, --person, --people <ID>     Filtrar recuerdos vinculados a una persona por su ID.\n"
        "      -d, --desc, --descending        Mostrar en orden descendente (del más reciente al más antiguo).\n\n"
        "  edit (alias: update)\n"
        "    Modifica un recuerdo existente identificado por su ID o prefijo único.\n"
        "    Argumentos:\n"
        "      <id>                            ID o prefijo único del recuerdo a modificar (obligatorio).\n"
        "      -y, --year <AÑO>                Nuevo año del recuerdo.\n"
        "      -m, --month <MES>               Nuevo mes del recuerdo (1 a 12).\n"
        "      -d, --description <TEXTO>       Nueva descripción del recuerdo.\n"
        "      --clear-month                   Elimina el mes asignado al recuerdo.\n"
        "      -t, --tag <ID>                  Nuevo ID de etiqueta para asociar al recuerdo.\n"
        "      --clear-tag                     Elimina la etiqueta asociada al recuerdo.\n"
        "      -p, --person, --people <ID...>  Nuevos ID(s) de personas para vincular al recuerdo.\n"
        "      --clear-people                  Desvincula todas las personas del recuerdo.\n\n"
        "  delete (alias: rm, remove)\n"
        "    Elimina un recuerdo existente por su ID o prefijo único.\n"
        "    Argumentos:\n"
        "      <id>                            ID o prefijo único del recuerdo a eliminar (obligatorio).\n\n"
        "  tag (alias: t)\n"
        "    Crea y administra etiquetas temáticas con emotes/emojis e ID numérico para categorizar recuerdos.\n"
        "    Subcomandos / Acciones:\n"
        "      add (o create) <NOMBRE> [-e <EMOTE>]   Crea una etiqueta con ID numérico (empezando en 1).\n"
        "      list (o ls)                            Lista todas las etiquetas registradas.\n"
        "      delete (o rm) <ID>                     Elimina una etiqueta por su ID numérico.\n"
        "    Argumentos:\n"
        "      -n, --name <NOMBRE>             Nombre de la etiqueta.\n"
        "      -e, --emoji, --emote <EMOTE>    Emote o emoji representativo de la etiqueta.\n"
        "      -l, --list                      Lista las etiquetas creadas.\n"
        "      -d, --delete, --rm <ID>         Elimina una etiqueta por su ID numérico.\n\n"
        "  person (alias: p)\n"
        "    Registra y administra personas con fecha de nacimiento para ver sus edades en recuerdos.\n"
        "    Subcomandos / Acciones:\n"
        "      add (o create) <NOMBRE> [-b <AÑO>] [-m <MES>]  Registra una persona con fecha de nacimiento opcional.\n"
        "      list (o ls)                                    Lista todas las personas registradas.\n"
        "      delete (o rm) <ID>                             Elimina una persona por su ID numérico.\n"
        "    Argumentos:\n"
        "      -n, --name <NOMBRE>             Nombre y apellido de la persona.\n"
        "      -b, -y, --birth-year <AÑO>      Año de nacimiento de la persona (opcional).\n"
        "      -m, --birth-month <MES>         Mes de nacimiento de la persona (opcional, 1 a 12).\n"
        "      -l, --list                      Lista las personas registradas.\n"
        "      -d, --delete, --rm <ID>         Elimina una persona por su ID numérico.\n\n"
        "  profile\n"
        "    Consulta o configura la fecha de nacimiento (año y mes) para el cálculo de edad.\n"
        "    Argumentos:\n"
        "      -b, -y, --year, --birth-year <AÑO>   Configura el año de nacimiento base.\n"
        "      -m, --month, --birth-month <MES>     Configura el mes de nacimiento (1 a 12).\n"
        "      --clear-birth-month                  Elimina la configuración del mes de nacimiento.\n"
        "      -c, --clear, --clear-birth-year      Elimina toda la configuración de nacimiento.\n\n"
        "  version (alias: v)\n"
        "    Muestra la versión actual de Novildo (ej: 'novildo version', 'novildo v', o bandera '-v').\n\n"
        "  help (alias: h)\n"
        "    Muestra esta ayuda completa de comandos y argumentos.\n"
        "    Uso: 'novildo help' o 'novildo help <comando>'."
    )
