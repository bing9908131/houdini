import os
import sys
from urllib.parse import unquote


def _script_dir():
    file_path = globals().get("__file__")
    if file_path:
        return os.path.dirname(os.path.abspath(file_path))

    try:
        import hou

        prefs = hou.getenv("HOUDINI_USER_PREF_DIR")
        if prefs:
            return os.path.join(prefs, "scripts")
    except Exception:
        pass

    return os.getcwd()


SCRIPT_DIR = _script_dir()
TOOL_DIR = os.path.join(SCRIPT_DIR, "houdini_drag_import")
if TOOL_DIR not in sys.path:
    sys.path.append(TOOL_DIR)

import drag_file_importer


def _normalize_dropped_item(item):
    if not item:
        return None

    path = str(item).strip()
    if not path:
        return None

    lower = path.lower()
    if lower.startswith("file:///"):
        path = path[8:]
    elif lower.startswith("file://"):
        path = path[7:]

    path = unquote(path).replace("\\", "/")

    if len(path) > 3 and path[0] == "/" and path[2] == ":":
        path = path[1:]

    return path


def _dropped_paths(file_list):
    paths = []
    for item in file_list or []:
        path = _normalize_dropped_item(item)
        if path:
            paths.append(path)
    return paths


def _display_error(message):
    try:
        import hou

        hou.ui.displayMessage(message)
    except Exception:
        pass


def dropAccept(file_list):
    paths = _dropped_paths(file_list)
    if not paths:
        return False

    try:
        drag_file_importer.import_external_drop_to_active_network(paths)
    except Exception as exc:
        _display_error("Drag import failed:\n{}".format(exc))

    return True
