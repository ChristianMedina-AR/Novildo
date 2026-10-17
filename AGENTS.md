# Directivas del Proyecto: Novildo

## 1. Visión y Dominio
- **Nombre:** Novildo.
- **Propósito:** Aplicación de línea de tiempo y memoria personal. Permite registrar hitos de vida indicando año (obligatorio), mes (opcional) y descripción (obligatoria), para visualizarlos cronológicamente calculando la edad relativa del usuario a partir de su año de nacimiento configurado.
- **Fase actual:** Interfaz de línea de comandos (CLI).
- **Fases futuras:** Interfaz gráfica de escritorio/móvil y web.
- **Regla de oro de arquitectura:** La capa `core/` contiene la lógica pura de cálculo de edad, ordenamiento, validación y persistencia. No debe importar `argparse`, ni ejecutar `print()`, `input()` o `sys.exit()`. Todo intercambio de datos con la interfaz es mediante objetos, métodos y excepciones.

---

## 2. Reglas de Negocio del Core
1. **Modelo de Memoria (`Memory` / `Record`):**
   - `year` (int, obligatorio): Año del suceso.
   - `month` (Optional[int], opcional, rango 1-12): Mes del suceso.
   - `description` (str, obligatorio): Texto descriptivo del recuerdo.
   - `created_at` (datetime): Timestamp de creación del registro.
2. **Perfil / Configuración de Usuario (`UserProfile`):**
   - `birth_year` (Optional[int]): Año de nacimiento base para estimar la edad en cada evento.
   - `birth_month` (Optional[int], rango 1-12): Mes de nacimiento para cálculo exacto de edad.
3. **Cálculo de Edad:**
   - Si no hay año de nacimiento configurado, el campo de edad se computa como `None`.
   - Si están presentes tanto el mes del evento como el mes de nacimiento, la edad exacta se calcula restando 1 si el cumpleaños aún no ocurrió en dicho año (`event.month < birth_month`).
   - Si falta el mes del evento o de nacimiento, se estima como `event.year - birth_year`.
4. **Ordenamiento de la Línea de Tiempo:**
   - Criterio ascendente (de menor a mayor): primero por `year`, luego por `month` (los registros con mes `None` se ubican al final del año de forma consistente).
5. **Persistencia inicial:**
   - Guardado local simple desacoplado mediante un repositorio (JSON o SQLite local en formato estándar), administrado por una interfaz o servicio en `core/storage.py`.

---

## 3. Estructura del Proyecto
```text
novildo/
├── core/
│   ├── __init__.py
│   ├── models.py          # Data classes: Memory, UserProfile
│   ├── services.py        # Casos de uso: registrar recuerdo, calcular edad, ordenar línea
│   └── storage.py         # Guardado y carga (JSON/SQLite) sin acoplar a CLI
├── interfaces/
│   ├── __init__.py
│   └── cli/
│       ├── __init__.py
│       ├── formatters.py  # Renderizado de tablas/listas para la terminal
│       └── main.py        # Parser de comandos (add, list, profile)
├── tests/
│   ├── test_core/
│   └── test_cli/
├── AGENTS.md
├── .gitignore
├── requirements.txt
└── main.py                # Wrapper raíz que invoca interfaces.cli.main
```
