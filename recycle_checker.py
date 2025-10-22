import os, json, subprocess
from pathlib import Path
from datetime import datetime, timedelta

class RecycleChecker:
    def __init__(self):
        self.clear_history = []; self.load_history()

    def load_history(self):
        try:
            history_file = Path("recycle_history.json")
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f); self.clear_history = data.get("clear_history", [])
        except: self.clear_history = []

    def save_history(self):
        try:
            with open("recycle_history.json", 'w', encoding='utf-8') as f:
                json.dump({"clear_history": self.clear_history}, f, ensure_ascii=False, indent=2)
        except: pass

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
            process = subprocess.Popen(["powershell", "-Command", ps_command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            stdout, stderr = process.communicate(timeout=30)
            if stdout:
                try:
                    files_data = json.loads(stdout.decode('utf-8'))
                    if not isinstance(files_data, list): files_data = [files_data]
                    now = datetime.now(); time_ago = now - timedelta(days=14)
                    for file_info in files_data:
                        try:
                            file_name = file_info.get('Name', ''); file_size = file_info.get('Length', 0) / 1024
                            last_write = file_info.get('LastWriteTime', ''); full_path = file_info.get('FullName', '')
                            if file_name.lower().endswith(('.jar', '.exe', '.dll', '.class')) and last_write:
                                if ':' in last_write: mod_time = datetime.strptime(last_write, '%m/%d/%Y %H:%M:%S')
                                else: mod_time = datetime.strptime(last_write, '%m/%d/%Y')
                                if mod_time >= time_ago:
                                    result["deleted"].append({"name": file_name, "date": mod_time.strftime("%d.%m.%Y"),
                                        "time": mod_time.strftime("%H:%M:%S"), "size": round(file_size, 1), "path": full_path})
                        except: continue
                except json.JSONDecodeError: self._fallback_check(result)
            else: self._fallback_check(result)
        except: self._fallback_check(result)
        result["deleted"].sort(key=lambda x: f"{x['date']} {x['time']}", reverse=True)
        if not result["deleted"]:
            result["cleared"] = True; clear_info = self._get_clear_time()
            if clear_info:
                result["clear_date"] = clear_info["date"]; result["clear_time"] = clear_info["time"]
                new_clear = {"date": clear_info["date"], "time": clear_info["time"], "detected_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S")}
                if not any(clear["date"] == new_clear["date"] and clear["time"] == new_clear["time"] for clear in self.clear_history):
                    self.clear_history.append(new_clear); self.save_history()
        return result

    def _fallback_check(self, result):
        now = datetime.now(); time_ago = now - timedelta(days=14)
        for drive in [f"{chr(c)}:\\\\" for c in range(65, 91) if os.path.exists(f"{chr(c)}:\\\\")]:
            recycle_bin = os.path.join(drive, "$Recycle.Bin")
            if not os.path.isdir(recycle_bin): continue
            try:
                for user_folder in os.listdir(recycle_bin):
                    user_path = os.path.join(recycle_bin, user_folder)
                    if not os.path.isdir(user_path): continue
                    for root, dirs, files in os.walk(user_path):
                        for file in files:
                            if file.lower().endswith((".jar", ".exe", ".dll", ".class")):
                                file_path = os.path.join(root, file)
                                try:
                                    stat = os.stat(file_path); mod_time = datetime.fromtimestamp(stat.st_mtime)
                                    if mod_time >= time_ago:
                                        result["deleted"].append({"name": file, "date": mod_time.strftime("%d.%m.%Y"),
                                            "time": mod_time.strftime("%H:%M:%S"), "size": round(stat.st_size / 1024, 1), "path": file_path})
                                except: pass
            except: pass

    def _get_clear_time(self):
        try:
            for drive in [f"{chr(c)}:\\\\" for c in range(65, 91) if os.path.exists(f"{chr(c)}:\\\\")]:
                recycle_bin = os.path.join(drive, "$Recycle.Bin")
                if os.path.isdir(recycle_bin):
                    try:
                        stat = os.stat(recycle_bin); mtime = datetime.fromtimestamp(stat.st_mtime)
                        return {"date": mtime.strftime("%d.%m.%Y"), "time": mtime.strftime("%H:%M:%S")}
                    except: continue
        except: pass
        return None

    def clear_history_data(self):
        self.clear_history = []; self.save_history()