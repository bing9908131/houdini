import os
import re
import hou

MODEL_EXTS = {
    ".obj",
    ".fbx",
    ".bgeo",
    ".bgeo.sc",
    ".stl",
    ".ply",
    ".geo",
}

IMAGE_EXTS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".exr",
    ".tif",
    ".tiff",
    ".bmp",
    ".hdr",
    ".tga",
    ".rat",
}


def _normalize_ext(path):
    lower = path.lower()
    if lower.endswith(".bgeo.sc"):
        return ".bgeo.sc"
    return os.path.splitext(lower)[1]


def _kind(path):
    ext = _normalize_ext(path)
    if ext in MODEL_EXTS:
        return "model"
    if ext in IMAGE_EXTS:
        return "image"
    return None


def _safe_node_name_from_path(path):
    base = os.path.basename(path)
    if base.lower().endswith(".bgeo.sc"):
        base = base[:-8]
    else:
        base = os.path.splitext(base)[0]
    name = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in base)
    while "__" in name:
        name = name.replace("__", "_")
    return name.strip("_") or "imported_file"


def _normalize_slashes(path):
    return (path or "").replace("\\", "/")


def _as_hip_path_if_possible(file_path):
    file_path = _normalize_slashes(file_path)
    if not file_path:
        return file_path

    hip = hou.getenv("HIP") or ""
    hip = _normalize_slashes(hip).rstrip("/")
    if not hip:
        return file_path

    try:
        file_norm = os.path.normcase(os.path.normpath(file_path))
        hip_norm = os.path.normcase(os.path.normpath(hip))
    except Exception:
        return file_path

    hip_norm_slash = _normalize_slashes(hip_norm).rstrip("/")
    file_norm_slash = _normalize_slashes(file_norm)
    if file_norm_slash == hip_norm_slash:
        return "$HIP"
    if not file_norm_slash.startswith(hip_norm_slash + "/"):
        return file_path

    rel = file_norm_slash[len(hip_norm_slash) + 1 :]
    if not rel:
        return "$HIP"
    return "$HIP/" + rel


def _get_active_network_editor():
    desktop = hou.ui.curDesktop()
    if desktop is None:
        return None
    return desktop.paneTabOfType(hou.paneTabType.NetworkEditor)


def _create_file_sop(parent, file_path, node_pos=None):
    node_name = _safe_node_name_from_path(file_path)
    file_node = parent.createNode("file", node_name=node_name)
    file_node.parm("file").set(_as_hip_path_if_possible(file_path))
    if node_pos is not None:
        file_node.setPosition(node_pos)
    else:
        file_node.moveToGoodPosition()
    return file_node


def _create_geo_and_file(obj_parent, file_path, node_pos=None):
    geo_name = _safe_node_name_from_path(file_path)
    geo_node = obj_parent.createNode("geo", node_name=geo_name)

    for child in geo_node.children():
        child.destroy()

    file_node = _create_file_sop(geo_node, file_path)
    out_node = geo_node.createNode("null", "OUT")
    out_node.setInput(0, file_node)
    out_node.setDisplayFlag(True)
    out_node.setRenderFlag(True)
    geo_node.layoutChildren()

    if node_pos is not None:
        geo_node.setPosition(node_pos)
    else:
        geo_node.moveToGoodPosition()

    return geo_node, file_node


def _is_redshift_builder(parent):
    try:
        tname = parent.type().name().lower()
    except Exception:
        tname = ""
    return any(k in tname for k in ["redshift_vopnet", "rs_vopnet"])


def _looks_like_normal_map(file_path):
    name = os.path.basename(file_path).lower()
    stem = os.path.splitext(name)[0]
    parts = [p for p in re.split(r"[\s_\-.]+", stem) if p]

    normal_tokens = {"normal", "normalmap", "nrm", "nor", "norm"}
    if any(p in normal_tokens for p in parts):
        return True

    if parts and parts[-1] == "n":
        return True

    if "normal" in stem and "abnormal" not in stem:
        return True

    if stem.endswith(("nrm", "nor", "norm")):
        return True

    return False


def _unique_child_name(parent, desired):
    if parent.node(desired) is None:
        return desired
    for i in range(2, 200):
        name = f"{desired}{i}"
        if parent.node(name) is None:
            return name
    return desired


def _create_rs_texture(parent, file_path, node_pos=None):
    node_name = _safe_node_name_from_path(file_path)
    tex = None
    for type_name in ["redshift::TextureSampler", "TextureSampler", "rstexture"]:
        try:
            tex = parent.createNode(type_name, node_name=_unique_child_name(parent, node_name))
            break
        except Exception:
            continue

    if tex is None:
        raise hou.Error("找不到可用的 Redshift texture 節點型別")

    norm = _as_hip_path_if_possible(file_path)
    for parm_name in ["tex0", "tex1", "file", "filename"]:
        parm = tex.parm(parm_name)
        if parm is not None:
            parm.set(norm)
            break

    if node_pos is not None:
        tex.setPosition(node_pos)
    else:
        tex.moveToGoodPosition()
    return tex


def _create_rs_normal_map(parent, file_path, node_pos=None):
    base_name = _safe_node_name_from_path(file_path)

    normal_node = None
    for type_name in ["redshift::NormalMap", "NormalMap", "RSNormalMap", "rsnormalmap"]:
        try:
            normal_node = parent.createNode(
                type_name, node_name=_unique_child_name(parent, f"{base_name}_normal")
            )
            break
        except Exception:
            continue

    if normal_node is None:
        raise hou.Error("找不到可用的 Redshift normal map 節點型別")

    norm = _as_hip_path_if_possible(file_path)
    file_set = False
    for parm_name in ["tex0", "tex1", "file", "filename", "texture", "texMap"]:
        parm = normal_node.parm(parm_name)
        if parm is not None:
            parm.set(norm)
            file_set = True
            break

    if node_pos is not None:
        normal_node.setPosition(node_pos)
    else:
        normal_node.moveToGoodPosition()

    if not file_set:
        pos = normal_node.position()
        tex_pos = hou.Vector2(pos[0] - 2.0, pos[1])
        tex = _create_rs_texture(parent, file_path, tex_pos)
        try:
            normal_node.setInput(0, tex)
        except Exception:
            pass

    return normal_node


def import_files_to_network(parent, file_paths, node_pos=None):
    created = []
    parent_path = parent.path()
    category_name = parent.childTypeCategory().name()

    for i, path in enumerate(file_paths):
        kind = _kind(path)
        if not kind:
            continue

        pos = None
        if node_pos is not None:
            pos = hou.Vector2(node_pos[0] + i * 2.0, node_pos[1])

        if kind == "model":
            if category_name == "Sop":
                created.append(_create_file_sop(parent, path, pos))
            elif parent_path == "/obj":
                geo_node, _ = _create_geo_and_file(parent, path, pos)
                created.append(geo_node)
            else:
                raise hou.Error(f"模型匯入目前只支援 SOP network 或 /obj，當前位置：{parent_path}")

        elif kind == "image":
            if _is_redshift_builder(parent):
                if _looks_like_normal_map(path):
                    created.append(_create_rs_normal_map(parent, path, pos))
                else:
                    created.append(_create_rs_texture(parent, path, pos))
            else:
                raise hou.Error(f"貼圖匯入目前只支援 Redshift material builder，當前位置：{parent_path}")

    return created


def import_files_to_active_network(file_paths):
    editor = _get_active_network_editor()
    if editor is None:
        raise hou.Error("找不到 active Network Editor")

    parent = editor.pwd()
    cursor_pos = editor.cursorPosition()
    return import_files_to_network(parent, file_paths, cursor_pos)


def import_paths_as_file_sops_to_network(parent, file_paths, node_pos=None):
    created = []
    parent_path = parent.path()
    category_name = parent.childTypeCategory().name()

    for i, path in enumerate(file_paths):
        if not path:
            continue

        pos = None
        if node_pos is not None:
            pos = hou.Vector2(node_pos[0] + i * 2.0, node_pos[1])

        if category_name == "Sop":
            created.append(_create_file_sop(parent, path, pos))
        elif parent_path == "/obj":
            _, file_node = _create_geo_and_file(parent, path, pos)
            created.append(file_node)
        else:
            raise hou.Error(f"Can only create File SOPs in a SOP network or /obj, not {parent_path}")

    return created


def import_paths_as_file_sops_to_active_network(file_paths):
    editor = _get_active_network_editor()
    if editor is None:
        raise hou.Error("?曆???active Network Editor")

    parent = editor.pwd()
    cursor_pos = editor.cursorPosition()
    return import_paths_as_file_sops_to_network(parent, file_paths, cursor_pos)


def import_external_drop_to_network(parent, file_paths, node_pos=None):
    if _is_redshift_builder(parent):
        created = []
        for i, path in enumerate(file_paths):
            if _kind(path) != "image":
                continue

            pos = None
            if node_pos is not None:
                pos = hou.Vector2(node_pos[0] + i * 2.0, node_pos[1])

            created.append(_create_rs_texture(parent, path, pos))
        return created

    return import_paths_as_file_sops_to_network(parent, file_paths, node_pos)


def import_external_drop_to_active_network(file_paths):
    editor = _get_active_network_editor()
    if editor is None:
        raise hou.Error("?????active Network Editor")

    parent = editor.pwd()
    cursor_pos = editor.cursorPosition()
    return import_external_drop_to_network(parent, file_paths, cursor_pos)
