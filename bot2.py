# ================================================================
#  봇2 - 대화만 했는데 데이터가 기록되는 봇   (챌린지 2)
#
#  켜기:  ./.venv/bin/python bot2.py           -> 127.0.0.1:7872
#         SHARE=1 ./.venv/bin/python bot2.py   -> 공개 주소도 같이
#
#  어제 봇(bot.py)과 하는 일은 비슷합니다. 다른 것은 딱 하나입니다.
#
#      어제 : 슬롯이 봇 안에 있다    gr.State(빈상자())
#      오늘 : 슬롯이 창고에 있다     sessions[입장코드]
#
#  그래서 봇은 아무것도 기억하지 않습니다. 말을 들으면
#      창고에서 꺼내 읽고 -> Gemini 1콜 -> 창고에 적고 -> 잊습니다.
#  대화 기록을 프롬프트에 안 넣기 때문에 20턴을 해도 프롬프트가 안 커집니다.
#  화면에 보이는 대화 내용은 사람이 보라고 띄우는 것일 뿐, 모델에는 안 갑니다.
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
from theme import THEME, CSS

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3.5-flash-lite")

# 채워야 하는 칸 5개. 강사님 화면과 같습니다.
칸이름 = {
    "place_kind":   "장소-종류",
    "place_name":   "장소-이름",
    "pickup":       "택시-출발지",
    "dropoff":      "택시-도착지",
    "request_time": "택시-출발시간",
}
되묻기 = {
    "place_kind":   "어떤 곳을 찾으시나요? 식당 · 숙소 · 관광 중에 말씀해 주세요.",
    "place_name":   "어디로 정할까요? 이름을 말씀해 주세요.",
    "pickup":       "어디서 타시겠어요?",
    "dropoff":      "어디로 가시나요?",
    "request_time": "몇 시에 출발할까요?",
}
지시어 = ("거기", "그곳", "그리로", "그 집", "아까")


# ----------------------------------------------------------
#  장소 이름 맞추기
#  손님이 "파스타집" 이라고 해도 창고에 있는 정식 이름으로 바꿔 적습니다.
#  장소 목록은 잘 안 바뀌므로 한 번만 읽어 두고 다시 씁니다.
# ----------------------------------------------------------
_장소캐시 = None


def 모든장소():
    global _장소캐시
    if _장소캐시 is None:
        _장소캐시 = (db.search_places("식당") + db.search_places("숙소")
                     + db.search_places("관광"))
    return _장소캐시


def 장소찾기(말):
    if not 말:
        return None
    말 = str(말).strip()
    for p in 모든장소():                      # 이름이 통째로 들어 있으면 그것이 먼저
        if p["name"] == 말:
            return p
    for p in 모든장소():
        if p["name"] in 말 or 말 in p["name"]:
            return p
    return None


# ================================================================
#  말 -> 칸   (턴 1. 여기가 이 봇의 전부입니다)
# ================================================================
def 뽑기(말, 메모):
    """손님의 말 한 개에서 칸을 뽑습니다.

    프롬프트에 들어가는 것은 '창고에 적힌 슬롯' 과 '이번 말' 뿐입니다.
    대화 기록은 넣지 않습니다. 그래서 프롬프트 길이가 안 늘어납니다.
    """
    적힌것 = "\n".join(
        f"  - {칸이름[k]} : {메모.get(k) or '(비어 있음)'}" for k in db.슬롯칸)

    이름 = 메모.get("place_name")
    if 이름:
        거기규칙 = (f'2. "거기", "그곳", "거기로" 는 지금 정해진 장소를 가리킵니다.\n'
                    f'   지금 정해진 장소 = {이름}\n'
                    f'   예) "거기로 가는 택시" -> dropoff = {이름}')
    else:
        거기규칙 = ('2. 아직 정해진 장소가 없습니다. "거기", "그곳" 이 나와도 '
                    '이름을 지어내지 마세요.')

    프롬프트 = f"""손님의 말에서 아래 칸을 찾아 JSON 으로만 답하세요.

- place_kind   : 식당 / 숙소 / 관광 중 하나
- place_name   : 가려는 곳의 이름
- pickup       : 택시를 타는 곳
- dropoff      : 택시에서 내리는 곳
- request_time : 19:00 처럼 24시간 형식
- 초기화       : "처음부터 다시", "다 지우고" 면 true

지금 창고에 적혀 있는 것:
{적힌것}

규칙
1. 못 찾은 칸은 아예 넣지 마세요. 빈 문자열로 넣지 마세요.
{거기규칙}
3. 이미 적혀 있는 값을 그대로 다시 넣지 마세요. 바뀐 것만 넣으세요.
4. 설명은 쓰지 말고 JSON 만 답하세요.

손님의 말: {말}"""

    try:
        글 = model.generate_content(프롬프트).text
    except Exception as e:
        return {"_오류": str(e)}
    m = re.search(r"\{.*\}", 글, re.S)        # ```json 울타리가 붙어 나와도 건집니다
    if not m:
        return {"_오류": f"JSON 을 못 찾았습니다: {글[:80]}"}
    try:
        return json.loads(m.group())
    except Exception as e:
        return {"_오류": f"JSON 이 깨졌습니다: {e}"}


# ================================================================
#  오른쪽 영수증판
#  창고에서 그때그때 읽어서 그립니다. 봇 안에 든 값을 그리는 게 아닙니다.
# ================================================================
def 판(코드):
    메모 = db.get_session(코드)
    찬것 = sum(1 for k in db.슬롯칸 if 메모.get(k))
    줄 = [f"**영수증** · 입장 코드 `{코드}` · **{찬것}/5**", "",
          "메모판 = Supabase. 같은 내용이 웹 화면에도 뜹니다.", "",
          "| | 칸 | 값 |", "|---|---|---|"]
    for k in db.슬롯칸:
        v = 메모.get(k)
        표시 = v if v else "—"
        if k == "dropoff" and 메모.get("carried") and v:
            표시 = f"🔵 {표시}  ← 장소에서 이월"
        아이콘 = "🍽️" if k.startswith("place") else "🚕"
        줄.append(f"| {아이콘} | {칸이름[k]} | {표시} |")

    줄 += ["", f"말한 횟수 **{메모.get('turns') or 0}회** · "
               f"Gemini 호출 **매번 1콜** · 프롬프트 길이 **안 늘어남**"]

    if 메모.get("ride_id"):
        r = db.get_ride(메모["ride_id"])
        d = db.get_driver(r["driver_id"]) if r.get("driver_id") else None
        줄 += ["", "---", "",
               f"### 🧾 영수증 발행됨",
               f"**호출번호 {r['id']}** · {r['status']}",
               f"기사 — {d['name']} · {d['phone']} · {d['vehicle_type']}"
               if d else "기사 — 배차 대기중",
               f"들어온 곳 — `{r['source']}`"]
    return "\n".join(줄)


def 영수증글(r, d, 메모):
    줄 = ["🧾 **영수증이 나왔습니다.**", "",
          f"- 호출번호 : **{r['id']}**",
          f"- 장소 : {메모.get('place_kind') or '-'} · {메모.get('place_name') or '-'}",
          f"- 택시 : {메모.get('pickup')} → {메모.get('dropoff')} · {메모.get('request_time')}"]
    if 메모.get("carried"):
        줄.append("- 🔵 도착지는 손님이 다시 말하지 않았습니다. 장소에서 이월됐습니다.")
    줄.append(f"- 기사 : {d['name']} · {d['phone']} · {d['vehicle_type']}"
              if d else "- 기사 : 배차 대기중")
    return "\n".join(줄)


# ================================================================
#  대화 한 번
# ================================================================
def 대화(말, 코드, 기록):
    말 = (말 or "").strip()
    코드 = (코드 or "1").strip() or "1"
    if not 말:
        return 기록, 판(코드), ""

    메모 = db.get_session(코드)                    # ① 창고에서 꺼낸다
    got = 뽑기(말, 메모)                           # ② Gemini 1콜

    if "_오류" in got:
        기록 = 기록 + [{"role": "user", "content": 말},
                      {"role": "assistant", "content": f"모델 오류: {got['_오류']}"}]
        return 기록, 판(코드), ""

    if got.get("초기화"):
        db.clear_session(코드)
        답 = "메모판을 비웠습니다. 처음부터 다시 시작합니다."
        return (기록 + [{"role": "user", "content": 말},
                       {"role": "assistant", "content": 답}], 판(코드), "")

    바뀐 = {}
    for k in db.슬롯칸:
        v = got.get(k)
        if v and str(v).strip():
            바뀐[k] = str(v).strip()

    # 장소 이름은 창고에 있는 정식 이름으로 맞춰 적습니다
    if 바뀐.get("place_name"):
        p = 장소찾기(바뀐["place_name"])
        if p:
            바뀐["place_name"] = p["name"]
            바뀐.setdefault("place_kind", p["domain"])

    # 이월 - 손님이 "거기로" 라고만 했으면 도착지를 장소 이름으로 채웁니다.
    # 모델이 놓쳐도 여기서 한 번 더 잡습니다.
    이름 = 바뀐.get("place_name") or 메모.get("place_name")
    if 이름 and not 바뀐.get("dropoff") and any(w in 말 for w in 지시어):
        바뀐["dropoff"] = 이름
    if 이름 and 바뀐.get("dropoff") == 이름:
        바뀐["carried"] = True

    바뀐["turns"] = (메모.get("turns") or 0) + 1
    메모 = db.save_session(코드, 바뀐)              # ③ 창고에 적는다
    # ④ 봇의 뇌는 여기서 끝납니다. 다음 턴에 아무것도 안 들고 갑니다.

    답 = []
    적은칸 = [칸이름[k] for k in db.슬롯칸 if k in 바뀐]
    if 적은칸:
        답.append("적었습니다 — " + " · ".join(적은칸))

    빈칸 = [k for k in db.슬롯칸 if not 메모.get(k)]
    if 빈칸:
        답.append(되묻기[빈칸[0]])
    elif not 메모.get("ride_id"):
        # 마지막 칸이 찼습니다. 영수증이 뿅 나옵니다.
        r = db.create_ride(
            pickup=메모["pickup"], dropoff=메모["dropoff"],
            request_time=메모["request_time"], source="bot2",
            place_domain=메모.get("place_kind"), place_name=메모.get("place_name"),
            carried=bool(메모.get("carried")))
        메모 = db.save_session(코드, {"ride_id": r["id"]})
        d = db.get_driver(r["driver_id"]) if r.get("driver_id") else None
        답.append(영수증글(r, d, 메모))
    else:
        답.append(f"이미 영수증이 나왔습니다. 호출번호 {메모['ride_id']} 입니다.")

    기록 = 기록 + [{"role": "user", "content": 말},
                  {"role": "assistant", "content": "\n\n".join(답)}]
    return 기록, 판(코드), ""


def 입장(코드):
    """입장 코드를 바꾸면 그 손님의 메모판을 꺼내 옵니다."""
    코드 = (코드 or "1").strip() or "1"
    메모 = db.get_session(코드)
    찬것 = sum(1 for k in db.슬롯칸 if 메모.get(k))
    안내 = (f"입장 코드 {코드} · 새 접수를 시작합니다." if 찬것 == 0
            else f"입장 코드 {코드} · 적어둔 {찬것}칸을 그대로 이어서 합니다.")
    return [{"role": "assistant", "content": 안내}], 판(코드), ""


def 지우기(코드):
    """내 메모만 지웁니다. 남의 입장 코드는 안 건드립니다."""
    코드 = (코드 or "1").strip() or "1"
    db.clear_session(코드)
    return ([{"role": "assistant", "content":
              f"입장 코드 {코드} 의 메모만 지웠습니다. 다른 손님 것은 그대로입니다."}],
            판(코드), "")


# ================================================================
#  화면
# ================================================================
with gr.Blocks(title="봇2 - 대화가 곧 기록", theme=THEME, css=CSS) as demo:
    with gr.Row(equal_height=True):
        코드 = gr.Textbox(value="1", label="입장 코드 (같은 코드로 들어오면 이어서 합니다)",
                          scale=1, container=True)
        gr.Markdown("**대화만 했는데 데이터가 기록됩니다.** 봇은 매 턴 아무것도 "
                    "기억하지 않고, 창고(Supabase)에서 꺼내 읽고 다시 적습니다.")

    with gr.Row(equal_height=False):
        with gr.Column(scale=3):
            화면 = gr.Chatbot(type="messages", height=330, show_label=False)
            with gr.Row():
                입력 = gr.Textbox(placeholder="예) 성수동 근처 파스타집 찾아줘",
                                  label="말하기", submit_btn=True, scale=5,
                                  container=False)
        with gr.Column(scale=2, elem_classes="card"):
            판md = gr.Markdown(판("1"), elem_classes="result")
            지우기btn = gr.Button("처음부터 다시 (내 메모만 지우기)", size="sm")

    입력.submit(대화, [입력, 코드, 화면], [화면, 판md, 입력], api_name=False)
    코드.change(입장, [코드], [화면, 판md, 입력], api_name=False)
    지우기btn.click(지우기, [코드], [화면, 판md, 입력], api_name=False)


if __name__ == "__main__":
    앱, 로컬주소, 공개주소 = demo.launch(
        share=os.getenv("SHARE") == "1", server_port=7872, show_api=False,
        prevent_thread_lock=True)
    # 켜질 때 내 주소를 창고에 적어 둡니다.
    # 웹사이트는 이것을 읽어서 iframe 에 꽂습니다. 그래서 주소가 바뀌어도
    # 다시 배포할 필요가 없습니다. (schema2.sql 의 settings 표)
    주소 = 공개주소 or 로컬주소
    try:
        db.set_setting("bot2_url", 주소)
        print(f"\n창고에 주소를 적었습니다 → {주소}\n")
    except Exception as e:
        print(f"\n주소 기록 실패(봇은 그대로 돕니다): {e}\n")
    demo.block_thread()
