# `export/` — 과제 필수 아님

PyInstaller로 만든 `travel_planner.exe`가 들어가는 폴더입니다.  
Git에는 exe를 넣지 않습니다. 받으려면  
https://github.com/seongbin45/CODYSSEY_5_ProJect/releases/tag/v1.0.0

채점의 기본 경로는 루트에서:

```bat
python travel_planner.py -date "2026-03-15"
```

exe를 다시 만들 때:

```bat
pip install pyinstaller
pyinstaller --noconfirm --clean --distpath export --workpath build travel_planner.spec
```

exe는 `.env`를 묶지 않습니다 (`datas=[]`). 키는 exe 옆 `.env` 또는 `--key-server`로만 넣습니다.
