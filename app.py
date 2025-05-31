from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
import pandas as pd
from datetime import datetime

app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///seats.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

class SeatLayout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(100))
    grade = db.Column(db.Integer)
    class_num = db.Column(db.Integer)
    row = db.Column(db.Integer)
    col = db.Column(db.Integer)
    name = db.Column(db.String(100))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/students', methods=['GET'])
def get_students():
    school_name = request.args.get('school_name')
    grade = request.args.get('grade')
    class_num = request.args.get('class_num')
    
    students = Student.query.filter_by(
        school_name=school_name,
        grade=grade,
        class_num=class_num
    ).all()
    
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'gender': s.gender,
        'eyestright': s.eyestright
    } for s in students])

@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.json
    student = Student(
        school_name=data['school_name'],
        grade=data['grade'],
        class_num=data['class_num'],
        student_number=data['student_number'],
        name=data['name'],
        gender=data['gender'],
        eyestright=data['eyestright']
    )
    db.session.add(student)
    db.session.commit()
    return jsonify({'message': 'success'})

@app.route('/api/layout', methods=['GET'])
def get_layout():
    school_name = request.args.get('school_name')
    grade = request.args.get('grade')
    class_num = request.args.get('class_num')
    
    layout = SeatLayout.query.filter_by(
        school_name=school_name,
        grade=grade,
        class_num=class_num
    ).all()
    
    return jsonify([{
        'row': s.row,
        'col': s.col,
        'name': s.name
    } for s in layout])

@app.route('/api/layout', methods=['POST'])
def save_layout():
    data = request.json
    # 기존 레이아웃 삭제
    SeatLayout.query.filter_by(
        school_name=data['school_name'],
        grade=data['grade'],
        class_num=data['class_num']
    ).delete()
    
    # 새로운 레이아웃 저장
    for seat in data['layout']:
        layout = SeatLayout(
            school_name=data['school_name'],
            grade=data['grade'],
            class_num=data['class_num'],
            row=seat['row'],
            col=seat['col'],
            name=seat['name']
        )
        db.session.add(layout)
    
    db.session.commit()
    return jsonify({'message': 'success'})

@app.route('/api/import', methods=['POST'])
def import_students():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.xlsx'):
        return jsonify({'error': 'Only Excel files are allowed'}), 400
    
    try:
        df = pd.read_excel(file)
        required_columns = ['학교명', '학년', '반', '학번', '이름', '성별', '시력']
        
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'Missing required columns'}), 400
        
        for _, row in df.iterrows():
            student = Student(
                school_name=row['학교명'],
                grade=int(row['학년']),
                class_num=int(row['반']),
                student_number=int(row['학번']),
                name=row['이름'],
                gender=row['성별'],
                eyestright=row['시력']
            )
            db.session.add(student)
        
        db.session.commit()
        return jsonify({'message': 'success'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['GET'])
def export_students():
    school_name = request.args.get('school_name')
    grade = request.args.get('grade')
    class_num = request.args.get('class_num')
    
    students = Student.query.filter_by(
        school_name=school_name,
        grade=grade,
        class_num=class_num
    ).all()
    
    data = []
    for student in students:
        data.append({
            '학교명': student.school_name,
            '학년': student.grade,
            '반': student.class_num,
            '학번': student.student_number,
            '이름': student.name,
            '성별': student.gender,
            '시력': student.eyestright
        })
    
    df = pd.DataFrame(data)
    filename = f'students_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    df.to_excel(filename, index=False)
    
    return send_from_directory('.', filename, as_attachment=True)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 