Houdini Drag Import - minimal install

Copy the contents of the scripts folder into your Houdini user scripts folder.

Example for Houdini 21.0 on Windows:
  Documents/houdini21.0/scripts/

Final layout:
  Documents/houdini21.0/scripts/externaldragdrop.py
  Documents/houdini21.0/scripts/houdini_drag_import/drag_file_importer.py

Restart Houdini after copying.

Behavior:
  - Drop files in /obj: creates a geo node with a file SOP inside.
  - Drop files inside /obj/<geo>: creates a file SOP in that SOP network.
  - Drop image files inside /mat/<redshift_vopnet>: creates redshift::TextureSampler.
