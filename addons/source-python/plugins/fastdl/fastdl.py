from __future__ import annotations
import warnings

bz2_loaded = True
try:
    import bz2
except ImportError:
    warnings.warn('FastDL: bz2 auto-compress feature is disabled because the bz2 module could not be imported.')
    bz2_loaded = False

from threading import Thread
from shutil import copy2
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# Source.Python imports
from stringtables import string_tables
from listeners.tick import Repeat, GameThread
from core import get_public_ip
from paths import CFG_PATH, GAME_PATH
from config.manager import ConfigManager
from cvars import cvar

IGNORED_MAPS_FILE = CFG_PATH / 'fastdl_ignored_maps.txt'

DEFAULT_IGNORED_MAPS = {
    'ar_baggage.bsp', 'ar_dizzy.bsp', 'ar_lunacy.bsp', 'ar_monastery.bsp', 'ar_shoots.bsp',
    'cs_agency.bsp', 'cs_assault.bsp', 'cs_italy.bsp', 'cs_militia.bsp', 'cs_office.bsp',
    'de_ancient.bsp', 'de_anubis.bsp', 'de_bank.bsp', 'de_boyard.bsp', 'de_cache.bsp',
    'de_canals.bsp', 'de_cbble.bsp', 'de_chalice.bsp', 'de_dust2.bsp', 'de_inferno.bsp',
    'de_lake.bsp', 'de_mirage.bsp', 'de_nuke.bsp', 'de_overpass.bsp', 'de_safehouse.bsp',
    'de_shortdust.bsp', 'de_shortnuke.bsp', 'de_stmarc.bsp', 'de_sugarcane.bsp',
    'de_train.bsp', 'de_tuscan.bsp', 'de_vertigo.bsp',
    'dz_blacksite.bsp', 'dz_ember.bsp', 'dz_sirocco.bsp', 'dz_vineyard.bsp',
    'gd_cbble.bsp', 'lobby_mapveto.bsp', 'training1.bsp',
}
DEFAULT_IGNORED_MAPS = {map_name.lower() for map_name in DEFAULT_IGNORED_MAPS}

with ConfigManager('fastdl') as fastdl_cvar:
    use_custom_path = fastdl_cvar.cvar('fastdl_use_custom_path', default=1, description='Use a separate FastDL directory instead of serving files directly from the game folders')
    custom_directory = fastdl_cvar.cvar('fastdl_custom_directory', default='fastdl', description='Custom directory used to store FastDL files. Only applies when fastdl_use_custom_path is enabled.')
    auto_compress = fastdl_cvar.cvar('fastdl_auto_compress', default=1, description='Automatically create and update .bz2 compressed files for FastDL downloads.')
    fallback_uncompressed = fastdl_cvar.cvar('fastdl_fallback_uncompressed', default=1, description='Copy original uncompressed files into the custom FastDL directory when .bz2 compression is disabled, unavailable, or fails. Requires fastdl_use_custom_path.')
    copy_uncompressed = fastdl_cvar.cvar('fastdl_copy_uncompressed', default=0, description='Copy original uncompressed files into the custom FastDL directory. Requires fastdl_use_custom_path. By default, only .bz2 files are created.')
    auto_create_subdirectories = fastdl_cvar.cvar('fastdl_auto_create_subdirectories', default=1, description='Automatically create required FastDL subdirectories such as maps, materials, models, and sound.')
    enable_auto_scan = fastdl_cvar.cvar('fastdl_enable_auto_scan', default=1, description='Enable automatic scanning for new FastDL content.')
    auto_scan_interval = fastdl_cvar.cvar('fastdl_auto_scan_interval', default=60, description='How often, in seconds, the plugin scans for new FastDL content.')
    reload_ignored_maps = fastdl_cvar.cvar('fastdl_reload_ignored_maps', default=0, description='Reload the ignored maps file on every FastDL scan. If disabled, it is only loaded when the plugin loads.')

class FastDLConfig:
    """Configuration for FastDL"""

    def __init__(self):
        self.public_ip: str = get_public_ip()
        self.server_port: int = cvar.find_var('hostport').get_int()

        if use_custom_path.get_int():
            custom_directory_path = custom_directory.get_string()
            if not custom_directory_path:
                custom_directory_path = "fastdl"
            self.fastdl_root_path = GAME_PATH / custom_directory_path / GAME_PATH.name
        else:
            self.fastdl_root_path = GAME_PATH

        self.ignored_map_files = set()
        self.load_ignored_maps_file()

        self.content_types = {
            "maps": {".bsp", ".nav"},
            "models": {".mdl", ".vtx", ".vvd", ".phy"},
            "materials": {".vmt", ".vtf"},
            "sound": {".wav", ".mp3"},
        }

    def load_ignored_maps_file(self) -> None:
        self.ignored_map_files.clear()
        self.ignored_map_files.update(DEFAULT_IGNORED_MAPS)

        if not IGNORED_MAPS_FILE.is_file():
            with open(IGNORED_MAPS_FILE, 'w', encoding='utf-8') as open_file:
                open_file.write(
                    '# Add map names here to block them from FastDL auto-compression.\n'
                    '# Use one map name per line. Both "de_dust2", "de_dust2.nav" and "de_dust2.bsp" are accepted.\n'
                    '# Lines starting with # are ignored.\n'
                    '\n'
                )
            return

        with open(IGNORED_MAPS_FILE, 'r', encoding='utf-8') as open_file:
            for line in open_file:
                map_name = line.strip().lower()

                if not map_name or map_name.startswith('#'):
                    continue

                if not map_name.endswith('nav'):
                    map_name = f'{map_name}.nav'


                if not map_name.endswith('.bsp'):
                    map_name = f'{map_name}.bsp'

                self.ignored_map_files.add(map_name)

class FastDLCompressor:
    def __init__(self, config: FastDLConfig):
        self.config = config
        self.compression_task = Repeat(self.repeat_scanner_callback)

    def ensure_directories_exist(self) -> None:
        root_path = self.config.fastdl_root_path

        if not root_path.is_dir():
            root_path.makedirs_p()
            print(f"FastDL: Created root directory -> {root_path}")

        for folder_name in self.config.content_types:
            target_folder = root_path / folder_name
            if not target_folder.is_dir():
                target_folder.makedirs_p()
                print(f"FastDL: Created subdirectory -> {target_folder}")

        print("FastDL: Directory structure ready.\n")

    @staticmethod
    def run_in_game_thread(function):
        def wrapper(*args, **kwargs):
            thread = GameThread(target=function, args=args, kwargs=kwargs)
            thread.daemon = True
            thread.start()
        return wrapper

    def repeat_scanner_callback(self):
        self.compress_all_content()

    @run_in_game_thread
    def compress_all_content(self) -> None:
        print("FastDL: Scanning for new content...\n")

        if reload_ignored_maps.get_int():
            self.config.load_ignored_maps_file()

        game_root_path = GAME_PATH
        downloadable_files = set(game_root_path.joinpath(file) for file in string_tables.downloadables)

        for folder_name, allowed_extensions in self.config.content_types.items():
            source_folder = game_root_path / folder_name
            target_folder = self.config.fastdl_root_path / folder_name

            if not source_folder.is_dir():
                print(f"  Skipping {folder_name}/ (missing)")
                continue

            print(f"  Processing {folder_name}/ ...")

            new_files_count = 0
            skipped_files_count = 0

            for source_file in source_folder.walkfiles():
                if not source_file.is_file():
                    continue

                file_ext = source_file.suffix.lower()

                if file_ext == ".bz2":
                    continue

                if file_ext not in allowed_extensions:
                    continue

                if folder_name != "maps" and source_file not in downloadable_files:
                    continue

                relative_path = source_file.relpath(source_folder)

                if folder_name == "maps" and relative_path.name.lower() in self.config.ignored_map_files:
                    continue

                compressed_file_path = target_folder / f"{relative_path}.bz2"
                uncompressed_file_path = target_folder / relative_path

                compression_success = False

                if auto_compress.get_int():
                    if not bz2_loaded:
                        print(f"     -> bz2 unavailable, skipped compression for {folder_name}/{relative_path}")

                    elif compressed_file_path.is_file():
                        skipped_files_count += 1
                        compression_success = True

                    else:
                        try:
                            file_bytes = source_file.read_bytes()
                            compressed_bytes = bz2.compress(file_bytes, compresslevel=9)

                            if not compressed_file_path.parent.is_dir():
                                compressed_file_path.parent.makedirs_p()

                            compressed_file_path.write_bytes(compressed_bytes)

                            new_files_count += 1
                            compression_success = True
                            print(f"    -> Compressed {folder_name}/{relative_path}")

                        except Exception as error:
                            print(f"     -> Failed compression {folder_name}/{relative_path}: {error}")

                should_copy_uncompressed = (use_custom_path.get_int() and (copy_uncompressed.get_int() or (fallback_uncompressed.get_int() and not compression_success)))

                if should_copy_uncompressed:
                    if uncompressed_file_path.is_file():
                        skipped_files_count += 1
                        continue

                    if not uncompressed_file_path.parent.is_dir():
                        uncompressed_file_path.parent.makedirs_p()

                    copy2(str(source_file), str(uncompressed_file_path))

                    new_files_count += 1
                    print(f"    -> Copied original {folder_name}/{relative_path}")

            print(f"   -> New: {new_files_count} | Skipped: {skipped_files_count}\n")

class FastDLHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str, **kwargs):
        super().__init__(*args, directory=str(directory), **kwargs)

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, BrokenPipeError):
            pass

    def list_directory(self, path):
        self.send_error(403, "Directory listing is forbidden")
        return None

    def log_message(self, format, *args):
        pass

class FastDLServer:
    """Handles HTTP server lifecycle"""

    def __init__(self, config: FastDLConfig):
        self.config = config
        self.http_server: ThreadingHTTPServer | None = None
        self.server_thread: Thread | None = None

    def start_server(self) -> None:
        try:
            self.http_server = ThreadingHTTPServer(
                (self.config.public_ip, self.config.server_port),
                lambda *args, **kwargs: FastDLHandler(
                    *args,
                    directory=self.config.fastdl_root_path,
                    **kwargs
                )
            )

            print(f"FastDL: Running at http://{self.config.public_ip}:{self.config.server_port}/")
            self.http_server.serve_forever()

        except Exception as error:
            print(f"FastDL: Server error: {error}")

        finally:
            print("FastDL: Server stopped.")

    def stop_server(self) -> None:
        if self.http_server:
            print("FastDL: Shutting down server...")
            self.http_server.shutdown()
            self.http_server.server_close()
            print("FastDL: Server shutdown complete.")


class FastDLPlugin:
    def __init__(self):
        self.config = FastDLConfig()
        self.compressor = FastDLCompressor(self.config)
        self.server = FastDLServer(self.config)

    def load(self) -> None:
        print("=== FastDL Plugin Loading ===")

        if auto_create_subdirectories.get_int():
            self.compressor.ensure_directories_exist()

        self.server.server_thread = Thread(
            target=self.server.start_server,
            daemon=True,
            name="FastDL-HTTP-Server"
        )
        self.server.server_thread.start()

        download_url = f"http://{self.config.public_ip}:{self.config.server_port}/"

        cvar.find_var('sv_downloadurl').set_string(download_url)
        cvar.find_var('sv_allowupload').set_int(0)
        cvar.find_var('sv_allowdownload').set_int(1)

        print(f"FastDL: URL -> {download_url}")

        if enable_auto_scan.get_int():
            self.compressor.compress_all_content()
            self.compressor.compression_task.start(auto_scan_interval.get_int())

        print("=== FastDL Plugin Loaded ===\n")

    def unload(self) -> None:
        print("=== FastDL Plugin Unloading ===")

        self.compressor.compression_task.stop()
        self.server.stop_server()

        if self.server.server_thread and self.server.server_thread.is_alive():
            self.server.server_thread.join(timeout=2.0)

        print("=== FastDL Plugin Unloaded ===\n")


fastdl = FastDLPlugin()


def load():
    fastdl.load()


def unload():
    fastdl.unload()