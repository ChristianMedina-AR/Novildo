# Novildo

Aplicación de línea de tiempo y memoria personal en Python.

Permite registrar hitos de vida indicando año (obligatorio), mes (opcional) y descripción (obligatoria), para visualizarlos cronológicamente calculando la edad relativa del usuario a partir de su año de nacimiento configurado.

## Características

- **Arquitectura desacoplada:** La lógica del dominio (`core/`) no depende de la interfaz de consola (`interfaces/cli/`), facilitando futuras interfaces gráficas o web.
- **Sin dependencias externas obligatorias:** Funciona directamente con la biblioteca estándar de Python 3.
- **Persistencia local:** Repositorio en archivo JSON estructurado y atómico.
- **Protección de datos sensibles:** Configuración completa en `.gitignore` para secretos, variables de entorno y datos de usuario.

---

## Estructura del Proyecto

```text
novildo/
├── core/
│   ├── __init__.py
│   ├── exceptions.py      # Jerarquía de excepciones de dominio
│   ├── models.py          # Clases Memory, UserProfile, Tag y Person
│   ├── services.py        # Casos de uso: registrar recuerdo, calcular edad, personas, ordenar línea
│   └── storage.py         # Repositorio desacoplado (JSONStorage e InMemoryStorage)
├── interfaces/
│   ├── __init__.py
│   └── cli/
│       ├── __init__.py
│       ├── formatters.py  # Renderizado y formato tabular para la consola
│       └── main.py        # Parser de comandos (add, list, tag, person, profile)
├── tests/
│   ├── test_core/         # Pruebas unitarias de modelos, servicios y persistencia
│   └── test_cli/          # Pruebas unitarias de comandos y formato CLI
├── AGENTS.md              # Directivas del proyecto
├── .gitignore             # Exclusión de archivos sensibles y entornos
├── requirements.txt       # Dependencias de desarrollo y testing
├── README.md
└── main.py                # Wrapper ejecutable raíz
```

---

## Uso de la CLI

Todos los comandos admiten alias cortos (`-y`, `-m`, `-d`, `-t`, `-p`, `-b`, `-c`) para mayor rapidez y comodidad al escribir.

### 1. Configurar o consultar fecha de cumpleaños (Perfil)

Configurar año y mes de nacimiento (`-b`/`-y` para año, `-m` para mes):
```bash
python3 main.py profile -b 1995 -m 5
```

Configurar o actualizar únicamente el mes de nacimiento:
```bash
python3 main.py profile -m 5
```

Consultar perfil actual:
```bash
python3 main.py profile
```

Limpiar únicamente el mes de nacimiento:
```bash
python3 main.py profile --clear-birth-month
```

Limpiar la configuración completa de nacimiento (`-c` o `--clear`):
```bash
python3 main.py profile -c
```

### 2. Crear y administrar etiquetas (`tag` o `t`)

Permite categorizar recuerdos mediante etiquetas con ID autoincremental empezando en 1 hacia adelante, nombre descriptivo y emote/emoji opcional:

Crear etiqueta con nombre y emote:
```bash
python3 main.py tag add "Estudios" -e "🎓"
# O con alias 't':
python3 main.py t add "Trabajo" -e "💼"
# Sintaxis directa:
python3 main.py tag "Personal"
```

Listar todas las etiquetas existentes:
```bash
python3 main.py tag list
# O con alias directo:
python3 main.py t
```

Eliminar una etiqueta por su ID numérico:
```bash
python3 main.py tag delete 1
# O con alias rm:
python3 main.py tag rm 1
```

### 3. Registrar y administrar personas (`person` o `p`)

Permite registrar personas (amigos, familiares, compañeros) con fecha de nacimiento opcional para saber qué edad tenían en cada momento y filtrar recuerdos compartidos:

Registrar persona con año y mes de nacimiento:
```bash
python3 main.py person add "Juan Pérez" -b 1990 -m 5
# O con el alias 'p':
python3 main.py p add "María Gómez" -b 1995 -m 10
# O con año únicamente:
python3 main.py person add "Carlos Ruiz" -b 1988
# Sintaxis directa sin fecha:
python3 main.py person "Laura Solís"
```

Listar todas las personas registradas:
```bash
python3 main.py person list
# O con alias directo:
python3 main.py p
```

Eliminar una persona por su ID numérico (desvincula automáticamente a la persona de todos los recuerdos):
```bash
python3 main.py person delete 1
# O con alias rm:
python3 main.py person rm 1
```

### 4. Registrar recuerdos (`add`)

Con alias cortos (`-y`, `-m`, `-d`, `-t`, `-p`):
```bash
python3 main.py add -y 2005 -m 3 -d "Comencé la escuela primaria" -t 1
```

Vinculando una o varias personas al recuerdo (admiten múltiples IDs separados por espacio o comas):
```bash
# Vincular a una persona (ID 1):
python3 main.py add -y 2015 -m 4 -d "Viaje a Bariloche" -p 1

# Vincular a múltiples personas (IDs 1 y 2):
python3 main.py add -y 2020 -m 6 -d "Fiesta de cumpleaños sorpresa" -p 1 2

# O separados por comas:
python3 main.py add -y 2022 -d "Proyecto universitario" -t 1 -p 1,2
```

Con argumentos completos:
```bash
python3 main.py add --year 2005 --month 3 --description "Comencé la escuela primaria" --tag 1 --people 1 2
```

### 5. Listar la línea de tiempo (`list`)

Muestra la tabla cronológica con el identificador corto (`ID`), edad calculada del usuario, etiqueta asociada y las personas vinculadas con sus respectivas edades en la fecha del evento:
```bash
python3 main.py list
```

Filtrar recuerdos vinculados a una persona por su ID (`-p` o `--person`):
```bash
python3 main.py list -p 1
```

Filtrar recuerdos asociados a una etiqueta por su ID (`-t` o `--tag`):
```bash
python3 main.py list -t 1
```

Filtrar recuerdos por un año específico (`-y` o `--year`):
```bash
python3 main.py list -y 2020
```

Listar del más reciente al más antiguo (descendente, con `-d` o `--desc`):
```bash
python3 main.py list -d
```

### 6. Editar un recuerdo (`edit` o `update`)

Permite actualizar el año (`-y`), mes (`-m`), descripción (`-d`), etiqueta (`-t`), personas vinculadas (`-p`), o limpiar campos (`--clear-month`, `--clear-tag`, `--clear-people`) usando el `ID` o prefijo único:
```bash
# Modificar descripción, etiqueta y vincular a las personas 2 y 3:
python3 main.py edit e77b1863 -m 3 -d "Entré a la UNAHUR" -t 2 -p 2 3

# Desvincular todas las personas del recuerdo:
python3 main.py edit e77b1863 --clear-people

# Quitar la etiqueta asignada:
python3 main.py edit e77b1863 --clear-tag

# Quitar el mes asignado:
python3 main.py edit e77b1863 --clear-month
```

### 7. Eliminar un recuerdo (`delete` o `rm`)

Elimina un recuerdo existente a partir de su `ID`:
```bash
python3 main.py delete e77b1863
```
O con el alias corto:
```bash
python3 main.py rm e77b1863
```

### 7. Consultar la ayuda y argumentos (`help` o `h`)

Muestra la guía completa con la descripción detallada de todos los comandos y sus argumentos:
```bash
python3 main.py help
# O con el alias corto:
python3 main.py h
# O mediante banderas:
python3 main.py -h
python3 main.py --help
```

Ver la ayuda específica de un comando:
```bash
python3 main.py help add
python3 main.py h list
```

### 8. Consultar la versión (`version` o `v`)

Muestra la versión instalada de Novildo:
```bash
python3 main.py version
# O con el alias corto:
python3 main.py v
# O mediante banderas:
python3 main.py -v
python3 main.py --version
```

---

## Ejecutar Pruebas

Con el ejecutor integrado de Python:
```bash
python3 -m unittest discover tests
```

---

## Licencia y Declaración de IA

Este proyecto es software libre y abierto publicado en el dominio público bajo **[The Unlicense](LICENSE)**:
- **Sin obligación de atribución:** No se requiere dar créditos ni atribuir autoría para utilizar, copiar, modificar, fusionar o distribuir el software.
- **Desarrollo asistido por IA:** Concebido y programado en colaboración con el asistente de codificación **Antigravity** (Google DeepMind) utilizando la familia de modelos **Gemini**.
- **Fuentes y originalidad:** Desarrollado desde cero apoyándose exclusivamente en la biblioteca estándar oficial de Python 3, sin reutilización ni copia de código propietario o restringido de terceros.

Para ver el texto completo y las notas legales, consulta el archivo [LICENSE](LICENSE).
