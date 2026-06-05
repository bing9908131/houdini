# Py_untriangulate

Py_untriangulate is a Houdini SOP HDA for rebuilding quad flow from triangulated meshes.

It is designed for cases where a model has already been triangulated and the original
quad topology is no longer available. The tool focuses on practical cleanup with a
small UI instead of exposing every internal scoring parameter.

## Install

Copy the HDA into your Houdini user preference `otls` folder:

```text
Documents/houdini21.0/otls/Py_untriangulate.hda
```

Restart Houdini, or use **Assets > Refresh Asset Libraries**.

## Houdini Node

Create this SOP node:

```text
Py_untriangulate
```

Current asset type:

```text
pyl::Py_untriangulate::1.0
```

## Controls

- `Method`: automatic cleanup mode selection, with manual cleanup/flow modes available.
- `Cleanup Amount`: conservative, balanced, or strong cleanup.
- `Iterations`: automatic, 1 pass, 2 passes, or 3 passes.
- `Guide / Keep Edge Group`: optional edge group to guide or preserve important edges.

## Features

- Reconstructs triangle pairs into quads without using Houdini Divide reconstruction.
- Uses automatic guide flow detection for common triangulated surface patterns.
- Supports UV boundary preference so UV seams can influence candidate selection.
- Includes hidden symmetry assist for objects that are approximately mirrored around
  an offset X/Y/Z-aligned center plane.
- Keeps the visible UI compact for day-to-day use.

## Notes

This is an experimental Houdini 21.0 HDA. It performs best on meshes that were
triangulated from quad-based topology. Highly irregular triangulation, arbitrary
rotated symmetry planes, or very noisy geometry may still require manual guide edges.

