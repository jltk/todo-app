import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["tkinter", "json", "pathlib"],
    "excludes": ["unittest", "email", "html", "http", "xml"],
    "include_files": [
        ("todo_app/app_icon.ico", "app_icon.ico"),
        ("todo_app/app_logo.png", "app_logo.png"),
    ],
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="TodoApp",
    version="0.3.0",
    description="A simple Todo application with python Tkinter GUI",
    options={"build_exe": build_exe_options},
    executables=[Executable("todo_app/todo_app.py", base=base, icon="todo_app/app_icon.ico")],
)
