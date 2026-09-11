#! python 2
"""Comando Rhino: apre la finestra Libreria Interni."""
import os
import sys

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
if PLUGIN_DIR not in sys.path:
    sys.path.insert(0, PLUGIN_DIR)

prefixes = ("plugin", "ui", "core", "settings", "services")
for name in list(sys.modules.keys()):
    for prefix in prefixes:
        if name == prefix or name.startswith(prefix + "."):
            sys.modules.pop(name, None)
            break

from plugin import OnLoadPlugIn
import plugin as plugin_mod
plugin_mod._library_form = None
OnLoadPlugIn()
