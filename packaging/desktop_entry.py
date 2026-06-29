"""PyInstaller entry point for the lablog desktop bundle.

Kept separate from the package so the spec has a stable, import-light script to
analyse. All it does is launch the native window.
"""

from lablog.desktop import run

if __name__ == "__main__":
    run()
