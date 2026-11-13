# -*- mode: python ; coding: utf-8 -*-

# 일본어 체험판 빌드 — TRIAL.flag을 datas로 동봉해 main.py의 TRIAL_MODE를 True로 켠다.
# KOR과 차이는 (1) DEFAULT_CONFIG['language']가 임시 'JPN'으로 패치된 main.py로 빌드,
# (2) exe 이름 'ファーキャットファーキャット 体験版'.

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('1.png', '.'),
        ('app_icon.ico', '.'),
        ('furcat_icon_16.png', '.'),
        ('Galmuri11.ttf', '.'), ('Galmuri11-Bold.ttf', '.'),
        ('Galmuri11Bitmap.ttf', '.'), ('Galmuri11Bitmap-Bold.ttf', '.'),
        ('TRIAL.flag', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'numpy', 'PIL', 'Pillow', 'pandas', 'matplotlib', 'scipy', 'tkinter',
        'test', 'unittest', 'xmlrpc', 'pydoc', 'doctest',
        'PyQt5', 'PyQt6', 'PySide2',
        'PySide6.QtSql', 'PySide6.QtTest', 'PySide6.QtXml', 'PySide6.QtNetwork',
        'PySide6.QtDBus', 'PySide6.QtDesigner', 'PySide6.QtHelp',
        'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
        'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets',
        'PySide6.QtPositioning', 'PySide6.QtLocation',
        'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickWidgets',
        'PySide6.QtQuick3D', 'PySide6.QtCharts', 'PySide6.QtDataVisualization',
        'PySide6.QtSensors', 'PySide6.QtSerialPort', 'PySide6.QtWebChannel',
        'PySide6.QtWebEngine', 'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets', 'PySide6.QtWebSockets',
        'PySide6.QtBluetooth', 'PySide6.QtNfc',
        'PySide6.QtPrintSupport', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
        'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic', 'PySide6.Qt3DAnimation', 'PySide6.Qt3DExtras',
        'PySide6.QtSvg', 'PySide6.QtSvgWidgets',
        'PySide6.QtConcurrent', 'PySide6.QtRemoteObjects',
        'PySide6.QtScxml', 'PySide6.QtStateMachine',
        'PySide6.QtTextToSpeech', 'PySide6.QtUiTools',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ファーキャットファーキャット 体験版',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ファーキャットファーキャット 体験版',
)
