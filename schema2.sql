-- ============================================================
--  봇2 (챌린지 2) 가 쓰는 표 2개.  Supabase [SQL Editor] 에 붙여 넣고 Run
--
--  schema.sql 은 건드리지 않습니다.
--  그 파일은 맨 위에서 표를 지우고 다시 만들기 때문에,
--  다시 돌리면 어제 쌓인 호출 기록이 전부 날아갑니다.
--  그래서 새로 쓰는 표만 여기에 따로 두었습니다.
-- ============================================================

drop table if exists sessions;
drop table if exists settings;

-- ----------------------------------------------------------
--  1. 메모판  <- 이 과제의 심장
--
--  어제 봇은 슬롯을 봇 안(gr.State)에 두었습니다.
--  새로고침하면 날아가고, 웹에서는 볼 수 없었습니다.
--  이제 슬롯이 여기 삽니다. 봇은 매번 여기서 꺼내 쓰고 다시 적습니다.
--  code(입장 코드)가 손님을 가르는 칸막이입니다. 회원가입 대신 쓰는 아이디입니다.
-- ----------------------------------------------------------
create table sessions (
  code         text primary key,      -- 입장 코드.  '1' 번 손님 · '5' 번 손님

  place_kind   text,                  -- 장소-종류    식당 / 숙소 / 관광
  place_name   text,                  -- 장소-이름
  pickup       text,                  -- 택시-출발지
  dropoff      text,                  -- 택시-도착지
  request_time text,                  -- 택시-출발시간

  carried      boolean default false, -- 도착지가 장소에서 이월된 것인가
  ride_id      bigint references rides(id),  -- 영수증이 나오면 그 호출 번호
  turns        int default 0,         -- 몇 번 말했나 (턴은 늘 1콜입니다)

  updated_at   timestamptz default now()
);

-- ----------------------------------------------------------
--  2. 설정판  <- 봇 주소를 코드에 안 박기 위한 표
--
--  gradio 의 공개 주소는 72시간마다 바뀝니다.
--  코드에 박아두면 바뀔 때마다 웹을 다시 배포해야 합니다.
--  여기에 두면 봇을 껐다 켜기만 하면 웹이 알아서 따라옵니다.
-- ----------------------------------------------------------
create table settings (
  key        text primary key,        -- 'bot_url' (어제 봇) · 'bot2_url' (오늘 봇)
  value      text,
  updated_at timestamptz default now()
);

-- ----------------------------------------------------------
--  3. 자물쇠 풀기  <-- 이것을 빼먹으면 저장이 안 됩니다
-- ----------------------------------------------------------
alter table sessions enable row level security;
alter table settings enable row level security;

create policy "실습 전체허용 sessions" on sessions for all using (true) with check (true);
create policy "실습 전체허용 settings" on settings for all using (true) with check (true);
