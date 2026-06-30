# Source.Python FastDL

A small Source.Python plugin that adds simple FastDL support without needing a separate web server.

The plugin can start a built-in HTTP server, set `sv_downloadurl` automatically, create a FastDL directory structure, and compress downloadable files to `.bz2`.

By default, the plugin uses a separate FastDL folder and creates `.bz2` files for maps, materials, models, and sounds. Original uncompressed files can also be copied if wanted, or used as a fallback when `.bz2` compression is unavailable or fails.

## Requirements

This plugin requires [Source.Python](https://github.com/Source-Python-Dev-Team/Source.Python/releases).

It should work with any game supported by Source.Python. The release archive is structured so it can be extracted directly into your game folder, such as `cstrike`, `csgo`, `hl2mp`, or another Source.Python-supported game folder.

## Features

* Built-in FastDL HTTP server
* Automatically sets `sv_downloadurl`
* Automatically creates required FastDL subdirectories
* Supports a custom FastDL directory
* Automatically creates `.bz2` compressed files
* Optional uncompressed file copying
* Optional fallback to uncompressed files if `.bz2` compression is unavailable or fails
* Ignores common stock CS:GO maps by default
* Only processes supported FastDL file types
* Automatically scans every minute for new downloadable files and creates missing `.bz2` FastDL files

## Basic idea

The plugin scans common game content folders such as:

```text
maps/
materials/
models/
sound/
```

Then it prepares matching FastDL files in a custom directory, for example:

```text
csgo/fastdl/csgo/maps/example.bsp.bz2
```

The built-in HTTP server serves that folder, so clients can download files from the URL set in `sv_downloadurl`.

## Installation

1. Install Source.Python.
2. Download the latest release of this plugin.
3. Extract the archive directly into your game folder, for example `csgo`, `cstrike`, or `hl2mp`.
4. Load the plugin with:

```text
sp plugin load fastdl
```

## Configuration

The plugin includes cvars for controlling the main behavior:

```text
fastdl_use_custom_path
fastdl_custom_directory
fastdl_auto_compress
fastdl_fallback_uncompressed
fastdl_copy_uncompressed
fastdl_auto_create_subdirectories
```

The default setup is intended to work without much configuration, but server owners can adjust the path and file behavior if needed.
