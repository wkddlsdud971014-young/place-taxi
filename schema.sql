-- ============================================================
--  Supabase 표 만들기  (장소 3종 + 택시)
--  Supabase 화면 왼쪽 [SQL Editor] 에 통째로 붙여 넣고 Run
--  두 번 돌려도 안전합니다 (있으면 지우고 다시 만듭니다)
-- ============================================================

drop table if exists rides;
drop table if exists drivers;
drop table if exists places;
drop table if exists restaurants;   -- 옛 이름. 있으면 같이 치웁니다

-- ----------------------------------------------------------
--  1. 장소 표  <- 1번 블록.  식당 · 숙소 · 관광을 한 표에 담습니다
-- ----------------------------------------------------------
create table places (
  id       bigserial primary key,
  domain   text not null,   -- 식당 / 숙소 / 관광
  name     text not null,
  area     text not null,   -- 서울 중앙 / 동쪽 / 서쪽 / 남쪽 / 북쪽
  category text not null,   -- 식당: 한식·중식·일식·양식·치킨 / 숙소: 호텔·모텔·게스트하우스 / 관광: 역사·자연·쇼핑
  price    text,            -- 저렴 / 보통 / 비싼   (관광은 비어도 됩니다)
  phone    text,
  -- 조건 걸기용. 시나리오 1 "헬스장 있는 숙소" -> "없어도 돼요" 가 이 칸입니다
  gym       boolean default false,   -- 헬스장
  parking   boolean default false,   -- 주차
  breakfast boolean default false    -- 조식
);

-- ----------------------------------------------------------
--  2. 기사 표
-- ----------------------------------------------------------
create table drivers (
  id           bigserial primary key,
  name         text not null,
  phone        text not null,
  vehicle_type text not null,          -- 일반 / 고급 / 대형
  is_available boolean default true
);

-- ----------------------------------------------------------
--  3. 호출 표  <- 두 블록이 만나는 곳
-- ----------------------------------------------------------
create table rides (
  id           bigserial primary key,

  -- 1번 블록에서 넘어온 것
  place_domain  text,                  -- 식당 / 숙소 / 관광
  place_name    text,
  place_booking text,
  carried       boolean default false, -- 도착지가 장소에서 이월된 것인가

  -- 2번 블록
  pickup       text,
  dropoff      text,
  request_time text,
  vehicle_type text default 'dontcare',
  status       text default '접수',     -- 접수 / 배차완료 / 취소
  driver_id    bigint references drivers(id),

  -- 9개 시나리오 비교용
  source       text default 'web',     -- 'web' 인가 'bot' 인가
  change_count int  default 0,

  created_at   timestamptz default now(),
  updated_at   timestamptz default now()
);

-- ----------------------------------------------------------
--  4. 장소 넣기 - 강사님 시나리오에 나오는 곳을 전부 넣습니다
-- ----------------------------------------------------------
insert into places (domain, name, area, category, price, phone, gym, parking, breakfast) values
  -- 관광 : 시나리오 2 · 7 (청와대 -> 경복궁 -> 창덕궁)
  ('관광','청와대',      '서울 중앙','역사','무료','02-730-5800', false,true, false),
  ('관광','경복궁',      '서울 중앙','역사','저렴','02-3700-3900',false,true, false),
  ('관광','창덕궁',      '서울 중앙','역사','저렴','02-3668-2300',false,true, false),
  ('관광','남산서울타워','서울 중앙','자연','보통','02-3455-9277',false,true, false),
  ('관광','가로수길',    '서울 남쪽','쇼핑','무료','02-000-0000', false,false,false),

  -- 숙소 : 시나리오 1 (헬스장 있는 -> 없어도 됨) · 8 (A -> B)
  ('숙소','그랜드 호텔',  '서울 중앙','호텔',        '비싼','02-201-0001', true, true, true),
  ('숙소','시티 호텔',    '서울 동쪽','호텔',        '보통','02-201-0002', true, true, true),
  ('숙소','심미 호스텔',  '서울 서쪽','게스트하우스','저렴','02-201-0003', false,false,true),
  ('숙소','달빛 모텔',    '서울 북쪽','모텔',        '저렴','02-201-0004', false,true, false),
  ('숙소','한강 레지던스','서울 남쪽','호텔',        '보통','02-201-0005', true, false,false),

  -- 식당 : 시나리오 3 (치킨 -> 일식) · 6 (엄중식이라는 식당)
  ('식당','엄중식',        '서울 중앙','한식','보통','02-101-0001',false,true, false),
  ('식당','소문난 감자탕',  '서울 서쪽','한식','저렴','02-101-0002',false,false,false),
  ('식당','바삭 치킨',      '서울 동쪽','치킨','저렴','02-101-0003',false,false,false),
  ('식당','호프 치킨하우스','서울 남쪽','치킨','보통','02-101-0004',false,true, false),
  ('식당','스시 하나',      '서울 중앙','일식','비싼','02-101-0005',false,true, false),
  ('식당','돈카츠 마루',    '서울 동쪽','일식','보통','02-101-0006',false,false,false),
  ('식당','북경장',        '서울 서쪽','중식','보통','02-101-0007',false,true, false),
  ('식당','트라토리아 봄',  '서울 남쪽','양식','보통','02-101-0008',false,false,false);

-- ----------------------------------------------------------
--  5. 기사 넣기  (시나리오 5 는 '고급 택시' 입니다)
-- ----------------------------------------------------------
insert into drivers (name, phone, vehicle_type) values
  ('김민수', '010-1111-2222', '일반'),
  ('박지영', '010-3333-4444', '일반'),
  ('이창호', '010-5555-6666', '고급'),
  ('정수연', '010-7777-8888', '고급'),
  ('최대현', '010-9999-0000', '대형');

-- ----------------------------------------------------------
--  6. 자물쇠 풀기  <-- 이것을 빼먹으면 저장이 안 됩니다
-- ----------------------------------------------------------
alter table places  enable row level security;
alter table drivers enable row level security;
alter table rides   enable row level security;

create policy "실습 전체허용 places"  on places  for all using (true) with check (true);
create policy "실습 전체허용 drivers" on drivers for all using (true) with check (true);
create policy "실습 전체허용 rides"   on rides   for all using (true) with check (true);
