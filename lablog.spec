# PyInstaller spec for the portable, offline lablog desktop app.
#
#   cd ui && npm install && npm run build && cd ..
#   uv run pyinstaller lablog.spec
#
# Produces dist/lablog (one-folder bundle). Zip it and run anywhere without a
# Python install. The Jupyter kernel (cell execution) and the optional voice
# model are heavy; see README "Packaging" for trimming options.

from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [("ui/dist", "ui/dist")]
binaries = []
hiddenimports = ["lablog.api", "ipykernel.kernelapp"]

# Jupyter / zmq / uvicorn discover modules dynamically; pull them in whole.
for pkg in ("jupyter_client", "ipykernel", "zmq", "uvicorn", "webview"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

hiddenimports += collect_submodules("encodings")


a = Analysis(
    ["packaging/desktop_entry.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["faster_whisper", "sounddevice", "tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="lablog",
    console=False,  # ventana sin consola
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="lablog",
)
