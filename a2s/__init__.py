"""Evidence-preserving accident reconstruction."""
import os
import sys
from pathlib import Path

# Select the verified client before any a2s module imports carla. The system
# Python on this workstation has an incompatible older development build.
_root=Path(os.environ.get('CARLA_PYTHON_ROOT',str(Path(__file__).resolve().parents[2]/'dynamic_data/dynamic_replay_0508656/runtime')))
if (_root/'carla').is_dir() and sys.version_info[:2]==(3,8):
    sys.path.insert(0,str(_root))
