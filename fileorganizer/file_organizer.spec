# file_organizer.spec
# Build with: pyinstaller file_organizer.spec

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# ttkbootstrap ships its theme definitions (fonts/colors/images) as package
# data - collect_data_files makes sure PyInstaller bundles them so the dark
# theme actually renders in the built exe, not just when run from source.
datas = collect_data_files('ttkbootstrap')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['watchdog.observers.winapi', 'PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FileOrganizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX-compressed binaries are strongly associated with malware packers,
    # which is a big driver of antivirus/SmartScreen false positives on
    # PyInstaller exes. Leaving the exe uncompressed (bigger file, but far
    # less "suspicious"-looking) meaningfully cuts down on false flags.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no black console window behind the GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # put an .ico path here if you make one, e.g. 'icon.ico'
)
