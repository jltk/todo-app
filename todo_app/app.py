import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
from typing import List, Dict, Any
import sys

class TodoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.is_dark_mode = False
        self.tasks: List[Dict[str, Any]] = self.load_tasks()
        self.ctrl_pressed = False
        self.shift_pressed = False
        self.bulk_selection_mode = False
        self.selected_indices = set()

        self.root.withdraw()

        self.setup_ui()
        self.load_config()
        self.setup_bindings()

        self.root.after(10, self.show_window)

    def setup_ui(self):
        self.root.title("TODO")
        self.root.minsize(300, 100)
        self.set_window_icon()

        self.main_frame = tk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(self.main_frame, selectmode=tk.SINGLE, bd=0, highlightthickness=0,
                                  activestyle='none', font=self.get_system_font(), width=40, height=10)
        self.listbox.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=(10, 5))
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.input_frame = tk.Frame(self.main_frame)
        self.input_frame.grid(row=1, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 5))
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry = tk.Text(self.input_frame, height=1, wrap='none', bd=0, font=self.get_system_font(), insertbackground='black')
        self.entry.grid(row=0, column=0, sticky="ew")

        self.entry.bind('<FocusIn>', self.on_entry_focus_in)
        self.entry.bind('<FocusOut>', self.on_entry_focus_out)
        self.entry.bind('<Button-1>', self.on_entry_click)

        button_style = {'width': 3, 'padding': (0, 0)}
        buttons = [
            ("➕", self.add_task),
            ("➖", self.remove_selected_tasks),
            ("✔", self.mark_selected_tasks_done)
        ]
        self.buttons = {}
        for col, (text, command) in enumerate(buttons, start=1):
            button = ttk.Button(self.input_frame, text=text, command=command, style='TButton', **button_style)
            button.grid(row=0, column=col, padx=(5, 0))
            self.buttons[text] = button

        self.populate_listbox()
        self.apply_theme()
        
        self.update_buttons_state()

    def setup_bindings(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind_all('<Control-d>', self.toggle_dark_mode)
        self.root.bind_all('<Control-u>', self.toggle_urgent_task)
        self.root.bind_all('<Control-m>', self.mark_selected_tasks_done)
        self.root.bind_all('<Delete>', self.remove_selected_tasks)
        self.root.bind('<Control-a>', self.select_all_or_text)
        self.listbox.bind('<<ListboxSelect>>', self.update_buttons_state)
        self.listbox.bind('<Double-1>', self.mark_selected_tasks_done)
        self.entry.bind('<Return>', self.add_task)
        self.entry.bind('<KeyRelease>', self.update_buttons_state)
        self.root.bind('<Control-KeyPress>', self.on_ctrl_key_press)
        self.root.bind('<Control-KeyRelease>', self.on_ctrl_key_release)
        self.root.bind('<Shift-KeyPress>', self.on_shift_key_press)
        self.root.bind('<Shift-KeyRelease>', self.on_shift_key_release)
        self.listbox.bind('<Button-1>', self.on_listbox_click)

    def on_entry_focus_in(self, event=None):
        colors = self.get_theme_colors()
        self.entry.configure(highlightbackground=colors['entry_border_focus'], highlightcolor=colors['entry_border_focus'], highlightthickness=1)
        self.entry.config(insertbackground=colors['caret_color_focus'])

    def on_entry_focus_out(self, event=None):
        colors = self.get_theme_colors()
        self.entry.configure(highlightbackground=colors['entry_bg'], highlightcolor=colors['entry_bg'], highlightthickness=1)
        self.entry.config(insertbackground=colors['caret_color'])

    def on_entry_click(self, event=None):
        self.listbox.selection_clear(0, tk.END)
        self.entry.focus_set()
        self.bulk_selection_mode = False
        self.update_buttons_state()

    def set_window_icon(self):
        icon_path = Path(__file__).parent / 'app_icon.ico'
        if icon_path.is_file():
            self.root.iconbitmap(icon_path)

    def apply_theme(self):
        colors = self.get_theme_colors()
        self.root.configure(bg=colors['bg'])
        self.main_frame.configure(bg=colors['bg'])
        self.input_frame.configure(bg=colors['bg'])
        self.listbox.configure(bg=colors['listbox_bg'], fg=colors['fg'],
                               selectbackground=colors['select_bg'], selectforeground=colors['fg'])
        self.entry.configure(bg=colors['entry_bg'], fg=colors['fg'])
        self.update_buttons_style(colors['button_bg'], colors['button_fg'])
        self.update_listbox_task_backgrounds()

        # Set caret color based on theme
        self.entry.config(insertbackground=colors['caret_color'])

    def get_theme_colors(self):
        return {
            'bg': '#17191e' if self.is_dark_mode else 'white',
            'fg': 'white' if self.is_dark_mode else 'black',
            'entry_bg': '#444444' if self.is_dark_mode else '#f0f0f0',
            'entry_border_focus': '#cccccc' if self.is_dark_mode else '#333333',
            'caret_color': 'white' if self.is_dark_mode else 'black',
            'caret_color_focus': '#cccccc' if self.is_dark_mode else '#333333',
            'button_bg': '#444444' if self.is_dark_mode else '#e0e0e0',
            'button_fg': '#00BFFF' if self.is_dark_mode else '#1E90FF',
            'listbox_bg': '#17191e' if self.is_dark_mode else 'white',
            'select_bg': '#555555' if self.is_dark_mode else '#d3d3d3',
            'done_color': '#29C458' if self.is_dark_mode else '#29C458'
        }

    def update_buttons_style(self, bg, fg):
        style = ttk.Style()
        style.configure('TButton', background=bg, foreground=fg, padding=5)
        style.map('TButton', 
                  background=[('active', bg), ('disabled', '#666666' if self.is_dark_mode else '#c0c0c0')],
                  foreground=[('active', fg), ('disabled', 'grey')])

    def populate_listbox(self):
        self.listbox.delete(0, tk.END)
        for index, task in enumerate(self.tasks):
            if task.get('done', False):
                display_text = f"✔ {task['name']}"
            elif task.get('urgent', False):
                display_text = f"🔲 {task['name']}"
            else:
                display_text = f"⬜ {task['name']}"
            self.listbox.insert(tk.END, display_text)
        self.update_listbox_task_backgrounds()
        self.adjust_window_size()

    def update_listbox_task_backgrounds(self):
        colors = self.get_theme_colors()
        for index, task in enumerate(self.tasks):
            if task.get('done', False):
                bg, fg = colors['done_color'], 'white'
            elif task.get('urgent', False):
                bg, fg = '#e72f3f', 'white'
            else:
                bg, fg = colors['listbox_bg'], colors['fg']
            self.listbox.itemconfig(index, {'bg': bg, 'fg': fg})

    def add_task(self, event=None):
        task_name = self.entry.get("1.0", "end-1c").strip()
        if task_name:
            self.tasks.append({'name': task_name})
            self.populate_listbox()
            self.save_tasks()
            self.entry.delete("1.0", tk.END)
            self.update_buttons_state()

    def remove_selected_tasks(self, event=None):
        selected_indices = sorted(self.listbox.curselection(), reverse=True)
        for index in selected_indices:
            del self.tasks[index]
        self.populate_listbox()
        self.save_tasks()
        self.update_buttons_state()

    def mark_selected_tasks_done(self, event=None):
        selected_indices = self.listbox.curselection()
        for index in selected_indices:
            task = self.tasks[index]
            task['done'] = not task.get('done', False)
        self.populate_listbox()
        self.save_tasks()
        self.update_buttons_state()

    def toggle_urgent_task(self, event=None):
        selected_indices = self.listbox.curselection()
        for index in selected_indices:
            task = self.tasks[index]
            task['urgent'] = not task.get('urgent', False)
        self.populate_listbox()
        self.save_tasks()
        self.update_buttons_state()

    def update_buttons_state(self, event=None):
        has_selection = bool(self.listbox.curselection()) or self.bulk_selection_mode
        self.buttons["➕"]['state'] = 'normal' if self.entry.get("1.0", "end-1c").strip() else 'disabled'
        for button in ["➖", "✔"]:
            self.buttons[button]['state'] = 'normal' if has_selection else 'disabled'

    def adjust_window_size(self):
        num_tasks = len(self.tasks)
        new_height = max(100, min(500, 100 + (num_tasks * 20)))
        self.root.geometry(f"300x{new_height}")

    @staticmethod
    def get_base_dir():
        return Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent

    @classmethod
    def get_tasks_file(cls):
        return cls.get_base_dir() / 'todo_app' / 'data' / 'tasks.json'

    @classmethod
    def get_config_file(cls):
        return cls.get_base_dir() / 'todo_app' / 'data' / 'config.json'

    @classmethod
    def load_tasks(cls):
        tasks_file = cls.get_tasks_file()
        tasks_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            return json.loads(tasks_file.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def save_tasks(self):
        try:
            self.get_tasks_file().write_text(json.dumps(self.tasks, indent=4), encoding='utf-8')
        except Exception as e:
            print(f"Error saving tasks: {e}")

    def save_config(self):
        config_file = self.get_config_file()
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config = {
            'geometry': self.root.geometry(),
            'dark_mode': self.is_dark_mode
        }
        config_file.write_text(json.dumps(config, indent=4), encoding='utf-8')

    def load_config(self):
        config_file = self.get_config_file()
        if config_file.is_file():
            config = json.loads(config_file.read_text(encoding='utf-8'))
            self.is_dark_mode = config.get('dark_mode', False)
            self.apply_theme()
            
            self.initial_geometry = config.get('geometry', '')
        else:
            self.initial_geometry = ''

    def show_window(self):
        if self.initial_geometry:
            self.root.geometry(self.initial_geometry)
        else:
            self.center_window(default_size="300x100")
        
        self.root.deiconify()
        
        self.root.lift()
        self.root.focus_force()
        
        if sys.platform == "win32":
            self.root.attributes('-topmost', True)
            self.root.update()
            self.root.attributes('-topmost', False)

    def on_close(self):
        self.save_config()
        self.root.destroy()

    def toggle_dark_mode(self, event=None):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def center_window(self, default_size=None):
        self.root.update_idletasks()
        if default_size:
            width, height = map(int, default_size.split('x'))
        else:
            width, height = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    @staticmethod
    def get_system_font():
        return ('Segoe UI', 10) if sys.platform == 'win32' else ('San Francisco', 11) if sys.platform == 'darwin' else ('Arial', 10)

    def on_ctrl_key_press(self, event):
        self.ctrl_pressed = True
        self.update_bulk_selection_mode()

    def on_ctrl_key_release(self, event):
        self.ctrl_pressed = False
        self.update_bulk_selection_mode()

    def on_shift_key_press(self, event):
        self.shift_pressed = True
        self.update_bulk_selection_mode()

    def on_shift_key_release(self, event):
        self.shift_pressed = False
        self.update_bulk_selection_mode()

    def update_bulk_selection_mode(self):
        self.bulk_selection_mode = self.ctrl_pressed or self.shift_pressed
        if not self.bulk_selection_mode:
            self.selected_indices = set(self.listbox.curselection())
        self.update_buttons_state()

    def on_listbox_click(self, event):
        index = self.listbox.nearest(event.y)
        if self.bulk_selection_mode:
            self.handle_bulk_selection(index)
        else:
            self.handle_single_selection(index)

    def handle_single_selection(self, index):
        if index in self.selected_indices:
            self.selected_indices.remove(index)
            self.listbox.selection_clear(index)
        else:
            self.selected_indices.add(index)
            self.listbox.selection_set(index)
        self.update_buttons_state()

    def handle_bulk_selection(self, index):
        if index in self.selected_indices:
            self.selected_indices.remove(index)
        else:
            self.selected_indices.add(index)
        
        self.update_listbox_selections()

    def update_listbox_selections(self):
        self.listbox.selection_clear(0, tk.END)
        for idx in self.selected_indices:
            self.listbox.selection_set(idx)
        self.update_buttons_state()

    def select_all_tasks(self, event=None):
        self.selected_indices = set(range(len(self.tasks)))
        self.update_listbox_selections()

    def select_all_or_text(self, event=None):
        if self.entry.focus_get() == self.entry:
            self.entry.tag_add(tk.SEL, "1.0", tk.END)
            self.entry.mark_set(tk.INSERT, "1.0")
            self.entry.see(tk.INSERT)
        else:
            self.select_all_tasks()

def main():
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
