// SPDX-License-Identifier: MPL-2.0
#include <fv1/spinasm.hpp>

#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#ifndef OPEN_SPIN_FV1_VERSION_STRING
#define OPEN_SPIN_FV1_VERSION_STRING "dev"
#endif

namespace fs = std::filesystem;

namespace {

void usage(std::ostream& os) {
    os <<
R"(open-spin-fv1 - open native SpinASM compiler for the Spin FV-1

Usage:
  open-spin-fv1 assemble <input.spn> <output.bin>
  open-spin-fv1 <input.spn> -o <output.bin>
  open-spin-fv1 --check <input.spn>
  open-spin-fv1 --version
  open-spin-fv1 --help

Output:
  Raw 512-byte FV-1 program image (128 big-endian 32-bit instruction words).
)";
}

std::string read_text(const fs::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error("cannot open input: " + path.string());
    return std::string(std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>());
}

void write_binary(const fs::path& path, const fv1::spinasm::CompileResult& result) {
    std::ofstream out(path, std::ios::binary);
    if (!out) throw std::runtime_error("cannot create output: " + path.string());
    out.write(reinterpret_cast<const char*>(result.image.data()),
              static_cast<std::streamsize>(result.image.size()));
    if (!out) throw std::runtime_error("cannot write output: " + path.string());
}

int compile_file(const fs::path& input, const fs::path* output, bool check_only) {
    try {
        const auto source = read_text(input);
        const auto result = fv1::spinasm::compile(source);
        if (!check_only && output != nullptr) {
            write_binary(*output, result);
        }
        std::cout << input.string() << ": OK"
                  << " (" << result.instruction_count << " instruction(s), "
                  << "highest delay address " << result.highest_delay_address << ")\n";
        return 0;
    } catch (const fv1::spinasm::CompileError& e) {
        std::cerr << input.string() << ": compile error";
        if (e.line() != 0) std::cerr << " on line " << e.line();
        std::cerr << ": " << e.what() << "\n";
        return 2;
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
}

} // namespace

int main(int argc, char** argv) {
    std::vector<std::string_view> args;
    for (int i = 1; i < argc; ++i) args.emplace_back(argv[i]);

    if (args.empty() || args[0] == "--help" || args[0] == "-h") {
        usage(args.empty() ? std::cerr : std::cout);
        return args.empty() ? 2 : 0;
    }
    if (args[0] == "--version") {
        std::cout << "open-spin-fv1 " << OPEN_SPIN_FV1_VERSION_STRING << "\n";
        return 0;
    }
    if (args[0] == "--check") {
        if (args.size() != 2) {
            usage(std::cerr);
            return 2;
        }
        const fs::path input(args[1]);
        return compile_file(input, nullptr, true);
    }
    if (args[0] == "assemble") {
        if (args.size() != 3) {
            usage(std::cerr);
            return 2;
        }
        const fs::path input(args[1]);
        const fs::path output(args[2]);
        return compile_file(input, &output, false);
    }
    if (args.size() == 3 && (args[1] == "-o" || args[1] == "--output")) {
        const fs::path input(args[0]);
        const fs::path output(args[2]);
        return compile_file(input, &output, false);
    }

    usage(std::cerr);
    return 2;
}
