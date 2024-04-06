# How to Build

If you want to make a zip from the repository, you should do the following steps.

## 0. Requirements

### Platforms

Make sure that [Texconv-Custom-DLL](https://github.com/matyalatte/Texconv-Custom-DLL#platform) supports your platform.  

### for Windows

- Visual Studio 2022
- CMake

If you won't use Visual Studio 2022, you could need to edit cmake commands in batch files.

### for Unix/Lunux

- xcode (for macOS)
- build-essential (for Ubuntu)
- cmake
- wget

## 1. Download Submodules

Move to `./Blender-DDS-Addon`.  
Then, type `git submodule update --init --recursive`.  
It'll clone external repositories to the addon's repo.

## 2. Get `sal.h` (for Unix/Linux systems)

If you are using non-Windows platforms, you should download [sal.h](https://github.com/dotnet/corert/blob/master/src/Native/inc/unix/sal.h)
for DirectXMath.  
Move to `./Blender-DDS-Addon/external/Texconv-Custom-DLL/shell_scripts`.  
Then, type `bash get_sal.sh`.  
It'll download the file and place it in a proper location.  

## 3. Build Texconv

Move to `./Blender-DDS-Addon/external/Texconv-Custom-DLL`.  
Then, run `batch_files/build_without_vcruntime.bat` or `bash shell_scripts/build_universal.sh`
`texconv.dll` or `libtexconv.*` will be generated in `./Blender-DDS-Addon/external/Texconv-Custom-DLL/`  

## 4. Copy Texconv

Copy the built binary (`texconv.dll`, `libtexconv.dylib` or `libtexconv.so`) to `./Blender-DDS-Addon/addons/blender_dds_addon/directx`.  

## 5. Build astc-encoder

Move to `C:\Users\nk0902\git\Blender-DDS-Addon\external`.  
Then, run `build_astcenc.bat`, `build_astcenc_Linux.sh`, or `build_astcenc_macOS.sh`.  
`astcenc-*.dll` or `libastcenc-*.*` will be generated in `./Blender-DDS-Addon/external/astc-encoder/`  

## 6. Copy astcenc

Copy the built binary (`astcenc-*.dll` or `libastcenc-*.*`) to `./Blender-DDS-Addon/addons/blender_dds_addon/astcenc`.  

## 7. Archive Files

Zip the addon folder (`./Blender-DDS-Addon/addons/blender_dds_addon`).  

## 8. Done!

You can install the addon with the zip file (`blender_dds_addon.zip`).  
