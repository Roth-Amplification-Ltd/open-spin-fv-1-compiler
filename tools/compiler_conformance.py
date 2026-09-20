#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Authoritative open-spin-fv1 differential conformance against SpinAsm 1.1.31.

Only genuine Spin Semiconductor SpinAsm output can establish compatibility.
The historical Python assembler is optional diagnostic context and can never
turn a native/official match into a failure.
"""
from __future__ import annotations
import argparse
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PROGRAM_BYTES = 512
PROGRAM_WORDS = 128
BANK_SLOTS = 8
BANK_BYTES = PROGRAM_BYTES * BANK_SLOTS


@dataclasses.dataclass(frozen=True)
class Case:
    source: Path
    rel: str
    stem_key: str
    source_sha256: str


def die(message: str, code: int = 2):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_checked(argv: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(argv)}\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
        )
    return proc


def discover_cases(repo: Path, explicit: list[str]) -> list[Case]:
    if explicit:
        sources = []
        for raw in explicit:
            p = Path(raw)
            if not p.is_absolute():
                p = repo / p
            if not p.is_file():
                die(f"source not found: {p}")
            sources.append(p.resolve())
    else:
        sources = []
        examples = repo / "examples"
        if examples.is_dir():
            sources.extend(
                p.resolve() for p in sorted(examples.rglob("*.spn"))
                if "compiled" not in p.parts
            )
        corpus = repo / "conformance" / "corpus"
        if corpus.is_dir():
            sources.extend(p.resolve() for p in sorted(corpus.glob("*.spn")))

    cases: list[Case] = []
    seen = set()
    for source in sources:
        try:
            rel = source.relative_to(repo).as_posix()
        except ValueError:
            rel = source.name
        if rel in seen:
            continue
        seen.add(rel)
        stem_key = rel[:-4] if rel.lower().endswith(".spn") else rel
        cases.append(Case(source, rel, stem_key, sha256(source.read_bytes())))
    if not cases:
        die("no .spn compiler-conformance cases found")
    return cases


def validate_program(data: bytes, label: str) -> None:
    if len(data) != PROGRAM_BYTES:
        raise ValueError(f"{label}: expected {PROGRAM_BYTES} bytes, got {len(data)}")


def compile_native(cli: Path, source: Path, output: Path) -> bytes:
    output.parent.mkdir(parents=True, exist_ok=True)
    run_checked([str(cli), "assemble", str(source), str(output)])
    data = output.read_bytes()
    validate_program(data, f"native output for {source.name}")
    return data


def compile_python(assembler: Path, source: Path, output: Path) -> bytes:
    output.parent.mkdir(parents=True, exist_ok=True)
    run_checked([sys.executable, str(assembler), str(source), str(output)])
    data = output.read_bytes()
    validate_program(data, f"Python output for {source.name}")
    return data


def intel_hex_to_bytes(path: Path) -> tuple[int, bytes]:
    memory: dict[int, int] = {}
    upper_linear = 0
    upper_segment = 0
    eof_seen = False

    for line_no, raw in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if not line.startswith(":"):
            raise ValueError(f"{path}:{line_no}: not an Intel HEX record")
        try:
            record = bytes.fromhex(line[1:])
        except ValueError as exc:
            raise ValueError(f"{path}:{line_no}: invalid hexadecimal data") from exc
        if len(record) < 5:
            raise ValueError(f"{path}:{line_no}: record too short")
        count = record[0]
        if len(record) != count + 5:
            raise ValueError(f"{path}:{line_no}: malformed byte count")
        if sum(record) & 0xFF:
            raise ValueError(f"{path}:{line_no}: Intel HEX checksum mismatch")

        address = (record[1] << 8) | record[2]
        rectype = record[3]
        payload = record[4:4+count]
        if rectype == 0x00:
            base = upper_linear + upper_segment + address
            for i, byte in enumerate(payload):
                a = base + i
                if a in memory and memory[a] != byte:
                    raise ValueError(f"{path}:{line_no}: overlapping conflicting data at 0x{a:X}")
                memory[a] = byte
        elif rectype == 0x01:
            eof_seen = True
            break
        elif rectype == 0x02:
            if count != 2:
                raise ValueError(f"{path}:{line_no}: malformed extended segment record")
            upper_segment = int.from_bytes(payload, "big") << 4
            upper_linear = 0
        elif rectype == 0x04:
            if count != 2:
                raise ValueError(f"{path}:{line_no}: malformed extended linear record")
            upper_linear = int.from_bytes(payload, "big") << 16
            upper_segment = 0
        elif rectype in (0x03, 0x05):
            continue
        else:
            raise ValueError(f"{path}:{line_no}: unsupported Intel HEX record type 0x{rectype:02X}")

    if not memory:
        raise ValueError(f"{path}: no Intel HEX data records found")
    if not eof_seen:
        raise ValueError(f"{path}: missing Intel HEX EOF record")

    lo, hi = min(memory), max(memory)
    for a in range(lo, hi + 1):
        if a not in memory:
            raise ValueError(f"{path}: data is not contiguous; missing 0x{a:X}")
    return lo, bytes(memory[a] for a in range(lo, hi + 1))


def normalize_official_bank(path: Path) -> tuple[int, bytes]:
    base, raw = intel_hex_to_bytes(path)
    if len(raw) < BANK_BYTES:
        raise ValueError(f"{path}: official HEX contains {len(raw)} bytes; need {BANK_BYTES}")
    return base, raw[:BANK_BYTES]


def words(data: bytes) -> list[int]:
    validate_program(data, "program")
    return [int.from_bytes(data[i:i+4], "big") for i in range(0, len(data), 4)]


def diagnose(lhs: bytes, rhs: bytes, lhs_name: str, rhs_name: str) -> str:
    if lhs == rhs:
        return "byte-identical"
    lw, rw = words(lhs), words(rhs)
    mismatch = [i for i, (a, b) in enumerate(zip(lw, rw)) if a != b]
    samples = " | ".join(
        f"word[{i:03d}] {lhs_name}=0x{lw[i]:08X} {rhs_name}=0x{rw[i]:08X}"
        for i in mismatch[:8]
    )
    return f"{len(mismatch)} word(s) differ; {samples}"


def batch_cases(cases: list[Case]) -> list[list[Case]]:
    return [cases[i:i+BANK_SLOTS] for i in range(0, len(cases), BANK_SLOTS)]


def prepare_official(work: Path, cases: list[Case]) -> None:
    prep = work / "official-input"
    out = work / "official-output"
    if prep.exists():
        shutil.rmtree(prep)
    prep.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    all_manifest = {
        "format": 2,
        "target": "Spin Semiconductor SpinAsm 1.1.31",
        "program_bytes": PROGRAM_BYTES,
        "bank_slots": BANK_SLOTS,
        "cases": len(cases),
        "batches": [],
    }

    for batch_index, batch in enumerate(batch_cases(cases)):
        name = f"batch-{batch_index:03d}"
        bd = prep / name
        bd.mkdir(parents=True)
        slots = []
        for slot, case in enumerate(batch):
            dst_name = f"slot{slot}_{Path(case.rel).name}"
            shutil.copy2(case.source, bd / dst_name)
            slots.append({
                "slot": slot,
                "source": case.rel,
                "source_sha256": case.source_sha256,
                "prepared_file": dst_name,
            })
        manifest = {"batch": name, "official_hex": f"{name}.hex", "slots": slots}
        (bd / "slots.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        all_manifest["batches"].append(manifest)

        lines = [
            f"open-spin-fv1 / SpinAsm 1.1.31 differential batch: {name}",
            "",
            "1. Create/open an 8-slot project in genuine SpinAsm 1.1.31.",
            "2. Put these exact files into the matching slots:",
        ]
        for item in slots:
            lines.append(f"   slot {item['slot']}: {item['prepared_file']}  sha256={item['source_sha256']}")
        lines += [
            "3. Leave unused slots empty.",
            "4. Enable Intel HEX output and build.",
            f"5. Copy the resulting HEX to ../../official-output/{name}.hex",
            "",
            "DO NOT edit the prepared sources. Their SHA-256 values are provenance.",
        ]
        (bd / "README-OFFICIAL-SPINASM.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    (prep / "manifest.json").write_text(json.dumps(all_manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(cases)} case(s) in {len(batch_cases(cases))} official SpinAsm batch(es)")
    print(f"Official input:  {prep}")
    print(f"Official output: {out}")


def load_official_slots(work: Path, cases: list[Case]) -> tuple[dict[str, bytes], dict[str, str], list[str]]:
    out = work / "official-output"
    official: dict[str, bytes] = {}
    batch_sha: dict[str, str] = {}
    notes: list[str] = []
    for batch_index, batch in enumerate(batch_cases(cases)):
        name = f"batch-{batch_index:03d}"
        hp = out / f"{name}.hex"
        if not hp.is_file():
            notes.append(f"{name}: missing")
            continue
        base, bank = normalize_official_bank(hp)
        digest = sha256(hp.read_bytes())
        notes.append(f"{name}: base=0x{base:X} sha256={digest}")
        for slot, case in enumerate(batch):
            start = slot * PROGRAM_BYTES
            official[case.stem_key] = bank[start:start+PROGRAM_BYTES]
            batch_sha[case.stem_key] = digest
    return official, batch_sha, notes


def render_report(rows: list[dict], notes: list[str]) -> str:
    total = len(rows)
    official_ok = sum(r["official_status"] == "PASS" for r in rows)
    pending = sum(r["official_status"] == "PENDING" for r in rows)
    failed = sum(r["official_status"] == "FAIL" or r["native_status"] == "FAIL" for r in rows)
    if failed:
        verdict = "FAIL"
    elif pending:
        verdict = "INCOMPLETE - official SpinAsm output missing"
    else:
        verdict = "PASS - native output is byte-identical to genuine SpinAsm 1.1.31"

    lines = [
        "# open-spin-fv1 SpinAsm Conformance Report", "",
        f"**Verdict:** {verdict}", "",
        f"- Corpus: {total}",
        f"- Native vs official PASS: {official_ok}/{total}",
        f"- Official pending: {pending}/{total}",
        "- Python assembler: diagnostic only; never authoritative",
        "", "## Results", "",
        "| Source | Native | Official/native | Python diagnostic | Native SHA-256 |",
        "|---|---:|---:|---:|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['source']}` | {r['native_status']} | {r['official_status']} | "
            f"{r['python_status']} | `{r['native_sha256'][:16]}…` |"
        )
    problems = [r for r in rows if r["details"]]
    if problems:
        lines += ["", "## Differences / diagnostics", ""]
        for r in problems:
            lines += [f"### `{r['source']}`", ""]
            lines.extend(f"- {d}" for d in r["details"])
            lines.append("")
    if notes:
        lines += ["", "## Official HEX ingestion", ""]
        lines.extend(f"- {n}" for n in notes)
    lines += [
        "", "## Authority contract", "",
        "PASS requires every native 512-byte output to equal the corresponding",
        "genuine Spin Semiconductor SpinAsm 1.1.31 EEPROM slot byte-for-byte.",
        "Python output may disagree or fail to compile without changing that verdict.",
    ]
    return "\n".join(lines) + "\n"


def command_run(args: argparse.Namespace) -> int:
    repo = args.repo.resolve()
    work = args.work.resolve()
    cases = discover_cases(repo, args.source)
    native_cli = args.native.resolve()
    python_assembler = args.python_assembler.resolve() if args.python_assembler else None

    if not native_cli.is_file():
        die(f"native compiler CLI not found: {native_cli}")
    if not os.access(native_cli, os.X_OK):
        die(f"native compiler CLI is not executable: {native_cli}")

    official, _, notes = load_official_slots(work, cases)
    generated = work / "generated"
    rows = []
    hard_fail = False
    pending = False

    for index, case in enumerate(cases, 1):
        safe = case.stem_key.replace("/", "__")
        details: list[str] = []
        print(f"[{index:02d}/{len(cases):02d}] {case.rel}")
        try:
            native = compile_native(native_cli, case.source, generated / "native" / f"{safe}.bin")
            native_status = "PASS"
            native_sha = sha256(native)
        except Exception as exc:
            rows.append({
                "source": case.rel, "native_status": "FAIL", "official_status": "N/A",
                "python_status": "N/A", "native_sha256": "", "details": [str(exc)],
            })
            hard_fail = True
            continue

        python_status = "SKIP"
        if python_assembler and python_assembler.is_file():
            try:
                py = compile_python(python_assembler, case.source, generated / "python" / f"{safe}.bin")
                if py == native:
                    python_status = "PASS"
                else:
                    python_status = "DIFF"
                    details.append("diagnostic Python differs: " + diagnose(native, py, "native", "python"))
            except Exception as exc:
                python_status = "ERROR"
                details.append(f"diagnostic Python error: {exc}")

        off = official.get(case.stem_key)
        if off is None:
            official_status = "PENDING"
            pending = True
        elif off == native:
            official_status = "PASS"
        else:
            official_status = "FAIL"
            hard_fail = True
            details.append("AUTHORITATIVE mismatch: " + diagnose(native, off, "native", "official"))

        rows.append({
            "source": case.rel,
            "native_status": native_status,
            "official_status": official_status,
            "python_status": python_status,
            "native_sha256": native_sha,
            "details": details,
        })

    work.mkdir(parents=True, exist_ok=True)
    (work / "report.md").write_text(render_report(rows, notes), encoding="utf-8")
    (work / "report.json").write_text(
        json.dumps({"format": 2, "rows": rows, "official_notes": notes}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Markdown report: {work / 'report.md'}")
    print(f"JSON report:     {work / 'report.json'}")

    if hard_fail:
        print("Compiler conformance: FAIL")
        return 1
    if pending:
        print("Compiler conformance: INCOMPLETE - official SpinAsm output missing")
        return 3
    print("Compiler conformance: PASS - byte-identical to genuine SpinAsm 1.1.31")
    return 0


def command_seal(args: argparse.Namespace) -> int:
    repo = args.repo.resolve()
    work = args.work.resolve()
    cases = discover_cases(repo, args.source)
    official, batch_sha, notes = load_official_slots(work, cases)
    missing = [c.rel for c in cases if c.stem_key not in official]
    if missing:
        die("cannot seal; official output missing for: " + ", ".join(missing))

    golden = repo / "conformance" / "golden"
    if golden.exists():
        shutil.rmtree(golden)
    golden.mkdir(parents=True)
    rows = []
    for case in cases:
        data = official[case.stem_key]
        safe = case.stem_key.replace("/", "__") + ".bin"
        gp = golden / safe
        gp.write_bytes(data)
        rows.append({
            "source": case.rel,
            "source_sha256": case.source_sha256,
            "golden": gp.relative_to(repo).as_posix(),
            "golden_sha256": sha256(data),
            "official_hex_sha256": batch_sha[case.stem_key],
            "target": "Spin Semiconductor SpinAsm 1.1.31",
        })
    manifest = {
        "format": 1,
        "target": "Spin Semiconductor SpinAsm 1.1.31",
        "cases": rows,
        "notes": notes,
    }
    (golden / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"SEALED {len(rows)} official program images under {golden}")
    print("Review redistribution/licensing policy before committing derived golden binaries.")
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="open-spin-fv1 differential SpinAsm conformance")
    sub = p.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", type=Path, default=Path.cwd())
    common.add_argument("--work", type=Path, default=Path("build/compiler-conformance"))
    common.add_argument("--source", action="append", default=[])

    sub.add_parser("prepare-official", parents=[common])

    run = sub.add_parser("run", parents=[common])
    run.add_argument("--native", type=Path, default=Path("build/open-spin-fv1"))
    run.add_argument("--python-assembler", type=Path, default=Path("tools/fv1_assembler.py"))

    seal = sub.add_parser("seal-official", parents=[common])
    return p


def main() -> int:
    args = parser().parse_args()
    args.repo = args.repo.resolve()
    if not args.work.is_absolute():
        args.work = args.repo / args.work
    if args.command == "prepare-official":
        prepare_official(args.work, discover_cases(args.repo, args.source))
        return 0
    if args.command == "run":
        if not args.native.is_absolute():
            args.native = args.repo / args.native
        if args.python_assembler and not args.python_assembler.is_absolute():
            args.python_assembler = args.repo / args.python_assembler
        return command_run(args)
    if args.command == "seal-official":
        return command_seal(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
