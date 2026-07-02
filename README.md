# Source.Python FastDL

A small Source.Python plugin that adds simple FastDL support without needing a separate web server.

The plugin can start a built-in HTTP server, set `sv_downloadurl` automatically, create a FastDL directory structure, and compress downloadable files to `.bz2`.

By default, the plugin uses a separate FastDL folder and creates `.bz2` files for maps, materials, models, and sounds. Original uncompressed files can also be copied if wanted, or used as a fallback when `.bz2` compression is unavailable or fails.

## Requirements

This plugin requires [Source.Python](https://github.com/Source-Python-Dev-Team/Source.Python/releases).

It should work with any game supported by Source.Python. The release archive is structured so it can be extracted directly into your game folder, such as `cstrike`, `csgo`, `hl2mp`, or another Source.Python-supported game folder.

## FastDL HTTP Port

By default, the built-in FastDL HTTP server uses the game server `hostport`.

For many servers this is usually `27015`, so the generated FastDL URL may look like this:

```text
http://your-server-ip:27015
```

The built-in HTTP server requires an available TCP port. If the plugin prints an error like this:

```text
FastDL: Server error: [Errno 98] Address already in use
```

Set `fastdl_server_port` to another open port provided by your host.

```text
fastdl_server_port 27016(for example)
```

If no additional port is available and the built-in HTTP server cannot start, set `fastdl_auto_set_fastdl_url` to 0:

fastdl_auto_set_fastdl_url 0

This prevents the plugin from setting sv_downloadurl to a broken FastDL URL, so players will not attempt to download files from an unavailable FastDL server.

The plugin can still be used to automatically prepare and compress FastDL content.


## Features

* Built-in FastDL HTTP server
* Automatically sets `sv_downloadurl`
* Automatically creates required FastDL subdirectories
* Supports a custom FastDL directory
* Automatically creates `.bz2` compressed files
* Optional uncompressed file copying
* Optional fallback to uncompressed files if `.bz2` compression is unavailable or fails
* Can be used only for preparing and compressing FastDL content if no port is available
* Ignores common stock CS:GO maps by default
* Supports a custom ignored maps file
* Only processes supported FastDL file types
* Automatically scans for new downloadable files
* Configurable auto-scan interval

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
fastdl_enable_auto_scan
fastdl_auto_scan_interval
fastdl_reload_ignored_maps
fastdl_server_port
fastdl_auto_set_fastdl_url
```

The default setup is intended to work without much configuration, but server owners can adjust the path, compression behavior, and scan behavior if needed.

## Ignored maps

Common stock CS:GO maps are ignored by default.

The plugin also creates an ignored maps file:

```text
cfg/source-python/fastdl_ignored_maps.txt
```

You can add extra map names there to block them from FastDL auto-compression. Use one map per line:

```text
de_dust2
de_mirage.bsp
my_private_map
```

Map names can be written with or without `.bsp` and `.nav` . Lines starting with `#` are ignored.

By default, the ignored maps file is loaded when the plugin loads. If `fastdl_reload_ignored_maps` is enabled, the file is reloaded on every FastDL scan.
