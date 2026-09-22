#!/usr/bin/env python3
"""Release qualification for open-spin-fv1.

The native compiler is authoritative for release behavior. Genuine SpinAsm 1.1.31
outputs, when sealed under conformance/golden/, are the compatibility oracle.
The historical Python assembler is not used by this release qualification path.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

PROGRAM_BYTES = 512


def run(argv, *, cwd=None, expect=0):
    p = subprocess.run([str(x) for x in argv], cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=True)
    if p.returncode != expect:
        raise RuntimeError(
            f"command rc={p.returncode}, expected {expect}: {' '.join(map(str, argv))}\n"
            f"stdout:\n{p.stdout}\nstderr:\n{p.stderr}"
        )
    return p


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def discover_cli(build: Path) -> Path:
    candidates = [
        build / "open-spin-fv1",
        build / "open-spin-fv1.exe",
        build / "Release" / "open-spin-fv1.exe",
        build / "Release" / "open-spin-fv1",
    ]
    for c in candidates:
        if c.is_file():
            return c
    raise RuntimeError(f"open-spin-fv1 executable not found under {build}")


def expect_reject(cli: Path, root: Path, name: str, source: str, contains: str | None = None) -> None:
    p = root / f"reject-{name}.spn"
    p.write_text(source, encoding="utf-8")
    proc = subprocess.run([str(cli), "--check", str(p)], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True)
    if proc.returncode == 0:
        raise RuntimeError(f"{name}: invalid source unexpectedly compiled")
    if contains and contains not in proc.stderr:
        raise RuntimeError(f"{name}: expected diagnostic containing {contains!r}, got {proc.stderr!r}")
    print(f"PASS reject {name}")


def load_corpus_manifest(repo: Path) -> dict:
    p = repo / "conformance" / "corpus-manifest.json"
    if not p.is_file():
        raise RuntimeError("conformance/corpus-manifest.json missing; run tools/generate_conformance_corpus.py")
    data = json.loads(p.read_text(encoding="utf-8"))
    for case in data.get("cases", []):
        src = repo / case["path"]
        if not src.is_file():
            raise RuntimeError(f"corpus source missing: {case['path']}")
        if sha256_path(src) != case["sha256"]:
            raise RuntimeError(f"corpus source hash drift: {case['path']}")
    return data


def sealed_golden_check(repo: Path, native_outputs: dict[str, bytes], require: bool) -> int:
    manifest_path = repo / "conformance" / "golden" / "manifest.json"
    if not manifest_path.is_file():
        if require:
            raise RuntimeError("sealed official golden manifest required but missing")
        print("INFO sealed official golden corpus not present (allowed for current 0.x qualification)")
        return 0

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = data.get("cases", [])
    if not rows:
        raise RuntimeError("sealed golden manifest contains no cases")

    checked = 0
    for row in rows:
        rel = row["source"]
        if rel not in native_outputs:
            raise RuntimeError(f"sealed golden source not compiled by qualification: {rel}")
        src = repo / rel
        if sha256_path(src) != row["source_sha256"]:
            raise RuntimeError(f"sealed golden source provenance mismatch: {rel}")
        gp = repo / row["golden"]
        if not gp.is_file():
            raise RuntimeError(f"sealed golden file missing: {row['golden']}")
        golden = gp.read_bytes()
        if len(golden) != PROGRAM_BYTES:
            raise RuntimeError(f"sealed golden size mismatch: {row['golden']}")
        if sha256_bytes(golden) != row["golden_sha256"]:
            raise RuntimeError(f"sealed golden checksum mismatch: {row['golden']}")
        if native_outputs[rel] != golden:
            raise RuntimeError(f"official SpinAsm sealed golden mismatch: {rel}")
        checked += 1

    expected_official = {
        c["path"] for c in load_corpus_manifest(repo)["cases"] if c["tier"] == "official"
    }
    sealed = {r["source"] for r in rows}
    missing = sorted(expected_official - sealed)
    if missing:
        raise RuntimeError("sealed golden corpus incomplete: " + ", ".join(missing))

    print(f"PASS sealed official SpinAsm golden corpus {checked}/{len(expected_official)}")
    return checked


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--build", type=Path, default=Path("build"))
    ap.add_argument("--expect-version", default=None)
    ap.add_argument("--require-sealed-golden", action="store_true")
    args = ap.parse_args()

    repo = args.repo.resolve()
    build = args.build if args.build.is_absolute() else (repo / args.build)
    cli = discover_cli(build)

    print(f"QUALIFICATION CLI: {cli}")
    ver = run([cli, "--version"]).stdout.strip()
    print(ver)
    if args.expect_version and ver != f"open-spin-fv1 {args.expect_version}":
        raise RuntimeError(f"version mismatch: {ver!r}")

    corpus = load_corpus_manifest(repo)
    official = sorted(repo / c["path"] for c in corpus["cases"] if c["tier"] == "official")
    local = sorted(repo / c["path"] for c in corpus["cases"] if c["tier"] == "local")
    rejection = sorted(repo / c["path"] for c in corpus["cases"] if c["tier"] == "rejection")
    shipped = sorted(p for p in (repo / "examples").rglob("*.spn") if "compiled" not in p.parts)
    if len(shipped) < 9:
        raise RuntimeError(f"expected at least 9 shipped programs, got {len(shipped)}")
    if len(official) < 19:
        raise RuntimeError(f"expected at least 19 official-positive torture cases, got {len(official)}")
    if len(rejection) < 12:
        raise RuntimeError(f"expected at least 12 official-rejection cases, got {len(rejection)}")
    if not local:
        raise RuntimeError("expected at least one local-extension corpus case")

    sources = shipped + official + local
    native_outputs: dict[str, bytes] = {}

    with tempfile.TemporaryDirectory(prefix="open-spin-qual-") as td_raw:
        td = Path(td_raw)

        for index, src in enumerate(sources):
            rel = src.relative_to(repo).as_posix()
            out1 = td / f"{index:03d}-1.bin"
            out2 = td / f"{index:03d}-2.bin"
            run([cli, "assemble", src, out1])
            run([cli, "assemble", src, out2])
            data1 = out1.read_bytes()
            data2 = out2.read_bytes()
            if len(data1) != PROGRAM_BYTES:
                raise RuntimeError(f"{rel}: output size != 512")
            if data1 != data2:
                raise RuntimeError(f"{rel}: nondeterministic output")
            run([cli, "--check", src])
            native_outputs[rel] = data1
            print(f"PASS deterministic {rel} {sha256_bytes(data1)}")

        # Known words captured from genuine Spin Semiconductor SpinAsm 1.1.31.
        oracle_src = td / "official-oracle.spn"
        oracle_src.write_text(
            "SOF 0.075, 0.004\n"
            "RDA 0, -0.22\n"
            "SOF -1.0, 0.999\n",
            encoding="utf-8",
        )
        oracle_bin = td / "official-oracle.bin"
        run([cli, "assemble", oracle_src, oracle_bin])
        data = oracle_bin.read_bytes()
        words = [int.from_bytes(data[i:i+4], "big") for i in range(0, 12, 4)]
        expected = [0x04CC008D, 0xF2000000, 0xC0007FCD]
        if words != expected:
            raise RuntimeError(f"official SpinAsm quantization oracle mismatch: {words!r} != {expected!r}")
        print("PASS official SpinAsm 1.1.31 fixed-point oracle")

        cho_src = td / "cho-v15-positive.spn"
        cho_src.write_text("CHO SOF,RMP1,NA,0\nCHO RDAL,COS0\nCHO RDAL,COS1\n", encoding="utf-8")
        run([cli, "--check", cho_src])
        expect_reject(cli, td, "cho-sof-missing-offset", "CHO SOF,RMP1,NA\n")
        expect_reject(cli, td, "cho-rdal-explicit-flags", "CHO RDAL,SIN0,COS|REG\n")
        print("PASS V15 CHO arity/alias contract")

        # 128 words is legal; 129 must fail.
        max_ok = td / "max128.spn"
        max_ok.write_text("NOP\n" * 128, encoding="utf-8")
        run([cli, "--check", max_ok])
        too_many = td / "too-many.spn"
        too_many.write_text("NOP\n" * 129, encoding="utf-8")
        proc = subprocess.run([str(cli), "--check", str(too_many)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode == 0:
            raise RuntimeError("129-instruction program unexpectedly compiled")
        print("PASS 128/129 instruction boundary")

        # Maximum legal delay allocation and basic register boundary.
        delay_max = td / "delay-max.spn"
        delay_max.write_text("MEM ALL 32767\nRDA ALL#,0\nLDAX 63\n", encoding="utf-8")
        run([cli, "--check", delay_max])
        print("PASS delay/register positive boundaries")

        # Negative/rejection surface. These are native contract gates; official
        # accept/reject adjudication lives separately under conformance/adjudication.
        rejections = [
            ("jmp", "JMP done\ndone:\nNOP\n", "unsupported mnemonic JMP"),
            ("register-negative", "RDAX -1,1.0\n", None),
            ("register-64", "RDAX 64,1.0\n", None),
            ("s1-9-low", "RDA 0,-2.0001\n", None),
            ("s1-9-high", "RDA 0,1.999\n", None),
            ("s1-14-low", "RDAX REG0,-2.0001\n", None),
            ("s1-14-high", "RDAX REG0,2.0\n", None),
            ("s10-low", "SOF 1.0,-1.0001\n", None),
            ("s10-high", "SOF 1.0,1.0\n", None),
            ("s15-low", "WLDS SIN0,1,-1.0001\n", None),
            ("skp-negative", "SKP RUN,-1\n", None),
            ("skp-64", "SKP RUN,64\n", None),
            ("skp-backward-label", "back:\nNOP\nSKP RUN,back\n", None),
            ("wlds-lfo", "WLDS 2,1,0\n", None),
            ("wlds-rate", "WLDS SIN0,512,0\n", None),
            ("wldr-lfo", "WLDR 4,0,4096\n", None),
            ("wldr-rate-high", "WLDR RMP0,32768,4096\n", None),
            ("wldr-rate-low", "WLDR RMP0,-16385,4096\n", None),
            ("wldr-range", "WLDR RMP0,0,123\n", None),
            ("jam-lfo", "JAM 4\n", None),
            ("cho-type", "CHO BAD,SIN0,0,0\n", None),
            ("cho-lfo", "CHO RDA,4,0,0\n", None),
            ("cho-rdal-extra", "CHO RDAL,SIN0,REG,0\n", None),
            ("mem-negative", "MEM BAD -1\n", None),
            ("mem-overflow", "MEM BAD 32768\n", None),
            ("duplicate-label", "x: NOP\nx: NOP\n", None),
            ("undefined-symbol", "RDAX DOES_NOT_EXIST,1.0\n", None),
            ("wrong-operand-count", "SOF 1.0\n", None),
        ]
        for name, source, contains in rejections:
            expect_reject(cli, td, name, source, contains)

        for src in rejection:
            proc = subprocess.run([str(cli), "--check", str(src)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode == 0:
                raise RuntimeError(f"{src.relative_to(repo).as_posix()}: V15-rejected source unexpectedly compiled")
            print(f"PASS V15 reject {src.relative_to(repo).as_posix()}")

        wldr_min = td / "wldr-min.spn"
        wldr_min.write_text("WLDR RMP0,-16384,4096\n", encoding="utf-8")
        run([cli, "--check", wldr_min])
        print("PASS V15 WLDR minimum integer rate -16384")

        # Output overwrite must be deterministic too.
        overwrite = td / "overwrite.bin"
        run([cli, "assemble", sources[0], overwrite])
        first = overwrite.read_bytes()
        overwrite.write_bytes(b"garbage")
        run([cli, "assemble", sources[0], overwrite])
        if overwrite.read_bytes() != first:
            raise RuntimeError("output overwrite is not deterministic")
        print("PASS output overwrite")

        require_golden = args.require_sealed_golden
        if args.expect_version:
            try:
                major = int(args.expect_version.split(".", 1)[0])
            except ValueError:
                major = 0
            if major >= 1:
                require_golden = True
        sealed = sealed_golden_check(repo, native_outputs, require_golden)

    print(
        "QUALIFICATION PASS: "
        f"shipped={len(shipped)} official-torture={len(official)} "
        f"local-extension={len(local)} official-rejection={len(rejection)} sealed-golden={sealed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
