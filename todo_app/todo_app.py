import tkinter as tk
from tkinter import ttk
from pathlib import Path
import sys

json = None
PhotoImage = None
webbrowser = None

class TodoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.is_dark_mode = False
        self.tasks = self.load_tasks()
        self.shift_pressed = False
        self.bulk_selection_mode = False
        self.key_event_processing = False
        self.selected_indices = set()

        self.root.withdraw()

        self.setup_ui()
        self.load_config()
        self.setup_bindings()

        self.listbox.bind('<Button-1>', self.start_drag)
        self.listbox.bind('<B1-Motion>', self.do_drag)
        self.listbox.bind('<ButtonRelease-1>', self.end_drag)

        self.drag_start_index = None

        self.root.after(10, self.show_window)

    def setup_ui(self):
        self.root.title("To-Do")
        self.root.minsize(300, 100)
        self.set_window_icon()

        self.main_frame = tk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(self.main_frame, selectmode=tk.EXTENDED, bd=0, highlightthickness=0,
                                activestyle='none', font=self.get_system_font(), width=40, height=10)
        self.listbox.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=(8, 5))
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
        self.create_context_menu() 

    def setup_bindings(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind_all('<Control-r>', self.toggle_dark_mode)
        self.root.bind_all('<Control-h>', self.show_about_dialog)

        self.listbox.bind('<Control-u>', self.toggle_urgent_task)
        self.listbox.bind('<Control-d>', self.mark_selected_tasks_done)

        self.listbox.bind('<Delete>', self.remove_selected_tasks)
        self.listbox.bind('<Control-e>', self.edit_task_shortcut)
        self.listbox.bind('<Control-a>', self.select_all_or_text)

        self.listbox.bind('<<ListboxSelect>>', self.update_buttons_state)
        self.listbox.bind('<Double-1>', self.mark_selected_tasks_done)
        self.listbox.bind('<Button-1>', self.on_listbox_click)
        self.listbox.bind('<Button-3>', self.show_context_menu)
        self.listbox.bind('<Control-Button-1>', self.on_ctrl_click)
        self.listbox.bind('<Shift-Button-1>', self.on_shift_click)

        self.entry.bind('<Return>', self.add_task)
        self.entry.bind('<KeyRelease>', self.update_buttons_state)



    def on_ctrl_click(self, event):
        """Handle robust Ctrl-click to toggle selection of individual tasks."""
        index = self.listbox.nearest(event.y)
        if index in self.listbox.curselection():
            self.listbox.selection_clear(index)
        else:
            self.listbox.selection_set(index)

        return 'break'

    def on_ctrl_click(self, event):
        """Handle robust Ctrl-click to toggle selection of individual tasks."""
        index = self.listbox.nearest(event.y)
        if index in self.listbox.curselection():
            self.listbox.selection_clear(index)
        else:
            self.listbox.selection_set(index)

        self.update_buttons_state()

        return 'break'

    def on_shift_click(self, event):
        """Handle Shift-click to select a range of tasks."""
        index = self.listbox.nearest(event.y)
        cur_selection = self.listbox.curselection()
        if cur_selection:
            start_index = cur_selection[0]
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(start_index, index)
        else:
            self.listbox.selection_set(index)

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

    def set_window_icon(self, window=None):
        global PhotoImage
        if window is None:
            window = self.root
        icon_path = Path(__file__).parent / 'app_icon.ico'
        if icon_path.is_file():
            window.iconbitmap(icon_path)

    def start_drag(self, event):
        """Handle the start of the drag event."""
        self.drag_start_index = self.listbox.nearest(event.y)
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.drag_start_index)
        self.selected_indices = {self.drag_start_index}
        self.update_buttons_state()

    def do_drag(self, event):
        """Handle the dragging motion and visually highlight the item being dragged over."""
        drag_over_index = self.listbox.nearest(event.y)
        if drag_over_index != self.drag_start_index:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(drag_over_index)
    
    def end_drag(self, event):
        """Handle dropping the item by moving it to the new position."""
        drag_end_index = self.listbox.nearest(event.y)
        if self.drag_start_index is not None and drag_end_index != self.drag_start_index:
            self.reorder_tasks(self.drag_start_index, drag_end_index)
        self.drag_start_index = None

    def reorder_tasks(self, start_index, end_index):
        """Move the task from start_index to end_index in the tasks list."""
        task = self.tasks.pop(start_index)
        self.tasks.insert(end_index, task)
        self.populate_listbox()
        self.save_tasks()
        self.update_buttons_state()

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
            'done_bg': '#29C458' if self.is_dark_mode else '#29C458',
            'done_fg': '#1A7B37' if self.is_dark_mode else '#1A7B37',
            'urgent_bg': '#de3f4d' if self.is_dark_mode else '#de3f4d'
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
            else:
                display_text = f"⬜ {task['name']}"
            self.listbox.insert(tk.END, display_text)
        self.update_listbox_task_backgrounds()
        self.adjust_window_size()
        self.update_title()

    def update_listbox_task_backgrounds(self):
        colors = self.get_theme_colors()
        for index, task in enumerate(self.tasks):
            if task.get('done', False):
                bg, fg = colors['done_bg'], colors['done_fg']
            elif task.get('urgent', False):
                bg, fg = colors['urgent_bg'], 'white'
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
            self.update_title()

            self.entry.focus_set()

    def remove_selected_tasks(self, event=None):
        selected_indices = list(self.listbox.curselection())
        for index in reversed(selected_indices):
            del self.tasks[index]
        self.populate_listbox()
        self.save_tasks()
        self.update_buttons_state()
        self.update_title()


    def mark_selected_tasks_done(self, event=None):
        selected_indices = self.listbox.curselection()
        for index in selected_indices:
            task = self.tasks[index]
            task['done'] = not task.get('done', False)
            if task.get('urgent', False) and task['done']:
                task['urgent'] = False
        self.populate_listbox()
        self.save_tasks()
        self.update_buttons_state()
        self.update_title()


    def toggle_urgent_task(self, event=None):
        selected_indices = self.listbox.curselection()
        for index in selected_indices:
            task = self.tasks[index]
            task['urgent'] = not task.get('urgent', False)
        self.populate_listbox()
        self.save_tasks()
        self.update_buttons_state()
        self.update_title()


    def update_buttons_state(self, event=None):
        has_selection = bool(self.listbox.curselection()) or self.bulk_selection_mode
        if event and event.type == '4':
            return

        self.buttons["➕"]['state'] = 'normal' if self.entry.get("1.0", "end-1c").strip() else 'disabled'
        for button in ["➖", "✔"]:
            self.buttons[button]['state'] = 'normal' if has_selection else 'disabled'

    def adjust_window_size(self):
        num_tasks = len(self.tasks)
        new_height = max(100, min(800, 100 + (num_tasks * 18)))
        self.root.geometry(f"300x{new_height}")

    def count_urgent_tasks(self):
        return sum(1 for task in self.tasks if task.get('urgent', False))

    def update_title(self):
        total_tasks = len(self.tasks)
        done_tasks = sum(task.get('done', False) for task in self.tasks)
        urgent_tasks = self.count_urgent_tasks()

        urgent_text = f"[{urgent_tasks} urgent]" if urgent_tasks > 0 else ""

        if total_tasks == 0:
            self.root.title("To-Do")
        elif done_tasks == total_tasks:
            self.root.title(f"To-Do ({done_tasks}/{total_tasks}) — All done! {urgent_text}")
        else:
            self.root.title(f"To-Do ({done_tasks}/{total_tasks}) {urgent_text}")

    @staticmethod
    def get_base_dir():
        return Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent

    @classmethod
    def get_tasks_file(cls):
        return cls.get_base_dir() / 'todo_app' / 'tasks.json'

    @classmethod
    def get_config_file(cls):
        return cls.get_base_dir() / 'todo_app' / 'config.json'

    @classmethod
    def load_tasks(cls):
        global json
        if json is None:
            import json
        tasks_file = cls.get_tasks_file()
        tasks_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            return json.loads(tasks_file.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def save_tasks(self):
        global json
        if json is None:
            import json
        try:
            self.get_tasks_file().write_text(json.dumps(self.tasks, indent=4), encoding='utf-8')
        except Exception as e:
            print(f"Error saving tasks: {e}")

    def save_config(self):
        global json
        if json is None:
            import json
        try:
            config_file = self.get_config_file()
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config = {
                'geometry': self.root.geometry(),
                'dark_mode': self.is_dark_mode
            }
            config_file.write_text(json.dumps(config, indent=4), encoding='utf-8')
        except Exception as e:
            print(f"Error saving config: {e}")

    def load_config(self):
        global json
        if json is None:
            import json
        config_file = self.get_config_file()
        if config_file.is_file():
            config = json.loads(config_file.read_text(encoding='utf-8'))
            self.is_dark_mode = config.get('dark_mode', False)
            self.apply_theme()
            
            self.initial_geometry = config.get('geometry', '')
        else:
            self.initial_geometry = ''

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Edit Task", command=self.edit_task_shortcut)
        self.context_menu.add_command(label="Un/Mark as Done", command=self.mark_selected_tasks_done)
        self.context_menu.add_command(label="Un/Mark as Urgent", command=self.toggle_urgent_task)
        self.context_menu.add_command(label="Remove Task/s", command=self.remove_selected_tasks)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Toggle Dark Mode", command=self.toggle_dark_mode)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="About", command=self.show_about_dialog)

    def show_about_dialog(self, event=None):
        global PhotoImage
        if PhotoImage is None:
            from tkinter import PhotoImage
        about_window = tk.Toplevel(self.root)
        about_window.title("About")
        about_window.resizable(False, False)

        self.set_window_icon(about_window)

        icon_path = Path(__file__).parent / 'app_logo.png'
        if icon_path.is_file():
            app_icon = PhotoImage(file=icon_path)
            icon_label = tk.Label(about_window, image=app_icon)
            icon_label.image = app_icon 
            icon_label.pack(pady=(5, 5))

        about_text = (
            "To-Do App 0.2.2\n\n"
            "© 2024 Jens Lettkemann <jltk@pm.me>\n\n"
            "This software is licensed under GPLv3+.\n"
        )
        github_link = "https://github.com/jltk/todo-app\n"
        license_link = "https://github.com/jltk/todo-app/LICENSE"

        text_frame = tk.Frame(about_window, padx=10, pady=10)
        text_frame.pack(fill="both", expand=True)

        text = tk.Label(text_frame, text=about_text, anchor="center")
        text.pack(fill="x", pady=(0, 5))

        github_label = tk.Label(text_frame, text=github_link, fg="blue", cursor="hand2")
        github_label.pack(fill="x", pady=5)
        github_label.bind("<Button-1>", lambda e: self.open_link("https://github.com/jltk/todo-app"))

        license_label = tk.Label(text_frame, text=license_link, fg="blue", cursor="hand2")
        license_label.pack(fill="x", pady=5)
        license_label.bind("<Button-1>", lambda e: self.open_link("https://github.com/jltk/todo-app/LICENSE"))

        about_window.update_idletasks()
        min_width = max(text.winfo_width(), github_label.winfo_width(), license_label.winfo_width()) + 20
        min_height = text.winfo_height() + github_label.winfo_height() + license_label.winfo_height() + 40
        about_window.geometry(f"{min_width}x{min_height}")

        self.center_window_over_window(about_window)

    def center_window_over_window(self, window):
        window.update_idletasks()
        
        main_window_width = self.root.winfo_width()
        main_window_height = self.root.winfo_height()
        main_window_x = self.root.winfo_x()
        main_window_y = self.root.winfo_y()

        window_width = window.winfo_reqwidth()
        window_height = window.winfo_reqheight()

        x = main_window_x + (main_window_width - window_width) // 2
        y = main_window_y + (main_window_height - window_height) // 2

        window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def open_link(self, url):
        global webbrowser
        if webbrowser is None:
            import webbrowser
        webbrowser.open(url)

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def on_listbox_click(self, event):
        if event.num == 3:
            self.show_context_menu(event)
        else:
            index = self.listbox.nearest(event.y)
            if self.bulk_selection_mode:
                self.handle_bulk_selection(index)
            else:
                self.handle_single_selection(index)

    def remove_task_shortcut(self, event=None):
        if self.listbox.curselection():
            self.remove_selected_tasks()

    def mark_as_done_shortcut(self, event=None):
        if self.listbox.curselection():
            self.mark_selected_tasks_done()

    def edit_task_shortcut(self, event=None):
        if self.listbox.curselection():
            self.edit_task()

    def edit_task(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            return

        index = selected_indices[0]
        current_task = self.tasks[index]

        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Task")
        edit_window.geometry("200x120")
        edit_window.transient(self.root)
        edit_window.grab_set()

        self.set_window_icon(edit_window)

        frame = tk.Frame(edit_window, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        text_entry = tk.Text(frame, wrap='word', height=2, width=28)
        text_entry.insert(tk.END, current_task['name'])
        text_entry.pack(fill="both", expand=True)

        def select_all_text(event=None):
            text_entry.tag_add(tk.SEL, "1.0", tk.END)
            text_entry.mark_set(tk.INSERT, "1.0")
            text_entry.see(tk.INSERT)
            return "break" 

        text_entry.bind("<Control-a>", select_all_text)

        def on_save(event=None):
            new_name = text_entry.get("1.0", "end-1c").strip()
            if new_name:
                self.tasks[index]['name'] = new_name
                self.populate_listbox()
                self.save_tasks()
                self.update_buttons_state()
                self.update_title()
            edit_window.destroy()

        def on_cancel():
            edit_window.destroy()

        text_entry.bind("<Return>", on_save)

        button_frame = tk.Frame(frame)
        button_frame.pack(fill="x", pady=(10, 0))

        save_button = ttk.Button(button_frame, text="Save", command=on_save)
        save_button.pack(side="left", padx=0)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=on_cancel)
        cancel_button.pack(side="left", padx=5)

        button_frame.pack(side="bottom", pady=(10, 0), fill="x")

        edit_window.protocol("WM_DELETE_WINDOW", on_cancel)
        self.center_window_over_window(edit_window)


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
        self.root.unbind_all('<Control-v>')
        self.root.unbind_all('<Control-u>')
        self.root.unbind_all('<Control-d>')
        self.root.unbind_all('<Delete>')
        self.root.unbind_all('<Control-e>')
        self.root.unbind_all('<Control-a>')
        self.listbox.unbind('<<ListboxSelect>>')
        self.listbox.unbind('<Double-1>')
        self.entry.unbind('<Return>')
        self.entry.unbind('<KeyRelease>')
        self.listbox.unbind('<Button-1>')
        self.listbox.unbind('<Button-3>')
        self.root.unbind_all('<Control-h>')

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

    def update_bulk_selection_mode(self):
        if self.shift_pressed:
            self.bulk_selection_mode = True
        else:
            self.bulk_selection_mode = False
        self.update_buttons_state()

    def on_shift_key_press(self, event):
        self.shift_pressed = True
        self.update_bulk_selection_mode()

    def on_shift_key_release(self, event):
        self.shift_pressed = False
        self.update_bulk_selection_mode()

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
