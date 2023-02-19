# Blender-DDS-Addon v0.3.1

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![build](https://github.com/matyalatte/Blender-DDS-Addon/actions/workflows/build.yml/badge.svg)
<a href="https://www.buymeacoffee.com/matyalatteQ" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>  

Blender addon to import and export dds textures  
  
![Screenshot](https://user-images.githubusercontent.com/69258547/194742234-9021612e-a49e-4b92-a92c-234678b7a298.png)  

## Features

- Import DDS textures as TGA (or HDR)
- Export textures as DDS
- Support many DXGI formats (including BC6 and BC7)
- Support non-2D textures (cubemaps, arrays, and volume textures)

## Download

You can download zip files from [the release page](https://github.com/matyalatte/Blender-DDS-Addon/releases).  

-   `blender_dds_addon*_Windows.zip` is for Windows.
-   `blender_dds_addon*_macOS.zip` is for Mac (10.15 or later).
-   `blender_dds_addon*_Linux.zip` is for Ubuntu (20.04 or later).

> The linux build only supports Ubuntu due to the glibc dependences.  
> If you want to use it on other linux distributions, you should get the lib or build [Texconv](https://github.com/matyalatte/Texconv-Custom-DLL) by yourself.  
> (But I don't know if it's possible on your platform.)  

## Getting Started

[Getting Started · matyalatte/Blender-DDS-Addon Wiki](https://github.com/matyalatte/Blender-DDS-Addon/wiki/Getting-Started)

## Supported Formats

The addon supports most of the DXGI formats.  
  
Here is a list of supported formats.  

<details>
<summary>Supported DXGI Formats</summary>

* BC1_UNORM
* BC1_UNORM_SRGB
* BC2_UNORM
* BC2_UNORM_SRGB
* BC3_UNORM
* BC3_UNORM_SRGB
* BC4_UNORM
* BC4_SNORM
* BC5_UNORM
* BC5_SNORM
* BC6H_UF16
* BC6H_SF16
* BC7_UNORM
* BC7_UNORM_SRGB
* R32G32B32A32_FLOAT
* R32G32B32A32_UINT
* R32G32B32A32_SINT
* R32G32B32_FLOAT
* R32G32B32_UINT
* R32G32B32_SINT
* R16G16B16A16_FLOAT
* R16G16B16A16_UNORM
* R16G16B16A16_UINT
* R16G16B16A16_SNORM
* R16G16B16A16_SINT
* R32G32_FLOAT
* R32G32_UINT
* R32G32_SINT
* D32_FLOAT_S8X24_UINT
* R10G10B10A2_UNORM
* R10G10B10A2_UINT
* R11G11B10_FLOAT
* R8G8B8A8_UNORM
* R8G8B8A8_UNORM_SRGB
* R8G8B8A8_UINT
* R8G8B8A8_SNORM
* R8G8B8A8_SINT
* R16G16_FLOAT
* R16G16_UNORM
* R16G16_UINT
* R16G16_SNORM
* R16G16_SINT
* D32_FLOAT
* R32_FLOAT
* R32_UINT
* R32_SINT
* D24_UNORM_S8_UINT
* R8G8_UNORM
* R8G8_UINT
* R8G8_SNORM
* R8G8_SINT
* R16_FLOAT
* D16_UNORM
* R16_UNORM
* R16_UINT
* R16_SNORM
* R16_SINT
* R8_UNORM
* R8_UINT
* R8_SNORM
* R8_SINT
* A8_UNORM
* R1_UNORM
* R9G9B9E5_SHAREDEXP
* R8G8_B8G8_UNORM
* G8R8_G8B8_UNORM
* B5G6R5_UNORM
* B5G5R5A1_UNORM
* B8G8R8A8_UNORM
* B8G8R8X8_UNORM
* R10G10B10_XR_BIAS_A2_UNORM
* B8G8R8A8_UNORM_SRGB
* B8G8R8X8_UNORM_SRGB
* B4G4R4A4_UNORM

</details>

## About Non-2D Textures
The addon supports non-2D textures except for partial cubemaps.  
See wiki pages for the details.  

- [Cubemaps](https://github.com/matyalatte/Blender-DDS-Addon/wiki/Cubemaps)  
- [Texture Arrays](https://github.com/matyalatte/Blender-DDS-Addon/wiki/Texture-Arrays)  

## External Dependencies

### Texconv-Custom-DLL

[Texconv](https://github.com/microsoft/DirectXTex/wiki/Texconv)
is a texture converter developed by Microsoft.  
It's the best DDS converter as far as I know.  
And [Texconv-Custom-DLL](https://github.com/matyalatte/Texconv-Custom-DLL) is a cross-platform implementation I made.  
The official Texconv only supports Windows but you can use it on Unix systems.  

## License

Files in this repository (including all submodules) are licensed under [MIT license](../LICENSE).

## For Developers

There are some documents for developers.

- [How to Build](./How-To-Build.md): See here if you want to know how to create a zip from the repository.
- [Tools for development](./For-Dev.md): See here if you want to know how to test the addon.
