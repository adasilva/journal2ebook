# setup.py
import setuptools

from src import __version__

setuptools.setup(
    version=__version__,
    install_requires=["appdirs", "poppler", "image", "pdf2image"],
    entry_points={"console_scripts": ["journal2ebook=src._window:main"]},
)
