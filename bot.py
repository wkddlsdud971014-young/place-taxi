# ================================================================
#  Gradio 봇 - 말로 하는 방식
#  켜기:  ./.venv/bin/python bot.py      (주소 127.0.0.1:7871)
#
#  웹(web.py) 과 똑같은 일을 합니다. 창고(db.py) 도 같은 것을 씁니다.
#  다른 것은 '칸을 채우느냐' 와 '말로 하느냐' 뿐입니다.
#  (지난주 과제 app.py 는 그대로 두었습니다)
# ================================================================
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="gradio")
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import os, json, re
import gradio as gr
import google.generativeai as genai
from dotenv import load_dotenv
import db

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3.5-flash-lite")

# 봇이 채워야 하는 칸. 웹 화면의 입력칸과 똑같습니다.
식당칸 = ["지역", "종류", "가격대"]
택시칸 = ["출발지", "도착지", "출발 시간", "차종"]


def 빈상자():
    return {"식당": {}, "택시": {}, "이름": None, "예약번호": None,
            "ride_id": None, "이월": False}


# ================================================================
#  말 -> 칸  (여기가 봇의 심장입니다)
# ================================================================
def 뽑기(말, 상자):
    """손님이 친 말 한 개에서 칸을 뽑아냅니다.

    웹과 다른 점이 여기 있습니다.
    웹은 손님이 어느 칸에 넣을지 직접 고르지만,
    봇은 '어느 칸에 넣을 말인지' 를 봇이 알아내야 합니다.
    """
    # 식당이 아직 안 정해졌으면 '거기' 규칙을 아예 넣지 않습니다.
    # 넣으면 모델이 안내문("아직 안 정함")을 값으로 그대로 베껴 옵니다(260827 실측).
    if 상자["이름"]:
        거기규칙 = (f'3. "거기", "그곳", "그 식당", "아까 그 집" 은 지금 정해진 식당을 가리킵니다.\n'
                    f'   지금 정해진 식당 = {상자["이름"]}\n'
                    f'   예) "거기로 가는 택시" -> 도착지 = {상자["이름"]}\n'
                    f'       "거기서 출발" -> 출발지 = {상자["이름"]}')
    else:
        거기규칙 = '3. 아직 정해진 식당이 없습니다. "거기", "그곳" 이 나와도 장소 이름을 지어내지 마세요.'
    프롬프트 = f"""손님의 말에서 아래 항목을 찾아 JSON 으로만 답하세요.

[식당 항목]
- 지역   : 서울 중앙 / 서울 동쪽 / 서울 서쪽 / 서울 남쪽 / 서울 북쪽 중 하나
- 종류   : 한식 / 중식 / 일식 / 양식 / 아시아음식 중 하나
- 가격대 : 저렴 / 보통 / 비싼 중 하나

[택시 항목]
- 출발지   : 장소 이름
- 도착지   : 장소 이름
- 출발 시간 : 19:00 처럼 24시간 형식
- 차종     : 일반 / 모범 / 대형 중 하나

[의도]
- 예약   : 손님이 식당을 예약해달라고 하면 true
- 호출   : 손님이 택시를 불러달라고 하면 true
- 기사변경 : 다른 기사/다른 차로 바꿔달라고 하면 true
- 취소   : 취소해달라고 하면 true

규칙
1. 못 찾은 항목은 아예 넣지 마세요. 빈 문자열로 넣지 마세요.
2. "아무거나", "상관없어요", "아직 못 정했어요" 는 그 항목에 "dontcare" 를 넣으세요.
   이것은 못 찾은 것이 아니라 손님이 정한 값입니다.
{거기규칙}
4. 설명은 쓰지 말고 JSON 만 답하세요.

손님의 말: {말}"""
    try:
        raw = model.generate_content(프롬프트).text
        raw = raw.replace("```json", "").replace("```", "")
        m = re.search(r"\{.*\}", raw, re.S)
        return 펴기(json.loads(m.group(0))) if m else {}
    except Exception as e:
        return {"_오류": f"{type(e).__name__}: {str(e)[:100]}"}


# 모델이 답을 {"의도": {"예약": true}} 처럼 한 겹 더 싸서 줄 때가 있습니다.
# 쌌든 안 쌌든 한 층으로 펴서 늘 같은 모양으로 만듭니다(260827 실측).
아는칸 = set(식당칸 + 택시칸 + ["예약", "호출", "기사변경", "취소"])


def 펴기(d, 부모=None):
    나온것 = {}
    for k, v in d.items():
        키 = k.strip()
        # 택시 안의 '종류' 는 차종을 뜻합니다. 식당 '종류' 와 겹치지 않게 이름을 바꿉니다.
        if 키 == "종류" and 부모 and "택시" in 부모:
            키 = "차종"
        if isinstance(v, dict):
            나온것.update(펴기(v, 부모=키))
        elif 키 in 아는칸 and v not in (None, "", [], {}):
            if isinstance(v, str) and ("정함" in v or "없음" in v or v.startswith("(")):
                continue
            나온것[키] = v
    return 나온것


# ================================================================
#  현황판 - 웹의 결과 카드와 같은 역할
# ================================================================
def 현황(상자):
    식 = 상자["식당"]
    줄 = ["**지금까지 채운 칸**", "",
          "| | 칸 | 값 |", "|---|---|---|"]
    for n in 식당칸:
        v = 식.get(n)
        줄.append(f"| 🍽️ | {n} | {'아무거나' if v == 'dontcare' else (v or '-')} |")
    이름 = 상자["이름"]
    줄.append(f"| 🍽️ | **식당** | **{이름 or '-'}** {('· 예약 ' + 상자['예약번호']) if 상자['예약번호'] else ''} |")
    for n in 택시칸:
        v = 상자["택시"].get(n)
        표시 = "아무거나" if v == "dontcare" else (v or "-")
        # 도착지가 식당에서 넘어온 것이면 표시해 줍니다
        if n == "도착지" and 상자["이월"] and v:
            표시 = f"🔵 {표시}  ← 식당에서 이월"
        줄.append(f"| 🚕 | {n} | {표시} |")
    if 상자["ride_id"]:
        r = db.get_ride(상자["ride_id"])
        d = db.get_driver(r["driver_id"])
        줄 += ["", f"**호출번호 {r['id']} · {r['status']} · 고친 횟수 {r['change_count']}회**",
               f"기사 — {d['name']} · {d['phone']} · {d['vehicle_type']}" if d else "기사 — 배차 대기중"]
    return "\n".join(줄)


# ================================================================
#  대화 한 번
# ================================================================
def 대화(말, 기록, 상자):
    if 상자 is None:
        상자 = 빈상자()
    got = 뽑기(말, 상자)
    if "_오류" in got:
        기록 = 기록 + [{"role": "user", "content": 말},
                      {"role": "assistant", "content": f"모델 오류: {got['_오류']}"}]
        return 기록, 상자, 현황(상자), ""

    # 1) 뽑은 값을 상자에 넣습니다
    for n in 식당칸:
        if got.get(n):
            상자["식당"][n] = got[n]
    for n in 택시칸:
        if got.get(n):
            상자["택시"][n] = got[n]
            if n == "도착지":
                # 손님이 친 값이 지금 식당과 같으면 이월로 봅니다
                상자["이월"] = (got[n] == 상자["이름"])

    답 = []

    # 2) 취소
    if got.get("취소") and 상자["ride_id"]:
        db.cancel_ride(상자["ride_id"])
        상자["ride_id"] = None
        답.append("호출을 취소했습니다.")

    # 3) 기사 변경 (시나리오 2-1)
    elif got.get("기사변경") and 상자["ride_id"]:
        r = db.update_ride(상자["ride_id"], {}, new_driver=True)
        d = db.get_driver(r["driver_id"])
        답.append(f"다른 기사로 바꿨습니다. {d['name']} · {d['phone']} · {d['vehicle_type']} 입니다.")

    # 4) 식당 예약
    elif got.get("예약") or (상자["이름"] is None and got.get("_고른식당")):
        후보 = db.search_restaurants(상자["식당"].get("지역"), 상자["식당"].get("종류"),
                                     상자["식당"].get("가격대"))
        if not 후보:
            답.append("조건에 맞는 식당이 없습니다. 조건을 좀 넓혀주시겠어요?")
        else:
            가게 = 후보[0]
            상자["이름"] = 가게["name"]
            상자["예약번호"] = db.make_booking_code()
            답.append(f"{가게['name']} 으로 예약했습니다. 예약번호는 {상자['예약번호']} 입니다.")
            # ★ 이월 ★ 손님이 도착지를 안 말했으면 식당을 도착지로 넣습니다
            if not 상자["택시"].get("도착지"):
                상자["택시"]["도착지"] = 가게["name"]
                상자["이월"] = True
                답.append(f"택시 도착지는 {가게['name']} 으로 잡아두겠습니다.")

    # 5) 식당 검색만
    elif 상자["이름"] is None and 상자["식당"]:
        후보 = db.search_restaurants(상자["식당"].get("지역"), 상자["식당"].get("종류"),
                                     상자["식당"].get("가격대"))
        if not 후보:
            답.append("조건에 맞는 식당이 없습니다. 조건을 좀 넓혀주시겠어요?")
        else:
            줄 = ", ".join(f"{r['name']}({r['price']})" for r in 후보[:3])
            답.append(f"{len(후보)}곳 찾았습니다. {줄} 중에 어디로 예약할까요?")

    # 6) 택시 - 이미 부른 것이 있으면 고치고, 없으면 새로 부릅니다
    택 = 상자["택시"]
    필수 = ["출발지", "도착지", "출발 시간"]
    빈칸 = [n for n in 필수 if not 택.get(n)]

    if 상자["ride_id"]:
        # 이미 부른 택시 고치기  <- 9개 시나리오가 전부 여기로 옵니다
        now = db.get_ride(상자["ride_id"])
        맵 = {"출발지": "pickup", "도착지": "dropoff",
              "출발 시간": "request_time", "차종": "vehicle_type"}
        바뀐것 = {}
        for 한글, 영문 in 맵.items():
            v = 택.get(한글)
            if 한글 == "차종":
                v = v or "dontcare"
            if v and v != now[영문]:
                바뀐것[영문] = v
        if 바뀐것:
            if "dropoff" in 바뀐것:
                바뀐것["carried"] = (바뀐것["dropoff"] == 상자["이름"])
            if 상자["이름"] and 상자["이름"] != now["place_name"]:
                바뀐것["place_name"] = 상자["이름"]
                바뀐것["place_booking"] = 상자["예약번호"]
            r = db.update_ride(상자["ride_id"], 바뀐것)
            이름표 = {v: k for k, v in 맵.items()}
            바뀐칸 = ", ".join(이름표[k] for k in 바뀐것 if k in 이름표)
            답.append(f"{바뀐칸} 을(를) 바꿨습니다. (총 {r['change_count']}번 고침)")

    elif not 빈칸 and (got.get("호출") or 상자["이름"]):
        # 새로 부르기
        r = db.create_ride(택["출발지"], 택["도착지"], 택["출발 시간"],
                           택.get("차종") or "dontcare", source="bot",
                           place_name=상자["이름"], place_booking=상자["예약번호"],
                           carried=상자["이월"])
        상자["ride_id"] = r["id"]
        d = db.get_driver(r["driver_id"])
        답.append(f"배차했습니다. 호출번호 {r['id']} 입니다.")
        답.append(f"기사님은 {d['name']}, 전화번호는 {d['phone']} 입니다." if d
                  else "지금 맞는 기사가 없어 접수만 해두었습니다.")

    elif 빈칸:
        # 차종은 94%가 '아무거나' 라서 묻지 않습니다. 필수 3칸만 묻습니다.
        묻기 = {"출발지": "어디서 타실 건가요?", "도착지": "어디로 가시나요?",
                "출발 시간": "몇 시에 출발하실까요?"}
        if 상자["이름"] or 택:
            답.append(묻기[빈칸[0]])

    if not 답:
        답.append("어떤 식당을 찾으시나요? 지역이나 음식 종류를 알려주세요.")

    기록 = 기록 + [{"role": "user", "content": 말},
                  {"role": "assistant", "content": "\n".join(답)}]
    return 기록, 상자, 현황(상자), ""


def 새로시작():
    상자 = 빈상자()
    return [], 상자, 현황(상자), ""


with gr.Blocks(title="식당 + 택시 (봇)") as demo:
    gr.Markdown("# 🍽️ ➜ 🚕  식당 예약하고 택시 부르기 (봇)\n말로 하세요. 한 번에 여러 개 말해도 됩니다.")
    상자 = gr.State(빈상자())

    with gr.Row():
        with gr.Column(scale=2):
            화면 = gr.Chatbot(type="messages", height=460)
            입력 = gr.Textbox(placeholder="예) 서울 서쪽에 저렴한 한식집 찾아주세요", label="", submit_btn=True)
            새로btn = gr.Button("새로 시작")
        with gr.Column(scale=1):
            판 = gr.Markdown(현황(빈상자()))

    # api_name=False 를 빼면 gradio 가 State 안의 사전으로 API 문서를 만들려다 터집니다.
    입력.submit(대화, [입력, 화면, 상자], [화면, 상자, 판, 입력], api_name=False)
    새로btn.click(새로시작, None, [화면, 상자, 판, 입력], api_name=False)

if __name__ == "__main__":
    demo.launch(server_port=7871, show_api=False)
