# `docs/` — 프로그램이 읽지 않는 참고 파일

여기 있는 파일은 `travel_planner.py` / `server/app.py` / `src/*.py`가 **import 하거나 open 하지 않습니다.**  
과제를 읽거나 TourAPI zip을 풀어 명세를 볼 때만 씁니다.

실행 코드는 루트의 `travel_planner.py`, `src/`, `server/`에 있습니다.

---

## 1. 무엇을 먼저 보나

과제를 처음 파악할 때:

1. 루트의 `과제조건.txt` — 원본 과제 화면을 HTML로 저장한 것
2. `과제요건_정리.md` — 그 HTML에서 본문만 뽑아 표로 정리한 것
3. 루트 [README.md](../README.md) — 지금 코드가 어떤 함수·URL을 부르는지

예전에 적어 둔 메모:

4. `implementation_plan.md` — 구현 전에 잡은 계획. 이후 코드와 다를 수 있음
5. `task.md` — 당시 작업 체크리스트
6. `API_추천_리포트.md` — 기상청·ODsay·네이버 이미지. **이 저장소에는 넣지 않기로 한** 목록

4~6과 지금 `src/`가 다르면 `src/`가 맞습니다.

---

## 2. zip 매뉴얼 (한국관광공사)

공공데이터포털에서 받은 공식 가이드입니다. 압축을 풀어 읽습니다.

| 파일 | `src/api_tour.py`가 부르는 서비스 |
|---|---|
| `개방데이터_활용매뉴얼(국문).zip` | KorService2 `searchKeyword2` |
| `TourAPI_Guide_(중심관광지)v4.1.zip` | LocgoHubTarService1 |
| `TourAPI_Guide_(연관관광지)v4.1.zip` | TarRlteTarService1 |
| `개방 데이터 활용 매뉴얼(관광지 집중률 ...)v4.1.zip` | TatsCnctrRateService |

실제 URL과 쿼리 파라미터는 `src/api_tour.py`와 [src/README.md](../src/README.md)에 있습니다.

zip은 용량이 커서 GitHub에 올리지 않는 것이 좋습니다. (`.gitignore`에 넣는 것을 권장)

---

## 3. 이 폴더에 새 자료를 넣을 때

- PDF, zip, 메모, 캡처만 둡니다.
- 실행에 필요한 `.py`는 루트 또는 `src/`, `server/`에 둡니다.
- 키가 적힌 메모는 두지 않습니다.

---

위로: [프로젝트 README](../README.md)
