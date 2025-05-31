import pandas as pd
import sqlite3

# 엑셀 파일 읽기
df = pd.read_excel('학생정보.xlsx')

# 열 이름 출력
print("엑셀 파일의 열 이름:")
print(df.columns.tolist())

# 처음 몇 행 출력
print("\n처음 5개 행의 데이터:")
print(df.head())

# SQLite 데이터베이스 연결
conn = sqlite3.connect('students.db')
cursor = conn.cursor()

# 기존 테이블 삭제 후 다시 생성
cursor.execute("DROP TABLE IF EXISTS students")
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_name TEXT NOT NULL,
    grade TEXT NOT NULL,
    class_num TEXT NOT NULL,
    student_number INTEGER NOT NULL,
    name TEXT NOT NULL,
    gender TEXT NOT NULL,
    eyestright TEXT,
    UNIQUE(school_name, grade, class_num, name)
)
""")

# 데이터 삽입
for _, row in df.iterrows():
    try:
        cursor.execute("""
        INSERT INTO students (school_name, grade, class_num, student_number, name, gender, eyestright)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            row['학교'],
            str(row['학년']),
            str(row['반']),
            int(row['번호']),
            row['이름'],
            'male' if row['성별'] == '남' else 'female',
            str(row['시력']) if pd.notna(row['시력']) else 'NA'
        ))
    except sqlite3.IntegrityError:
        print(f"중복된 학생 정보가 있습니다: {row['이름']}")

# 변경사항 저장 및 연결 종료
conn.commit()
conn.close()

print("데이터베이스 생성이 완료되었습니다.") 