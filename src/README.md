# `src/`

과제 필수 파일만 먼저 보면 됩니다. 루트 [README.md](../README.md)의 채점 대조와 같습니다.

| 파일 | 단계 | HTTP |
|---|---|---|
| `api_llm.py` | 1단계 JSON, 3단계 Markdown | POST `generateContent` |
| `api_map.py` | 2단계 맛집 | GET Kakao keyword, `FD6` |
| `utils.py` | 날짜, `.env`, `results/` 저장 | 없음 |

CLI는 `travel_planner.py`의 `main()`이 위 함수를 직접 호출합니다.

---

## 확장 (없어도 과제 최소는 동작)

| 파일 | 언제 호출되나 |
|---|---|
| `api_tour.py` | `TOUR_API_SERVICE_KEY`가 있을 때만 |
| `api_tmap.py` | `TMAP_OPEN_API_APP_KEY`가 있을 때만 |
| `key_client.py` | `--key-server` 또는 `KEY_SERVER_URL`을 **명시한 경우만** |

웹용 `pipeline.py`와 로컬 `key_server.py`는 이 브랜치에 없습니다. `fastapi-web`에 있습니다.
