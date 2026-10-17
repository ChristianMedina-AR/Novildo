"""Punto de entrada de la interfaz de línea de comandos (CLI) de Novildo.
Maneja argumentos mediante argparse y llama a la capa de servicios del core.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import List, Optional

from core.services import TimelineService
from core.storage import JSONStorage
from core.exceptions import NovildoError
from .formatters import (
    format_timeline,
    format_memory_added,
    format_memory_updated,
    format_memory_deleted,
    format_profile,
    format_profile_updated,
)


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

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

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

    # Comando 'list'
    list_parser = subparsers.add_parser("list", help="Ver la línea de tiempo cronológica")
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

    # Comando 'delete'
    delete_parser = subparsers.add_parser("delete", aliases=["rm", "remove"], help="Eliminar un recuerdo por su ID")
    delete_parser.add_argument(
        "id",
        type=str,
        help="ID (o prefijo único) del recuerdo a eliminar",
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

    return parser


def handle_add(service: TimelineService, args: argparse.Namespace) -> int:
    """Maneja el comando 'add'."""
    memory = service.register_memory(
        year=args.year,
        description=args.description,
        month=args.month,
    )
    print(format_memory_added(memory))
    return 0


def handle_list(service: TimelineService, args: argparse.Namespace) -> int:
    """Maneja el comando 'list'."""
    ascending = not getattr(args, "descending", False)
    entries = service.get_timeline(ascending=ascending)
    print(format_timeline(entries))
    return 0


def handle_edit(service: TimelineService, args: argparse.Namespace) -> int:
    """Maneja el comando 'edit' / 'update'."""
    updated = service.update_memory(
        memory_id=args.id,
        year=args.year,
        month=args.month,
        description=args.description,
        clear_month=args.clear_month,
    )
    print(format_memory_updated(updated))
    return 0


def handle_delete(service: TimelineService, args: argparse.Namespace) -> int:
    """Maneja el comando 'delete' / 'rm'."""
    deleted = service.delete_memory(memory_id=args.id)
    print(format_memory_deleted(deleted))
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


def cli_main(args: Optional[List[str]] = None) -> int:
    """Punto de entrada programático y ejecutable para la CLI."""
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 0

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
