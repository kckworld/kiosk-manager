# Immich Kiosk Manager

Immich Kiosk용 단축 URL 관리 도구입니다.  
슬러그 기반 단축 URL을 생성하여 Immich Kiosk의 긴 URL을 간단하게 공유할 수 있습니다.

예) `https://kiosklink.example.com/mom` → Immich Kiosk URL로 리다이렉트

---

## 요구 사항

- Docker, Docker Compose
- 실행 중인 [Immich](https://immich.app) 서버
- 실행 중인 [Immich Kiosk](https://github.com/damongolding/immich-kiosk) 서버

---

## 설치

### 1. docker-compose.yml 작성

기존 Immich `docker-compose.yml`에 아래 서비스를 추가하거나, 별도 파일로 작성합니다.

```yaml
services:
  kiosk-manager:
    image: kck9010/kiosk-manager:latest
    container_name: kiosk_manager
    network_mode: host
    volumes:
      - ./kiosk-manager/data:/app/data
      - ./kiosk-manager/static:/app/static
      - /var/run/docker.sock:/var/run/docker.sock  # 역지오코딩 실행용 Docker 소켓
    env_file:
      - ./kiosk-manager/.env
    restart: unless-stopped
```

> ⚠️ 역지오코딩 기능을 사용하려면 **반드시** `/var/run/docker.sock` 마운트 필요합니다.

### 2. .env 파일 작성

`./kiosk-manager/.env` 파일을 생성하고 아래 내용을 채웁니다.

```env
IMMICH_URL=http://127.0.0.1:2283
IMMICH_API_KEY=your_immich_api_key
BASE_KIOSK_URL=https://kiosk.example.com
BASE_SHORT_URL=https://kiosklink.example.com
DATABASE_URL=sqlite:///./data/kiosk_links.db

# 역지오코딩용 PostgreSQL 접속 정보 (기본값 표시)
DB_HOST=127.0.0.1
DB_PORT=15432
DB_NAME=immich
DB_USER=immich
DB_PASSWORD=immich
```

### 3. 실행

```bash
docker compose up -d kiosk-manager
```

---

## 환경변수 설명

| 변수 | 설명 | 기본값 | 예시 |
|------|------|--------|------|
| `IMMICH_URL` | Immich 서버 주소. `network_mode: host`이므로 `127.0.0.1` 사용 | - | `http://127.0.0.1:2283` |
| `IMMICH_API_KEY` | Immich API 키 ([발급 방법](#immich-api-키-발급)) | - | `T1mknMq...` |
| `BASE_KIOSK_URL` | Immich Kiosk 서버 주소. 단축 URL이 최종적으로 이 주소로 리다이렉트됨 | - | `https://kiosk.example.com` |
| `BASE_SHORT_URL` | kiosk-manager 자체 주소. 생성되는 단축 URL의 도메인이 됨 | - | `https://kiosklink.example.com` |
| `DATABASE_URL` | SQLite DB 경로 | `sqlite:///./data/kiosk_links.db` | - |
| `DB_HOST` | PostgreSQL(Immich) 호스트 | `127.0.0.1` | - |
| `DB_PORT` | PostgreSQL 포트 | `15432` | - |
| `DB_NAME` | PostgreSQL 데이터베이스명 | `immich` | - |
| `DB_USER` | PostgreSQL 사용자명 | `immich` | - |
| `DB_PASSWORD` | PostgreSQL 비밀번호 | `immich` | - |

> ⚠️ `BASE_KIOSK_URL`과 `BASE_SHORT_URL`은 반드시 서로 달라야 합니다.
> - `BASE_KIOSK_URL`: Immich Kiosk가 떠 있는 주소
> - `BASE_SHORT_URL`: kiosk-manager가 떠 있는 주소 (단축 URL 도메인)

---

## Immich API 키 발급

1. Immich 웹 접속
2. 우측 상단 프로필 클릭 > **계정 설정**
3. **API 키** 탭 > **새 API 키** 생성

---

## 역방향 프록시 설정

kiosk-manager는 `8000` 포트로 실행됩니다.  
Nginx, Caddy, Synology DSM 역방향 프록시 등으로 도메인을 연결해주세요.

**Synology DSM 예시:**

| 항목 | 값 |
|------|----|
| 소스 도메인 | `kiosklink.example.com` |
| 대상 호스트 | `localhost` |
| 대상 포트 | `8000` |

---

## 사용 방법

### 단축 링크 관리

1. `https://kiosklink.example.com/admin` 접속
2. **새 링크 추가** 클릭
3. 슬러그(예: `mom`)와 연결할 Immich Kiosk URL 입력
4. 생성된 단축 URL 공유: `https://kiosklink.example.com/mom`

### 링크 옵션

단축 링크 생성 시 아래 옵션을 추가할 수 있습니다:

| 옵션 | 설명 | 예시 |
|------|------|------|
| `duration` | 사진 재생 시간(초) | `15` |
| `layout` | 레이아웃 방식 | `single`, `portrait`, `landscape`, `splitview` 등 |
| `image_fit` | 이미지 맞춤 방식 | `contain`, `cover` |
| `image_effect` | 이미지 효과 | `zoom`, `smart-zoom` |
| `show_album_name` | 앨범명 표시 여부 | `true`, `false` |
| `weather` | 날씨 정보 표시 위치 | `성남`, `동탄` |

예) `https://kiosklink.example.com/mom?duration=10&layout=splitview&weather=성남`

### 관리 패널

`/admin` 페이지 상단의 **관리** 카드에서 다음 작업을 수행할 수 있습니다:

#### 역지오코딩 현황
- **변환완료 건수**: 정상적으로 지오코딩된 사진 수 (국가명: 대한민국)
- **미변환 건수**: 아직 지오코딩되지 않은 사진 수
- **전체 건수**: GPS 좌표가 있는 사진의 총 개수

#### 역지오코딩 실행
- Docker를 통해 Naver Reverse Geocoding 서비스 실행
- 배경 작업으로 진행되며 소요 시간은 사진 수에 따라 다릅니다.

#### 외부 라이브러리 재탐색
- Immich 외부 라이브러리 스캔 시작
- 새로 추가된 사진이 라이브러리에 반영됩니다.

---

## API 엔드포인트

### GET /api/albums
Immich 앨범 목록 조회

### GET /api/geocoding/status
역지오코딩 현황 조회 (변환완료/미변환/전체 건수)

### POST /api/geocoding/run
역지오코딩 실행 (Docker 소켓 기반)

### POST /api/library/scan
외부 라이브러리 재탐색 실행
