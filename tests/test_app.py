import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
from todo_app.app import TodoApp, Task, TaskStatus, ThemeColors

class TestTodoApp(unittest.TestCase):

    @patch('todo_app.app.Path.read_text')
    def test_load_tasks(self, mock_read_text):
        mock_read_text.return_value = json.dumps([
            {"name": "Task 1", "status": "PENDING", "urgent": False},
            {"name": "Task 2", "status": "DONE", "urgent": True}
        ])
        tasks = TodoApp._load_tasks()
        self.assertEqual(len(tasks), 2)
        self.assertIsInstance(tasks[0], Task)
        self.assertEqual(tasks[0].name, "Task 1")
        self.assertEqual(tasks[0].status, TaskStatus.PENDING)
        self.assertFalse(tasks[0].urgent)
        self.assertEqual(tasks[1].name, "Task 2")
        self.assertEqual(tasks[1].status, TaskStatus.DONE)
        self.assertTrue(tasks[1].urgent)

    @patch('todo_app.app.Path.write_text')
    def test_save_tasks(self, mock_write_text):
        tasks = [
            Task("Task 1", TaskStatus.PENDING, False),
            Task("Task 2", TaskStatus.DONE, True)
        ]
        TodoApp._save_tasks(tasks)
        mock_write_text.assert_called_once()
        saved_data = json.loads(mock_write_text.call_args[0][0])
        self.assertEqual(len(saved_data), 2)
        self.assertEqual(saved_data[0]['name'], "Task 1")
        self.assertEqual(saved_data[0]['status'], "PENDING")
        self.assertFalse(saved_data[0]['urgent'])
        self.assertEqual(saved_data[1]['name'], "Task 2")
        self.assertEqual(saved_data[1]['status'], "DONE")
        self.assertTrue(saved_data[1]['urgent'])

    def test_toggle_dark_mode(self):
        app = TodoApp(MagicMock())
        initial_mode = app.is_dark_mode
        app._toggle_dark_mode()
        self.assertNotEqual(initial_mode, app.is_dark_mode)

    def test_get_theme_colors(self):
        app = TodoApp(MagicMock())
        light_colors = app._get_theme_colors()
        self.assertEqual(light_colors, ThemeColors.LIGHT.value)
        app.is_dark_mode = True
        dark_colors = app._get_theme_colors()
        self.assertEqual(dark_colors, ThemeColors.DARK.value)

    def test_add_task(self):
        app = TodoApp(MagicMock())
        app.entry = MagicMock()
        app.entry.get.return_value = "New Task"
        app._add_task()
        self.assertEqual(len(app.tasks), 1)
        self.assertEqual(app.tasks[0].name, "New Task")
        self.assertEqual(app.tasks[0].status, TaskStatus.PENDING)
        self.assertFalse(app.tasks[0].urgent)

    def test_remove_selected_tasks(self):
        app = TodoApp(MagicMock())
        app.tasks = [Task("Task 1"), Task("Task 2"), Task("Task 3")]
        app.listbox = MagicMock()
        app.listbox.curselection.return_value = [1]
        app._remove_selected_tasks()
        self.assertEqual(len(app.tasks), 2)
        self.assertEqual(app.tasks[0].name, "Task 1")
        self.assertEqual(app.tasks[1].name, "Task 3")

    def test_mark_selected_tasks_done(self):
        app = TodoApp(MagicMock())
        app.tasks = [Task("Task 1"), Task("Task 2")]
        app.listbox = MagicMock()
        app.listbox.curselection.return_value = [0]
        app._mark_selected_tasks_done()
        self.assertEqual(app.tasks[0].status, TaskStatus.DONE)
        self.assertEqual(app.tasks[1].status, TaskStatus.PENDING)

if __name__ == "__main__":
    unittest.main()
