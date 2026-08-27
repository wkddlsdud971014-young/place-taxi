# Supabase 가 연결됐는지 확인합니다. 고치지 않아도 됩니다.
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import dotenv
    from supabase import create_client
except ImportError as e:
    print(f"설치 안 됨: {e.name}  -> pip install supabase 를 다시 하세요")
    sys.exit(1)

dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("주소나 열쇠가 없음  -> .env 에 SUPABASE_URL 과 SUPABASE_KEY 를 넣으세요")
    sys.exit(1)
if not url.startswith("https://"):
    print(f"주소가 이상합니다: {url[:30]}  -> https:// 로 시작해야 합니다")
    sys.exit(1)
print(f"주소 OK  {url}")
print(f"열쇠 OK  길이 {len(key)}")

sb = create_client(url, key)

# 1. 장소 표와 기사 표를 읽어봅니다
try:
    places = sb.table("places").select("*").execute().data
    drivers = sb.table("drivers").select("*").execute().data
except Exception as e:
    msg = str(e)
    if "does not exist" in msg or "PGRST205" in msg:
        print("기사 표가 없습니다  -> schema.sql 을 SQL Editor 에 붙여 넣고 Run 하세요")
    elif "Invalid API key" in msg or "JWT" in msg:
        print("열쇠가 맞지 않습니다  -> Settings > API 의 anon public 키를 다시 복사하세요")
    else:
        print(f"읽기 실패: {type(e).__name__}  {msg[:150]}")
    sys.exit(1)

if len(drivers) == 0:
    print("기사 표가 비었습니다  -> schema.sql 의 insert 부분이 안 돌았습니다")
    sys.exit(1)
도메인별 = {}
for p in places:
    도메인별[p["domain"]] = 도메인별.get(p["domain"], 0) + 1
print(f"장소 OK  {len(places)}곳  ({' · '.join(f'{k} {v}' for k, v in sorted(도메인별.items()))})")
print(f"기사 OK  {len(drivers)}명  (예: {drivers[0]['name']} / {drivers[0]['vehicle_type']})")

# 2. 호출 표에 진짜로 써봅니다  <- 자물쇠(RLS)가 안 풀렸으면 여기서 막힙니다
try:
    row = sb.table("rides").insert({
        "pickup": "연결확인용",
        "dropoff": "연결확인용",
        "request_time": "00:00",
        "source": "check",
    }).execute().data[0]
except Exception as e:
    msg = str(e)
    if "row-level security" in msg or "42501" in msg:
        print("자물쇠에 막혔습니다  -> schema.sql 의 4번(자물쇠 풀기) 부분을 다시 돌리세요")
    else:
        print(f"쓰기 실패: {type(e).__name__}  {msg[:150]}")
    sys.exit(1)

print(f"쓰기 OK  id={row['id']}  status={row['status']}  vehicle_type={row['vehicle_type']}")

# 3. 확인용으로 넣은 줄은 지웁니다
sb.table("rides").delete().eq("id", row["id"]).execute()
print("지우기 OK")
print()
print("전부 통과. 2단계(웹 만들기)로 가도 됩니다.")
