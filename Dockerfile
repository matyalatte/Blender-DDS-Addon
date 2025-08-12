# Building workflow for ubuntu 20.04 or later.
#
# 1. Use this docker file to build shared libraries.
#    docker build -t blender_dds -f Dockerfile ./
#
# 2. Run the built image.
#    docker run --name blender_dds blender_dds
#
# 3. Use "docker cp" to get the built libraries.
#    docker cp blender_dds:/Blender-DDS-Addon/bin ./
#    cp ./bin/libtexconv.* ./somewhere
#    cp ./bin/libastcenc* ./somewhere

# Base image
FROM matyalatte/ubuntu20.04-cmake3.25:latest

# Install packages
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates build-essential git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Clone repo
COPY . /Blender-DDS-Addon
WORKDIR /Blender-DDS-Addon
RUN git submodule update --init --recursive --recommend-shallow --depth 1

# Build
WORKDIR /Blender-DDS-Addon
RUN mkdir bin && \
    bash external/Texconv-Custom-DLL/shell_scripts/build.sh && \
    cp external/Texconv-Custom-DLL/libtexconv.* bin && \
    bash external/build_astcenc_Linux.sh && \
    cp external/astc-encoder/libastcenc* bin
