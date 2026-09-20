# Compiler qualification policy

`open-spin-fv-1-compiler` is the canonical implementation of the native SpinASM compiler used by Roth Amplification projects.

The compatibility target is **Spin Semiconductor SpinAsm 1.1.31**. The project does not claim exhaustive compatibility with every historical source program. A release claim is limited to behavior covered by the qualification suite and the official differential corpus.

## Release gates

Every release binary must pass on its native runner:

1. normal CMake build and CTest;
2. all shipped `.spn` programs compile to exactly 512 bytes;
3. repeated compilation is byte-for-byte deterministic;
4. `--check` succeeds for every shipped program;
5. known words captured from genuine SpinAsm 1.1.31 match exactly;
6. the non-official `JMP` mnemonic is rejected;
7. the 128-instruction boundary succeeds and 129 instructions are rejected;
8. staged CMake install succeeds;
9. package SHA-256 and provenance manifest are generated.

Linux additionally executes the same tests under AddressSanitizer and UndefinedBehaviorSanitizer on normal CI.

## Official differential corpus

The authoritative reverse-engineering procedure remains `tools/compiler_conformance.py`: native output is compared byte-for-byte with Intel HEX emitted by the real SpinAsm 1.1.31 application. The historical Python assembler is diagnostic only and never establishes conformance.

The current audited product corpus reached **9/9 byte-identical** native output. Two incompatibilities discovered by that process are permanently guarded in automated qualification:

- unconditional forward branch syntax is `SKP 0, label`; `JMP` is rejected;
- real-valued fixed-point operands truncate toward zero rather than round-to-nearest.

Before a future `1.0.0` compiler release, expand and seal a syntax/opcode/boundary torture corpus against the genuine official compiler. The 0.x release line is intentionally the qualification series.

## 1.0 expansion

The historical 9/9 product corpus is not the final 1.0 proof. The repository now
contains a deterministic instruction/parser/boundary census under
`conformance/`, audited by `tools/corpus_audit.py`.

Before 1.0, every case in `conformance/corpus/` must be byte-identical to
genuine SpinAsm 1.1.31 output. Parser features whose official accept/reject
behavior is not yet sealed live under `conformance/adjudication/` and must be
tested individually rather than guessed.

See [`QUALIFICATION-1.0.md`](QUALIFICATION-1.0.md).
