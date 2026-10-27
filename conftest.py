import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để pytest nhận diện các module
sys.path.insert(0, str(Path(__file__).parent))
