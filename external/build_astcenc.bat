@echo off

REM Builds astcenc-*-shared.dll with CMake and Visual Studio.
REM astcenc-*-shared.dll will be generated in astc-encoder

set VS_VERSION=Visual Studio 17 2022

if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set TARGET_ARCH=x64
    set ISA_FLAG=ASTCENC_ISA_SSE2=ON
    set DLL_NAME=astcenc-sse2-shared.dll
) else if "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
    set TARGET_ARCH=arm64
    set ISA_FLAG=ASTCENC_ISA_NEON=ON
    set DLL_NAME=astcenc-neon-shared.dll
) else (
    echo Unsupported architecture: %PROCESSOR_ARCHITECTURE%
    pause
    exit /b 1
)

@pushd %~dp0\astc-encoder\
mkdir build
cd build

REM VS 2022 17.10 requires _DISABLE_CONSTEXPR_MUTEX_CONSTRUCTOR
REM https://github.com/actions/runner-images/issues/10004

cmake -G "%VS_VERSION%"^
 -A %TARGET_ARCH%^
 -D CMAKE_CONFIGURATION_TYPES=Release^
 -D CMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL^
 -D ASTCENC_CLI=OFF^
 -D %ISA_FLAG%^
 -D ASTCENC_SHAREDLIB=ON^
 -D CMAKE_CXX_FLAGS='-D_DISABLE_CONSTEXPR_MUTEX_CONSTRUCTOR'^
 ../

cmake --build . --config Release
copy Source\Release\%DLL_NAME% ..\
@popd

pause
