from setuptools import setup, find_packages

setup(
    name="reporting",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "jinja2",
        "pytest",
    ],
    python_requires=">=3.8",
)