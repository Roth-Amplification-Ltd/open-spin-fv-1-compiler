#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil, tarfile, zipfile
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument('--stage',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
ap.add_argument('--version',required=True)
ap.add_argument('--target',required=True)
ap.add_argument('--commit',required=True)
a=ap.parse_args()
a.out.mkdir(parents=True,exist_ok=True)
base=f"open-spin-fv1-{a.version}-{a.target}"
archive=a.out/(base + ('.zip' if a.target.startswith('windows-') else '.tar.gz'))
if archive.exists(): archive.unlink()
if a.target.startswith('windows-'):
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(a.stage.rglob('*')):
            if p.is_file(): z.write(p, Path(base)/p.relative_to(a.stage))
else:
    with tarfile.open(archive,'w:gz') as t:
        t.add(a.stage,arcname=base)
h=hashlib.sha256(archive.read_bytes()).hexdigest()
sha=Path(str(archive)+'.sha256')
sha.write_text(f"{h}  {archive.name}\n",encoding='utf-8')
manifest=Path(str(archive)+'.manifest.json')
manifest.write_text(json.dumps({
    'schema':'open-spin-fv1-release-v1','product':'open-spin-fv1','version':a.version,
    'commit':a.commit,'target':a.target,'archive':archive.name,'sha256':h,
    'compiler_target':'Spin Semiconductor SpinAsm 1.1.31',
    'qualification':'native deterministic corpus + preserved official oracle vectors'
},indent=2)+'\n',encoding='utf-8')
print(archive)
