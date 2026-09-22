#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

def C(path,tier,covers,source):
    return {"path":path,"tier":tier,"covers":covers,"source":source}

CASES = [
C("conformance/corpus/00-register-alu.spn","official",["opcode:RDAX","opcode:RDFX","alias:LDAX","opcode:WRAX","opcode:WRHX","opcode:WRLX","opcode:MAXX","alias:ABSA","opcode:MULX","opcode:LOG","opcode:EXP","opcode:SOF","opcode:AND","alias:CLR","opcode:OR","opcode:XOR","alias:NOT","register:special","register:REG0","register:REG31"],"; Core register/ALU instruction surface.\nRDAX ADCL,-2.0\nRDAX REG31,1.99993896484375\nRDFX REG0,-1.0\nLDAX ADCR\nWRAX DACL,0.0\nWRHX REG1,0.5\nWRLX REG2,-0.5\nMAXX REG3,1.0\nABSA\nMULX POT0\nLOG 1.5,-0.3\nEXP 0.8,0\nSOF 1.5,-0.3\nAND $7FFFFF\nCLR\nOR %000000000000000000000001\nXOR $FFFFFF\nNOT\n"),
C("conformance/corpus/01-delay-memory.spn","official",["opcode:RDA","opcode:RMPA","opcode:WRA","opcode:WRAP","directive:MEM-prefix","directive:MEM-infix","memory:start","memory:mid","memory:end"],"; Delay memory addressing and both documented MEM forms.\nMEM DEL0 32\nDEL1 MEM 64\nRDA DEL0,1.0\nRDA DEL0^,0.5\nRDA DEL0#,-0.5\nRMPA 1.0\nWRA DEL1,0.0\nWRAP DEL1#,1.0\n"),
C("conformance/corpus/02-lfo-control.spn","official",["opcode:WLDS","opcode:WLDR","opcode:JAM","lfo:SIN0","lfo:SIN1","lfo:RMP0","lfo:RMP1","boundary:WLDS-rate-min","boundary:WLDS-rate-max","boundary:WLDR-rate-min","boundary:WLDR-rate-max","boundary:ramp-range-4096","boundary:ramp-range-2048","boundary:ramp-range-1024","boundary:ramp-range-512"],"; LFO setup/control and ramp range encodings.\nWLDS SIN0,1,1\nWLDS SIN1,511,32767\nWLDR RMP0,0,4096\nWLDR RMP1,32767,2048\nWLDR RMP0,-16384,1024\nWLDR RMP1,-1,512\nJAM RMP0\nJAM RMP1\n"),
C("conformance/corpus/03-cho-sine.spn","official",["opcode:CHO-RDA","opcode:CHO-SOF","opcode:CHO-RDAL","cho:SIN","cho:COS","cho:REG","cho:COMPC","cho:COMPA","cho:SIN0","cho:SIN1","cho:COS0-alias","cho:COS1-alias"],"MEM CHOBUF 128\nCHO RDA,SIN0,REG|COMPC,CHOBUF^\nCHO RDA,SIN1,COS|REG|COMPA,CHOBUF^\nCHO SOF,SIN0,REG|COMPC,0\nCHO RDAL,SIN0\nCHO RDAL,COS0\nCHO RDAL,SIN1\nCHO RDAL,COS1\n"),
C("conformance/corpus/04-cho-ramp.spn","official",["opcode:CHO-RDA","opcode:CHO-SOF","opcode:CHO-RDAL","cho:RMP0","cho:RMP1","cho:RPTR2","cho:NA","cho:REG","cho:COMPC","cho:COMPA","cho:SOF-explicit-offset"],"MEM RAMPBUF 256\nCHO RDA,RMP0,REG|COMPC|RPTR2,RAMPBUF\nCHO RDA,RMP1,REG|COMPA|NA,RAMPBUF#\nCHO SOF,RMP0,REG|NA,0\nCHO SOF,RMP1,NA,0\nCHO RDAL,RMP1\n"),
C("conformance/corpus/05-skp-conditions.spn","official",["opcode:SKP","alias:NOP","skp:unconditional","skp:RUN","skp:ZRC","skp:ZRO","skp:GEZ","skp:NEG","skp:combined-flags","boundary:SKP-offset-0","boundary:SKP-offset-1"],"SKP 0,zero\nzero:\nSKP RUN,one\nNOP\none:\nSKP ZRC|ZRO|GEZ|NEG,two\nNOP\ntwo:\nSKP NEG,0\nNOP\n"),
C("conformance/corpus/06-skp-offset-63.spn","official",["opcode:SKP","alias:NOP","boundary:SKP-offset-63","label:forward"],"SKP RUN,far\n"+"NOP\n"*63+"far:\nNOP\n"),
C("conformance/corpus/07-equ-mem-symbols.spn","official",["directive:EQU-prefix","directive:EQU-infix","directive:MEM-prefix","directive:MEM-infix","literal:decimal","literal:hex","literal:binary","expression:add","expression:or","case:insensitive","comment:semicolon","label:same-line"],"; Both documented declaration forms and basic documented numeric forms.\nEQU HALF 0.5\nUNITY EQU 1.0\nEQU HEXVAL $10\nBINVAL EQU %10\nEQU SUM $10+%10\nMEM A 8\nB MEM 8\nstart: rdax adcl,UNITY ; lower-case opcode and inline comment\nSOF HALF,0\nAND HEXVAL|BINVAL\nOR SUM\nRDA A#,0.5\nWRA B,0\nSKP 0,done\ndone: NOP\n"),
C("conformance/corpus/08-fixed-point-boundaries.spn","official",["fixed:S1.9-min","fixed:S1.9-max","fixed:S1.14-min","fixed:S1.14-max","fixed:S.10-min","fixed:S.10-max","fixed:S.15-min","fixed:S.15-max","mask:24bit-min","mask:24bit-max"],"RDA 0,-2.0\nRDA 0,1.998046875\nRDAX REG0,-2.0\nRDAX REG0,1.99993896484375\nSOF -2.0,-1.0\nSOF 1.99993896484375,0.9990234375\nCHO SOF,SIN0,0,-1.0\nCHO SOF,SIN1,0,0.999969482421875\nAND $000000\nOR $FFFFFF\n"),
C("conformance/corpus/09-official-quantization-oracle.spn","official",["oracle:SOF-0.075-0.004","oracle:RDA-minus-0.22","oracle:SOF-minus1-0.999","quantization:truncate-toward-zero"],"SOF 0.075,0.004\nRDA 0,-0.22\nSOF -1.0,0.999\n"),
C("conformance/corpus/10-register-symbol-map.spn","official",["register:SIN0_RATE","register:SIN0_RANGE","register:SIN1_RATE","register:SIN1_RANGE","register:RMP0_RATE","register:RMP0_RANGE","register:RMP1_RATE","register:RMP1_RANGE","register:POT0","register:POT1","register:POT2","register:ADCL","register:ADCR","register:DACL","register:DACR","register:ADDR_PTR","register:REG0","register:REG31"],"CLR\nWRAX SIN0_RATE,0\nWRAX SIN0_RANGE,0\nWRAX SIN1_RATE,0\nWRAX SIN1_RANGE,0\nWRAX RMP0_RATE,0\nWRAX RMP0_RANGE,0\nWRAX RMP1_RATE,0\nWRAX RMP1_RANGE,0\nLDAX POT0\nLDAX POT1\nLDAX POT2\nLDAX ADCL\nLDAX ADCR\nWRAX DACL,0\nWRAX DACR,0\nWRAX ADDR_PTR,0\nLDAX REG0\nLDAX REG31\n"),
C("conformance/corpus/11-padding-and-empty-labels.spn","official",["padding:NOP","label:standalone","label:same-line","case:upper-lower"],"begin:\nNOP\nMiddle: nop\nSKP 0,EndLabel\nEndLabel:\nNOP\n"),
C("conformance/corpus/12-expression-divide.spn","official",["expression:divide"],"EQU X 1/2\nSOF X,0\n"),
C("conformance/corpus/13-expression-bitwise-not.spn","official",["expression:bitwise-not"],"EQU X ~0\nAND X\n"),
C("conformance/corpus/14-real-bitmask-max.spn","official",["mask:real-positive-max"],"OR 0.9999998807907104\n"),
C("conformance/corpus/15-label-over-32.spn","official",["label:over-32"],"ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFG: NOP\n"),
C("conformance/corpus/16-wlds-zero-rate.spn","official",["boundary:WLDS-rate-zero"],"WLDS SIN0,0,1\n"),
C("conformance/corpus/17-wlds-real-amplitude.spn","official",["wlds:real-amplitude"],"WLDS SIN0,1,0.5\n"),
C("conformance/corpus/18-wldr-real-rate.spn","official",["wldr:real-rate"],"WLDR RMP0,0.5,4096\n"),
C("conformance/local/00-raw-extension.spn","local",["extension:RAW"],"RAW $12345678\nRAW $FFFFFFFF\nRAW 0\n"),
C("conformance/rejection/00-expression-multiply.spn","rejection",["reject:expression-multiply"],"EQU X 2*3\nSOF X,0\n"),
C("conformance/rejection/01-expression-floor-divide.spn","rejection",["reject:expression-floor-divide"],"EQU X 7//2\nSOF X,0\n"),
C("conformance/rejection/02-expression-power.spn","rejection",["reject:expression-power"],"EQU X 2**3\nSOF X,0\n"),
C("conformance/rejection/03-expression-shift.spn","rejection",["reject:expression-shift"],"EQU X 1<<4\nAND X\n"),
C("conformance/rejection/04-expression-int.spn","rejection",["reject:expression-INT"],"EQU X INT(1.5)\nSOF X,0\n"),
C("conformance/rejection/05-numeric-underscores.spn","rejection",["reject:literal-underscore"],"EQU X 1_024\nAND X\n"),
C("conformance/rejection/06-scientific-notation.spn","rejection",["reject:literal-scientific"],"SOF 1e-1,0\n"),
C("conformance/rejection/07-real-bitmask-negative.spn","rejection",["reject:real-bitmask-negative"],"AND -1.0\n"),
C("conformance/rejection/08-label-leading-underscore.spn","rejection",["reject:label-leading-underscore"],"_start: NOP\n"),
C("conformance/rejection/09-cho-rdal-explicit-flags.spn","rejection",["reject:cho-rdal-explicit-flags"],"CHO RDAL,SIN0,COS|REG\n"),
C("conformance/rejection/10-cho-sof-missing-offset.spn","rejection",["reject:cho-sof-missing-offset"],"CHO SOF,RMP1,NA\n"),
C("conformance/rejection/11-wldr-below-min.spn","rejection",["reject:wldr-below-min"],"WLDR RMP0,-16385,4096\n"),
]

def h(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()
def manifest(): return {"format":2,"target":"Spin Semiconductor SpinAsm 1.1.31","oracle_pass":"V15","cases":[{"path":c["path"],"tier":c["tier"],"covers":c["covers"],"sha256":h(c["source"])} for c in CASES]}

def generate(repo):
    expected={c["path"] for c in CASES}
    for d in ("corpus","local","rejection","adjudication"):
        p=repo/"conformance"/d
        if p.exists():
            for f in p.glob("*.spn"):
                if f.relative_to(repo).as_posix() not in expected: f.unlink()
    for c in CASES:
        p=repo/c["path"]; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(c["source"].encode("utf-8"))
    (repo/"conformance/corpus-manifest.json").write_bytes((json.dumps(manifest(),indent=2,sort_keys=True)+"\n").encode("utf-8"))

def check(repo):
    ok=True; expected={c["path"] for c in CASES}
    for c in CASES:
        p=repo/c["path"]
        if not p.is_file(): print("MISSING",c["path"],file=sys.stderr); ok=False; continue
        if p.read_text(encoding="utf-8")!=c["source"]: print("DRIFT",c["path"],file=sys.stderr); ok=False
    for d in ("corpus","local","rejection","adjudication"):
        p=repo/"conformance"/d
        if p.is_dir():
            for f in p.glob("*.spn"):
                rel=f.relative_to(repo).as_posix()
                if rel not in expected: print("UNTRACKED CORPUS SOURCE",rel,file=sys.stderr); ok=False
    mp=repo/"conformance/corpus-manifest.json"; exp=json.dumps(manifest(),indent=2,sort_keys=True)+"\n"
    if not mp.is_file() or mp.read_text(encoding="utf-8")!=exp: print("DRIFT conformance/corpus-manifest.json",file=sys.stderr); ok=False
    if ok:
        t={}
        for c in CASES: t[c["tier"]]=t.get(c["tier"],0)+1
        print("CORPUS CHECK PASS "+" ".join(f"{k}={v}" for k,v in sorted(t.items())))
        return 0
    return 1

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",type=Path,default=Path.cwd()); ap.add_argument("--check",action="store_true")
    a=ap.parse_args(); r=a.repo.resolve()
    if a.check: return check(r)
    generate(r); return check(r)
if __name__=="__main__": raise SystemExit(main())
