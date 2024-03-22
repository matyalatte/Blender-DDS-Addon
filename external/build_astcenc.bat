@echo off

REM Builds texconv.dll with CMake and Visual Studio.
REM texconv.dll will be generated in ..\

set VS_VERSION=Visual Studio 17 2022

@pushd %~dp0\astc-encoder\
mkdir build
cd build

cmake -G "%VS_VERSION%"^
 -A x64^
 -D CMAKE_CONFIGURATION_TYPES=Release^
 -D CMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL^
 -D ASTCENC_CLI=OFF^
 -D ASTCENC_ISA_SSE2=ON^
 -D ASTCENC_SHAREDLIB=ON^
 ../

cmake --build . --config Release
copy Source\Release\astcenc-sse2-shared.dll ..\
@popd

pause
