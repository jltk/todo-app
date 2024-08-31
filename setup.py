from setuptools import setup, find_packages

setup(
    name="todo-app",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # List any additional dependencies here
    ],
    entry_points={
        'console_scripts': [
            'todo-app=todo_app.app:main',
        ],
    },
)
