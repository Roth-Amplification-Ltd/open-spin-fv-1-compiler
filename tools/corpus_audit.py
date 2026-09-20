#!/usr/bin/env python3
"""Audit the committed conformance corpus against the compiler surface census."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

REQUIRED_COVERAGE = ['alias:ABSA', 'alias:CLR', 'alias:LDAX', 'alias:NOP', 'alias:NOT', 'boundary:SKP-offset-0', 'boundary:SKP-offset-1', 'boundary:SKP-offset-63', 'cho:COS0-alias', 'cho:COS1-alias', 'cho:SOF-default-offset', 'directive:EQU-infix', 'directive:EQU-prefix', 'directive:MEM-infix', 'directive:MEM-prefix', 'extension:RAW', 'memory:end', 'memory:mid', 'memory:start', 'opcode:AND', 'opcode:CHO-RDA', 'opcode:CHO-RDAL', 'opcode:CHO-SOF', 'opcode:EXP', 'opcode:JAM', 'opcode:LOG', 'opcode:MAXX', 'opcode:MULX', 'opcode:OR', 'opcode:RDA', 'opcode:RDAX', 'opcode:RDFX', 'opcode:RMPA', 'opcode:SKP', 'opcode:SOF', 'opcode:WLDR', 'opcode:WLDS', 'opcode:WRA', 'opcode:WRAP', 'opcode:WRAX', 'opcode:WRHX', 'opcode:WRLX', 'opcode:XOR', 'quantization:truncate-toward-zero']

def main() -> int:
    repo = Path.cwd()
    manifest_path = repo / "conformance" / "corpus-manifest.json"
    if not manifest_path.is_file():
        print("missing conformance/corpus-manifest.json", file=sys.stderr)
        return 1
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    seen_paths = set()
    covered = set()
    tiers = {}
    errors = []
    for case in cases:
        path = case["path"]
        if path in seen_paths:
            errors.append(f"duplicate manifest path: {path}")
        seen_paths.add(path)
        p = repo / path
        if not p.is_file():
            errors.append(f"missing source: {path}")
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if digest != case["sha256"]:
            errors.append(f"sha256 drift: {path}")
        tier = case["tier"]
        tiers[tier] = tiers.get(tier, 0) + 1
        if tier in ("official", "local"):
            covered.update(case.get("covers", []))

    missing = sorted(set(REQUIRED_COVERAGE) - covered)
    if missing:
        errors.append("missing required coverage: " + ", ".join(missing))
    official = tiers.get("official", 0)
    adjudication = tiers.get("adjudication", 0)
    if official < 12:
        errors.append(f"expected >=12 official positive corpus cases, got {official}")
    if adjudication < 10:
        errors.append(f"expected >=10 adjudication cases, got {adjudication}")

    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        return 1

    print(f"CORPUS AUDIT PASS cases={len(cases)} official={official} "
          f"local={tiers.get('local',0)} adjudication={adjudication} coverage={len(covered)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
