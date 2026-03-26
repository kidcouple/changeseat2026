from flask import Flask, render_template, request, jsonify, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
import os
import pandas as pd
import math
import random
from datetime import datetime

app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///seats.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)
db = SQLAlchemy(app)

# 모델 정의
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(100))
    grade = db.Column(db.Integer)
    class_num = db.Column(db.Integer)
    student_number = db.Column(db.Integer)
    name = db.Column(db.String(100))
    gender = db.Column(db.String(10))
    eyestright = db.Column(db.String(10))
    is_transferred = db.Column(db.Boolean, default=False)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(100))
    grade = db.Column(db.Integer)
    class_num = db.Column(db.Integer)
    motto = db.Column(db.String(200))
    num_columns = db.Column(db.Integer, default=6)
    use_aisle_gap = db.Column(db.Boolean, default=True)
    consider_eyesight = db.Column(db.Boolean, default=False)
    separate_gender = db.Column(db.Boolean, default=True)
    prevent_same_seat = db.Column(db.Boolean, default=False)
    prevent_same_seat_count = db.Column(db.Integer, default=1)
    disabled_seats = db.Column(db.Text)  # JSON string
    forced_seats = db.Column(db.Text)    # JSON string

class SeatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(100))
    grade = db.Column(db.Integer)
    class_num = db.Column(db.Integer)
    layout_data = db.Column(db.Text) # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/students', methods=['GET'])
def get_students():
    school_name = request.args.get('school_name')
    grade = request.args.get('grade')
    class_num = request.args.get('class_num')
    mode = request.args.get('mode')
    
    # 숫자 필드 변환 및 정규화
    def safe_int(v, default=0):
        try: return int(float(v)) if v is not None and str(v).strip() else default
        except: return default

    school_name = school_name or ''
    grade = safe_int(grade)
    class_num = safe_int(class_num)

    query = Student.query.filter_by(
        school_name=school_name,
        grade=grade,
        class_num=class_num
    )
    
    if mode != 'list':
        query = query.filter_by(is_transferred=False)
    
    students = query.order_by(Student.student_number).all()
    
    return jsonify([{
        'id': s.id,
        'number': s.student_number,
        'name': s.name,
        'gender': s.gender,
        'eyesight': 1 if s.eyestright == '정상' else 2,
        'is_transferred': s.is_transferred
    } for s in students])

@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.json or {}
    args = request.args
    try:
        # 숫자 필드 변환 및 정규화
        def safe_int(v, default=0):
            try: return int(float(v)) if v is not None and str(v).strip() else default
            except: return default

        # Body와 URL 파라미터 모두 확인 (하이브리드 지원)
        school = data.get('school_name') or args.get('school_name', '')
        grade = data.get('grade') or args.get('grade')
        class_num = data.get('class_num') or args.get('class_num')

        # Handle both 'eyestright' and 'eyesight' keys for compatibility
        vision = data.get('eyestright') or data.get('eyesight') or '정상'
        if str(vision) == '2' or '이상' in str(vision): vision = '이상'
        elif str(vision) == '1' or '정상' in str(vision): vision = '정상'

        student = Student(
            school_name=str(school),
            grade=safe_int(grade),
            class_num=safe_int(class_num),
            student_number=safe_int(data.get('student_number')),
            name=str(data.get('name', '')).strip(),
            gender=str(data.get('gender', '남')),
            eyestright=str(vision),
            is_transferred=bool(data.get('is_transferred', False))
        )
        if not student.name:
            return jsonify({'error': 'Name is required'}), 400
            
        db.session.add(student)
        db.session.commit()
        print(f"Added student: {student.name} ({student.school_name} {student.grade}-{student.class_num})")
        return jsonify({'message': 'success'})
    except Exception as e:
        print(f"Error adding student: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/bulk', methods=['POST'])
def bulk_add_students():
    data = request.json
    students_data = data.get('students', [])
    school = data.get('school_name', '')
    grade = data.get('grade', 0)
    class_num = data.get('class_num', 0)
    
    try:
        count = 0
        for s in students_data:
            vision = s.get('eyestright') or s.get('eyesight') or '정상'
            if str(vision) == '2' or '이상' in str(vision): vision = '이상'
            elif str(vision) == '1' or '정상' in str(vision): vision = '정상'
            
            student = Student(
                school_name=school,
                grade=int(grade),
                class_num=int(class_num),
                student_number=int(s.get('student_number') or 0),
                name=str(s.get('name', '')).strip(),
                gender=str(s.get('gender', '남')),
                eyestright=str(vision),
                is_transferred=bool(s.get('is_transferred', False))
            )
            if student.name:
                db.session.add(student)
                count += 1
        
        db.session.commit()
        print(f"Bulk added {count} students for {school} {grade}-{class_num}")
        return jsonify({'status': 'success', 'count': count})
    except Exception as e:
        db.session.rollback()
        print(f"Bulk add error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    def safe_int(v, default=0):
        try: return int(float(v)) if v is not None and str(v).strip() else default
        except: return default

    school = request.args.get('school', '')
    grade = safe_int(request.args.get('grade'))
    class_num = safe_int(request.args.get('class_num'))
    
    # 학년/반 정보를 기반으로 기존 설정 검색
    setting = Setting.query.filter_by(school_name=school, grade=grade, class_num=class_num).first()
    
    if request.method == 'GET':
        if not setting:
            return jsonify({
                "motto": "",
                "numColumns": 6,
                "useAisleGap": True,
                "considerEyesight": False,
                "separateGender": True,
                "preventSameSeat": False,
                "preventSameSeatCount": 1,
                "disabledSeats": [],
                "forcedSeats": []
            })
        
        return jsonify({
            "motto": setting.motto,
            "numColumns": setting.num_columns,
            "useAisleGap": setting.use_aisle_gap,
            "considerEyesight": setting.consider_eyesight,
            "separateGender": setting.separate_gender,
            "preventSameSeat": setting.prevent_same_seat,
            "preventSameSeatCount": setting.prevent_same_seat_count,
            "disabledSeats": eval(setting.disabled_seats) if setting.disabled_seats else [],
            "forcedSeats": eval(setting.forced_seats) if setting.forced_seats else []
        })
    
    else: # POST
        data = request.json
        if not setting:
            # 존재하지 않으면 새로 생성
            setting = Setting(school_name=school, grade=grade, class_num=class_num)
            db.session.add(setting)
        # 이미 세션에 있거나 방금 add된 setting 객체의 속성을 변경
        setting.motto = data.get('motto', "")
        setting.num_columns = data.get('numColumns', 6)
        setting.use_aisle_gap = data.get('useAisleGap', True)
        setting.consider_eyesight = data.get('considerEyesight', False)
        setting.separate_gender = data.get('separateGender', True)
        setting.prevent_same_seat = data.get('preventSameSeat', False)
        setting.prevent_same_seat_count = data.get('preventSameSeatCount', 1)
        setting.disabled_seats = str(data.get('disabledSeats', []))
        setting.forced_seats = str(data.get('forcedSeats', []))
        
        db.session.commit()
        return jsonify({"status": "success"})

@app.route('/api/shuffle', methods=['POST'])
def shuffle_students():
    data = request.json
    school = data.get('school_name') or data.get('school') or data.get('school_id')
    grade = int(data.get('grade', 0))
    class_num = int(data.get('class_num', 0))
    cols = int(data.get('num_columns', 6))
    disabled_seats = data.get('disabled_seats', [])
    forced_seats = data.get('forced_seats', [])
    
    # 🔍 [Debug] 요청 파라미터 확인
    print(f"--- Shuffle Debug ---")
    print(f"Request: school={school}, grade={grade}, class_num={class_num}, cols={cols}")
    
    students = Student.query.filter_by(school_name=school, grade=grade, class_num=class_num, is_transferred=False).all()
    print(f"Students found: {len(students)}")
    
    if not students:
        return jsonify({'layout': []})
    
    forced_names = [f['name'] for f in forced_seats]
    pool = [s for s in students if s.name not in forced_names]
    random.shuffle(pool)
    
    rows = math.ceil((len(students) + len(disabled_seats)) / cols)
    if rows < 5: rows = 5
    
    layout = []
    occupied = set()
    for f in forced_seats:
        layout.append({'name': f['name'], 'row': f['row'], 'col': f['col']})
        occupied.add((f['row'], f['col']))
    
    student_idx = 0
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            if (r, c) in occupied or f"{r}-{c}" in disabled_seats:
                continue
            
            if student_idx < len(pool):
                s = pool[student_idx]
                layout.append({'name': s.name, 'row': r, 'col': c})
                student_idx += 1
                
    history = SeatHistory(
        school_name=school,
        grade=grade,
        class_num=class_num,
        layout_data=str(layout)
    )
    db.session.add(history)
    db.session.commit()
    
    return jsonify({'layout': layout})

@app.route('/api/students/upload', methods=['POST'])
def upload_students():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    try:
        df = pd.read_excel(file)
        col_map = {
            'student_number': ['번호', '학번', 'no', '순번'],
            'name': ['이름', '성함', '성명', '학생명'],
            'gender': ['성별', '남녀'],
            'eyestright': ['시력', '시력구분', '눈']
        }
        
        parsed_students = []
        for _, row in df.iterrows():
            s_data = {
                'student_number': 0,
                'name': '',
                'gender': '남',
                'eyestright': '정상'
            }
            
            for attr, aliases in col_map.items():
                for col in df.columns:
                    if any(alias in str(col) for alias in aliases):
                        val = row[col]
                        if pd.isna(val): continue
                        
                        if attr == 'student_number':
                            try: s_data[attr] = int(float(val))
                            except: pass
                        elif attr == 'eyestright':
                            v_str = str(val).strip()
                            if v_str == '1' or '정상' in v_str: s_data[attr] = '정상'
                            elif v_str == '2' or '이상' in v_str: s_data[attr] = '이상'
                            else: s_data[attr] = v_str
                        else:
                            s_data[attr] = str(val).strip()
            
            if s_data['name'] and s_data['name'] != 'nan':
                parsed_students.append(s_data)
        
        return jsonify({'students': parsed_students, 'status': 'success'})
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<int:id>', methods=['PUT', 'DELETE'])
def update_student(id):
    student = Student.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(student)
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        data = request.json
        student.name = data.get('name', student.name)
        student.gender = data.get('gender', student.gender)
        eyesight_val = data.get('eyesight')
        if eyesight_val is not None:
            student.eyestright = '정상' if eyesight_val == 1 else '이상'
        student.is_transferred = data.get('is_transferred', student.is_transferred)
        db.session.commit()
        return jsonify({'status': 'success'})

@app.route('/api/seat_history', methods=['GET'])
def get_history():
    school = request.args.get('school_id')
    history = SeatHistory.query.filter_by(school_name=school).order_by(SeatHistory.created_at.desc()).limit(10).all()
    return jsonify([{
        'id': h.id,
        'created_at': h.created_at.isoformat(),
        'layout_data': eval(h.layout_data) if h.layout_data else []
    } for h in history])

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        try:
            from sqlalchemy import text
            db.session.execute(text('ALTER TABLE student ADD COLUMN is_transferred BOOLEAN DEFAULT 0'))
            db.session.commit()
        except:
            db.session.rollback()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)