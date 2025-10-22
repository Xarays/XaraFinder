import tkinter as tk
from tkinter import messagebox
import webbrowser
from pathlib import Path
import subprocess

class ToolManager:
    @staticmethod
    def download_all_tools():
        try:
            tools_dir = Path("GammaDetector_Tools"); tools_dir.mkdir(exist_ok=True)
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
            with open(tools_dir / "README.txt", "w", encoding="utf-8") as f: f.write(readme_content)
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
            with open(tools_dir / "Tools_Links.bat", "w", encoding="utf-8") as f: f.write(bat_content)
            messagebox.showinfo("Успех", f"Папка с инструментами создана: {tools_dir.absolute()}\n\nВ папке вы найдете:\n• README.txt - описание инструментов\n• Tools_Links.bat - быстрый доступ к ссылкам\n\nТеперь вы можете скачать инструменты с официальных сайтов.")
            subprocess.Popen(f'explorer "{tools_dir.absolute()}"')
        except Exception as e: messagebox.showerror("Ошибка", f"Не удалось создать архив инструментов: {str(e)}")