-- ============================================================
--  Supabase 표 만들기  (식당 + 택시)
--  Supabase 화면 왼쪽 [SQL Editor] 에 통째로 붙여 넣고 Run
--  두 번 돌려도 안전합니다 (있으면 지우고 다시 만듭니다)
-- ============================================================

drop table if exists rides;
drop table if exists drivers;
drop table if exists restaurants;

-- ----------------------------------------------------------
--  1. 식당 표  <- 1번 블록.  손님이 여기서 하나를 고릅니다
-- ----------------------------------------------------------
create table restaurants (
  id       bigserial primary key,
  name     text not null,
  area     text not null,   -- 서울 중앙 / 동쪽 / 서쪽 / 남쪽 / 북쪽
  category text not null,   -- 한식 / 중식 / 일식 / 양식 / 아시아음식
  price    text not null,   -- 저렴 / 보통 / 비싼
  phone    text
);

-- ----------------------------------------------------------
--  2. 기사 표  <- 2번 블록에서 배차할 때 꺼내 씁니다
-- ----------------------------------------------------------
create table drivers (
  id           bigserial primary key,
  name         text not null,
  phone        text not null,
  vehicle_type text not null,          -- 일반 / 모범 / 대형
  is_available boolean default true
);

-- ----------------------------------------------------------
--  3. 호출 표  <- 두 블록이 만나는 곳. 한 건이 한 줄
-- ----------------------------------------------------------
create table rides (
  id           bigserial primary key,

  -- 1번 블록에서 넘어온 것
  place_name    text,                  -- 고른 식당 이름
  place_booking text,                  -- 예약번호
  carried       boolean default false, -- 도착지가 식당에서 이월된 것인가  <- 체크리스트 2번의 증거

  -- 2번 블록
  pickup       text,                   -- 출발지
  dropoff      text,                   -- 도착지
  request_time text,                   -- 출발 시간 (그냥 글자로 받습니다)
  vehicle_type text default 'dontcare',-- 94%가 '아무거나' 이므로 이것이 기본값
  status       text default '접수',     -- 접수 / 배차완료 / 취소
  driver_id    bigint references drivers(id),

  -- 9개 시나리오 비교용
  source       text default 'web',     -- 'web' 인가 'bot' 인가
  change_count int  default 0,         -- 접수 후 몇 번 고쳤나

  created_at   timestamptz default now(),
  updated_at   timestamptz default now()
);

-- ----------------------------------------------------------
--  4. 식당 10곳 미리 넣기
-- ----------------------------------------------------------
insert into restaurants (name, area, category, price, phone) values
  ('소문난 감자탕',   '서울 서쪽', '한식',      '저렴', '02-111-1111'),
  ('할매 순대국',     '서울 북쪽', '한식',      '저렴', '02-222-2222'),
  ('한우다이닝 목',   '서울 중앙', '한식',      '비싼', '02-333-3333'),
  ('북경장',         '서울 서쪽', '중식',      '보통', '02-444-4444'),
  ('사천루',         '서울 남쪽', '중식',      '비싼', '02-555-5555'),
  ('스시 하나',      '서울 중앙', '일식',      '비싼', '02-666-6666'),
  ('돈카츠 마루',    '서울 동쪽', '일식',      '보통', '02-777-7777'),
  ('트라토리아 봄',  '서울 남쪽', '양식',      '보통', '02-888-8888'),
  ('스테이크 하우스','서울 중앙', '양식',      '비싼', '02-999-9999'),
  ('방콕 키친',      '서울 동쪽', '아시아음식', '저렴', '02-101-0101');

-- ----------------------------------------------------------
--  5. 기사 5명 미리 넣기
-- ----------------------------------------------------------
insert into drivers (name, phone, vehicle_type) values
  ('김민수', '010-1111-2222', '일반'),
  ('박지영', '010-3333-4444', '일반'),
  ('이창호', '010-5555-6666', '모범'),
  ('정수연', '010-7777-8888', '모범'),
  ('최대현', '010-9999-0000', '대형');

-- ----------------------------------------------------------
--  6. 자물쇠 풀기  <-- 이것을 빼먹으면 저장이 안 됩니다
--     실습이므로 누구나 읽고 쓸 수 있게 열어둡니다.
-- ----------------------------------------------------------
alter table restaurants enable row level security;
alter table drivers     enable row level security;
alter table rides       enable row level security;

create policy "실습 전체허용 restaurants" on restaurants for all using (true) with check (true);
create policy "실습 전체허용 drivers"     on drivers     for all using (true) with check (true);
create policy "실습 전체허용 rides"       on rides       for all using (true) with check (true);
