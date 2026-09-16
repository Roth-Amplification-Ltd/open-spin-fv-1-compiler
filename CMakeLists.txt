cmake_minimum_required(VERSION 3.20)
project(open_spin_fv1_compiler VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(GNUInstallDirs)
include(CTest)

option(OPEN_SPIN_FV1_WARNINGS "Enable strict warnings" ON)

function(open_spin_warnings target)
    if(NOT OPEN_SPIN_FV1_WARNINGS)
        return()
    endif()
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4)
    else()
        target_compile_options(${target} PRIVATE
            -Wall -Wextra -Wpedantic -Wconversion -Wshadow)
    endif()
endfunction()

add_library(open-spin-fv1-compiler STATIC
    src/spinasm/spinasm.cpp)
add_library(OpenSpinFV1::compiler ALIAS open-spin-fv1-compiler)
target_include_directories(open-spin-fv1-compiler PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)
set_target_properties(open-spin-fv1-compiler PROPERTIES
    POSITION_INDEPENDENT_CODE ON)
open_spin_warnings(open-spin-fv1-compiler)

add_executable(open-spin-fv1 src/cli/main.cpp)
target_link_libraries(open-spin-fv1 PRIVATE OpenSpinFV1::compiler)
target_compile_definitions(open-spin-fv1 PRIVATE
    OPEN_SPIN_FV1_VERSION_STRING="${PROJECT_VERSION}")
open_spin_warnings(open-spin-fv1)

if(BUILD_TESTING)
    add_executable(open-spin-fv1-tests tests/test_spinasm.cpp)
    target_link_libraries(open-spin-fv1-tests PRIVATE OpenSpinFV1::compiler)
    open_spin_warnings(open-spin-fv1-tests)
    add_test(NAME open-spin-fv1-tests COMMAND open-spin-fv1-tests)
endif()

install(TARGETS open-spin-fv1 open-spin-fv1-compiler
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(FILES include/fv1/spinasm.hpp
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/fv1)
