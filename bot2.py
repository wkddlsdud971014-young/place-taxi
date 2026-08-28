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


def _납작(글):
    """띄어쓰기를 없앱니다. 사람은 '바삭치킨' 이라고 치는데
    창고에는 '바삭 치킨' 으로 들어 있어서 못 찾았습니다(260828 실측)."""
    return re.sub(r"\s+", "", str(글 or ""))


def 장소찾기(말):
    if not 말:
        return None
    납 = _납작(말)
    if not 납:
        return None
    for p in 모든장소():                      # 이름이 통째로 같으면 그것이 먼저
        if _납작(p["name"]) == 납:
            return p
    for p in 모든장소():
        n = _납작(p["name"])
        if n and (n in 납 or 납 in n):
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

    # 봇은 늘 '빈칸 중 첫 번째' 를 되묻습니다. 그래서 슬롯만 보면
    # 직전에 무엇을 물었는지 다시 계산할 수 있습니다.
    # 대화 기록을 안 들고도 "어디서 타시겠어요? -> 광화문" 을 출발지로 넣을 수 있는
    # 이유가 이것입니다. 이게 없으면 엉뚱한 칸에 들어갑니다(260828 실측).
    빈칸 = [k for k in db.슬롯칸 if not 메모.get(k)]
    if 빈칸:
        물은칸 = (f'0. 방금 손님에게 "{칸이름[빈칸[0]]}" 을 물었습니다.\n'
                  f'   손님의 말이 어느 칸인지 애매하면 {빈칸[0]} 에 넣으세요.\n'
                  f'   예) "어디서 타시겠어요?" 뒤의 "광화문" 은 장소가 아니라 pickup 입니다.')
    else:
        물은칸 = "0. 칸이 다 찼습니다. 손님이 고치겠다고 한 칸만 넣으세요."

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
{물은칸}
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
#  한 줄 상태
#  영수증표는 웹(/bot2)이 그립니다. 여기에 또 그리면 좁은 iframe 안에서
#  채팅 아래로 밀려 내려가 세로로 길어집니다(260828 실측). 그래서 한 줄만 둡니다.
# ================================================================
def 한줄(코드):
    메모 = db.get_session(코드)
    찬것 = sum(1 for k in db.슬롯칸 if 메모.get(k))
    빈칸 = [칸이름[k] for k in db.슬롯칸 if not 메모.get(k)]
    줄 = f"**{찬것}/5** 채움"
    if 빈칸:
        줄 += " · 남은 칸 — " + " · ".join(빈칸)
    if 메모.get("ride_id"):
        줄 += f" · 🧾 호출 **{메모['ride_id']}**"
    return 줄 + "\n\n자세한 영수증은 오른쪽 화면에 있습니다."


def 후보안내(종류):
    """창고에 없는 곳을 말했을 때, 있는 곳을 몇 개 보여줍니다."""
    후보 = [p["name"] for p in 모든장소() if not 종류 or p["domain"] == 종류][:6]
    머리 = f"{종류} 중에는" if 종류 else "저희가 아는 곳은"
    return f"{머리} 이런 곳이 있습니다 — " + " · ".join(후보)


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
        return 기록, 한줄(코드), ""

    옛 = db.get_session(코드)                      # ① 창고에서 꺼낸다
    got = 뽑기(말, 옛)                             # ② Gemini 1콜

    if "_오류" in got:
        기록 = 기록 + [{"role": "user", "content": 말},
                      {"role": "assistant", "content": f"모델 오류: {got['_오류']}"}]
        return 기록, 한줄(코드), ""

    if got.get("초기화"):
        db.clear_session(코드)
        답 = "메모판을 비웠습니다. 처음부터 다시 시작합니다."
        return (기록 + [{"role": "user", "content": 말},
                       {"role": "assistant", "content": 답}], 한줄(코드), "")

    바뀐 = {}
    for k in db.슬롯칸:
        v = got.get(k)
        if v and str(v).strip():
            바뀐[k] = str(v).strip()

    # 창고에 없는 장소는 적지 않습니다.
    # 안 막으면 '성수동 근처 파스타집' 처럼 없는 곳으로 접수가 됩니다(260828 실측).
    없던곳 = None
    if 바뀐.get("place_name"):
        p = 장소찾기(바뀐["place_name"])
        if p:
            바뀐["place_name"] = p["name"]
            바뀐.setdefault("place_kind", p["domain"])
        else:
            없던곳 = 바뀐.pop("place_name")
            # 같은 이름이 도착지·출발지로도 새어 들어옵니다.
            # "성수동 파스타집으로 바꿔줘" 는 장소이면서 도착지이기도 해서,
            # 장소만 막으면 도착지로 들어가 버립니다(260828 실측).
            for 칸 in ("dropoff", "pickup"):
                v = 바뀐.get(칸)
                if v and (v == 없던곳 or v in 없던곳 or 없던곳 in v):
                    바뀐.pop(칸)

    # 이미 적혀 있는 값과 같으면 뺍니다.
    # 안 빼면 "적었습니다 - 장소-종류" 가 헛되이 뜨고 호출도 괜히 고쳐집니다.
    바뀐 = {k: v for k, v in 바뀐.items() if v != 옛.get(k)}

    # 이월 - "거기로" 라고만 하면 도착지를 장소 이름으로 채웁니다
    이름 = 바뀐.get("place_name") or 옛.get("place_name")
    if 이름 and not 바뀐.get("dropoff") and any(w in 말 for w in 지시어):
        바뀐["dropoff"] = 이름

    # 장소를 바꿨는데 도착지가 그 장소에서 이월된 것이었으면 도착지도 따라갑니다.
    # 어제 시나리오 7번(경복궁 -> 창덕궁)과 같은 동작입니다.
    if 바뀐.get("place_name") and 옛.get("carried") and 옛.get("dropoff") == 옛.get("place_name"):
        바뀐["dropoff"] = 바뀐["place_name"]

    if 이름 and 바뀐.get("dropoff") == 이름:
        바뀐["carried"] = True

    답 = []
    # '식당' 처럼 종류를 말한 것을 가게 이름으로 보고 혼내면 안 됩니다(260828 실측).
    if 없던곳 in ("식당", "숙소", "관광"):
        없던곳 = None
    if 없던곳:
        종류 = 바뀐.get("place_kind") or 옛.get("place_kind")
        답.append(f"'{없던곳}' 은 저희가 모르는 곳입니다. " + 후보안내(종류))

    바뀐["turns"] = (옛.get("turns") or 0) + 1
    메모 = db.save_session(코드, 바뀐)              # ③ 창고에 적는다
    # ④ 봇의 뇌는 여기서 끝납니다. 다음 턴에 아무것도 안 들고 갑니다.

    # 손님이 친 글자가 값 안에 그대로 있으면 '들은 것',
    # 없으면 봇이 미루어 짐작한 것입니다. 둘을 갈라서 말해 줍니다.
    # "배고프네요 -> 식당", "7시 -> 19:00" 처럼 짐작해 놓고 값을 안 보여주면
    # 손님은 무엇이 적혔는지 모른 채 넘어갑니다(260828 실측).
    적은칸 = [k for k in db.슬롯칸 if k in 바뀐]
    말납 = _납작(말)
    들은것 = [k for k in 적은칸 if _납작(바뀐[k]) in 말납]
    짐작 = [k for k in 적은칸 if k not in 들은것]
    if 들은것:
        답.append("적었습니다 — " +
                  " · ".join(f"{칸이름[k]} **{바뀐[k]}**" for k in 들은것))
    if 짐작:
        답.append("이렇게 봤습니다 — " +
                  " · ".join(f"{칸이름[k]} **{바뀐[k]}**" for k in 짐작) +
                  "\n아니면 그냥 다시 말씀해 주세요. 고쳐 적습니다.")

    # 영수증이 이미 나왔으면 호출도 같이 고칩니다.
    # 안 고치면 메모판과 영수증이 서로 다른 값을 갖게 됩니다(260828 실측).
    if 옛.get("ride_id") and 적은칸:
        변경 = {k: 바뀐[k] for k in ("pickup", "dropoff", "request_time") if k in 바뀐}
        if "place_name" in 바뀐:
            변경["place_name"] = 바뀐["place_name"]
            변경["place_domain"] = 메모.get("place_kind")
        if 변경:
            r = db.update_ride(옛["ride_id"], 변경)
            답.append(f"호출 **{r['id']}** 도 같이 고쳤습니다. "
                      f"(고친 횟수 {r['change_count']}회 · 도착지 {r['dropoff']})")

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

    기록 = 기록 + [{"role": "user", "content": 말},
                  {"role": "assistant", "content": "\n\n".join(답)}]
    return 기록, 한줄(코드), ""


def 지우기(코드):
    """내 메모만 지웁니다. 남의 입장 코드는 안 건드립니다."""
    코드 = (코드 or "1").strip() or "1"
    db.clear_session(코드)
    return ([{"role": "assistant", "content":
              f"입장 코드 {코드} 의 메모만 지웠습니다. 다른 손님 것은 그대로입니다."}],
            한줄(코드), "")


# ================================================================
#  화면
#
#  입장 코드 칸을 여기 두지 않습니다. 웹(/bot2)에 하나 있는데 여기에도 두면
#  둘이 따로 놀아서, 웹은 7번 손님을 보는데 봇은 1번에 적고 있었습니다(260828 실측).
#  이제 웹이 iframe 주소에 ?code=7 을 실어 보내고 봇은 그것을 읽기만 합니다.
# ================================================================
def 시작(request: gr.Request):
    """웹이 주소에 실어 보낸 입장 코드를 읽습니다."""
    try:
        코드 = (request.query_params.get("code") or "1").strip() or "1"
    except Exception:
        코드 = "1"
    메모 = db.get_session(코드)
    찬것 = sum(1 for k in db.슬롯칸 if 메모.get(k))
    안내 = (f"입장 코드 {코드} · 새 접수를 시작합니다."
            if 찬것 == 0 else
            f"입장 코드 {코드} · 적어둔 {찬것}칸을 그대로 이어서 합니다.")
    return (코드, f"입장 코드 **{코드}**",
            [{"role": "assistant", "content": 안내}], 한줄(코드))


with gr.Blocks(title="봇2 - 대화가 곧 기록", theme=THEME, css=CSS) as demo:
    # 입장 코드는 화면에 칸으로 두지 않고 State 로만 들고 있습니다.
    코드 = gr.State("1")

    머리 = gr.Markdown("입장 코드 **1**")
    화면 = gr.Chatbot(type="messages", height=300, show_label=False)
    입력 = gr.Textbox(placeholder="예) 스시 하나 예약해줘", label="말하기",
                      submit_btn=True, container=False)
    상태 = gr.Markdown(한줄("1"))
    지우기btn = gr.Button("처음부터 다시 (내 메모만 지우기)", size="sm")

    # api_name=False 를 빼면 gradio 가 State 로 API 문서를 만들려다 터집니다.
    # bot.py 에도 같은 주의가 적혀 있습니다(260827).
    demo.load(시작, None, [코드, 머리, 화면, 상태], api_name=False)
    입력.submit(대화, [입력, 코드, 화면], [화면, 상태, 입력], api_name=False)
    지우기btn.click(지우기, [코드], [화면, 상태, 입력], api_name=False)


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
