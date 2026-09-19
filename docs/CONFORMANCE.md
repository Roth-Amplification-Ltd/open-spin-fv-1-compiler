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
