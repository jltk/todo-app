import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
import json
from pathlib import Path
import sys
sys.path.append('../')
from todo_app.todo_app import TodoApp

class TestTodoApp(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.app = TodoApp(self.root)

    def tearDown(self):
        self.root.destroy()

    @patch('todo_app.todo_app.Path.read_text')
    def test_load_tasks(self, mock_read_text):
        mock_tasks = [
            {"name": "Task 1", "done": False, "cancelled": False, "urgent": False, "separator": False},
            {"name": "Task 2", "done": True, "cancelled": False, "urgent": True, "separator": False},
            {"name": "───────", "separator": True, "title": False}
        ]
        mock_read_text.return_value = json.dumps(mock_tasks)
        
        tasks = self.app.load_tasks()
        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[0]['name'], "Task 1")
        self.assertFalse(tasks[0]['done'])
        self.assertTrue(tasks[1]['done'])
        self.assertTrue(tasks[1]['urgent'])
        self.assertTrue(tasks[2]['separator'])

    @patch('todo_app.todo_app.Path.write_text')
    def test_save_tasks(self, mock_write_text):
        self.app.tasks = [
            {"name": "Task 1", "done": False, "cancelled": False, "urgent": False, "separator": False},
            {"name": "Task 2", "done": True, "cancelled": False, "urgent": True, "separator": False},
            {"name": "───────", "separator": True, "title": False}
        ]
        self.app.save_tasks()
        mock_write_text.assert_called_once()
        saved_data = json.loads(mock_write_text.call_args[0][0])
        self.assertEqual(len(saved_data), 3)
        self.assertEqual(saved_data[0]['name'], "Task 1")
        self.assertFalse(saved_data[0]['done'])
        self.assertTrue(saved_data[1]['urgent'])
        self.assertTrue(saved_data[2]['separator'])

    def test_toggle_dark_mode(self):
        initial_mode = self.app.is_dark_mode
        self.app.toggle_dark_mode()
        self.assertNotEqual(initial_mode, self.app.is_dark_mode)

    def test_add_task(self):
        self.app.entry = MagicMock()
        self.app.entry.get.return_value = "New Task"
        self.app.add_task()
        self.assertEqual(len(self.app.tasks), 1)
        self.assertEqual(self.app.tasks[0]['name'], "New Task")
        self.assertFalse(self.app.tasks[0]['done'])

    @patch('todo_app.todo_app.TodoApp.populate_listbox')
    @patch('todo_app.todo_app.TodoApp.save_tasks')
    def test_remove_selected_tasks(self, mock_save, mock_populate):
        self.app.tasks = [
            {"name": "Task 1", "done": False, "cancelled": False, "urgent": False, "separator": False},
            {"name": "Task 2", "done": False, "cancelled": False, "urgent": False, "separator": False}
        ]
        self.app.listbox = MagicMock()
        self.app.listbox.curselection.return_value = [0]
        self.app.remove_selected_tasks()
        self.assertEqual(len(self.app.tasks), 1)
        self.assertEqual(self.app.tasks[0]['name'], "Task 2")

    @patch('todo_app.todo_app.TodoApp.populate_listbox')
    @patch('todo_app.todo_app.TodoApp.save_tasks')
    def test_mark_selected_tasks_done(self, mock_save, mock_populate):
        self.app.tasks = [
            {"name": "Task 1", "done": False, "cancelled": False, "urgent": False, "separator": False},
            {"name": "Task 2", "done": False, "cancelled": False, "urgent": False, "separator": False}
        ]
        self.app.listbox = MagicMock()
        self.app.listbox.curselection.return_value = [0]
        self.app.mark_selected_tasks_done()
        self.assertTrue(self.app.tasks[0]['done'])
        self.assertFalse(self.app.tasks[1]['done'])

if __name__ == "__main__":
    unittest.main()
