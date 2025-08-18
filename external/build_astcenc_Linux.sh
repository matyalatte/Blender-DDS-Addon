#!/usr/bin/env bash
# Builds astc-encoder with cmake on Linux.
# libastc-sse2-shared.so will be generated in ./astc-encoder/

pushd $(dirname "$0")/astc-encoder/
mkdir build
cd build
cmake \
  -D CMAKE_BUILD_TYPE=Release\
  -D CMAKE_POSITION_INDEPENDENT_CODE=ON\
  -D ASTCENC_CLI=OFF\
  -D ASTCENC_ISA_SSE2=ON\
  -D ASTCENC_SHAREDLIB=ON\
  ../
cmake --build .
cp Source/libastcenc-sse2-shared.so ../
popd
