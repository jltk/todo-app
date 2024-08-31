# tests/test_app.py

import unittest
from todo_app.app import load_tasks, save_tasks

class TestTodoApp(unittest.TestCase):
    def test_load_tasks(self):
        tasks = load_tasks()
        self.assertIsInstance(tasks, list)

    def test_save_tasks(self):
        save_tasks(["test task"])
        tasks = load_tasks()
        self.assertIn("test task", tasks)

if __name__ == "__main__":
    unittest.main()
