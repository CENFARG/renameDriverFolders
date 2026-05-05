import sys
from pathlib import Path

# Add src/ to sys.path so tests can import worker modules
src_dir = Path(__file__).parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
