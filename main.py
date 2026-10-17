#!/usr/bin/env python3
"""Wrapper raíz para ejecutar la aplicación Novildo.
Invoca interfaces.cli.main.cli_main.
"""

import sys
from interfaces.cli.main import cli_main

if __name__ == "__main__":
    sys.exit(cli_main())
