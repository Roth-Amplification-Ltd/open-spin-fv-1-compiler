#!/usr/bin/env python3
"""Generate the deterministic SpinAsm 1.1.31 qualification corpus."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

CASES = [{'path': 'conformance/corpus/00-register-alu.spn', 'tier': 'official', 'covers': ['opcode:RDAX', 'opcode:RDFX', 'alias:LDAX', 'opcode:WRAX', 'opcode:WRHX', 'opcode:WRLX', 'opcode:MAXX', 'alias:ABSA', 'opcode:MULX', 'opcode:LOG', 'opcode:EXP', 'opcode:SOF', 'opcode:AND', 'alias:CLR', 'opcode:OR', 'opcode:XOR', 'alias:NOT', 'register:special', 'register:REG0', 'register:REG31'], 'source': '; Core register/ALU instruction surface.\nRDAX ADCL,-2.0\nRDAX REG31,1.99993896484375\nRDFX REG0,-1.0\nLDAX ADCR\nWRAX DACL,0.0\nWRHX REG1,0.5\nWRLX REG2,-0.5\nMAXX REG3,1.0\nABSA\nMULX POT0\nLOG 1.5,-0.3\nEXP 0.8,0\nSOF 1.5,-0.3\nAND $7FFFFF\nCLR\nOR %000000000000000000000001\nXOR $FFFFFF\nNOT\n'}, {'path': 'conformance/corpus/01-delay-memory.spn', 'tier': 'official', 'covers': ['opcode:RDA', 'opcode:RMPA', 'opcode:WRA', 'opcode:WRAP', 'directive:MEM-prefix', 'directive:MEM-infix', 'memory:start', 'memory:mid', 'memory:end'], 'source': '; Delay memory addressing and both documented MEM forms.\nMEM DEL0 32\nDEL1 MEM 64\nRDA DEL0,1.0\nRDA DEL0^,0.5\nRDA DEL0#,-0.5\nRMPA 1.0\nWRA DEL1,0.0\nWRAP DEL1#,1.0\n'}, {'path': 'conformance/corpus/02-lfo-control.spn', 'tier': 'official', 'covers': ['opcode:WLDS', 'opcode:WLDR', 'opcode:JAM', 'lfo:SIN0', 'lfo:SIN1', 'lfo:RMP0', 'lfo:RMP1', 'boundary:WLDS-rate-min', 'boundary:WLDS-rate-max', 'boundary:WLDR-rate-min', 'boundary:WLDR-rate-max', 'boundary:ramp-range-4096', 'boundary:ramp-range-2048', 'boundary:ramp-range-1024', 'boundary:ramp-range-512'], 'source': '; LFO setup/control and ramp range encodings.\nWLDS SIN0,1,1\nWLDS SIN1,511,32767\nWLDR RMP0,0,4096\nWLDR RMP1,32767,2048\nWLDR RMP0,-32768,1024\nWLDR RMP1,-1,512\nJAM RMP0\nJAM RMP1\n'}, {'path': 'conformance/corpus/03-cho-sine.spn', 'tier': 'official', 'covers': ['opcode:CHO-RDA', 'opcode:CHO-SOF', 'opcode:CHO-RDAL', 'cho:SIN', 'cho:COS', 'cho:REG', 'cho:COMPC', 'cho:COMPA', 'cho:SIN0', 'cho:SIN1', 'cho:COS0-alias', 'cho:COS1-alias'], 'source': 'MEM CHOBUF 128\nCHO RDA,SIN0,REG|COMPC,CHOBUF^\nCHO RDA,SIN1,COS|REG|COMPA,CHOBUF^\nCHO SOF,SIN0,REG|COMPC,0\nCHO RDAL,SIN0\nCHO RDAL,COS0\nCHO RDAL,SIN1\nCHO RDAL,COS1\n'}, {'path': 'conformance/corpus/04-cho-ramp.spn', 'tier': 'official', 'covers': ['opcode:CHO-RDA', 'opcode:CHO-SOF', 'opcode:CHO-RDAL', 'cho:RMP0', 'cho:RMP1', 'cho:RPTR2', 'cho:NA', 'cho:REG', 'cho:COMPC', 'cho:COMPA', 'cho:SOF-default-offset'], 'source': 'MEM RAMPBUF 256\nCHO RDA,RMP0,REG|COMPC|RPTR2,RAMPBUF\nCHO RDA,RMP1,REG|COMPA|NA,RAMPBUF#\nCHO SOF,RMP0,REG|NA,0\nCHO SOF,RMP1,NA\nCHO RDAL,RMP1\n'}, {'path': 'conformance/corpus/05-skp-conditions.spn', 'tier': 'official', 'covers': ['opcode:SKP', 'alias:NOP', 'skp:unconditional', 'skp:RUN', 'skp:ZRC', 'skp:ZRO', 'skp:GEZ', 'skp:NEG', 'skp:combined-flags', 'boundary:SKP-offset-0', 'boundary:SKP-offset-1'], 'source': 'SKP 0,zero\nzero:\nSKP RUN,one\nNOP\none:\nSKP ZRC|ZRO|GEZ|NEG,two\nNOP\ntwo:\nSKP NEG,0\nNOP\n'}, {'path': 'conformance/corpus/06-skp-offset-63.spn', 'tier': 'official', 'covers': ['opcode:SKP', 'alias:NOP', 'boundary:SKP-offset-63', 'label:forward'], 'source': 'SKP RUN,far\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nNOP\nfar:\nNOP\n'}, {'path': 'conformance/corpus/07-equ-mem-symbols.spn', 'tier': 'official', 'covers': ['directive:EQU-prefix', 'directive:EQU-infix', 'directive:MEM-prefix', 'directive:MEM-infix', 'literal:decimal', 'literal:hex', 'literal:binary', 'expression:add', 'expression:or', 'case:insensitive', 'comment:semicolon', 'label:same-line'], 'source': '; Both documented declaration forms and basic documented numeric forms.\nEQU HALF 0.5\nUNITY EQU 1.0\nEQU HEXVAL $10\nBINVAL EQU %10\nEQU SUM $10+%10\nMEM A 8\nB MEM 8\nstart: rdax adcl,UNITY ; lower-case opcode and inline comment\nSOF HALF,0\nAND HEXVAL|BINVAL\nOR SUM\nRDA A#,0.5\nWRA B,0\nSKP 0,done\ndone: NOP\n'}, {'path': 'conformance/corpus/08-fixed-point-boundaries.spn', 'tier': 'official', 'covers': ['fixed:S1.9-min', 'fixed:S1.9-max', 'fixed:S1.14-min', 'fixed:S1.14-max', 'fixed:S.10-min', 'fixed:S.10-max', 'fixed:S.15-min', 'fixed:S.15-max', 'mask:24bit-min', 'mask:24bit-max'], 'source': 'RDA 0,-2.0\nRDA 0,1.998046875\nRDAX REG0,-2.0\nRDAX REG0,1.99993896484375\nSOF -2.0,-1.0\nSOF 1.99993896484375,0.9990234375\nCHO SOF,SIN0,0,-1.0\nCHO SOF,SIN1,0,0.999969482421875\nAND $000000\nOR $FFFFFF\n'}, {'path': 'conformance/corpus/09-official-quantization-oracle.spn', 'tier': 'official', 'covers': ['oracle:SOF-0.075-0.004', 'oracle:RDA-minus-0.22', 'oracle:SOF-minus1-0.999', 'quantization:truncate-toward-zero'], 'source': 'SOF 0.075,0.004\nRDA 0,-0.22\nSOF -1.0,0.999\n'}, {'path': 'conformance/corpus/10-register-symbol-map.spn', 'tier': 'official', 'covers': ['register:SIN0_RATE', 'register:SIN0_RANGE', 'register:SIN1_RATE', 'register:SIN1_RANGE', 'register:RMP0_RATE', 'register:RMP0_RANGE', 'register:RMP1_RATE', 'register:RMP1_RANGE', 'register:POT0', 'register:POT1', 'register:POT2', 'register:ADCL', 'register:ADCR', 'register:DACL', 'register:DACR', 'register:ADDR_PTR', 'register:REG0', 'register:REG31'], 'source': 'CLR\nWRAX SIN0_RATE,0\nWRAX SIN0_RANGE,0\nWRAX SIN1_RATE,0\nWRAX SIN1_RANGE,0\nWRAX RMP0_RATE,0\nWRAX RMP0_RANGE,0\nWRAX RMP1_RATE,0\nWRAX RMP1_RANGE,0\nLDAX POT0\nLDAX POT1\nLDAX POT2\nLDAX ADCL\nLDAX ADCR\nWRAX DACL,0\nWRAX DACR,0\nWRAX ADDR_PTR,0\nLDAX REG0\nLDAX REG31\n'}, {'path': 'conformance/corpus/11-padding-and-empty-labels.spn', 'tier': 'official', 'covers': ['padding:NOP', 'label:standalone', 'label:same-line', 'case:upper-lower'], 'source': 'begin:\nNOP\nMiddle: nop\nSKP 0,EndLabel\nEndLabel:\nNOP\n'}, {'path': 'conformance/local/00-raw-extension.spn', 'tier': 'local', 'covers': ['extension:RAW'], 'source': 'RAW $12345678\nRAW $FFFFFFFF\nRAW 0\n'}, {'path': 'conformance/adjudication/00-expression-multiply.spn', 'tier': 'adjudication', 'covers': ['expression:multiply'], 'source': 'EQU X 2*3\nSOF X,0\n'}, {'path': 'conformance/adjudication/01-expression-divide.spn', 'tier': 'adjudication', 'covers': ['expression:divide'], 'source': 'EQU X 1/2\nSOF X,0\n'}, {'path': 'conformance/adjudication/02-expression-floor-divide.spn', 'tier': 'adjudication', 'covers': ['expression:floor-divide'], 'source': 'EQU X 7//2\nSOF X,0\n'}, {'path': 'conformance/adjudication/03-expression-power.spn', 'tier': 'adjudication', 'covers': ['expression:power'], 'source': 'EQU X 2**3\nSOF X,0\n'}, {'path': 'conformance/adjudication/04-expression-shift.spn', 'tier': 'adjudication', 'covers': ['expression:shift'], 'source': 'EQU X 1<<4\nAND X\n'}, {'path': 'conformance/adjudication/05-expression-bitwise-not.spn', 'tier': 'adjudication', 'covers': ['expression:bitwise-not'], 'source': 'EQU X ~0\nAND X\n'}, {'path': 'conformance/adjudication/06-expression-int.spn', 'tier': 'adjudication', 'covers': ['expression:INT'], 'source': 'EQU X INT(1.5)\nSOF X,0\n'}, {'path': 'conformance/adjudication/07-numeric-underscores.spn', 'tier': 'adjudication', 'covers': ['literal:underscore'], 'source': 'EQU X 1_024\nAND X\n'}, {'path': 'conformance/adjudication/08-scientific-notation.spn', 'tier': 'adjudication', 'covers': ['literal:scientific'], 'source': 'SOF 1e-1,0\n'}, {'path': 'conformance/adjudication/09-raw-pseudo-op.spn', 'tier': 'adjudication', 'covers': ['extension:RAW-official-status'], 'source': 'RAW $12345678\n'}, {'path': 'conformance/adjudication/10-real-bitmask-min.spn', 'tier': 'adjudication', 'covers': ['candidate:real-bitmask'], 'source': 'AND -1.0\n'}, {'path': 'conformance/adjudication/11-real-bitmask-max.spn', 'tier': 'adjudication', 'covers': ['candidate:real-bitmask'], 'source': 'OR 0.9999998807907104\n'}, {'path': 'conformance/adjudication/12-label-leading-underscore.spn', 'tier': 'adjudication', 'covers': ['candidate:label-leading-underscore'], 'source': '_start: NOP\n'}, {'path': 'conformance/adjudication/13-label-over-32.spn', 'tier': 'adjudication', 'covers': ['candidate:label-length'], 'source': 'ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFG: NOP\n'}, {'path': 'conformance/adjudication/14-cho-rdal-explicit-flags.spn', 'tier': 'adjudication', 'covers': ['candidate:cho-rdal-flags'], 'source': 'CHO RDAL,SIN0,COS|REG\n'}, {'path': 'conformance/adjudication/15-wlds-zero-rate.spn', 'tier': 'adjudication', 'covers': ['candidate:wlds-zero-rate'], 'source': 'WLDS SIN0,0,1\n'}, {'path': 'conformance/adjudication/16-wlds-real-amplitude.spn', 'tier': 'adjudication', 'covers': ['candidate:wlds-real-amplitude'], 'source': 'WLDS SIN0,1,0.5\n'}, {'path': 'conformance/adjudication/17-wldr-real-rate.spn', 'tier': 'adjudication', 'covers': ['candidate:wldr-real-rate'], 'source': 'WLDR RMP0,0.5,4096\n'}]

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def manifest() -> dict:
    return {
        "format": 1,
        "target": "Spin Semiconductor SpinAsm 1.1.31",
        "cases": [
            {
                "path": c["path"],
                "tier": c["tier"],
                "covers": c["covers"],
                "sha256": sha256_text(c["source"]),
            }
            for c in CASES
        ],
    }

def generate(repo: Path) -> None:
    for c in CASES:
        p = repo / c["path"]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(c["source"], encoding="utf-8")
    mp = repo / "conformance" / "corpus-manifest.json"
    mp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(json.dumps(manifest(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

def check(repo: Path) -> int:
    ok = True
    for c in CASES:
        p = repo / c["path"]
        if not p.is_file():
            print(f"MISSING {c['path']}", file=sys.stderr)
            ok = False
            continue
        actual = p.read_text(encoding="utf-8")
        if actual != c["source"]:
            print(f"DRIFT {c['path']}", file=sys.stderr)
            ok = False
    mp = repo / "conformance" / "corpus-manifest.json"
    expected = json.dumps(manifest(), indent=2, sort_keys=True) + "\n"
    if not mp.is_file() or mp.read_text(encoding="utf-8") != expected:
        print("DRIFT conformance/corpus-manifest.json", file=sys.stderr)
        ok = False
    if ok:
        by_tier = {}
        for c in CASES:
            by_tier[c["tier"]] = by_tier.get(c["tier"], 0) + 1
        print("CORPUS CHECK PASS " + " ".join(f"{k}={v}" for k,v in sorted(by_tier.items())))
        return 0
    return 1

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    repo = args.repo.resolve()
    if args.check:
        return check(repo)
    generate(repo)
    return check(repo)

if __name__ == "__main__":
    raise SystemExit(main())
