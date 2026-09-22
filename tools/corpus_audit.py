#!/usr/bin/env python3
import hashlib, json, sys
from pathlib import Path

POS={"alias:ABSA","alias:CLR","alias:LDAX","alias:NOP","alias:NOT","boundary:SKP-offset-0","boundary:SKP-offset-1","boundary:SKP-offset-63","boundary:WLDR-rate-min","boundary:WLDR-rate-max","boundary:WLDS-rate-zero","cho:COS0-alias","cho:COS1-alias","cho:SOF-explicit-offset","directive:EQU-infix","directive:EQU-prefix","directive:MEM-infix","directive:MEM-prefix","extension:RAW","memory:end","memory:mid","memory:start","opcode:AND","opcode:CHO-RDA","opcode:CHO-RDAL","opcode:CHO-SOF","opcode:EXP","opcode:JAM","opcode:LOG","opcode:MAXX","opcode:MULX","opcode:OR","opcode:RDA","opcode:RDAX","opcode:RDFX","opcode:RMPA","opcode:SKP","opcode:SOF","opcode:WLDR","opcode:WLDS","opcode:WRA","opcode:WRAP","opcode:WRAX","opcode:WRHX","opcode:WRLX","opcode:XOR","quantization:truncate-toward-zero","expression:divide","expression:bitwise-not","mask:real-positive-max","label:over-32","wlds:real-amplitude","wldr:real-rate"}
REJ={"reject:expression-multiply","reject:expression-floor-divide","reject:expression-power","reject:expression-shift","reject:expression-INT","reject:literal-underscore","reject:literal-scientific","reject:real-bitmask-negative","reject:label-leading-underscore","reject:cho-rdal-explicit-flags","reject:cho-sof-missing-offset","reject:wldr-below-min"}

def main():
    repo=Path.cwd(); mp=repo/"conformance/corpus-manifest.json"
    if not mp.is_file(): return 1
    cases=json.loads(mp.read_text())["cases"]; pos=set(); rej=set(); tiers={}; errors=[]
    for c in cases:
        p=repo/c["path"]
        if not p.is_file(): errors.append("missing "+c["path"]); continue
        if hashlib.sha256(p.read_bytes()).hexdigest()!=c["sha256"]: errors.append("sha drift "+c["path"])
        tiers[c["tier"]]=tiers.get(c["tier"],0)+1
        if c["tier"] in ("official","local"): pos.update(c["covers"])
        if c["tier"]=="rejection": rej.update(c["covers"])
    if POS-pos: errors.append("missing positive: "+", ".join(sorted(POS-pos)))
    if REJ-rej: errors.append("missing rejection: "+", ".join(sorted(REJ-rej)))
    if tiers.get("official",0)<19: errors.append("official count")
    if tiers.get("rejection",0)<12: errors.append("rejection count")
    if tiers.get("local",0)<1: errors.append("local count")
    if errors:
        for e in errors: print("ERROR:",e,file=sys.stderr)
        return 1
    print(f"CORPUS AUDIT PASS cases={len(cases)} official={tiers.get('official',0)} local={tiers.get('local',0)} rejection={tiers.get('rejection',0)} positive_coverage={len(pos)} rejection_coverage={len(rej)}")
    return 0
if __name__=="__main__": raise SystemExit(main())
