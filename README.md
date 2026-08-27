# 식당 + 택시 — 두 도메인을 잇는 하나의 서비스

같은 일을 **웹(폼)** 과 **봇(대화)** 두 가지로 만들고, 어느 쪽이 편한지 비교하는 실습입니다.

```
1️⃣ 식당 블록          2️⃣ 택시 블록
조건 → 검색 → 예약  ──▶  도착지에 자동으로 채워짐 → 배차
                        ↑
                     이월 (carry-over)
```

## 이 프로젝트의 핵심 — 이월

WoS 데이터셋의 식당+택시 대화 481건을 세어보니 **48.0%** 에서 식당 이름이 택시 도착지로 그대로 이어졌습니다.
그리고 그중 대부분은 택시를 부를 때 **식당 이름을 다시 말하지 않습니다.** "거기로 가는 택시" 라고만 합니다.

그래서 이 서비스의 원칙은 하나입니다.

> **이미 정해진 것을 손님에게 다시 입력시키지 않는다.**

`rides.carried` 칸이 그 증거입니다. 도착지를 손님이 쳤으면 `false`, 식당에서 넘어왔으면 `true` 입니다.

## 파일

| 파일 | 하는 일 |
|---|---|
| `schema.sql` | Supabase 표 3개 (restaurants / drivers / rides) |
| `db.py` | 창고 담당. **웹과 봇이 같이 씁니다** |
| `web.py` | 웹 서비스 — 칸을 채우고 버튼을 누름 (`:7870`) |
| `bot.py` | Gradio 봇 — 말로 함 (`:7871`) |
| `check_db.py` | Supabase 연결 확인 |
| `app.py`, `settings.py` | 지난주 과제 (슬롯 채우기 연습) |

## 켜는 법

```bash
python3.12 -m venv .venv
./.venv/bin/python -m pip install "gradio==5.14.0" google-generativeai python-dotenv supabase

cp .env.example .env      # 그리고 키 3개를 채웁니다
# schema.sql 을 Supabase SQL Editor 에 붙여 넣고 Run

./.venv/bin/python check_db.py   # 연결 확인
./.venv/bin/python web.py        # 웹
./.venv/bin/python bot.py        # 봇
```

파이썬은 **3.10 ~ 3.12** 여야 합니다. 3.9 에서는 gradio 5 가 깔리지 않습니다.

## 테스트 시나리오 9개

접수한 뒤 **고치는** 상황만 모았습니다. 만드는 것보다 고치는 것이 어렵습니다.

| | 케이스 1 (장소) | 케이스 2 (택시) | 케이스 3 (둘 다) |
|---|---|---|---|
| -1 | 출발지 변경 | 차량(기사) 변경 | 출발지 + 차량 |
| -2 | 도착지(식당) 변경 | 요청 시간 변경 | 도착지 + 시간 |
| -3 | 출발지·도착지 변경 | 차량 옵션 변경 | 전부 변경 |

`rides.change_count` 와 `rides.source` 칸에 결과가 자동으로 쌓입니다.

## 올리지 않은 것

- `.env` — 열쇠
- `data/` — 수업에서 받은 WoS 원본 (135MB)
- `.venv/` — 각자 다시 만들면 됩니다
