# SpinAsm 1.1.31 qualification corpus

This directory separates three different claims:

- `corpus/`: intended genuine-SpinAsm-compatible positive programs;
- `local/`: open-spin-fv1 extensions that are not part of the official claim;
- `adjudication/`: isolated parser/syntax questions that still need the genuine
  SpinAsm 1.1.31 application to classify.

`corpus-manifest.json` is generated deterministically by
`tools/generate_conformance_corpus.py` and records SHA-256 for every source.

Run:

```sh
python3 tools/generate_conformance_corpus.py --check
python3 tools/corpus_audit.py
```

before differential work so the exact source under test cannot silently drift.

The authoritative differential harness is `tools/compiler_conformance.py`.
