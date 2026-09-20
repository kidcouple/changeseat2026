# Supabase 영구 DB 및 비공개 백업 설정

## 1. Render에서 Supabase 연결

Supabase Dashboard의 `Connect`에서 PostgreSQL 연결 문자열을 복사한다. 무료
환경에서는 IPv4를 지원하는 Session pooler 연결 문자열을 권장한다.

Render의 `seat-arrangement` 서비스에서 다음 환경 변수를 등록한다.

- `DATABASE_URL`: Supabase PostgreSQL 연결 문자열

연결 문자열과 DB 비밀번호는 저장소나 소스 코드에 기록하지 않는다. 환경 변수를
저장한 뒤 Render를 다시 배포하면 앱이 Supabase에 연결된다.

학생 이름이 포함된 `업데이트해야함` 폴더는 공개 소스 저장소에 올리지 않는다.
Supabase 연결을 마친 뒤 로컬 PowerShell에서 복구 자료를 1회만 등록한다.

```powershell
$env:DATABASE_URL = "Supabase Session pooler 연결 문자열"
python -X utf8 import_recovery_data.py
Remove-Item Env:DATABASE_URL
```

복구 스크립트는 기존 학생의 시력 정보와 사용자가 바꾼 설정을 덮어쓰지 않는다.
Render 시작 명령에는 복구 스크립트를 넣지 않으므로 재배포 시에도 수정값이
초기화되지 않는다.

## 2. 비공개 백업 저장소

GitHub에 `changeseat-backup` 비공개 저장소를 생성하고 README를 추가해 기본
브랜치를 만든다. 앱 저장소의 Actions secrets에 다음 값을 등록한다.

- `SUPABASE_DB_URL`: Supabase PostgreSQL 연결 문자열
- `BACKUP_REPOSITORY`: `소유자/changeseat-backup`
- `BACKUP_REPO_TOKEN`: 백업 저장소에만 Contents 읽기/쓰기를 허용한 fine-grained PAT
- `BACKUP_ENCRYPTION_PASSWORD`: 백업 암호화 전용의 긴 무작위 비밀번호

`.github/workflows/supabase-backup.yml`은 매일 한국 시간 03:00에 다음 작업을 한다.

1. Supabase DB를 SQL로 덤프
2. gzip 압축 및 검증
3. AES-256으로 암호화
4. 비공개 저장소에 저장
5. 일별 백업은 30일 보관하고 매월 1일 백업은 장기 보관

백업 암호화 비밀번호를 잃으면 복구할 수 없으므로 비밀번호 관리자에 별도로
보관한다.

## 3. 백업 복호화

```bash
openssl enc -d -aes-256-cbc -pbkdf2 \
  -in changeseat_YYYY-MM-DD_HHMMSS.sql.gz.enc \
  -out changeseat.sql.gz
gzip -t changeseat.sql.gz
gunzip changeseat.sql.gz
```

복호화한 SQL은 새 PostgreSQL DB에 `psql`로 복원한다.
