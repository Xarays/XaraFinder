import zipfile, os, threading, time, tkinter as tk, subprocess, winsound, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import ttk, filedialog, scrolledtext, messagebox
from datetime import datetime, timedelta
import psutil
import random
import requests
import io
from PIL import Image, ImageTk
import webbrowser
import csv
import tempfile
import shutil

# цвета
COLORS = {
    "bg": "#0d1117", "card": "#161b22", "card_dark": "#0d1117",
    "accent": "#58a6ff", "danger": "#f85149", "success": "#3fb950",
    "warning": "#d29922", "text": "#c9d1d9", "text_light": "#8b949e",
    "input_bg": "#1c2128", "hover": "#21262d", "scrollbar": "#30363d"
}


# звуки
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
            for freq in [400, 300, 200, 300, 400]:
                winsound.Beep(freq, 100)
        except:
            winsound.Beep(400, 500)

    @staticmethod
    def play_clean_system():
        try:
            for freq in [1000, 1200, 1500]:
                winsound.Beep(freq, 150)
        except:
            winsound.Beep(1000, 200)

    @staticmethod
    def play_recycle_info():
        try:
            winsound.Beep(700, 100)
            winsound.Beep(900, 100)
        except:
            pass


# бд
class CheatDB:

    def protect_doomsday(self):
        """Принудительная защита DoomsDay - гарантирует его наличие и неизменность"""
        original_doomsday = {
            "directories": ["net/java/"],
            "classes": ["i.class"],
            "exclude_dirs": [
                "org/apache/", "com/google/", "io/netty/", "net/minecraft/",
                "net/minecraftforge/", "optifine/", "javax/", "sun/", "org/lwjgl/"
            ],
            "sizes_kb": [],
            "description": "DoomsDay чит (опасный)",
            "strict_mode": True,
            "min_conditions": 3,
        }

        # Гарантируем, что DoomsDay всегда в базе и неизменен
        self.cheat_database["DoomsDay"] = original_doomsday
        self._build_indexes()

    def enhanced_cheat_detection(self, file_size_kb, file_list_lower):
        """УЛУЧШЕННОЕ обнаружение читов с приоритетом на директории"""
        detected_cheats = []

        for cheat_name, cheat_info in self.cheat_database.items():
            conditions_met = 0
            found_dirs = []
            found_classes = []

            # чек директорий
            if cheat_info["directories"]:
                for directory in cheat_info["directories"]:
                    dir_lower = directory.lower()
                    for filepath in file_list_lower:
                        if dir_lower in filepath:
                            found_dirs.append(directory)
                            conditions_met += 1
                            break
                    if found_dirs:
                        break

            # чек классов
            if cheat_info["classes"] and conditions_met < 2:
                for class_name in cheat_info["classes"]:
                    class_lower = class_name.lower()
                    for filepath in file_list_lower:
                        if class_lower in filepath:
                            found_classes.append(class_name)
                            conditions_met += 1
                            break
                    if found_classes:
                        break

            # чек веса
            if cheat_info["sizes_kb"] and conditions_met < 2:
                file_size_rounded = round(file_size_kb)
                for target in cheat_info["sizes_kb"]:
                    target_rounded = round(target)
                    if abs(file_size_rounded - target_rounded) <= 2:
                        conditions_met += 1
                        break


            min_required = cheat_info.get("min_conditions", 2)
            if conditions_met >= min_required:
                detected_cheats.append({
                    "name": cheat_name,
                    "info": cheat_info,
                    "conditions_met": conditions_met,
                    "found_dirs": found_dirs,
                    "found_classes": found_classes
                })

        return detected_cheats

    def __init__(self):
        self.cheat_database = {}
        self.last_update = None
        self._size_index = {}
        self._dir_index = {}
        self._class_index = {}
        self.load_from_rust_data()
        self._build_indexes()

    def _build_indexes(self):
        self._size_index.clear()
        self._dir_index.clear()
        self._class_index.clear()

        for cheat_name, cheat_info in self.cheat_database.items():
            for size in cheat_info.get("sizes_kb", []):
                size_key = round(size)
                if size_key not in self._size_index:
                    self._size_index[size_key] = []
                self._size_index[size_key].append(cheat_name)

            for directory in cheat_info.get("directories", []):
                dir_key = directory.split('/')[0] if '/' in directory else directory
                if dir_key not in self._dir_index:
                    self._dir_index[dir_key] = []
                self._dir_index[dir_key].append(cheat_name)

            for class_name in cheat_info.get("classes", []):
                class_key = class_name.split('.')[0] if '.' in class_name else class_name
                if class_key not in self._class_index:
                    self._class_index[class_key] = []
                self._class_index[class_key].append(cheat_name)

    def get_possible_cheats_by_size(self, file_size_kb):
        size_key = round(file_size_kb)
        possible_matches = set()

        for check_size in [size_key - 1, size_key, size_key + 1]:
            if check_size in self._size_index:
                possible_matches.update(self._size_index[check_size])

        return list(possible_matches)

    def get_possible_cheats_by_path_elements(self, file_list):
        possible_matches = set()


        for filepath in file_list:
            path_lower = filepath.lower()


            for dir_key, cheat_names in self._dir_index.items():
                if dir_key and len(dir_key) > 2 and dir_key in path_lower:
                    possible_matches.update(cheat_names)


            for class_key, cheat_names in self._class_index.items():
                if class_key and len(class_key) > 2 and class_key in path_lower:
                    possible_matches.update(cheat_names)


            path_parts = path_lower.split('/')
            for part in path_parts:
                if len(part) > 4:

                    for dir_key, cheat_names in self._dir_index.items():
                        if dir_key and dir_key in part:
                            possible_matches.update(cheat_names)

                    for class_key, cheat_names in self._class_index.items():
                        if class_key and class_key in part:
                            possible_matches.update(cheat_names)

        return list(possible_matches)

    def load_from_rust_data(self):

        self.cheat_database = {
            "DoomsDay": {
                "directories": ["net/java/"],
                "classes": ["i.class"],
                "exclude_dirs": [
                    "org/apache/", "com/google/", "io/netty/", "net/minecraft/",
                    "net/minecraftforge/", "optifine/", "javax/", "sun/", "org/lwjgl/"
                ],
                "sizes_kb": [],
                "description": "DoomsDay чит (опасный)",
                "strict_mode": True,
                "min_conditions": 3,
            },
            "Freecam": {
                "directories": ["net/xolt/freecam/"],
                "classes": ["freecam.class"],
                "exclude_dirs": [],
                "sizes_kb": [42.0, 74.0, 1047.0, 1048.0, 1059.0, 1069.0, 1075.0, 1104.0, 1111.0, 1117.0, 1122.0, 1124.0,
                             1130.0],
                "description": "Freecam мод",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "NekoClient": {
                "directories": ["net/redteadev/nekoclient/", "zrhx/nekoparts/"],
                "classes": ["necolient.mixins.json", "nekoclient.accesswidener", "nekoclient.class"],
                "exclude_dirs": [],
                "sizes_kb": [40.0],
                "description": "NekoClient Ghost чит",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "SeedCracker": {
                "directories": ["kaptainwutax/seedcracker/"],
                "classes": ["SeedCracker.class"],
                "exclude_dirs": [],
                "sizes_kb": [607.0],
                "description": "SeedCracker",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Britva": {
                "directories": ["britva/britva/", "me/britva/myst/"],
                "classes": ["britva.class"],
                "exclude_dirs": [],
                "sizes_kb": [1207.0, 782.0, 24.0, 4503.0],
                "description": "Britva Ghost/AutoMyst",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Troxill": {
                "directories": ["ru/zdcoder/troxill/", "the/dmkn/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [1457.0, 165.0, 557.0, 167.0, 603.0],
                "description": "Troxill Crack",
                "strict_mode": False,
                "min_conditions": 1,
            },
            "AutoBuy": {
                "directories": ["me/lithium/autobuy/", "com/ch0ffaindustries/ch0ffa_mod/", "ru/xorek/nbtautobuy/",
                                "dev/sxmurxy/"],
                "classes": ["autobuy.class", "buyhelper.class"],
                "exclude_dirs": [],
                "sizes_kb": [143.0, 301.0, 398.0, 7310.0, 269.0, 2830.0, 2243.0],
                "description": "AutoBuy читы",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "WindyAutoMyst": {
                "directories": ["dev/windymyst/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [93.0, 111.0],
                "description": "WindyAutoMyst",
                "strict_mode": False,
                "min_conditions": 1,
            },
            "HorekAutoBuy": {
                "directories": ["bre2el/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [144.0, 136.0],
                "description": "HorekAutoBuy (под fpsreducer)",
                "strict_mode": False,
                "min_conditions": 1,
            },
            "Inventory Walk": {
                "directories": ["me/pieking1215/invmove/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [119.0, 122.0, 123.0, 125.0, 126.0],
                "description": "Inventory Walk",
                "strict_mode": False,
                "min_conditions": 1,
            },
            "WorldDownloader": {
                "directories": ["wdl/"],
                "classes": ["WorldBackup.class"],
                "exclude_dirs": [],
                "sizes_kb": [574.0],
                "description": "WorldDownloader",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Ezhitboxes": {
                "directories": ["me/bushroot/hb/", "me/bush1root/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [8.0, 9.0, 10.0, 20.0, 21.0, 66.0],
                "description": "Ezhitboxes/bush1root",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Ch0ffa": {
                "directories": ["com/ch0ffaindustries/ch0ffa_box/", "ch0ffaindustries/ch0ffa_box/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [58.0, 67.0],
                "description": "Ch0ffa client",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "RastyPaster": {
                "directories": ["ua/RastyPaster/"],
                "classes": ["RastyLegit"],
                "exclude_dirs": [],
                "sizes_kb": [118.0, 138.0],
                "description": "RastyPaster",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Minced": {
                "directories": ["free/minced/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [1610.0],
                "description": "Minced",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "ShareX": {
                "directories": ["ru/centbrowser/sharex/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [32.0, 76.0, 45.0],
                "description": "ShareX",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Rolleron": {
                "directories": ["me/rolleron/launch/"],
                "classes": ["This.class"],
                "exclude_dirs": [],
                "sizes_kb": [30.0, 31.0, 32.0, 33.0, 34.0, 41.0, 43.0, 55.0, 64.0, 52.0],
                "description": "Rolleron GH",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Bedrock Bricker": {
                "directories": ["net/mcreator/bedrockmod/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [41.8],
                "description": "Bedrock Bricker",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Double Hotbar": {
                "directories": ["com/sidezbros/double_hotbar/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [29.0, 35.0, 36.0, 37.0, 42.0, 43.0],
                "description": "Double Hotbar",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Elytra Swap": {
                "directories": ["net/szum123321/elytra_swap/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [568.0],
                "description": "Elytra Swap",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Armor Hotswap": {
                "directories": ["com/loucaskreger/armorhotswap/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [19.0, 20.0, 21.0, 28.0, 29.0],
                "description": "Armor Hotswap",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "GUMBALLOFFMODE": {
                "directories": ["com/moandjiezana/toml/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [2701.0],
                "description": "GUMBALLOFFMODE",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Librarian Trade Finder": {
                "directories": ["de/greenman999/Librarian/"],
                "classes": ["Trade.class"],
                "exclude_dirs": [],
                "sizes_kb": [94.0, 100.0, 101.0, 3203.0],
                "description": "Librarian Trade Finder",
                "strict_mode": True,
                "min_conditions": 2,
            },
            "Auto Attack": {
                "directories": ["com/tfar/autoattack/", "vin35/autoattack/"],
                "classes": ["AutoAttack.class"],
                "exclude_dirs": [],
                "sizes_kb": [4.0, 77.0],
                "description": "Auto Attack",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Entity Outliner": {
                "directories": ["net/entityoutliner/"],
                "classes": ["EntityOutliner.class"],
                "exclude_dirs": [],
                "sizes_kb": [32.0, 33.0, 39.0, 41.0],
                "description": "Entity Outliner",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Camera Utils": {
                "directories": ["de/maxhenkel/camerautils/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [88.0, 296.0, 317.0, 344.0, 348.0],
                "description": "Camera Utils",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Wall-Jump": {
                "directories": ["com/jahirtrap/walljump/", "genandnic/walljump/"],
                "classes": ["WallJump.class"],
                "exclude_dirs": [],
                "sizes_kb": [155.0, 159.0, 160.0, 161.0, 162.0, 163.0, 165.0],
                "description": "Wall-Jump TXF",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "CrystalOptimizer": {
                "directories": ["com/marlowcrystal/marlowcrystal/"],
                "classes": ["MarlowCrystal.class", "CrystalOptimizer.class"],
                "exclude_dirs": [],
                "sizes_kb": [90.0, 97.0],
                "description": "CrystalOptimizer",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "ClickCrystals": {
                "directories": ["io/github/itzispyder/clickcrystals/"],
                "classes": ["ClickCrystals.class"],
                "exclude_dirs": [],
                "sizes_kb": [2800.0, 3000.0, 3200.0, 3500.0, 4000.0],
                "description": "ClickCrystals",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "TAKKER": {
                "directories": ["com/example/examplemod/Modules/"],
                "classes": ["AfkTaker.class"],
                "exclude_dirs": [],
                "sizes_kb": [9.0],
                "description": "TAKKER (AfkTaker)",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Cortezz": {
                "directories": ["client/cortezz/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [3599.0],
                "description": "Cortezz client",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "DezC BetterFPS": {
                "directories": ["com/dezc/betterfps/modules/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [52.0],
                "description": "DezC BetterFPS HB",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "NeverVulcan": {
                "directories": ["ru/nedan/vulcan/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [1232.0],
                "description": "NeverVulcan",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "ArbuzMyst": {
                "directories": ["me/leansani/phasma/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [293.0, 298.0],
                "description": "ArbuzMyst/Arbuz GH",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "SevenMyst": {
                "directories": ["assets/automyst/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [991.0, 992.0, 2346.0],
                "description": "SevenMyst AutoMyst",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Francium": {
                "directories": ["dev/jnic/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [875.0, 3041.0, 1283.0],
                "description": "Francium",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "BetterHUD": {
                "directories": ["assets/minecraft/fragment/events/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [3557.0],
                "description": "BetterHUD HB",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Waohitboxes": {
                "directories": ["com/wao/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [36.0],
                "description": "Waohitboxes",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "MinecraftOptimization": {
                "directories": ["dev/minecraftoptimization/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [69.0],
                "description": "MinecraftOptimization HB",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Jeed": {
                "directories": [],
                "classes": ["mixins.jeed"],
                "exclude_dirs": [],
                "sizes_kb": [43.0],
                "description": "Jeed",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "ViaVersion": {
                "directories": ["com/viaversion/"],
                "classes": [],
                "exclude_dirs": [],
                "sizes_kb": [5031.0],
                "description": "ViaVersion",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "NoHurtCam DanilSimX": {
                "directories": ["nohurtcam/"],
                "classes": ["ML.class"],
                "exclude_dirs": [],
                "sizes_kb": [95.0],
                "description": "NoHurtCam DanilSimX",
                "strict_mode": False,
                "min_conditions": 2,
            },
            "Fabric hits": {
                "directories": ["net/fabricmc/example/mixin"],
                "classes": ["RenderMixin.class"],
                "exclude_dirs": [],
                "sizes_kb": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
                "description": "Fabric hits",
                "strict_mode": False,
                "min_conditions": 2,
            }
        }

        self.protect_doomsday()

    def update_from_google_sheets(self):
        # подгрузка бд из гугл таблиц, сложна
        try:
            sheet_url = "https://docs.google.com/spreadsheets/d/1sEfDVLLO8UehREu2JQUCmzeueH7F_Yx_AzylENOqnHc/export?format=csv&gid=0"
            response = requests.get(sheet_url, timeout=30)
            response.encoding = 'utf-8'

            if response.status_code == 200:
                csv_data = response.text.splitlines()
                csv_data = [line for line in csv_data if line.strip()]
                csv_reader = csv.reader(csv_data)
                rows = list(csv_reader)

                if len(rows) < 2:
                    return False, "Таблица пуста или содержит только заголовки"

                headers = [cell.strip().lower() for cell in rows[0]]
                name_idx = -1
                weight_idx = -1
                version_idx = -1
                comment_idx = -1
                proof_idx = -1

                for i, header in enumerate(headers):
                    if 'мод' in header or 'название' in header:
                        name_idx = i
                    elif 'вес' in header or 'размер' in header:
                        weight_idx = i
                    elif 'версия' in header:
                        version_idx = i
                    elif 'комментар' in header:
                        comment_idx = i
                    elif 'доказать' in header or 'как доказать' in header:
                        proof_idx = i

                if name_idx == -1:
                    name_idx = 0

                new_database = {}
                updated_count = 0

                original_doomsday = self.cheat_database.get("DoomsDay")

                for row_num, row in enumerate(rows[1:], start=2):
                    if len(row) <= max(name_idx, weight_idx, proof_idx):
                        continue

                    cheat_name = row[name_idx].strip()

                    if cheat_name.lower() == "doomsday":
                        continue

                    if not cheat_name or cheat_name.lower() in ['моды', 'mods', 'название']:
                        continue

                    weight_str = row[weight_idx] if weight_idx < len(row) else ""
                    proof_str = row[proof_idx] if proof_idx < len(row) else ""
                    comment_str = row[comment_idx] if comment_idx < len(row) else ""

                    sizes_kb = self.parse_sizes_from_string(weight_str)
                    directories, classes = self.parse_proof_string(proof_str)

                    strict_mode = False
                    min_conditions = 2

                    high_risk_cheats = ['soup api', 'topkaautobuy']
                    if any(risk in cheat_name.lower() for risk in high_risk_cheats):
                        strict_mode = True
                        min_conditions = 3

                    new_database[cheat_name] = {
                        "directories": directories,
                        "classes": classes,
                        "exclude_dirs": [],
                        "sizes_kb": sizes_kb,
                        "description": f"{cheat_name}{' - ' + comment_str if comment_str else ''}",
                        "strict_mode": strict_mode,
                        "min_conditions": min_conditions
                    }

                    updated_count += 1

                old_count = len(self.cheat_database)

                cheats_to_remove = []
                for cheat_name in self.cheat_database:
                    if cheat_name not in new_database and cheat_name.lower() != "doomsday":
                        cheats_to_remove.append(cheat_name)

                for cheat_name in cheats_to_remove:
                    del self.cheat_database[cheat_name]

                for cheat_name, cheat_data in new_database.items():
                    self.cheat_database[cheat_name] = cheat_data

                if original_doomsday and "DoomsDay" not in self.cheat_database:
                    self.cheat_database["DoomsDay"] = original_doomsday

                new_count = len(self.cheat_database)

                self.last_update = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                self._build_indexes()

                return True, f"База обновлена! Добавлено: {updated_count}, Всего записей: {new_count} (+{new_count - old_count}). DoomsDay защищен от изменений."

            else:
                return False, f"Ошибка загрузки: {response.status_code}"

        except requests.RequestException as e:
            return False, f"Ошибка сети: {str(e)}"
        except Exception as e:
            return False, f"Ошибка обновления: {str(e)}"

    def parse_sizes_from_string(self, sizes_str):
        sizes = []
        if not sizes_str or not isinstance(sizes_str, str):
            return sizes

        try:
            cleaned = sizes_str.replace(',', '|').replace(';', '|')
            parts = cleaned.split('|')

            for part in parts:
                part = part.strip()
                if not part:
                    continue

                cleaned_part = ''.join(c for c in part if c.isdigit() or c == '.')
                if cleaned_part:
                    try:
                        size_kb = float(cleaned_part)
                        if 0.1 <= size_kb <= 50000:
                            sizes.append(size_kb)
                    except ValueError:
                        continue

        except Exception as e:
            print(f"Ошибка парсинга размеров '{sizes_str}': {e}")

        return sizes

    def parse_proof_string(self, proof_str):
        directories = []
        classes = []

        if not proof_str or not isinstance(proof_str, str):
            return directories, classes

        try:
            proof_str = proof_str.strip()
            parts = []
            if '\\' in proof_str:
                parts = [p.strip() for p in proof_str.split('\\') if p.strip()]
            elif '/' in proof_str:
                parts = [p.strip() for p in proof_str.split('/') if p.strip()]
            else:
                parts = [proof_str]

            for part in parts:
                if '.class' in part.lower():
                    class_name = part.split('/')[-1].split('\\')[-1]
                    if class_name and class_name.endswith('.class'):
                        classes.append(class_name)

            if parts:
                dir_parts = []
                for part in parts:
                    if not part.endswith('.class') and len(part) > 3:
                        dir_parts.append(part)

                if dir_parts:
                    directory = '/'.join(dir_parts) + '/'
                    directories.append(directory.lower())

        except Exception as e:
            print(f"Ошибка парсинга proof '{proof_str}': {e}")

        return directories, classes

    def _save_backup(self):
        try:
            backup_dir = Path("database_backups")
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"cheat_db_backup_{timestamp}.json"

            backup_data = {
                "timestamp": self.last_update,
                "database": self.cheat_database,
                "total_entries": len(self.cheat_database)
            }

            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)

            backup_files = sorted(backup_dir.glob("cheat_db_backup_*.json"))
            for old_backup in backup_files[:-10]:
                old_backup.unlink()

        except Exception as e:
            print(f"Ошибка создания бэкапа: {e}")

    def restore_backup(self, backup_file):
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            self.cheat_database = backup_data.get("database", {})
            self.last_update = backup_data.get("timestamp")

            self.protect_doomsday()

            return True, f"База восстановлена! Записей: {len(self.cheat_database)}"
        except Exception as e:
            return False, f"Ошибка восстановления: {str(e)}"

    def get_database_info(self):
        total = len(self.cheat_database)
        with_sizes = sum(1 for cheat in self.cheat_database.values() if cheat.get("sizes_kb"))
        with_dirs = sum(1 for cheat in self.cheat_database.values() if cheat.get("directories"))
        with_classes = sum(1 for cheat in self.cheat_database.values() if cheat.get("classes"))
        strict_mode = sum(1 for cheat in self.cheat_database.values() if cheat.get("strict_mode"))

        return {
            "total": total,
            "with_sizes": with_sizes,
            "with_dirs": with_dirs,
            "with_classes": with_classes,
            "strict_mode": strict_mode,
            "last_update": self.last_update
        }

    def validate_database(self):
        errors = []
        warnings = []

        if "DoomsDay" not in self.cheat_database:
            errors.append("DoomsDay отсутствует в базе данных!")
        else:
            doomsday_data = self.cheat_database["DoomsDay"]
            expected_dirs = ["net/java/"]
            expected_classes = ["i.class"]

            if doomsday_data.get("directories") != expected_dirs:
                warnings.append("DoomsDay: директории изменены")
            if doomsday_data.get("classes") != expected_classes:
                warnings.append("DoomsDay: классы изменены")
            if not doomsday_data.get("strict_mode", False):
                warnings.append("DoomsDay: строгий режим отключен")

        for name, data in self.cheat_database.items():
            if name == "DoomsDay":
                continue  # DoomsDay уже проверен

            if not name.strip():
                errors.append("Пустое название чита")
                continue

            if not data.get("directories") and not data.get("classes"):
                warnings.append(f"{name}: нет директорий или классов")

            if not data.get("sizes_kb"):
                warnings.append(f"{name}: нет информации о размерах")

            if data.get("min_conditions", 1) < 1:
                errors.append(f"{name}: min_conditions меньше 1")

        return errors, warnings


# детектор
class Detector:

    def simple_cheat_check(self, file_size_kb, file_list_lower, cheat_name, cheat_info):
        """Упрощенная проверка чита - находит DoomsDay и NekoClient"""
        conditions = []
        found_dirs = []
        found_classes = []

        # Проверка директорий
        if cheat_info["directories"]:
            for directory in cheat_info["directories"]:
                dir_lower = directory.lower()
                for filepath in file_list_lower:
                    if dir_lower in filepath:
                        conditions.append("directory")
                        found_dirs.append(directory)
                        break
                if found_dirs:
                    break

        # Проверка классов
        if cheat_info["classes"]:
            for class_name in cheat_info["classes"]:
                class_lower = class_name.lower()
                for filepath in file_list_lower:
                    if class_lower in filepath:
                        conditions.append("class")
                        found_classes.append(class_name)
                        break
                if found_classes:
                    break

        # Проверка веса
        if cheat_info["sizes_kb"]:
            file_size_rounded = round(file_size_kb)
            for target in cheat_info["sizes_kb"]:
                target_rounded = round(target)
                if abs(file_size_rounded - target_rounded) <= 2:
                    conditions.append("weight")
                    break

        min_required = 1

        if cheat_info.get("strict_mode"):
            if cheat_info["directories"] and cheat_info["classes"]:
                for directory in cheat_info["directories"]:
                    dir_lower = directory.lower()
                    for class_name in cheat_info["classes"]:
                        class_lower = class_name.lower()
                        expected_path = dir_lower + class_lower
                        for filepath in file_list_lower:
                            if expected_path in filepath:
                                conditions.append("strict")
                                break

        return len(conditions) >= min_required, conditions, found_dirs, found_classes

    def __init__(self):
        self.db = CheatDB()
        self.active = self.db.cheat_database
        self.scanning = False
        self.results = []
        self.stats = {"total": 0, "checked": 0, "found": 0, "clean": 0}
        self.tolerance_kb = 1.0
        self.max_threads = min(32, (os.cpu_count() or 1) * 4)
        self.cache_dir = Path("scanner_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self._file_cache = {}

    def find_jars(self, base):
        jars = []
        ignored_dirs = {
            "Windows", "Program Files", "Program Files (x86)", "AppData\\Local\\Temp",
            "System32", "syswow64", "Microsoft", "Adobe", "Intel", "AMD", "NVIDIA",
            "Windows.old", "Recovery", "$Recycle.Bin", "System Volume Information"
        }

        try:
            with os.scandir(base) as entries:
                for entry in entries:
                    if entry.is_dir():
                        dir_name = entry.name
                        if dir_name in ignored_dirs or dir_name.startswith('.'):
                            continue
                        jars.extend(self.find_jars(entry.path))
                    elif entry.is_file() and entry.name.lower().endswith('.jar'):
                        try:
                            file_size = entry.stat().st_size
                            if 1024 <= file_size <= 50 * 1024 * 1024:
                                jars.append(entry.path)
                        except (OSError, ValueError):
                            continue
        except (OSError, PermissionError):
            pass

        return jars

    def check_weight_match(self, file_size_kb, cheat_sizes):
        if not cheat_sizes:
            return False

        file_size_rounded = round(file_size_kb)
        for target in cheat_sizes:
            target_rounded = round(target)
            if abs(file_size_rounded - target_rounded) <= 1:
                return True
        return False

    def has_legit_libraries(self, files, exclude_dirs):
        if not exclude_dirs:
            return False

        for filepath in files[:100]:
            file_lower = filepath.lower()
            for exclude in exclude_dirs:
                if exclude in file_lower:
                    return True
        return False

    def check_jar_fast(self, path):
        result = {
            "path": path,
            "name": os.path.basename(path),
            "size": os.path.getsize(path),
            "is_threat": False,
            "cheat_type": "Unknown",
            "details": [],
            "found_signatures": [],
            "match_score": 0,
            "conditions_met": [],
            "found_dirs": [],
            "found_classes": [],
            "file_size_kb": 0
        }

        try:
            file_size_kb = result["size"] / 1024
            result["file_size_kb"] = round(file_size_kb, 1)

            with zipfile.ZipFile(path, 'r') as jar:
                file_list = [f.filename for f in jar.filelist]
                file_list_lower = [f.lower() for f in file_list]


            possible_cheats_by_size = self.db.get_possible_cheats_by_size(file_size_kb)
            possible_cheats_by_path = self.db.get_possible_cheats_by_path_elements(file_list_lower)

            possible_cheats = set(possible_cheats_by_size + possible_cheats_by_path)

            if not possible_cheats:
                return result

            for cheat_name in possible_cheats:
                cheat_info = self.active[cheat_name]
                conditions_met = []
                found_items = []
                found_dirs = []
                found_classes = []


                if cheat_info.get("strict_mode") and self.has_legit_libraries(file_list_lower,
                                                                              cheat_info["exclude_dirs"]):
                    continue


                dir_found = False
                if cheat_info["directories"]:
                    for directory in cheat_info["directories"]:
                        dir_lower = directory.lower()
                        for filepath in file_list_lower:
                            if dir_lower in filepath:
                                dir_found = True
                                found_items.append(f"DIR: {directory}")
                                found_dirs.append(directory)
                                break
                        if dir_found:
                            break
                    if dir_found:
                        conditions_met.append("directory")


                class_found = False
                if cheat_info["classes"]:
                    for class_name in cheat_info["classes"]:
                        class_lower = class_name.lower()
                        for filepath in file_list_lower:
                            if class_lower in filepath:
                                class_found = True
                                found_items.append(f"CLASS: {class_name}")
                                found_classes.append(class_name)
                                break
                        if class_found:
                            break
                    if class_found:
                        conditions_met.append("class")


                weight_found = False
                if cheat_info["sizes_kb"]:
                    weight_found = self.check_weight_match(file_size_kb, cheat_info["sizes_kb"])
                    if weight_found:
                        conditions_met.append("weight")
                        found_items.append(f"WEIGHT: {file_size_kb:.1f}KB")


                min_required = cheat_info.get("min_conditions", 2)
                is_detected = False

                if cheat_info.get("strict_mode"):

                    strict_match_found = False
                    if cheat_info["directories"] and cheat_info["classes"]:
                        for directory in cheat_info["directories"]:
                            dir_lower = directory.lower()
                            for class_name in cheat_info["classes"]:
                                class_lower = class_name.lower()
                                expected_path = dir_lower + class_lower
                                for filepath in file_list_lower:
                                    if expected_path in filepath:
                                        strict_match_found = True
                                        found_items.append(f"STRICT: {directory} + {class_name}")
                                        found_dirs.append(directory)
                                        found_classes.append(class_name)
                                        break
                                if strict_match_found:
                                    break
                            if strict_match_found:
                                break
                        if strict_match_found:
                            conditions_met.append("strict_class")
                            is_detected = True
                else:

                    has_main_condition = dir_found or class_found
                    has_additional_condition = weight_found or (dir_found and class_found)

                    if has_main_condition and (has_additional_condition or len(conditions_met) >= min_required):
                        is_detected = True


                if not is_detected and (dir_found or class_found):

                    if len(conditions_met) >= min_required:
                        is_detected = True

                    elif (dir_found or class_found) and weight_found:
                        is_detected = True

                    elif dir_found and class_found:
                        is_detected = True

                if is_detected:
                    result.update({
                        "is_threat": True,
                        "cheat_type": cheat_name,
                        "found_signatures": found_items,
                        "conditions_met": conditions_met,
                        "match_score": len(conditions_met),
                        "found_dirs": found_dirs,
                        "found_classes": found_classes,
                        "details": [
                            f"🚨 {cheat_info['description']}",
                            f"Размер: {file_size_kb:.1f} KB",
                            f"Совпадений: {len(conditions_met)}",
                            f"Условия: {', '.join(conditions_met)}"
                        ]
                    })
                    if cheat_info.get("strict_mode"):
                        result["details"].append("⚠️ СТРОГИЙ РЕЖИМ - проверены исключения")
                    break

        except zipfile.BadZipFile:
            result["details"].append("⚠️ Поврежденный JAR файл")
        except Exception as e:
            result["details"].append(f"❌ Ошибка анализа: {str(e)}")

        return result

    def scan(self, jars, progress_callback, log_callback):

        self.scanning = True
        self.stats = {"total": len(jars), "checked": 0, "found": 0, "clean": 0}
        self.results = []

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_jar = {executor.submit(self.check_jar_fast, jar): jar for jar in jars}

            for future in as_completed(future_to_jar):
                if not self.scanning:
                    break

                result = future.result()
                self.stats["checked"] += 1

                if result["is_threat"]:
                    self.stats["found"] += 1
                    self.results.append(result)
                    # Детальное логирование найденных угроз
                    conditions_str = " + ".join(result["conditions_met"])
                    details = f" | Директории: {result['found_dirs']}" if result['found_dirs'] else ""
                    details += f" | Классы: {result['found_classes']}" if result['found_classes'] else ""
                    log_callback(f"🚨 УГРОЗА: {result['name']} - {result['cheat_type']} [{conditions_str}]{details}")
                else:
                    self.stats["clean"] += 1

                progress_callback(self.stats)

        self.scanning = False
        return self.results

    def clear_cache(self):
        try:
            self._file_cache.clear()
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)
            return True, "Кэш очищен"
        except Exception as e:
            return False, f"Ошибка очистки кэша: {str(e)}"


# чекаем корзинууу
class RecycleChecker:
    def __init__(self):
        self.clear_history = []
        self.load_history()

    def load_history(self):
        try:
            history_file = Path("recycle_history.json")
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.clear_history = data.get("clear_history", [])
        except:
            self.clear_history = []

    def save_history(self):
        try:
            with open("recycle_history.json", 'w', encoding='utf-8') as f:
                json.dump({"clear_history": self.clear_history}, f, ensure_ascii=False, indent=2)
        except:
            pass

    def check(self):
        result = {"deleted": [], "cleared": False, "clear_date": None, "clear_time": None, "clear_history": []}

        try:
            result["clear_history"] = self.clear_history.copy()

            ps_command = """
            Get-ChildItem -Path $env:SystemDrive\\`$Recycle.Bin -Recurse -Force -ErrorAction SilentlyContinue | 
            Where-Object { $_.PSIsContainer -eq $false } |
            Select-Object Name, Length, LastWriteTime, FullName |
            ConvertTo-Json
            """

            process = subprocess.Popen([
                "powershell", "-Command", ps_command
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

            stdout, stderr = process.communicate(timeout=30)

            if stdout:
                try:
                    files_data = json.loads(stdout.decode('utf-8'))
                    if not isinstance(files_data, list):
                        files_data = [files_data]

                    now = datetime.now()
                    time_ago = now - timedelta(days=14)

                    for file_info in files_data:
                        try:
                            file_name = file_info.get('Name', '')
                            file_size = file_info.get('Length', 0) / 1024
                            last_write = file_info.get('LastWriteTime', '')
                            full_path = file_info.get('FullName', '')

                            if file_name.lower().endswith(('.jar', '.exe', '.dll', '.class')):
                                if last_write:
                                    if ':' in last_write:
                                        mod_time = datetime.strptime(last_write, '%m/%d/%Y %H:%M:%S')
                                    else:
                                        mod_time = datetime.strptime(last_write, '%m/%d/%Y')

                                    if mod_time >= time_ago:
                                        result["deleted"].append({
                                            "name": file_name,
                                            "date": mod_time.strftime("%d.%m.%Y"),
                                            "time": mod_time.strftime("%H:%M:%S"),
                                            "size": round(file_size, 1),
                                            "path": full_path
                                        })
                        except Exception as e:
                            continue

                except json.JSONDecodeError:
                    self._fallback_check(result)
            else:
                self._fallback_check(result)

        except Exception as e:
            self._fallback_check(result)

        result["deleted"].sort(key=lambda x: f"{x['date']} {x['time']}", reverse=True)

        if not result["deleted"]:
            result["cleared"] = True
            clear_info = self._get_clear_time()
            if clear_info:
                result["clear_date"] = clear_info["date"]
                result["clear_time"] = clear_info["time"]

                new_clear = {
                    "date": clear_info["date"],
                    "time": clear_info["time"],
                    "detected_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                }

                if not any(clear["date"] == new_clear["date"] and clear["time"] == new_clear["time"]
                           for clear in self.clear_history):
                    self.clear_history.append(new_clear)
                    self.save_history()

        return result

    def _fallback_check(self, result):
        now = datetime.now()
        time_ago = now - timedelta(days=14)

        for drive in [f"{chr(c)}:\\\\" for c in range(65, 91) if os.path.exists(f"{chr(c)}:\\\\")]:
            recycle_bin = os.path.join(drive, "$Recycle.Bin")
            if not os.path.isdir(recycle_bin):
                continue

            try:
                for user_folder in os.listdir(recycle_bin):
                    user_path = os.path.join(recycle_bin, user_folder)
                    if not os.path.isdir(user_path):
                        continue

                    for root, dirs, files in os.walk(user_path):
                        for file in files:
                            if file.lower().endswith((".jar", ".exe", ".dll", ".class")):
                                file_path = os.path.join(root, file)
                                try:
                                    stat = os.stat(file_path)
                                    mod_time = datetime.fromtimestamp(stat.st_mtime)
                                    if mod_time >= time_ago:
                                        result["deleted"].append({
                                            "name": file,
                                            "date": mod_time.strftime("%d.%m.%Y"),
                                            "time": mod_time.strftime("%H:%M:%S"),
                                            "size": round(stat.st_size / 1024, 1),
                                            "path": file_path
                                        })
                                except:
                                    pass
            except:
                pass

    def _get_clear_time(self):
        try:
            for drive in [f"{chr(c)}:\\\\" for c in range(65, 91) if os.path.exists(f"{chr(c)}:\\\\")]:
                recycle_bin = os.path.join(drive, "$Recycle.Bin")
                if os.path.isdir(recycle_bin):
                    try:
                        stat = os.stat(recycle_bin)
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        return {
                            "date": mtime.strftime("%d.%m.%Y"),
                            "time": mtime.strftime("%H:%M:%S")
                        }
                    except:
                        continue
        except:
            pass

        return None

    def clear_history_data(self):
        self.clear_history = []
        self.save_history()


# :)
class Aquarium:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("🐠 Секретный аквариум создателей")
        self.window.geometry("900x700")
        self.window.configure(bg="#001122")
        self.window.resizable(False, False)
        self.window.attributes('-topmost', True)

        header = tk.Frame(self.window, bg="#58a6ff", height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="🐠 Аквариум создателей: Kara7s (Xarays) & Nakish_",
                 font=("Segoe UI", 14, "bold"), bg="#58a6ff", fg="white").pack(pady=15)

        self.canvas = tk.Canvas(self.window, width=900, height=600, bg="#001122", highlightthickness=0)
        self.canvas.pack()

        self.creator_fishes = [
            {"name": "Kara7s", "x": 200, "y": 300, "color": "#FF6B6B", "size": 35, "speed_x": 2, "speed_y": 1},
            {"name": "Xarays", "x": 400, "y": 200, "color": "#4ECDC4", "size": 32, "speed_x": -2, "speed_y": 0},
            {"name": "Nakish_", "x": 600, "y": 400, "color": "#FFE66D", "size": 38, "speed_x": 1, "speed_y": -1},
            {"name": "Fancy_Legend", "x": 300, "y": 100, "color": "#FFE66D", "size": 40, "speed_x": 1, "speed_y": -2},
            {"name": "botinok", "x": 700, "y": 200, "color": "#FFE66D", "size": 42, "speed_x": 2, "speed_y": -1}
        ]

        self.fishes = []
        for _ in range(10):
            self.create_fish()

        self.bubbles = []
        self.animate()

        close_btn = tk.Button(self.window, text="Закрыть аквариум", command=self.window.destroy,
                              bg="#f85149", fg="white", font=("Arial", 10), pady=5)
        close_btn.pack(pady=10)

    def create_fish(self):
        colors = ["#FF6B6B", "#4ECDC4", "#FFE66D", "#6A0572", "#FF9A8B", "#95E1D3", "#FCE38A"]
        x = random.randint(50, 850)
        y = random.randint(50, 550)
        color = random.choice(colors)
        size = random.randint(20, 40)
        speed_x = random.choice([-3, -2, -1, 1, 2, 3])
        speed_y = random.choice([-1, 0, 1])

        fish = {
            "body": None, "tail": None, "eye": None, "label": None,
            "x": x, "y": y, "size": size, "speed_x": speed_x,
            "speed_y": speed_y, "color": color, "name": None
        }
        self.fishes.append(fish)

    def draw_fish(self, fish, is_creator=False):
        direction = 1 if fish["speed_x"] > 0 else -1
        size = fish["size"]

        body = self.canvas.create_oval(fish["x"] - size, fish["y"] - size // 2,
                                       fish["x"] + size, fish["y"] + size // 2,
                                       fill=fish["color"], outline="")

        tail_x = fish["x"] - direction * size
        tail_points = [
            tail_x, fish["y"],
            tail_x - direction * size, fish["y"] - size // 2,
            tail_x - direction * size, fish["y"] + size // 2
        ]
        tail = self.canvas.create_polygon(tail_points, fill=fish["color"], outline="")

        eye_x = fish["x"] + direction * size // 2
        eye = self.canvas.create_oval(eye_x - 2, fish["y"] - 2, eye_x + 2, fish["y"] + 2, fill="black")

        label = None
        if is_creator and fish["name"]:
            label = self.canvas.create_text(fish["x"], fish["y"] - size - 10,
                                            text=fish["name"], fill=fish["color"],
                                            font=("Arial", 10, "bold"))

        return body, tail, eye, label

    def animate(self):
        self.canvas.delete("all")

        self.canvas.create_rectangle(0, 550, 900, 600, fill="#2d1b00", outline="")

        for x in range(50, 900, 80):
            height = random.randint(80, 200)
            self.canvas.create_line(x, 550, x, 550 - height, fill="#00AA00", width=3)
            for y in range(550 - height, 550, 20):
                self.canvas.create_line(x, y, x + random.randint(10, 30), y - random.randint(5, 15),
                                        fill="#00CC00", width=2)

        if random.random() < 0.1:
            self.bubbles.append({
                "x": random.randint(50, 850),
                "y": 550,
                "size": random.randint(5, 15),
                "speed": random.uniform(1, 3)
            })

        new_bubbles = []
        for bubble in self.bubbles:
            bubble["y"] -= bubble["speed"]
            if bubble["y"] > 0:
                new_bubbles.append(bubble)
                self.canvas.create_oval(bubble["x"] - bubble["size"], bubble["y"] - bubble["size"],
                                        bubble["x"] + bubble["size"], bubble["y"] + bubble["size"],
                                        fill="#88FFFF", outline="")
        self.bubbles = new_bubbles

        for fish in self.fishes:
            fish["x"] += fish["speed_x"]
            fish["y"] += fish["speed_y"]

            if fish["x"] < 20 or fish["x"] > 880:
                fish["speed_x"] *= -1
            if fish["y"] < 20 or fish["y"] > 530:
                fish["speed_y"] *= -1

            if random.random() < 0.02:
                fish["speed_y"] = random.choice([-1, 0, 1])

            fish["body"], fish["tail"], fish["eye"], _ = self.draw_fish(fish)

        for fish in self.creator_fishes:
            fish["x"] += fish["speed_x"]
            fish["y"] += fish["speed_y"]

            if fish["x"] < 50 or fish["x"] > 850:
                fish["speed_x"] *= -1
            if fish["y"] < 50 or fish["y"] > 500:
                fish["speed_y"] *= -1

            if random.random() < 0.01:
                fish["speed_y"] = random.choice([-1, 0, 1])

            fish["body"], fish["tail"], fish["eye"], fish["label"] = self.draw_fish(fish, True)

        self.window.after(50, self.animate)


# инструментс
class ToolManager:
    @staticmethod
    def download_all_tools():
        try:
            tools_dir = Path("GammaDetector_Tools")
            tools_dir.mkdir(exist_ok=True)

            readme_content = """
Gamma Detector - Инструменты

В этом архиве собраны все рекомендуемые инструменты для анализа системы:

1. Everything - мгновенный поиск файлов
2. System Informer - мониторинг процессов  
3. WinPrefetchView - анализ Prefetch
4. Process Monitor - мониторинг системы
5. И многие другие...

Скачайте нужные инструменты с официальных сайтов, указанных в программе.

Будьте осторожны: скачивайте инструменты только с официальных источников!
            """

            with open(tools_dir / "README.txt", "w", encoding="utf-8") as f:
                f.write(readme_content)

            bat_content = """@echo off
echo Gamma Detector Tools Manager
echo.
echo Рекомендуемые инструменты:
echo 1. Everything - https://www.voidtools.com
echo 2. System Informer - https://systeminformer.sourceforge.io
echo 3. Process Monitor - https://docs.microsoft.com/en-us/sysinternals/downloads/procmon
echo.
echo Откройте программу Gamma Detector для получения всех ссылок.
pause
            """

            with open(tools_dir / "Tools_Links.bat", "w", encoding="utf-8") as f:
                f.write(bat_content)

            messagebox.showinfo("Успех",
                                f"Папка с инструментами создана: {tools_dir.absolute()}\n\n"
                                "В папке вы найдете:\n"
                                "• README.txt - описание инструментов\n"
                                "• Tools_Links.bat - быстрый доступ к ссылкам\n\n"
                                "Теперь вы можете скачать инструменты с официальных сайтов.")

            subprocess.Popen(f'explorer "{tools_dir.absolute()}"')

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать архив инструментов: {str(e)}")


class App:
    def __init__(self):
        self.detector = Detector()
        self.recycle_checker = RecycleChecker()
        self.root = tk.Tk()
        self.root.title("🛡️ GAMMA DETECTOR - ВЫСОКАЯ ПРОИЗВОДИТЕЛЬНОСТЬ")
        self.root.geometry("1500x950")
        self.root.configure(bg=COLORS["bg"])

        default_threads = min(32, (os.cpu_count() or 1) * 4)

        self.settings = {
            "threads": tk.IntVar(value=default_threads),
            "tolerance": tk.DoubleVar(value=1.0),
            "min_matches": tk.IntVar(value=2),
            "cpu_limit": tk.IntVar(value=80),
            "sounds": tk.BooleanVar(value=True),
            "auto_update_db": tk.BooleanVar(value=True),
            "fast_scan": tk.BooleanVar(value=True)
        }

        self.setup_styles()
        self.build()
        self.load_settings()

        self.verdict_shown = False
        self.root.mainloop()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TNotebook", background=COLORS["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=COLORS["card"], foreground=COLORS["text"],
                        padding=[20, 10], borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", COLORS["accent"])],
                  foreground=[("selected", "white")])

        style.configure("Custom.Horizontal.TProgressbar",
                        thickness=25, troughcolor=COLORS["card"],
                        background=COLORS["accent"], bordercolor=COLORS["card"])

        style.configure("Treeview",
                        background=COLORS["card"], foreground=COLORS["text"],
                        fieldbackground=COLORS["card"], borderwidth=0)
        style.configure("Treeview.Heading",
                        background=COLORS["input_bg"], foreground=COLORS["text"],
                        borderwidth=1, relief="flat")
        style.map("Treeview.Heading", background=[("active", COLORS["accent"])])
        style.map("Treeview", background=[("selected", COLORS["accent"])],
                  foreground=[("selected", "white")])

    def load_settings(self):
        try:
            if os.path.exists("detector_settings.json"):
                with open("detector_settings.json", "r") as f:
                    saved_settings = json.load(f)
                    for key, value in saved_settings.items():
                        if key in self.settings:
                            self.settings[key].set(value)
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")

    def show_aquarium(self, event=None):
        if hasattr(self, 'aquarium') and self.aquarium and self.aquarium.window.winfo_exists():
            self.aquarium.window.lift()
            return
        self.aquarium = Aquarium(self.root)

    def show_creators(self):
        creators_window = tk.Toplevel(self.root)
        creators_window.title("О создателях")
        creators_window.geometry("500x400")
        creators_window.configure(bg=COLORS["bg"])
        creators_window.resizable(False, False)

        header = tk.Frame(creators_window, bg=COLORS["accent"], height=80)
        header.pack(fill=tk.X)
        tk.Label(header, text="👨‍💻 СОЗДАТЕЛИ", font=("Segoe UI", 20, "bold"),
                 bg=COLORS["accent"], fg="white").pack(pady=20)

        content = tk.Frame(creators_window, bg=COLORS["card"])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        creators_info = [
            {"name": "Kara7s (Xarays)", "role": "Главный разработчик", "color": "#FF6B6B"},
            {"name": "Nakish_", "role": "Со-разработчик", "color": "#4ECDC4"}
        ]

        for i, creator in enumerate(creators_info):
            frame = tk.Frame(content, bg=COLORS["input_bg"], relief="flat")
            frame.pack(fill=tk.X, pady=10, padx=10)

            tk.Label(frame, text=creator["name"], font=("Segoe UI", 16, "bold"),
                     bg=COLORS["input_bg"], fg=creator["color"]).pack(anchor="w", padx=15, pady=(15, 5))

            tk.Label(frame, text=creator["role"], font=("Segoe UI", 12),
                     bg=COLORS["input_bg"], fg=COLORS["text_light"]).pack(anchor="w", padx=15, pady=(0, 15))

        tk.Button(content, text="🐠 Открыть аквариум", command=self.show_aquarium,
                  bg=COLORS["accent"], fg="white", font=("Segoe UI", 12, "bold"),
                  relief="flat", pady=10).pack(pady=20)

        tk.Button(creators_window, text="Закрыть", command=creators_window.destroy,
                  bg=COLORS["hover"], fg="white", font=("Segoe UI", 10),
                  relief="flat", padx=30, pady=10).pack(pady=10)

    def build(self):
        header = tk.Frame(self.root, bg=COLORS["accent"], height=75)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        self.header_label = tk.Label(header, text="🛡️ GAMMA DETECTOR",
                                     font=("Segoe UI", 24, "bold"), bg=COLORS["accent"],
                                     fg="white", cursor="hand2")
        self.header_label.pack(side=tk.LEFT, padx=25, pady=22)
        self.header_label.bind("<Double-Button-1>", self.show_aquarium)

        creators_btn = tk.Button(header, text="👨‍💻 Создатели", command=self.show_creators,
                                 bg=COLORS["hover"], fg="white", font=("Segoe UI", 10, "bold"),
                                 relief="flat", padx=15)
        creators_btn.pack(side=tk.RIGHT, padx=10, pady=22)

        db_info = self.detector.db.get_database_info()
        db_label = tk.Label(header,
                            text=f"База: {db_info['total']} читов | Обновлено: {db_info['last_update'] or 'Никогда'}",
                            font=("Segoe UI", 11), bg=COLORS["accent"], fg="white")
        db_label.pack(side=tk.RIGHT, padx=25, pady=22)

        tabs = ttk.Notebook(self.root)
        tabs.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        scan_tab = tk.Frame(tabs, bg=COLORS["bg"])
        tabs.add(scan_tab, text="🔍 Сканер")
        self.build_scanner(scan_tab)

        settings_tab = tk.Frame(tabs, bg=COLORS["bg"])
        tabs.add(settings_tab, text="⚙️ Настройки")
        self.build_settings(settings_tab)

        tools_tab = tk.Frame(tabs, bg=COLORS["bg"])
        tabs.add(tools_tab, text="🔧 Инструменты")
        self.build_tools(tools_tab)

        db_tab = tk.Frame(tabs, bg=COLORS["bg"])
        tabs.add(db_tab, text="🗃️ База данных")
        self.build_database_tab(db_tab)

    def build_scanner(self, parent):
        ctrl = tk.Frame(parent, bg=COLORS["card"], relief="flat")
        ctrl.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(ctrl, text="📁 Путь:", bg=COLORS["card"], fg=COLORS["text"],
                 font=("Segoe UI", 11, "bold")).grid(row=0, column=0, padx=15, pady=15, sticky="w")

        self.path_var = tk.StringVar(value=str(Path.home() / ".minecraft" / "mods"))
        tk.Entry(ctrl, textvariable=self.path_var, width=65, font=("Consolas", 10),
                 bg=COLORS["input_bg"], fg=COLORS["text"], insertbackground=COLORS["text"],
                 relief="flat").grid(row=0, column=1, padx=10, pady=15)

        tk.Button(ctrl, text="📂", command=self.browse_path,
                  bg=COLORS["hover"], fg=COLORS["text"], font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=15, pady=10, cursor="hand2").grid(row=0, column=2, padx=5, pady=15)

        self.scan_btn = tk.Button(ctrl, text="🎯 Сканировать", command=self.start_scan,
                                  bg=COLORS["success"], fg="white", font=("Segoe UI", 11, "bold"),
                                  relief="flat", padx=25, pady=12, cursor="hand2")
        self.scan_btn.grid(row=0, column=3, padx=15, pady=15)

        self.stop_btn = tk.Button(ctrl, text="⏹ Стоп", command=self.stop_scan,
                                  bg=COLORS["danger"], fg="white", font=("Segoe UI", 10, "bold"),
                                  relief="flat", state=tk.DISABLED, padx=18, pady=12)
        self.stop_btn.grid(row=0, column=4, padx=5, pady=15)

        stats = tk.Frame(parent, bg=COLORS["bg"])
        stats.pack(fill=tk.X, padx=10, pady=10)

        self.stats_labels = {}
        for i, (key, label, color) in enumerate([
            ("total", "Всего", COLORS["accent"]),
            ("checked", "Проверено", "#4fc3f7"),
            ("found", "Найдено", COLORS["danger"]),
            ("clean", "Чисто", COLORS["success"])
        ]):
            card = tk.Frame(stats, bg=COLORS["card"], relief="flat")
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")

            tk.Frame(card, bg=color, height=4).pack(fill=tk.X)

            val = tk.Label(card, text="0", font=("Segoe UI", 30, "bold"),
                           fg=color, bg=COLORS["card"])
            val.pack(pady=(18, 5))

            tk.Label(card, text=label, font=("Segoe UI", 10),
                     fg=COLORS["text_light"], bg=COLORS["card"]).pack(pady=(0, 18))

            self.stats_labels[key] = val
            stats.columnconfigure(i, weight=1)

        mon = tk.Frame(stats, bg=COLORS["card"], relief="flat")
        mon.grid(row=0, column=4, padx=10, pady=10, sticky="nsew")

        tk.Label(mon, text="⚙️ Система", font=("Segoe UI", 10, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(pady=(10, 5))

        self.cpu_label = tk.Label(mon, text="CPU: 0%", font=("Consolas", 10),
                                  bg=COLORS["card"], fg=COLORS["warning"])
        self.cpu_label.pack(pady=2)

        self.mem_label = tk.Label(mon, text="RAM: 0%", font=("Consolas", 10),
                                  bg=COLORS["card"], fg=COLORS["warning"])
        self.mem_label.pack(pady=(2, 10))

        prog_cont = tk.Frame(parent, bg=COLORS["card"], relief="flat")
        prog_cont.pack(fill=tk.X, padx=10, pady=5)

        self.progress_bar = ttk.Progressbar(prog_cont, mode="determinate",
                                            style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, padx=2, pady=2)

        content = tk.Frame(parent, bg=COLORS["bg"])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left = tk.Frame(content, bg=COLORS["card"], relief="flat")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        hdr = tk.Frame(left, bg=COLORS["danger"], height=45)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        tk.Label(hdr, text="🚨 ОБНАРУЖЕННЫЕ УГРОЗЫ", font=("Segoe UI", 13, "bold"),
                 bg=COLORS["danger"], fg="white").pack(pady=12)

        res_cont = tk.Frame(left, bg=COLORS["card"])
        res_cont.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.results_tree = ttk.Treeview(res_cont,
                                         columns=("file", "size", "cheat", "score", "conditions"),
                                         show="headings", height=15)

        for col, text, width in [
            ("file", "Файл", 280),
            ("size", "Размер (KB)", 100),
            ("cheat", "Тип чита", 180),
            ("score", "Совпадений", 90),
            ("conditions", "Условия", 200)
        ]:
            self.results_tree.heading(col, text=text)
            self.results_tree.column(col, width=width)

        scroll_y = ttk.Scrollbar(res_cont, orient="vertical", command=self.results_tree.yview)
        scroll_x = ttk.Scrollbar(res_cont, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.results_tree.bind("<Double-1>", self.open_file_location)
        self.results_tree.bind("<Button-3>", self.show_threat_details)

        right = tk.Frame(content, bg=COLORS["card"], width=420, relief="flat")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right.pack_propagate(False)

        t_hdr = tk.Frame(right, bg=COLORS["warning"], height=45)
        t_hdr.pack(fill=tk.X)
        t_hdr.pack_propagate(False)

        tk.Label(t_hdr, text="🔧 ИНСТРУМЕНТЫ", font=("Segoe UI", 12, "bold"),
                 bg=COLORS["warning"], fg="white").pack(pady=12)

        tools = tk.Frame(right, bg=COLORS["card"])
        tools.pack(fill=tk.X, padx=15, pady=15)

        tk.Button(tools, text="🗑 Проверить корзину", command=self.check_recycle_bin,
                  bg=COLORS["hover"], fg=COLORS["text"], font=("Segoe UI", 11, "bold"),
                  relief="flat", cursor="hand2", pady=12).pack(fill=tk.X, pady=5)

        verdict_frame = tk.Frame(right, bg=COLORS["card_dark"], relief="flat", borderwidth=2)
        verdict_frame.pack(fill=tk.X, padx=15, pady=10)

        self.verdict_label = tk.Label(verdict_frame, text="🔍 ОЖИДАНИЕ СКАНИРОВАНИЯ",
                                      font=("Segoe UI", 14, "bold"), bg=COLORS["card_dark"],
                                      fg=COLORS["text_light"], pady=20)
        self.verdict_label.pack(fill=tk.X)

        search = tk.Frame(right, bg=COLORS["card"])
        search.pack(fill=tk.X, padx=15, pady=10)

        s_hdr = tk.Frame(search, bg=COLORS["accent"], height=40)
        s_hdr.pack(fill=tk.X, pady=(0, 15))
        s_hdr.pack_propagate(False)

        tk.Label(s_hdr, text="🔍 Ручной поиск", font=("Segoe UI", 12, "bold"),
                 bg=COLORS["accent"], fg="white").pack(pady=10)

        w_cont = tk.Frame(search, bg=COLORS["card"])
        w_cont.pack(fill=tk.X, pady=8)

        tk.Label(w_cont, text="Вес (KB ±1KB):", bg=COLORS["card"],
                 fg=COLORS["text"], font=("Segoe UI", 10), width=14, anchor="w").pack(side=tk.LEFT, padx=(0, 10))
        self.search_weight = tk.Entry(w_cont, width=20, font=("Consolas", 10),
                                      bg=COLORS["input_bg"], fg=COLORS["text"],
                                      insertbackground=COLORS["text"], relief="flat")
        self.search_weight.pack(side=tk.LEFT, fill=tk.X, expand=True)

        n_cont = tk.Frame(search, bg=COLORS["card"])
        n_cont.pack(fill=tk.X, pady=8)

        tk.Label(n_cont, text="Название:", bg=COLORS["card"],
                 fg=COLORS["text"], font=("Segoe UI", 10), width=14, anchor="w").pack(side=tk.LEFT, padx=(0, 10))
        self.search_name = tk.Entry(n_cont, width=20, font=("Consolas", 10),
                                    bg=COLORS["input_bg"], fg=COLORS["text"],
                                    insertbackground=COLORS["text"], relief="flat")
        self.search_name.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(search, text="🔎 Искать", command=self.search_database,
                  bg=COLORS["accent"], fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", cursor="hand2", pady=10).pack(fill=tk.X, pady=(15, 0))

        log = tk.Frame(right, bg=COLORS["card"])
        log.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        l_hdr = tk.Frame(log, bg=COLORS["input_bg"], height=35)
        l_hdr.pack(fill=tk.X, pady=(0, 5))
        l_hdr.pack_propagate(False)

        tk.Label(l_hdr, text="📋 Журнал (увеличенный)", font=("Segoe UI", 11, "bold"),
                 bg=COLORS["input_bg"], fg=COLORS["text"]).pack(pady=8, padx=10, anchor="w")

        self.log_text = scrolledtext.ScrolledText(log, height=12,
                                                  bg=COLORS["card"], fg=COLORS["text"],
                                                  font=("Consolas", 9), wrap=tk.WORD,
                                                  insertbackground=COLORS["text"],
                                                  relief="flat", borderwidth=0)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def build_settings(self, parent):
        hdr = tk.Frame(parent, bg=COLORS["accent"], height=60)
        hdr.pack(fill=tk.X, pady=(0, 20))
        hdr.pack_propagate(False)

        tk.Label(hdr, text="⚙️ НАСТРОЙКИ ВЫСОКОЙ ПРОИЗВОДИТЕЛЬНОСТИ", font=("Segoe UI", 16, "bold"),
                 bg=COLORS["accent"], fg="white").pack(pady=18, padx=20, anchor="w")

        settings_data = [
            ("🔢 Потоки сканирования",
             f"Количество параллельных потоков (рекомендуется: {min(32, (os.cpu_count() or 1) * 4)})", "threads",
             (1, 32, 1)),
            ("📊 Погрешность веса", "Допустимая погрешность размера файла (KB)", "tolerance", (0.1, 10.0, 0.1)),
            ("🎯 Мин. совпадений", "Минимальное количество совпадений для детекции", "min_matches", (1, 3, 1)),
            ("⚡ Контроль CPU", "Максимальная нагрузка на процессор (%)", "cpu_limit", (50, 100, 5)),
            ("🔊 Звуки", "Воспроизводить звуковые уведомления", "sounds", None),
            ("🚀 Быстрое сканирование", "Использовать оптимизированные алгоритмы (рекомендуется)", "fast_scan", None)
        ]

        for title, desc, key, range_vals in settings_data:
            card = tk.Frame(parent, bg=COLORS["card"], relief="flat")
            card.pack(fill=tk.X, padx=25, pady=10)

            left_part = tk.Frame(card, bg=COLORS["card"])
            left_part.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=20)

            tk.Label(left_part, text=title, font=("Segoe UI", 13, "bold"),
                     bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")

            tk.Label(left_part, text=desc, font=("Segoe UI", 9),
                     bg=COLORS["card"], fg=COLORS["text_light"]).pack(anchor="w", pady=(5, 0))

            if range_vals:
                spin = tk.Spinbox(card, from_=range_vals[0], to=range_vals[1],
                                  increment=range_vals[2], textvariable=self.settings[key],
                                  width=10, font=("Consolas", 11), bg=COLORS["input_bg"],
                                  fg=COLORS["text"], relief="flat")
                spin.pack(side=tk.RIGHT, padx=20, pady=20)
            else:
                cb = tk.Checkbutton(card, variable=self.settings[key],
                                    bg=COLORS["card"], fg=COLORS["text"],
                                    selectcolor=COLORS["input_bg"])
                cb.pack(side=tk.RIGHT, padx=20, pady=20)

        perf_card = tk.Frame(parent, bg=COLORS["success"], relief="flat")
        perf_card.pack(fill=tk.X, padx=25, pady=15)

        perf_text = """
        🚀 ОПТИМИЗАЦИИ ПРОИЗВОДИТЕЛЬНОСТИ:

        • Многоуровневое индексирование базы данных
        • Быстрый поиск по размерам и путям  
        • Оптимизированное чтение JAR файлов
        • Интеллектуальная фильтрация на основе индексов
        • Автоматическая настройка потоков по ядрам CPU
        • Кэширование результатов для повторных проверок
        • Приоритетная обработка подозрительных файлов
        • УЛУЧШЕННОЕ обнаружение: директории + классы + вес
        • Минимум 2 совпадения для детекции
        • Исправлены баги с поиском NekoClient и других читов
                """

        tk.Label(perf_card, text=perf_text, font=("Consolas", 9),
                 bg=COLORS["success"], fg="white", justify=tk.LEFT).pack(padx=15, pady=15)

        apply_btn = tk.Button(parent, text="💾 Применить настройки", command=self.apply_settings,
                              bg=COLORS["success"], fg="white", font=("Segoe UI", 12, "bold"),
                              relief="flat", padx=30, pady=15, cursor="hand2")
        apply_btn.pack(pady=20)

    def build_tools(self, parent):
        canvas = tk.Canvas(parent, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["bg"])

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        hdr = tk.Frame(scrollable_frame, bg=COLORS["accent"], height=60)
        hdr.pack(fill=tk.X, pady=(0, 20))
        hdr.pack_propagate(False)

        tk.Label(hdr, text="🛠️ ВНЕШНИЕ ИНСТРУМЕНТЫ", font=("Segoe UI", 16, "bold"),
                 bg=COLORS["accent"], fg="white").pack(pady=18, padx=20, anchor="w")

        download_frame = tk.Frame(scrollable_frame, bg=COLORS["card"], relief="flat")
        download_frame.pack(fill=tk.X, padx=25, pady=15)

        tk.Button(download_frame, text="📦 СКАЧАТЬ ВСЕ ИНСТРУМЕНТЫ",
                  command=ToolManager.download_all_tools,
                  bg=COLORS["success"], fg="white", font=("Segoe UI", 12, "bold"),
                  relief="flat", pady=15, cursor="hand2").pack(fill=tk.X, pady=10)

        tk.Label(download_frame, text="Создает архив со всеми инструментами и инструкциями",
                 font=("Segoe UI", 9), bg=COLORS["card"], fg=COLORS["text_light"]).pack(pady=(0, 10))

        tools_data = [
            ("Everything", "https://www.voidtools.com", "Мгновенный поиск файлов", "🔍"),
            ("System Informer", "https://systeminformer.sourceforge.io", "Мониторинг процессов", "📊"),
            ("WinPrefetchView", "https://www.nirsoft.net/utils/win_prefetch_view.html", "Анализ Prefetch", "📂"),
            ("Process Monitor", "https://docs.microsoft.com/en-us/sysinternals/downloads/procmon", "Мониторинг системы",
             "👁️"),
            ("HashCalc", "https://www.slavasoft.com/hashcalc/", "Вычисление хешей", "🔢"),
            ("Wireshark", "https://www.wireshark.org/", "Анализ сетевого трафика", "🌐"),
            ("Process Explorer", "https://docs.microsoft.com/en-us/sysinternals/downloads/process-explorer",
             "Продвинутый мониторинг процессов", "🔬"),
            ("Autoruns", "https://docs.microsoft.com/en-us/sysinternals/downloads/autoruns", "Автозагрузка и сервисы",
             "🚀"),
            ("TCPView", "https://docs.microsoft.com/en-us/sysinternals/downloads/tcpview", "Сетевые соединения", "🔌")
        ]

        for name, url, desc, icon in tools_data:
            card = tk.Frame(scrollable_frame, bg=COLORS["card"], relief="flat")
            card.pack(fill=tk.X, padx=25, pady=10)

            left = tk.Frame(card, bg=COLORS["card"])
            left.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=20)

            tk.Label(left, text=icon, font=("Segoe UI", 24), bg=COLORS["card"], fg=COLORS["accent"]).pack(side=tk.LEFT,
                                                                                                          padx=(0, 15))
            tk.Label(left, text=name, font=("Segoe UI", 13, "bold"), bg=COLORS["card"], fg=COLORS["text"]).pack(
                side=tk.LEFT)

            tk.Label(card, text=desc, bg=COLORS["card"], fg=COLORS["text_light"],
                     font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=20, pady=20, fill=tk.X, expand=True)

            tk.Button(card, text="Скачать ⤴", command=lambda u=url: webbrowser.open(u),
                      bg=COLORS["accent"], fg="white", font=("Segoe UI", 10, "bold"),
                      relief="flat", cursor="hand2", padx=20, pady=10).pack(side=tk.RIGHT, padx=20, pady=15)

        tools_hdr = tk.Frame(scrollable_frame, bg=COLORS["warning"], height=45)
        tools_hdr.pack(fill=tk.X, padx=25, pady=(30, 10))
        tools_hdr.pack_propagate(False)

        tk.Label(tools_hdr, text="🛠️ ДОПОЛНИТЕЛЬНЫЕ ИНСТРУМЕНТЫ", font=("Segoe UI", 14, "bold"),
                 bg=COLORS["warning"], fg="white").pack(pady=10)

        actions_frame = tk.Frame(scrollable_frame, bg=COLORS["bg"])
        actions_frame.pack(fill=tk.X, padx=25, pady=10)

        quick_actions = [
            ("🧹 Очистить кэш сканера", self.clear_cache),
            ("📊 Статистика базы", self.show_db_stats),
            ("🔄 Обновить базу", self.update_database),
            ("📝 Экспорт результатов", self.export_results),
            ("🔍 Быстрое сканирование", self.quick_scan),
            ("📄 Текст детектор", self.text_detector)
        ]

        for i, (text, command) in enumerate(quick_actions):
            btn = tk.Button(actions_frame, text=text, command=command,
                            bg=COLORS["hover"], fg=COLORS["text"], font=("Segoe UI", 10),
                            relief="flat", cursor="hand2", pady=8)
            btn.grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky="ew")
            actions_frame.columnconfigure(i % 3, weight=1)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def build_database_tab(self, parent):
        hdr = tk.Frame(parent, bg=COLORS["accent"], height=60)
        hdr.pack(fill=tk.X, pady=(0, 20))
        hdr.pack_propagate(False)

        tk.Label(hdr, text="🗃️ УПРАВЛЕНИЕ БАЗОЙ ДАННЫХ", font=("Segoe UI", 16, "bold"),
                 bg=COLORS["accent"], fg="white").pack(pady=18, padx=20, anchor="w")

        content = tk.Frame(parent, bg=COLORS["card"])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        info_frame = tk.Frame(content, bg=COLORS["input_bg"], relief="flat")
        info_frame.pack(fill=tk.X, pady=(0, 15))

        db_info = self.detector.db.get_database_info()

        info_text = f"""
📊 Статистика базы данных:

• Всего записей: {db_info['total']}
• Записей с размерами: {db_info['with_sizes']}
• Записей с директориями: {db_info['with_dirs']}
• Записей с классами: {db_info['with_classes']}
• В строгом режиме: {db_info['strict_mode']}
• Последнее обновление: {db_info['last_update'] or 'Никогда'}
"""
        tk.Label(info_frame, text=info_text, font=("Consolas", 10),
                 bg=COLORS["input_bg"], fg=COLORS["text"], justify=tk.LEFT).pack(padx=15, pady=15)

        buttons_frame = tk.Frame(content, bg=COLORS["card"])
        buttons_frame.pack(fill=tk.X, pady=10)

        action_buttons = [
            ("🔄 Обновить из Google Sheets", self.update_database),
            ("📊 Проверить целостность", self.validate_database),
            ("💾 Создать бэкап", self.create_backup),
            ("📥 Восстановить из бэкапа", self.restore_backup),
            ("👁️ Просмотреть все записи", self.show_database_manager)
        ]

        for text, command in action_buttons:
            btn = tk.Button(buttons_frame, text=text, command=command,
                            bg=COLORS["hover"], fg=COLORS["text"], font=("Segoe UI", 10),
                            relief="flat", cursor="hand2", pady=8)
            btn.pack(fill=tk.X, pady=5)

        list_frame = tk.Frame(content, bg=COLORS["card"])
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

        tk.Label(list_frame, text="📋 Последние добавленные записи:", font=("Segoe UI", 11, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        list_container = tk.Frame(list_frame, bg=COLORS["card"])
        list_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.cheat_list = tk.Listbox(list_container, yscrollcommand=scrollbar.set,
                                     bg=COLORS["input_bg"], fg=COLORS["text"],
                                     font=("Consolas", 9), selectbackground=COLORS["accent"])
        self.cheat_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.cheat_list.yview)

        self.update_cheat_list()

        self.cheat_list.bind("<Double-Button-1>", lambda e: self.show_cheat_details())

        tk.Button(content, text="🔄 Обновить список", command=self.update_cheat_list,
                  bg=COLORS["accent"], fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=20, pady=8, cursor="hand2").pack(pady=10)

    def update_cheat_list(self):
        self.cheat_list.delete(0, tk.END)

        for name, data in self.detector.db.cheat_database.items():
            has_size = "📏" if data.get("sizes_kb") else "　"
            has_dir = "📁" if data.get("directories") else "　"
            has_class = "📄" if data.get("classes") else "　"
            strict = "🔒" if data.get("strict_mode") else "　"

            self.cheat_list.insert(tk.END, f"{has_size}{has_dir}{has_class}{strict} {name}")

    def show_cheat_details(self):
        selection = self.cheat_list.curselection()
        if not selection:
            return

        cheat_name = self.cheat_list.get(selection[0]).split(" ", 1)[1]
        cheat_data = self.detector.db.cheat_database.get(cheat_name)

        if not cheat_data:
            return

        details_window = tk.Toplevel(self.root)
        details_window.title(f"Детали: {cheat_name}")
        details_window.geometry("600x500")
        details_window.configure(bg=COLORS["bg"])
        details_window.resizable(False, False)

        header = tk.Frame(details_window, bg=COLORS["accent"], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text=f"📋 {cheat_name}", font=("Segoe UI", 14, "bold"),
                 bg=COLORS["accent"], fg="white").pack(pady=15)

        content = tk.Frame(details_window, bg=COLORS["card"])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        details_text = f"""
Описание: {cheat_data.get('description', 'Нет описания')}

📏 Размеры: {', '.join(map(str, cheat_data.get('sizes_kb', []))) or 'Не указаны'}

📁 Директории:
{chr(10).join(f'  • {dir}' for dir in cheat_data.get('directories', [])) or '  Не указаны'}

📄 Классы:
{chr(10).join(f'  • {cls}' for cls in cheat_data.get('classes', [])) or '  Не указаны'}

⚙️ Настройки:
  • Строгий режим: {'Да' if cheat_data.get('strict_mode') else 'Нет'}
  • Мин. условий: {cheat_data.get('min_conditions', 2)}
  • Исключения: {len(cheat_data.get('exclude_dirs', []))}
"""
        details_label = tk.Label(content, text=details_text, font=("Consolas", 9),
                                 bg=COLORS["card"], fg=COLORS["text"], justify=tk.LEFT)
        details_label.pack(fill=tk.BOTH, expand=True)

        tk.Button(content, text="Закрыть", command=details_window.destroy,
                  bg=COLORS["hover"], fg="white", font=("Segoe UI", 10),
                  relief="flat", padx=20, pady=8).pack(pady=10)

    def apply_settings(self):
        try:
            self.detector.max_threads = self.settings["threads"].get()
            self.detector.tolerance_kb = self.settings["tolerance"].get()

            settings_data = {
                "threads": self.settings["threads"].get(),
                "tolerance": self.settings["tolerance"].get(),
                "min_matches": self.settings["min_matches"].get(),
                "cpu_limit": self.settings["cpu_limit"].get(),
                "sounds": self.settings["sounds"].get(),
                "fast_scan": self.settings["fast_scan"].get()
            }

            with open("detector_settings.json", "w") as f:
                json.dump(settings_data, f)

            self.log_message("⚙️ Настройки высокой производительности применены!")
            messagebox.showinfo("Успех", "Настройки производительности применены!\n\n" +
                                f"Потоки: {self.detector.max_threads}\n" +
                                f"Быстрое сканирование: {'ВКЛ' if self.settings['fast_scan'].get() else 'ВЫКЛ'}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось применить настройки: {str(e)}")

    def show_verdict(self, has_threats, threat_count=0):
        if has_threats:
            self.verdict_label.config(
                text=f"🚨 ВЕРДИКТ: СКОРЕЕ ВСЕГО ЧИТЕР!",
                bg=COLORS["danger"],
                fg="white",
                font=("Segoe UI", 16, "bold")
            )
            if self.settings["sounds"].get():
                SoundManager.play_threat_found()
        else:
            self.verdict_label.config(
                text="✅ ВЕРДИКТ: ТРЕБУЕТСЯ РУЧНАЯ ПРОВЕРКА.",
                bg=COLORS["success"],
                fg="white",
                font=("Segoe UI", 12, "bold")
            )
            if self.settings["sounds"].get():
                SoundManager.play_clean_system()

    def check_recycle_bin(self):
        self.log_message("🗑 Проверка корзины...")
        if self.settings["sounds"].get():
            SoundManager.play_recycle_info()

        result = self.recycle_checker.check()

        bin_window = tk.Toplevel(self.root)
        bin_window.title("Детальный анализ корзины")
        bin_window.geometry("800x600")
        bin_window.configure(bg=COLORS["bg"])

        header = tk.Frame(bin_window, bg=COLORS["warning"], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🗑 Детальный анализ корзины", font=("Segoe UI", 16, "bold"),
                 bg=COLORS["warning"], fg="white").pack(pady=18)

        content = tk.Frame(bin_window, bg=COLORS["card"])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        clear_frame = tk.Frame(content, bg=COLORS["input_bg"], relief="flat")
        clear_frame.pack(fill=tk.X, pady=(0, 15))

        if result["cleared"] and result["clear_date"]:
            tk.Label(clear_frame, text="✅ Корзина очищалась:", font=("Segoe UI", 11, "bold"),
                     bg=COLORS["input_bg"], fg=COLORS["success"]).pack(anchor="w", padx=15, pady=(15, 5))

            time_frame = tk.Frame(clear_frame, bg=COLORS["input_bg"])
            time_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

            tk.Label(time_frame, text=f"📅 Дата: {result['clear_date']}", font=("Consolas", 11),
                     bg=COLORS["input_bg"], fg=COLORS["text"]).pack(side=tk.LEFT)

            tk.Label(time_frame, text=f"🕒 Время: {result['clear_time']}", font=("Consolas", 11),
                     bg=COLORS["input_bg"], fg=COLORS["text"]).pack(side=tk.RIGHT)
        else:
            tk.Label(clear_frame, text="❓ Время последней очистки не определено",
                     font=("Segoe UI", 11), bg=COLORS["input_bg"], fg=COLORS["text_light"]).pack(anchor="w", padx=15,
                                                                                                 pady=15)

        if result["clear_history"]:
            history_frame = tk.Frame(content, bg=COLORS["input_bg"])
            history_frame.pack(fill=tk.X, pady=(0, 15))

            tk.Label(history_frame, text="📋 История очисток:", font=("Segoe UI", 11, "bold"),
                     bg=COLORS["input_bg"], fg=COLORS["accent"]).pack(anchor="w", padx=15, pady=(15, 5))

            history_text = scrolledtext.ScrolledText(history_frame, height=6,
                                                     bg=COLORS["card"], fg=COLORS["text"],
                                                     font=("Consolas", 9), wrap=tk.WORD)
            history_text.pack(fill=tk.X, padx=15, pady=(0, 15))

            for i, clear in enumerate(result["clear_history"][:10]):
                history_text.insert(tk.END,
                                    f"{i + 1}. 📅 {clear['date']} 🕒 {clear['time']} (обнаружено: {clear['detected_at']})\n")
            history_text.config(state=tk.DISABLED)

        if result["deleted"]:
            tk.Label(content, text=f"📁 Обнаружено удаленных файлов: {len(result['deleted'])}",
                     font=("Segoe UI", 12, "bold"), bg=COLORS["card"], fg=COLORS["danger"]).pack(anchor="w",
                                                                                                 pady=(10, 10))

            files_text = scrolledtext.ScrolledText(content, height=12,
                                                   bg=COLORS["input_bg"], fg=COLORS["text"],
                                                   font=("Consolas", 9), wrap=tk.WORD)
            files_text.pack(fill=tk.BOTH, expand=True)

            for item in result["deleted"][:20]:
                files_text.insert(tk.END, f"📄 {item['name']}\n")
                files_text.insert(tk.END, f"   Размер: {item['size']} KB | ")
                files_text.insert(tk.END, f"Дата: {item['date']} | ")
                files_text.insert(tk.END, f"Время: {item['time']}\n")
                files_text.insert(tk.END, f"   Путь: {item['path']}\n\n")

            files_text.config(state=tk.DISABLED)
        else:
            tk.Label(content, text="✅ Подозрительных файлов в корзине не обнаружено",
                     font=("Segoe UI", 11), bg=COLORS["card"], fg=COLORS["success"]).pack(anchor="w", pady=20)

        button_frame = tk.Frame(bin_window, bg=COLORS["bg"])
        button_frame.pack(pady=15)

        if result["clear_history"]:
            tk.Button(button_frame, text="🧹 Очистить историю",
                      command=lambda: [self.recycle_checker.clear_history_data(), bin_window.destroy(),
                                       self.check_recycle_bin()],
                      bg=COLORS["danger"], fg="white", font=("Segoe UI", 10),
                      relief="flat", padx=15, pady=8).pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="🔄 Обновить",
                  command=lambda: [bin_window.destroy(), self.check_recycle_bin()],
                  bg=COLORS["accent"], fg="white", font=("Segoe UI", 10),
                  relief="flat", padx=15, pady=8).pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="Закрыть", command=bin_window.destroy,
                  bg=COLORS["hover"], fg="white", font=("Segoe UI", 10),
                  relief="flat", padx=15, pady=8).pack(side=tk.LEFT, padx=5)

        self.log_message("✅ Проверка корзины завершена")

    def start_scan(self):
        path = self.path_var.get()
        if not os.path.exists(path):
            messagebox.showerror("Ошибка", "Указанный путь не существует!")
            return

        self.verdict_label.config(
            text="🚀 СКАНИРОВАНИЕ...",
            bg=COLORS["warning"],
            fg="white",
            font=("Segoe UI", 14, "bold")
        )
        self.verdict_shown = False

        if self.settings["sounds"].get():
            SoundManager.play_scan_start()

        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        self.log_text.delete(1.0, tk.END)

        for key in self.stats_labels:
            self.stats_labels[key].config(text="0")

        self.progress_bar["value"] = 0

        self.scan_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        self.log_message(f"🚀 Запуск высокоскоростного сканирования: {path}")
        self.log_message(
            f"⚡ Потоки: {self.detector.max_threads}, Алгоритм: {'ОПТИМИЗИРОВАННЫЙ' if self.settings['fast_scan'].get() else 'СТАНДАРТНЫЙ'}")

        scan_thread = threading.Thread(target=self._scan_thread, args=(path,), daemon=True)
        scan_thread.start()

    def _scan_thread(self, base_path):
        start_time = time.time()

        jars = self.detector.find_jars(base_path)
        self.log_message(f"📦 Найдено JAR файлов: {len(jars)} за {time.time() - start_time:.2f}с")

        if not jars:
            self.log_message("ℹ️ JAR файлы не найдены")
            self.scan_finished()
            return

        if self.settings["fast_scan"].get():
            results = self.detector.scan(jars, self.update_progress, self.log_message)
        else:
            results = self.detector.scan(jars, self.update_progress, self.log_message)

        total_time = time.time() - start_time
        self.log_message(f"⏱️ Сканирование завершено за {total_time:.2f} секунд")
        self.log_message(f"📊 Производительность: {len(jars) / total_time:.1f} файлов/секунду")

        for result in results:
            self.add_scan_result(result)

        self.show_verdict(bool(results), len(results))

        if results:
            self.log_message(f"🚨 Обнаружено угроз: {len(results)}")
            self.log_message("╔════════════════════════════════════╗")
            self.log_message("║         🔴 ВЕРДИКТ: ЧИТЕР!         ║")
            self.log_message("║    Обнаружены читы и моды!         ║")
            self.log_message("╚════════════════════════════════════╝")
        else:
            self.log_message("✅ Угроз не обнаружено - система чиста!")
            self.log_message("╔════════════════════════════════════╗")
            self.log_message("║         🟢 ВЕРДИКТ: ЧИСТ!          ║")
            self.log_message("║     Читы не обнаружены!            ║")
            self.log_message("╚════════════════════════════════════╝")

        self.scan_finished()

    def scan_finished(self):
        self.scan_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        if self.settings["sounds"].get():
            SoundManager.play_scan_complete()

    def browse_path(self):
        path = filedialog.askdirectory(initialdir=self.path_var.get())
        if path:
            self.path_var.set(path)

    def log_message(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def update_progress(self, stats):
        for key, value in stats.items():
            if key in self.stats_labels:
                self.stats_labels[key].config(text=str(value))

        if stats["total"] > 0:
            self.progress_bar["value"] = (stats["checked"] / stats["total"]) * 100

        self.cpu_label.config(text=f"CPU: {psutil.cpu_percent():.1f}%")
        self.mem_label.config(text=f"RAM: {psutil.virtual_memory().percent:.1f}%")
        self.root.update_idletasks()

    def add_scan_result(self, result):
        self.results_tree.insert("", 0, values=(
            result["name"],
            result["file_size_kb"],
            result["cheat_type"],
            f"{result['match_score']}/3",
            " | ".join(result["conditions_met"])
        ))

    def stop_scan(self):
        self.detector.scanning = False
        self.log_message("⏹ Сканирование остановлено пользователем")

    def open_file_location(self, event):
        selection = self.results_tree.selection()
        if not selection:
            return

        file_name = self.results_tree.item(selection[0])["values"][0]

        for result in self.detector.results:
            if result["name"] == file_name:
                folder_path = os.path.dirname(result["path"])
                self.root.clipboard_clear()
                self.root.clipboard_append(folder_path)
                self.root.update()

                try:
                    subprocess.Popen(f'explorer /select,"{result["path"]}"')
                except:
                    pass

                self.log_message(f"📋 Скопирован путь: {folder_path}")
                break

    def show_threat_details(self, event):
        selection = self.results_tree.selection()
        if not selection:
            return

        file_name = self.results_tree.item(selection[0])["values"][0]

        for result in self.detector.results:
            if result["name"] == file_name:
                self.show_detailed_threat_info(result)
                break

    def show_detailed_threat_info(self, result):
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Детали угрозы: {result['name']}")
        details_window.geometry("700x600")
        details_window.configure(bg=COLORS["bg"])

        header = tk.Frame(details_window, bg=COLORS["danger"], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text=f"🚨 {result['cheat_type']}", font=("Segoe UI", 16, "bold"),
                 bg=COLORS["danger"], fg="white").pack(pady=18)

        content = tk.Frame(details_window, bg=COLORS["card"])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        info_labels = [
            ("Файл:", result["name"]),
            ("Полный путь:", result["path"]),
            ("Размер:", f"{result['file_size_kb']} KB"),
            ("Совпадений:", f"{result['match_score']}/3 условий"),
            ("Уровень угрозы:", "ВЫСОКИЙ" if result.get('strict_mode', False) else "СРЕДНИЙ")
        ]

        for label, value in info_labels:
            row = tk.Frame(content, bg=COLORS["input_bg"])
            row.pack(fill=tk.X, pady=5)

            tk.Label(row, text=label, font=("Segoe UI", 10, "bold"),
                     bg=COLORS["input_bg"], fg=COLORS["text_light"],
                     width=15, anchor="w").pack(side=tk.LEFT, padx=10, pady=8)

            tk.Label(row, text=value, font=("Consolas", 9),
                     bg=COLORS["input_bg"], fg=COLORS["text"],
                     anchor="w").pack(side=tk.LEFT, padx=10, pady=8, fill=tk.X, expand=True)

        if result["found_dirs"]:
            tk.Label(content, text="📁 Обнаруженные директории:", font=("Segoe UI", 11, "bold"),
                     bg=COLORS["card"], fg=COLORS["accent"]).pack(anchor="w", pady=(15, 5))

            for directory in result["found_dirs"]:
                tk.Label(content, text=f"  • {directory}", font=("Consolas", 9),
                         bg=COLORS["card"], fg=COLORS["success"]).pack(anchor="w", padx=20)

        if result["found_classes"]:
            tk.Label(content, text="📄 Обнаруженные классы:", font=("Segoe UI", 11, "bold"),
                     bg=COLORS["card"], fg=COLORS["accent"]).pack(anchor="w", pady=(15, 5))

            for class_name in result["found_classes"]:
                tk.Label(content, text=f"  • {class_name}", font=("Consolas", 9),
                         bg=COLORS["card"], fg=COLORS["success"]).pack(anchor="w", padx=20)

        tk.Label(content, text="📋 Детали обнаружения:", font=("Segoe UI", 11, "bold"),
                 bg=COLORS["card"], fg=COLORS["accent"]).pack(anchor="w", pady=(15, 5))

        details_text = scrolledtext.ScrolledText(content, height=10,
                                                 bg=COLORS["input_bg"], fg=COLORS["text"],
                                                 font=("Consolas", 9), wrap=tk.WORD, relief="flat")
        details_text.pack(fill=tk.BOTH, expand=True, pady=5)

        for detail in result["details"]:
            details_text.insert(tk.END, f"{detail}\n")

        details_text.config(state=tk.DISABLED)

        button_frame = tk.Frame(details_window, bg=COLORS["bg"])
        button_frame.pack(pady=15)

        tk.Button(button_frame, text="📂 Открыть папку",
                  command=lambda: subprocess.Popen(f'explorer /select,"{result["path"]}"'),
                  bg=COLORS["accent"], fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=20, pady=10, cursor="hand2").pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="🗑 Удалить файл",
                  command=lambda: self.delete_threat_file(result["path"]),
                  bg=COLORS["danger"], fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=20, pady=10, cursor="hand2").pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="Закрыть", command=details_window.destroy,
                  bg=COLORS["hover"], fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=20, pady=10, cursor="hand2").pack(side=tk.LEFT, padx=5)

    def delete_threat_file(self, file_path):
        try:
            os.remove(file_path)
            self.log_message(f"🗑 Файл удален: {os.path.basename(file_path)}")
            messagebox.showinfo("Успех", "Файл угрозы успешно удален!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить файл: {str(e)}")

    def search_database(self):
        try:
            weight = float(self.search_weight.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный вес!")
            return

        keyword = self.search_name.get().strip()
        results = []

        for name, data in self.detector.active.items():
            for size in data.get("sizes_kb", []):
                if abs(weight - size) <= self.detector.tolerance_kb:
                    results.append((name, size))
            if keyword and keyword.lower() in name.lower():
                results.append((name, None))

        if not results:
            messagebox.showinfo("Поиск", "Совпадений нет")
            return

        message = "🔍 Результаты:\n\n"
        for name, size in results:
            if size:
                message += f"• {name} ({size} KB)\n"
            else:
                message += f"• {name}\n"

        messagebox.showinfo("Поиск", message)
        self.log_message(f"🔍 Найдено: {len(results)}")

    def clear_cache(self):
        success, message = self.detector.clear_cache()
        if success:
            self.log_message("🧹 Кэш сканера очищен")
            messagebox.showinfo("Успех", message)
        else:
            messagebox.showerror("Ошибка", message)

    def show_db_stats(self):
        db_info = self.detector.db.get_database_info()
        stats = f"""
📊 Статистика базы данных:

Всего записей: {db_info['total']}
Читы со строгим режимом: {db_info['strict_mode']}
Обычные читы: {db_info['total'] - db_info['strict_mode']}

С размерами: {db_info['with_sizes']}
С директориями: {db_info['with_dirs']}
С классами: {db_info['with_classes']}

Последнее обновление: {db_info['last_update'] or 'Никогда'}
        """
        messagebox.showinfo("Статистика базы", stats)

    def update_database(self):
        self.log_message("🔄 Начинаем обновление базы данных из Google Sheets...")

        progress_window = tk.Toplevel(self.root)
        progress_window.title("Обновление базы данных")
        progress_window.geometry("400x150")
        progress_window.configure(bg=COLORS["bg"])
        progress_window.resizable(False, False)
        progress_window.transient(self.root)
        progress_window.grab_set()

        tk.Label(progress_window, text="🔄 Обновление базы данных...",
                 font=("Segoe UI", 12, "bold"), bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=20)

        progress = ttk.Progressbar(progress_window, mode='indeterminate')
        progress.pack(fill=tk.X, padx=50, pady=10)
        progress.start()

        tk.Label(progress_window, text="Это может занять несколько секунд",
                 font=("Segoe UI", 9), bg=COLORS["bg"], fg=COLORS["text_light"]).pack(pady=5)

        def update_thread():
            success, message = self.detector.db.update_from_google_sheets()

            if success:
                self.detector.active = self.detector.db.cheat_database

            progress_window.after(0, lambda: self._update_finished(success, message, progress_window))

        threading.Thread(target=update_thread, daemon=True).start()

    def _update_finished(self, success, message, progress_window):
        progress_window.destroy()

        if success:
            self.log_message(f"✅ {message}")

            db_info = self.detector.db.get_database_info()
            info_msg = f"""
✅ База данных успешно обновлена!

📊 Статистика:
• Всего записей: {db_info['total']}
• С размерами: {db_info['with_sizes']}
• С директориями: {db_info['with_dirs']} 
• С классами: {db_info['with_classes']}
• Строгий режим: {db_info['strict_mode']}
• Последнее обновление: {db_info['last_update']}
"""
            messagebox.showinfo("Обновление базы данных", info_msg)

            errors, warnings = self.detector.db.validate_database()
            if warnings:
                self.log_message(f"⚠️ Предупреждения базы: {len(warnings)}")
            if errors:
                self.log_message(f"❌ Ошибки базы: {len(errors)}")

        else:
            self.log_message(f"❌ {message}")
            messagebox.showerror("Ошибка обновления",
                                 f"Не удалось обновить базу данных:\n{message}\n\n"
                                 f"Проверьте подключение к интернету и доступность таблицы.")

    def show_database_manager(self):
        db_window = tk.Toplevel(self.root)
        db_window.title("🗃️ Менеджер базы данных")
        db_window.geometry("800x600")
        db_window.configure(bg=COLORS["bg"])
        db_window.resizable(True, True)

        header = tk.Frame(db_window, bg=COLORS["accent"], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="🗃️ Менеджер базы данных", font=("Segoe UI", 16, "bold"),
                 bg=COLORS["accent"], fg="white").pack(pady=18)

        content = tk.Frame(db_window, bg=COLORS["card"])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        info_frame = tk.Frame(content, bg=COLORS["input_bg"], relief="flat")
        info_frame.pack(fill=tk.X, pady=(0, 15))

        db_info = self.detector.db.get_database_info()

        info_text = f"""
📊 Статистика базы данных:

• Всего записей: {db_info['total']}
• Записей с размерами: {db_info['with_sizes']}
• Записей с директориями: {db_info['with_dirs']}
• Записей с классами: {db_info['with_classes']}
• В строгом режиме: {db_info['strict_mode']}
• Последнее обновление: {db_info['last_update'] or 'Никогда'}
"""
        tk.Label(info_frame, text=info_text, font=("Consolas", 10),
                 bg=COLORS["input_bg"], fg=COLORS["text"], justify=tk.LEFT).pack(padx=15, pady=15)

        buttons_frame = tk.Frame(content, bg=COLORS["card"])
        buttons_frame.pack(fill=tk.X, pady=10)

        action_buttons = [
            ("🔄 Обновить из Google Sheets", self.update_database),
            ("📊 Проверить целостность", self.validate_database),
            ("💾 Создать бэкап", self.create_backup),
            ("📥 Восстановить из бэкапа", self.restore_backup),
            ("🧹 Очистить кэш", self.clear_database_cache)
        ]

        for text, command in action_buttons:
            btn = tk.Button(buttons_frame, text=text, command=command,
                            bg=COLORS["hover"], fg=COLORS["text"], font=("Segoe UI", 10),
                            relief="flat", cursor="hand2", pady=8)
            btn.pack(fill=tk.X, pady=5)

        list_frame = tk.Frame(content, bg=COLORS["card"])
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

        tk.Label(list_frame, text="📋 Список записей в базе:", font=("Segoe UI", 11, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        list_container = tk.Frame(list_frame, bg=COLORS["card"])
        list_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        cheat_list = tk.Listbox(list_container, yscrollcommand=scrollbar.set,
                                bg=COLORS["input_bg"], fg=COLORS["text"],
                                font=("Consolas", 9), selectbackground=COLORS["accent"])
        cheat_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=cheat_list.yview)

        for i, (name, data) in enumerate(self.detector.db.cheat_database.items()):
            has_size = "📏" if data.get("sizes_kb") else "　"
            has_dir = "📁" if data.get("directories") else "　"
            has_class = "📄" if data.get("classes") else "　"
            strict = "🔒" if data.get("strict_mode") else "　"

            cheat_list.insert(tk.END, f"{has_size}{has_dir}{has_class}{strict} {name}")

        cheat_list.bind("<Double-Button-1>", lambda e: self.show_cheat_details_manager(cheat_list, db_window))

        tk.Button(content, text="Закрыть", command=db_window.destroy,
                  bg=COLORS["danger"], fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=30, pady=10, cursor="hand2").pack(pady=15)

    def show_cheat_details_manager(self, cheat_list, parent_window):
        selection = cheat_list.curselection()
        if not selection:
            return

        cheat_name = cheat_list.get(selection[0]).split(" ", 1)[1]
        cheat_data = self.detector.db.cheat_database.get(cheat_name)

        if not cheat_data:
            return

        self.show_cheat_details()

    def validate_database(self):
        errors, warnings = self.detector.db.validate_database()

        result_text = "✅ База данных в порядке!"

        if warnings:
            result_text = f"⚠️ Найдены предупреждения ({len(warnings)}):\n" + "\n".join(f"• {w}" for w in warnings[:10])
            if len(warnings) > 10:
                result_text += f"\n• ... и еще {len(warnings) - 10}"

        if errors:
            result_text = f"❌ Найдены ошибки ({len(errors)}):\n" + "\n".join(f"• {e}" for e in errors[:10])
            if len(errors) > 10:
                result_text += f"\n• ... и еще {len(errors) - 10}"

        messagebox.showinfo("Проверка целостности базы", result_text)
        self.log_message(f"🔍 Проверка целостности: {len(errors)} ошибок, {len(warnings)} предупреждений")

    def create_backup(self):
        self.detector.db._save_backup()
        messagebox.showinfo("Бэкап создан", "Резервная копия базы данных успешно создана!")
        self.log_message("💾 Создана резервная копия базы данных")

    def restore_backup(self):
        backup_file = filedialog.askopenfilename(
            title="Выберите файл бэкапа",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if backup_file:
            success, message = self.detector.db.restore_backup(backup_file)
            if success:
                self.detector.active = self.detector.db.cheat_database
                messagebox.showinfo("Восстановление", message)
                self.log_message("📥 База данных восстановлена из бэкапа")
            else:
                messagebox.showerror("Ошибка", message)

    def clear_database_cache(self):
        try:
            self.log_message("🧹 Кэш базы данных очищен")
            messagebox.showinfo("Успех", "Кэш базы данных очищен!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось очистить кэш: {str(e)}")

    def export_results(self):
        if not self.detector.results:
            messagebox.showinfo("Экспорт", "Нет результатов для экспорта")
            return

        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Экспорт результатов"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("GAMMA DETECTOR - Результаты сканирования\n")
                    f.write("=" * 50 + "\n")
                    f.write(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                    f.write(f"Обнаружено угроз: {len(self.detector.results)}\n\n")

                    for i, result in enumerate(self.detector.results, 1):
                        f.write(f"УГРОЗА #{i}\n")
                        f.write(f"Файл: {result['name']}\n")
                        f.write(f"Тип: {result['cheat_type']}\n")
                        f.write(f"Размер: {result['file_size_kb']} KB\n")
                        f.write(f"Совпадений: {result['match_score']}/3\n")
                        f.write(f"Путь: {result['path']}\n")
                        f.write("Детали:\n")
                        for detail in result['details']:
                            f.write(f"  - {detail}\n")
                        f.write("\n" + "-" * 40 + "\n\n")

                self.log_message(f"📝 Результаты экспортированы в: {file_path}")
                messagebox.showinfo("Успех", f"Результаты экспортированы в:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать результаты: {str(e)}")

    def text_detector(self):
        file_path = filedialog.askopenfilename(
            title="Выберите текстовый файл для анализа",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()

                suspicious_keywords = [
                    "cheat", "hack", "exploit", "bypass", "inject", "crack",
                    "ghost", "aimbot", "xray", "noclip", "flyhack", "killaura",
                    "autoclick", "reach", "velocity", "noslow", "speedmine"
                ]

                found_keywords = []
                text_lower = text.lower()

                for keyword in suspicious_keywords:
                    if keyword in text_lower:
                        found_keywords.append(keyword)

                if found_keywords:
                    result = f"🔍 Обнаружены подозрительные ключевые слова:\n\n"
                    for keyword in found_keywords:
                        result += f"• {keyword}\n"

                    result += f"\nВсего найдено: {len(found_keywords)}"
                    messagebox.showwarning("Текст детектор", result)
                    self.log_message(f"📄 Текст детектор: обнаружено {len(found_keywords)} подозрительных слов")
                else:
                    messagebox.showinfo("Текст детектор", "✅ Подозрительных ключевых слов не обнаружено")
                    self.log_message("📄 Текст детектор: подозрительных слов не обнаружено")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось проанализировать файл: {str(e)}")

    def quick_scan(self):
        quick_paths = [
            str(Path.home() / ".minecraft" / "mods"),
            str(Path.home() / "AppData" / "Roaming" / ".minecraft" / "mods"),
            str(Path.home() / "Downloads")
        ]

        for path in quick_paths:
            if os.path.exists(path):
                self.path_var.set(path)
                self.start_scan()
                return

        messagebox.showinfo("Быстрое сканирование", "Стандартные пути не найдены. Выберите путь вручную.")


# стартуеммммммммммм
if __name__ == "__main__":
    App()