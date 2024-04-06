#!/bin/bash
# Builds astc-encoder with cmake on macOS.
# libastc-shared.dylib will be generated in ./astc-encoder/

pushd $(dirname "$0")/astc-encoder/
mkdir build
cd build
cmake -D CMAKE_BUILD_TYPE=Release -D CMAKE_POSITION_INDEPENDENT_CODE=ON -D CMAKE_OSX_DEPLOYMENT_TARGET=10.15 -D ASTCENC_CLI=OFF -D ASTCENC_SHAREDLIB=ON ../
cmake --build .
cd Source
lipo -create -output libastcenc-shared.dylib -arch x86_64 libastcenc-sse4.1-shared.dylib -arch x86_64h libastcenc-avx2-shared.dylib -arch arm64 libastcenc-neon-shared.dylib
cp libastcenc-shared.dylib ../../
popd
