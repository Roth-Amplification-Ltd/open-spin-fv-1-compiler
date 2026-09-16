# open-spin-fv-1-compiler

Open-source native SpinASM compiler for the Spin Semiconductor FV-1.

This project is the compiler-only extraction of the native compiler developed
inside `Spin-FV-1-Emulator`. It has no emulator, audio, GUI, Qt, or realtime
runtime dependency.

## Provenance

Imported from:

```
Roth-Amplification-Ltd/Spin-FV-1-Emulator
7116ad3b0fc91f3099d546467d567e39c343252e
```

That upstream compiler reached **9/9 byte-identical output** against the real
Spin Semiconductor SpinAsm 1.1.31 compiler for the current conformance corpus.

This is a corpus-scoped compatibility claim, not an assertion that every
possible historical SpinASM input has already been exhaustively proven.

## Build

Linux/macOS:

```sh
./tools/build.sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File tools/build.ps1
```

## Use

```sh
open-spin-fv1 assemble program.spn program.bin
open-spin-fv1 program.spn -o program.bin
open-spin-fv1 --check program.spn
open-spin-fv1 --version
```

The output is one raw 512-byte FV-1 program image.

## License

Mozilla Public License 2.0. See `LICENSE`.
