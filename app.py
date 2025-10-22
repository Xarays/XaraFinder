import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import json, os, threading, time, subprocess, webbrowser
from pathlib import Path
from detector import Detector, SoundManager
from recycle_checker import RecycleChecker
from aquarium import Aquarium
from tool_manager import ToolManager

COLORS = {
    "bg": "#0d1117", "card": "#161b22", "card_dark": "#0d1117",
    "accent": "#58a6ff", "danger": "#f85149", "success": "#3fb950",
    "warning": "#d29922", "text": "#c9d1d9", "text_light": "#8b949e",
    "input_bg": "#1c2128", "hover": "#21262d", "scrollbar": "#30363d"
}


class App:
    def __init__(self):
        self.detector = Detector()
        self.recycle_checker = RecycleChecker()
        self.root = tk.Tk()
        self.root.title("🛡️ GAMMA DETECTOR")
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
            "fast_scan": tk.BooleanVar(value=True),
            "scan_exe": tk.BooleanVar(value=True)
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
        header.pack_propagate(False)

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

    def start_comprehensive_scan(self):
        """ЗАПУСК КОМПЛЕКСНОГО СКАНИРОВАНИЯ ВСЕХ ДИСКОВ"""
        if not messagebox.askyesno("ВНИМАНИЕ",
                                   "🚨 КОМПЛЕКСНОЕ СКАНИРОВАНИЕ ВСЕХ ДИСКОВ!\n\n"
                                   "Это займет ОЧЕНЬ много времени (несколько часов).\n"
                                   "Сканируются ВСЕ файлы на ВСЕХ дисках.\n\n"
                                   "Продолжить?"):
            return

        self.verdict_label.config(
            text="🚀 ЗАПУСК КОМПЛЕКСНОГО СКАНИРОВАНИЯ...",
            bg=COLORS["warning"],
            fg="white",
            font=("Segoe UI", 14, "bold")
        )

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

        self.log_message("🚀 ЗАПУСК КОМПЛЕКСНОГО СКАНИРОВАНИЯ ВСЕХ ДИСКОВ!")
        self.log_message("⚠️ Это может занять несколько часов!")
        self.log_message("🔍 Сканируем все диски: C:\\\\, D:\\\\, E:\\\\ и т.д.")

        scan_thread = threading.Thread(target=self._comprehensive_scan_thread, daemon=True)
        scan_thread.start()

    def _comprehensive_scan_thread(self):
        """ПОТОК КОМПЛЕКСНОГО СКАНИРОВАНИЯ"""
        start_time = time.time()
        all_jars = []

        # Сканируем все доступные диски
        for drive_letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            drive_path = f"{drive_letter}:\\"
            if os.path.exists(drive_path):
                self.log_message(f"🔍 Сканируем диск {drive_path}...")
                drive_jars = self.detector.scan_entire_drive(drive_letter)
                all_jars.extend(drive_jars)
                self.log_message(f"📦 На диске {drive_path} найдено: {len(drive_jars)} JAR файлов")

        self.log_message(f"🎯 ВСЕГО НАЙДЕНО JAR ФАЙЛОВ: {len(all_jars)}")

        if not all_jars:
            self.log_message("ℹ️ JAR файлы не найдены")
            self.scan_finished()
            return

        # Запускаем сканирование найденных файлов
        results = self.detector.scan(all_jars, self.update_progress, self.log_message, self.settings["scan_exe"].get())

        total_time = time.time() - start_time
        self.log_message(f"⏱️ Комплексное сканирование завершено за {total_time:.2f} секунд")
        self.log_message(f"📊 Производительность: {len(all_jars) / total_time:.1f} файлов/секунду")

        for result in results:
            self.add_scan_result(result)

        self.show_verdict(bool(results), len(results))

        if results:
            self.log_message(f"🚨 ОБНАРУЖЕНО УГРОЗ: {len(results)}")
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
        self.build_settings_tab(settings_tab)

        tools_tab = tk.Frame(tabs, bg=COLORS["bg"])
        tabs.add(tools_tab, text="🔧 Инструменты")
        self.build_tools_tab(tools_tab)

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

        # Добавьте эту кнопку после обычной кнопки сканирования
        self.comprehensive_btn = tk.Button(ctrl, text="🌍 Комплексное сканирование",
                                           command=self.start_comprehensive_scan,
                                           bg=COLORS["danger"], fg="white", font=("Segoe UI", 11, "bold"),
                                           relief="flat", padx=25, pady=12, cursor="hand2")
        self.comprehensive_btn.grid(row=0, column=5, padx=15, pady=15)

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
                                         columns=("file", "size", "type", "cheat", "score", "conditions"),
                                         show="headings", height=15)

        for col, text, width in [
            ("file", "Файл", 250),
            ("size", "Размер (KB)", 90),
            ("type", "Тип", 60),
            ("cheat", "Тип чита", 160),
            ("score", "Совпадений", 80),
            ("conditions", "Условия", 180)
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

    def build_settings_tab(self, parent):
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
            ("🚀 Быстрое сканирование", "Использовать оптимизированные алгоритмы (рекомендуется)", "fast_scan", None),
            ("🔍 Сканировать EXE", "Сканировать .exe файлы (обнаружение Nursultan и других)", "scan_exe", None)
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
        • 🔥 ОБНОВЛЕНИЕ: Обнаружение .exe файлов (Nursultan)
                """

        tk.Label(perf_card, text=perf_text, font=("Consolas", 9),
                 bg=COLORS["success"], fg="white", justify=tk.LEFT).pack(padx=15, pady=15)

        apply_btn = tk.Button(parent, text="💾 Применить настройки", command=self.apply_settings,
                              bg=COLORS["success"], fg="white", font=("Segoe UI", 12, "bold"),
                              relief="flat", padx=30, pady=15, cursor="hand2")
        apply_btn.pack(pady=20)

    def build_tools_tab(self, parent):
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
                "fast_scan": self.settings["fast_scan"].get(),
                "scan_exe": self.settings["scan_exe"].get()
            }

            with open("detector_settings.json", "w") as f:
                json.dump(settings_data, f)

            self.log_message("⚙️ Настройки высокой производительности применены!")
            messagebox.showinfo("Успех", "Настройки производительности применены!\n\n" +
                                f"Потоки: {self.detector.max_threads}\n" +
                                f"Быстрое сканирование: {'ВКЛ' if self.settings['fast_scan'].get() else 'ВЫКЛ'}\n" +
                                f"Сканирование EXE: {'ВКЛ' if self.settings['scan_exe'].get() else 'ВЫКЛ'}")

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
            results = self.detector.scan(jars, self.update_progress, self.log_message, self.settings["scan_exe"].get())
        else:
            results = self.detector.scan(jars, self.update_progress, self.log_message, self.settings["scan_exe"].get())

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
        timestamp = time.strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def update_progress(self, stats):
        for key, value in stats.items():
            if key in self.stats_labels:
                self.stats_labels[key].config(text=str(value))

        if stats["total"] > 0:
            self.progress_bar["value"] = (stats["checked"] / stats["total"]) * 100

        import psutil
        self.cpu_label.config(text=f"CPU: {psutil.cpu_percent():.1f}%")
        self.mem_label.config(text=f"RAM: {psutil.virtual_memory().percent:.1f}%")
        self.root.update_idletasks()

    def add_scan_result(self, result):
        file_type = result.get("file_type", "JAR")

        # Безопасное получение conditions_met
        conditions_met = result.get("conditions_met", [])

        # Преобразуем в список, если это не итерируемый объект
        if not isinstance(conditions_met, (list, tuple)):
            if isinstance(conditions_met, (int, float)):
                conditions_met = [str(conditions_met)]
            else:
                conditions_met = [str(conditions_met)] if conditions_met else []

        # Безопасное создание строки условий
        conditions_str = " | ".join(map(str, conditions_met)) if conditions_met else "нет данных"

        self.results_tree.insert("", 0, values=(
            result["name"],
            result["file_size_kb"],
            file_type,
            result["cheat_type"],
            f"{result['match_score']}/3",
            conditions_str
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

        file_type = result.get("file_type", "JAR")

        info_labels = [
            ("Файл:", result["name"]),
            ("Тип файла:", file_type),
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
                    f.write(f"Дата: {time.strftime('%d.%m.%Y %H:%M:%S')}\n")
                    f.write(f"Обнаружено угроз: {len(self.detector.results)}\n\n")

                    for i, result in enumerate(self.detector.results, 1):
                        file_type = result.get("file_type", "JAR")
                        f.write(f"УГРОЗА #{i}\n")
                        f.write(f"Файл: {result['name']}\n")
                        f.write(f"Тип файла: {file_type}\n")
                        f.write(f"Тип чита: {result['cheat_type']}\n")
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