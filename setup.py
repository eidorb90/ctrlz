from setuptools import setup, find_packages

setup(
    name="ctrlz",
    version="0.1.0",
    packages=find_packages(),  # Discover all packages, including 'app'
    install_requires=[
        "colorama",
    ],
    entry_points={
        "console_scripts": [
            "ctrlz=app.main:main",  # Use the correct import path
        ],
    },
)
