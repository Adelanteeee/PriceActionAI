from __future__ import annotations
import base64
from pathlib import Path

PKG = Path(__file__).resolve().parent / 'btpkg'
print('PKG_FILES_BEGIN')
for p in sorted(PKG.rglob('*')):
    if p.is_file():
        rel = p.relative_to(PKG)
        print(f'FILE {rel} SIZE {p.stat().st_size}')
        if p.suffix in {'.py','.json'}:
            data = base64.b64encode(p.read_bytes()).decode('ascii')
            print(f'B64 {rel} {data}')
print('PKG_FILES_END')
