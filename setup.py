from setuptools import setup, find_packages

setup(
    name="todo-app",
    version="0.2.2",
    packages=find_packages(),
    install_requires=[

    ],
    entry_points={
        'console_scripts': [
            'todo-app=todo_app.app:main',
        ],
    },
)
