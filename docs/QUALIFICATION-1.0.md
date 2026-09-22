# open-spin-fv1 1.0 qualification plan

## V15 oracle lock

Genuine SpinAsm 1.1.31 executable SHA-256:
`c20c46a6c8999ead5ac088ea9b7700b7fae168b6ee704e26218e40166fa6189f`

V14/V15 established:

- integer WLDR frequency descriptor: **-16384 through 32767**;
- `CHO SOF,RMP1,NA` rejects; `CHO SOF,RMP1,NA,0` accepts;
- `CHO RDAL,COS0` / `COS1` accept;
- explicit flags on `CHO RDAL` reject;
- V15 adjudication: **7 ACCEPT / 11 REJECT / 0 INDETERMINATE**;
- `RAW` is officially rejected but remains a deliberate local extension.

## Corpus

- `conformance/corpus/`: 19 positive torture programs.
- `conformance/rejection/`: 12 strict official-rejection regressions.
- `conformance/local/`: deliberate extensions.
- `conformance/golden/`: sealed genuine-SpinAsm program images.

## Final positive differential

```sh
cmake -S . -B build/qual-1.0 -DCMAKE_BUILD_TYPE=Release
cmake --build build/qual-1.0 --parallel
ctest --test-dir build/qual-1.0 --output-on-failure
python3 tools/qualification.py --repo . --build build/qual-1.0 --expect-version 0.2.0

python3 tools/compiler_conformance.py prepare-official --repo . --work build/compiler-conformance-1.0
```

After genuine SpinAsm builds every batch:

```sh
python3 tools/compiler_conformance.py run --repo . --work build/compiler-conformance-1.0 --native build/qual-1.0/open-spin-fv1
python3 tools/compiler_conformance.py seal-official --repo . --work build/compiler-conformance-1.0
python3 tools/qualification.py --repo . --build build/qual-1.0 --expect-version 0.2.0 --require-sealed-golden
```

Only genuine SpinAsm output is authoritative. After the corrected positive corpus
is byte-identical and sealed, rerun six-platform CI plus sanitizers, then promote
`0.9.0` as the semantics-frozen RC.

## V16 four-bank byte differential findings

The first complete 28-program genuine-SpinAsm pass compiled all four official
banks successfully and then exposed seven native byte mismatches. They reduced
to six implementation behaviors:

- even-length `MEM` midpoint (`^`) selects the lower middle sample;
- `CHO SOF ...,-1.0` encodes a zero D-field in genuine SpinAsm 1.1.31;
- the accepted `~0` expression evaluates to zero;
- accepted real values supplied to bit-vector fields are integer-truncated;
- accepted real `WLDS` amplitude values are integer-truncated;
- accepted real `WLDR` frequency values are integer-truncated.

The four official HEX banks from that pass remain authoritative because no
positive corpus source changed; only native compiler semantics were corrected.
