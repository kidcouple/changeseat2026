import os
import sys

# 🚩 [중요] PythonAnywhere 환경에서 app을 불러오기 위한 경로 설정
basedir = os.path.abspath(os.path.dirname(__file__))
if basedir not in sys.path:
    sys.path.append(basedir)

from app import app, db

print("Starting database initialization...")
with app.app_context():
    # 모든 테이블(student, setting, seat_history) 생성
    db.create_all()
    print("Success: All tables have been created!")
    
    # 생성된 데이터베이스 파일 위치 확인
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    print(f"Database URI: {db_uri}")
