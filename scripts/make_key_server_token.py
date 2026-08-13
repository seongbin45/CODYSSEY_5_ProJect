"""KEY_SERVER_TOKEN 을 이 PC에서 만든다. 외부 사이트가 발급하지 않는다."""

import secrets

token = secrets.token_urlsafe(32)
print(token)
print()
print("위 한 줄을 아래 두 곳에 똑같이 붙이세요.")
print("1) Render Dashboard -> 이 서비스 -> Environment -> KEY_SERVER_TOKEN")
print("2) (exe를 쓸 때만) 로컬 .env 의 KEY_SERVER_TOKEN=")
print("GitHub, README, Release 에는 붙이지 마세요.")
