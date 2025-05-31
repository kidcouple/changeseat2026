import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect('students.db')
cursor = conn.cursor()

# 모든 테이블 삭제
cursor.execute("DELETE FROM school_info")
cursor.execute("DELETE FROM students")
cursor.execute("DELETE FROM last_layout")
cursor.execute("DELETE FROM settings")
cursor.execute("DELETE FROM seat_history")

# 변경사항 저장
conn.commit()
conn.close()

print("데이터베이스가 초기화되었습니다.") 