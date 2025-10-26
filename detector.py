import zipfile
import os
import threading
import time
import subprocess
import winsound
import json
import csv
import shutil
import requests
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import psutil
import random

class SoundManager:
    @staticmethod
    def play_scan_start():
        try:
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
        except:
            winsound.Beep(800, 200)

    @staticmethod
    def play_scan_complete():
        try:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        except:
            winsound.Beep(600, 300)

    @staticmethod
    def play_threat_found():
        try:
            for freq in [400, 300, 200, 300, 400]: winsound.Beep(freq, 100)
        except:
            winsound.Beep(400, 500)

    @staticmethod
    def play_clean_system():
        try:
            for freq in [1000, 1200, 1500]: winsound.Beep(freq, 150)
        except:
            winsound.Beep(1000, 200)

    @staticmethod
    def play_recycle_info():
        try:
            winsound.Beep(700, 100); winsound.Beep(900, 100)
        except: pass

class CheatDB:
    def __init__(self):
        self.cheat_database = {}
        self.last_update = None
        self._size_index = {}; self._dir_index = {}; self._class_index = {}
        self.load_from_rust_data()
        self._build_indexes()

    def _build_indexes(self):
        self._size_index.clear(); self._dir_index.clear(); self._class_index.clear()
        for cheat_name, cheat_info in self.cheat_database.items():
            for size in cheat_info.get("sizes_kb", []):
                size_key = round(size)
                if size_key not in self._size_index: self._size_index[size_key] = []
                self._size_index[size_key].append(cheat_name)
            for directory in cheat_info.get("directories", []):
                dir_key = directory.split('/')[0] if '/' in directory else directory
                if dir_key not in self._dir_index: self._dir_index[dir_key] = []
                self._dir_index[dir_key].append(cheat_name)
            for class_name in cheat_info.get("classes", []):
                class_key = class_name.split('.')[0] if '.' in class_name else class_name
                if class_key not in self._class_index: self._class_index[class_key] = []
                self._class_index[class_key].append(cheat_name)

    def load_from_rust_data(self):
        self.cheat_database = {
            "DoomsDay": {
                "directories": ["net/java/"], "classes": ["i.class"], "exclude_dirs": [
                    "org/apache/", "com/google/", "io/netty/", "net/minecraft/",
                    "net/minecraftforge/", "optifine/", "javax/", "sun/", "org/lwjgl/"
                ], "sizes_kb": [], "description": "DoomsDay чит", "strict_mode": True, "min_conditions": 2
            },
            "Freecam": {
                "directories": ["net/xolt/freecam/"], "classes": ["freecam.class"], "exclude_dirs": [],
                "sizes_kb": [42.0, 74.0, 1047.0, 1048.0, 1059.0, 1069.0, 1075.0, 1104.0, 1111.0, 1117.0, 1122.0, 1124.0, 1130.0],
                "description": "Freecam мод", "strict_mode": False, "min_conditions": 2
            },
            "NekoClient": {
                "directories": ["net/redteadev/nekoclient/", "zrhx/nekoparts/"],
                "classes": ["necolient.mixins.json", "nekoclient.accesswidener", "nekoclient.class"],
                "exclude_dirs": [], "sizes_kb": [40.0], "description": "NekoClient Ghost чит", "strict_mode": False, "min_conditions": 2
            },
            "SeedCracker": {
                "directories": ["kaptainwutax/seedcracker/"], "classes": ["SeedCracker.class"], "exclude_dirs": [],
                "sizes_kb": [607.0], "description": "SeedCracker", "strict_mode": False, "min_conditions": 2
            },
            "Britva": {
                "directories": ["britva/britva/", "me/britva/myst/"], "classes": ["britva.class"], "exclude_dirs": [],
                "sizes_kb": [1207.0, 782.0, 24.0, 4503.0], "description": "Britva Ghost/AutoMyst", "strict_mode": False, "min_conditions": 2
            },
            "Troxill": {
                "directories": ["ru/zdcoder/troxill/", "the/dmkn/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [1457.0, 165.0, 557.0, 167.0, 603.0], "description": "Troxill Crack", "strict_mode": False, "min_conditions": 2
            },
            "AutoBuy": {
                "directories": ["me/lithium/autobuy/", "com/ch0ffaindustries/ch0ffa_mod/", "ru/xorek/nbtautobuy/", "dev/sxmurxy/"],
                "classes": ["autobuy.class", "buyhelper.class"], "exclude_dirs": [],
                "sizes_kb": [143.0, 301.0, 398.0, 7310.0, 269.0, 2830.0, 2243.0], "description": "AutoBuy читы", "strict_mode": False, "min_conditions": 2
            },
            "WindyAutoMyst": {
                "directories": ["dev/windymyst/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [93.0, 111.0], "description": "WindyAutoMyst", "strict_mode": False, "min_conditions": 2
            },
            "HorekAutoBuy": {
                "directories": ["bre2el/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [144.0, 136.0], "description": "HorekAutoBuy", "strict_mode": False, "min_conditions": 2
            },
            "Inventory Walk": {
                "directories": ["me/pieking1215/invmove/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [119.0, 122.0, 123.0, 125.0, 126.0], "description": "Inventory Walk", "strict_mode": False, "min_conditions": 2
            },
            "WorldDownloader": {
                "directories": ["wdl/"], "classes": ["WorldBackup.class"], "exclude_dirs": [],
                "sizes_kb": [574.0], "description": "WorldDownloader", "strict_mode": False, "min_conditions": 2
            },
            "Ezhitboxes": {
                "directories": ["me/bushroot/hb/", "me/bush1root/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [8.0, 9.0, 10.0, 20.0, 21.0, 66.0], "description": "Ezhitboxes/bush1root", "strict_mode": False, "min_conditions": 2
            },
            "Ch0ffa": {
                "directories": ["com/ch0ffaindustries/ch0ffa_box/", "ch0ffaindustries/ch0ffa_box/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [58.0, 67.0], "description": "Ch0ffa client", "strict_mode": False, "min_conditions": 2
            },
            "RastyPaster": {
                "directories": ["ua/RastyPaster/"], "classes": ["RastyLegit"], "exclude_dirs": [],
                "sizes_kb": [118.0, 138.0], "description": "RastyPaster", "strict_mode": False, "min_conditions": 2
            },
            "Minced": {
                "directories": ["free/minced/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [1610.0], "description": "Minced", "strict_mode": False, "min_conditions": 2
            },
            "ShareX": {
                "directories": ["ru/centbrowser/sharex/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [32.0, 76.0, 45.0], "description": "ShareX", "strict_mode": False, "min_conditions": 2
            },
            "Rolleron": {
                "directories": ["me/rolleron/launch/"], "classes": ["This.class"], "exclude_dirs": [],
                "sizes_kb": [30.0, 31.0, 32.0, 33.0, 34.0, 41.0, 43.0, 55.0, 64.0, 52.0], "description": "Rolleron GH", "strict_mode": False, "min_conditions": 2
            },
            "Bedrock Bricker": {
                "directories": ["net/mcreator/bedrockmod/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [41.8], "description": "Bedrock Bricker", "strict_mode": False, "min_conditions": 2
            },
            "Double Hotbar": {
                "directories": ["com/sidezbros/double_hotbar/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [29.0, 35.0, 36.0, 37.0, 42.0, 43.0], "description": "Double Hotbar", "strict_mode": False, "min_conditions": 2
            },
            "Elytra Swap": {
                "directories": ["net/szum123321/elytra_swap/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [568.0], "description": "Elytra Swap", "strict_mode": False, "min_conditions": 2
            },
            "Armor Hotswap": {
                "directories": ["com/loucaskreger/armorhotswap/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [19.0, 20.0, 21.0, 28.0, 29.0], "description": "Armor Hotswap", "strict_mode": False, "min_conditions": 2
            },
            "GUMBALLOFFMODE": {
                "directories": ["com/moandjiezana/toml/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [2701.0], "description": "GUMBALLOFFMODE", "strict_mode": False, "min_conditions": 2
            },
            "Librarian Trade Finder": {
                "directories": ["de/greenman999/Librarian/"], "classes": ["Trade.class"], "exclude_dirs": [],
                "sizes_kb": [94.0, 100.0, 101.0, 3203.0], "description": "Librarian Trade Finder", "strict_mode": True, "min_conditions": 2
            },
            "Auto Attack": {
                "directories": ["com/tfar/autoattack/", "vin35/autoattack/"], "classes": ["AutoAttack.class"], "exclude_dirs": [],
                "sizes_kb": [4.0, 77.0], "description": "Auto Attack", "strict_mode": False, "min_conditions": 2
            },
            "Entity Outliner": {
                "directories": ["net/entityoutliner/"], "classes": ["EntityOutliner.class"], "exclude_dirs": [],
                "sizes_kb": [32.0, 33.0, 39.0, 41.0], "description": "Entity Outliner", "strict_mode": False, "min_conditions": 2
            },
            "Camera Utils": {
                "directories": ["de/maxhenkel/camerautils/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [88.0, 296.0, 317.0, 344.0, 348.0], "description": "Camera Utils", "strict_mode": False, "min_conditions": 2
            },
            "Wall-Jump": {
                "directories": ["com/jahirtrap/walljump/", "genandnic/walljump/"], "classes": ["WallJump.class"], "exclude_dirs": [],
                "sizes_kb": [155.0, 159.0, 160.0, 161.0, 162.0, 163.0, 165.0], "description": "Wall-Jump TXF", "strict_mode": False, "min_conditions": 2
            },
            "CrystalOptimizer": {
                "directories": ["com/marlowcrystal/marlowcrystal/"], "classes": ["MarlowCrystal.class", "CrystalOptimizer.class"], "exclude_dirs": [],
                "sizes_kb": [90.0, 97.0], "description": "CrystalOptimizer", "strict_mode": False, "min_conditions": 2
            },
            "ClickCrystals": {
                "directories": ["io/github/itzispyder/clickcrystals/"], "classes": ["ClickCrystals.class"], "exclude_dirs": [],
                "sizes_kb": [2800.0, 3000.0, 3200.0, 3500.0, 4000.0], "description": "ClickCrystals", "strict_mode": False, "min_conditions": 2
            },
            "TAKKER": {
                "directories": ["com/example/examplemod/Modules/"], "classes": ["AfkTaker.class"], "exclude_dirs": [],
                "sizes_kb": [9.0], "description": "TAKKER (AfkTaker)", "strict_mode": False, "min_conditions": 2
            },
            "Cortezz": {
                "directories": ["client/cortezz/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [3599.0], "description": "Cortezz client", "strict_mode": False, "min_conditions": 2
            },
            "DezC BetterFPS": {
                "directories": ["com/dezc/betterfps/modules/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [52.0], "description": "DezC BetterFPS HB", "strict_mode": False, "min_conditions": 2
            },
            "NeverVulcan": {
                "directories": ["ru/nedan/vulcan/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [1232.0], "description": "NeverVulcan", "strict_mode": False, "min_conditions": 2
            },
            "ArbuzMyst": {
                "directories": ["me/leansani/phasma/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [293.0, 298.0], "description": "ArbuzMyst/Arbuz GH", "strict_mode": False, "min_conditions": 2
            },
            "SevenMyst": {
                "directories": ["assets/automyst/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [991.0, 992.0, 2346.0], "description": "SevenMyst AutoMyst", "strict_mode": False, "min_conditions": 2
            },
            "Francium": {
                "directories": ["dev/jnic/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [875.0, 3041.0, 1283.0], "description": "Francium", "strict_mode": False, "min_conditions": 2
            },
            "BetterHUD": {
                "directories": ["assets/minecraft/fragment/events/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [3557.0], "description": "BetterHUD HB", "strict_mode": False, "min_conditions": 2
            },
            "Waohitboxes": {
                "directories": ["com/wao/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [36.0], "description": "Waohitboxes", "strict_mode": False, "min_conditions": 2
            },
            "MinecraftOptimization": {
                "directories": ["dev/minecraftoptimization/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [69.0], "description": "MinecraftOptimization HB", "strict_mode": False, "min_conditions": 2
            },
            "Jeed": {
                "directories": [], "classes": ["mixins.jeed"], "exclude_dirs": [],
                "sizes_kb": [43.0], "description": "Jeed", "strict_mode": False, "min_conditions": 2
            },
            "ViaVersion": {
                "directories": ["com/viaversion/"], "classes": [], "exclude_dirs": [],
                "sizes_kb": [5031.0], "description": "ViaVersion", "strict_mode": False, "min_conditions": 2
            },
            "NoHurtCam DanilSimX": {
                "directories": ["nohurtcam/"], "classes": ["ML.class"], "exclude_dirs": [],
                "sizes_kb": [95.0], "description": "NoHurtCam DanilSimX", "strict_mode": False, "min_conditions": 2
            },
            "Fabric hits": {
                "directories": ["net/fabricmc/example/mixin"], "classes": ["RenderMixin.class"], "exclude_dirs": [],
                "sizes_kb": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0], "description": "Fabric hits", "strict_mode": False, "min_conditions": 2
            },
            "SoupApi": {
                "directories": ["assets/soupapi", "org/ChSP/soupapi"],
                "classes": ["SoupAPI-refmap.json", "soupapi.mixins.json", "SoupApi.class"], "exclude_dirs": [],
                "sizes_kb": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0], "description": "SoupApi", "strict_mode": False, "min_conditions": 2
            }
        }

    def enhanced_cheat_detection(self, file_size_kb, file_list_lower):
        detected_cheats = []
        for cheat_name, cheat_info in self.cheat_database.items():
            conditions_met = 0
            found_dirs = []
            found_classes = []

            if cheat_info["directories"]:
                for directory in cheat_info["directories"]:
                    dir_lower = directory.lower().rstrip('/')
                    for filepath in file_list_lower:
                        if f"/{dir_lower}/" in filepath or filepath.startswith(f"{dir_lower}/"):
                            found_dirs.append(directory)
                            conditions_met += 1
                            break
                    if found_dirs: break

            if cheat_info["classes"]:
                for class_name in cheat_info["classes"]:
                    class_lower = class_name.lower()
                    for filepath in file_list_lower:
                        if filepath.endswith(f"/{class_lower}"):
                            found_classes.append(class_name)
                            conditions_met += 1
                            break
                    if found_classes: break

            if cheat_info["sizes_kb"]:
                file_size_rounded = round(file_size_kb)
                for target in cheat_info["sizes_kb"]:
                    target_rounded = round(target)
                    if abs(file_size_rounded - target_rounded) <= 2:
                        conditions_met += 1
                        break

            min_required = cheat_info.get("min_conditions", 2)

            if conditions_met >= min_required:
                detected_cheats.append({
                    "name": cheat_name, "info": cheat_info, "conditions_met": conditions_met,
                    "found_dirs": found_dirs, "found_classes": found_classes
                })

        return detected_cheats

    def update_from_google_sheets(self):
        try:
            sheet_url = "https://docs.google.com/spreadsheets/d/1sEfDVLLO8UehREu2JQUCmzeueH7F_Yx_AzylENOqnHc/export?format=csv&gid=0"
            response = requests.get(sheet_url, timeout=30); response.encoding = 'utf-8'
            if response.status_code == 200:
                csv_data = response.text.splitlines(); csv_data = [line for line in csv_data if line.strip()]
                csv_reader = csv.reader(csv_data); rows = list(csv_reader)
                if len(rows) < 2: return False, "таблица пуста"
                headers = [cell.strip().lower() for cell in rows[0]]
                name_idx = -1; weight_idx = -1; version_idx = -1; comment_idx = -1; proof_idx = -1
                for i, header in enumerate(headers):
                    if 'мод' in header or 'название' in header: name_idx = i
                    elif 'вес' in header or 'размер' in header: weight_idx = i
                    elif 'версия' in header: version_idx = i
                    elif 'комментар' in header: comment_idx = i
                    elif 'доказать' in header or 'как доказать' in header: proof_idx = i
                if name_idx == -1: name_idx = 0
                new_database = {}; updated_count = 0

                for row_num, row in enumerate(rows[1:], start=2):
                    if len(row) <= max(name_idx, weight_idx, proof_idx): continue
                    cheat_name = row[name_idx].strip()
                    if not cheat_name or cheat_name.lower() in ['моды', 'mods', 'название']: continue
                    weight_str = row[weight_idx] if weight_idx < len(row) else ""
                    proof_str = row[proof_idx] if proof_idx < len(row) else ""
                    comment_str = row[comment_idx] if comment_idx < len(row) else ""
                    sizes_kb = self.parse_sizes_from_string(weight_str)
                    directories, classes = self.parse_proof_string(proof_str)
                    strict_mode = False; min_conditions = 2
                    high_risk_cheats = ['soup api', 'topkaautobuy']
                    if any(risk in cheat_name.lower() for risk in high_risk_cheats):
                        strict_mode = True; min_conditions = 3
                    new_database[cheat_name] = {
                        "directories": directories, "classes": classes, "exclude_dirs": [],
                        "sizes_kb": sizes_kb, "description": f"{cheat_name}{' - ' + comment_str if comment_str else ''}",
                        "strict_mode": strict_mode, "min_conditions": min_conditions
                    }
                    updated_count += 1

                old_count = len(self.cheat_database)
                cheats_to_remove = [cheat_name for cheat_name in self.cheat_database if cheat_name not in new_database]
                for cheat_name in cheats_to_remove: del self.cheat_database[cheat_name]
                for cheat_name, cheat_data in new_database.items(): self.cheat_database[cheat_name] = cheat_data

                new_count = len(self.cheat_database); self.last_update = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                self._build_indexes()
                return True, f"база обновлена! добавлено: {updated_count}, всего: {new_count}"
            else: return False, f"ошибка загрузки: {response.status_code}"
        except requests.RequestException as e: return False, f"ошибка сети: {str(e)}"
        except Exception as e: return False, f"ошибка обновления: {str(e)}"

    def parse_sizes_from_string(self, sizes_str):
        sizes = []
        if not sizes_str or not isinstance(sizes_str, str): return sizes
        try:
            cleaned = sizes_str.replace(',', '|').replace(';', '|'); parts = cleaned.split('|')
            for part in parts:
                part = part.strip(); cleaned_part = ''.join(c for c in part if c.isdigit() or c == '.')
                if cleaned_part:
                    try:
                        size_kb = float(cleaned_part)
                        if 0.1 <= size_kb <= 50000: sizes.append(size_kb)
                    except ValueError: continue
        except Exception as e: print(f"ошибка парсинга размеров '{sizes_str}': {e}")
        return sizes

    def parse_proof_string(self, proof_str):
        directories = []; classes = []
        if not proof_str or not isinstance(proof_str, str): return directories, classes
        try:
            proof_str = proof_str.strip(); parts = []
            if '\\' in proof_str: parts = [p.strip() for p in proof_str.split('\\') if p.strip()]
            elif '/' in proof_str: parts = [p.strip() for p in proof_str.split('/') if p.strip()]
            else: parts = [proof_str]
            for part in parts:
                if '.class' in part.lower():
                    class_name = part.split('/')[-1].split('\\')[-1]
                    if class_name and class_name.endswith('.class'): classes.append(class_name)
            if parts:
                dir_parts = [part for part in parts if not part.endswith('.class') and len(part) > 3]
                if dir_parts: directory = '/'.join(dir_parts) + '/'; directories.append(directory.lower())
        except Exception as e: print(f"ошибка парсинга proof '{proof_str}': {e}")
        return directories, classes

    def get_database_info(self):
        total = len(self.cheat_database)
        with_sizes = sum(1 for cheat in self.cheat_database.values() if cheat.get("sizes_kb"))
        with_dirs = sum(1 for cheat in self.cheat_database.values() if cheat.get("directories"))
        with_classes = sum(1 for cheat in self.cheat_database.values() if cheat.get("classes"))
        strict_mode = sum(1 for cheat in self.cheat_database.values() if cheat.get("strict_mode"))
        return {"total": total, "with_sizes": with_sizes, "with_dirs": with_dirs, "with_classes": with_classes,
                "strict_mode": strict_mode, "last_update": self.last_update}

class Detector:
    def __init__(self):
        self.db = CheatDB(); self.active = self.db.cheat_database; self.scanning = False; self.results = []
        self.stats = {"total": 0, "checked": 0, "found": 0, "clean": 0}; self.tolerance_kb = 1.0
        self.max_threads = min(32, (os.cpu_count() or 1) * 4); self.cache_dir = Path("scanner_cache")
        self.cache_dir.mkdir(exist_ok=True); self._file_cache = {}

    def find_jars(self, base):
        jars = []
        try:
            with os.scandir(base) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir(follow_symlinks=False): jars.extend(self.find_jars(entry.path))
                        elif entry.is_file() and entry.name.lower().endswith('.jar'):
                            try:
                                file_size = entry.stat().st_size
                                if 1024 <= file_size <= 50 * 1024 * 1024: jars.append(entry.path)
                            except (OSError, ValueError): continue
                    except (PermissionError, OSError): continue
        except (OSError, PermissionError): pass
        return jars

    def scan_entire_drive(self, drive_letter):
        jars = []
        drive_path = f"{drive_letter}:\\"
        if not os.path.exists(drive_path): return jars
        system_dirs = {"Windows", "Program Files", "Program Files (x86)", "System32", "syswow64", "Recovery", "System Volume Information", "$Recycle.Bin"}

        def scan_drive(path, depth=0):
            if depth > 50: return
            try:
                with os.scandir(path) as entries:
                    for entry in entries:
                        try:
                            if entry.is_dir(follow_symlinks=False):
                                dir_name = entry.name
                                if depth <= 2 and dir_name in system_dirs: continue
                                scan_drive(entry.path, depth + 1)
                            elif entry.is_file() and entry.name.lower().endswith('.jar'):
                                try:
                                    file_size = entry.stat().st_size
                                    if 1024 <= file_size <= 50 * 1024 * 1024: jars.append(entry.path)
                                except (OSError, ValueError): continue
                        except (PermissionError, OSError): continue
            except (PermissionError, OSError): pass

        scan_drive(drive_path)
        return jars

    def check_jar_fast(self, path):
        result = {"path": path, "name": os.path.basename(path), "size": os.path.getsize(path), "is_threat": False,
                  "cheat_type": "Unknown", "details": [], "found_signatures": [], "match_score": 0, "conditions_met": [],
                  "found_dirs": [], "found_classes": [], "file_size_kb": 0}
        try:
            file_size_kb = result["size"] / 1024; result["file_size_kb"] = round(file_size_kb, 1)
            with zipfile.ZipFile(path, 'r') as jar:
                file_list = [f.filename for f in jar.filelist]; file_list_lower = [f.lower() for f in file_list]

            detected_cheats = self.db.enhanced_cheat_detection(file_size_kb, file_list_lower)

            if detected_cheats:
                best_match = detected_cheats[0]
                cheat_info = best_match["info"]
                conditions_met = best_match["conditions_met"]
                if not isinstance(conditions_met, (list, tuple)): conditions_met = [str(conditions_met)]

                result.update({
                    "is_threat": True, "cheat_type": best_match["name"],
                    "found_signatures": best_match["found_dirs"] + best_match["found_classes"],
                    "conditions_met": conditions_met, "match_score": best_match["conditions_met"],
                    "found_dirs": best_match["found_dirs"], "found_classes": best_match["found_classes"],
                    "details": [
                        f"🚨 {cheat_info['description']}", f"Размер: {file_size_kb:.1f} KB",
                        f"Совпадений: {best_match['conditions_met']}",
                        f"Условия: {', '.join(['directory' if best_match['found_dirs'] else '', 'class' if best_match['found_classes'] else '', 'weight'][:best_match['conditions_met']])}"
                    ]
                })
                if cheat_info.get("strict_mode"): result["details"].append("⚠️ строгий режим")
        except zipfile.BadZipFile: result["details"].append("⚠️ поврежденный JAR файл")
        except Exception as e: result["details"].append(f"❌ ошибка анализа: {str(e)}")
        return result

    def scan(self, jars, progress_callback, log_callback):
        self.scanning = True; self.stats = {"total": len(jars), "checked": 0, "found": 0, "clean": 0}; self.results = []

        file_groups = {}
        for file_path in jars:
            try:
                size = os.path.getsize(file_path); file_ext = os.path.splitext(file_path)[1].lower()
                size_key = f"{file_ext}_{round(size / 1024)}"
                if size_key not in file_groups: file_groups[size_key] = []
                file_groups[size_key].append(file_path)
            except: continue

        processed = 0
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            for group_key, file_list in file_groups.items():
                future_to_file = {}
                for file_path in file_list:
                    future = executor.submit(self.check_jar_fast, file_path); future_to_file[future] = file_path

                for future in as_completed(future_to_file):
                    if not self.scanning: executor.shutdown(wait=False); break
                    result = future.result(); processed += 1; self.stats["checked"] = processed

                    if result["is_threat"]:
                        self.stats["found"] += 1; self.results.append(result)
                        conditions_met = result.get("conditions_met", [])
                        if not isinstance(conditions_met, (list, tuple)): conditions_met = [str(conditions_met)] if conditions_met else []
                        conditions_str = " + ".join(map(str, conditions_met))
                        details = f" | директории: {result['found_dirs']}" if result['found_dirs'] else ""
                        details += f" | классы: {result['found_classes']}" if result['found_classes'] else ""
                        log_callback(f"🚨 угроза (JAR): {result['name']} - {result['cheat_type']} [{conditions_str}]{details}")
                    else: self.stats["clean"] += 1

                    if processed % 10 == 0 or processed == self.stats["total"]: progress_callback(self.stats)

        self.scanning = False; return self.results

    def clear_cache(self):
        try:
            self._file_cache.clear()
            if self.cache_dir.exists(): shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True); return True, "кэш очищен"
        except Exception as e: return False, f"ошибка очистки кэша: {str(e)}"