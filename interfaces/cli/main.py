"""Punto de entrada de la interfaz de línea de comandos (CLI) de Novildo.
Maneja argumentos mediante argparse y llama a la capa de servicios del core.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import List, Optional

from core import __version__
from core.services import TimelineService
from core.storage import JSONStorage
from core.exceptions import NovildoError, ValidationError
from .formatters import (
    format_timeline,
    format_memory_added,
    format_memory_updated,
    format_memory_deleted,
    format_tags,
    format_tag_added,
    format_tag_deleted,
    format_persons,
    format_person_added,
    format_person_deleted,
    format_profile,
    format_profile_updated,
    format_version,
    format_help_guide,
)


def parse_person_ids(raw_values: Optional[List[str]]) -> Optional[List[int]]:
    """Convierte una lista de strings (ej: ['1', '2'] o ['1,2']) en una lista de enteros únicos.
    Retorna None si raw_values es None.
    """
    if raw_values is None:
        return None
    ids: List[int] = []
    for item in raw_values:
        for part in item.split(","):
            part_str = part.strip()
            if not part_str:
                continue
            try:
                pid = int(part_str)
                if pid not in ids:
                    ids.append(pid)
            except ValueError:
                raise ValidationError(f"El ID de persona debe ser un número entero, se recibió: '{part_str}'")
    return ids


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de línea de comandos."""
    parser = argparse.ArgumentParser(
        prog="novildo",
        description="Novildo - Línea de tiempo y memoria personal.",
    )
    parser.add_argument(
        "--data-file",
        dest="data_file",
        default="novildo_data.json",
        help="Ruta al archivo JSON de persistencia (por defecto: novildo_data.json).",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=format_version(__version__),
        help="Muestra la versión actual de Novildo y finaliza.",
    )

    # Reemplazamos format_help para brindar la descripción integral de todos los comandos y argumentos
    parser.format_help = lambda: format_help_guide(__version__)

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    parser._subparsers_action = subparsers

    # Comando 'add'
    add_parser = subparsers.add_parser("add", help="Registrar un nuevo recuerdo")
    add_parser.add_argument(
        "-y", "--year",
        type=int,
        required=True,
        help="Año del suceso (obligatorio)",
    )
    add_parser.add_argument(
        "-m", "--month",
        type=int,
        default=None,
        help="Mes del suceso (opcional, 1 a 12)",
    )
    add_parser.add_argument(
        "-d", "--description",
        type=str,
        required=True,
        help="Descripción del recuerdo (obligatorio)",
    )
    add_parser.add_argument(
        "-t", "--tag",
        type=int,
        default=None,
        help="ID numérico de la etiqueta a asociar al recuerdo (opcional, entero >= 1)",
    )
    add_parser.add_argument(
        "-p", "--person", "--people",
        nargs="+",
        dest="people",
        default=None,
        help="ID(s) de personas vinculadas al recuerdo (opcional, enteros >= 1)",
    )

    # Comando 'list'
    list_parser = subparsers.add_parser("list", help="Ver la línea de tiempo cronológica")
    list_parser.add_argument(
        "-y", "--year",
        type=int,
        default=None,
        help="Filtrar los recuerdos por un año específico",
    )
    list_parser.add_argument(
        "-t", "--tag",
        type=int,
        default=None,
        help="Filtrar los recuerdos asociados a una etiqueta por su ID",
    )
    list_parser.add_argument(
        "-p", "--person", "--people",
        type=int,
        dest="person",
        default=None,
        help="Filtrar los recuerdos vinculados a una persona por su ID",
    )
    list_parser.add_argument(
        "-d", "--desc", "--descending",
        dest="descending",
        action="store_true",
        help="Mostrar en orden descendente (del más reciente al más antiguo)",
    )

    # Comando 'edit'
    edit_parser = subparsers.add_parser("edit", aliases=["update"], help="Editar un recuerdo existente por su ID")
    edit_parser.add_argument(
        "id",
        type=str,
        help="ID (o prefijo único) del recuerdo a editar",
    )
    edit_parser.add_argument(
        "-y", "--year",
        type=int,
        default=None,
        help="Nuevo año del suceso",
    )
    edit_parser.add_argument(
        "-m", "--month",
        type=int,
        default=None,
        help="Nuevo mes del suceso (opcional, 1 a 12)",
    )
    edit_parser.add_argument(
        "--clear-month",
        action="store_true",
        help="Eliminar el mes registrado en el recuerdo",
    )
    edit_parser.add_argument(
        "-d", "--description",
        type=str,
        default=None,
        help="Nueva descripción del recuerdo",
    )
    edit_parser.add_argument(
        "-t", "--tag",
        type=int,
        default=None,
        help="Nuevo ID de etiqueta para asociar al recuerdo",
    )
    edit_parser.add_argument(
        "--clear-tag",
        action="store_true",
        help="Eliminar la etiqueta asociada al recuerdo",
    )
    edit_parser.add_argument(
        "-p", "--person", "--people",
        nargs="+",
        dest="people",
        default=None,
        help="Nuevos ID(s) de personas para vincular al recuerdo",
    )
    edit_parser.add_argument(
        "--clear-people",
        action="store_true",
        help="Desvincular todas las personas asociadas al recuerdo",
    )

    # Comando 'delete'
    delete_parser = subparsers.add_parser("delete", aliases=["rm", "remove"], help="Eliminar un recuerdo por su ID")
    delete_parser.add_argument(
        "id",
        type=str,
        help="ID (o prefijo único) del recuerdo a eliminar",
    )

    # Comando 'tag'
    tag_parser = subparsers.add_parser(
        "tag",
        aliases=["t"],
        help="Crear y administrar etiquetas para recuerdos",
    )
    tag_parser.add_argument(
        "action_or_name",
        nargs="?",
        default=None,
        help="Acción ('add', 'list', 'delete') o nombre directo de la etiqueta a crear",
    )
    tag_parser.add_argument(
        "extra_arg",
        nargs="?",
        default=None,
        help="Nombre de la etiqueta (con 'add') o ID de la etiqueta (con 'delete')",
    )
    tag_parser.add_argument(
        "-n", "--name",
        type=str,
        default=None,
        help="Nombre de la etiqueta",
    )
    tag_parser.add_argument(
        "-e", "--emoji", "--emote",
        dest="emoji",
        type=str,
        default=None,
        help="Emote o emoji asociado a la etiqueta",
    )
    tag_parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="Listar todas las etiquetas existentes",
    )
    tag_parser.add_argument(
        "-d", "--delete", "--rm",
        dest="delete_id",
        type=int,
        default=None,
        help="ID de la etiqueta a eliminar",
    )

    # Comando 'person'
    person_parser = subparsers.add_parser(
        "person",
        aliases=["p"],
        help="Registrar y administrar personas para asociar a recuerdos",
    )
    person_parser.add_argument(
        "action_or_name",
        nargs="?",
        default=None,
        help="Acción ('add', 'list', 'delete') o nombre directo de la persona a registrar",
    )
    person_parser.add_argument(
        "extra_arg",
        nargs="?",
        default=None,
        help="Nombre de la persona (con 'add') o ID de la persona (con 'delete')",
    )
    person_parser.add_argument(
        "-n", "--name",
        type=str,
        default=None,
        help="Nombre y apellido de la persona",
    )
    person_parser.add_argument(
        "-b", "-y", "--birth-year", "--year",
        dest="birth_year",
        type=int,
        default=None,
        help="Año de nacimiento de la persona (opcional)",
    )
    person_parser.add_argument(
        "-m", "--month", "--birth-month",
        dest="birth_month",
        type=int,
        default=None,
        help="Mes de nacimiento de la persona (opcional, 1 a 12)",
    )
    person_parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="Listar todas las personas registradas",
    )
    person_parser.add_argument(
        "-d", "--delete", "--rm",
        dest="delete_id",
        type=int,
        default=None,
        help="ID de la persona a eliminar",
    )

    # Comando 'profile'
    profile_parser = subparsers.add_parser("profile", help="Ver o configurar el perfil de usuario")
    profile_parser.add_argument(
        "-y", "--year", "-b", "--birth-year",
        type=int,
        dest="birth_year",
        default=None,
        help="Configurar el año de nacimiento base",
    )
    profile_parser.add_argument(
        "-m", "--month", "--birth-month",
        type=int,
        dest="birth_month",
        default=None,
        help="Configurar el mes de nacimiento (1 a 12)",
    )
    profile_parser.add_argument(
        "--clear-birth-month",
        action="store_true",
        help="Eliminar la configuración del mes de nacimiento",
    )
    profile_parser.add_argument(
        "-c", "--clear-birth-year", "--clear",
        dest="clear_birth_year",
        action="store_true",
        help="Eliminar la configuración de la fecha de nacimiento",
    )

    # Comando 'version'
    subparsers.add_parser(
        "version",
        aliases=["v"],
        help="Muestra la versión actual de Novildo",
    )

    # Comando 'help'
    help_parser = subparsers.add_parser(
        "help",
        aliases=["h"],
        help="Muestra la ayuda detallada de todos los comandos y argumentos",
    )
    help_parser.add_argument(
        "topic",
        nargs="?",
        default=None,
        help="Comando específico del cual ver la ayuda detallada (opcional)",
    )

    return parser


def handle_add(service: TimelineService, args: argparse.Namespace) -> int:
    """Maneja el comando 'add'."""
    tag_id = getattr(args, "tag", None)
    person_ids = parse_person_ids(getattr(args, "people", None))
    memory = service.register_memory(
        year=args.year,
        description=args.description,
        month=args.month,
        tag_id=tag_id,
        person_ids=person_ids,
    )
    tag = service.get_tag(tag_id) if tag_id is not None else None
    people = service.get_people_in_memory(memory) if memory.person_ids else None
    print(format_memory_added(memory, tag=tag, people=people))
    return 0


def handle_list(service: TimelineService, args: argparse.Namespace) -> int:
    """Maneja el comando 'list'."""
    ascending = not getattr(args, "descending", False)
    year = getattr(args, "year", None)
    tag_id = getattr(args, "tag", None)
    person_id = getattr(args, "person", None)
    tag = service.get_tag(tag_id) if tag_id is not None else None
    person = service.get_person(person_id) if person_id is not None else None
    entries = service.get_timeline(
        ascending=ascending,
        year=year,
        tag_id=tag_id,
        person_id=person_id,
    )
    print(format_timeline(
        entries,
        year=year,
        tag=tag,
        tag_id=tag_id,
        person=person,
        person_id=person_id,
    ))
    return 0


def handle_edit(service: TimelineService, args: argparse.Namespace) -> int:
    """Maneja el comando 'edit' / 'update'."""
    tag_id = getattr(args, "tag", None)
    clear_tag = getattr(args, "clear_tag", False)
    clear_people = getattr(args, "clear_people", False)
    person_ids = parse_person_ids(getattr(args, "people", None))
    updated = service.update_memory(
        memory_id=args.id,
        year=args.year,
        month=args.month,
        description=args.description,
        clear_month=args.clear_month,
        tag_id=tag_id,
        clear_tag=clear_tag,
        person_ids=person_ids,
        clear_people=clear_people,
    )
    tag = service.get_tag(updated.tag_id) if updated.tag_id is not None else None
    people = service.get_people_in_memory(updated) if updated.person_ids else None
    print(format_memory_updated(updated, tag=tag, people=people))
    return 0


def handle_delete(service: TimelineService, args: argparse.Namespace) -> int:
    """Maneja el comando 'delete' / 'rm'."""
    deleted = service.delete_memory(memory_id=args.id)
    print(format_memory_deleted(deleted))
    return 0


def handle_tag(service: TimelineService, args: argparse.Namespace) -> int:
    """Maneja el comando 'tag' / 't'."""
    if getattr(args, "delete_id", None) is not None:
        deleted = service.delete_tag(args.delete_id)
        print(format_tag_deleted(deleted))
        return 0

    action = (args.action_or_name or "").strip().lower()

    if action in ("delete", "rm", "remove"):
        if not args.extra_arg:
            print("Error: Debes especificar el ID de la etiqueta a eliminar. Ejemplo: 'novildo tag delete 1'", file=sys.stderr)
            return 1
        try:
            tag_id = int(args.extra_arg)
        except ValueError:
            print(f"Error: El ID de la etiqueta debe ser un número entero, se recibió: '{args.extra_arg}'", file=sys.stderr)
            return 1
        deleted = service.delete_tag(tag_id)
        print(format_tag_deleted(deleted))
        return 0

    if getattr(args, "list", False) or action in ("list", "ls") or (not action and not args.name):
        tags = service.get_tags()
        print(format_tags(tags))
        return 0

    if action in ("add", "create", "new"):
        name = args.name or args.extra_arg
    else:
        name = args.name or args.action_or_name

    if not name or not name.strip():
        print("Error: Debes proporcionar un nombre para la etiqueta. Ejemplo: 'novildo tag add \"Estudios\" -e \"🎓\"'", file=sys.stderr)
        return 1

    tag = service.register_tag(name=name, emoji=args.emoji)
    print(format_tag_added(tag))
    return 0


def handle_person(service: TimelineService, args: argparse.Namespace) -> int:
    """Maneja el comando 'person' / 'p'."""
    if getattr(args, "delete_id", None) is not None:
        deleted = service.delete_person(args.delete_id)
        print(format_person_deleted(deleted))
        return 0

    action = (args.action_or_name or "").strip().lower()

    if action in ("delete", "rm", "remove"):
        if not args.extra_arg:
            print("Error: Debes especificar el ID de la persona a eliminar. Ejemplo: 'novildo person delete 1'", file=sys.stderr)
            return 1
        try:
            person_id = int(args.extra_arg)
        except ValueError:
            print(f"Error: El ID de la persona debe ser un número entero, se recibió: '{args.extra_arg}'", file=sys.stderr)
            return 1
        deleted = service.delete_person(person_id)
        print(format_person_deleted(deleted))
        return 0

    if getattr(args, "list", False) or action in ("list", "ls") or (not action and not args.name):
        persons = service.get_persons()
        print(format_persons(persons))
        return 0

    if action in ("add", "create", "new"):
        name = args.name or args.extra_arg
    else:
        name = args.name or args.action_or_name

    if not name or not name.strip():
        print("Error: Debes proporcionar un nombre para la persona. Ejemplo: 'novildo person add \"Juan Pérez\" -b 1990 -m 5'", file=sys.stderr)
        return 1

    person = service.register_person(
        name=name,
        birth_year=getattr(args, "birth_year", None),
        birth_month=getattr(args, "birth_month", None),
    )
    print(format_person_added(person))
    return 0


def handle_profile(service: TimelineService, args: argparse.Namespace) -> int:
    """Maneja el comando 'profile'."""
    if args.clear_birth_year:
        updated = service.update_profile(clear_birth_year=True)
        print(format_profile_updated(updated))
        return 0

    if args.clear_birth_month:
        updated = service.update_profile(clear_birth_month=True)
        print(format_profile_updated(updated))
        return 0

    if args.birth_year is not None or args.birth_month is not None:
        updated = service.update_profile(
            birth_year=args.birth_year,
            birth_month=args.birth_month,
        )
        print(format_profile_updated(updated))
        return 0

    # Si no se pasó argumento para modificar, mostramos el perfil actual
    profile = service.get_profile()
    print(format_profile(profile))
    return 0


def handle_version() -> int:
    """Maneja el comando 'version' / 'v'."""
    print(format_version(__version__))
    return 0


def handle_help(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """Maneja el comando 'help' / 'h'."""
    if args.topic:
        topic = args.topic.strip().lower()
        subparsers_action = getattr(parser, "_subparsers_action", None)
        choices = getattr(subparsers_action, "choices", {}) if subparsers_action else {}
        if topic in choices:
            choices[topic].print_help()
            return 0
        else:
            print(f"Comando desconocido: '{args.topic}'. Usa 'novildo help' para ver la lista completa de comandos.", file=sys.stderr)
            return 1

    print(format_help_guide(__version__))
    return 0


def cli_main(args: Optional[List[str]] = None) -> int:
    """Punto de entrada programático y ejecutable para la CLI."""
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 0

    if parsed_args.command in ("version", "v"):
        return handle_version()

    if parsed_args.command in ("help", "h"):
        return handle_help(parser, parsed_args)

    storage = JSONStorage(filepath=Path(parsed_args.data_file))
    service = TimelineService(repository=storage)

    try:
        if parsed_args.command == "add":
            return handle_add(service, parsed_args)
        elif parsed_args.command == "list":
            return handle_list(service, parsed_args)
        elif parsed_args.command in ("edit", "update"):
            return handle_edit(service, parsed_args)
        elif parsed_args.command in ("delete", "rm", "remove"):
            return handle_delete(service, parsed_args)
        elif parsed_args.command in ("tag", "t"):
            return handle_tag(service, parsed_args)
        elif parsed_args.command in ("person", "p"):
            return handle_person(service, parsed_args)
        elif parsed_args.command == "profile":
            return handle_profile(service, parsed_args)
        else:
            parser.print_help()
            return 1
    except NovildoError as err:
        print(f"Error en Novildo: {err}", file=sys.stderr)
        return 1
    except Exception as err:
        print(f"Error inesperado: {err}", file=sys.stderr)
        return 1
