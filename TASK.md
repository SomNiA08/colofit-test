# ColorFit Task Tracker

**프로젝트 기간:** 5주 (W1: 3/24~3/28 ~ W5: 4/21~4/25)
**현재 상태:** W2 진행 중 (2026-04-05)
**Fallback 기준:** W3 금요일에 가격비교 미완이면 Fallback 발동

**사용법:** Claude Code에게 `"Task 1.3을 진행해줘"` 처럼 번호로 지시하세요.

---

## Phase 0: 수요 검증 (이번 주, W2 병행)

> office-hours 세션에서 도출된 새 기능 방향 (디지털 옷장 + 아바타 착용) 검증.
> 개발 착수 전 5명 반응 수집. 3명 이상 "신기한데" or "써보고 싶어"면 W3에 Lane E 착수.

**Task P0.1 — 수동 컨시어지 테스트**
- [ ] Figma로 아바타 캐릭터 기본 실루엣 1개 제작 (또는 무료 스티커 활용)
- [ ] 지인 5명에게 "내 옷 사진 보내줘 → 아바타에 입혀줄게" 메시지 발송
- [ ] Figma/Photoshop으로 수동으로 옷 이미지 아바타 위에 합성
- [ ] 반응 기록: 이름, "신기한데"/"그래서?"/"써보고 싶어" 등 그대로 메모
- [ ] **Go/No-go 판단**: 5명 중 3명 이상 긍정 반응 → Task P0.2 진행, 미달 → 아바타 방향 재검토

**Task P0.2 — Go 판정 시 기술 스파이크 (1~2일)**
- [ ] remove.bg API 테스트: 옷 사진 3장으로 배경 제거 품질 확인 (무료 50장/월)
- [ ] Canvas/SVG 오버레이 방식 PoC: 배경 제거 PNG → 고정 캐릭터 위에 겹치기
- [ ] 결과 스크린샷으로 팀 공유 → W3 Lane E 착수 여부 최종 결정

---

---

## W1: 데이터 + 인프라 (3/24~3/28)

### Lane A: 데이터 파이프라인

**Task 1.1 — 12톤 팔레트 JSON 생성** ✅ 완료 (2026-03-28)
- [x] `backend/data/palettes/` 디렉토리 생성
- [x] 12개 톤별 JSON 파일 생성 (예: `spring_warm_light.json`)
- [x] 각 톤당 25개 대표 색상 (HEX, RGB, HSL, 한글 색상명)
- [x] 총 300개 색상 데이터 (12톤 × 25색)
- [x] 참조: 기획서 섹션 7.1 (12-tone 분류 체계)

**Task 1.2 — 브랜드 화이트리스트 JSON** ✅ 완료 (2026-03-28)
- [x] `backend/data/brand_whitelist.json` 생성
- [x] 인지도 있는 브랜드 133개 리스트 (무신사 스탠다드, 유니클로, COS 등)
- [x] 형식: `["무신사 스탠다드", "유니클로", ...]`

**Task 1.3 — 네이버 쇼핑 API 수집 스크립트 기본 구조** ✅ 완료 (2026-03-28)
- [x] `backend/scripts/curate_by_tone.py` 생성
- [x] 네이버 쇼핑 API 호출 함수 (`search_products(query, display, start)`)
- [x] API 응답 파싱 + raw JSON 저장
- [x] Rate limit 처리 (exponential backoff: 1s→2s→4s→8s)
- [x] `.env`에서 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` 읽기
- [x] 테스트: `python curate_by_tone.py test` 로 연결 확인 가능
- ⚠️ API 키 발급 후 `.env` 파일 작성 필요 (Task 1.5 실행 전 필수)

**Task 1.4 — 톤별 수집 키워드 설계** ✅ 완료 (2026-03-28)
- [x] `backend/data/tone_queries.json` 생성
- [x] 12톤별 검색 키워드 리스트 (톤 x 카테고리)
- [x] 예: `"spring_warm_light": ["봄 코랄 블라우스", "아이보리 원피스", ...]`
- [x] 카테고리: outer, top, bottom, onepiece, shoes, bag, acc
- [x] 참조: 기획서 섹션 5.2 (수집 쿼리 설계)
- ⚠️ 총 312개 쿼리 (12톤 × 26개 평균). 수집 후 부족 톤은 동의어 확장 쿼리 추가 예정

**Task 1.5 — 상품 수집 실행** ✅ 완료 (2026-03-28)
- [x] Task 1.3 스크립트로 실제 수집 실행
- [x] 4톤 병렬 수집 x 3라운드 = 12톤 커버
- [x] raw JSON을 `backend/data/raw/` 에 톤별 저장
- [x] 목표: 25,000개 상품
- [x] 톤별 수집량 확인 (최소 1,000개/톤)
- 📊 실제 수집 결과: 총 55,600개 (목표 대비 222%)
  - spring_warm_light: 3,778개 / spring_warm_bright: 3,069개 / spring_warm_mute: 3,263개
  - summer_cool_light: 3,430개 / summer_cool_soft: 3,190개 / summer_cool_mute: 2,440개
  - autumn_warm_deep: 5,930개 / autumn_warm_mute: 6,492개 / autumn_warm_bright: 6,000개
  - winter_cool_deep: 5,956개 / winter_cool_bright: 6,216개 / winter_cool_light: 5,836개

**Task 1.6 — 전처리: 상품 정규화** ✅ 완료 (2026-03-28)
- [x] `backend/scripts/rebuild_from_tones.py` 생성
- [x] HTML 태그 제거 (`<b>` 등 title에 포함된 태그)
- [x] 브랜드명 추출 (mall_name 화이트리스트 확인 → title 파싱 → mall_name 폴백 3단계)
- [x] 정규화 결과를 `NormalizedProduct` 형식으로 출력
- [x] 참조: 기획서 섹션 5.4 (전처리 과정)
- 📊 결과: 고유 상품 39,149개 (중복 16,451개 제거) → `data/normalized/normalized_products.json`
  - HTML 태그 잔존: 0개 (100% 제거)
  - 화이트리스트 브랜드 히트: 14,563개 (37.2%) / 브랜드 미확인: 0개
  - color_hex, category는 Task 1.7 / 1.8에서 채울 예정

**Task 1.7 — 전처리: 이미지 색상 추출 + 톤 매핑** ✅ 완료 (2026-03-29)
- [x] PIL + scikit-learn K-means로 상위 3개 dominant color 추출
- [x] 추출된 HEX → 12톤 팔레트와 RGB 유클리드 거리 비교
- [x] 가장 가까운 톤 ID 매핑 (`tone_id` 부여)
- [x] 참조: 기획서 섹션 7.1 (상품 색상 → 톤 매핑 흐름도)
- 📊 결과: 39,145/39,149개 color_hex + tone_id 부여 (실패 4개, 99.99% 성공)
  - winter_cool_light: 6,767개 / autumn_warm_mute: 5,501개 / summer_cool_light: 5,240개
  - spring_warm_mute: 5,205개 / winter_cool_deep: 4,792개 / summer_cool_soft: 4,439개
  - summer_cool_mute: 2,353개 / autumn_warm_deep: 2,350개 / spring_warm_light: 1,526개
  - autumn_warm_bright: 448개 / spring_warm_bright: 358개 / winter_cool_bright: 166개

**Task 1.8 — 전처리: 하이브리드 카테고리 분류** ✅ 완료 (2026-03-29)
- [x] 키워드 기반 분류 딕셔너리 (31개 카테고리 x 3~5 키워드)
- [x] 키워드 매칭 실패 시 Gemini Flash 폴백 분류 (코드 완성, API 활성화 후 재실행 가능)
- [x] LLM 분류 결과 캐싱 (`backend/data/llm_cache.json`)
- [x] 분류 속성: category, silhouette, formality, tpo, gender
- [x] 참조: 기획서 섹션 5.4.1 (하이브리드 분류 체계)
- 📊 결과: 38,968/39,149개 분류 완료 (99.5%)
  - 키워드 분류: 38,968개 (99.5%) / 미분류: 181개 (비패션 상품 — 아이스박스·음료 등)
  - female: 31,472개 / unisex: 6,416개 / male: 1,080개
  - 상위 카테고리: onepiece 5,424 / jacket 3,248 / skirt 3,248 / slacks 2,763 / blouse 2,585
  - ⚠️ Gemini 폴백 미실행 (신규 API 키 무료 한도 초기화 대기 중, --resume으로 재실행 가능)

**Task 1.9 — 코디 레시피 JSON 정의** ✅ 완료 (2026-03-29)
- [x] `backend/data/outfit_recipes.json` 생성
- [x] 여성 TPO 8종 x 무드 레시피 (필수/선택/금지 카테고리, 포멀도 범위)
- [x] 남성 TPO 8종 x 무드 레시피
- [x] 참조: 기획서 섹션 5.3.1 (TPO x 무드 레시피 매트릭스)
- 📊 결과: 총 16개 레시피 (여성 8 + 남성 8) → `data/outfit_recipes.json`
  - 여성: interview/commute/date/weekend/campus/travel/event/workout
  - 남성: interview/commute/date/weekend/campus/travel/event/workout
  - 각 레시피: required(OR그룹) + optional + forbidden + formality_range + moods + silhouette_hints

**Task 1.10 — 코디 조합 생성 알고리즘** ✅ 완료 (2026-03-29)
- [x] 레시피 기반 코디 조합 생성 스크립트 (`backend/scripts/generate_outfits.py`)
- [x] 필수 카테고리 선택 → 선택 카테고리 확률적 추가 → 금지 카테고리 검증
- [x] 포멀도 편차 ≤ 2, 가격 비율 5배 이내, 중복 조합 방지
- [x] designed_tpo, designed_moods 태그 부여
- [x] 참조: 기획서 섹션 5.3.1 (조합 알고리즘 의사코드)
- 📊 결과: 1,212개 생성 → `data/outfits.json`
  - 여성: 828개 / 남성: 384개
  - TPO별: date 189 / weekend 186 / commute 171 / event 171 / interview 162 / travel 135 / campus 108 / workout 90
  - ⚠️ 목표(1,500~1,900개) 미달 — 남성 상품 부족 (spring_warm/male 톤에서 shirt/slacks 희소)

**Task 1.11 — 코디 품질 평가** ✅ 완료 (2026-03-29)
- [x] `backend/scripts/evaluate_outfits.py` 생성
- [x] 규칙 기반 평가 (5점 척도) — Gemini 대신 포멀도/TPO/구성 완성도 기반
- [x] 3점 미만 코디 제거
- [x] 평가 결과를 `llm_quality_score` 필드에 저장
- ⚠️ 1,212개 평가 → 62개 제거 → 최종 1,150개 (목표 1,500개 미달, 남성 상품 부족 동일 원인)
- 점수 분포: 5점 56개 / 4점 689개 / 3점 405개 / 2점(제거) 62개
- Gemini 재평가 (2026-03-30): 통과 1,056개 | 실제 평가 399개, Rate Limit 기본 3점 처리 813개 ⚠️

### Lane B: 인프라 셋업

**Task 1.12 — Next.js 15 프로젝트 초기화**
- [x] `frontend/` 디렉토리에 Next.js 15 (App Router) 생성
- [x] TypeScript 설정
- [x] TailwindCSS 4.0 설치 + 설정
- [x] Framer Motion 11 설치 (v12.38.0 설치됨)
- [x] 동작 확인: `npm run dev` → localhost:3000
⚠️ Next.js 16.2.1 설치됨 (15 최신 = 16.x 브랜드, App Router 동일), Framer Motion v12 설치

**Task 1.13 — 프론트엔드 디자인 토큰 세팅**
- [x] DESIGN.md 읽고 CSS variables 세팅 (`globals.css`)
- [x] 컬러 토큰 (--bg, --surface, --accent, --border 등)
- [x] 스코어 축 컬러 5개
- [x] 다크모드 토큰 (`[data-theme="dark"]`)
- [x] 스페이싱 스케일 (--space-2xs ~ --space-3xl)
- [x] Nanum Myeongjo Google Fonts 로딩 설정
⚠️ Pretendard Variable은 Google Fonts 미지원 → jsdelivr CDN 링크로 layout.tsx에 추가

**Task 1.14 — FastAPI 프로젝트 초기화** ✅ 완료 (2026-03-30)
- [x] `backend/` 디렉토리에 FastAPI 프로젝트 생성
- [x] `requirements.txt` (fastapi, uvicorn, pydantic, sqlalchemy, httpx, pillow, numpy, scikit-learn)
- [x] 프로젝트 구조: `app/main.py`, `app/config.py`, `app/routers/`, `app/services/`, `app/models/`, `app/schemas/`, `app/db/`
- [x] CORS 미들웨어 설정 (localhost:3000 허용)
- [x] 헬스체크 엔드포인트 (`GET /health`)
- [x] 동작 확인: `uvicorn app.main:app --reload` → localhost:8000/docs

**Task 1.15 — DB 스키마 적용**
- [x] Supabase 연결 설정 (`app/db/database.py`)
- [x] SQLAlchemy 2.0 모델 정의
  - [x] `models/user.py` (users 테이블)
  - [x] `models/product.py` (products 테이블)
  - [x] `models/outfit.py` (outfits 테이블)
  - [x] `models/reaction.py` (reactions 테이블)
  - [x] `models/style_seed.py` (style_seeds 테이블)
  - [x] `models/user_preference.py` (user_preferences 테이블)
- [x] 인덱스 생성 (tone_id, designed_tpo, gender)
- [x] 참조: 기획서 섹션 14.4 (DB 스키마)

**Task 1.16 — 배포 설정**
- [x] Vercel 연결 (frontend/) — `vercel.json` 생성 (rootDirectory: frontend)
- [x] Railway 연결 (backend/) — `Dockerfile` + `railway.json` 생성
- [x] 환경변수 설정 (각 플랫폼) — `.env.example` 생성 (frontend, backend)
- [x] 배포 확인: 프론트 + 백엔드 둘 다 접속 가능

### W1 완료 기준
- [ ] 상품 DB 20,000건 이상 (Task 1.5)
- [ ] 코디 1,500개 이상, Gemini 평가 통과 (Task 1.11)
- [x] 프론트/백엔드 빈 프로젝트 배포 성공 (Task 1.16)

---

## W2: 추천 엔진 + 온보딩 (3/31~4/4)

### Lane C: 추천 엔진 코어

**Task 2.1 — PCF 스코어링 (퍼스널컬러 적합도)** ✅ 완료 (2026-04-05)
- [x] `backend/app/services/scoring.py` 생성
- [x] `calculate_pcf(item_tone_ids, item_hex_colors, user_tone_id)` 함수
- [x] 톤 레벨 매칭 (동일 100, 호환 95) + 색상 레벨 매칭 (RGB 거리 → 점수)
- [x] pytest 테스트: 동일 톤, 호환 톤, 반대 시즌, 경계값 — 24/24 통과
- [x] 참조: 기획서 섹션 5.5.1

**Task 2.2 — OF 스코어링 (TPO 적합도)** ✅ 완료 (2026-04-05)
- [x] `calculate_of(outfit_tags, user_tpo_list)` 함수
- [x] TPO 동의어 확장 매핑 (commute↔office 등, 11개 TPO 커버)
- [x] match_count 기반 점수 변환 (30점 하한)
- [x] pytest 테스트: 정확 매칭, 동의어 매칭, 미매칭 — 26개 테스트 전체 통과 (누적 50/50)
- [x] 참조: 기획서 섹션 5.5.2

**Task 2.3 — CH 스코어링 (색상 조화)** ✅ 완료 (2026-04-05)
- [x] `calculate_ch(item_hex_colors)` 함수
- [x] 모든 아이템 쌍의 RGB 거리 → 구간별 점수 (유사색/보색/과도한 대비)
- [x] 채도 보너스 (+5점, 표준편차 0.15~0.40)
- [x] pytest 테스트: 올블랙, 톤온톤, 보색, 형광+파스텔 — 29개 테스트 전체 통과 (누적 79/79)
- [x] 참조: 기획서 섹션 5.5.3

**Task 2.4 — PE 스코어링 (가격 효율)** ✅ 완료 (2026-04-05)
- [x] `calculate_pe(total_price, budget_min, budget_max)` 함수
- [x] 3개 Case: 범위 내 (중앙 가까울수록 높음), 초과 (감점), 미만 (완만 감점, 최저 40점)
- [x] pytest 테스트: 중앙, 상한, 하한, 50%+ 초과, 극단 저가 — 19개 테스트 전체 통과 (누적 98/98)
- [x] 참조: 기획서 섹션 5.5.4

**Task 2.5 — SF 스코어링 (스타일 적합도)** ✅ 완료 (2026-04-05)
- [x] `calculate_sf(items)` 함수
- [x] 카테고리 궁합 점수 (50%) — `data/style_compat.json` 매트릭스 참조
- [x] 실루엣 밸런스 점수 (25%) — Y/A/I/X 라인 15개 규칙
- [x] 포멀도 일관성 점수 (25%) — 표준편차 x 40 감점
- [x] pytest 테스트: 블라우스+슬랙스(86.25점), 후드+정장(31.25점 < 55점 컷오프) — 34개 테스트 전체 통과 (누적 132/132)
- [x] 참조: 기획서 섹션 5.5.5, 6.6

**Task 2.6 — 스타일 호환성 데이터 파일** ✅ 완료 (2026-04-05)
- [x] `backend/data/style_compat.json` 생성 — 카테고리 궁합 227개 조합 점수
- [x] `backend/data/silhouette_rules.json` 생성 — 실루엣 15개 조합
- [x] `backend/data/formality_map.json` 생성 — 아이템별 포멀도 (1~5) 33개 규칙
- [x] 참조: 기획서 섹션 6.6

**Task 2.7 — StyleFilter (규칙 기반 사전 필터)** ✅ 완료 (2026-04-05)
- [x] `backend/app/services/style_filter.py` 생성
- [x] `detect_category(title, category3)` — 키워드 → 캐시 → LLM 3단계
- [x] `filter_outfit(items)` — 3축 가중합 계산, 55점 미만 False
- [x] pytest 테스트: 통과(블라우스+슬랙스), 탈락(후드+정장), 55점 경계 — 26개 테스트 전체 통과 (누적 158/158)
- [x] 참조: 기획서 섹션 6.6

**Task 2.8 — Hard Filter 체인** ✅ 완료 (2026-04-05)
- [x] `backend/app/services/feed_builder.py` 생성
- [x] Hard Filter 8단계 순차 적용 (H1 성별 → H2 예산 → H3 계절 → H4 TPO → H5 브랜드 → H7 톤 → H8 StyleFilter → H6 LLM)
- [x] 각 필터는 독립 함수로 분리 (h1_gender ~ h8_style_filter + apply_hard_filters)
- [x] pytest 테스트: 각 필터별 통과/탈락 + 통합 체인 — 50개 테스트 전체 통과 (누적 208/208)
- [x] 참조: 기획서 섹션 5.4 (Hard Filter 상세)

**Task 2.9 — Soft Score + 리랭킹** ✅ 완료 (2026-04-05)
- [x] feed_builder.py에 Soft Score 계산 추가 (5축 가중합: PCF×0.25 + OF×0.20 + CH×0.15 + PE×0.15 + SF×0.25)
- [x] 리랭킹: 완성 코디 가산(+3점), dislike 제외, 톤 다양성(동일 톤 3개 제한), 메인아이템 중복 제거(1개 제한)
- [x] 개인화 보정 (-10 ~ +10): 선호 톤/카테고리/브랜드 일치 가감
- [x] 상위 200개 반환
- [x] pytest 테스트: 5축 가중합, 가중치 오버라이드, 완성도 가산, dislike 제외, 톤 다양성, 메인아이템 중복, 개인화 보정 순위역전 — 22개 테스트 전체 통과 (누적 230/230)
- [x] 참조: 기획서 섹션 6.1

**Task 2.10 — 추천 이유 생성** ✅ 완료 (2026-04-06)
- [x] `backend/app/services/reason_generator.py` 생성
- [x] 5축 가중 기여도 계산 → 상위 2개 축 선택
- [x] high(75점+) / mid(75점 미만) 템플릿 분기
- [x] 톤별 한글 이름 매핑 ("여름쿨소프트 핵심 컬러...")
- [x] pytest 테스트: PCF 최고 기여, OF 최고 기여, 동점 처리, 75점 경계, 가중치 오버라이드 등 — 24개 테스트 전체 통과 (누적 254/254)
- [x] 참조: 기획서 섹션 6.4

**Task 2.11 — Feed API 엔드포인트** ✅ 완료 (2026-04-06)
- [x] `backend/app/routers/feed.py` — GET /api/feed
- [x] 파라미터: tone_id, tpo, gender, budget_min, budget_max, page
- [x] Profile Load → Filter → StyleFilter → Score → Rerank → Reason 전체 파이프라인
- [x] 응답: 코디 리스트 + 5축 스코어 + 이유 2줄
- [x] `backend/app/routers/outfit.py` — GET /api/outfit/{id}
- [x] Pydantic 스키마 정의 (`schemas/outfit.py`)

**Task 2.12 — 스코어 프리컴퓨팅** ✅ 완료 (2026-04-06)
- [x] `backend/scripts/precompute_scores.py` 생성
- [x] CH(색상 조화)·SF(스타일 적합도) 사전 계산 — 사용자 무관 2축 (PCF·OF·PE는 사용자별 런타임 계산)
- [x] outfits.scores JSONB에 저장 (--dry-run 옵션 지원)
- [x] compute_soft_scores()에서 캐시된 CH·SF 재사용, 없으면 런타임 폴백
- [x] 기존 테스트 254개 전체 통과 (누적 254/254)

### Lane D: 온보딩 + 피드 UI

**Task 2.13 — 온보딩 공통 레이아웃** ✅ 완료 (2026-04-06)
- [x] `frontend/app/onboarding/layout.tsx` — 공통 레이아웃
- [x] 상단 진행 바 (5단계, Marsala 채움, 세그먼트별 0.4s ease-out 애니메이션)
- [x] 뒤로가기 버튼 (Step 1에서는 숨김, router.back())
- [x] 좌→우 슬라이드 전환 (Framer Motion AnimatePresence, mode="wait")
- [x] MotionConfig reducedMotion="user" — prefers-reduced-motion 접근성 지원
- [x] TypeScript 타입 에러 없음
- [x] 참조: 기획서 섹션 8.4.1

**Task 2.14 — 온보딩 Step 1: 성별 선택** ✅ 완료 (2026-04-06)
- [x] `frontend/app/onboarding/step1/page.tsx`
- [x] "나에 대해 알려주세요" 헤드라인 (Nanum Myeongjo 28px) + 서브텍스트
- [x] 여성/남성 2개 카드 (가로 배치, w-[45%], aspect-[3/4], radius-xl)
- [x] 탭 시 scale 1.05 + Marsala 아웃라인 → 400ms 후 자동 Step 2 이동
- [x] 진입 애니메이션: fadeInUp 0.4s, stagger 0.15s
- [x] "건너뛰기" 텍스트 링크 (기본값 female 저장 후 Step 2 이동)
- [x] 성별 선택값 localStorage 저장 (onboarding_gender)
- [x] TypeScript 타입 오류 없음

**Task 2.15 — 온보딩 Step 2: 퍼스널컬러 선택** ✅ 완료 (2026-04-07)
- [x] `frontend/app/onboarding/step2/page.tsx`
- [x] 시즌별 그라데이션 스트립 4개 (봄/여름/가을/겨울) — 코랄→피치→아이보리 / 라벤더→스카이→민트 / 버건디→테라코타→카멜 / 블랙→로열블루→아이시핑크
- [x] 각 스트립 아래 세부 톤 칩 3개 (32px 원형, 탭 시 Marsala 링 표시)
- [x] 선택 시 다른 시즌 디밍 (opacity 0.4)
- [x] "잘 모르겠어요" → 바텀시트 간이 진단 2문항 (피부 언더톤 + 자주 입는 상의 색 계열)

**Task 2.16 — 온보딩 Step 3: TPO + 무드 선택** ✅ 완료 (2026-04-07)
- [x] `frontend/app/onboarding/step3/page.tsx`
- [x] TPO 8종 필 버튼 (성별에 따라 다른 세트) — 여성/남성 각 8종 (출근/데이트/면접/주말/캠퍼스/여행/행사/운동)
- [x] 무드 태그 클라우드 (성별에 따라 다른 세트) — 여성(캐주얼/미니멀/러블리/클래식/스트릿/에디토리얼) / 남성(캐주얼/미니멀/댄디/클래식/스트릿/아메카지)
- [x] 복수 선택: TPO 최대 3개, 무드 최대 5개 (선택 개수 표시)
- [x] 상단 퍼스널컬러 칩 미리보기 (localStorage에서 읽기)
- [x] 선택값 localStorage 저장 (onboarding_tpo, onboarding_mood)

**Task 2.17 — 온보딩 Step 4: 예산 설정** ✅ 완료 (2026-04-07)
- [x] `frontend/app/onboarding/step4/page.tsx`
- [x] 듀얼 썸 레인지 슬라이더 (min/max)
- [x] 빠른 프리셋 4개 버튼 (~3만 / 3~7만 / 7~15만 / 15만~)
- [x] "추천 코디 보러가기" CTA (풀와이드, Marsala)

**Task 2.18 — 온보딩 Step 5: 비주얼 취향 분석** ✅ 완료 (2026-04-07)
- [x] `frontend/app/onboarding/step5/page.tsx`
- [x] 2x2 이미지 그리드, 4라운드
- [x] 탭 시 선택 → 0.5s 후 다음 라운드 crossfade
- [x] "패스" 링크, 라운드 인디케이터
- [x] 완료 후 피드로 전환 ⚠️ 이미지 src는 picsum 플레이스홀더. 실제 패션 사진으로 교체 필요

**Task 2.19 — 온보딩 API 연동** ✅ 완료 (2026-04-07)
- [x] `backend/app/routers/onboarding.py` — POST /api/onboarding
- [x] 프론트에서 5 Step 결과를 모아서 전송
- [x] users 테이블 + style_seeds 테이블에 저장
- [x] 프론트 → API 호출 연동 (`frontend/lib/api.ts` + step5 완료 시 호출)

**Task 2.20 — 코디 카드 컴포넌트**
- [ ] `frontend/components/OutfitCard.tsx`
- [ ] 이미지 (3:4, rounded-lg) + 아이템 수 뱃지 + 하트 아이콘
- [ ] 제목 (Nanum Myeongjo 16px) + 가격 (bold) + 추천 이유 1줄
- [ ] 스코어 뱃지 미니 필 2개 ("PCF 95" "OF 80")
- [ ] fadeInUp 등장 애니메이션

**Task 2.21 — 코디 피드 화면**
- [ ] `frontend/app/feed/page.tsx`
- [ ] 헤더 (ColorFit 로고 + 프로필 아이콘)
- [ ] TPO 탭 필터 (가로 스크롤 필 버튼)
- [ ] 예산 슬라이더 (접힌 상태, 탭 시 펼침)
- [ ] "오늘의 컬러핏" 특별 카드 (피드 최상단)
- [ ] OutfitCard 리스트 (무한 스크롤, 커서 기반 페이지네이션)
- [ ] GET /api/feed 연동
- [ ] 스켈레톤 로딩 + empty state + error state

**Task 2.22 — save/dislike 인터랙션**
- [ ] 좌 스와이프 → dislike (카드 슬라이드 아웃 + "관심없음" 토스트)
- [ ] 더블탭 → save (하트 뿅 애니메이션, Marsala 전환)
- [ ] 우상단 하트 탭 → save 토글
- [ ] POST /api/reaction 연동 (save/dislike)
- [ ] `backend/app/routers/reaction.py` — POST /api/reaction

**Task 2.23 — 코디 상세 화면**
- [ ] `frontend/app/outfit/[id]/page.tsx`
- [ ] 히어로 이미지 (풀블리드, parallax scroll)
- [ ] 5축 스코어 바 차트 (width 0% → 실제값, ease-out 0.8s)
- [ ] 추천 이유 카드 (배경 #F0EDE8)
- [ ] 아이템 캐러셀 (가로 스크롤, 80px 정사각 이미지)
- [ ] 코디 합계 가격 + 최저가 합산
- [ ] 하단 CTA ("저장" + "A vs B 비교")
- [ ] GET /api/outfit/{id} 연동

**Task 2.24 — 하단 탭바**
- [ ] `frontend/components/BottomTabBar.tsx`
- [ ] 홈/저장/Top/마이 4탭
- [ ] 활성 탭: Marsala 아이콘 + bold 라벨
- [ ] 전환 모션: 아이콘 scale 0.9→1.1→1.0

### W2 완료 기준
- [ ] 5 Step 온보딩 → 코디 피드 진입 동작
- [ ] 스코어링 기반 피드가 실제 데이터로 동작
- [ ] save/dislike 동작
- [ ] 추천 이유 2줄 노출

---

## W3: 가격비교 + 유사상품 (4/7~4/11)

**Task 3.1 — 유사 상품 매칭 서비스**
- [ ] `backend/app/services/similar_finder.py` 생성
- [ ] 색상 유사도 (가중치 0.6) + 가격 유사도 (0.4) 계산
- [ ] Exact(동일 상품 다른 판매처) / Similar(대체재) 구분
- [ ] 상위 5개 반환
- [ ] pytest 테스트
- [ ] 참조: 기획서 섹션 6.2

**Task 3.2 — 아이템 API**
- [ ] `backend/app/routers/item.py`
- [ ] GET /api/item/{id} — 아이템 상세 + 판매처별 가격
- [ ] GET /api/item/{id}/similar — 유사 상품 리스트
- [ ] Pydantic 스키마 정의

**Task 3.3 — 아이템 상세 화면**
- [ ] `frontend/app/item/[id]/page.tsx`
- [ ] 아이템 이미지 (1:1) + 브랜드 + 상품명 + 가격
- [ ] 가격 비교 테이블 (판매처, 가격, 유형, 바로가기)
- [ ] 최저가 행 하이라이트 (#F0EDE8 + Marsala 뱃지)
- [ ] 유사 상품 섹션 (2열 그리드 + 유사도 % 뱃지)
- [ ] 하단 CTA "최저가 쇼핑몰에서 보기" (Marsala 버튼)

**Task 3.4 — 외부 쇼핑몰 링크**
- [ ] 가격 비교 행 탭 → 새 탭 열기
- [ ] 하단 CTA 탭 → 최저가 쇼핑몰 새 탭
- [ ] 유사 상품 카드 탭 → 해당 아이템 상세로 이동

**Task 3.5 — 프로필/마이페이지**
- [ ] `frontend/app/profile/page.tsx`
- [ ] 톤 카드 (그라데이션 배경 + 톤 이름, Nanum Myeongjo 28px)
- [ ] 잘 어울리는 색 스와치 6개 + 피해야 할 색 4개
- [ ] 내 정보 (성별, TPO, 예산) + "변경" 버튼 → 해당 Step 바텀시트
- [ ] 취향 관리 행 → 취향 관리 화면

**Task 3.6 — 톤 설명 화면**
- [ ] `frontend/app/tone/[id]/page.tsx`
- [ ] 톤 그라데이션 히어로 (height 200px)
- [ ] 시즌 설명 1~2문장
- [ ] 잘 어울리는 색 스와치 + 피해야 할 색 스와치
- [ ] 어울리는 코디 3개 캐러셀
- [ ] "다른 톤으로 변경하기" 버튼
- [ ] `backend/app/routers/tone.py` — GET /api/tone/{id}

**Task 3.7 — 취향 관리 화면**
- [ ] Style Seed 시각화 (무드/실루엣/색감/가격 4축 요약)
- [ ] 학습 상태 진행바 ("피드백 N건 학습됨", 30건 목표)
- [ ] "취향 다시 분석하기" → Step 5 재진행
- [ ] "취향 초기화" → 확인 다이얼로그 → 데이터 삭제

### Lane E: 디지털 옷장 (Phase 0 Go 판정 시에만 진행)

> Phase 0에서 수요 확인된 경우에만 착수. W3 Lane A~D와 병렬 진행.
> 기존 추천 엔진 흐름(핵심 사수 라인)을 절대 밀지 않는다.

**Task 3.E1 — 내 옷장 DB 모델 + API**
- [ ] `backend/app/models/wardrobe_item.py` — WardrobeItem 테이블 생성
  - 필드: `{ id, user_id, image_url, category("상의"|"하의"|"아우터"), color_tags[], avatar_layer_id, created_at }`
- [ ] `backend/app/routers/wardrobe.py`
  - `POST /api/wardrobe/items` — 아이템 등록 (이미지 + 메타데이터)
  - `GET /api/wardrobe/items` — 내 아이템 목록
  - `DELETE /api/wardrobe/items/{id}` — 삭제
- [ ] Supabase Storage 연동 — 이미지 업로드 버킷 설정
- [ ] pytest 테스트

**Task 3.E2 — 배경 제거 파이프라인**
- [ ] `backend/app/services/background_remover.py`
- [ ] remove.bg API 연동 (API key: `.env`에 `REMOVEBG_API_KEY` 추가)
- [ ] 실패/불량 시 응답: `{ "success": false, "message": "배경 제거가 어렵습니다. 단색 배경에서 재촬영해주세요." }`
- [ ] GPT-4o vision으로 category + color_tags 3개 자동 추출
  - 분류 불확실 시 → `needs_review: true` 플래그 → 프론트에서 수동 선택 드롭다운 표시
- [ ] 비용 계획: GPT-4o 이미지 1장 ≈ $0.003, 테스트 100장 기준 약 300원

**Task 3.E3 — 아바타 기본 렌더링 (프론트엔드)**
- [ ] `frontend/components/Avatar.tsx` — 고정 캐릭터 실루엣 (SVG 기반)
  - 성별 선택값에 따라 기본 실루엣 SVG 로드
  - 레이어 슬롯: top_slot / bottom_slot / outer_slot (각 절대 좌표 고정)
- [ ] `frontend/components/AvatarCanvas.tsx` — Canvas + 아이템 PNG 오버레이
  - `drawImage()`로 슬롯 좌표에 배경 제거된 PNG 렌더링
  - 상/하의/아우터 순서대로 레이어 쌓기
- [ ] 스파이크 실패 시 CSS 대안: `position: absolute` + `object-fit: contain`으로 폴백

**Task 3.E4 — 내 옷장 화면 (프론트엔드)**
- [ ] `frontend/app/wardrobe/page.tsx` — 내 옷장 메인
  - 아바타 프리뷰 영역 (상단 40%)
  - 아이템 그리드 (하단 60%): 카테고리 탭 필터 (전체/상의/하의/아우터)
  - 아이템 카드: 배경 제거 이미지 + 카테고리 뱃지
  - "+" 플로팅 버튼 → 사진 등록 플로우
- [ ] `frontend/app/wardrobe/add/page.tsx` — 사진 등록 플로우
  - 카메라 촬영 / 갤러리 선택 (모바일 웹 `<input type="file" accept="image/*" capture="environment">`)
  - 업로드 → 배경 제거 → 아바타 미리보기 → 카테고리 확인/수정 → 저장
  - 30초 처리 시간 스피너 + "배경을 지우는 중..." 안내

**Task 3.E5 — 하단 탭바에 "내 옷장" 탭 추가**
- [ ] 기존 4탭(홈/저장/Top/마이) → 5탭(홈/저장/내 옷장/Top/마이) 또는 마이 → 내 옷장으로 통합
- [ ] 팀 의견에 따라 결정, 핵심 탭(홈/저장)은 건드리지 않음

**W3 금요일 — Fallback 판단 시점**
- [ ] TASK.md 전체 진행 상황 확인
- [ ] 밀리는 항목이 있으면 Fallback 발동 (CLAUDE.md 참조)
- [ ] Lane E는 Lane A~D가 완료되지 않으면 W4로 이동

### W3 완료 기준
- [ ] 가격 비교 테이블 동작 (Task 3.3)
- [ ] Exact/Similar 구분 표시 (Task 3.1)
- [ ] 외부 쇼핑몰 링크 동작 (Task 3.4)
- [ ] 마이페이지 동작 (Task 3.5)
- [ ] (Lane E) 사진 업로드 → 아바타 착용 데모 가능 (Phase 0 Go 시에만)

---

## W4: 결정 지원 + 통합 (4/14~4/18)

**Task 4.1 — Top Pick 서비스**
- [ ] `backend/app/services/top_pick.py`
- [ ] 저장 목록 기반: 저장 코디 중 최고 점수 1개
- [ ] 전체 DB 기반: 전체 코디 중 최고 점수 1개 (콜드스타트)
- [ ] 시간대 기반 TPO 자동 추론 (오전=출근, 오후=캐주얼, 저녁=데이트)
- [ ] `backend/app/routers/top_pick.py` — GET /api/top-pick

**Task 4.2 — A vs B 비교 서비스**
- [ ] `backend/app/services/comparator.py`
- [ ] 두 코디의 5축 점수 비교 + 결정적 차이 요인 추출
- [ ] `backend/app/routers/compare.py` — GET /api/compare?ids=a,b

**Task 4.3 — 저장 목록 화면**
- [ ] `frontend/app/saved/page.tsx`
- [ ] 2열 그리드 (이미지 3:4 + 1줄 제목 + 가격)
- [ ] 정렬 드롭다운 (최근/점수/가격)
- [ ] 비어있을 때: 일러스트 + "아직 저장한 코디가 없어요" + CTA
- [ ] 롱프레스 → 삭제 확인 바텀시트
- [ ] GET /api/saved 연동

**Task 4.4 — Top Pick 모달**
- [ ] "Top Pick 보기" 버튼 (저장 목록 상단)
- [ ] 풀스크린 모달: 1위 코디 확대 + 추천 이유 3줄 + 5축 바 차트
- [ ] GET /api/top-pick 연동

**Task 4.5 — A vs B 비교 화면**
- [ ] 좌우 분할 (50:50), 각 코디 이미지 + 정보
- [ ] 중앙 5축 비교 (레이더 차트 또는 바 차트 오버레이)
- [ ] 하단 1줄 결론 ("A가 퍼스널컬러에 더 잘 맞아요")
- [ ] GET /api/compare 연동

**Task 4.6 — 로그인 화면**
- [ ] `frontend/app/login/page.tsx`
- [ ] ColorFit 로고 + 서브카피
- [ ] 카카오 로그인 버튼 (#FEE500)
- [ ] 구글 로그인 버튼 (#FFFFFF + border)
- [ ] "게스트로 둘러보기" 텍스트 링크

**Task 4.7 — 소셜 로그인 백엔드**
- [ ] `backend/app/services/jwt.py` — JWT 토큰 발급/검증
- [ ] `backend/app/routers/auth.py` — 카카오/구글 OAuth 콜백
- [ ] 게스트 → 로그인 전환 (저장/Top Pick 접근 시 로그인 요구)

**Task 4.8 — 피드백 개인화 학습**
- [ ] `backend/app/services/preference_tracker.py`
- [ ] 피드백 행동별 가중치: save(+2.0), like(+1.0), click(+0.3), dislike(-1.5)
- [ ] tone/category/brand/price 선호도 누적
- [ ] 10건+ 축적 시 weight_overrides 자동 생성
- [ ] `backend/app/routers/feedback.py` — POST /api/feedback
- [ ] 참조: 기획서 섹션 6.8

**Task 4.9 — 구매 후 피드백 바텀시트**
- [ ] 외부 쇼핑몰 이동 후 복귀 시 자동 표시
- [ ] "이 추천이 도움이 됐나요?" + 3개 버튼
- [ ] 👎 선택 시 이유 태그 추가 표시
- [ ] POST /api/feedback 연동

**Task 4.10 — 통합 테스트**
- [ ] 온보딩 → 피드 → 코디 상세 → 가격비교 → 외부 링크 전체 플로우
- [ ] 저장 → 저장 목록 → Top Pick 플로우
- [ ] Edge case: 코디 0개 결과, 예산 초과, 톤 불일치

### W4 완료 기준
- [ ] Top Pick 동작 (Task 4.4)
- [ ] A vs B 비교 동작 (Task 4.5)
- [ ] 소셜 로그인 동작 (Task 4.7)
- [ ] 전체 플로우 통합 테스트 통과 (Task 4.10)

---

## W5: 폴리싱 + 배포 (4/21~4/25)

**Task 5.1 — 반응형 QA**
- [ ] 모바일 (375px): 전체 화면 확인
- [ ] 태블릿 (768px): 레이아웃 확인
- [ ] 데스크톱 (1280px): 최대 폭 제한 확인
- [ ] 가로 스크롤 없는지 확인
- [ ] 터치 타겟 44px 이상 확인

**Task 5.2 — 다크모드**
- [ ] CSS variables 다크 테마 적용
- [ ] 다크모드 토글 구현 (마이페이지 설정)
- [ ] 웜 언더톤 유지 (#1A1714, 쿨그레이 아님)
- [ ] 스코어 축 컬러 밝기 조정

**Task 5.3 — 성능 최적화**
- [ ] 이미지 lazy loading + Cloudflare CDN 설정
- [ ] 피드 API 응답 800ms 이내 확인
- [ ] Next.js Server Components 활용
- [ ] Lighthouse 성능 점수 확인 (목표: 80+)

**Task 5.4 — 버그 수정**
- [ ] 발견된 버그 목록 정리 + 수정
- [ ] 크로스 브라우저 테스트 (Chrome, Safari)

**Task 5.5 — 프로덕션 배포**
- [ ] 프론트엔드 프로덕션 빌드 + Vercel 배포
- [ ] 백엔드 프로덕션 설정 + Railway 배포
- [ ] 프로덕션 URL 접속 확인

**Task 5.6 — 데모 준비**
- [ ] 데모 시나리오 작성 (페르소나 A 기준: 소개팅 룩 찾기)
- [ ] 데모용 샘플 데이터 확인
- [ ] 발표 자료 작성

### W5 완료 기준
- [ ] 프로덕션 URL 접속 가능 (Task 5.5)
- [ ] 주요 플로우 버그 없음 (Task 5.4)
- [ ] 데모 준비 완료 (Task 5.6)

---

## MVP 핵심 지표 (W5 기준)

| 지표 | 목표 |
|------|------|
| 온보딩 완주율 | >= 60% |
| 회원 전환율 | >= 40% |
| 첫 코디 저장 도달율 | >= 25% |

---

## Fallback 순서 (W3 금요일 판단)

밀릴 경우 아래 순서로 2차 미룸:
1. A vs B 비교 (Task 4.2, 4.5)
2. Top Pick + One-shot (Task 4.1, 4.4)
3. 가격비교 (Task 3.1~3.4, 외부 링크만 유지)
4. 스코어링 5축 → 3축(PCF+OF+SF) (Task 2.1~2.5 단순화)

**절대 미루지 않는 것:** 온보딩 → 코디 피드 → 추천 이유 → save/dislike → 외부 링크
