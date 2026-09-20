# SpinAsm conformance

The authoritative compatibility target is the real Spin Semiconductor **SpinAsm 1.1.31** compiler.

Original audited upstream snapshot:

```
Roth-Amplification-Ltd/Spin-FV-1-Emulator
7116ad3b0fc91f3099d546467d567e39c343252e
```

Differential testing found and corrected two important incompatibilities:

1. `JMP` was a non-official convenience mnemonic. Official unconditional forward skip syntax is `SKP 0, label`.
2. SpinAsm 1.1.31 truncates real-valued fixed-point operands toward zero instead of rounding to nearest.

The audited product corpus reached **9/9 byte-identical programs** against real SpinAsm 1.1.31 output. That is a corpus-scoped result, not a claim that every possible historical input has been exhaustively proven.

`tools/qualification.py` permanently guards the known official oracle behavior, deterministic compilation, shipped corpus, parser rejection, and size boundaries on every supported release architecture. `tools/compiler_conformance.py` remains the authoritative procedure for new differential work with the genuine official compiler.

Official SpinAsm itself is not distributed by this repository.

## Expanded 1.0 differential

The next compatibility gate is the deterministic corpus under
`conformance/corpus/`, not merely the nine shipped product examples. The
conformance harness now discovers both sets, records source SHA-256 in every
prepared official batch, and treats the historical Python assembler as
diagnostic only.

`conformance/adjudication/` contains isolated syntax questions that require the
genuine SpinAsm application to classify before they are promoted to an official
positive or negative contract.

No 1.0 claim should be made until the expanded corpus is complete and sealed.
