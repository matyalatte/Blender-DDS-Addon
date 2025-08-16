# How to Build

If you want to make a zip from the repository, you should do the following steps.

## 0. Requirements

- c++17 compiler
- CMake 3.20 or later
- git
- Visual Studio 2022 (for Windows)

> [!Note]
> If you won't use Visual Studio 2022 on Windows, you could need to edit cmake commands in batch files.

## 1. Download Submodules

Move to `./Blender-DDS-Addon` and type `git submodule update --init --recursive`.  
It clones external repositories to the addon's repo.

## 2. Build Texconv

Move to `./Blender-DDS-Addon/external/Texconv-Custom-DLL`.  
Then, run `batch_files/build_without_vcruntime.bat` or `bash shell_scripts/build_universal.sh`.  
It generates `texconv.dll` or `libtexconv.*` in `./Blender-DDS-Addon/external/Texconv-Custom-DLL/`  

## 4. Copy Texconv

Copy the built binary (`texconv.dll`, `libtexconv.dylib` or `libtexconv.so`) to `./Blender-DDS-Addon/addons/blender_dds_addon/directx`.  

## 5. Build astc-encoder

Move to `./Blender-DDS-Addon/external`.  
Then, run `build_astcenc.bat`, `build_astcenc_Linux.sh`, or `build_astcenc_macOS.sh`.  
It generates `astcenc-*.dll` or `libastcenc-*.*` in `./Blender-DDS-Addon/external/astc-encoder/`  

## 6. Copy astcenc

Copy the built binary (`astcenc-*.dll` or `libastcenc-*.*`) to `./Blender-DDS-Addon/addons/blender_dds_addon/astcenc`.  

## 7. Archive Files

Zip the addon folder (`./Blender-DDS-Addon/addons/blender_dds_addon`).  

## 8. Done!

You can install the addon with the zip file (`blender_dds_addon.zip`).  
