# `scripts/` — 이 브랜치에서만 쓰는 보조 명령

`main` 브랜치의 과제 CLI와 별개입니다.  
지금은 토큰을 만드는 파일 하나입니다.

---

## `make_key_server_token.py`

Kakao/Google/공공데이터포털은 `KEY_SERVER_TOKEN`을 주지 않습니다.  
이 파일이 `secrets.token_urlsafe(32)`로 문자열을 하나 출력합니다.

프로젝트 루트에서:

```bat
cd C:\Users\seong\Downloads\CODYSSEY_5_ProJect
python scripts\make_key_server_token.py
```

출력의 **첫 줄**이 토큰입니다. 그 줄을

1. Render → Environment → `KEY_SERVER_TOKEN`
2. exe를 쓸 때만 로컬 `.env`의 `KEY_SERVER_TOKEN=`

에 **똑같이** 붙입니다. GitHub에는 올리지 않습니다.

자세한 클릭 순서: [루트 README 1단계](../README.md)
