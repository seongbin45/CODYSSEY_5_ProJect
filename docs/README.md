# `docs/` — 읽기 전용 참고 자료

여기 있는 파일은 **프로그램이 실행할 때 읽지 않습니다.**  
과제를 이해하거나 API 명세를 찾아볼 때 씁니다.

코드는 루트, `src/`, `server/`에 있습니다.

---

## 1. 무엇을 먼저 보나

과제를 처음 파악할 때:

1. 루트의 `과제조건.txt` — 원본 과제 화면을 HTML로 저장한 것
2. `과제요건_정리.md` — 그 HTML에서 본문만 뽑아 표로 정리한 것
3. 루트 [README.md](../README.md) — 지금 코드가 과제를 어떻게 구현했는지

구현을 따라갈 때:

4. `implementation_plan.md` — 예전에 잡은 구현 계획
5. `task.md` — 당시 작업 체크리스트
6. `API_추천_리포트.md` — 기상청·ODsay·네이버 이미지 등 **넣지 않기로 한** 확장 아이디어

---

## 2. zip 매뉴얼 (한국관광공사)

공공데이터포털에서 받은 공식 가이드입니다. 압축을 풀어 읽습니다.

| 파일 | 대응 API |
|---|---|
| `개방데이터_활용매뉴얼(국문).zip` | KorService2 공식 관광지/숙소 |
| `TourAPI_Guide_(중심관광지)v4.1.zip` | LocgoHubTarService1 |
| `TourAPI_Guide_(연관관광지)v4.1.zip` | TarRlteTarService1 |
| `개방 데이터 활용 매뉴얼(관광지 집중률 ...)v4.1.zip` | TatsCnctrRateService |

코드에서 실제로 부르는 주소와 파라미터는 `src/api_tour.py`와 [src/README.md](../src/README.md)에 정리되어 있습니다.

zip은 용량이 커서 GitHub에는 올리지 않는 것이 좋습니다.

---

## 3. 이 폴더에 새 자료를 넣을 때

- 코드가 아닌 PDF, zip, 메모, 캡처는 여기에 둡니다.
- 실행에 필요한 `.py`는 넣지 않습니다.
- 키가 적힌 메모는 넣지 않습니다.

---

위로: [프로젝트 README](../README.md)
