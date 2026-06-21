# Source.Python FastDL

A small Source.Python plugin that adds simple FastDL support without needing a separate web server.

The plugin can start a built-in HTTP server, set `sv_downloadurl` automatically, create a FastDL directory structure, and compress downloadable files to `.bz2`.
By default, the plugin uses a separate FastDL folder and creates `.bz2` files for maps, materials, models, and sounds. Original uncompressed files can also be copied if wanted, or used as a fallback when `.bz2` compression is unavailable or fails.

## Features

* Built-in FastDL HTTP server
* Automatically sets `sv_downloadurl`
* Automatically creates FastDL subdirectories
* Supports custom FastDL directory
* Automatically creates `.bz2` compressed files
* Optional uncompressed file copying
* Optional fallback to uncompressed files if `.bz2` compression fails
* Ignores common stock maps(CSGO ones listed as default)
* Only processes supported FastDL file types

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

Load command: sp plugin load fastdl