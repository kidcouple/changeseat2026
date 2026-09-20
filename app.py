from flask import Flask, render_template, request, jsonify, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
import ast
import json
import os
import math
import random
from datetime import datetime, timezone

try:
    import pandas as pd
except ImportError:  # 복구 스크립트 실행 시 엑셀 의존성은 선택 사항
    pd = None

app = Flask(__name__, static_folder='static')
basedir = os.path.abspath(os.path.dirname(__file__))
database_url = os.environ.get('DATABASE_URL', '').strip()
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
elif database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    database_url or 'sqlite:///' + os.path.join(basedir, 'seats.db')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
app.secret_key = os.urandom(24)
db = SQLAlchemy(app)

def utc_now():
    """기존 시간대 없는 DB 열에 맞춘 경고 없는 UTC 현재 시각."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_created_at(raw):
    if not raw:
        return None
    try:
        text = str(raw).strip().replace('Z', '')
        if len(text) == 10:
            text += 'T12:00:00'
        value = datetime.fromisoformat(text)
        return value.replace(tzinfo=None) if value.tzinfo else value
    except ValueError:
        return None


def parse_layout(raw):
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except (TypeError, json.JSONDecodeError):
        pass
    try:
        data = ast.literal_eval(raw)
        return data if isinstance(data, list) else []
    except (ValueError, SyntaxError):
        return []


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
    prevent_same_pair = db.Column(db.Boolean, default=False)
    disabled_seats = db.Column(db.Text)  # JSON string
    forced_seats = db.Column(db.Text)    # JSON string
    last_active_at = db.Column(db.DateTime, default=utc_now)

class PairHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(100))
    grade = db.Column(db.Integer)
    class_num = db.Column(db.Integer)
    name = db.Column(db.String(100))
    pair_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=utc_now)

class SeatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(100))
    grade = db.Column(db.Integer)
    class_num = db.Column(db.Integer)
    layout_data = db.Column(db.Text) # JSON string
    created_at = db.Column(db.DateTime, default=utc_now)

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

    school_name = (school_name or '').strip()
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
        school = (data.get('school_name') or args.get('school_name', '')).strip()
        grade = data.get('grade') or args.get('grade')
        class_num = data.get('class_num') or args.get('class_num')

        # Handle both 'eyestright' and 'eyesight' keys for compatibility
        vision = data.get('eyestright') or data.get('eyesight') or '정상'
        if str(vision) == '2' or '이상' in str(vision): vision = '이상'
        elif str(vision) == '1' or '정상' in str(vision): vision = '정상'

        student = Student(
            school_name=school,
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
        school = school.strip()
        for s in students_data:
            vision = s.get('eyestright') or s.get('eyesight') or '정상'
            if str(vision) == '2' or '이상' in str(vision): vision = '이상'
            elif str(vision) == '1' or '정상' in str(vision): vision = '정상'

            student_number = int(s.get('student_number') or 0)
            name = str(s.get('name', '')).strip()
            if not name:
                continue

            identity = {
                'school_name': school,
                'grade': int(grade),
                'class_num': int(class_num),
            }
            if student_number:
                student = Student.query.filter_by(
                    **identity, student_number=student_number
                ).first()
            else:
                student = Student.query.filter_by(
                    **identity, name=name
                ).first()

            if not student:
                student = Student(**identity)
                db.session.add(student)

            student.student_number = student_number
            student.name = name
            student.gender = str(s.get('gender', '남'))
            student.eyestright = str(vision)
            student.is_transferred = bool(s.get('is_transferred', False))
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

    school = (request.args.get('school', '')).strip()
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
                "preventSamePair": False,
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
            "preventSamePair": bool(setting.prevent_same_pair) if setting.prevent_same_pair is not None else False,
            "disabledSeats": parse_layout(setting.disabled_seats),
            "forcedSeats": parse_layout(setting.forced_seats)
        })

    else: # POST
        data = request.get_json(silent=True) or {}
        if not setting:
            setting = Setting(school_name=school, grade=grade, class_num=class_num)
            db.session.add(setting)
        setting.motto = data.get('motto', "")
        setting.num_columns = max(1, safe_int(data.get('numColumns'), 6))
        setting.use_aisle_gap = data.get('useAisleGap', True)
        setting.consider_eyesight = data.get('considerEyesight', False)
        setting.separate_gender = data.get('separateGender', True)
        setting.prevent_same_seat = data.get('preventSameSeat', False)
        setting.prevent_same_seat_count = max(
            1, safe_int(data.get('preventSameSeatCount'), 1)
        )
        setting.prevent_same_pair = data.get('preventSamePair', False)
        setting.disabled_seats = json.dumps(
            data.get('disabledSeats', []), ensure_ascii=False
        )
        setting.forced_seats = json.dumps(
            data.get('forcedSeats', []), ensure_ascii=False
        )
        setting.last_active_at = utc_now()
        
        db.session.commit()
        return jsonify({"status": "success"})

@app.route('/api/shuffle', methods=['POST'])
def shuffle_students():
    data = request.get_json(silent=True) or {}
    school = (data.get('school_name') or data.get('school') or data.get('school_id') or '').strip()
    try:
        grade = int(data.get('grade', 0))
        class_num = int(data.get('class_num', 0))
        cols = int(data.get('num_columns', 6))
    except (TypeError, ValueError):
        return jsonify({'error': '학년, 반, 열 수는 숫자여야 합니다.'}), 400
    if not school or grade < 1 or class_num < 1 or cols < 1:
        return jsonify({'error': '학교, 학년, 반, 열 수를 확인해 주세요.'}), 400

    raw_disabled = data.get('disabled_seats', [])
    raw_designated = data.get('designated_seats', [])
    raw_forced = data.get('forced_seats', [])
    disabled_seats = list(dict.fromkeys(raw_disabled)) if isinstance(raw_disabled, list) else []
    designated_seats = raw_designated if isinstance(raw_designated, list) else []
    forced_seats = raw_forced if isinstance(raw_forced, list) else []
    
    students = Student.query.filter_by(school_name=school, grade=grade, class_num=class_num, is_transferred=False).all()

    if not students:
        return jsonify({'layout': []})

    setting = Setting.query.filter_by(school_name=school, grade=grade, class_num=class_num).first()
    use_aisle_gap = setting.use_aisle_gap if setting else True
    consider_eyesight = bool(setting.consider_eyesight) if setting else False
    separate_gender = bool(setting.separate_gender) if setting else False
    prevent_same_seat = bool(setting.prevent_same_seat) if setting else False
    prevent_same_pair = bool(setting.prevent_same_pair) if setting and setting.prevent_same_pair is not None else False
    prevent_same_seat_count = max(1, setting.prevent_same_seat_count if setting else 1)

    rows_count = math.ceil((len(students) + len(disabled_seats)) / cols)
    if rows_count < 5:
        rows_count = 5

    # 삭제·전출된 학생, 범위 밖 좌석, 빈자리로 막힌 좌석의 오래된 지정값은 무시
    active_names = {student.name for student in students}

    def valid_fixed_entries(raw_items):
        valid = []
        for item in raw_items:
            try:
                row_i = int(item['row'])
                col_i = int(item['col'])
                name = item['name']
            except (KeyError, TypeError, ValueError):
                continue
            if (
                name in active_names
                and 1 <= row_i <= rows_count
                and 1 <= col_i <= cols
                and f"{row_i}-{col_i}" not in disabled_seats
            ):
                valid.append({'name': name, 'row': row_i, 'col': col_i})
        return valid

    designated_seats = valid_fixed_entries(designated_seats)
    forced_seats = valid_fixed_entries(forced_seats)

    # 우선순위: 지정석 > 강제지정. 이름·자리가 겹치면 지정석을 남긴다.
    merged_fixed = []
    taken_names = set()
    taken_pos = set()
    for item in designated_seats + forced_seats:
        if item['name'] in taken_names or (item['row'], item['col']) in taken_pos:
            continue
        merged_fixed.append(item)
        taken_names.add(item['name'])
        taken_pos.add((item['row'], item['col']))
    forced_seats = merged_fixed
    locked_names = taken_names

    forced_names = [f['name'] for f in forced_seats]
    pool = [s for s in students if s.name not in forced_names]

    # 분단(aisle gap) 모드 여부: cols가 짝수이고 use_aisle_gap=True이면 분단 모드
    is_bundan = use_aisle_gap and cols % 2 == 0

    forced_layout = []
    occupied = set()
    for f in forced_seats:
        row_i = int(f['row'])
        col_i = int(f['col'])
        forced_layout.append({'name': f['name'], 'row': row_i, 'col': col_i})
        occupied.add((row_i, col_i))

    available_positions = [
        (row, col)
        for row in range(1, rows_count + 1)
        for col in range(1, cols + 1)
        if (row, col) not in occupied and f"{row}-{col}" not in disabled_seats
    ]

    # 동일 자리 금지: 최근 N개 배치의 학생별 좌석을 로드
    recent_seats = {}
    if prevent_same_seat:
        recent_histories = SeatHistory.query.filter_by(
            school_name=school, grade=grade, class_num=class_num
        ).order_by(SeatHistory.created_at.desc()).limit(prevent_same_seat_count).all()
        for history in recent_histories:
            history_layout = parse_layout(history.layout_data)
            for seat in history_layout:
                if seat.get('name'):
                    recent_seats.setdefault(seat['name'], set()).add(
                        (int(seat['row']), int(seat['col']))
                    )

    # 동일짝 금지: 짝 이력 로드
    # 시력 이상은 앞자리 배치가 막히지 않도록 최근 2회(직전 짝 위주)만 본다.
    EYESIGHT_PAIR_LIMIT = 2
    pair_history_map = {}
    if prevent_same_pair and is_bundan:
        for s in students:
            pair_limit = (
                min(EYESIGHT_PAIR_LIMIT, prevent_same_seat_count)
                if s.eyestright == '이상'
                else prevent_same_seat_count
            )
            rows_ph = PairHistory.query.filter_by(
                school_name=school, grade=grade, class_num=class_num, name=s.name
            ).order_by(PairHistory.created_at.desc()).limit(pair_limit).all()
            pair_history_map[s.name] = [r.pair_name for r in rows_ph]

    eyesight_priority_pool = [
        student for student in pool if student.eyestright == '이상'
    ]
    regular_pool = [
        student for student in pool if student.eyestright != '이상'
    ]
    student_gender = {student.name: student.gender for student in students}
    forced_gender_by_pos = {
        (seat['row'], seat['col']): student_gender.get(seat['name'])
        for seat in forced_layout
    }
    forced_name_by_pos = {
        (seat['row'], seat['col']): seat['name']
        for seat in forced_layout
    }

    def pair_partner_col(col):
        return col + 1 if col % 2 == 1 else col - 1

    def pick_eyesight_positions(count):
        """교탁 바로 앞자리부터 시력 학생 수만큼 예약. 시력은 남여 구분보다 우선한다."""
        if count <= 0:
            return []
        return sorted(available_positions)[:count]

    def assign_by_priority(
        students, positions, occupied_genders, occupied_names, all_valid_positions
    ):
        leftover_students = list(students)
        random.shuffle(leftover_students)
        seat_gender = dict(occupied_genders)
        seat_name = dict(occupied_names)
        assignments = []

        def wanted_gender(row, col):
            partner_pos = (row, pair_partner_col(col))
            partner = seat_gender.get(partner_pos)
            if partner == '남':
                return '여'
            if partner == '여':
                return '남'
            if partner_pos not in all_valid_positions:
                males = sum(1 for student in leftover_students if student.gender == '남')
                females = sum(1 for student in leftover_students if student.gender == '여')
                return '남' if males >= females else '여'
            return '남' if col % 2 == 1 else '여'

        def penalty(student, row, col, wanted):
            pair_pen = 0
            if prevent_same_pair and is_bundan:
                partner_name = seat_name.get((row, pair_partner_col(col)))
                if partner_name and partner_name in pair_history_map.get(student.name, []):
                    pair_pen = 1
            eye_pen = 0
            if consider_eyesight:
                in_front = (row, col) in eyesight_position_set
                is_eye = student.eyestright == '이상'
                if is_eye != in_front:
                    eye_pen = 1
            seat_pen = 0
            if prevent_same_seat and (row, col) in recent_seats.get(student.name, set()):
                seat_pen = 1
            gender_pen = 0
            if separate_gender and wanted and student.gender != wanted:
                gender_pen = 1
            # 지정석/강제지정 다음 우선순위: 동일짝 > 시력 > 이전자리 > 남여
            return (pair_pen, eye_pen, seat_pen, gender_pen)

        for row, col in sorted(positions):
            if not leftover_students:
                break
            wanted = wanted_gender(row, col) if separate_gender and is_bundan else None
            student = min(
                leftover_students,
                key=lambda candidate: penalty(candidate, row, col, wanted),
            )
            leftover_students.remove(student)
            assignments.append((student, (row, col)))
            seat_gender[(row, col)] = student.gender
            seat_name[(row, col)] = student.name
        leftover_positions = [
            position
            for position in positions
            if position not in {pos for _, pos in assignments}
        ]
        assignments.extend(zip(leftover_students, leftover_positions))
        return assignments, seat_gender, seat_name

    eyesight_positions = pick_eyesight_positions(len(eyesight_priority_pool))
    eyesight_position_set = set(eyesight_positions)
    regular_positions = [
        position
        for position in available_positions
        if position not in eyesight_position_set
    ]

    def shuffled_candidate_assignments():
        occupied_genders = dict(forced_gender_by_pos)
        occupied_names = dict(forced_name_by_pos)
        all_valid = set(available_positions) | set(forced_name_by_pos)
        assignments = []
        if consider_eyesight and eyesight_priority_pool and eyesight_positions:
            eye_assignments, occupied_genders, occupied_names = assign_by_priority(
                eyesight_priority_pool,
                eyesight_positions,
                occupied_genders,
                occupied_names,
                all_valid,
            )
            assignments.extend(eye_assignments)
        rest_assignments, _, _ = assign_by_priority(
            regular_pool if consider_eyesight else pool,
            regular_positions if consider_eyesight else available_positions,
            occupied_genders,
            occupied_names,
            all_valid,
        )
        assignments.extend(rest_assignments)
        return assignments

    has_constraints = (
        prevent_same_seat
        or prevent_same_pair
        or consider_eyesight
        or (is_bundan and separate_gender)
    )
    attempts = 300 if has_constraints else 1
    best_layout = None
    best_score = None
    student_eyesight = {student.name: student.eyestright for student in students}
    for _ in range(attempts):
        candidate_assignments = shuffled_candidate_assignments()
        candidate_layout = forced_layout + [
            {'name': student.name, 'row': position[0], 'col': position[1]}
            for student, position in candidate_assignments
        ]

        same_seat_conflicts = sum(
            (seat['row'], seat['col']) in recent_seats.get(seat['name'], set())
            for seat in candidate_layout
            if seat['name'] not in locked_names
        ) if prevent_same_seat else 0

        eyesight_conflicts = 0
        if consider_eyesight:
            eyesight_conflicts = sum(
                1
                for seat in candidate_layout
                if seat['name'] not in locked_names
                and student_eyesight.get(seat['name']) == '이상'
                and (seat['row'], seat['col']) not in eyesight_position_set
            )

        pair_conflicts = 0
        same_gender_conflicts = 0
        if is_bundan and (prevent_same_pair or separate_gender):
            seat_map = {
                (seat['row'], seat['col']): seat['name'] for seat in candidate_layout
            }
            for row in range(1, rows_count + 1):
                for first_col in range(1, cols + 1, 2):
                    first_name = seat_map.get((row, first_col))
                    second_name = seat_map.get((row, first_col + 1))
                    if not first_name or not second_name:
                        continue
                    both_locked = (
                        first_name in locked_names and second_name in locked_names
                    )
                    if both_locked:
                        continue
                    if (
                        prevent_same_pair
                        and second_name in pair_history_map.get(first_name, [])
                    ):
                        pair_conflicts += 1
                    if (
                        separate_gender
                        and student_gender.get(first_name)
                        and student_gender.get(first_name)
                        == student_gender.get(second_name)
                    ):
                        same_gender_conflicts += 1

        # 지정석/강제지정은 이미 고정. 나머지 점수 우선순위:
        # 동일짝 > 시력 > 이전자리 > 남여
        score = (
            pair_conflicts,
            eyesight_conflicts,
            same_seat_conflicts,
            same_gender_conflicts,
        )
        if best_score is None or score < best_score:
            best_score = score
            best_layout = candidate_layout
            if score == (0, 0, 0, 0):
                break

    layout = best_layout or forced_layout

    # 🚩 배치 실행 시 해당 학급을 '최근 활성화 학급'으로 갱신
    if setting:
        setting.last_active_at = utc_now()

    db.session.commit()

    return jsonify({'layout': layout})

@app.route('/api/students/upload', methods=['POST'])
def upload_students():
    if pd is None:
        return jsonify({'error': '엑셀 처리 모듈이 설치되지 않았습니다.'}), 503
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

@app.route('/api/seat_history', methods=['GET', 'DELETE'])
def get_history():
    school = (request.args.get('school_id') or request.args.get('school') or '').strip()
    grade = request.args.get('grade')
    class_num = request.args.get('class_num')

    query = SeatHistory.query.filter_by(school_name=school)
    pair_query = PairHistory.query.filter_by(school_name=school)
    if grade:
        query = query.filter_by(grade=int(grade))
        pair_query = pair_query.filter_by(grade=int(grade))
    if class_num:
        query = query.filter_by(class_num=int(class_num))
        pair_query = pair_query.filter_by(class_num=int(class_num))

    if request.method == 'DELETE':
        if not school or not grade or not class_num:
            return jsonify({'error': '학교, 학년, 반을 지정해 주세요.'}), 400
        deleted_pairs = pair_query.delete(synchronize_session=False)
        deleted_histories = query.delete(synchronize_session=False)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'deleted_histories': deleted_histories,
            'deleted_pairs': deleted_pairs,
        })

    history = query.order_by(SeatHistory.created_at.desc()).limit(10).all()
    return jsonify([{
        'id': h.id,
        'created_at': h.created_at.isoformat(),
        'layout_data': parse_layout(h.layout_data)
    } for h in history])

@app.route('/api/seat_history/<int:id>', methods=['DELETE'])
def delete_history(id):
    history = SeatHistory.query.get_or_404(id)
    try:
        PairHistory.query.filter_by(
            school_name=history.school_name,
            grade=history.grade,
            class_num=history.class_num,
            created_at=history.created_at,
        ).delete(synchronize_session=False)
        db.session.delete(history)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/latest_state', methods=['GET'])
def get_latest_state():
    # 1. 가장 최근에 배치(Shuffle/Save)된 기록 찾기
    latest_history = SeatHistory.query.order_by(SeatHistory.created_at.desc()).first()
    
    # 2. 가장 최근에 설정이 변경된 학급 찾기
    latest_setting = Setting.query.order_by(Setting.last_active_at.desc()).first()
    
    if not latest_history and not latest_setting:
        return jsonify({"found": False})

    # 3. 둘 중 더 최근 것을 기준으로 학급 정보 결정
    t1 = latest_history.created_at if latest_history else datetime.min
    t2 = latest_setting.last_active_at if latest_setting and latest_setting.last_active_at else datetime.min
    
    if t1 >= t2:
        target = latest_history
    else:
        target = latest_setting

    # 해당 학급의 최신 설정 가져오기
    setting = Setting.query.filter_by(
        school_name=target.school_name,
        grade=target.grade,
        class_num=target.class_num
    ).first()

    # 해당 학급의 최신 배치 기록 가져오기 (target이 history가 아닐 수도 있으므로 재검색)
    history = SeatHistory.query.filter_by(
        school_name=target.school_name,
        grade=target.grade,
        class_num=target.class_num
    ).order_by(SeatHistory.created_at.desc()).first()

    return jsonify({
        "found": True,
        "school_info": {
            "school_name": target.school_name,
            "grade": target.grade,
            "class_num": target.class_num,
            "motto": setting.motto if setting else ""
        },
        "settings": {
            "motto": setting.motto if setting else "",
            "numColumns": setting.num_columns if setting else 6,
            "useAisleGap": setting.use_aisle_gap if setting else True,
            "considerEyesight": setting.consider_eyesight if setting else False,
            "separateGender": setting.separate_gender if setting else True,
            "preventSameSeat": setting.prevent_same_seat if setting else False,
            "preventSameSeatCount": setting.prevent_same_seat_count if setting else 1,
            "preventSamePair": bool(setting.prevent_same_pair) if setting and setting.prevent_same_pair is not None else False,
            "disabledSeats": parse_layout(setting.disabled_seats) if setting else [],
            "forcedSeats": parse_layout(setting.forced_seats) if setting else []
        },
        "layout": parse_layout(history.layout_data) if history else []
    })

@app.route('/api/save_layout', methods=['POST'])
def save_layout():
    data = request.json
    school = (data.get('school_name') or '').strip()
    grade = int(data.get('grade', 0))
    class_num = int(data.get('class_num', 0))
    layout = data.get('layout', [])
    created_at = parse_created_at(data.get('created_at')) or utc_now()

    history = SeatHistory.query.filter_by(
        school_name=school,
        grade=grade,
        class_num=class_num,
        created_at=created_at,
    ).first()
    if not history:
        history = SeatHistory(
            school_name=school,
            grade=grade,
            class_num=class_num,
            created_at=created_at,
        )
        db.session.add(history)
    history.layout_data = json.dumps(layout, ensure_ascii=False)

    PairHistory.query.filter_by(
        school_name=school,
        grade=grade,
        class_num=class_num,
        created_at=created_at,
    ).delete(synchronize_session=False)

    # 분단 모드이면 짝 이력 저장
    setting = Setting.query.filter_by(school_name=school, grade=grade, class_num=class_num).first()
    if setting and setting.use_aisle_gap:
        cols = setting.num_columns
        if cols % 2 == 0:
            seat_map = {(s['row'], s['col']): s['name'] for s in layout if s.get('name')}
            num_groups = cols // 2
            max_row = max((s['row'] for s in layout if s.get('name')), default=0)
            for r in range(1, max_row + 1):
                for g in range(num_groups):
                    col1 = g * 2 + 1
                    col2 = g * 2 + 2
                    n1 = seat_map.get((r, col1))
                    n2 = seat_map.get((r, col2))
                    if n1 and n2:
                        db.session.add(PairHistory(school_name=school, grade=grade, class_num=class_num, name=n1, pair_name=n2, created_at=created_at))
                        db.session.add(PairHistory(school_name=school, grade=grade, class_num=class_num, name=n2, pair_name=n1, created_at=created_at))

    # 🚩 수동 저장 시에도 해당 학급을 '최근 활성화 학급'으로 갱신
    if setting:
        setting.last_active_at = utc_now()

    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# 🚩 [중요] 모든 테이블 생성 및 마이그레이션 (WSGI 환경 대응)
with app.app_context():
    db.create_all()
    try:
        from sqlalchemy import text
        db.session.execute(text('ALTER TABLE student ADD COLUMN is_transferred BOOLEAN DEFAULT 0'))
        db.session.commit()
    except:
        db.session.rollback()

    try:
        from sqlalchemy import text
        db.session.execute(text('ALTER TABLE setting ADD COLUMN last_active_at DATETIME'))
        db.session.commit()
    except:
        db.session.rollback()

    try:
        from sqlalchemy import text
        db.session.execute(text('ALTER TABLE setting ADD COLUMN prevent_same_pair BOOLEAN DEFAULT 0'))
        db.session.commit()
    except:
        db.session.rollback()

    # 🚩 모든 테이블의 학교 이름 공백 제거 (소급 적용)
    try:
        from sqlalchemy import text
        db.session.execute(text("UPDATE student SET school_name = TRIM(school_name)"))
        db.session.execute(text("UPDATE setting SET school_name = TRIM(school_name)"))
        db.session.execute(text("UPDATE seat_history SET school_name = TRIM(school_name)"))
        db.session.commit()
    except:
        db.session.rollback()

    # 🚩 기존 데이터 소급 적용 (오늘 데이터 보존을 위해 현재 시간으로 초기화)
    try:
        from sqlalchemy import text
        db.session.execute(text('UPDATE setting SET last_active_at = :now WHERE last_active_at IS NULL'), {'now': utc_now()})
        db.session.commit()
    except:
        db.session.rollback()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)