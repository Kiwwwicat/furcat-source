"""털캣털캣 — desktop pet that you can pet to scatter fur particles.

Single-file PySide6 app. Run with `python main.py` or build a one-file exe with
`pyinstaller 털캣털캣.spec`.
"""

import sys
import os
import copy
import json
import math
import random
import time

from PySide6.QtCore import (
    Qt, QTimer, QPoint, QPointF, QRect, QRectF, QSize, Signal, QEvent
)
from PySide6.QtGui import (
    QPainter, QPixmap, QImage, QColor, QPen, QBrush, QPainterPath, QFont,
    QFontDatabase, QIcon, QRegion, QBitmap, QGuiApplication, QPolygonF, QCursor,
    QFontMetrics
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QPlainTextEdit, QCheckBox, QRadioButton,
    QButtonGroup, QColorDialog, QGroupBox, QSlider, QSystemTrayIcon, QMenu,
    QFrame, QSizePolicy, QDialog, QFileDialog, QMessageBox, QComboBox,
    QScrollArea
)
import shutil


# 1.png 머리카락 sage 톤(#609090) 기반 파스텔 팔레트
PALETTE = {
    'primary':      '#7BAFA0',  # 메인 sage
    'primary_dark': '#5B8B7B',  # 진한 sage (제목 텍스트)
    'text':         '#3F6957',  # 본문 텍스트 (deep forest)
    'text_soft':    '#6B8A7E',  # 보조 텍스트
    'bg':           '#FAFCFB',  # 패널 배경 (거의 흰색에 sage hint)
    'bg_soft':      '#F0F7F3',  # 그룹 배경
    'bg_hover':     '#E2EEE7',  # 호버 강조
    'border_light': '#C8DDD2',  # 연한 테두리
    'border':       '#A0C5B6',  # 보통 테두리
    'accent':       '#D9858A',  # 액센트 (캐릭터 넥타이의 dusty rose)
    'fur_default':  '#7BAFA0',  # 새 기본 털 색 (앱 톤에 맞춰 sage)
}

APP_FONT_FAMILY = 'Galmuri11'  # _load_app_font()이 성공하면 이 이름이 등록됨


# 언어 / 번역 ----------------------------------------------------------------
# 사용자가 언어 다이얼로그에서 선택한 언어를 모듈 전역으로 보관해 t() 한 호출로
# 어디서든 번역된 문자열을 받을 수 있게 한다. 기본 KOR. 언어 변경 시 패널/트레이는
# 다시 빌드, 펫 윈도우 타이틀과 컨텍스트 메뉴는 매번 t()로 가져오므로 자동 반영.
APP_LANG_OPTIONS = [
    ('KOR', '한국어'),
    ('JPN', '日本語'),
    ('ENG', 'English'),
]
_CURRENT_LANG = 'KOR'

TR = {
    # 브랜드명: 한국어는 "털캣털캣"(반복형 귀여움). 영어는 사용자 지시로 공백 없이 'FurcatFurcat'.
    # 일본어는 외래어 도-약 + 의성·의태 동음 반복(わんわん/にゃんにゃん 식)을 살려
    # 'ファーキャットファーキャット'(공백 없이) 유지 — 브랜드 정체성을 보존하면서
    # 카타카나 외래어 표기를 따라 자연스러움.
    'app_name':        {'KOR': '털캣털캣', 'JPN': 'ファーキャットファーキャット', 'ENG': 'FurcatFurcat'},
    'pet_window_title': {'KOR': '털캣 #{n}', 'JPN': 'ファーキャット #{n}', 'ENG': 'Furcat #{n}'},
    'panel_title':     {'KOR': '털캣털캣 — 설정', 'JPN': 'ファーキャットファーキャット — 設定', 'ENG': 'FurcatFurcat — Settings'},
    'trial_suffix':    {'KOR': ' (체험판)', 'JPN': ' (体験版)', 'ENG': ' (Trial)'},
    'trial_badge':     {'KOR': '체험판: 1번 캐릭터만 등록 가능',
                        'JPN': '体験版: キャラクター1のみ登録可能',
                        'ENG': 'Trial: only Character 1 is available'},
    'subtitle':        {'KOR': '컴퓨터 화면에 사이버 털 묻히기',
                        'JPN': 'パソコン画面にサイバー毛をくっつけよう',
                        'ENG': 'Stick cyber fur on your screen'},
    'info':            {'KOR': '정보', 'JPN': '情報', 'ENG': 'About'},
    'language':        {'KOR': '언어', 'JPN': '言語', 'ENG': 'Language'},

    'group_chars':     {'KOR': '캐릭터', 'JPN': 'キャラクター', 'ENG': 'Characters'},
    'char_n':          {'KOR': '{n}번 캐릭터', 'JPN': 'キャラクター{n}', 'ENG': 'Character {n}'},
    'edit_image':      {'KOR': '이미지 변경', 'JPN': '画像変更', 'ENG': 'Change Image'},
    'fur_color_label': {'KOR': '털 색', 'JPN': '毛色', 'ENG': 'Fur color'},
    'motion_label':    {'KOR': '움직임', 'JPN': '動き', 'ENG': 'Motion'},
    'motion_jump':     {'KOR': '띠용띠용', 'JPN': 'ぴょんぴょん', 'ENG': 'Bouncy'},
    'motion_sway':     {'KOR': '까딱까딱', 'JPN': 'ゆらゆら', 'ENG': 'Sway'},
    'motion_none':     {'KOR': '정지', 'JPN': '停止', 'ENG': 'Still'},

    'group_dialog':    {'KOR': '대사', 'JPN': 'セリフ', 'ENG': 'Dialog'},
    'dialog_hint':     {'KOR': '엔터로 구분. 캐릭터별로 다르게. 쓰다듬을 때 그중 하나가 랜덤으로 뜹니다.',
                        'JPN': 'Enterで区切る。キャラごとに別。なでた時にランダムで一つ表示。',
                        'ENG': 'One per line. Per character. A random one shows when petted.'},
    'dialog_n':        {'KOR': '{n}번', 'JPN': '#{n}', 'ENG': '#{n}'},
    'dialog_placeholder': {'KOR': '쓰담쓰담~\n문질문질~\n(비울 시 대사 표시하지 않음)',
                           'JPN': 'なでなで~\nもふもふ~\n(空欄ならセリフ非表示)',
                           'ENG': 'pet pet~\nrub rub~\n(leave empty to hide)'},

    'group_fur':       {'KOR': '털', 'JPN': '毛', 'ENG': 'Fur'},
    'fur_action':      {'KOR': '동작', 'JPN': '動作', 'ENG': 'Behavior'},
    'fur_keep':        {'KOR': '남기기', 'JPN': '残す', 'ENG': 'Keep'},
    'fur_fade':        {'KOR': '사라지기', 'JPN': '消える', 'ENG': 'Fade'},

    'group_layer':     {'KOR': 'PNG 위치', 'JPN': 'PNGの位置', 'ENG': 'PNG layer'},
    'layer_top':       {'KOR': '최상단 (모든 창 위)', 'JPN': '最前面（すべてのウィンドウの上）',
                        'ENG': 'Top (above all windows)'},
    'layer_bottom':    {'KOR': '배경화면 위 (다른 창 아래)', 'JPN': '背景の上（他のウィンドウの下）',
                        'ENG': 'Above wallpaper (below windows)'},

    'group_motion':    {'KOR': '동작', 'JPN': '動作', 'ENG': 'Movement'},
    'wander':          {'KOR': '화면을 돌아다니게 하기', 'JPN': '画面を歩き回らせる',
                        'ENG': 'Wander around the screen'},

    'help_1': {'KOR': '• 이미지를 클릭하거나 드래그해 쓰다듬을 수 있습니다.',
               'JPN': '• 画像をクリックまたはドラッグでなでられます。',
               'ENG': '• Click or drag the image to pet.'},
    'help_2': {'KOR': '• 우클릭 → 위치 이동 모드로 전환 후 드래그해 옮겨주세요.',
               'JPN': '• 右クリック → 位置移動モードに切り替えてドラッグ。',
               'ENG': '• Right-click → switch to Move mode then drag.'},
    'help_3': {'KOR': '   위치 이동이 끝나면 쓰다듬기 모드로 다시 전환해 주세요.',
               'JPN': '   移動が終わったらなでるモードに戻してください。',
               'ENG': '   Switch back to Pet mode when done.'},
    'help_4': {'KOR': '• 캐릭터 카드의 "이미지 변경" 버튼으로 이미지를 교체할 수 있습니다.',
               'JPN': '• キャラカードの「画像変更」ボタンで画像を入れ替え。',
               'ENG': '• Use the "Change Image" button to replace an image.'},
    'help_img_indent': {'KOR': '이미지를 변경하면 폴더 내의 1, 2, 3 이미지에 덮어쓰기됩니다.',
                        'JPN': '画像を変更するとフォルダー内の1, 2, 3画像に上書きされます。',
                        'ENG': 'Replacing the image overwrites 1.png / 2.png / 3.png.'},
    'help_tray': {'KOR': '• 설정 창을 닫아도 트레이에서 계속 실행됩니다.',
                  'JPN': '• 設定ウィンドウを閉じてもトレイで動作し続けます。',
                  'ENG': '• Closing this window keeps the app running in the tray.'},
    'help_tray_indent': {'KOR': '완전히 종료하려면 트레이 아이콘을 우클릭하고 "종료"를 눌러주세요.',
                          'JPN': '完全に終了するにはトレイアイコンを右クリックして「終了」を選んでください。',
                          'ENG': 'To fully quit, right-click the tray icon and choose "Quit".'},

    'btn_clear_fur':   {'KOR': '떨어진 털 모두 정리', 'JPN': '落ちた毛を全部片付ける',
                        'ENG': 'Clear all fallen fur'},
    'btn_quit':        {'KOR': '앱 종료', 'JPN': 'アプリ終了', 'ENG': 'Quit App'},

    # 우클릭 컨텍스트 메뉴
    'ctx_unlock':      {'KOR': '위치 이동 모드', 'JPN': '位置移動モード', 'ENG': 'Move Mode'},
    'ctx_lock':        {'KOR': '쓰다듬기 모드', 'JPN': 'なでるモード', 'ENG': 'Pet Mode'},
    'ctx_clear_fur':   {'KOR': '털 정리', 'JPN': '毛を片付ける', 'ENG': 'Clear fur'},
    'ctx_settings':    {'KOR': '설정 열기', 'JPN': '設定を開く', 'ENG': 'Open Settings'},
    'ctx_hide':        {'KOR': '이 캐릭터 숨기기', 'JPN': 'このキャラを隠す', 'ENG': 'Hide this character'},
    'ctx_quit':        {'KOR': '앱 종료', 'JPN': 'アプリ終了', 'ENG': 'Quit App'},

    # 트레이 메뉴
    'tray_open_settings': {'KOR': '설정 열기', 'JPN': '設定を開く', 'ENG': 'Open Settings'},
    'tray_clear_fur': {'KOR': '떨어진 털 모두 정리', 'JPN': '落ちた毛を全部片付ける',
                       'ENG': 'Clear all fallen fur'},
    'tray_about':      {'KOR': '정보', 'JPN': '情報', 'ENG': 'About'},
    'tray_language':   {'KOR': '언어', 'JPN': '言語', 'ENG': 'Language'},
    'tray_quit':       {'KOR': '종료', 'JPN': '終了', 'ENG': 'Quit'},

    # 파일 다이얼로그·알림
    'fd_select_char_image': {'KOR': '{n}번 캐릭터 이미지 선택',
                              'JPN': 'キャラクター{n}の画像を選択',
                              'ENG': 'Select image for character {n}'},
    'fd_image_filter': {'KOR': '이미지 파일 (*.png *.jpg *.jpeg *.bmp *.webp *.gif);;모든 파일 (*.*)',
                         'JPN': '画像ファイル (*.png *.jpg *.jpeg *.bmp *.webp *.gif);;すべてのファイル (*.*)',
                         'ENG': 'Image files (*.png *.jpg *.jpeg *.bmp *.webp *.gif);;All files (*.*)'},
    'msg_image_error_title': {'KOR': '이미지 오류', 'JPN': '画像エラー', 'ENG': 'Image Error'},
    'msg_image_error_body':  {'KOR': '선택한 파일을 이미지로 열 수 없습니다.',
                              'JPN': '選択したファイルを画像として開けません。',
                              'ENG': 'Cannot open the selected file as an image.'},
    'msg_save_failed_title': {'KOR': '저장 실패', 'JPN': '保存失敗', 'ENG': 'Save Failed'},
    'msg_save_failed_body':  {'KOR': '이미지를 저장할 수 없습니다:\n{e}',
                              'JPN': '画像を保存できません:\n{e}',
                              'ENG': 'Cannot save image:\n{e}'},
    'thumb_none':      {'KOR': '(없음)', 'JPN': '(なし)', 'ENG': '(none)'},

    # 색상 다이얼로그
    'color_dialog_title': {'KOR': '털 색상 선택', 'JPN': '毛色を選択', 'ENG': 'Pick Fur Color'},
    'trial_color_hint': {'KOR': '체험판은 20색만 선택할 수 있습니다.\n정식판에서는 자유롭게 색상을 선택할 수 있습니다!',
                          'JPN': '体験版は20色のみ選択できます。\n製品版では自由に色を選べます！',
                          'ENG': 'Trial: only 20 colors. Pick any color in the full version!'},

    # 크레딧
    'credits_made_by': {'KOR': 'made by 키위캣(@kiwwwicat)',
                        'JPN': 'made by キウィキャット(@kiwwwicat)',
                        'ENG': 'made by KiwiCat (@kiwwwicat)'},
    'credits_ai':      {'KOR': '이 프로그램은 AI의 도움을 받아 제작되었습니다.',
                        'JPN': 'このプログラムはAIの助けを借りて制作されました。',
                        'ENG': 'This program was made with help from AI.'},
    'credits_fonts':   {'KOR': '사용 폰트', 'JPN': '使用フォント', 'ENG': 'Fonts used'},

    # 언어 다이얼로그
    'lang_dialog_title': {'KOR': '언어 선택', 'JPN': '言語選択', 'ENG': 'Language'},
    'lang_kor':        {'KOR': '한국어 (KOR)', 'JPN': '韓国語 (KOR)', 'ENG': 'Korean (KOR)'},
    'lang_jpn':        {'KOR': '일본어 (JPN)', 'JPN': '日本語 (JPN)', 'ENG': 'Japanese (JPN)'},
    'lang_eng':        {'KOR': '영어 (ENG)', 'JPN': '英語 (ENG)', 'ENG': 'English (ENG)'},
    'ok':              {'KOR': '확인', 'JPN': 'OK', 'ENG': 'OK'},
    'cancel':          {'KOR': '취소', 'JPN': 'キャンセル', 'ENG': 'Cancel'},
}


def t(key, **kwargs):
    """현재 언어로 키 번역. 누락 시 KOR 폴백, 그것도 없으면 키 그대로."""
    entry = TR.get(key, {})
    s = entry.get(_CURRENT_LANG) or entry.get('KOR') or key
    if kwargs:
        try:
            s = s.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return s


def set_lang(lang):
    global _CURRENT_LANG
    if lang in ('KOR', 'JPN', 'ENG'):
        _CURRENT_LANG = lang
    else:
        _CURRENT_LANG = 'KOR'


def current_lang():
    return _CURRENT_LANG


def _load_app_font():
    """Galmuri11 아웃라인 변형 등록 (1순위). 시스템 폰트로 폴백."""
    global APP_FONT_FAMILY
    candidates = [
        os.path.join(EXTERNAL_DIR, 'Galmuri11.ttf'),
        os.path.join(BASE_DIR, 'Galmuri11.ttf'),
    ]
    bold_candidates = [
        os.path.join(EXTERNAL_DIR, 'Galmuri11-Bold.ttf'),
        os.path.join(BASE_DIR, 'Galmuri11-Bold.ttf'),
    ]
    family = None
    for p in candidates:
        if os.path.exists(p):
            fid = QFontDatabase.addApplicationFont(p)
            if fid >= 0:
                fams = QFontDatabase.applicationFontFamilies(fid)
                if fams:
                    family = fams[0]
            break
    for p in bold_candidates:
        if os.path.exists(p):
            QFontDatabase.addApplicationFont(p)
            break
    if family:
        APP_FONT_FAMILY = family
    return APP_FONT_FAMILY


if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    EXTERNAL_DIR = os.path.dirname(sys.executable)
    # PyInstaller windowed 모드에서 stdout/stderr가 None이라
    # 라이브러리/Qt 로그가 print하는 순간 AttributeError로 크래시함.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w', encoding='utf-8')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w', encoding='utf-8')
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXTERNAL_DIR = BASE_DIR

# 체험판 모드: 빌드 시점에 spec이 'TRIAL.flag'을 datas로 동봉하면 ON.
# 정식판 빌드는 이 파일이 없으므로 항상 OFF. 체험판은 캐릭터 1명만 등록 가능.
# PyInstaller 버전/모드에 따라 sys._MEIPASS와 exe 옆 위치 둘 다 가능성이 있어
# 양쪽 모두 검사한다.
TRIAL_MODE = (
    os.path.exists(os.path.join(BASE_DIR, 'TRIAL.flag'))
    or os.path.exists(os.path.join(EXTERNAL_DIR, 'TRIAL.flag'))
)
TRIAL_MAX_CHARS = 1

# 정식판/체험판 동일 디렉터리 사용 — 사용자 요청. 체험판은 디스크 쓰기 시
# 슬롯 2/3 데이터를 디스크 기존 값에서 보존(_trial_merge_for_save)해서
# 정식판이 저장한 슬롯 2/3 설정이 체험판 실행으로 망가지지 않게 한다.
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.furcat')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

_DEFAULT_DIALOG_LINES = ['쓰담쓰담~', '문질문질~']

DEFAULT_CONFIG = {
    'enabled': [True, False, False],
    'positions': [[300, 300], [500, 300], [700, 300]],
    'scale': 100,
    'scales': [100, 100, 100],  # 캐릭터별 개별 크기 (%)
    'dialogs_per_char': [
        list(_DEFAULT_DIALOG_LINES),
        list(_DEFAULT_DIALOG_LINES),
        list(_DEFAULT_DIALOG_LINES),
    ],
    'fur_color': '#7BAFA0',
    'fur_colors': ['#7BAFA0', '#D9858A', '#E8C580'],
    'fur_persistent': False,
    'idle_motion': 'jump',  # legacy 단일값 (마이그레이션용)
    'idle_motions': ['jump', 'jump', 'jump'],  # 캐릭터별
    'wander': False,
    'layer': 'top',  # 'top' (창 최상단) | 'bottom' (배경화면 위, 창 아래)
    'language': 'KOR',  # KOR / JPN / ENG
}


def _migrate_config(cfg):
    """이전 버전 키(`dialog` 단수, `dialogs` 공유, `scale` 단일값)를 새 구조로 옮긴다."""
    # dialogs_per_char (캐릭터별 대사 풀)
    if 'dialogs_per_char' not in cfg or not isinstance(cfg.get('dialogs_per_char'), list):
        legacy = cfg.get('dialogs')
        old_singular = cfg.get('dialog')
        if isinstance(legacy, list) and legacy:
            base = [s for s in legacy if isinstance(s, str) and s.strip()]
        elif isinstance(old_singular, str) and old_singular.strip():
            base = [old_singular.strip()]
        else:
            base = list(_DEFAULT_DIALOG_LINES)
        cfg['dialogs_per_char'] = [list(base), list(base), list(base)]
    while len(cfg['dialogs_per_char']) < 3:
        cfg['dialogs_per_char'].append(list(_DEFAULT_DIALOG_LINES))
    for i in range(3):
        slot = cfg['dialogs_per_char'][i]
        if not isinstance(slot, list):
            cfg['dialogs_per_char'][i] = list(_DEFAULT_DIALOG_LINES)
        else:
            cfg['dialogs_per_char'][i] = [s for s in slot if isinstance(s, str) and s.strip()]
    cfg.pop('dialog', None)
    cfg.pop('dialogs', None)
    if 'scales' not in cfg or not isinstance(cfg.get('scales'), list):
        base = int(cfg.get('scale', 100))
        cfg['scales'] = [base, base, base]
    while len(cfg['scales']) < 3:
        cfg['scales'].append(100)
    if 'fur_colors' not in cfg or not isinstance(cfg.get('fur_colors'), list):
        base = cfg.get('fur_color', '#7BAFA0')
        cfg['fur_colors'] = [base, base, base]
    while len(cfg['fur_colors']) < 3:
        cfg['fur_colors'].append('#7BAFA0')
    if 'idle_motions' not in cfg or not isinstance(cfg.get('idle_motions'), list):
        base = cfg.get('idle_motion', 'jump')
        cfg['idle_motions'] = [base, base, base]
    while len(cfg['idle_motions']) < 3:
        cfg['idle_motions'].append('jump')
    if TRIAL_MODE:
        _enforce_trial_limits(cfg)
    return cfg


def _enforce_trial_limits(cfg):
    """체험판: enabled 슬롯을 앞 TRIAL_MAX_CHARS개만 허용. 나머지는 강제 False."""
    enabled = list(cfg.get('enabled') or [])
    while len(enabled) < 3:
        enabled.append(False)
    for i in range(len(enabled)):
        if i >= TRIAL_MAX_CHARS:
            enabled[i] = False
    if not any(enabled[:TRIAL_MAX_CHARS]):
        enabled[0] = True
    cfg['enabled'] = enabled[:3]


def _panel_title():
    """패널/타이틀에 체험판 접미사 자동 부착."""
    return t('panel_title') + (t('trial_suffix') if TRIAL_MODE else '')


def _app_name_with_suffix():
    return t('app_name') + (t('trial_suffix') if TRIAL_MODE else '')


def get_png_path(n):
    """1/2/3.png — 사용자가 exe 옆에 둔 파일을 우선, 없으면 번들된 것."""
    p1 = os.path.join(EXTERNAL_DIR, f'{n}.png')
    if os.path.exists(p1):
        return p1
    return os.path.join(BASE_DIR, f'{n}.png')


def get_app_icon():
    """앱 아이콘. app_icon.ico (다해상도) 우선, 없으면 3.png 폴백."""
    for path in (
        os.path.join(EXTERNAL_DIR, 'app_icon.ico'),
        os.path.join(BASE_DIR, 'app_icon.ico'),
    ):
        if os.path.exists(path):
            return QIcon(path)
    return QIcon(get_png_path(3))


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = copy.deepcopy(v)
            cfg = _migrate_config(cfg)
            set_lang(cfg.get('language', 'KOR'))
            return cfg
        except Exception:
            pass
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    set_lang(cfg.get('language', 'KOR'))
    return cfg


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    out = _trial_merge_for_save(cfg) if TRIAL_MODE else cfg
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)


def _trial_merge_for_save(cfg):
    """체험판은 슬롯 1만 책임진다. 디스크의 기존 슬롯 2/3 값을 보존해서
    정식판이 저장한 enabled/scales/fur_colors/idle_motions/positions/dialogs_per_char의
    [1]/[2] 인덱스 데이터가 체험판 실행으로 사라지지 않게 한다."""
    if not os.path.exists(CONFIG_FILE):
        return cfg
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            disk = json.load(f)
    except Exception:
        return cfg
    out = copy.deepcopy(cfg)
    keys = ('enabled', 'scales', 'fur_colors', 'idle_motions', 'positions', 'dialogs_per_char')
    for key in keys:
        disk_v = disk.get(key)
        cur_v = out.get(key)
        if not isinstance(disk_v, list) or not isinstance(cur_v, list):
            continue
        while len(cur_v) < 3:
            cur_v.append(None)
        for i in (1, 2):
            if i < len(disk_v):
                cur_v[i] = copy.deepcopy(disk_v[i])
        out[key] = cur_v
    return out


# --------------------------------------------------------------------------
# 말풍선 색
# --------------------------------------------------------------------------
def bubble_colors_from_fur(fur_hex):
    """캐릭터 털 색 → 말풍선 (배경, 테두리, 텍스트) QColor 3종.

    원칙:
    - 배경은 기존(v1.0.0)처럼 거의 흰색 톤으로 밝게 유지하되 hue만 fur에 맞춰 살짝 틴트
    - 테두리·텍스트는 fur 색을 진하게 끌어와 캐릭터별 통일감 + 가독성
    - 사용자가 아주 연한 fur를 골라도 테두리·텍스트는 어느 정도 진하기를 유지
    - 무채색(흰/회/검) fur는 hue가 의미 없으므로 중성 그레이 톤으로 폴백
    """
    fur = QColor(fur_hex) if fur_hex else QColor(PALETTE['fur_default'])
    if not fur.isValid():
        fur = QColor(PALETTE['fur_default'])
    h, s, l, _ = fur.getHslF()
    if h < 0:
        h = 0.0

    if s < 0.05:
        # 무채색 fur: hue 강제 시 핑크빛이 도므로 중성 톤으로
        return (QColor(250, 252, 251), QColor(140, 152, 146), QColor(48, 58, 54))

    # 배경: 매우 밝게(거의 흰색) + fur hue 살짝만
    bg_l = 0.97
    bg_s = min(s * 0.35, 0.22)
    # 테두리: fur보다 살짝 진하게 — 연한 fur도 연한 흰바탕 위에서 보이도록 하한
    border_l = max(0.40, min(l - 0.10, 0.62))
    border_s = max(0.40, min(s + 0.15, 0.70))
    # 텍스트: 충분히 진하게 — 연한 fur도 흰 배경에서 또렷하게
    text_l = max(0.18, min(l - 0.40, 0.32))
    text_s = max(0.45, min(s + 0.20, 0.80))
    return (QColor.fromHslF(h, bg_s, bg_l),
            QColor.fromHslF(h, border_s, border_l),
            QColor.fromHslF(h, text_s, text_l))


# --------------------------------------------------------------------------
# 털 입자
# --------------------------------------------------------------------------
class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'rotation', 'angular_velocity',
                 'color', 'length', 'width', 'age', 'max_age', 'persistent',
                 'settled', 'radius', '_qcolor', '_path')

    def __init__(self, x, y, color, persistent=False, burst_strength=1.0):
        self.x = x
        self.y = y
        # 화면을 향해 랜덤 방향으로 등속 비행 (중력 없음, 살짝 감속)
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(4.0, 9.0) * burst_strength
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.rotation = random.uniform(0, 360)
        self.angular_velocity = random.uniform(-10, 10)
        self.color = color
        self.length = random.uniform(8, 16)
        self.width = random.uniform(2.0, 3.5)
        self.age = 0
        self.max_age = random.randint(160, 240)
        self.persistent = persistent
        self.settled = False
        # 회전·곡선·펜 두께를 모두 덮는 반경 (dirty rect 계산용)
        self.radius = self.length * 0.6 + self.width + 2
        # 모양은 생성 후 불변이라 색/경로를 한 번만 만든다 (매 프레임 생성 비용 제거)
        self._qcolor = QColor(color)
        half = self.length / 2
        self._path = QPainterPath()
        self._path.moveTo(-half, 0)
        self._path.quadTo(0, -self.length * 0.28, half, 0)

    def is_changing(self):
        """이번 프레임에 화면상 모습이 바뀌는지 (이동 중 또는 페이드 중)."""
        if not self.settled:
            return True
        return not self.persistent and self.age > self.max_age * 0.6

    def update(self, ground_y, world_w, world_h, dt=1.0):
        # dt: 60fps(16.7ms) 1프레임 = 1.0. 프레임이 밀려도 실제 경과 시간만큼
        # 진행시켜 큰 모니터/고부하에서 털이 느려지지 않게 한다.
        if self.settled:
            # settle 후에도 age는 계속 증가시켜 fade out + max_age 사망 보장.
            # (예전에는 즉시 return True라 비-persistent 입자가 영원히 화면에 박혀
            #  alpha()도 멈추고 1500개 cap에 의해 갑자기 잘려나가는 시각 이슈 있었음)
            self.age += dt
            if not self.persistent and self.age > self.max_age:
                return False
            return True
        # 직선 비행 + 점진 감속 (중력 X)
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.angular_velocity * dt
        decay = 0.965 ** dt
        self.vx *= decay
        self.vy *= decay
        self.angular_velocity *= 0.94 ** dt

        # 감속으로 거의 멈추면 그 자리에 그대로 부착
        if abs(self.vx) < 0.35 and abs(self.vy) < 0.35:
            self.vx = 0
            self.vy = 0
            self.angular_velocity = 0
            self.settled = True

        # 화면 밖으로 새어 나가면 가장자리에 클램프해서 부착
        margin = 4
        if self.x <= margin:
            self.x = margin
            self.settled = True
        elif self.x >= world_w - margin:
            self.x = world_w - margin
            self.settled = True
        if self.y <= margin:
            self.y = margin
            self.settled = True
        elif self.y >= world_h - margin:
            self.y = world_h - margin
            self.settled = True
        if self.settled:
            self.vx = 0
            self.vy = 0
            self.angular_velocity = 0

        self.age += dt
        if not self.persistent and self.age > self.max_age:
            return False
        return True

    def alpha(self):
        if self.persistent:
            return 1.0
        fade_start = self.max_age * 0.6
        if self.age > fade_start:
            return max(0.0, 1.0 - (self.age - fade_start) / (self.max_age - fade_start))
        return 1.0

    def draw(self, painter):
        c = self._qcolor
        c.setAlphaF(self.alpha())
        pen = QPen(c, self.width, Qt.SolidLine, Qt.RoundCap)
        painter.save()
        painter.translate(self.x, self.y)
        painter.rotate(self.rotation)
        painter.setPen(pen)
        painter.drawPath(self._path)
        painter.restore()


# --------------------------------------------------------------------------
# Pet overlay
# --------------------------------------------------------------------------
class FXOverlay(QWidget):
    """단일 펫의 털 입자 + 대사를 그리는 한 화면 click-through 오버레이.
    멀티 모니터+DPI 불일치 환경에서 단일 창이 두 화면을 덮으면 보조 모니터 쪽
    좌표가 어긋나는 Qt6 한계가 있어, 펫 1마리당 1개 FX를 두고 그 펫이 현재
    있는 화면 1개만 덮는다(`set_screen`). 펫이 다른 화면으로 이동하면 FX도
    따라가며 기존 입자는 글로벌 위치를 보존한 채 새 origin으로 재변환된다.
    WA_TransparentForMouseEvents로 모든 마우스 이벤트는 아래로 통과."""

    def __init__(self, initial_screen=None):
        super().__init__(None)
        # WA_TranslucentBackground는 네이티브 HWND 생성 전에 켜야
        # Windows에서 WS_EX_LAYERED가 적용되어 투명 합성이 동작한다.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        self.particles = []
        self.dialogs = {}  # pet_index -> {'text', 'cx', 'top_y', 'expire_at'}

        # WindowStaysOnTopHint를 layer에 따라 동적으로 박는다. SetWindowPos만
        # 의존했더니 PySide6/Qt 환경에서 다른 일반 창이 위로 올라오는 race가 있음.
        # 'top' 모드에서는 WindowStaysOnTopHint로 OS에 명시적으로 TopMost 그룹을
        # 알려주는 게 가장 확실. layer 토글은 setWindowFlags 재적용으로 처리하고
        # 입자/대사는 self.particles/self.dialogs에 보관돼 윈도우 재시각화에도 보존.
        self._layer = 'top'
        self._apply_window_flags(self._layer)

        # 펫이 현재 위치한 단일 화면만 덮는다. 처음에는 initial_screen 또는
        # primary로 시작하고, 펫이 화면을 옮기면 set_screen으로 따라간다.
        self._origin = QPoint(0, 0)
        self._current_screen = initial_screen or QGuiApplication.primaryScreen()
        self._apply_screen_geometry()
        self._apply_taskbar_hide()
        self._apply_layer(self._layer)

        # 화면 자체가 OS 설정에서 변경되는 케이스(해상도/배치 변경)에 한해 재적용.
        # 화면 추가/제거는 set_screen 호출자가 책임지므로 여기서 union은 안 만든다.
        gapp = QGuiApplication.instance()
        gapp.screenRemoved.connect(self._on_screen_removed)
        for sc in QGuiApplication.screens():
            sc.geometryChanged.connect(self._on_screen_geometry_changed)

        # 큰 모니터(32"/4K)에서 풀스크린 투명 창 전체를 60Hz로 다시 그리면
        # 프레임이 밀려 털이 느려지고 PC 전체가 버벅인다. 바뀐 영역만 다시 그리고
        # (_tick의 dirty rect), 바뀐 게 없으면 아예 그리지 않는다.
        self._last_tick = time.perf_counter()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

        # z-order heartbeat: 다른 TopMost 창(브라우저 PIP, 일부 비디오 플레이어 등)이
        # 나중에 TopMost로 등록되어 FX를 가리는 케이스 방어. click-through 투명창이라
        # SetWindowPos 재호출이 시각적으로 보이지 않아 깜빡임 X.
        self._z_timer = QTimer(self)
        self._z_timer.timeout.connect(self._reapply_layer)
        self._z_timer.start(1000)

    def _apply_window_flags(self, layer):
        """layer에 따라 windowFlags 재계산.
        'top'이면 Qt.WindowStaysOnTopHint를 박아 OS에 TopMost 그룹임을 명시.
        'bottom'이면 빼고 SetWindowPos(HWND_BOTTOM)으로 강등."""
        flags = (Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus
                 | Qt.NoDropShadowWindowHint | Qt.WindowTransparentForInput)
        if layer == 'top':
            flags |= Qt.WindowStaysOnTopHint
        was_visible = self.isVisible()
        self.setWindowFlags(flags)
        # setWindowFlags는 윈도우를 hide할 수 있어 attribute/show 재적용
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        if was_visible:
            self.show()

    def set_layer(self, layer):
        """펫의 layer를 따라간다 ('top' | 'bottom')."""
        if layer not in ('top', 'bottom'):
            layer = 'top'
        flags_changed = (layer != self._layer)
        self._layer = layer
        if flags_changed:
            self._apply_window_flags(layer)
            self._apply_taskbar_hide()
        self._apply_layer(layer)
        # show 직후 Qt가 z-order를 다시 잡는 race를 피하려고 다음 이벤트 사이클에서도 한 번 더
        QTimer.singleShot(50, self._reapply_layer)
        QTimer.singleShot(200, self._reapply_layer)

    def _reapply_layer(self):
        self._apply_layer(self._layer)

    def showEvent(self, event):
        # native window가 확실히 visible 상태가 됐을 때 z-order 강제.
        super().showEvent(event)
        self._apply_layer(getattr(self, '_layer', 'top'))

    def _apply_layer(self, layer):
        """Win32 SetWindowPos로 z-order만 강제. WindowStaysOnTopHint는 안 박음."""
        if sys.platform != 'win32':
            if layer == 'bottom':
                self.lower()
            else:
                self.raise_()
            return
        try:
            import ctypes
            hwnd = int(self.winId())
            if not hwnd:
                return
            u32 = ctypes.windll.user32
            HWND_TOPMOST = -1
            HWND_NOTOPMOST = -2
            HWND_BOTTOM = 1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            f = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
            if layer == 'bottom':
                u32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, f)
                u32.SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0, f)
            else:
                u32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, f)
                u32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, f)
        except Exception as e:
            _diag(f'fx _apply_layer failed: {e}')

    def _apply_screen_geometry(self):
        """`self._current_screen` 한 화면만 덮도록 윈도우를 리사이즈하고 origin을 갱신.
        origin이 바뀌면 기존 입자/대사 좌표도 같이 이동시켜 시각적 점프 방지."""
        scr = self._current_screen
        if scr is None:
            scr = QGuiApplication.primaryScreen()
        if scr is None:
            return
        rect = scr.geometry()
        # 모니터와 정확히 같은 크기 + topmost면 Windows가 '전체화면 앱'으로 오판해
        # 집중 지원(Focus Assist)을 자동 발동 → 디스코드 등 토스트 알림이 차단된다.
        # 높이를 1px 줄여 전체화면 판정을 회피 (효과 레이어엔 영향 없음).
        rect.setHeight(rect.height() - 1)
        new_origin = rect.topLeft()
        if self._origin != new_origin:
            dx = self._origin.x() - new_origin.x()
            dy = self._origin.y() - new_origin.y()
            for p in self.particles:
                p.x += dx
                p.y += dy
            for d in self.dialogs.values():
                d['cx'] += dx
                d['top_y'] += dy
                d.pop('_rect', None)
        self._origin = new_origin
        self.setGeometry(rect)
        self.update()
        # geometry 변경이 z-order에 영향을 줄 수 있으므로 layer 재적용
        # (단 __init__의 첫 호출 시점에는 _layer가 아직 정의 전일 수 있음 → getattr)
        if getattr(self, '_layer', None) is not None:
            self._apply_layer(self._layer)

    def set_screen(self, screen):
        """펫이 다른 화면으로 이동했을 때 호출. FX가 새 화면을 덮도록 재배치하고
        기존 입자/대사의 글로벌 위치를 보존한다."""
        if screen is None or screen is self._current_screen:
            return
        try:
            screen.geometryChanged.connect(self._on_screen_geometry_changed)
        except Exception:
            pass
        self._current_screen = screen
        self._apply_screen_geometry()

    def _on_screen_removed(self, screen):
        # 현재 따라가는 화면이 사라졌으면 primary로 폴백.
        if screen is self._current_screen:
            self._current_screen = QGuiApplication.primaryScreen()
            self._apply_screen_geometry()

    def _on_screen_geometry_changed(self, _rect):
        # 현재 화면의 해상도/위치가 OS에서 바뀐 경우만 재적용.
        if self._current_screen is not None:
            self._apply_screen_geometry()

    def _apply_taskbar_hide(self):
        if sys.platform != 'win32':
            return
        try:
            import ctypes
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_NOACTIVATE = 0x08000000
            WS_EX_TRANSPARENT = 0x00000020
            user32 = ctypes.windll.user32
            ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ex |= WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_TRANSPARENT
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex)
        except Exception as e:
            _diag(f'fx taskbar hide failed: {e}')

    def add_particles(self, n, x, y, color, persistent, burst=1.0, spread=20):
        # x, y는 글로벌 좌표. 위젯 로컬로 변환해서 저장 (멀티모니터 대응).
        lx = x - self._origin.x()
        ly = y - self._origin.y()
        for _ in range(n):
            ox = lx + random.uniform(-spread, spread)
            oy = ly + random.uniform(-spread, spread)
            self.particles.append(Particle(ox, oy, color, persistent, burst))

    def show_dialog(self, pet_index, text, cx, top_y, fur_color=None, ms=2200):
        old = self.dialogs.get(pet_index)
        if old is not None and old.get('_rect') is not None:
            # 같은 펫의 이전 말풍선 자리를 지우도록 영역 갱신
            self.update(old['_rect'])
        self.dialogs[pet_index] = {
            'text': text,
            'cx': cx - self._origin.x(),
            'top_y': top_y - self._origin.y(),
            'fur_color': fur_color,
            'expire_at': time.time() + ms / 1000.0,
        }

    def update_dialog_anchor(self, pet_index, cx, top_y):
        d = self.dialogs.get(pet_index)
        if d:
            d['cx'] = cx - self._origin.x()
            d['top_y'] = top_y - self._origin.y()

    def clear_all(self):
        self.particles = []
        self.update()

    def _tick(self):
        now_pc = time.perf_counter()
        # 60fps 1프레임 = 1.0. 절전 복귀 등 긴 공백 뒤 순간이동 방지로 상한 4프레임.
        dt = max(0.25, min(4.0, (now_pc - self._last_tick) * 60.0))
        self._last_tick = now_pc

        w, h = self.width(), self.height()
        ground_y = h - 4
        # 이번 프레임에 모습이 바뀌는 입자의 이동 전/후 위치를 덮는 bounding box
        x0 = y0 = float('inf')
        x1 = y1 = float('-inf')
        alive = []
        for p in self.particles:
            changing = p.is_changing()
            if changing:
                r = p.radius
                if p.x - r < x0: x0 = p.x - r
                if p.x + r > x1: x1 = p.x + r
                if p.y - r < y0: y0 = p.y - r
                if p.y + r > y1: y1 = p.y + r
            if p.update(ground_y, w, h, dt):
                alive.append(p)
                # 이번 프레임에 페이드가 막 시작된 입자도 포함
                if changing or p.is_changing():
                    r = p.radius
                    if p.x - r < x0: x0 = p.x - r
                    if p.x + r > x1: x1 = p.x + r
                    if p.y - r < y0: y0 = p.y - r
                    if p.y + r > y1: y1 = p.y + r
        if len(alive) > 1500:
            # cap으로 잘려나가는 입자 자리도 지워야 하니 전체 갱신
            alive = alive[-1500:]
            x0, y0, x1, y1 = 0, 0, w, h
        self.particles = alive

        dirty = QRect()
        if x1 >= x0:
            dirty = QRect(int(x0) - 1, int(y0) - 1,
                          int(x1 - x0) + 3, int(y1 - y0) + 3)

        # 대사: 직전에 그린 자리 + 이번에 그릴 자리 (펫 점프에 따라 움직임)
        now = time.time()
        for k in list(self.dialogs):
            d = self.dialogs[k]
            prev = d.get('_rect')
            if prev is not None:
                dirty = dirty.united(prev)
            if d['expire_at'] < now:
                del self.dialogs[k]
                continue
            cur = self._dialog_rect(d['text'], d['cx'], d['top_y'])
            d['_rect'] = cur
            dirty = dirty.united(cur)

        if not dirty.isEmpty():
            self.update(dirty)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 다시 그리는 영역 밖 입자는 건너뛴다 (Python 루프 비용 절감)
        er = event.rect()
        ex0, ey0, ex1, ey1 = er.left(), er.top(), er.right() + 1, er.bottom() + 1
        settled_list = []
        moving_list = []
        for p in self.particles:
            r = p.radius
            if p.x + r < ex0 or p.x - r > ex1 or p.y + r < ey0 or p.y - r > ey1:
                continue
            (settled_list if p.settled else moving_list).append(p)
        for p in settled_list:
            p.draw(painter)
        for p in moving_list:
            p.draw(painter)

        for d in self.dialogs.values():
            self._draw_dialog(painter, d['text'], d['cx'], d['top_y'],
                              d.get('fur_color'))

    def _dialog_font(self):
        font = QFont(APP_FONT_FAMILY)
        font.setPixelSize(11)
        font.setBold(False)
        font.setStyleStrategy(QFont.PreferAntialias | QFont.PreferQuality)
        font.setHintingPreference(QFont.PreferDefaultHinting)
        return font

    def _dialog_rect(self, text, cx, top_y):
        """말풍선(꼬리·테두리 포함)이 차지하는 영역. _draw_dialog와 같은 계산."""
        text_rect = QFontMetrics(self._dialog_font()).boundingRect(text)
        bw = text_rect.width() + 28
        bh = text_rect.height() + 16
        bx = cx - bw / 2
        by = top_y - bh - 14
        return QRect(int(bx) - 3, int(by) - 3, int(bw) + 7, int(bh) + 8 + 7)

    def _draw_dialog(self, painter, text, cx, top_y, fur_color=None):
        painter.setFont(self._dialog_font())
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        metrics = painter.fontMetrics()
        text_rect = metrics.boundingRect(text)
        pad_x, pad_y = 14, 8
        bw = text_rect.width() + pad_x * 2
        bh = text_rect.height() + pad_y * 2
        bx = cx - bw / 2
        by = top_y - bh - 14

        # 캐릭터 털 색에서 도출한 말풍선 팔레트 (bg/border/text)
        bg_color, border_color, text_color = bubble_colors_from_fur(fur_color)
        bg_color.setAlpha(245)

        painter.setPen(QPen(border_color, 1.4))
        painter.setBrush(QBrush(bg_color))
        path = QPainterPath()
        path.addRoundedRect(QRectF(bx, by, bw, bh), 12, 12)
        tail = QPainterPath()
        tail.moveTo(cx - 7, by + bh - 0.5)
        tail.lineTo(cx, by + bh + 8)
        tail.lineTo(cx + 7, by + bh - 0.5)
        tail.closeSubpath()
        path = path.united(tail)
        painter.drawPath(path)

        painter.setPen(QPen(text_color))
        painter.drawText(QRectF(bx, by, bw, bh), Qt.AlignCenter, text)


class PetOverlay(QWidget):
    """단일 PNG 펫. 윈도우 크기 = PNG 스케일된 크기 (Kiwimage 패턴).
    입자/대사 효과는 FXOverlay에 위임한다."""

    request_show_panel = Signal()
    request_disable_self = Signal(int)
    request_quit = Signal()
    request_clear_all_fur = Signal()

    def __init__(self, index, config):
        super().__init__(None)
        # WA_TranslucentBackground는 네이티브 HWND 생성 전에 켜야
        # Windows에서 WS_EX_LAYERED가 적용된다. _apply_window_flags가
        # 내부적으로 winId()를 호출하므로 그 전에 설정한다.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        self.index = index
        self.config = config
        # 펫별 FX overlay (멀티 모니터 + DPI 불일치 시 단일 풀스크린 FX가 보조
        # 모니터에서 위치 어긋남 발생 → 펫마다 자기 화면용 FX를 둔다).
        # show()는 펫이 _current screen 결정 직후 _ensure_fx_screen에서 호출.
        self.fx = FXOverlay()

        self.pixmap_orig = QPixmap(get_png_path(index + 1))
        self.pixmap_scaled = QPixmap()
        self.opaque_top_ratio = 0.0  # PNG 위쪽 빈 여백 비율 (말풍선 anchor 계산용)
        self._compute_opaque_top_ratio()
        self._update_scaled_pixmap()

        self.anim_t = random.uniform(0, 10)
        self.squash_x = 1.0
        self.squash_y = 1.0
        self.jump_offset = 0.0
        self.sway_angle = 0.0

        self.pet_intensity = 0.0
        # 클릭 모션 페이즈: 0=정지, >0이면 찌그러짐→펴짐→안정 순으로 진행
        self.click_phase_t = 0.0

        self.wander_vx = 0.0
        self.wander_target_x = None
        self.wander_pause = 0
        self.wander_x_float = None
        self.wander_stuck_ticks = 0

        self.dragging = False
        self.drag_start_global = QPoint()
        self.drag_start_window = QPoint()
        self.locked = True
        self.last_mouse = None

        self._apply_window_flags(initial=True)
        self.setMouseTracking(True)
        # PNG 위 hover 시 손바닥 커서. 알파 마스크로 윈도우 모양이 잡혀 있어
        # 불투명 픽셀 위에서만 보이고 투명 영역은 click-through라 자동 제외.
        self.setCursor(QCursor(Qt.OpenHandCursor))
        self.setWindowTitle(t('pet_window_title', n=index + 1))

        self._apply_box_size()

        positions = self.config.get('positions') or DEFAULT_CONFIG['positions']
        if self.index < len(positions):
            x, y = positions[self.index]
        else:
            x, y = 300 + index * 200, 300
        self.move(int(x), int(y))

        # 펫의 초기 화면을 결정하고 FX를 그 화면에 맞춰 띄운다. show 순서가 늦으면
        # 입자/말풍선이 잠깐 잘못된 화면에 뜰 수 있으므로 PetOverlay show 전에 FX 먼저.
        self._last_fx_screen = self._screen_at_pet_center()
        if self._last_fx_screen is not None:
            self.fx.set_screen(self._last_fx_screen)
        self.fx.show()
        self.fx.set_layer(self.config.get('layer', 'top'))

        # 프레임이 밀려도 움직임 속도가 유지되도록 실제 경과 시간(dt)으로 진행
        self._last_tick = time.perf_counter()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

        # z-order heartbeat (펫 본체용). 작업표시줄(Shell_TrayWnd)도 topmost 윈도우라
        # 사용자가 작업표시줄을 클릭하면 OS가 작업표시줄 자신을 topmost 그룹 최상위로
        # 올리고 우리 펫이 그 아래로 보이게 된다. Windows의 topmost는 동등 그룹이라
        # "더 topmost"는 없고, 마지막으로 SetWindowPos(HWND_TOPMOST)를 호출한 윈도우가
        # 그 그룹 최상위. 즉 사후 대응(reactive) 외에 막을 방법이 없다.
        # 60Hz (16ms)로 재적용 → 사용자 입장에서 깜빡임이 1프레임 이내라 인지 불가.
        # SetWindowPos(SWP_NOMOVE|NOSIZE|NOACTIVATE)는 매우 가벼워 60Hz도 CPU 영향 미미.
        self._z_timer = QTimer(self)
        self._z_timer.timeout.connect(self._reapply_z_order)
        self._z_timer.start(16)

    def _reapply_z_order(self):
        if self.config.get('layer', 'top') == 'top':
            self._apply_z_order('top')

    def _apply_z_order(self, layer):
        """Win32 SetWindowPos로 펫 윈도우의 z-order 재적용.
        NOTOPMOST → TOPMOST 2단계 호출이 핵심. 윈도우가 이미 WS_EX_TOPMOST면
        SetWindowPos(HWND_TOPMOST) 단독 호출은 OS가 z-order를 재평가하지 않는
        no-op 케이스가 있다. 한 번 NOTOPMOST로 내렸다가 다시 TOPMOST로 올려야
        실제로 topmost 그룹 최상위로 재배치된다. FXOverlay._apply_layer와 동일 패턴."""
        if sys.platform != 'win32':
            if layer == 'bottom':
                self.lower()
            else:
                self.raise_()
            return
        try:
            import ctypes
            hwnd = int(self.winId())
            if not hwnd:
                return
            u32 = ctypes.windll.user32
            HWND_TOPMOST = -1
            HWND_NOTOPMOST = -2
            HWND_BOTTOM = 1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            f = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
            if layer == 'bottom':
                u32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, f)
                u32.SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0, f)
            else:
                u32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, f)
                u32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, f)
        except Exception as e:
            _diag(f'pet _apply_z_order failed: {e}')

    def nativeEvent(self, eventType, message):
        # OS가 펫 윈도우의 z-order를 변경하려는 순간(WM_WINDOWPOSCHANGING)을 가로채
        # hwndInsertAfter를 강제로 HWND_TOPMOST로 덮어쓴다. 작업표시줄 클릭 시 OS가
        # 펫을 비-topmost로 강등시키려는 시도 자체를 무효화 → 가려졌다가 복귀하는
        # 깜빡임 없이 항상 위에 있게 됨. heartbeat는 위치/이동 등 다른 경로로 z-order
        # 가 무너진 케이스를 잡는 보강용으로 유지.
        # SWP_NOZORDER 플래그가 박혀 있으면 z-order는 안 바꾸는 메시지(위치만 이동)
        # 이므로 건드리지 않는다 → minimize/maximize/이동 등 정상 동작 보존.
        if sys.platform == 'win32' and self.config.get('layer', 'top') == 'top':
            try:
                import ctypes
                from ctypes import wintypes
                ptr = None
                try:
                    ptr = int(message)
                except (TypeError, ValueError):
                    try:
                        import shiboken6
                        ptr = shiboken6.getCppPointer(message)[0]
                    except Exception:
                        ptr = None
                if ptr:
                    msg = ctypes.cast(ptr, ctypes.POINTER(wintypes.MSG)).contents
                    WM_WINDOWPOSCHANGING = 0x0046
                    if msg.message == WM_WINDOWPOSCHANGING:
                        class WINDOWPOS(ctypes.Structure):
                            _fields_ = [
                                ('hwndInsertAfter', ctypes.c_void_p),
                                ('hwnd', ctypes.c_void_p),
                                ('x', ctypes.c_int),
                                ('y', ctypes.c_int),
                                ('cx', ctypes.c_int),
                                ('cy', ctypes.c_int),
                                ('flags', ctypes.c_uint),
                            ]
                        SWP_NOZORDER = 0x0004
                        wp = ctypes.cast(int(msg.lParam), ctypes.POINTER(WINDOWPOS)).contents
                        if not (wp.flags & SWP_NOZORDER):
                            # OS가 z-order를 바꾸려 함 → 강제로 HWND_TOPMOST(-1)로
                            wp.hwndInsertAfter = ctypes.c_void_p(-1).value
            except Exception:
                pass
        return super().nativeEvent(eventType, message)

    def _screen_at_pet_center(self):
        """펫이 현재 위치한 QScreen 반환.
        1순위: Qt가 펫 윈도우에 직접 할당한 screen (`windowHandle().screen()`).
        OS 네이티브 트래킹(WM_DPICHANGED 등) 기반이라 신티크 같은 액정타블렛/
        Wacom 드라이버 환경에서도 정확. v1.2.4에서 좌표 기반 screenAt만 썼는데,
        일부 액정타블렛에서 None 반환 → primary로 잘못 폴백 → 펫과 다른 화면에
        FX가 붙어 털·말풍선이 안 보이는 케이스가 발견돼 보강.
        2순위: 펫 중앙 좌표로 screenAt — windowHandle 미생성 시점 폴백.
        3순위: primary."""
        wh = self.windowHandle()
        if wh is not None:
            scr = wh.screen()
            if scr is not None:
                return scr
        cx = self.x() + self.width() // 2
        cy = self.y() + self.height() // 2
        scr = QGuiApplication.screenAt(QPoint(cx, cy))
        if scr is None:
            scr = QGuiApplication.primaryScreen()
        return scr

    def _sync_fx_screen(self):
        """펫이 화면을 옮기면 FX도 따라가게. 매 tick 호출."""
        if self.fx is None:
            return
        scr = self._screen_at_pet_center()
        if scr is not None and scr is not self._last_fx_screen:
            self.fx.set_screen(scr)
            self._last_fx_screen = scr

    def showEvent(self, event):
        # show 직후엔 Qt가 펫 윈도우의 실제 screen을 비로소 확정함.
        # 첫 _tick(16ms) 전에 FX를 한 번 즉시 동기화해 두면 show 직후 클릭 시
        # 입자가 잠깐 옛 screen 기준으로 emit되는 케이스를 막을 수 있다.
        # 또한 windowHandle.screenChanged에 연결해 펫이 화면을 옮길 때 FX가
        # 16ms 폴링을 기다리지 않고 즉시 따라가게 한다.
        super().showEvent(event)
        self._sync_fx_screen()
        wh = self.windowHandle()
        if wh is not None and not getattr(self, '_screen_signal_connected', False):
            try:
                # screenChanged 시그널은 QScreen* 인자 1개를 넘김. _sync_fx_screen은
                # 인자 안 받으니 lambda로 흡수.
                wh.screenChanged.connect(lambda _scr: self._sync_fx_screen())
                self._screen_signal_connected = True
            except Exception:
                pass

    def _apply_window_flags(self, initial=False):
        # 'top' 레이어는 Qt.WindowStaysOnTopHint로 OS가 직접 z-order 보장.
        # (이전엔 Win32 SetWindowPos만 썼는데 다른 앱 활성화 시 펫이 뒤로 빠지는
        # 케이스가 보고됐고, 일정 주기 재적용으로는 깜빡임이 남았다.
        # 레이어 토글은 어차피 close+deleteLater + 재생성으로 처리되므로
        # 양방향 토글 깨짐 문제는 발생하지 않는다.)
        flags = Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
        if self.config.get('layer', 'top') == 'top':
            flags |= Qt.WindowStaysOnTopHint
        if not initial:
            cur_pos = self.pos()
            was_visible = self.isVisible()
            if was_visible:
                self.hide()
            self.setWindowFlags(flags)
            if was_visible:
                self.move(cur_pos)
                self.show()
        else:
            self.setWindowFlags(flags)
        self._apply_taskbar_hide()
        # setWindowFlags 호출이 native HWND를 재생성할 수 있어 mouseTracking과
        # cursor를 다시 보장. 호버 시 mouseMoveEvent가 호출돼 hover 시 털 빠지는
        # 동작 유지 + PNG 위 손바닥 커서 유지.
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.OpenHandCursor))

    def _apply_taskbar_hide(self):
        """Win32 WS_EX_TOOLWINDOW + (bottom일 때) WS_EX_NOACTIVATE."""
        if sys.platform != 'win32':
            return
        try:
            import ctypes
            hwnd = int(self.winId())
            GWL_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_NOACTIVATE = 0x08000000
            user32 = ctypes.windll.user32
            ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ex_style |= WS_EX_TOOLWINDOW
            if self.config.get('layer', 'top') == 'bottom':
                ex_style |= WS_EX_NOACTIVATE
            else:
                ex_style &= ~WS_EX_NOACTIVATE
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)
        except Exception as e:
            _diag(f'taskbar hide failed: {e}')

    def _current_scale_pct(self):
        scales = self.config.get('scales') or [100, 100, 100]
        if self.index < len(scales):
            return int(scales[self.index])
        return int(self.config.get('scale', 100))

    def _compute_opaque_top_ratio(self):
        """원본 PNG에서 위쪽으로부터 첫 불투명 픽셀이 나타나는 행의 비율(0~1).
        말풍선이 PNG 박스 윗변이 아니라 캐릭터 머리 바로 위에 뜨도록 사용."""
        if self.pixmap_orig.isNull():
            self.opaque_top_ratio = 0.0
            return
        img = self.pixmap_orig.toImage().convertToFormat(QImage.Format_ARGB32)
        w, h = img.width(), img.height()
        if w == 0 or h == 0:
            self.opaque_top_ratio = 0.0
            return
        threshold = 8
        step = max(1, w // 64)  # 가로 64샘플로 충분 (오탐 거의 없음)
        found = 0
        for y in range(h):
            row_has = False
            for x in range(0, w, step):
                if (img.pixel(x, y) >> 24) & 0xFF > threshold:
                    row_has = True
                    break
            if row_has:
                found = y
                break
        self.opaque_top_ratio = found / h

    def _update_scaled_pixmap(self):
        if self.pixmap_orig.isNull():
            self.pixmap_scaled = QPixmap(120, 120)
            self.pixmap_scaled.fill(QColor(180, 180, 180, 200))
            return
        scale = max(20, min(300, self._current_scale_pct())) / 100.0
        w = max(8, int(self.pixmap_orig.width() * scale))
        h = max(8, int(self.pixmap_orig.height() * scale))
        self.pixmap_scaled = self.pixmap_orig.scaled(
            w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

    def _apply_box_size(self):
        # 좌우 흔들기(±10°)와 squash·stretch 시 PNG가 원본 박스를 넘어가므로
        # 회전 + 스케일 변형 후의 최대 점유 면적 만큼 윈도우 폭과 높이를 키운다.
        iw = self.pixmap_scaled.width()
        ih = self.pixmap_scaled.height()
        max_sx = 1.10  # 클릭 부스트 등으로 최대 +10% 가로 확대
        max_sy = 1.20
        max_angle_rad = math.radians(11)  # ±10°에 약간 여유
        sw = iw * max_sx
        sh = ih * max_sy
        # 하단 중심을 회전축으로 회전한 사각형의 max half-width / height
        cos_a = abs(math.cos(max_angle_rad))
        sin_a = abs(math.sin(max_angle_rad))
        rot_half_w = (sw / 2) * cos_a + sh * sin_a
        rot_h = sh * cos_a + (sw / 2) * sin_a
        side_pad = max(0, int(math.ceil(rot_half_w - iw / 2))) + 4
        self.jump_headroom = max(60, int(math.ceil(rot_h - ih)) + 14)
        box_w = iw + side_pad * 2
        box_h = int(rot_h) + self.jump_headroom + 4
        self.setFixedSize(box_w, box_h)
        self.image_w = iw
        self.image_h = ih
        self.side_pad = side_pad

    def _tick(self):
        now_pc = time.perf_counter()
        # 60fps 1프레임 = 1.0. 절전 복귀 등 긴 공백 뒤 순간이동 방지로 상한 4프레임.
        dt = max(0.25, min(4.0, (now_pc - self._last_tick) * 60.0))
        self._last_tick = now_pc

        # 펫이 다른 모니터로 넘어갔는지 매 프레임 검사. FX는 단일 화면용이라
        # 화면 변경 시점에 따라가야 보조 모니터에서 입자/말풍선이 정상 표시된다.
        self._sync_fx_screen()

        # 위치 이동 모드(unlock) 또는 드래그 중에는 idle 모션을 정지해
        # 사용자가 옮기는 동안 펫이 흔들리거나 미끄러지지 않도록 한다.
        if not self.locked or self.dragging:
            self.sway_angle = 0.0
            self.squash_x = 1.0
            self.squash_y = 1.0
            self.jump_offset = 0.0
            self.pet_intensity = 0.0
            self.click_phase_t = 0.0
            self.update()
            return

        motions = self.config.get('idle_motions') or []
        if self.index < len(motions):
            motion = motions[self.index]
        else:
            motion = self.config.get('idle_motion', 'jump')
        self.anim_t += 0.03 * dt

        # idle 베이스 변형
        if motion == 'jump':
            phase = math.sin(self.anim_t * 2 * math.pi / 1.4)
            base_sx = 1.0 - 0.035 * phase
            base_sy = 1.0 + 0.05 * phase
            base_jo = (-7 * phase if phase > 0 else 0)
            self.sway_angle = 0.0
        elif motion == 'sway':
            self.sway_angle = 6.0 * math.sin(self.anim_t * 2 * math.pi / 2.6)
            base_sx, base_sy, base_jo = 1.0, 1.0, 0.0
        else:
            self.sway_angle = 0.0
            base_sx, base_sy, base_jo = 1.0, 1.0, 0.0

        # 클릭 모션: 찌그러짐 → 펴짐 → 안정 (총 ~0.5s)
        click_sx, click_sy, click_jo = 0.0, 0.0, 0.0
        if self.click_phase_t > 0:
            t = self.click_phase_t
            if t < 0.30:
                # 1단계: 찌그러짐 (가로 ↑, 세로 ↓)
                s = t / 0.30
                ease = s * s * (3 - 2 * s)  # smoothstep
                click_sx = 0.18 * ease
                click_sy = -0.16 * ease
                click_jo = 0.0
            elif t < 0.70:
                # 2단계: 펴짐 (가로 ↓, 세로 ↑) + 약간 떠오름
                s = (t - 0.30) / 0.40
                ease = s * s * (3 - 2 * s)
                click_sx = 0.18 + (-0.30) * ease   # 0.18 → -0.12
                click_sy = -0.16 + (0.36) * ease   # -0.16 → 0.20
                click_jo = -22 * ease
            elif t < 1.00:
                # 3단계: 안정 복귀
                s = (t - 0.70) / 0.30
                ease = s * s * (3 - 2 * s)
                click_sx = -0.12 * (1 - ease)
                click_sy = 0.20 * (1 - ease)
                click_jo = -22 * (1 - ease)
            self.click_phase_t += 0.045 * dt
            if self.click_phase_t >= 1.0:
                self.click_phase_t = 0.0

        self.squash_x = base_sx + click_sx
        self.squash_y = base_sy + click_sy
        self.jump_offset = base_jo + click_jo

        self.squash_y -= self.pet_intensity * 0.04
        self.squash_x += self.pet_intensity * 0.03

        self.pet_intensity *= 0.90 ** dt

        if self.config.get('wander', False) and not self.dragging and self.locked:
            self._wander_step(dt)

        # 대사 anchor 갱신 (펫이 움직일 때 따라감)
        if self.fx and self.index in self.fx.dialogs:
            cx, top_y = self._dialog_anchor_global()
            self.fx.update_dialog_anchor(self.index, cx, top_y)

        self.update()

    def _wander_step(self, dt=1.0):
        # 펫이 현재 위치한 모니터의 availableGeometry를 기준으로 클램프해야
        # 서브 모니터에 있는 펫이 primary로 끌려오지 않는다.
        cx = self.x() + self.width() // 2
        cy = self.y() + self.height() // 2
        scr = QGuiApplication.screenAt(QPoint(cx, cy))
        if scr is None:
            scr = QGuiApplication.primaryScreen()
        screen = scr.availableGeometry()

        if self.wander_pause > 0:
            self.wander_pause -= dt
            self.wander_vx *= 0.85 ** dt
            self.wander_x_float = float(self.x())
            self.wander_stuck_ticks = 0
            return

        margin = 80
        min_x = screen.x() + margin
        max_x = max(min_x + 1, screen.x() + screen.width() - self.width() - margin)

        if self.wander_target_x is None:
            cur_x = self.x()
            min_disp = min(160, max(40, (max_x - min_x) // 4))
            target = random.randint(int(min_x), int(max_x))
            for _ in range(8):
                if abs(target - cur_x) >= min_disp:
                    break
                target = random.randint(int(min_x), int(max_x))
            self.wander_target_x = target
            self.wander_x_float = float(self.x())
            self.wander_stuck_ticks = 0

        diff = self.wander_target_x - self.x()
        if abs(diff) < 3:
            self.wander_target_x = None
            self.wander_pause = random.randint(45, 150)
            self.wander_vx *= 0.3
            self.wander_stuck_ticks = 0
            return

        target_v = max(-1.6, min(1.6, diff * 0.04))
        self.wander_vx += (target_v - self.wander_vx) * (1 - 0.88 ** dt)
        # 가속 초반에 vx가 너무 작아 int 변환에서 묻히는 구간을 없앤다.
        if abs(self.wander_vx) < 0.5:
            self.wander_vx = 0.5 if diff > 0 else -0.5

        # 외부에서 self.move()가 호출됐거나 누적 오차가 클 때 재동기화
        if self.wander_x_float is None or abs(self.wander_x_float - self.x()) > 30:
            self.wander_x_float = float(self.x())
        self.wander_x_float += self.wander_vx * dt

        new_x = int(self.wander_x_float)
        new_x = max(screen.x(), min(screen.x() + screen.width() - self.width(), new_x))

        if new_x == self.x():
            # vx가 너무 작아 정수 픽셀로는 안 움직이는 경우 워치독
            self.wander_stuck_ticks += dt
            if self.wander_stuck_ticks > 90:
                # 1.5초 이상 정수 좌표로 안 움직이면 타깃 재선정 (방어책)
                self.wander_target_x = None
                self.wander_vx = 0.0
                self.wander_stuck_ticks = 0
            return

        self.wander_stuck_ticks = 0
        self.move(new_x, self.y())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # 변환: 하단 중앙 기준 (sway, squash, jump)
        cx = getattr(self, 'side_pad', 0) + self.image_w / 2
        cy_bottom = self.jump_headroom + self.image_h + self.jump_offset

        painter.translate(cx, cy_bottom)
        painter.rotate(self.sway_angle)
        painter.scale(self.squash_x, self.squash_y)
        painter.drawPixmap(int(-self.image_w / 2), -self.image_h, self.pixmap_scaled)

    def _pet_center_global(self, local_x=None, local_y=None):
        """로컬 좌표를 글로벌(스크린)로 변환. None이면 PNG 중앙."""
        sp = getattr(self, 'side_pad', 0)
        if local_x is None:
            local_x = sp + self.image_w / 2
        if local_y is None:
            local_y = self.jump_headroom + self.image_h / 2
        gp = self.mapToGlobal(QPoint(int(local_x), int(local_y)))
        return gp.x(), gp.y()

    def _dialog_anchor_global(self):
        """대사 꼬리 위치(불투명 영역 위쪽 중앙)의 글로벌 좌표.
        PNG 위쪽 빈 여백을 건너뛰어 말풍선이 캐릭터 머리 바로 위에 뜨게 한다."""
        local_cx = getattr(self, 'side_pad', 0) + self.image_w / 2
        opaque_offset = int(self.image_h * getattr(self, 'opaque_top_ratio', 0.0))
        local_top = self.jump_headroom + self.jump_offset + opaque_offset
        gp = self.mapToGlobal(QPoint(int(local_cx), int(local_top)))
        return gp.x(), gp.y()

    def _current_fur_color(self):
        colors = self.config.get('fur_colors') or []
        if self.index < len(colors) and colors[self.index]:
            return colors[self.index]
        return self.config.get('fur_color', '#7BAFA0')

    def _emit_fur(self, n, local_x, local_y, burst=1.0):
        if not self.fx:
            return
        gp = self.mapToGlobal(QPoint(int(local_x), int(local_y)))
        color = self._current_fur_color()
        persistent = bool(self.config.get('fur_persistent', False))
        spread = max(8, min(self.image_w, self.image_h) * 0.25)
        self.fx.add_particles(n, gp.x(), gp.y(), color, persistent, burst, spread)

    # 마우스
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 쓰담쓰담/드래그 양쪽 모두 grab → grabbing 메타포로 통일.
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            if self.locked:
                lp = event.position().toPoint()
                self.last_mouse = lp
                self._emit_fur(10, lp.x(), lp.y(), burst=1.2)
                self.click_phase_t = 0.001  # 클릭 모션 시작 (찌그러짐→펴짐)
                per_char = self.config.get('dialogs_per_char') or []
                slot = per_char[self.index] if 0 <= self.index < len(per_char) else []
                pool = [s for s in slot if isinstance(s, str) and s.strip()]
                if pool and self.fx:
                    text = random.choice(pool)
                    cx, top_y = self._dialog_anchor_global()
                    self.fx.show_dialog(self.index, text, cx, top_y,
                                        self._current_fur_color())
            else:
                self.dragging = True
                self.drag_start_global = event.globalPosition().toPoint()
                self.drag_start_window = self.pos()
                self.grabMouse()
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.globalPosition().toPoint() - self.drag_start_global
            self.move(self.drag_start_window + delta)
            return
        if not self.locked:
            return
        pos = event.position().toPoint()
        if self.last_mouse is None:
            self.last_mouse = pos
            return
        dx = pos.x() - self.last_mouse.x()
        dy = pos.y() - self.last_mouse.y()
        dist = math.hypot(dx, dy)
        if event.buttons() & Qt.LeftButton:
            if dist > 4:
                n = max(1, min(7, int(dist / 6)))
                self._emit_fur(n, pos.x(), pos.y(), burst=1.0)
                self.pet_intensity = min(1.0, self.pet_intensity + 0.18)
                self.last_mouse = pos
        else:
            if dist > 10:
                self._emit_fur(1, pos.x(), pos.y(), burst=0.6)
                self.pet_intensity = min(1.0, self.pet_intensity + 0.05)
                self.last_mouse = pos

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.dragging:
                self.dragging = False
                self.releaseMouse()
                self._save_position()
                # 드래그로 위치가 바뀌었으니 wander 상태(target_x/vx)를 리셋.
                # 안 그러면 옛 위치 기준 target으로 즉시 가속해 사용자에게
                # "마우스 가까이 가니 도망" 처럼 보이는 현상 발생.
                self._reset_wander()
            self.setCursor(QCursor(Qt.OpenHandCursor))
            self.last_mouse = None

    def leaveEvent(self, event):
        self.last_mouse = None

    def closeEvent(self, event):
        # 펫 윈도우가 닫힐 때 자기 FX overlay도 같이 정리. 안 하면 FX 윈도우만
        # 화면에 남아 입자/말풍선이 좀비처럼 보임.
        try:
            if self.fx is not None:
                self.fx.close()
                self.fx.deleteLater()
                self.fx = None
        except Exception:
            pass
        super().closeEvent(event)

    def _reset_wander(self, pause_ticks=None):
        """드래그 종료/위치 모드 → 쓰다듬기 모드 전환 시 wander 상태 초기화.
        pause_ticks 만큼 정지 후 다음 _wander_step에서 새 target 선정. None이면
        60~120 ticks (16ms tick 기준 약 1~2초) 정지."""
        self.wander_target_x = None
        self.wander_vx = 0.0
        self.wander_x_float = float(self.x())
        self.wander_stuck_ticks = 0
        if pause_ticks is None:
            pause_ticks = random.randint(60, 120)
        self.wander_pause = pause_ticks

    def _save_position(self):
        positions = list(self.config.get('positions', DEFAULT_CONFIG['positions']))
        while len(positions) <= self.index:
            positions.append([300, 300])
        positions[self.index] = [self.x(), self.y()]
        self.config['positions'] = positions
        save_config(self.config)

    def _show_context_menu(self, global_pos):
        menu = QMenu()
        if self.locked:
            act_mode = menu.addAction(t('ctx_unlock'))
            act_mode.setData('unlock')
        else:
            act_mode = menu.addAction(t('ctx_lock'))
            act_mode.setData('lock')
        menu.addSeparator()
        act_clear = menu.addAction(t('ctx_clear_fur'))
        act_clear.setData('clear')
        act_settings = menu.addAction(t('ctx_settings'))
        act_settings.setData('settings')
        menu.addSeparator()
        act_hide = menu.addAction(t('ctx_hide'))
        act_hide.setData('hide')
        act_quit = menu.addAction(t('ctx_quit'))
        act_quit.setData('quit')

        chosen = menu.exec(global_pos)
        if chosen is None:
            return
        kind = chosen.data()
        if kind == 'unlock':
            self.locked = False
        elif kind == 'lock':
            self.locked = True
            self._save_position()
            # 위치 모드 → 쓰다듬기 모드 전환 시 wander 상태 리셋.
            # 옛 target_x로 즉시 가속해 "도망"처럼 보이는 현상 방지.
            self._reset_wander()
        elif kind == 'clear':
            # 펫별 FX 모델이라 자기 fx만 비우면 다른 펫·다른 화면 입자가 남는다.
            # 모든 펫의 FX를 비우는 의미를 유지하기 위해 FurcatApp으로 위임.
            self.request_clear_all_fur.emit()
        elif kind == 'settings':
            self.request_show_panel.emit()
        elif kind == 'hide':
            self.request_disable_self.emit(self.index)
        elif kind == 'quit':
            self.request_quit.emit()

    def reload_config(self, cfg):
        old_scale = self._current_scale_pct()
        old_layer = self.config.get('layer', 'top')
        self.config = cfg
        new_scale = self._current_scale_pct()
        # 디스크의 PNG 파일이 갱신됐을 수도 있으므로 매번 다시 로드
        new_pix = QPixmap(get_png_path(self.index + 1))
        if not new_pix.isNull():
            self.pixmap_orig = new_pix
            self._compute_opaque_top_ratio()
            self._update_scaled_pixmap()
            self._apply_box_size()
        elif new_scale != old_scale:
            self._update_scaled_pixmap()
            self._apply_box_size()
        if cfg.get('layer', 'top') != old_layer:
            self._apply_window_flags()


# --------------------------------------------------------------------------
# Control panel
# --------------------------------------------------------------------------
_COLOR_DIALOG_KO = {
    '&Basic colors': '기본 색상',
    'Basic colors': '기본 색상',
    '&Custom colors': '사용자 색상',
    'Custom colors': '사용자 색상',
    '&Add to Custom Colors': '사용자 색상에 추가',
    'Add to Custom Colors': '사용자 색상에 추가',
    'Pick Screen Color': '화면 색 추출',
    '&Pick Screen Color': '화면 색 추출',
    'Hu&e:': '색조:',
    'Hue:': '색조:',
    '&Sat:': '채도:',
    'Sat:': '채도:',
    '&Val:': '명도:',
    'Val:': '명도:',
    '&Red:': '빨강:',
    'Red:': '빨강:',
    '&Green:': '초록:',
    'Green:': '초록:',
    'Bl&ue:': '파랑:',
    'Blue:': '파랑:',
    'A&lpha channel:': '투명도:',
    'Alpha channel:': '투명도:',
    '&HTML:': 'HTML:',
    'HTML:': 'HTML:',
    'OK': '확인',
    'Cancel': '취소',
    '&OK': '확인',
    '&Cancel': '취소',
}

_COLOR_DIALOG_JP = {
    '&Basic colors': '基本色',
    'Basic colors': '基本色',
    '&Custom colors': 'カスタム色',
    'Custom colors': 'カスタム色',
    '&Add to Custom Colors': 'カスタム色に追加',
    'Add to Custom Colors': 'カスタム色に追加',
    'Pick Screen Color': '画面の色を取得',
    '&Pick Screen Color': '画面の色を取得',
    'Hu&e:': '色相:',
    'Hue:': '色相:',
    '&Sat:': '彩度:',
    'Sat:': '彩度:',
    '&Val:': '明度:',
    'Val:': '明度:',
    '&Red:': '赤:',
    'Red:': '赤:',
    '&Green:': '緑:',
    'Green:': '緑:',
    'Bl&ue:': '青:',
    'Blue:': '青:',
    'A&lpha channel:': '透明度:',
    'Alpha channel:': '透明度:',
    '&HTML:': 'HTML:',
    'HTML:': 'HTML:',
    'OK': 'OK',
    'Cancel': 'キャンセル',
    '&OK': 'OK',
    '&Cancel': 'キャンセル',
}


def _localize_color_dialog(dlg):
    """현재 언어에 맞춰 QColorDialog 라벨/버튼을 치환.
    ENG는 Qt 기본(영문)이라 치환 생략."""
    table = None
    if _CURRENT_LANG == 'KOR':
        table = _COLOR_DIALOG_KO
    elif _CURRENT_LANG == 'JPN':
        table = _COLOR_DIALOG_JP
    if table is None:
        return
    for child in dlg.findChildren(QWidget):
        if isinstance(child, (QLabel, QPushButton)):
            txt = child.text()
            if txt in table:
                child.setText(table[txt])


class CardSeparator(QWidget):
    """캐릭터 카드 사이 세로 구분선. 위/아래 여백 남기고 가운데만 1px 선."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(1)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setPen(QColor(PALETTE['border_light']))
        h = self.height()
        margin = 18
        if h > margin * 2:
            p.drawLine(0, margin, 0, h - margin)


class ArrowComboBox(QComboBox):
    """우측에 채워진 역삼각형(▼)을 paintEvent로 직접 그리는 콤보박스.
    QSS data URI SVG는 Qt 환경에 따라 렌더링이 불안정해 직접 그림."""

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(PALETTE['primary_dark'])))
        cx = self.width() - 8
        cy = self.height() / 2
        # 역삼각형: (-3.5,-2), (+3.5,-2), (0,+3)
        pts = QPolygonF([
            QPointF(cx - 3.5, cy - 2),
            QPointF(cx + 3.5, cy - 2),
            QPointF(cx, cy + 3),
        ])
        p.drawPolygon(pts)


def _install_rainbow_standard_colors():
    """QColorDialog의 standard color 48 슬롯을 6행 8열 그라디언트로 덮어쓴다.
    좌→우는 hue 0/45/90/135/180/225/270/315° (빨→자홍), 위→아래는
    비비드 2행 → 파스텔 3행 → 흰~검 회색 1행. 한 번 호출하면 이후 모든
    QColorDialog 인스턴스에 반영된다."""
    import colorsys
    color_rows = [
        (0.40, 1.00),  # 0: 진한 비비드
        (0.55, 0.95),  # 1: 표준 비비드
        (0.68, 0.60),  # 2: 중간 파스텔
        (0.78, 0.55),  # 3: 연한 파스텔
        (0.88, 0.50),  # 4: 가장 연한 파스텔
    ]
    for r, (lightness, sat) in enumerate(color_rows):
        for c in range(8):
            h = (c * 45.0) / 360.0
            rr, gg, bb = colorsys.hls_to_rgb(h, lightness, sat)
            qc = QColor(int(round(rr * 255)), int(round(gg * 255)), int(round(bb * 255)))
            try:
                QColorDialog.setStandardColor(r * 8 + c, qc)
            except Exception:
                pass
    # 마지막 행(인덱스 5): 흰색→검은색 8단계 그라디언트
    for c in range(8):
        v = int(round(255 - c * 255 / 7))
        try:
            QColorDialog.setStandardColor(5 * 8 + c, QColor(v, v, v))
        except Exception:
            pass


# 체험판 파스텔 팔레트 — 무지개 17색(hue 360°/17 균등, S=0.5, L=0.78) +
# 흰/회/검 3색. 총 20색.
TRIAL_PASTEL_COLORS = [
    '#E3ABAB', '#E3BFAB', '#E3D2AB', '#E0E3AB', '#CCE3AB', '#B8E3AB',
    '#ABE3B1', '#ABE3C5', '#ABE3D9', '#ABD9E3', '#ABC5E3', '#ABB1E3',
    '#B8ABE3', '#CCABE3', '#E0ABE3', '#E3ABD2', '#E3ABBF',
    '#FFFFFF', '#808080', '#000000',
]
TRIAL_PASTEL_GRID_COLS = 10  # 20색 / 2행


class TrialPastelDialog(QDialog):
    """체험판 전용 색상 선택 다이얼로그. 미리 정한 파스텔 10색만 선택 가능 +
    정식판 안내 문구 표시."""

    def __init__(self, current_hex, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t('color_dialog_title'))
        self._selected = QColor(current_hex) if QColor(current_hex).isValid() else QColor(TRIAL_PASTEL_COLORS[0])

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        hint = QLabel(t('trial_color_hint'))
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"color:{PALETTE['primary_dark']}; font-size:11px; "
            f"background:{PALETTE['bg_soft']}; border:1px solid {PALETTE['border_light']}; "
            f"border-radius:8px; padding:8px 10px;"
        )
        root.addWidget(hint)

        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)
        cur = self._selected.name().lower()
        self._swatches = []
        cols = TRIAL_PASTEL_GRID_COLS
        for idx, hx in enumerate(TRIAL_PASTEL_COLORS):
            sw = QPushButton()
            sw.setFixedSize(32, 32)
            sw.setCursor(Qt.PointingHandCursor)
            sw.setCheckable(True)
            is_cur = (hx.lower() == cur)
            sw.setChecked(is_cur)
            sw.setStyleSheet(
                f"QPushButton {{ background:{hx}; border:2px solid "
                f"{PALETTE['primary_dark'] if is_cur else PALETTE['border']}; "
                f"border-radius:7px; }}"
                f"QPushButton:hover {{ border:2px solid {PALETTE['primary_dark']}; }}"
            )
            sw.clicked.connect(lambda _=False, h=hx: self._on_pick(h))
            self._swatches.append((hx, sw))
            grid.addWidget(sw, idx // cols, idx % cols)
        root.addLayout(grid)

        from PySide6.QtWidgets import QDialogButtonBox
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(t('ok'))
        bb.button(QDialogButtonBox.Cancel).setText(t('cancel'))
        btn_qss = (
            f"background-color: {PALETTE['bg_hover']};"
            f"color: {PALETTE['primary_dark']};"
            f"border: 1px solid {PALETTE['border']};"
            "border-radius: 9px; padding: 7px 16px; font-weight: bold;"
        )
        for b in bb.buttons():
            b.setStyleSheet(
                f"QPushButton {{ {btn_qss} }}"
                f"QPushButton:hover {{ background-color: {PALETTE['border_light']}; }}"
                f"QPushButton:pressed {{ background-color: {PALETTE['border']}; }}"
            )
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        root.addWidget(bb)

        self.setStyleSheet(f"QDialog {{ background:{PALETTE['bg']}; }}")

    def _on_pick(self, hex_str):
        self._selected = QColor(hex_str)
        cur = hex_str.lower()
        for hx, sw in self._swatches:
            is_cur = (hx.lower() == cur)
            sw.blockSignals(True)
            sw.setChecked(is_cur)
            sw.blockSignals(False)
            sw.setStyleSheet(
                f"QPushButton {{ background:{hx}; border:2px solid "
                f"{PALETTE['primary_dark'] if is_cur else PALETTE['border']}; "
                f"border-radius:7px; }}"
                f"QPushButton:hover {{ border:2px solid {PALETTE['primary_dark']}; }}"
            )

    def selected_color(self):
        return self._selected


class ColorButton(QPushButton):
    color_changed = Signal(str)

    def __init__(self, color_hex, parent=None):
        super().__init__(parent)
        self.setFixedSize(48, 28)
        self.setCursor(Qt.PointingHandCursor)
        self._color = QColor(color_hex)
        self.clicked.connect(self._pick)
        self._refresh_style()

    def _pick(self):
        if TRIAL_MODE:
            dlg = TrialPastelDialog(self._color.name(), self)
            accepted = dlg.exec() == QDialog.Accepted
            if accepted:
                c = dlg.selected_color()
                if c.isValid():
                    self._color = c
                    self._refresh_style()
                    self.color_changed.emit(c.name())
            dlg.deleteLater()
            return
        dlg = QColorDialog(self._color, self)
        # WA_DeleteOnClose는 PySide6 일부 환경에서 exec() 반환 직전/직후에
        # 다이얼로그가 삭제돼 currentColor()가 invalid color를 반환하는 케이스가 있다.
        # 명시적으로 exec() 후 deleteLater() 호출하는 패턴으로 변경.
        dlg.setOption(QColorDialog.DontUseNativeDialog, True)
        dlg.setWindowTitle(t('color_dialog_title'))
        # 배경은 v1.0.0과 동일하게 Qt 기본 톤. 글씨가 들어있는 버튼들만
        # 바깥 '이미지 변경'(secondary) 톤으로 고정한다.
        # 다이얼로그/QApplication 레벨 QSS는 QDialogButtonBox 안 OK/Cancel에
        # 잘 적용되지 않는 케이스가 있어, 자식 버튼들에 inline setStyleSheet으로
        # 직접 박는다 (selector 우선순위와 무관하게 항상 최우선).
        _localize_color_dialog(dlg)
        btn_qss = (
            f"background-color: {PALETTE['bg_hover']};"
            f"color: {PALETTE['primary_dark']};"
            f"border: 1px solid {PALETTE['border']};"
            "border-radius: 9px; padding: 7px 16px; font-weight: bold;"
        )
        for btn in dlg.findChildren(QPushButton):
            btn.setStyleSheet(
                f"QPushButton {{ {btn_qss} }}"
                f"QPushButton:hover {{ background-color: {PALETTE['border_light']}; }}"
                f"QPushButton:pressed {{ background-color: {PALETTE['border']}; }}"
                f"QPushButton:default {{ {btn_qss} }}"
            )
        accepted = dlg.exec() == QColorDialog.Accepted
        if accepted:
            c = dlg.currentColor()
            if c.isValid():
                self._color = c
                self._refresh_style()
                self.color_changed.emit(c.name())
        dlg.deleteLater()

    def set_color(self, hex_str):
        c = QColor(hex_str)
        if c.isValid():
            self._color = c
            self._refresh_style()

    def _refresh_style(self):
        self.setStyleSheet(
            f'QPushButton {{ background:{self._color.name()}; '
            f'border:1.5px solid {PALETTE["border"]}; border-radius:6px; }}'
            f'QPushButton:hover {{ border:1.5px solid {PALETTE["primary_dark"]}; }}'
        )


APP_VERSION = '1.2.8'
APP_RELEASE_DATE = '2026.11.12'


class LanguageDialog(QDialog):
    """언어 선택 다이얼로그. KOR/JPN/ENG 라디오 + 확인/취소.
    선택값은 selected_lang()으로 반환. Cancel 또는 X 누르면 변경 없음."""

    def __init__(self, parent=None, current='KOR'):
        super().__init__(parent)
        # Qt 기본 다이얼로그 타이틀바 우상단 ?(WhatsThis) 아이콘 제거
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        # 누수 방지는 호출 측에서 명시적 deleteLater()로 처리.
        # WA_DeleteOnClose는 일부 PySide6 환경에서 exec() 반환 직후 객체가
        # 삭제돼 결과 조회가 실패하는 케이스가 있어 사용하지 않는다.
        self.setWindowTitle(t('lang_dialog_title'))
        self.setWindowIcon(get_app_icon())
        self.setStyleSheet(_build_panel_qss())
        self.setMinimumWidth(280)
        self._chosen = current

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 18, 20, 16)
        v.setSpacing(10)

        title = QLabel(t('lang_dialog_title'))
        title.setStyleSheet(
            f"font-size:16px; font-weight:bold; color:{PALETTE['primary_dark']};"
        )
        v.addWidget(title)

        self._group = QButtonGroup(self)
        self._radios = {}
        for code, _native in APP_LANG_OPTIONS:
            label_key = {'KOR': 'lang_kor', 'JPN': 'lang_jpn', 'ENG': 'lang_eng'}[code]
            rb = QRadioButton(t(label_key))
            rb.setChecked(code == current)
            self._radios[code] = rb
            self._group.addButton(rb)
            v.addWidget(rb)

        v.addSpacing(6)
        bl = QHBoxLayout()
        bl.addStretch(1)
        btn_ok = QPushButton('YES')
        btn_ok.setObjectName('secondary')
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self._accept)
        btn_cancel = QPushButton('NO')
        btn_cancel.setObjectName('secondary')
        btn_cancel.clicked.connect(self.reject)
        bl.addWidget(btn_ok)
        bl.addWidget(btn_cancel)
        v.addLayout(bl)

    def _accept(self):
        for code, rb in self._radios.items():
            if rb.isChecked():
                self._chosen = code
                break
        self.accept()

    def selected_lang(self):
        return self._chosen


class CreditsDialog(QDialog):
    """KIWI_CREDIT_GUIDE.md 표준 PySide6 크레딧 다이얼로그.
    1.png 메인 색상을 따 sage/파스텔 톤으로 채색."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 누수 방지는 호출 측 명시적 deleteLater()로 통일 (다이얼로그 일관성).
        self.setFixedWidth(420)
        self._drag_offset = None
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setObjectName('creditContainer')
        container.setStyleSheet(f"""
            QWidget#creditContainer {{
                background-color: white;
                border-radius: 18px;
                border: 1px solid {PALETTE['border_light']};
            }}
            QLabel {{
                background: transparent;
                color: {PALETTE['text']};
                font-family: '{APP_FONT_FAMILY}', '맑은 고딕', sans-serif;
            }}
        """)
        outer.addWidget(container)

        v = QVBoxLayout(container)
        v.setContentsMargins(28, 28, 28, 28)
        v.setSpacing(0)

        # 우상단 닫기 — 컨테이너에 직접 자식으로 띄워 항상 위에 보이게
        self._btn_close = QPushButton('×', container)
        self._btn_close.setFixedSize(30, 30)
        self._btn_close.setCursor(Qt.PointingHandCursor)
        self._btn_close.setFocusPolicy(Qt.NoFocus)
        self._btn_close.setStyleSheet(f"""
            QPushButton {{
                background: {PALETTE['bg_soft']};
                color: {PALETTE['text_soft']};
                font-family: 'Arial', sans-serif;
                font-size: 18px;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                padding: 0;
            }}
            QPushButton:hover {{
                background: {PALETTE['border_light']};
                color: {PALETTE['primary_dark']};
            }}
        """)
        self._btn_close.clicked.connect(self.accept)
        self._btn_close.raise_()

        # 타이틀 + 앱 아이콘 (16px 픽셀아트 → x5 NEAREST 업스케일로 80px 크리스피)
        thumb = QLabel()
        icon_png = None
        for p in (os.path.join(EXTERNAL_DIR, 'furcat_icon_16.png'),
                  os.path.join(BASE_DIR, 'furcat_icon_16.png')):
            if os.path.exists(p):
                icon_png = p
                break
        if icon_png:
            pm = QPixmap(icon_png)
            if not pm.isNull():
                pm = pm.scaled(80, 80, Qt.KeepAspectRatio, Qt.FastTransformation)
                thumb.setPixmap(pm)
        else:
            pm = QPixmap(get_png_path(3))
            if not pm.isNull():
                pm = pm.scaledToHeight(84, Qt.SmoothTransformation)
                thumb.setPixmap(pm)
        thumb.setAlignment(Qt.AlignCenter)
        v.addWidget(thumb)

        title = QLabel(_app_name_with_suffix())
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {PALETTE['primary_dark']}; "
            "padding-top: 10px;"
        )
        v.addWidget(title)

        v.addSpacing(14)
        v.addWidget(self._sep())
        v.addSpacing(14)

        # Galmuri11 ppem 친화 사이즈: 11 / 22 / 33 px
        body_lines = [
            (f"Version {APP_VERSION}", 11, False),
            (f"Release {APP_RELEASE_DATE}", 11, False),
            (None, None, None),
            (t('credits_made_by'), 11, True),
            (None, None, None),
            ('Used Tools: Claude / Claude Code', 11, False),
            (t('credits_ai'), 11, False),
            (None, None, None),
            ('Special Thanks', 11, True),
            ('챠(@final_bbung)', 11, False),
            (None, None, None),
            (t('credits_fonts'), 11, True),
            ('Galmuri11 / Galmuri11-Bold', 11, False),
            ('© 2019-2025 Lee Minseo', 11, False),
            ('SIL Open Font License 1.1', 11, False),
            (None, None, None),
            ('Contact', 11, True),
            ('Twitter(X): @kiwwwicat', 11, False),
        ]
        for text, size, bold in body_lines:
            if text is None:
                v.addSpacing(10)
                continue
            lab = QLabel(text)
            lab.setAlignment(Qt.AlignCenter)
            lab.setWordWrap(True)
            color = PALETTE['primary_dark'] if bold else PALETTE['text']
            weight = 'bold' if bold else 'normal'
            lab.setStyleSheet(
                f"font-size: {size}px; color: {color}; font-weight: {weight}; "
                "padding: 3px 0;"
            )
            v.addWidget(lab)

        v.addSpacing(14)
        v.addWidget(self._sep())
        v.addSpacing(14)

        copy = QLabel('© 2026 Kiwicat.')
        copy.setAlignment(Qt.AlignCenter)
        copy.setStyleSheet(
            f"font-size: 11px; color: {PALETTE['text_soft']};"
        )
        v.addWidget(copy)

    def _sep(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(
            f"background-color: {PALETTE['border_light']}; "
            f"color: {PALETTE['border_light']}; "
            "max-height: 1px;"
        )
        return line

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, '_btn_close'):
            container = self._btn_close.parentWidget()
            if container is not None:
                self._btn_close.move(container.width() - 40, 10)

    def showEvent(self, e):
        super().showEvent(e)
        if hasattr(self, '_btn_close'):
            container = self._btn_close.parentWidget()
            if container is not None:
                self._btn_close.move(container.width() - 40, 10)
                self._btn_close.raise_()

    # 프레임 없는 다이얼로그라 직접 드래그 처리
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_offset = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if self._drag_offset is not None and (e.buttons() & Qt.LeftButton):
            self.move(e.globalPosition().toPoint() - self._drag_offset)
            e.accept()

    def mouseReleaseEvent(self, e):
        self._drag_offset = None


def _build_panel_qss():
    p = PALETTE
    return f"""
    QMainWindow, QDialog {{
        background-color: {p['bg']};
        font-family: '{APP_FONT_FAMILY}', '맑은 고딕', sans-serif;
        color: {p['text']};
    }}
    QWidget {{
        font-family: '{APP_FONT_FAMILY}', '맑은 고딕', sans-serif;
        color: {p['text']};
    }}
    QGroupBox {{
        background-color: {p['bg_soft']};
        border: 1px solid {p['border_light']};
        border-radius: 10px;
        margin-top: 14px;
        padding: 14px 12px 10px 12px;
        font-size: 11px;
        color: {p['primary_dark']};
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 14px;
        padding: 3px 12px;
        background-color: {p['bg']};
        color: {p['primary_dark']};
        border: 1px solid {p['border']};
        border-radius: 9px;
    }}
    QLabel {{ color: {p['text']}; background: transparent; }}
    QLineEdit {{
        background-color: white;
        border: 1px solid {p['border_light']};
        border-radius: 8px;
        padding: 6px 10px;
        selection-background-color: {p['primary']};
        selection-color: white;
    }}
    QLineEdit:focus {{ border: 1.5px solid {p['primary']}; }}
    QPushButton {{
        background-color: {p['primary']};
        color: white;
        border: none;
        border-radius: 9px;
        padding: 7px 16px;
        font-weight: bold;
    }}
    QPushButton:hover {{ background-color: {p['primary_dark']}; }}
    QPushButton:pressed {{ background-color: {p['text']}; }}
    QPushButton#secondary {{
        background-color: {p['bg_hover']};
        color: {p['primary_dark']};
        border: 1px solid {p['border']};
    }}
    QPushButton#secondary:hover {{ background-color: {p['border_light']}; }}
    QPushButton#danger {{ background-color: {p['accent']}; }}
    QPushButton#danger:hover {{ background-color: #BE6F75; }}
    QCheckBox, QRadioButton {{ spacing: 6px; color: {p['text']}; }}
    QCheckBox::indicator, QRadioButton::indicator {{ width: 16px; height: 16px; }}
    QCheckBox::indicator {{
        width: 16px; height: 16px;
        border-radius: 4px;
    }}
    QCheckBox::indicator:unchecked {{
        border: 1.5px solid {p['border']};
        background-color: white;
    }}
    QCheckBox::indicator:hover {{ border: 1.5px solid {p['primary']}; }}
    QCheckBox::indicator:checked {{
        border: 1.5px solid {p['primary_dark']};
        background-color: {p['primary']};
        image: url("data:image/svg+xml;utf8,<svg/>");
    }}
    QRadioButton::indicator {{
        width: 16px; height: 16px;
        border-radius: 8px;
    }}
    QRadioButton::indicator:unchecked {{
        border: 1.5px solid {p['border']};
        background-color: white;
    }}
    QRadioButton::indicator:hover {{ border: 1.5px solid {p['primary']}; }}
    QRadioButton::indicator:checked {{
        border: 1.5px solid {p['primary_dark']};
        background-color: {p['primary']};
        image: url("data:image/svg+xml;utf8,<svg/>");
    }}
    QSlider::groove:horizontal {{
        height: 6px; border-radius: 3px;
        background: {p['border_light']};
    }}
    QSlider::sub-page:horizontal {{
        background: {p['primary']};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: white;
        border: 1.5px solid {p['primary']};
        width: 14px; height: 14px;
        margin: -5px 0;
        border-radius: 8px;
    }}
    QSlider::handle:horizontal:hover {{ background: {p['bg_soft']}; }}
    QMenu {{
        background-color: white;
        border: 1px solid {p['border_light']};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 16px;
        border-radius: 5px;
        color: {p['text']};
    }}
    QMenu::item:selected {{
        background-color: {p['bg_hover']};
        color: {p['primary_dark']};
    }}
    QMenu::separator {{ height: 1px; background: {p['border_light']}; margin: 4px 6px; }}
    QScrollArea#panelScroll {{ background: transparent; border: none; }}
    QScrollBar:vertical {{
        background: transparent; width: 10px; margin: 4px 2px 4px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {p['border']}; border-radius: 4px; min-height: 40px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {p['primary']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
    """


class ControlPanel(QMainWindow):
    config_changed = Signal(dict)
    quit_requested = Signal()
    clear_fur_requested = Signal()
    language_changed = Signal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle(_panel_title())
        self.resize(500, 700)
        self.setWindowIcon(get_app_icon())
        self.setStyleSheet(_build_panel_qss())
        # save_config 디바운스: 슬라이더/대사 빠른 변경 시 매 이벤트마다 디스크
        # 쓰기를 피하려고 300ms 디바운스. config_changed 시그널은 즉시 발화해
        # 펫 UI 반영은 즉시 + 디스크 쓰기만 모아서. 패널 close/앱 quit 시 flush.
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(300)
        self._save_timer.timeout.connect(self._flush_save)
        self._building = True
        self._build_ui()
        self._building = False
        self._fitted = False

    def showEvent(self, event):
        # 첫 표시 때 1회만: show()가 스타일을 적용(polish)한 뒤라 내용 높이가 정확하다
        if not self._fitted:
            self._fitted = True
            self._fit_to_screen()
        super().showEvent(event)

    def _fit_to_screen(self):
        """내용 전체 높이로 열되, 모니터 작업 영역보다 크면 그 높이로 줄이고
        커서가 있는 화면 가운데에 배치 (넘치는 부분은 스크롤)."""
        scr = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        avail = scr.availableGeometry()
        title_h = 40  # 창 제목 표시줄 + 테두리 여유
        sc = self.centralWidget()
        content = sc.widget()
        h = min(content.sizeHint().height(), avail.height() - title_h)
        need_sb = content.sizeHint().height() > h
        self._update_min_width(need_sb)
        # 예전처럼 최소 500px 폭, 내용이 더 넓으면 내용 폭 (스크롤바 생기면 그만큼 더)
        w = max(500, sc.minimumWidth())
        self.resize(w, h)
        self.move(avail.x() + (avail.width() - w) // 2,
                  avail.y() + max(0, (avail.height() - h - title_h) // 2))

    def _update_min_width(self, need_sb=None):
        """가로 스크롤을 끄므로 창 폭이 내용 최소폭(+세로 스크롤바 폭) 밑으로 못 줄게 한다.
        스타일 적용(polish) 후 값이 정확해서 표시 시점/스크롤 범위 변경 때마다 다시 잰다."""
        sc = self.centralWidget()
        if not isinstance(sc, QScrollArea) or sc.widget() is None:
            return
        sb = sc.verticalScrollBar()
        if need_sb is None:
            need_sb = sb.maximum() > 0
        sb_w = sb.sizeHint().width() if need_sb else 0
        sc.setMinimumWidth(sc.widget().minimumSizeHint().width() + sb_w)

    def _flush_save(self):
        """pending된 save_config을 즉시 실행 (timer timeout 또는 외부에서 강제 flush)."""
        if self._save_timer.isActive():
            self._save_timer.stop()
        save_config(self.config)

    def closeEvent(self, event):
        # 트레이로 숨김 — pending save가 있으면 손실 방지를 위해 flush
        if self._save_timer.isActive():
            self._flush_save()
        event.ignore()
        self.hide()

    def nativeEvent(self, eventType, message):
        # 두 번째 인스턴스가 broadcast한 'show panel' 메시지를 받으면
        # 자기 패널을 다시 띄운다.
        # 주의: x64에서 c_uint[7] 캐스팅 + msg[1]은 HWND 상위 32비트를 읽기 때문에
        # 절대로 _SHOW_PANEL_MSG_ID와 매칭되지 않는다. wintypes.MSG로 정확히 캐스팅.
        # PySide6 환경에서 message 인자는 보통 int(주소)지만, 일부 버전에서는
        # PyCapsule/voidptr-like일 수 있어 두 경로 모두 시도한다.
        if sys.platform == 'win32' and _SHOW_PANEL_MSG_ID:
            try:
                import ctypes
                from ctypes import wintypes
                ptr = None
                try:
                    ptr = int(message)
                except (TypeError, ValueError):
                    try:
                        import shiboken6
                        ptr = shiboken6.getCppPointer(message)[0]
                    except Exception:
                        ptr = None
                if ptr:
                    msg = ctypes.cast(ptr, ctypes.POINTER(wintypes.MSG)).contents
                    if msg.message == _SHOW_PANEL_MSG_ID:
                        self.show()
                        self.raise_()
                        self.activateWindow()
            except Exception:
                pass
        return False, 0

    def _build_ui(self):
        # 내용이 모니터 세로보다 길 수 있어 스크롤 영역으로 감싼다.
        # (예전엔 내용 높이가 곧 창 최소 높이라 작은 화면에서 아래가 잘리고 줄일 수도 없었음)
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title_row = QHBoxLayout()
        title = QLabel(_app_name_with_suffix())
        title.setStyleSheet(
            f"font-size:18px; font-weight:bold; color:{PALETTE['primary_dark']};"
        )
        title_row.addWidget(title)
        title_row.addStretch(1)
        btn_lang = QPushButton(f"{t('language')} ({_CURRENT_LANG})")
        btn_lang.setObjectName('secondary')
        btn_lang.setMinimumWidth(96)
        btn_lang.setStyleSheet('padding: 7px 14px;')
        btn_lang.clicked.connect(self._show_language)
        title_row.addWidget(btn_lang)
        btn_info = QPushButton(t('info'))
        btn_info.setObjectName('secondary')
        btn_info.setMinimumWidth(80)
        btn_info.setStyleSheet('padding: 7px 22px;')
        btn_info.clicked.connect(self._show_credits)
        title_row.addWidget(btn_info)
        root.addLayout(title_row)
        sub = QLabel(t('subtitle'))
        sub.setStyleSheet(f"color:{PALETTE['text_soft']}; font-size: 11px;")
        root.addWidget(sub)

        # 캐릭터 선택
        gb_chars = QGroupBox(t('group_chars'))
        cl = QGridLayout(gb_chars)
        cl.setHorizontalSpacing(14)
        cl.setVerticalSpacing(6)
        self.char_checks = []
        self.char_thumbs = []
        self.char_scale_sliders = []
        self.char_scale_labels = []
        self.char_color_btns = []
        self.char_motion_combos = []
        enabled = self.config.get('enabled', DEFAULT_CONFIG['enabled'])
        scales = self.config.get('scales', DEFAULT_CONFIG['scales'])
        fur_colors = self.config.get('fur_colors', DEFAULT_CONFIG['fur_colors'])
        idle_motions = self.config.get('idle_motions', DEFAULT_CONFIG['idle_motions'])
        char_count = TRIAL_MAX_CHARS if TRIAL_MODE else 3
        for i in range(char_count):
            thumb = QLabel()
            thumb.setAlignment(Qt.AlignCenter)
            thumb.setFixedSize(80, 80)
            thumb.setStyleSheet(
                f"border:1px solid {PALETTE['border_light']}; "
                f"border-radius:8px; background:white;"
            )
            self.char_thumbs.append(thumb)
            self._refresh_thumb(i)
            cb = QCheckBox(t('char_n', n=i + 1))
            cb.setChecked(bool(enabled[i]) if i < len(enabled) else False)
            cb.toggled.connect(self._on_enabled_changed)
            self.char_checks.append(cb)
            edit_btn = QPushButton(t('edit_image'))
            edit_btn.setObjectName('secondary')
            edit_btn.setStyleSheet('padding: 7px 18px;')
            edit_btn.clicked.connect(lambda _, idx=i: self._edit_char_image(idx))
            # edit_btn 폭은 그룹 폭과 같게 → 모든 행이 같은 좌우 끝 정렬

            # 컨트롤 폭 통일: 털 색 박스 = 움직임 콤보박스
            # 영문/일문 라벨("Fur color", "Motion", "Change Image", "毛色", "動き", "画像変更")이
            # 잘리지 않도록 LABEL_W·GROUP_W를 넉넉히 키운다.
            CTRL_W = 88
            LABEL_W = 56
            ROW_SPACING = 4
            # 세 그룹 모두 같은 폭으로 고정 → 그리드 셀에서 AlignCenter로 좌측 끝 일치.
            GROUP_W = LABEL_W + ROW_SPACING + CTRL_W  # 148
            edit_btn.setFixedWidth(GROUP_W)

            # 캐릭터별 크기 슬라이더 (바 + 퍼센트)
            # 슬라이더 위젯 좌측 = 털 색 라벨 좌측, 퍼센트 우측 끝 = 색상 박스 우측 끝.
            scale_row = QHBoxLayout()
            scale_row.setContentsMargins(0, 0, 0, 0)
            scale_row.setSpacing(ROW_SPACING)
            sval = int(scales[i]) if i < len(scales) else 100
            slider = QSlider(Qt.Horizontal)
            slider.setRange(40, 200)
            slider.setSingleStep(10)
            slider.setPageStep(10)
            slider.setTickInterval(10)
            SLAB_W = 34  # "200%" 세자릿수+% 우측 정렬 기준 (Galmuri11 11px 4글자 잘림 방지)
            slider.setValue(sval)
            # 슬라이더 폭 = 그룹 전체 폭 - 퍼센트 라벨 폭 - spacing
            # → 슬라이더 좌측 = 색상 라벨 좌측 / 퍼센트 우측 끝 = 색상 박스 우측 끝
            slider.setFixedWidth(GROUP_W - ROW_SPACING - SLAB_W)
            slider.valueChanged.connect(lambda v, idx=i: self._on_char_scale_changed(idx, v))
            self.char_scale_sliders.append(slider)
            # 퍼센트 라벨: 우측 정렬로 색상 박스 우측 끝과 맞춤
            slab = QLabel(f'{sval}%')
            slab.setStyleSheet(
                f"color:{PALETTE['text_soft']}; font-size:11px; background:transparent;"
            )
            slab.setFixedWidth(SLAB_W)
            slab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.char_scale_labels.append(slab)
            scale_row.addWidget(slider)
            scale_row.addWidget(slab)
            scale_wrap = QWidget()
            scale_wrap.setContentsMargins(0, 0, 0, 0)
            scale_wrap.setLayout(scale_row)
            scale_wrap.setFixedWidth(GROUP_W)

            # 캐릭터별 털 색상 (왼쪽 정렬)
            color_row = QHBoxLayout()
            color_row.setContentsMargins(0, 0, 0, 0)
            color_row.setSpacing(4)
            color_lab = QLabel(t('fur_color_label'))
            color_lab.setStyleSheet(
                f"color:{PALETTE['text_soft']}; font-size:11px; background:transparent;"
            )
            color_lab.setFixedWidth(LABEL_W)
            ccol = (fur_colors[i] if i < len(fur_colors) else '#7BAFA0') or '#7BAFA0'
            color_btn = ColorButton(ccol)
            color_btn.setFixedSize(CTRL_W, 26)
            color_btn.color_changed.connect(lambda hx, idx=i: self._on_char_color_changed(idx, hx))
            self.char_color_btns.append(color_btn)
            color_row.addWidget(color_lab)
            color_row.addWidget(color_btn)
            color_wrap = QWidget()
            color_wrap.setContentsMargins(0, 0, 0, 0)
            color_wrap.setLayout(color_row)
            color_wrap.setFixedWidth(GROUP_W)

            # 캐릭터별 움직임 (왼쪽 정렬)
            motion_row = QHBoxLayout()
            motion_row.setContentsMargins(0, 0, 0, 0)
            motion_row.setSpacing(4)
            motion_lab = QLabel(t('motion_label'))
            motion_lab.setStyleSheet(
                f"color:{PALETTE['text_soft']}; font-size:11px; background:transparent;"
            )
            motion_lab.setFixedWidth(LABEL_W)
            combo = ArrowComboBox()
            combo.addItem(t('motion_jump'), 'jump')
            combo.addItem(t('motion_sway'), 'sway')
            combo.addItem(t('motion_none'), 'none')
            cur_motion = idle_motions[i] if i < len(idle_motions) else 'jump'
            for j in range(combo.count()):
                if combo.itemData(j) == cur_motion:
                    combo.setCurrentIndex(j)
                    break
            combo.setFixedSize(CTRL_W, 26)
            combo.setStyleSheet(f"""
                QComboBox {{
                    background-color: white;
                    border: 1px solid {PALETTE['border_light']};
                    border-radius: 6px;
                    padding: 3px 16px 3px 5px;
                    color: {PALETTE['text']};
                }}
                QComboBox:hover {{ border: 1px solid {PALETTE['primary']}; }}
                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 14px;
                    border-left: 1px solid {PALETTE['border_light']};
                    background: {PALETTE['bg_soft']};
                    border-top-right-radius: 6px;
                    border-bottom-right-radius: 6px;
                }}
                QComboBox:hover::drop-down {{
                    background: {PALETTE['bg_hover']};
                    border-left: 1px solid {PALETTE['primary']};
                }}
                QComboBox::down-arrow {{
                    image: none;
                    width: 0; height: 0;
                }}
                QComboBox QAbstractItemView {{
                    background: white;
                    border: 1px solid {PALETTE['border_light']};
                    selection-background-color: {PALETTE['bg_hover']};
                    selection-color: {PALETTE['primary_dark']};
                }}
            """)
            combo.currentIndexChanged.connect(
                lambda _, idx=i, c=combo: self._on_char_motion_changed(idx, c.currentData())
            )
            self.char_motion_combos.append(combo)
            motion_row.addWidget(motion_lab)
            motion_row.addWidget(combo)
            motion_wrap = QWidget()
            motion_wrap.setContentsMargins(0, 0, 0, 0)
            motion_wrap.setLayout(motion_row)
            motion_wrap.setFixedWidth(GROUP_W)

            col = i * 2  # 짝수 column에 카드, 홀수 column에 구분선
            cl.addWidget(thumb, 0, col, Qt.AlignCenter)
            cl.addWidget(cb, 1, col, Qt.AlignCenter)
            cl.addWidget(edit_btn, 2, col, Qt.AlignCenter)
            cl.addWidget(scale_wrap, 3, col, Qt.AlignCenter)
            cl.addWidget(color_wrap, 4, col, Qt.AlignCenter)
            cl.addWidget(motion_wrap, 5, col, Qt.AlignCenter)
        # 캐릭터 카드 사이 세로 구분선 (체험판은 1장이라 구분선 불필요)
        if char_count > 1:
            sep_cols = [c * 2 + 1 for c in range(char_count - 1)]
            for sep_col in sep_cols:
                cl.addWidget(CardSeparator(), 0, sep_col, 6, 1)
        if TRIAL_MODE:
            badge = QLabel(t('trial_badge'))
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet(
                f"color:{PALETTE['primary_dark']}; font-size:11px; "
                f"background:{PALETTE['bg_hover']}; "
                f"border:1px solid {PALETTE['border_light']}; "
                f"border-radius:8px; padding:6px 10px;"
            )
            cl.addWidget(badge, 6, 0, 1, max(1, char_count * 2 - 1))
        root.addWidget(gb_chars)

        # 대사 — 캐릭터별 (한 줄당 한 대사, 쓰다듬으면 그중 하나가 랜덤으로 뜸)
        gb_dialog = QGroupBox(t('group_dialog'))
        dl = QVBoxLayout(gb_dialog)
        hint = QLabel(t('dialog_hint'))
        hint.setStyleSheet(
            f"color:{PALETTE['text_soft']}; font-size:11px; background:transparent;"
        )
        dl.addWidget(hint)
        edit_qss = f"""
            QPlainTextEdit {{
                background-color: white;
                border: 1px solid {PALETTE['border_light']};
                border-radius: 8px;
                padding: 6px 8px;
                color: {PALETTE['text']};
                font-family: '{APP_FONT_FAMILY}', '맑은 고딕', sans-serif;
                selection-background-color: {PALETTE['primary']};
                selection-color: white;
            }}
            QPlainTextEdit:focus {{ border: 1.5px solid {PALETTE['primary']}; }}
        """
        self.dialog_edits = []
        per_char = self.config.get('dialogs_per_char', DEFAULT_CONFIG['dialogs_per_char'])
        for i in range(char_count):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(6)
            lab = QLabel(t('dialog_n', n=i + 1))
            lab.setFixedWidth(28)
            lab.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            lab.setStyleSheet(
                f"color:{PALETTE['primary_dark']}; font-weight:bold; "
                f"background:transparent; padding-top:6px;"
            )
            slot = per_char[i] if i < len(per_char) else list(_DEFAULT_DIALOG_LINES)
            edit = QPlainTextEdit('\n'.join(slot))
            edit.setPlaceholderText(t('dialog_placeholder'))
            edit.setFixedHeight(60)
            edit.setStyleSheet(edit_qss)
            edit.textChanged.connect(lambda idx=i: self._on_dialog_changed(idx))
            self.dialog_edits.append(edit)
            row.addWidget(lab)
            row.addWidget(edit, 1)
            dl.addLayout(row)
        root.addWidget(gb_dialog)

        # 털 옵션 (색상은 캐릭터 카드별 버튼으로 분리)
        gb_fur = QGroupBox(t('group_fur'))
        fl = QVBoxLayout(gb_fur)
        ff = QHBoxLayout()
        ff.addWidget(QLabel(t('fur_action')))
        self.fur_persist_radio = QRadioButton(t('fur_keep'))
        self.fur_fade_radio = QRadioButton(t('fur_fade'))
        if self.config.get('fur_persistent', False):
            self.fur_persist_radio.setChecked(True)
        else:
            self.fur_fade_radio.setChecked(True)
        bg_fur = QButtonGroup(self)
        bg_fur.addButton(self.fur_persist_radio)
        bg_fur.addButton(self.fur_fade_radio)
        self.fur_persist_radio.toggled.connect(self._on_fur_persist_changed)
        ff.addWidget(self.fur_fade_radio)
        ff.addWidget(self.fur_persist_radio)
        ff.addStretch(1)
        fl.addLayout(ff)
        root.addWidget(gb_fur)

        # PNG 위치 (배경/최상단)
        gb_layer = QGroupBox(t('group_layer'))
        ll = QHBoxLayout(gb_layer)
        self.layer_top = QRadioButton(t('layer_top'))
        self.layer_bottom = QRadioButton(t('layer_bottom'))
        if self.config.get('layer', 'top') == 'bottom':
            self.layer_bottom.setChecked(True)
        else:
            self.layer_top.setChecked(True)
        bg_layer = QButtonGroup(self)
        bg_layer.addButton(self.layer_top)
        bg_layer.addButton(self.layer_bottom)
        self.layer_top.toggled.connect(self._on_layer_changed)
        self.layer_bottom.toggled.connect(self._on_layer_changed)
        ll.addWidget(self.layer_top)
        ll.addWidget(self.layer_bottom)
        ll.addStretch(1)
        root.addWidget(gb_layer)

        # 추가 동작 (캐릭터별 움직임은 위 카드에서, 여기는 화면 돌아다니기 등 공통)
        gb_motion = QGroupBox(t('group_motion'))
        ml = QVBoxLayout(gb_motion)
        self.wander_check = QCheckBox(t('wander'))
        self.wander_check.setChecked(bool(self.config.get('wander', False)))
        self.wander_check.toggled.connect(self._on_wander_changed)
        ml.addWidget(self.wander_check)
        root.addWidget(gb_motion)

        # 도움말
        help_box = QFrame()
        help_box.setStyleSheet(
            f"background:{PALETTE['bg_hover']}; "
            "border: none; "
            "border-radius:10px;"
        )
        hb = QVBoxLayout(help_box)
        hb.setContentsMargins(14, 12, 14, 12)
        hb.setSpacing(4)
        bullet_lines = [
            t('help_1'),
            t('help_2'),
            t('help_3'),
            t('help_4'),
        ]
        for line in bullet_lines:
            lab = QLabel(line)
            lab.setStyleSheet(
                f"background:transparent; border:none; "
                f"color:{PALETTE['text_soft']}; font-size:11px;"
            )
            hb.addWidget(lab)
        # 이미지 변경 보충
        img_indent = QLabel(t('help_img_indent'))
        img_indent.setStyleSheet(
            f"background:transparent; border:none; "
            f"color:{PALETTE['text_soft']}; font-size:11px; "
            "padding-left:14px;"
        )
        hb.addWidget(img_indent)
        # 트레이 안내
        tray_lab = QLabel(t('help_tray'))
        tray_lab.setStyleSheet(
            f"background:transparent; border:none; "
            f"color:{PALETTE['text_soft']}; font-size:11px;"
        )
        hb.addWidget(tray_lab)
        # 트레이 보충 (들여쓰기, 구분점 없음)
        indent_lab = QLabel(t('help_tray_indent'))
        indent_lab.setStyleSheet(
            f"background:transparent; border:none; "
            f"color:{PALETTE['text_soft']}; font-size:11px; "
            "padding-left:14px;"
        )
        hb.addWidget(indent_lab)
        root.addWidget(help_box)

        root.addStretch(1)

        bl = QHBoxLayout()
        btn_clear = QPushButton(t('btn_clear_fur'))
        btn_clear.setObjectName('secondary')
        btn_clear.clicked.connect(self.clear_fur_requested.emit)
        bl.addWidget(btn_clear)
        bl.addStretch(1)
        btn_quit = QPushButton(t('btn_quit'))
        btn_quit.setObjectName('danger')
        btn_quit.clicked.connect(self.quit_requested.emit)
        bl.addWidget(btn_quit)
        root.addLayout(bl)

        scroll = QScrollArea()
        scroll.setObjectName('panelScroll')
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(central)
        scroll.viewport().setAutoFillBackground(False)
        central.setAutoFillBackground(False)
        self.setCentralWidget(scroll)
        # 세로 스크롤바가 생기거나 사라질 때 그 폭만큼 최소폭 조정 (내용 잘림 방지)
        scroll.verticalScrollBar().rangeChanged.connect(lambda *_: self._update_min_width())
        # 휠로 스크롤하다 슬라이더/콤보 위를 지나가도 값이 바뀌지 않게 (클릭해 포커스 잡은 경우만 휠 허용)
        for w in central.findChildren(QSlider) + central.findChildren(QComboBox):
            w.setFocusPolicy(Qt.StrongFocus)
            w.installEventFilter(self)

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Wheel and isinstance(obj, (QSlider, QComboBox))
                and not obj.hasFocus()):
            sc = self.centralWidget()
            if isinstance(sc, QScrollArea):
                QApplication.sendEvent(sc.verticalScrollBar(), event)
            return True
        return super().eventFilter(obj, event)

    def _show_credits(self):
        dlg = CreditsDialog(self)
        dlg.exec()
        dlg.deleteLater()

    def _show_language(self):
        dlg = LanguageDialog(self, current=_CURRENT_LANG)
        accepted = dlg.exec() == QDialog.Accepted
        new_lang = dlg.selected_lang() if accepted else None
        dlg.deleteLater()
        if not accepted or not new_lang or new_lang == _CURRENT_LANG:
            return
        set_lang(new_lang)
        self.config['language'] = new_lang
        save_config(self.config)
        self.retranslate_ui()
        self.language_changed.emit(new_lang)

    def retranslate_ui(self):
        # 언어 변경 시 패널 전체를 같은 config로 다시 빌드. state는 self.config에 있어
        # 이미지·체크상태·슬라이더값은 그대로 복원된다.
        self._building = True
        old = self.centralWidget()
        if old is not None:
            old.setParent(None)
            old.deleteLater()
        w0 = self.width()
        was_full = isinstance(old, QScrollArea) and old.verticalScrollBar().maximum() == 0
        self.setWindowTitle(_panel_title())
        self._build_ui()
        self._building = False
        # 새 위젯은 스타일 적용 후에야 크기가 정확 → 다음 이벤트 사이클에서 재계산.
        # 재빌드 중 스크롤바가 잠깐 생겼다 사라지며 넓어진 폭은 원래 폭으로 되돌리고,
        # 전환 전에 전체가 보이던 창이면 언어별 내용 높이 차이만큼 높이도 맞춘다.
        def _settle():
            h = self.height()
            if was_full:
                avail = self.screen().availableGeometry()
                h = min(self.centralWidget().widget().sizeHint().height(), avail.height() - 40)
            self._update_min_width(self.centralWidget().widget().sizeHint().height() > h)
            self.resize(max(w0, self.minimumSizeHint().width()), h)
        QTimer.singleShot(0, _settle)

    # 핸들러
    def _emit(self):
        if self._building:
            return
        # 디스크 쓰기는 300ms 디바운스 (빠른 슬라이더/대사 변경 시 I/O 폭주 방지).
        # 펫 UI 반영용 시그널은 즉시 발화 — 사용자 체감 즉시성 유지.
        self._save_timer.start()
        self.config_changed.emit(self.config)

    def _on_enabled_changed(self, _):
        new_enabled = [cb.isChecked() for cb in self.char_checks]
        # 체험판: 패널이 1번 카드만 노출하지만, 저장 시 3-슬롯으로 패딩하고
        # 정원 초과는 강제 False로 막는다.
        while len(new_enabled) < 3:
            new_enabled.append(False)
        self.config['enabled'] = new_enabled
        if TRIAL_MODE:
            _enforce_trial_limits(self.config)
        self._emit()

    def _on_char_scale_changed(self, idx, v):
        # 10% 단위로 스냅
        snapped = int(round(v / 10.0) * 10)
        snapped = max(40, min(200, snapped))
        slider = self.char_scale_sliders[idx]
        if slider.value() != snapped:
            slider.blockSignals(True)
            slider.setValue(snapped)
            slider.blockSignals(False)
        self.char_scale_labels[idx].setText(f'{snapped}%')
        scales = list(self.config.get('scales') or [100, 100, 100])
        while len(scales) <= idx:
            scales.append(100)
        if scales[idx] == snapped:
            return
        scales[idx] = snapped
        self.config['scales'] = scales
        self._emit()

    def _on_dialog_changed(self, idx):
        raw = self.dialog_edits[idx].toPlainText()
        lines = [s.strip() for s in raw.splitlines() if s.strip()]
        per_char = list(self.config.get('dialogs_per_char') or [])
        while len(per_char) < 3:
            per_char.append(list(_DEFAULT_DIALOG_LINES))
        per_char[idx] = lines
        self.config['dialogs_per_char'] = per_char
        self._emit()

    def _refresh_thumb(self, i):
        thumb = self.char_thumbs[i]
        pm = QPixmap(get_png_path(i + 1))
        if not pm.isNull():
            pm = pm.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            thumb.setPixmap(pm)
            thumb.setText('')
        else:
            thumb.clear()
            thumb.setText(t('thumb_none'))

    def _edit_char_image(self, index):
        path, _ = QFileDialog.getOpenFileName(
            self,
            t('fd_select_char_image', n=index + 1),
            os.path.expanduser('~'),
            t('fd_image_filter'),
        )
        if not path:
            return
        pm = QPixmap(path)
        if pm.isNull():
            QMessageBox.warning(self, t('msg_image_error_title'), t('msg_image_error_body'))
            return
        target = os.path.join(EXTERNAL_DIR, f'{index + 1}.png')
        try:
            if path.lower().endswith('.png'):
                shutil.copyfile(path, target)
            else:
                pm.save(target, 'PNG')
        except Exception as e:
            QMessageBox.warning(self, t('msg_save_failed_title'),
                                t('msg_save_failed_body', e=e))
            return
        self._refresh_thumb(index)
        if not self._building:
            # 펫에 즉시 반영하도록 시그널을 한번 쏘면 FurcatApp이 reload_config + 이미지 갱신
            self.config_changed.emit(self.config)

    def _on_char_color_changed(self, idx, hex_str):
        colors = list(self.config.get('fur_colors') or ['#7BAFA0'] * 3)
        while len(colors) <= idx:
            colors.append('#7BAFA0')
        colors[idx] = hex_str
        self.config['fur_colors'] = colors
        self._emit()

    def _on_fur_persist_changed(self, checked):
        self.config['fur_persistent'] = bool(self.fur_persist_radio.isChecked())
        self._emit()

    def _on_char_motion_changed(self, idx, motion):
        motions = list(self.config.get('idle_motions') or ['jump'] * 3)
        while len(motions) <= idx:
            motions.append('jump')
        motions[idx] = motion or 'jump'
        self.config['idle_motions'] = motions
        self._emit()

    def _on_wander_changed(self, checked):
        self.config['wander'] = bool(checked)
        self._emit()

    def _on_layer_changed(self, _):
        self.config['layer'] = 'bottom' if self.layer_bottom.isChecked() else 'top'
        self._emit()


# --------------------------------------------------------------------------
# App orchestrator
# --------------------------------------------------------------------------
class FurcatApp:
    def __init__(self, qapp):
        _diag('FurcatApp.__init__ start')
        self.qapp = qapp
        self.config = load_config()
        # ControlPanel이 self.config를 같은 딕셔너리로 공유해서
        # 시그널 도착 시 old_layer==new_layer가 되어 버린다.
        # 별도 추적 변수로 비교한다.
        self._last_layer = self.config.get('layer', 'top')
        _diag(f'config loaded: enabled={self.config.get("enabled")}, layer={self.config.get("layer")}')
        self.pets = {}
        # 펫별 FXOverlay 모델: 각 PetOverlay가 자기 화면용 FX를 직접 소유한다
        # (멀티 모니터 + DPI 불일치 환경 대응). FurcatApp은 글로벌 FX를 갖지 않음.

        self.panel = ControlPanel(self.config)
        self.panel.config_changed.connect(self._on_config_changed)
        self.panel.quit_requested.connect(self.quit)
        self.panel.clear_fur_requested.connect(self._clear_all_fur)
        self.panel.language_changed.connect(self._on_language_changed)
        _diag('panel created')

        self.tray = self._build_tray()
        _diag('tray built')

        self._sync_pets()
        _diag(f'pets synced: {list(self.pets.keys())}')
        self.panel.show()
        self.panel.raise_()
        self.panel.activateWindow()
        _diag(f'panel shown geometry={self.panel.geometry().getRect()}')

    def _build_tray(self):
        icon = get_app_icon()
        if icon.isNull():
            icon = self.qapp.style().standardIcon(self.qapp.style().SP_ComputerIcon)
        tray = QSystemTrayIcon(icon)
        tray.setToolTip(_app_name_with_suffix())
        menu = QMenu()
        act_show = menu.addAction(t('tray_open_settings'))
        act_show.triggered.connect(self._show_panel)
        act_clear = menu.addAction(t('tray_clear_fur'))
        act_clear.triggered.connect(self._clear_all_fur)
        menu.addSeparator()
        act_about = menu.addAction(t('tray_about'))
        act_about.triggered.connect(self._show_credits)
        act_lang = menu.addAction(f"{t('tray_language')} ({_CURRENT_LANG})")
        act_lang.triggered.connect(self._show_language_dialog)
        menu.addSeparator()
        act_quit = menu.addAction(t('tray_quit'))
        act_quit.triggered.connect(self.quit)
        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        tray.show()
        return tray

    def _show_language_dialog(self):
        # 패널의 핸들러로 위임 (config 갱신·signal 발화 한 곳에서 처리)
        self.panel._show_language()

    def _on_language_changed(self, _new_lang):
        # 트레이 메뉴는 t()로 한 번 만들면 다시 안 바뀌므로 통째로 다시 빌드.
        # 펫 윈도우 타이틀과 컨텍스트 메뉴는 t() 호출 시점이 우클릭이라 자동 반영.
        if self.tray:
            self.tray.hide()
            self.tray.deleteLater()
        self.tray = self._build_tray()
        for pet in self.pets.values():
            pet.setWindowTitle(t('pet_window_title', n=pet.index + 1))

    def _show_credits(self):
        dlg = CreditsDialog(self.panel)
        dlg.exec()
        dlg.deleteLater()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._show_panel()

    def _show_panel(self):
        self.panel.show()
        self.panel.raise_()
        self.panel.activateWindow()

    def _sync_pets(self):
        if TRIAL_MODE:
            _enforce_trial_limits(self.config)
        enabled = self.config.get('enabled', DEFAULT_CONFIG['enabled'])
        layer = self.config.get('layer', 'top')
        for i in range(3):
            want = bool(enabled[i]) if i < len(enabled) else False
            if want and i not in self.pets:
                pet = PetOverlay(i, self.config)
                pet.request_show_panel.connect(self._show_panel)
                pet.request_disable_self.connect(self._disable_pet)
                pet.request_quit.connect(self.quit)
                pet.request_clear_all_fur.connect(self._clear_all_fur)
                pet.show()
                self._force_z_order(pet, layer)
                _diag(f'pet[{i}] shown geom={pet.geometry().getRect()} layer={layer}')
                self.pets[i] = pet
            elif not want and i in self.pets:
                self.pets[i].close()
                self.pets[i].deleteLater()
                del self.pets[i]

        for pet in self.pets.values():
            pet.reload_config(self.config)
            self._force_z_order(pet, layer)

    def _force_z_order(self, widget, layer):
        """Win32 SetWindowPos로만 Z-order 관리.
        Qt의 WindowStaysOnTopHint/WindowStaysOnBottomHint를 안 쓰는 설계라
        Qt 플래그 토글 비대칭 문제가 없다."""
        if sys.platform != 'win32':
            if layer == 'bottom':
                widget.lower()
            else:
                widget.raise_()
            return
        # WS_EX_NOACTIVATE 플래그도 layer에 맞춰 갱신 (ex-style)
        try:
            widget._apply_taskbar_hide()
        except Exception:
            pass
        try:
            import ctypes
            u32 = ctypes.windll.user32
            hwnd = int(widget.winId())
            HWND_TOPMOST = -1
            HWND_NOTOPMOST = -2
            HWND_BOTTOM = 1
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            SWP_FRAMECHANGED = 0x0020
            f = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED
            if layer == 'bottom':
                u32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, f)
                u32.SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0, f)
            else:
                u32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, f)
                u32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, f)
        except Exception as e:
            _diag(f'_force_z_order failed: {e}')

    def _on_config_changed(self, cfg):
        # cfg는 ControlPanel이 갖고 있는 같은 딕셔너리. self.config도 같음.
        # → 별도 추적 변수와 비교.
        old_layer = self._last_layer
        self.config = cfg
        new_layer = cfg.get('layer', 'top')
        layer_changed = (new_layer != old_layer)
        self._last_layer = new_layer
        if layer_changed:
            _diag(f'layer change: {old_layer} -> {new_layer}, recreating pets')
            for i in list(self.pets.keys()):
                self.pets[i].close()
                self.pets[i].deleteLater()
                del self.pets[i]
            QApplication.processEvents()
        self._sync_pets()
        if layer_changed:
            # 각 펫의 FX(털·말풍선)도 펫과 같은 레이어로 따라가게.
            # 펫 재생성된 직후라 fx는 새 인스턴스. 추가 _reapply_layer_all에서
            # SetWindowPos로 한 번 더 보강.
            for pet in self.pets.values():
                if pet.fx is not None:
                    pet.fx.set_layer(new_layer)
            QTimer.singleShot(80, lambda L=new_layer: self._reapply_layer_all(L))
            if self.panel.isVisible():
                self.panel.raise_()
                self.panel.activateWindow()

    def _reapply_layer_all(self, layer):
        for pet in list(self.pets.values()):
            self._force_z_order(pet, layer)
            if pet.fx is not None:
                pet.fx.set_layer(layer)

    def _clear_all_fur(self):
        for pet in self.pets.values():
            if pet.fx is not None:
                pet.fx.clear_all()

    def _disable_pet(self, index):
        enabled = list(self.config.get('enabled', DEFAULT_CONFIG['enabled']))
        while len(enabled) <= index:
            enabled.append(False)
        enabled[index] = False
        self.config['enabled'] = enabled
        save_config(self.config)
        if hasattr(self.panel, 'char_checks') and index < len(self.panel.char_checks):
            self.panel.char_checks[index].blockSignals(True)
            self.panel.char_checks[index].setChecked(False)
            self.panel.char_checks[index].blockSignals(False)
        self._sync_pets()

    def quit(self):
        # pending된 디스크 쓰기 flush (300ms 디바운스 미처리 변경 손실 방지)
        if self.panel and hasattr(self.panel, '_flush_save'):
            try:
                self.panel._flush_save()
            except Exception:
                pass
        # PetOverlay.closeEvent에서 자기 FX도 같이 정리한다.
        for pet in list(self.pets.values()):
            pet.close()
            pet.deleteLater()
        self.pets.clear()
        if self.tray:
            self.tray.hide()
        self.qapp.quit()


DIAG_LOG = os.path.join(CONFIG_DIR, 'diag.log')
CRASH_LOG = os.path.join(CONFIG_DIR, 'crash.log')

# 디버그 로그 회전 임계값. 시작 시 한 번 검사 — 매 호출 검사는 비용.
# 오래 켜둘수록 무한 append 되는 것을 방지.
_LOG_MAX_BYTES = 1_000_000   # 1 MB 초과면 회전
_LOG_KEEP_BYTES = 200_000    # 끝에서 200 KB만 보존 (최근 이벤트 디버깅용)


def _rotate_log(path):
    """파일이 _LOG_MAX_BYTES 초과면 끝 _LOG_KEEP_BYTES 분량만 남기고 앞을 버림.
    임의 위치라 첫 줄이 잘릴 수 있어 첫 개행 다음부터 보존. 실패해도 앱은 정상 진행."""
    try:
        if not os.path.exists(path):
            return
        if os.path.getsize(path) <= _LOG_MAX_BYTES:
            return
        with open(path, 'rb') as f:
            f.seek(-_LOG_KEEP_BYTES, os.SEEK_END)
            tail = f.read()
        nl = tail.find(b'\n')
        if nl >= 0:
            tail = tail[nl + 1:]
        with open(path, 'wb') as f:
            f.write(b'--- log truncated on startup ---\n')
            f.write(tail)
    except Exception:
        pass


def _diag(msg):
    try:
        os.makedirs(os.path.dirname(DIAG_LOG), exist_ok=True)
        import datetime
        with open(DIAG_LOG, 'a', encoding='utf-8') as f:
            f.write(f'[{datetime.datetime.now().isoformat()}] {msg}\n')
    except Exception:
        pass


def _install_crash_log():
    os.makedirs(os.path.dirname(CRASH_LOG), exist_ok=True)

    def hook(exctype, value, tb):
        import traceback
        with open(CRASH_LOG, 'a', encoding='utf-8') as f:
            f.write('\n--- crash ---\n')
            traceback.print_exception(exctype, value, tb, file=f)
        try:
            sys.__excepthook__(exctype, value, tb)
        except Exception:
            pass

    sys.excepthook = hook


SHOW_PANEL_MSG_NAME = (
    'FurcatTrialShowPanel_v1' if TRIAL_MODE else 'FurcatShowPanel_v1'
)
# 세션별 단일 인스턴스라 Local\ 네임스페이스로 충분.
# Global\는 SeCreateGlobalPrivilege 필요 → 표준 사용자는 ACCESS_DENIED.
# 체험판은 별도 mutex로 정식판과 동시 실행 가능.
SINGLE_INSTANCE_MUTEX = (
    'Local\\FurcatTrialPet_SingleInstance_v1' if TRIAL_MODE
    else 'Local\\FurcatPet_SingleInstance_v1'
)

# main()에서 채워둠. 두 번째 인스턴스가 종료 직전 첫 인스턴스에 PostMessage로 신호.
_SHOW_PANEL_MSG_ID = None
_INSTANCE_MUTEX_HANDLE = None  # 프로세스 살아있는 동안 OS가 보유


def _enforce_single_instance():
    """Windows named mutex로 atomic 단일 인스턴스 보장.
    이미 실행 중이면 RegisterWindowMessage + PostMessage(HWND_BROADCAST)로
    기존 인스턴스에 '패널 표시' 신호를 쏘고 종료. mutex 생성 자체가 실패하면
    가드를 비활성화하고 정상 진행 (앱 자체가 시작 못 하는 사고 방지)."""
    global _SHOW_PANEL_MSG_ID, _INSTANCE_MUTEX_HANDLE
    if sys.platform != 'win32':
        return  # 다른 OS는 보호 생략 (현재 Windows 전용 빌드)
    try:
        import ctypes
        from ctypes import wintypes
        # use_last_error=True → ctypes.get_last_error()로 안전하게 GetLastError 취득
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        ERROR_ALREADY_EXISTS = 183
        HWND_BROADCAST = 0xFFFF

        user32.RegisterWindowMessageW.restype = wintypes.UINT
        user32.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
        user32.PostMessageW.restype = wintypes.BOOL
        user32.PostMessageW.argtypes = [
            wintypes.HWND, wintypes.UINT, ctypes.c_void_p, ctypes.c_void_p
        ]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.CreateMutexW.argtypes = [
            ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR
        ]
        kernel32.CloseHandle.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

        _SHOW_PANEL_MSG_ID = user32.RegisterWindowMessageW(SHOW_PANEL_MSG_NAME)

        h = kernel32.CreateMutexW(None, False, SINGLE_INSTANCE_MUTEX)
        last_err = ctypes.get_last_error()

        if not h:
            # mutex 생성 자체가 실패 (권한 부족 등). 단일 인스턴스 가드를
            # 비활성화하고 앱은 정상 시작시킨다.
            _diag(f'CreateMutexW failed (err={last_err}); guard disabled, continuing')
            return

        if last_err != ERROR_ALREADY_EXISTS:
            # 첫 인스턴스: mutex 핸들 보유 (프로세스 종료 시 OS가 자동 해제)
            _INSTANCE_MUTEX_HANDLE = h
            return

        # 이미 실행 중. 기존 인스턴스에 패널 표시 신호 송신 후 종료
        if _SHOW_PANEL_MSG_ID:
            user32.PostMessageW(HWND_BROADCAST, _SHOW_PANEL_MSG_ID, 0, 0)
        kernel32.CloseHandle(h)
        _diag('another instance running, signaled show-panel and exiting')
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        _diag(f'single instance guard failed: {e}')


def main():
    _install_crash_log()
    # 로그 회전 (1MB 초과 시 끝 200KB만 보존). 무한 append 방지.
    _rotate_log(DIAG_LOG)
    _rotate_log(CRASH_LOG)
    _diag(f'main() entered, frozen={getattr(sys, "frozen", False)}, exe={sys.executable}')
    _diag(f'TRIAL_MODE={TRIAL_MODE}, BASE_DIR={BASE_DIR}, EXTERNAL_DIR={EXTERNAL_DIR}, CONFIG_DIR={CONFIG_DIR}')
    _enforce_single_instance()
    # Qt6/PySide6에서는 HiDPI 스케일링/픽스맵이 항상 활성화되어 있어
    # AA_EnableHighDpiScaling, AA_UseHighDpiPixmaps는 obsolete (no-op).
    _diag('creating QApplication')
    qapp = QApplication(sys.argv)
    qapp.setQuitOnLastWindowClosed(False)
    _diag('QApplication ready')

    _load_app_font()
    # Galmuri11 아웃라인은 ppem 11px 설계. 11/22/33 같은 ppem 정수배에서
    # 안티앨리어싱 켠 채로 가장 또렷하다. NoAntialias 끄면 가는 선이 사라짐.
    base_font = QFont(APP_FONT_FAMILY)
    base_font.setPixelSize(11)
    base_font.setStyleStrategy(QFont.PreferAntialias | QFont.PreferQuality)
    base_font.setHintingPreference(QFont.PreferDefaultHinting)
    qapp.setFont(base_font)
    _diag(f'app font loaded: {APP_FONT_FAMILY}')

    _install_rainbow_standard_colors()
    _diag('rainbow standard colors installed')

    _diag('creating FurcatApp')
    # FurcatApp 인스턴스를 변수에 보관해야 한다. 안 그러면 식의 값이
    # 즉시 버려져 GC되고, self.pets/self.tray/self.panel 등 강참조가
    # 끊겨 펫의 QTimer가 멈추고 paintEvent도 안 돌아 layered 윈도우가
    # UpdateLayeredWindow를 못 받아 화면에 안 나타난다.
    _app_holder = FurcatApp(qapp)  # noqa: F841
    _diag('FurcatApp ready, entering exec()')
    rc = qapp.exec()
    _diag(f'exec() returned {rc}')
    return rc


if __name__ == '__main__':
    sys.exit(main())
