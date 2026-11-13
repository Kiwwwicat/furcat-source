# 털캣털캣 (FurcatFurcat) - source

데스크톱에 PNG 캐릭터를 띄우고, 클릭/드래그로 쓰다듬으면 털 입자가 흩어져 화면에 묻는 Windows 데스크톱 펫 앱의 소스 코드입니다.

이 저장소는 **코드 열람과 버그 수정 제안**을 위해 공개합니다. 실행 파일(exe)과 배포용 zip은 포함하지 않습니다.
개인적으로 고쳐 쓰는 것은 괜찮지만, 원본이나 수정본을 다른 사람에게 배포하는 것은 금지합니다 (아래 "라이선스").

현재 버전: v1.2.8

## 기능

- 캐릭터 1~3 동시 표시, 캐릭터마다 개별 설정 (이미지, 크기 40~200%, 털 색상, 움직임)
- 클릭/드래그로 쓰다듬기 -> 털 입자가 날아가 화면에 부착
- 사용자 지정 대사 (클릭마다 랜덤 표시, 말풍선 색은 털 색에 맞춰 자동 조정)
- 화면 최상단 / 배경화면 위(다른 창 아래) 배치 전환
- 화면 돌아다니기
- 한국어 / 일본어 / 영어 UI
- 트레이 상주, 단일 인스턴스
- 멀티 모니터 (DPI가 다른 모니터, 액정 타블렛 포함)

## 소스 구조

전체 로직은 `main.py` 한 파일에 있습니다.

| 구성 | 역할 |
| --- | --- |
| `TR` / `t()` | 3개 언어 UI 문자열 |
| `DEFAULT_CONFIG`, `load_config()` / `save_config()` | 설정 (`~/.furcat/config.json`) |
| `TRIAL_MODE`, `_enforce_trial_limits()` | 체험판 제한 (`TRIAL.flag` 존재 시 ON) |
| `Particle` | 털 입자 1개의 물리/그리기 |
| `FXOverlay` | 화면 전체 투명 창. 털 입자와 말풍선을 그림 (변경 영역만 다시 그림) |
| `PetOverlay` | 캐릭터 창. 쓰다듬기, 움직임, 돌아다니기 |
| `ControlPanel` | 설정 창 (화면보다 길면 스크롤) |

애니메이션은 경과 시간 기준(`dt`, 60fps = 1.0)으로 계산하므로 프레임이 떨어져도 속도는 유지됩니다.

## 실행

Windows 10/11, Python 3.12 기준 (PySide6 6.10.1에서 확인).

```
pip install -r requirements.txt
python main.py
```

설정과 로그는 `%USERPROFILE%\.furcat\` 에 저장됩니다 (`config.json`, `diag.log`, `crash.log`). 오류를 제보할 때 `diag.log`와 `crash.log` 내용을 함께 보내주시면 원인을 찾는 데 도움이 됩니다.

## 빌드 (PyInstaller onedir)

```
pip install pyinstaller
pyinstaller --clean 털캣털캣.spec
```

| spec | 결과 |
| --- | --- |
| `털캣털캣.spec` | 한국어 정식판 |
| `털캣털캣-체험판.spec` | 한국어 체험판 (`TRIAL.flag` 동봉) |
| `ファーキャットファーキャット-体験版.spec` | 일본어 체험판 |

일본어판은 빌드 전에 `main.py`의 `_CURRENT_LANG = 'KOR'`과 `DEFAULT_CONFIG`의 `'language': 'KOR'`을 `'JPN'`으로 바꿔서 빌드합니다 (처음 실행할 때의 언어만 달라집니다).

PySide6(LGPL-3.0)의 라이브러리 교체 가능 의무를 지키기 위해 onefile이 아닌 onedir로 빌드합니다.

## 오류 제보 / 수정 제안

- 버그는 Issue로 알려주세요. 증상, Windows 버전, 모니터 구성(해상도, 배율, 대수), `diag.log` / `crash.log`가 있으면 좋습니다.
- 코드 수정은 이 저장소를 fork한 뒤 Pull Request로 보내주세요.
- Pull Request를 보내면, 그 수정 내용을 저작자가 이 앱에 반영하고 배포하는 데 동의하는 것으로 봅니다.

## 라이선스

이 저장소의 코드와 캐릭터 이미지(`1.png`, `2.png`, `3.png`, 아이콘)는 © 2026 kiwwwicat. **All Rights Reserved.**

- **허용:** 코드 열람, 개인적으로 사용하기 위한 수정과 빌드, GitHub 안에서의 fork, Issue / Pull Request로 수정 제안
- **금지:** 원본이나 수정본(소스 코드, 빌드한 exe)을 다른 사람에게 배포, 업로드, 판매

자세한 내용은 `LICENSE`를 보세요. 외부 구성 요소는 각자의 라이선스를 따르며, 위 조건은 그 라이선스가 주는 권리(예: PySide6/Qt 라이브러리 교체)를 제한하지 않습니다.

포함된 외부 구성 요소:

- **PySide6 / shiboken6 / Qt** (LGPL-3.0): 저장소에는 포함하지 않고 `pip`로 설치합니다. 빌드 결과물에 동봉할 라이선스 전문은 `LGPL-3.0.txt`, `GPL-3.0.txt` (LGPL-3.0은 GPL-3.0에 추가 권한을 더한 형식). 배포본에 쓴 버전의 소스: [PySide6 6.10.1](https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.10.1-src/), [Qt 6.10.1](https://download.qt.io/official_releases/qt/6.10/6.10.1/).
- **Python** (PSF License)과 Windows용 Python에 함께 들어 있는 OpenSSL, libffi, bzip2 등: 빌드 결과물에 `Python-LICENSE.txt`를 동봉합니다.
- **Galmuri11 / Galmuri11-Bold / Galmuri11Bitmap** © 2019-2025 Lee Minseo, SIL Open Font License 1.1 (`Galmuri-OFL.txt`).

빌드할 때 spec 파일이 Qt Virtual Keyboard 관련 DLL을 뺍니다. 이 모듈은 LGPL이 아닌 GPL-3.0 전용이라, 비공개 코드와 함께 배포하면 안 되기 때문입니다 (앱에서 쓰지 않음).

## Special Thanks

- 챠 (@final_bbung)

## 제작

made by 키위캣 (@kiwwwicat)
