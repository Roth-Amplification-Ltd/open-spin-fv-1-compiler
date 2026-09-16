# SpinAsm conformance

The authoritative compatibility target is the real Spin Semiconductor
SpinAsm 1.1.31 compiler.

Upstream source snapshot:

```
7116ad3b0fc91f3099d546467d567e39c343252e
```

Differential testing found and corrected two important incompatibilities:

1. `JMP` was a non-official convenience mnemonic. Official unconditional
   forward skip syntax is `SKP 0, label`.
2. SpinAsm 1.1.31 truncates real-valued fixed-point operands toward zero
   instead of rounding to nearest.

The imported upstream compiler reached 9/9 byte-identical programs in the
current official corpus.

Official SpinAsm itself is not distributed by this repository.
