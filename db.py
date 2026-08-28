# ================================================================
#  창고 담당.  웹(web.py) 과 봇(app.py) 이 이 파일을 같이 씁니다.
#  같은 창고를 쓰기 때문에 웹에서 부른 택시가 봇에도 보입니다.
# ================================================================
import os
import random
import string
import dotenv
from supabase import create_client

dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

_sb = None


def sb():
    """창고 연결. 처음 한 번만 연결하고 그 다음부터는 그것을 다시 씁니다."""
    global _sb
    if _sb is None:
        url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError(".env 에 SUPABASE_URL / SUPABASE_KEY 가 없습니다")
        _sb = create_client(url, key)
    return _sb


# ================================================================
#  1번 블록 - 장소 (식당 · 숙소 · 관광)
# ================================================================
def search_places(domain, area=None, category=None, price=None, **옵션):
    """조건에 맞는 장소를 찾습니다. 'dontcare' 나 빈 값은 안 따집니다.

    옵션(gym / parking / breakfast) 은 True 일 때만 거릅니다.
    끄면 '없어도 된다' 는 뜻이라 안 거릅니다.
    시나리오 1 "헬스장 있는 숙소" -> "없어도 돼요" 가 이것입니다.
    """
    q = sb().table("places").select("*").eq("domain", domain)
    for 칸, 값 in (("area", area), ("category", category), ("price", price)):
        if 값 and 값 != "dontcare":
            q = q.eq(칸, 값)
    for 칸 in ("gym", "parking", "breakfast"):
        if 옵션.get(칸):
            q = q.eq(칸, True)
    return q.order("id").execute().data


def get_place(name):
    rows = sb().table("places").select("*").eq("name", name).execute().data
    return rows[0] if rows else None


def make_booking_code():
    """WoS 데이터의 예약번호(IUJH6 같은 것)를 흉내냅니다."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=5))


# ================================================================
#  2번 블록 - 기사
# ================================================================
def pick_driver(vehicle_type="dontcare", exclude_id=None):
    """조건에 맞는 기사 한 명을 고릅니다. 없으면 None.

    exclude_id 는 '다른 기사로 바꿔주세요'(시나리오 2-1) 때 씁니다.
    """
    q = sb().table("drivers").select("*").eq("is_available", True)
    # dontcare 면 차종을 안 따집니다. 실제 데이터의 94% 가 이 경우입니다.
    if vehicle_type and vehicle_type != "dontcare":
        q = q.eq("vehicle_type", vehicle_type)
    rows = q.execute().data
    if exclude_id is not None:
        rows = [r for r in rows if r["id"] != exclude_id]
    return rows[0] if rows else None


def get_driver(driver_id):
    if not driver_id:
        return None
    rows = sb().table("drivers").select("*").eq("id", driver_id).execute().data
    return rows[0] if rows else None


# ================================================================
#  두 블록이 만나는 곳 - 호출
# ================================================================
def create_ride(pickup, dropoff, request_time, vehicle_type="dontcare",
                source="web", place_domain=None, place_name=None,
                place_booking=None, carried=False):
    """새 호출을 접수하고 기사까지 배정합니다.

    carried = True 는 '도착지를 손님이 치지 않고 식당에서 넘어왔다' 는 뜻입니다.
              체크리스트 2번(도착지가 이월되나요?)의 증거가 이 칸입니다.
    """
    driver = pick_driver(vehicle_type)
    return sb().table("rides").insert({
        "place_domain": place_domain,
        "place_name": place_name,
        "place_booking": place_booking,
        "carried": carried,
        "pickup": pickup,
        "dropoff": dropoff,
        "request_time": request_time,
        "vehicle_type": vehicle_type or "dontcare",
        "source": source,
        "status": "배차완료" if driver else "접수",
        "driver_id": driver["id"] if driver else None,
    }).execute().data[0]


def update_ride(ride_id, changes, new_driver=False):
    """이미 접수한 호출을 고칩니다.  <- 9개 시나리오가 전부 이것입니다.

    changes    : 바꿀 칸만 담은 사전. 여기 없는 칸은 건드리지 않습니다.
    new_driver : True 면 지금 기사를 빼고 다른 기사로 다시 배정합니다.
    """
    now = get_ride(ride_id)
    if now is None:
        return None

    fields = dict(changes)
    want_type = fields.get("vehicle_type", now["vehicle_type"])
    if new_driver or ("vehicle_type" in fields and fields["vehicle_type"] != now["vehicle_type"]):
        driver = pick_driver(want_type, exclude_id=now["driver_id"] if new_driver else None)
        fields["driver_id"] = driver["id"] if driver else None
        fields["status"] = "배차완료" if driver else "접수"

    fields["change_count"] = now["change_count"] + 1
    fields["updated_at"] = "now()"
    return sb().table("rides").update(fields).eq("id", ride_id).execute().data[0]


def cancel_ride(ride_id):
    return sb().table("rides").update({"status": "취소"}).eq("id", ride_id).execute().data[0]


def get_ride(ride_id):
    rows = sb().table("rides").select("*").eq("id", ride_id).execute().data
    return rows[0] if rows else None


def recent_rides(limit=10):
    """최근 호출 목록. 웹과 봇에서 만든 것이 한 곳에 섞여 보입니다."""
    return sb().table("rides").select("*").order("id", desc=True).limit(limit).execute().data


# ================================================================
#  4번 블록 - 메모판 (봇2 · 챌린지 2)
#
#  어제 봇은 슬롯을 봇 안(gr.State)에 두었습니다.
#  새로고침하면 날아가고, 웹에서는 볼 수 없었습니다.
#  이제 슬롯이 창고에 삽니다. 봇은 말 한 번마다
#  여기서 꺼내 읽고 -> 한 칸 채우고 -> 다시 적습니다.
#  그래서 봇이 아무것도 기억하지 않아도 대화가 이어집니다.
#
#  code(입장 코드)가 손님을 가르는 칸막이입니다. 회원가입 대신 쓰는 아이디입니다.
# ================================================================
from datetime import datetime, timezone

슬롯칸 = ["place_kind", "place_name", "pickup", "dropoff", "request_time"]
_저장가능 = 슬롯칸 + ["carried", "ride_id", "turns"]


def _지금():
    return datetime.now(timezone.utc).isoformat()


def get_session(code):
    """입장 코드로 메모판을 꺼냅니다. 그 코드가 처음이면 새로 한 장 만듭니다."""
    code = str(code).strip()
    rows = sb().table("sessions").select("*").eq("code", code).execute().data
    if rows:
        return rows[0]
    return sb().table("sessions").insert({"code": code}).execute().data[0]


def save_session(code, 값들):
    """바뀐 칸만 적습니다. 값이 안 온 칸은 안 건드립니다.

    한 칸씩만 덮어쓰는 것이 중요합니다. 통째로 갈아끼우면
    이번 말에 안 나온 칸이 지워집니다.
    """
    fields = {k: v for k, v in 값들.items() if k in _저장가능}
    if not fields:
        return get_session(code)
    get_session(code)                       # 줄이 없으면 먼저 만들어 둡니다
    fields["updated_at"] = _지금()
    return sb().table("sessions").update(fields).eq(
        "code", str(code).strip()).execute().data[0]


def clear_session(code):
    """내 메모만 지웁니다. 남의 입장 코드는 안 건드립니다."""
    빈칸 = {k: None for k in 슬롯칸}
    빈칸.update({"carried": False, "ride_id": None, "turns": 0, "updated_at": _지금()})
    get_session(code)
    return sb().table("sessions").update(빈칸).eq(
        "code", str(code).strip()).execute().data[0]


def 다찼나(메모):
    """5칸이 전부 찼으면 True. 이때만 영수증을 낼 수 있습니다."""
    return all(메모.get(k) for k in 슬롯칸)


# ----------------------------------------------------------
#  봇 주소도 창고에 둡니다.
#
#  gradio 의 공개 주소(*.gradio.live)는 72시간마다 바뀝니다.
#  코드나 .env 에 박아두면 바뀔 때마다 웹을 다시 배포해야 합니다.
#  창고에 두면 봇을 껐다 켜기만 하면 웹이 알아서 새 주소를 따라옵니다.
#  슬롯을 gr.State 에서 창고로 옮긴 것과 똑같은 이야기입니다.
# ----------------------------------------------------------
def set_setting(key, value):
    return sb().table("settings").upsert(
        {"key": key, "value": value, "updated_at": _지금()}).execute().data[0]


def get_setting(key):
    rows = sb().table("settings").select("value").eq("key", key).execute().data
    return rows[0]["value"] if rows else None
