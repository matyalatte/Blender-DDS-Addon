# How to Build

If you want to make a zip from the repository, you should do the following steps.

## 0. Requirements

### Platforms

Make sure that [Texconv-Custom-DLL](https://github.com/matyalatte/Texconv-Custom-DLL#platform) supports your platform.  

### for Windows

- Visual Studio 2022
- CMake

If you won't use Visual Studio 2022, you could need to edit cmake commands in batch files.

### for Unix

- xcode (for macOS)
- build-essential (for Ubuntu)
- cmake
- wget

## 1. Download Submodules

Move to `./Blender-DDS-Addon`.  
Then, type `git submodule update --init --recursive`.  
It'll clone external repositories to the addon's repo.

## 2. Get `sal.h` (for Unix systems)

If you are using non-Windows platforms, you should download [sal.h](https://github.com/dotnet/corert/blob/master/src/Native/inc/unix/sal.h)
for DirectXMath.  
Move to `./Blender-DDS-Addon/external/Texconv-Custom-DLL/shell_scripts`.  
Then, type `bash get_sal.sh`.  
It'll download the file and place it in a proper location.  

## 3. Build Texconv

### for Windows

Move to `./Blender-DDS-Addon/external/Texconv-Custom-DLL/batch_files`.  
Then, type `build_dds_full_support.bat`.  
`texconv.dll` will be generated in `./Blender-DDS-Addon/external/Texconv-Custom-DLL/`  

### for Unix

Move to `./Blender-DDS-Addon/external/Texconv-Custom-DLL/shell_scripts`.  
Then, type `bash build_dds_full_support.sh`.  
`libtexconv.so` (or `libtexconv.dylib`) will be generated in `./Blender-DDS-Addon/external/Texconv-Custom-DLL/`  

## 4. Copy Texconv

Copy the built binary (`texconv.dll`, `libtexconv.dylib` or `libtexconv.so`) to `./Blender-DDS-Addon/addons/blender_dds_addon`.  

## 5. Archive Files

Zip the addon folder (`./Blender-DDS-Addon/addons/blender_dds_addon`).  

## 6. Done!

You can install the addon with the zip file (`blender_dds_addon.zip`).  
