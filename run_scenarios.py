# ================================================================
#  테스트 시나리오 9개를 웹 경로와 봇 경로로 각각 돌립니다.
#  웹 경로 = web 화면이 부르는 것과 같은 db.py 함수를 같은 순서로
#  봇 경로 = bot.대화() 에 진짜 사람 말을 넣어서
#  결과는 RESULT.md 로 나옵니다.
# ================================================================
import sys, time, io, json
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import warnings; warnings.filterwarnings("ignore")
import db, bot

기록 = []          # 시나리오별 결과
치운것 = []        # 끝나고 지울 ride id


# ---------------- 웹 경로 도우미 ----------------
class 웹:
    """웹 화면을 코드로 흉내냅니다. 누른 것을 하나씩 셉니다."""
    def __init__(self):
        self.도메인 = "식당"; self.지역 = self.종류 = self.가격 = None
        self.옵션 = {}; self.후보 = []; self.장소 = None; self.예약번호 = None
        self.출발지 = self.도착지 = self.시간 = ""; self.차종 = "dontcare"
        self.ride = None; self.클릭 = []

    def 탭(self, d):
        self.도메인 = d; self.종류 = self.가격 = None
        self.옵션 = {}; self.후보 = []; self.클릭.append(f"[{d} 탭]")

    def 고르기(self, 칸, 값):
        setattr(self, 칸, 값); self.클릭.append(f"[{칸}={값}]")

    def 칩(self, 이름):
        self.옵션[이름] = not self.옵션.get(이름)
        self.클릭.append(f"[{이름} {'켬' if self.옵션[이름] else '끔'}]")

    def 검색(self):
        self.후보 = db.search_places(self.도메인, self.지역, self.종류, self.가격, **self.옵션)
        self.클릭.append("[검색]")
        return self.후보

    def 선택예약(self, 이름=None):
        가게 = next((r for r in self.후보 if r["name"] == 이름), None) if 이름 else (self.후보[0] if self.후보 else None)
        if not 가게: return None
        self.클릭.append(f"[{가게['name']} 선택]"); self.클릭.append("[이 장소 예약]")
        self.장소 = 가게; self.예약번호 = db.make_booking_code()
        if not self.도착지 or (self.ride and self.ride["carried"]):
            self.도착지 = 가게["name"]          # ★ 이월 ★
        if self.ride:                            # 이미 부른 택시도 같이 고칩니다
            self.ride = db.update_ride(self.ride["id"], {
                "dropoff": 가게["name"], "place_domain": self.도메인,
                "place_name": 가게["name"], "place_booking": self.예약번호,
                "carried": True})
        return 가게

    def 부르기(self):
        self.클릭.append("[택시 부르기]")
        self.ride = db.create_ride(self.출발지, self.도착지, self.시간, self.차종, source="web",
                                   place_domain=self.도메인 if self.장소 else None,
                                   place_name=self.장소["name"] if self.장소 else None,
                                   place_booking=self.예약번호,
                                   carried=bool(self.장소) and self.도착지 == self.장소["name"])
        치운것.append(self.ride["id"]); return self.ride

    def 한줄수정(self, 칸, 값):
        """장바구니식 - 결과 카드의 그 줄만 고칩니다. [수정] + [저장] = 2클릭"""
        self.클릭.append(f"[{칸} 수정]"); self.클릭.append("[저장]")
        바꿈 = {칸: 값}
        if 칸 == "dropoff":
            바꿈["carried"] = bool(self.장소) and 값 == self.장소["name"]
        self.ride = db.update_ride(self.ride["id"], 바꿈); return self.ride

    def 폼일괄(self, **칸들):
        """폼 일괄식 - 위 칸을 고치고 [변경 저장] 한 번 = 1클릭"""
        self.클릭.append("[변경 저장]")
        self.ride = db.update_ride(self.ride["id"], 칸들); return self.ride

    def 기사변경(self):
        self.클릭.append("[다른 기사로]")
        self.ride = db.update_ride(self.ride["id"], {}, new_driver=True); return self.ride

    def 처음부터(self):
        self.클릭.append("[처음부터 다시]")
        if self.ride: db.cancel_ride(self.ride["id"])
        전 = self.ride
        self.__init__(); self.클릭 = ["[처음부터 다시]"]
        return 전


# ---------------- 봇 경로 도우미 ----------------
def 봇대화(말들, 쉬기=4.5):
    상자 = bot.빈상자(); 로그 = []; 기록2 = []
    for m in 말들:
        기록2, 상자, _, _ = bot.대화(m, 기록2, 상자)
        로그.append(("나", m)); 로그.append(("봇", 기록2[-1]["content"]))
        if 상자.get("ride_id") and 상자["ride_id"] not in 치운것:
            치운것.append(상자["ride_id"])
        time.sleep(쉬기)          # 1분에 15번 제한을 넘지 않게 쉽니다
    return 상자, 로그


def 담기(번호, 제목, 웹결과, 웹클릭, 봇턴, 봇로그, 봇결과, 발견):
    기록.append(dict(번호=번호, 제목=제목, 웹결과=웹결과, 웹클릭=웹클릭,
                     봇턴=봇턴, 봇로그=봇로그, 봇결과=봇결과, 발견=발견))
    print(f"  {번호}. {제목} — 웹 {len(웹클릭)}클릭 / 봇 {봇턴}턴")
    sys.stdout.flush()


print("=== 웹 경로 9개 ===")

# ---------- 1. 헬스장 있는 숙소 -> 없어도 돼요 ----------
w = 웹(); w.탭("숙소"); w.칩("gym"); 있 = w.검색(); w.칩("gym"); 없 = w.검색()
S1웹 = f"헬스장 켬 {len(있)}곳 → 끔 {len(없)}곳"; S1클릭 = list(w.클릭)

# ---------- 2. 청와대 -> (택시) -> 경복궁 ----------
w = 웹(); w.탭("관광"); w.검색(); w.선택예약("청와대")
w.출발지, w.시간 = "강남역", "14:00"; w.부르기()
전2 = w.ride["dropoff"]; w.검색(); w.선택예약("경복궁")
S2웹 = f"도착지 {전2} → {w.ride['dropoff']} (이월 {w.ride['carried']}, 고침 {w.ride['change_count']})"
S2클릭 = list(w.클릭)

# ---------- 3. 치킨집 -> 일식집 ----------
w = 웹(); w.탭("식당"); w.고르기("종류", "치킨"); 치 = w.검색()
w.고르기("종류", "일식"); 일 = w.검색(); w.선택예약()
S3웹 = f"치킨 {len(치)}곳 → 일식 {len(일)}곳, {w.장소['name']} 예약"; S3클릭 = list(w.클릭)

# ---------- 4. 4:30 -> 20:30  (두 길 비교) ----------
w = 웹(); w.탭("식당"); w.검색(); w.선택예약()
w.출발지, w.시간 = "강남역", "04:30"; w.부르기(); 기준 = len(w.클릭)
w.한줄수정("request_time", "20:30"); 장바구니 = len(w.클릭) - 기준
w2 = 웹(); w2.ride = w.ride; w2.클릭 = []
w2.폼일괄(request_time="04:30"); 폼 = len(w2.클릭)
S4웹 = f"04:30 → {w.ride['request_time']} · 장바구니 {장바구니}클릭 / 폼 {폼}클릭"
S4클릭 = list(w.클릭)

# ---------- 5. 아무거나 -> 고급 ----------
w = 웹(); w.탭("식당"); w.검색(); w.선택예약()
w.출발지, w.시간, w.차종 = "강남역", "19:00", "dontcare"; w.부르기()
기사전 = db.get_driver(w.ride["driver_id"])["name"]
w.한줄수정("vehicle_type", "고급")
기사후 = db.get_driver(w.ride["driver_id"])
S5웹 = (f"차종 아무거나 → 고급 · 기사 {기사전} → "
        f"{기사후['name']}({기사후['vehicle_type']}) 자동 재배차")
S5클릭 = list(w.클릭)

# ---------- 6. 엄중식에서 출발 -> 집에서 출발 ----------
w = 웹(); w.탭("식당"); w.검색(); w.선택예약("엄중식")
w.출발지, w.도착지, w.시간 = "엄중식", "엄중식", "18:00"; w.부르기()
겹침 = w.ride["pickup"] == w.ride["dropoff"]
w.한줄수정("pickup", "집")
S6웹 = (f"출발지 엄중식 → {w.ride['pickup']} · 도착지 {w.ride['dropoff']} 그대로"
        + (" · ⚠️ 부를 때 출발지=도착지 였음" if 겹침 else ""))
S6클릭 = list(w.클릭)

# ---------- 7. ⭐ 경복궁 -> 창덕궁 ----------
w = 웹(); w.탭("관광"); w.검색(); w.선택예약("경복궁")
w.출발지, w.시간 = "서울역", "10:00"; w.부르기()
전7 = (w.ride["place_name"], w.ride["dropoff"])
w.검색(); w.선택예약("창덕궁")
S7웹 = (f"장소 {전7[0]}→{w.ride['place_name']} · 도착지 {전7[1]}→{w.ride['dropoff']} "
        f"(따라감 {'O' if w.ride['dropoff']=='창덕궁' else 'X'}, 이월 {w.ride['carried']}, "
        f"고침 {w.ride['change_count']})")
S7클릭 = list(w.클릭)

# ---------- 8. 숙소 A+4시 -> B+6시 ----------
w = 웹(); w.탭("숙소"); w.검색(); w.선택예약("그랜드 호텔")
w.출발지, w.시간 = "김포공항", "04:00"; w.부르기(); 기준 = len(w.클릭)
w.검색(); w.선택예약("시티 호텔"); w.한줄수정("request_time", "06:00")
장바구니8 = len(w.클릭) - 기준
S8웹 = (f"숙소 그랜드→{w.ride['place_name']} · 도착지 {w.ride['dropoff']} · "
        f"시간 04:00→{w.ride['request_time']} · 장바구니 {장바구니8}클릭 "
        f"(폼일괄은 장소를 못 바꿔서 [검색][선택][예약]+[변경저장]=4클릭)")
S8클릭 = list(w.클릭)

# ---------- 9. 처음부터 다시 ----------
w = 웹(); w.탭("관광"); w.검색(); w.선택예약()
w.출발지, w.시간 = "서울역", "09:00"; w.부르기(); 옛 = w.처음부터()
옛상태 = db.get_ride(옛["id"])["status"]
w.탭("식당"); 새 = w.검색()
S9웹 = f"옛 호출 상태 → {옛상태} · 도메인 관광→식당, {len(새)}곳 조회"
S9클릭 = list(w.클릭)

print("웹 경로 끝\n")

print("=== 봇 경로 9개 (모델 호출이 있어 몇 분 걸립니다) ===")

봇대본 = {
 1: ["헬스장 있는 숙소 찾아줘", "아 헬스장 없어도 돼요"],
 2: ["관광지 찾아줘", "청와대로 정할게요", "강남역에서 14시에 택시 불러줘", "아니 경복궁으로 바꿀래요"],
 3: ["치킨집 찾아요", "그냥 일식집으로요"],
 4: ["스시 하나로 예약하고 강남역에서 4시 30분 출발하는 택시", "아 20시 30분 출발로 바꿔요"],
 5: ["소문난 감자탕 예약하고 강남역에서 19시 택시, 아무 택시나요", "고급 택시로 해주세요"],
 6: ["엄중식이라는 식당 예약해줘", "엄중식에서 출발해서 강남역으로 18시 택시", "그냥 집에서 출발할게요"],
 7: ["경복궁 갈 거고 거기까지 택시", "서울역에서 10시 출발이요", "아 창덕궁으로 바꿀래요"],
 8: ["그랜드 호텔 예약하고 김포공항에서 4시 택시", "숙소는 시티 호텔로, 택시는 6시로"],
 9: ["가로수길 예약하고 서울역에서 9시 택시", "처음부터 다시요. 식당으로 할게요"],
}

봇결과 = {}
for n in range(1, 10):
    상자, 로그 = 봇대화(봇대본[n])
    r = db.get_ride(상자["ride_id"]) if 상자.get("ride_id") else None
    봇결과[n] = dict(턴=len(봇대본[n]), 로그=로그, 상자=상자, ride=r)
    끝 = (f"{r['place_name']} · {r['pickup']}→{r['dropoff']} · {r['request_time']} · "
          f"{r['vehicle_type']} · 이월 {r['carried']} · 고침 {r['change_count']}") if r else "호출 없음"
    print(f"  {n}. {len(봇대본[n])}턴 → {끝}")
    sys.stdout.flush()

# ---------------- 결과 저장 ----------------
웹표 = {
 1: ("헬스장 있는 숙소 → 없어도 돼요", S1웹, S1클릭),
 2: ("청와대 → (택시) → 경복궁", S2웹, S2클릭),
 3: ("치킨집 → 일식집", S3웹, S3클릭),
 4: ("4:30 → 20:30", S4웹, S4클릭),
 5: ("아무 택시 → 고급 택시", S5웹, S5클릭),
 6: ("엄중식에서 출발 → 집에서 출발", S6웹, S6클릭),
 7: ("⭐ 경복궁 → 창덕궁", S7웹, S7클릭),
 8: ("숙소 A+4시 → B+6시", S8웹, S8클릭),
 9: ("처음부터 다시 → 식당으로", S9웹, S9클릭),
}
json.dump({
  "web": {str(n): {"제목": t, "결과": r, "클릭": c} for n, (t, r, c) in 웹표.items()},
  "bot": {str(n): {"턴": v["턴"], "로그": v["로그"],
                   "ride": v["ride"], "상자이름": v["상자"].get("이름"),
                   "상자도메인": v["상자"]["식당"].get("도메인")} for n, v in 봇결과.items()},
}, open("scenario_raw.json", "w"), ensure_ascii=False, indent=1, default=str)
print("\nscenario_raw.json 저장")

# 테스트로 만든 호출을 지웁니다
for i in set(치운것):
    try: db.sb().table("rides").delete().eq("id", i).execute()
    except Exception: pass
print(f"테스트 호출 {len(set(치운것))}건 정리 완료")
