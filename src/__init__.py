import sys
import os

_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)
_SRC_DIR = os.path.abspath(os.path.dirname(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

