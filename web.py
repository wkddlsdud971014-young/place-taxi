# ================================================================
#  웹 서비스 - 칸을 채우고 버튼을 누르는 방식
#  켜기:  ./.venv/bin/python web.py      (주소 127.0.0.1:7870)
#
#  1번 블록(식당) 에서 고른 이름이 2번 블록(택시) 의 도착지로 넘어갑니다.
#  그것을 '이월' 이라고 부릅니다.  체크리스트 2번이 그것입니다.
# ================================================================
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="gradio")
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gradio as gr
import db

AREAS = ["상관없음", "서울 중앙", "서울 동쪽", "서울 서쪽", "서울 남쪽", "서울 북쪽"]
CATES = ["상관없음", "한식", "중식", "일식", "양식", "아시아음식"]
PRICES = ["상관없음", "저렴", "보통", "비싼"]
TYPES = ["아무거나", "일반", "모범", "대형"]


def _db(v):
    return "dontcare" if v in ("상관없음", "아무거나") else v


def _ui(v):
    return "아무거나" if v == "dontcare" else v


# ================================================================
#  1번 블록 - 식당
# ================================================================
def 식당검색(area, cate, price):
    rows = db.search_restaurants(_db(area), _db(cate), _db(price))
    if not rows:
        return gr.update(choices=[], value=None), "조건에 맞는 식당이 없습니다. 조건을 넓혀보세요."
    이름들 = [f"{r['name']} ({r['area']} · {r['category']} · {r['price']})" for r in rows]
    return gr.update(choices=이름들, value=이름들[0]), f"**{len(rows)}곳** 찾았습니다. 하나 고르세요."


def 식당예약(고른것, ride_id):
    """예약하면 그 이름이 택시 도착지로 넘어갑니다. 이것이 '이월' 입니다."""
    if not 고른것:
        return None, None, "먼저 [식당 검색] 을 눌러 하나 고르세요.", gr.update(), 목록()

    이름 = 고른것.split(" (")[0]
    가게 = db.get_restaurant(이름)
    코드 = db.make_booking_code()
    안내 = (f"### 예약 완료\n"
            f"| | |\n|---|---|\n"
            f"| 식당 | **{가게['name']}** |\n"
            f"| 위치 | {가게['area']} |\n"
            f"| 종류 | {가게['category']} · {가게['price']} |\n"
            f"| 전화 | {가게['phone']} |\n"
            f"| 예약번호 | `{코드}` |\n\n"
            f"> ↓ **도착지 칸에 자동으로 넘어갔습니다 (이월)**")

    # 이미 택시를 불러둔 상태라면 그 호출의 도착지까지 같이 고칩니다.
    # 시나리오 1-2(도착지 변경) 가 바로 이 경우입니다.
    if ride_id:
        db.update_ride(ride_id, {"dropoff": 이름, "place_name": 이름,
                                 "place_booking": 코드, "carried": True})
        안내 += "\n\n> 이미 부른 택시(호출번호 %s)의 도착지도 같이 바꿨습니다." % ride_id

    return 이름, 코드, 안내, gr.update(value=이름), 목록()


# ================================================================
#  2번 블록 - 택시
# ================================================================
def card(ride):
    if ride is None:
        return "아직 부른 택시가 없습니다."
    d = db.get_driver(ride["driver_id"])
    기사 = f"{d['name']} · {d['phone']} · {d['vehicle_type']}" if d else "배차 대기중 (맞는 기사가 없습니다)"
    이월 = "🔵 예 (식당에서 넘어옴)" if ride["carried"] else "아니오 (직접 입력)"
    return (
        f"### {ride['status']}  (호출번호 {ride['id']})\n"
        f"| | |\n|---|---|\n"
        f"| 식당 | {ride['place_name'] or '-'} |\n"
        f"| 출발지 | {ride['pickup']} |\n"
        f"| 도착지 | {ride['dropoff']} |\n"
        f"| **도착지 이월?** | **{이월}** |\n"
        f"| 출발시간 | {ride['request_time']} |\n"
        f"| 차종 | {_ui(ride['vehicle_type'])} |\n"
        f"| 기사 | {기사} |\n"
        f"| **고친 횟수** | **{ride['change_count']}회** |\n"
    )


def 목록():
    rows = db.recent_rides(10)
    return [[r["id"], r["source"], r["place_name"] or "-", r["pickup"], r["dropoff"],
             "🔵" if r["carried"] else "", r["request_time"],
             _ui(r["vehicle_type"]), r["status"], r["change_count"]] for r in rows]


def 부르기(pickup, dropoff, time, vtype, place, booking):
    if not pickup or not dropoff:
        return None, "출발지와 도착지를 채워주세요.", 목록()
    # 도착지가 고른 식당과 같으면 '손님이 치지 않고 넘어온 것' 으로 봅니다
    이월 = bool(place) and dropoff == place
    ride = db.create_ride(pickup, dropoff, time, _db(vtype), source="web",
                          place_name=place, place_booking=booking, carried=이월)
    return ride["id"], card(ride), 목록()


def 변경저장(ride_id, pickup, dropoff, time, vtype, place):
    if not ride_id:
        return "먼저 [택시 부르기] 를 눌러주세요.", 목록()
    now = db.get_ride(ride_id)
    새값 = {"pickup": pickup, "dropoff": dropoff,
            "request_time": time, "vehicle_type": _db(vtype)}
    바뀐것 = {k: v for k, v in 새값.items() if v != now[k]}
    if not 바뀐것:
        return card(now) + "\n> 바뀐 것이 없습니다.", 목록()
    # 도착지를 손으로 고쳐서 식당과 달라졌으면 이월이 깨진 것입니다
    if "dropoff" in 바뀐것:
        바뀐것["carried"] = bool(place) and 바뀐것["dropoff"] == place
    ride = db.update_ride(ride_id, 바뀐것)
    이름 = {"pickup": "출발지", "dropoff": "도착지",
            "request_time": "출발시간", "vehicle_type": "차종"}
    바뀐칸 = ", ".join(이름[k] for k in 바뀐것 if k in 이름)
    return card(ride) + f"\n> 바꾼 칸: **{바뀐칸}**", 목록()


def 기사변경(ride_id):
    if not ride_id:
        return "먼저 [택시 부르기] 를 눌러주세요.", 목록()
    return card(db.update_ride(ride_id, {}, new_driver=True)) + "\n> 다른 기사로 다시 배차했습니다.", 목록()


def 취소(ride_id):
    if not ride_id:
        return None, "취소할 호출이 없습니다.", 목록()
    db.cancel_ride(ride_id)
    return None, "취소했습니다.", 목록()


# ================================================================
#  화면
# ================================================================
with gr.Blocks(title="식당 + 택시 (웹)") as demo:
    gr.Markdown("# 🍽️ ➜ 🚕  식당 예약하고 택시 부르기 (웹)")
    현재호출 = gr.State(None)
    고른식당 = gr.State(None)
    예약번호 = gr.State(None)

    with gr.Row():
        # ---------------- 1번 블록 ----------------
        with gr.Column(scale=1):
            gr.Markdown("## 1️⃣ 식당 찾기")
            area = gr.Dropdown(AREAS, value="상관없음", label="지역")
            cate = gr.Dropdown(CATES, value="상관없음", label="종류")
            price = gr.Dropdown(PRICES, value="상관없음", label="가격대")
            검색btn = gr.Button("식당 검색")
            검색안내 = gr.Markdown("")
            결과목록 = gr.Radio([], label="검색 결과")
            예약btn = gr.Button("이 식당 예약", variant="primary")
            식당결과 = gr.Markdown("")

        # ---------------- 2번 블록 ----------------
        with gr.Column(scale=1):
            gr.Markdown("## 2️⃣ 택시 부르기")
            pickup = gr.Textbox(label="출발지", placeholder="강남역")
            dropoff = gr.Textbox(label="🔵 도착지  (식당을 예약하면 자동으로 채워집니다)")
            time = gr.Textbox(label="출발 시간", placeholder="19:00")
            # 기본값이 '아무거나' 입니다. 실제 데이터의 94% 가 이것입니다.
            vtype = gr.Radio(TYPES, value="아무거나", label="차종")
            부르기btn = gr.Button("택시 부르기", variant="primary")
            gr.Markdown("---\n**접수한 뒤 고칠 때**  위 칸을 고치고 아래를 누르세요.")
            with gr.Row():
                변경btn = gr.Button("변경 저장")
                기사btn = gr.Button("다른 기사로")
                취소btn = gr.Button("취소")
            결과 = gr.Markdown("아직 부른 택시가 없습니다.")

    gr.Markdown("### 최근 호출 (웹 · 봇 같이 보임)")
    표 = gr.Dataframe(
        headers=["번호", "어디서", "식당", "출발지", "도착지", "이월", "시간", "차종", "상태", "고친횟수"],
        value=목록, interactive=False)

    검색btn.click(식당검색, [area, cate, price], [결과목록, 검색안내])
    예약btn.click(식당예약, [결과목록, 현재호출],
                 [고른식당, 예약번호, 식당결과, dropoff, 표])
    부르기btn.click(부르기, [pickup, dropoff, time, vtype, 고른식당, 예약번호],
                   [현재호출, 결과, 표])
    변경btn.click(변경저장, [현재호출, pickup, dropoff, time, vtype, 고른식당], [결과, 표])
    기사btn.click(기사변경, [현재호출], [결과, 표])
    취소btn.click(취소, [현재호출], [현재호출, 결과, 표])

if __name__ == "__main__":
    demo.launch(server_port=7870)
