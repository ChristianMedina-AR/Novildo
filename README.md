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
│   ├── models.py          # Clases Memory y UserProfile
│   ├── services.py        # Casos de uso: registrar recuerdo, calcular edad, ordenar línea
│   └── storage.py         # Repositorio desacoplado (JSONStorage e InMemoryStorage)
├── interfaces/
│   ├── __init__.py
│   └── cli/
│       ├── __init__.py
│       ├── formatters.py  # Renderizado y formato tabular para la consola
│       └── main.py        # Parser de comandos (add, list, profile)
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

Todos los comandos admiten alias cortos (`-y`, `-m`, `-d`, `-b`, `-c`) para mayor rapidez y comodidad al escribir.

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

### 2. Registrar recuerdos (`add`)

Con alias cortos (`-y`, `-m`, `-d`):
```bash
python3 main.py add -y 2005 -m 3 -d "Comencé la escuela primaria"
```

Con argumentos completos:
```bash
python3 main.py add --year 2005 --month 3 --description "Comencé la escuela primaria"
```

Con año únicamente (mes opcional):
```bash
python3 main.py add -y 2013 -d "Terminé el secundario"
```

### 3. Listar la línea de tiempo (`list`)

Muestra la tabla cronológica con el identificador corto (`ID`) asignado a cada recuerdo:
```bash
python3 main.py list
```

Listar del más reciente al más antiguo (descendente, con `-d` o `--desc`):
```bash
python3 main.py list -d
```

### 4. Editar un recuerdo (`edit` o `update`)

Permite actualizar el año (`-y`), mes (`-m`), descripción (`-d`) o eliminar el mes (`--clear-month`) usando el `ID` o prefijo único:
```bash
# Modificar descripción y mes
python3 main.py edit e77b1863 -m 3 -d "Entré a la UNAHUR"

# Quitar el mes asignado
python3 main.py edit e77b1863 --clear-month
```

### 5. Eliminar un recuerdo (`delete` o `rm`)

Elimina un recuerdo existente a partir de su `ID`:
```bash
python3 main.py delete e77b1863
```
O con el alias corto:
```bash
python3 main.py rm e77b1863
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
