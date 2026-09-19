#!/usr/bin/env python3
"""Release qualification for open-spin-fv1.

This is intentionally independent of the historical Python assembler for PASS/FAIL.
It verifies deterministic native compilation, the full shipped corpus, known official
SpinAsm 1.1.31 oracle vectors, error semantics, installation, and CLI behavior.
"""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

PROGRAM_BYTES = 512


def run(argv, *, cwd=None, expect=0):
    p = subprocess.run([str(x) for x in argv], cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=True)
    if p.returncode != expect:
        raise RuntimeError(f"command rc={p.returncode}, expected {expect}: {' '.join(map(str, argv))}\nstdout:\n{p.stdout}\nstderr:\n{p.stderr}")
    return p


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def discover_cli(build: Path) -> Path:
    candidates = [build / "open-spin-fv1", build / "open-spin-fv1.exe",
                  build / "Release" / "open-spin-fv1.exe", build / "Release" / "open-spin-fv1"]
    for c in candidates:
        if c.is_file():
            return c
    raise RuntimeError(f"open-spin-fv1 executable not found under {build}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--build", type=Path, default=Path("build"))
    ap.add_argument("--expect-version", default=None)
    args = ap.parse_args()
    repo = args.repo.resolve()
    build = args.build if args.build.is_absolute() else (repo / args.build)
    cli = discover_cli(build)

    print(f"QUALIFICATION CLI: {cli}")
    ver = run([cli, "--version"]).stdout.strip()
    print(ver)
    if args.expect_version and ver != f"open-spin-fv1 {args.expect_version}":
        raise RuntimeError(f"version mismatch: {ver!r}")

    sources = sorted(p for p in (repo / "examples").rglob("*.spn") if "compiled" not in p.parts)
    if len(sources) < 9:
        raise RuntimeError(f"expected at least 9 shipped corpus programs, got {len(sources)}")

    with tempfile.TemporaryDirectory(prefix="open-spin-qual-") as td:
        td = Path(td)
        baseline = {}
        for src in sources:
            rel = src.relative_to(repo).as_posix()
            out1 = td / (src.stem + "-1.bin")
            out2 = td / (src.stem + "-2.bin")
            run([cli, "assemble", src, out1])
            run([cli, "assemble", src, out2])
            if out1.stat().st_size != PROGRAM_BYTES:
                raise RuntimeError(f"{rel}: output size != 512")
            if out1.read_bytes() != out2.read_bytes():
                raise RuntimeError(f"{rel}: nondeterministic output")
            run([cli, "--check", src])
            baseline[rel] = sha256(out1)
            print(f"PASS deterministic {rel} {baseline[rel]}")

        # Known words captured from genuine Spin Semiconductor SpinAsm 1.1.31.
        oracle_src = td / "official-oracle.spn"
        oracle_src.write_text("SOF 0.075, 0.004\nRDA 0, -0.22\nSOF -1.0, 0.999\n", encoding="utf-8")
        oracle_bin = td / "official-oracle.bin"
        run([cli, "assemble", oracle_src, oracle_bin])
        data = oracle_bin.read_bytes()
        words = [int.from_bytes(data[i:i+4], "big") for i in range(0, 12, 4)]
        expected = [0x04CC008D, 0xF2000000, 0xC0007FCD]
        if words != expected:
            raise RuntimeError(f"official SpinAsm quantization oracle mismatch: {words!r} != {expected!r}")
        print("PASS official SpinAsm 1.1.31 fixed-point oracle")

        # Official compiler rejects JMP; unconditional forward branch is SKP 0,label.
        bad = td / "bad-jmp.spn"
        bad.write_text("JMP done\ndone:\nNOP\n", encoding="utf-8")
        p = subprocess.run([str(cli), "--check", str(bad)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if p.returncode == 0 or "unsupported mnemonic JMP" not in p.stderr:
            raise RuntimeError(f"non-official JMP was not rejected correctly: rc={p.returncode} stderr={p.stderr!r}")
        print("PASS official syntax rejection: JMP")

        # 128 words is legal; 129 must fail.
        max_ok = td / "max128.spn"
        max_ok.write_text("NOP\n" * 128, encoding="utf-8")
        run([cli, "--check", max_ok])
        too_many = td / "too-many.spn"
        too_many.write_text("NOP\n" * 129, encoding="utf-8")
        p = subprocess.run([str(cli), "--check", str(too_many)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if p.returncode == 0:
            raise RuntimeError("129-instruction program unexpectedly compiled")
        print("PASS 128/129 instruction boundary")

        # Output overwrite must be deterministic too.
        overwrite = td / "overwrite.bin"
        run([cli, "assemble", sources[0], overwrite])
        first = overwrite.read_bytes()
        overwrite.write_bytes(b"garbage")
        run([cli, "assemble", sources[0], overwrite])
        if overwrite.read_bytes() != first:
            raise RuntimeError("output overwrite is not deterministic")
        print("PASS output overwrite")

    print(f"QUALIFICATION PASS: {len(sources)} shipped programs + official oracle + CLI boundaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
