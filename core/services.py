"""Casos de uso y lógica de negocio para Novildo.
No contiene dependencias de terminal ni UI.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List

from .models import Memory, UserProfile, Tag, Person
from .storage import StorageRepository, JSONStorage
from .exceptions import ValidationError, NotFoundError, AmbiguousIdError


@dataclass
class PersonInEvent:
    """Representa a una persona en un evento con su edad calculada para ese momento."""
    person: Person
    age: Optional[int]


@dataclass
class TimelineEntry:
    """Entrada en la línea de tiempo que combina un recuerdo con la edad relativa calculada, su etiqueta opcional y las personas vinculadas."""
    memory: Memory
    age: Optional[int]
    tag: Optional[Tag] = None
    people: List[PersonInEvent] = field(default_factory=list)


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

    def register_memory(
        self,
        year: int,
        description: str,
        month: Optional[int] = None,
        tag_id: Optional[int] = None,
        person_ids: Optional[List[int]] = None,
    ) -> Memory:
        """Registra un nuevo recuerdo en el almacenamiento."""
        if tag_id is not None:
            tag = self.repository.get_tag_by_id(tag_id)
            if tag is None:
                raise NotFoundError(f"No existe ninguna etiqueta con el ID {tag_id}.")

        clean_person_ids = []
        if person_ids:
            for pid in person_ids:
                person = self.repository.get_person_by_id(pid)
                if person is None:
                    raise NotFoundError(f"No existe ninguna persona con el ID {pid}.")
                if pid not in clean_person_ids:
                    clean_person_ids.append(pid)

        memory = Memory(
            year=year,
            month=month,
            description=description,
            tag_id=tag_id,
            person_ids=clean_person_ids,
        )
        return self.repository.add_memory(memory)

    def get_timeline(
        self,
        ascending: bool = True,
        year: Optional[int] = None,
        tag_id: Optional[int] = None,
        person_id: Optional[int] = None,
    ) -> List[TimelineEntry]:
        """Retorna todos los recuerdos ordenados cronológicamente con la edad calculada, su etiqueta y personas vinculadas.
        Opcionalmente filtra por un año específico, por ID de etiqueta o por ID de persona.
        
        Criterio de ordenamiento:
        1. Año (ascendente)
        2. Mes (ascendente; mes None se ubica al final del año: valor 13)
        3. Fecha de creación (para desempates deterministas)
        """
        memories = self.repository.get_memories()
        if year is not None:
            memories = [m for m in memories if m.year == year]
        if tag_id is not None:
            memories = [m for m in memories if m.tag_id == tag_id]
        if person_id is not None:
            memories = [m for m in memories if person_id in m.person_ids]

        profile = self.repository.get_profile()
        tags_map = {t.id: t for t in self.repository.get_tags()}
        persons_map = {p.id: p for p in self.repository.get_persons()}

        # Clave de ordenamiento: (año, mes si existe o 13 para ir al final del año, timestamp de creación)
        sorted_memories = sorted(
            memories,
            key=lambda m: (m.year, m.month if m.month is not None else 13, m.created_at),
            reverse=not ascending
        )

        entries = []
        for m in sorted_memories:
            people_in_entry = []
            for pid in m.person_ids:
                if pid in persons_map:
                    p = persons_map[pid]
                    p_age = self.calculate_age(
                        event_year=m.year,
                        birth_year=p.birth_year,
                        event_month=m.month,
                        birth_month=p.birth_month,
                    )
                    people_in_entry.append(PersonInEvent(person=p, age=p_age))

            entries.append(
                TimelineEntry(
                    memory=m,
                    age=self.calculate_age(
                        event_year=m.year,
                        birth_year=profile.birth_year,
                        event_month=m.month,
                        birth_month=profile.birth_month,
                    ),
                    tag=tags_map.get(m.tag_id) if m.tag_id is not None else None,
                    people=people_in_entry,
                )
            )
        return entries

    def get_people_in_memory(self, memory: Memory) -> List[PersonInEvent]:
        """Obtiene las personas vinculadas a un recuerdo con sus edades calculadas para ese evento."""
        people = []
        for pid in memory.person_ids:
            p = self.repository.get_person_by_id(pid)
            if p is not None:
                p_age = self.calculate_age(
                    event_year=memory.year,
                    birth_year=p.birth_year,
                    event_month=memory.month,
                    birth_month=p.birth_month,
                )
                people.append(PersonInEvent(person=p, age=p_age))
        return people

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
        tag_id: Optional[int] = None,
        clear_tag: bool = False,
        person_ids: Optional[List[int]] = None,
        clear_people: bool = False,
    ) -> Memory:
        """Edita los campos especificados de un recuerdo existente."""
        memory = self.get_memory(memory_id)

        if (
            year is None
            and month is None
            and description is None
            and not clear_month
            and tag_id is None
            and not clear_tag
            and person_ids is None
            and not clear_people
        ):
            raise ValidationError("No se proporcionó ningún cambio para actualizar el recuerdo. Usa -y, -m, -d, -t, -p, --clear-month, --clear-tag o --clear-people.")

        if year is not None:
            memory.year = year

        if clear_month:
            memory.month = None
        elif month is not None:
            memory.month = month

        if description is not None:
            memory.description = description

        if clear_tag:
            memory.tag_id = None
        elif tag_id is not None:
            tag = self.repository.get_tag_by_id(tag_id)
            if tag is None:
                raise NotFoundError(f"No existe ninguna etiqueta con el ID {tag_id}.")
            memory.tag_id = tag_id

        if clear_people:
            memory.person_ids = []
        elif person_ids is not None:
            clean_person_ids = []
            for pid in person_ids:
                person = self.repository.get_person_by_id(pid)
                if person is None:
                    raise NotFoundError(f"No existe ninguna persona con el ID {pid}.")
                if pid not in clean_person_ids:
                    clean_person_ids.append(pid)
            memory.person_ids = clean_person_ids

        # Re-validar las reglas del modelo
        memory._validate()

        return self.repository.update_memory(memory)

    def delete_memory(self, memory_id: str) -> Memory:
        """Elimina un recuerdo existente por su ID o prefijo único y lo retorna."""
        memory = self.get_memory(memory_id)
        self.repository.delete_memory(memory.id)
        return memory

    def register_tag(self, name: str, emoji: Optional[str] = None) -> Tag:
        """Crea una nueva etiqueta con ID autoincremental empezando en 1."""
        clean_name = name.strip() if name else ""
        if not clean_name:
            raise ValidationError("El nombre de la etiqueta no puede estar vacío.")

        existing_tags = self.repository.get_tags()
        for t in existing_tags:
            if t.name.lower() == clean_name.lower():
                raise ValidationError(f"Ya existe una etiqueta con el nombre '{clean_name}' (ID: {t.id}).")

        next_id = max([t.id for t in existing_tags], default=0) + 1
        clean_emoji = emoji.strip() if emoji and emoji.strip() else None
        tag = Tag(id=next_id, name=clean_name, emoji=clean_emoji)
        return self.repository.add_tag(tag)

    def get_tags(self) -> List[Tag]:
        """Obtiene todas las etiquetas ordenadas por ID ascendente."""
        return sorted(self.repository.get_tags(), key=lambda t: t.id)

    def get_tag(self, tag_id: int) -> Tag:
        """Obtiene una etiqueta por su ID. Lanza NotFoundError si no existe."""
        tag = self.repository.get_tag_by_id(tag_id)
        if tag is None:
            raise NotFoundError(f"No existe ninguna etiqueta con el ID {tag_id}.")
        return tag

    def delete_tag(self, tag_id: int) -> Tag:
        """Elimina una etiqueta por su ID y la retorna."""
        tag = self.get_tag(tag_id)
        self.repository.delete_tag(tag.id)
        return tag

    def register_person(
        self,
        name: str,
        birth_year: Optional[int] = None,
        birth_month: Optional[int] = None,
    ) -> Person:
        """Crea una nueva persona con ID autoincremental empezando en 1."""
        clean_name = name.strip() if name else ""
        if not clean_name:
            raise ValidationError("El nombre de la persona no puede estar vacío.")

        existing_persons = self.repository.get_persons()
        for p in existing_persons:
            if p.name.lower() == clean_name.lower():
                raise ValidationError(f"Ya existe una persona registrada con el nombre '{clean_name}' (ID: {p.id}).")

        next_id = max([p.id for p in existing_persons], default=0) + 1
        person = Person(
            id=next_id,
            name=clean_name,
            birth_year=birth_year,
            birth_month=birth_month,
        )
        return self.repository.add_person(person)

    def get_persons(self) -> List[Person]:
        """Obtiene todas las personas ordenadas por ID ascendente."""
        return sorted(self.repository.get_persons(), key=lambda p: p.id)

    def get_person(self, person_id: int) -> Person:
        """Obtiene una persona por su ID. Lanza NotFoundError si no existe."""
        person = self.repository.get_person_by_id(person_id)
        if person is None:
            raise NotFoundError(f"No existe ninguna persona con el ID {person_id}.")
        return person

    def delete_person(self, person_id: int) -> Person:
        """Elimina una persona por su ID y la retorna."""
        person = self.get_person(person_id)
        self.repository.delete_person(person.id)
        return person


