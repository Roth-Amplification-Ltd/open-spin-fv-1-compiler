# open-spin-fv-1-compiler

Open-source native SpinASM compiler for the Spin Semiconductor FV-1. This repository is the **canonical compiler implementation**; FV-1 Lab consumes a synchronized/pinned snapshot but remains a separate emulator/testbench product.

The project ships two things:

- `open-spin-fv1` — standalone command-line compiler;
- `OpenSpinFV1::compiler` — embeddable C++20 static library/CMake package.

## Compatibility status

Target: **Spin Semiconductor SpinAsm 1.1.31**.

Reverse-engineering and byte-level differential testing found and corrected real incompatibilities, including non-official `JMP` handling and fixed-point rounding behavior. The audited product corpus reached **9/9 byte-identical output** versus genuine SpinAsm 1.1.31.

That statement is deliberately corpus-scoped. See `docs/CONFORMANCE.md` and `docs/QUALIFICATION.md`.

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

Output is one raw 512-byte FV-1 program image (128 big-endian 32-bit instruction words).

## Embedding

After installation:

```cmake
find_package(OpenSpinFV1 CONFIG REQUIRED)
target_link_libraries(my_target PRIVATE OpenSpinFV1::compiler)
```

Include:

```cpp
#include <fv1/spinasm.hpp>
```

## Releases

Version tags (`v0.2.0`, etc.) build and qualify native release assets for:

- Linux x86_64 and ARM64;
- macOS x86_64 and Apple Silicon ARM64;
- Windows x86_64 and ARM64.

Each release includes the CLI, static library, public header, CMake package metadata, documentation, SHA-256 checksums and provenance manifests.

## License

Mozilla Public License 2.0. See `LICENSE`.
