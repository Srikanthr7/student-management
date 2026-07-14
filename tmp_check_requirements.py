from pathlib import Path
from tempfile import NamedTemporaryFile
import subprocess
import sys

text = Path('requirements.txt').read_text(encoding='utf-16')
with NamedTemporaryFile('w', delete=False, suffix='.txt', encoding='utf-8') as tmp:
    tmp.write(text)
    tmp_path = tmp.name
proc = subprocess.run([sys.executable, '-m', 'pip', 'install', '--dry-run', '-r', tmp_path], capture_output=True, text=True)
print('returncode:', proc.returncode)
print('stdout:\n', proc.stdout)
print('stderr:\n', proc.stderr)
