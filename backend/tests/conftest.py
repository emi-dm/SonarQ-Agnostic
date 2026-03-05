import os
import sys

# ensure the root src package is importable during tests
project_root = os.path.dirname(os.path.dirname(__file__))
src_path = os.path.normpath(os.path.join(project_root, "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
