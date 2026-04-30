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
    env_file:
      - ./kiosk-manager/.env
    restart: unless-stopped
```

### 2. .env 파일 작성

`./kiosk-manager/.env` 파일을 생성하고 아래 내용을 채웁니다.

```env
IMMICH_URL=http://127.0.0.1:2283
IMMICH_API_KEY=your_immich_api_key
BASE_KIOSK_URL=https://kiosk.example.com
BASE_SHORT_URL=https://kiosklink.example.com
DATABASE_URL=sqlite:///./data/kiosk_links.db
```

### 3. 실행

```bash
docker compose up -d kiosk-manager
```

---

## 환경변수 설명

| 변수 | 설명 | 예시 |
|------|------|------|
| `IMMICH_URL` | Immich 서버 주소. `network_mode: host`이므로 `127.0.0.1` 사용 | `http://127.0.0.1:2283` |
| `IMMICH_API_KEY` | Immich API 키 ([발급 방법](#immich-api-키-발급)) | `T1mknMq...` |
| `BASE_KIOSK_URL` | Immich Kiosk 서버 주소. 단축 URL이 최종적으로 이 주소로 리다이렉트됨 | `https://kiosk.example.com` |
| `BASE_SHORT_URL` | kiosk-manager 자체 주소. 생성되는 단축 URL의 도메인이 됨 | `https://kiosklink.example.com` |
| `DATABASE_URL` | SQLite DB 경로. 변경 불필요 | `sqlite:///./data/kiosk_links.db` |

> `BASE_KIOSK_URL`과 `BASE_SHORT_URL`은 반드시 서로 달라야 합니다.
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

1. `https://kiosklink.example.com/admin` 접속
2. **새 링크 추가** 클릭
3. 슬러그(예: `mom`)와 연결할 Immich Kiosk URL 입력
4. 생성된 단축 URL 공유: `https://kiosklink.example.com/mom`
