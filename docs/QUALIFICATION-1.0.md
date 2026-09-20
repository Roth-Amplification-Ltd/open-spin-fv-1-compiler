# open-spin-fv1 1.0 qualification plan

The standalone compiler is already released and usable in the 0.x line. The 1.0
gate is deliberately stricter: it must freeze the documented SpinAsm 1.1.31
surface against genuine official compiler output instead of extrapolating from a
small product corpus.

## Qualification tiers

`conformance/corpus/`
: Positive compatibility corpus. These sources are intended to compile in both
  `open-spin-fv1` and genuine SpinAsm 1.1.31 and must become byte-identical
  official differentials before 1.0.

`conformance/local/`
: Deliberate open-spin-fv1 extensions such as `RAW`. They are regression-tested
  locally but are not included in claims of official SpinAsm compatibility.

`conformance/adjudication/`
: One-feature-per-file parser/syntax probes where acceptance by SpinAsm 1.1.31
  has not yet been sealed. Run these individually in the genuine compiler,
  classify accept/reject behavior, then either promote the case into the
  official-positive corpus or add a native rejection/extension gate.

`conformance/golden/`
: Optional sealed 512-byte program images extracted from genuine SpinAsm Intel
  HEX output. The sealing tool records source SHA-256, golden SHA-256 and
  official HEX SHA-256 provenance. Review redistribution policy before
  committing derived binary outputs.

## Pass 1 surface census

The deterministic corpus currently guards every native instruction encoder:

- RDA, RMPA, WRA, WRAP;
- RDAX, RDFX/LDAX, WRAX, WRHX, WRLX, MAXX/ABSA, MULX;
- LOG, EXP, SOF;
- AND/CLR, OR, XOR/NOT;
- SKP/NOP;
- WLDS, WLDR, JAM;
- CHO RDA, CHO SOF and CHO RDAL;
- local-only RAW.

It also covers both EQU/MEM declaration forms, delay start/mid/end addressing,
the reserved register/LFO/condition symbols, forward-label SKP offsets including
0 and 63, fixed-point boundaries and the already established SpinAsm truncation
oracle.

## Genuine SpinAsm procedure

Build the native compiler first:

```sh
cmake -S . -B build/qual-1.0 -DCMAKE_BUILD_TYPE=Release
cmake --build build/qual-1.0 --parallel
ctest --test-dir build/qual-1.0 --output-on-failure
python3 tools/qualification.py --repo . --build build/qual-1.0 --expect-version 0.2.0
```

Prepare exact official batches:

```sh
python3 tools/compiler_conformance.py prepare-official \
  --repo . \
  --work build/compiler-conformance-1.0
```

The generated `official-input/batch-*` directories contain exact source files,
slot maps and SHA-256 provenance. Build every batch in genuine SpinAsm 1.1.31 and
copy its Intel HEX file into the corresponding `official-output/` filename.

Then run the authoritative comparison:

```sh
python3 tools/compiler_conformance.py run \
  --repo . \
  --work build/compiler-conformance-1.0 \
  --native build/qual-1.0/open-spin-fv1
```

A Python-assembler mismatch is diagnostic only. The only compatibility authority
is native output versus genuine SpinAsm output.

## Sealing

After every official-positive case passes:

```sh
python3 tools/compiler_conformance.py seal-official \
  --repo . \
  --work build/compiler-conformance-1.0
```

Then test the sealed gate:

```sh
python3 tools/qualification.py \
  --repo . \
  --build build/qual-1.0 \
  --expect-version 0.2.0 \
  --require-sealed-golden
```

A future `1.x` version automatically requires a complete sealed golden corpus
when `--expect-version` is supplied.

## Promotion policy

Do not jump directly from 0.2.0 to 1.0.0 after adding tooling.

1. Generate and audit the corpus.
2. Run the complete genuine SpinAsm differential.
3. Resolve every mismatch or classify it as a deliberate extension.
4. Run the adjudication probes individually.
5. Seal the accepted official-positive corpus.
6. Re-run all six native CI targets plus sanitizers.
7. Promote a semantics-frozen `0.9.0` release candidate.
8. Make only conformance/test/documentation fixes during the RC window.
9. Tag `1.0.0` only when the sealed corpus, package qualification and release
   provenance all pass from the exact tag.

The 9/9 historical product corpus remains useful evidence, but it is not the
1.0 proof by itself.
