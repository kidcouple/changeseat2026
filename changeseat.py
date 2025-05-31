import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                            QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, 
                            QMessageBox, QDialog, QFrame, QRadioButton,
                            QCheckBox, QTextEdit, QInputDialog, QTreeView,
                            QButtonGroup, QGridLayout, QFileDialog, QSizePolicy,
                            QTableWidget, QTableWidgetItem, QGraphicsBlurEffect,
                            QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, QRect, QUrl, QEvent, QPointF
from PyQt6.QtGui import QPixmap, QStandardItemModel, QStandardItem, QPainter, QPen, QBrush, QPolygon, QColor, QImage, QPainterPath, QPalette, QMouseEvent
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
import random
import sqlite3
from collections import defaultdict
import pandas as pd
from collections import deque
import traceback
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
import webbrowser
import weakref
import datetime
import math

class SchoolInfoDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("학교 정보 입력")
        self.setFixedSize(300, 200)
        
        # 레이아웃 설정
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 입력 필드들
        self.inputs = {}
        
        # 학교명
        school_layout = QHBoxLayout()
        school_label = QLabel("학교명:")
        self.inputs['school'] = QLineEdit()
        school_layout.addWidget(school_label)
        school_layout.addWidget(self.inputs['school'])
        layout.addLayout(school_layout)
        
        # 학년
        grade_layout = QHBoxLayout()
        grade_label = QLabel("학년:")
        self.inputs['grade'] = QLineEdit()
        grade_layout.addWidget(grade_label)
        grade_layout.addWidget(self.inputs['grade'])
        layout.addLayout(grade_layout)
        
        # 반
        class_layout = QHBoxLayout()
        class_label = QLabel("반:")
        self.inputs['class'] = QLineEdit()
        class_layout.addWidget(class_label)
        class_layout.addWidget(self.inputs['class'])
        layout.addLayout(class_layout)
        
        # 버튼들
        button_layout = QHBoxLayout()
        save_btn = QPushButton("저장")
        cancel_btn = QPushButton("취소")
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        save_btn.clicked.connect(self.on_save)
        cancel_btn.clicked.connect(self.reject)
        
        # 첫 번째 입력 필드에 포커스
        self.inputs['school'].setFocus()
        
        # 저장된 값을 저장할 변수
        self.saved_values = None
    
    def on_save(self):
        school = self.inputs['school'].text().strip()
        grade = self.inputs['grade'].text().strip()
        class_num = self.inputs['class'].text().strip()
        
        if not all([school, grade, class_num]):
            QMessageBox.warning(self, "경고", "모든 항목을 입력해주세요.")
            return
        
        self.saved_values = {
            'school_name': school,
            'grade': grade,
            'class_num': class_num
        }
        
        self.accept()
    
    def get_values(self):
        return self.saved_values

class BalloonImageWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
            QLabel:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(60, 60)
        self.setText("클릭")  # 클릭 가능한 영역임을 표시

    def mousePressEvent(self, event):
        # 전역 좌표 계산
        global_pos = event.globalPosition()
        local_pos = event.position()
        parent_pos = self.mapToParent(local_pos)
        
        # 모든 좌표 출력 (콘솔)
        print(f"전역 좌표: ({int(global_pos.x())}, {int(global_pos.y())})")
        print(f"로컬 좌표: ({int(local_pos.x())}, {int(local_pos.y())})")
        print(f"부모 기준 좌표: ({int(parent_pos.x())}, {int(parent_pos.y())})")
        
        # 부모 위젯의 자리바꾸기 함수 호출
        if self.parent():
            self.parent().on_shuffle_button_clicked()

class SeatFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.coord_label = None
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        x = int(event.position().x())
        y = int(event.position().y())
        exec_areas = [
            (101, 146, 69, 89),    # 자리바꾸기
            (186, 228, 69, 84),    # 수동지정
            (270, 315, 61, 96),    # 수동바꾸기
            (355, 394, 61, 94),    # 자리배치
            (440, 479, 61, 96),    # 저장
            (719, 763, 62, 97),    # 학생등록
            (806, 846, 60, 95),    # DB보기
            (890, 930, 63, 100),   # 초기화
            (974, 1013, 61, 98),   # 설정
        ]
        in_area = any(x1 <= x <= x2 and y1 <= y <= y2 for (x1, x2, y1, y2) in exec_areas)
        if in_area:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        x = int(event.position().x())
        y = int(event.position().y())
        print(f"\n=== 좌석 선택 시작 ===")
        print(f"클릭 좌표: ({x}, {y})")
        win = self.window()
        
        # 버튼 영역 처리
        exec_areas = [
            (101, 146, 69, 89),    # 자리바꾸기
            (186, 228, 69, 84),    # 수동지정
            (270, 315, 61, 96),    # 수동바꾸기
            (355, 394, 61, 94),    # 자리배치
            (440, 479, 61, 96),    # 저장
            (719, 763, 62, 97),    # 학생등록
            (806, 846, 60, 95),    # DB보기
            (890, 930, 63, 100),   # 초기화
            (974, 1013, 61, 98),   # 설정
        ]
        
        # 버튼 영역 확인
        for i, (x1, x2, y1, y2) in enumerate(exec_areas):
            if x1 <= x <= x2 and y1 <= y <= y2:
                print(f"버튼 영역 클릭: {i}")
                if i == 0:  # 자리바꾸기
                    print("자리바꾸기 버튼 클릭")
                    if hasattr(win, 'on_shuffle_button_clicked'):
                        win.on_shuffle_button_clicked()
                elif i == 1:  # 수동지정
                    if hasattr(win, 'on_manual_designate_click'):
                        win.on_manual_designate_click()
                elif i == 2:  # 수동바꾸기
                    if hasattr(win, 'on_manual_swap_click'):
                        win.on_manual_swap_click()
                elif i == 3:  # 자리배치
                    if hasattr(win, 'ask_layout_mode'):
                        win.ask_layout_mode()
                elif i == 4:  # 저장
                    if hasattr(win, 'on_save_layout_click'):
                        win.on_save_layout_click()
                elif i == 5:  # 학생등록
                    if hasattr(win, 'on_register_student_click'):
                        win.on_register_student_click()
                elif i == 6:  # DB보기
                    if hasattr(win, 'on_view_db_click'):
                        win.on_view_db_click()
                elif i == 7:  # 초기화
                    if hasattr(win, 'on_reset_data_click'):
                        win.on_reset_data_click()
                elif i == 8:  # 설정
                    print("설정 버튼 클릭")
                    if hasattr(win, 'on_settings_click'):
                        win.on_settings_click()
                return

        # 좌석 영역 클릭 처리
        row, col = self.get_seat_position_from_xy(x, y)
        if row and col:
            print(f"좌석 클릭: ({row}, {col})")
            
            # 수동지정 모드일 때
            if getattr(win, 'manual_designate_mode', False):
                seat = next((s for s in win.current_layout if s['row'] == row and s['col'] == col), None)
                if seat and seat['name']:
                    if (row, col) in win.fixed_seats:
                        # 고정 해제
                        del win.fixed_seats[(row, col)]
                        if hasattr(win, 'seat_labels') and (row, col) in win.seat_labels:
                            win.seat_labels[(row, col)].setStyleSheet("border: 1px solid #888; background: #fff; font-size: 12pt; min-width: 60px; min-height: 40px; max-width: 90px; max-height: 50px;")
                    else:
                        # 고정 설정
                        win.fixed_seats[(row, col)] = seat['name']
                        if hasattr(win, 'seat_labels') and (row, col) in win.seat_labels:
                            win.seat_labels[(row, col)].setStyleSheet("background-color: yellow; border: 2px solid #f90; font-size: 12pt; min-width: 60px; min-height: 40px; max-width: 90px; max-height: 50px;")
                print(f"고정된 좌석 목록: {win.fixed_seats}")
            
            # 수동바꾸기 모드일 때
            elif getattr(win, 'manual_swap_mode', False):
                if hasattr(win, 'select_for_swap'):
                    win.select_for_swap(row, col)

    def get_seat_position_from_xy(self, x, y):
        """
        클릭 좌표(x, y)로부터 정확한 (row, col) 좌석 위치를 반환합니다.
        draw_seats의 좌표 계산과 완전히 동일하게 동작합니다.
        """
        win = self.window()
        num_columns = getattr(win, 'num_columns', 4)
        layout_mode = getattr(win, 'layout_mode', '열')
        current_layout = getattr(win, 'current_layout', [])
        # 좌석 영역 정의
        seat_area = (134, 1110, 163, 638)  # (x1, x2, y1, y2)
        area_width = seat_area[1] - seat_area[0]
        area_height = seat_area[3] - seat_area[2]
        seat_width = 90
        seat_height = 50
        max_col_gap = 20
        min_col_gap = 5
        group_gap = 60 if layout_mode == '분단' else 0
        num_groups = (num_columns + 1) // 2 if layout_mode == '분단' else 0
        available_width = area_width - (group_gap * (num_groups - 1))
        col_gap = min(max_col_gap, max(min_col_gap, (available_width - (seat_width * num_columns)) // (num_columns - 1))) if num_columns > 1 else 0
        row_gap = 10
        # 열별 x좌표 오프셋 계산
        col_x_offsets = []
        if layout_mode == '분단':
            for col in range(1, num_columns + 1):
                group_idx = (col - 1) // 2
                x_offset = group_idx * group_gap + (col - 1) * (seat_width + col_gap)
                col_x_offsets.append(x_offset)
        else:
            for col in range(1, num_columns + 1):
                col_x_offsets.append((col - 1) * (seat_width + col_gap))
        total_width = col_x_offsets[-1] + seat_width
        start_x = seat_area[0] + (area_width - total_width) // 2
        # 행 수 계산
        num_rows = max([seat['row'] for seat in current_layout], default=4)
        total_height = (num_rows * seat_height) + ((num_rows - 1) * row_gap)
        start_y = seat_area[2] + (area_height - total_height) // 2
        # 열 계산
        col = None
        for i, x_offset in enumerate(col_x_offsets):
            x1 = start_x + x_offset
            x2 = x1 + seat_width
            if x1 <= x <= x2:
                col = i + 1
                break
        # 행 계산
        row = None
        for i in range(num_rows):
            y1 = start_y + i * (seat_height + row_gap)
            y2 = y1 + seat_height
            if y1 <= y <= y2:
                row = i + 1
                break
        return row, col

class SeatChangeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 기본 속성 초기화
        self.school_info = {
            'school_name': '',
            'grade': '',
            'class_num': ''
        }
        
        self.settings = {
            'consider_eyesight': False,
            'separate_gender': True,
            'prevent_same_seat': False,
            'prevent_same_seat_count': 3,
            'motto': '',
            'countdown_text': ''
        }
        
        self.layout_mode = '열'
        self.num_columns = 4
        
        # 학생 데이터 초기화
        self.male_students = []
        self.female_students = []
        self.all_students = []
        
        # 자리 배치 관련 변수 초기화
        self.current_layout = []
        self.previous_layout = []
        self.selected_seat = None
        self.excluded_students = set()
        self.seat_labels = {}
        self.student_seat_history = defaultdict(list)
        self.fixed_seats = {}  # 딕셔너리로 변경: {(row, col): student_name}
        self.fixed_counts = dict()
        
        # 배경 이미지 크기에 맞게 창 크기 고정
        bg_pixmap = QPixmap('CLASS_MAIN.PNG')
        if not bg_pixmap.isNull():
            bg_pixmap = bg_pixmap.scaled(1280, 720, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.setFixedSize(1280, 720)
        else:
            self.setGeometry(100, 100, 1280, 720)

        # 중앙 위젯 설정
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # 전체 위젯 배경 투명 리셋
        self.setStyleSheet("QWidget { background-color: transparent; }")

        # 데이터베이스 연결
        try:
            # 데이터베이스 파일 경로 설정
            db_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(db_dir, 'students.db')
            
            # 디렉토리가 없으면 생성
            os.makedirs(db_dir, exist_ok=True)
            
            print(f"데이터베이스 경로: {db_path}")  # 디버그 메시지
            
            # 데이터베이스 연결 설정
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.cursor = self.conn.cursor()
            
            # 테이블 생성
            self.create_tables()
            print("데이터베이스 연결 및 테이블 생성 완료")  # 디버그 메시지

            # 책상 이미지 로드
            current_dir = os.path.dirname(os.path.abspath(__file__))
            desk_image_path = os.path.join(current_dir, "desk.png")
            if not os.path.exists(desk_image_path):
                # 책상 이미지가 없으면 생성
                self.create_desk_image(desk_image_path)
            
            self.desk_pixmap = QPixmap(desk_image_path)
            if self.desk_pixmap.isNull():
                print("책상 이미지 로드 실패")
            else:
                print("책상 이미지 로드 성공")
            
        except sqlite3.Error as e:
            print(f"데이터베이스 오류: {str(e)}")  # 디버그 메시지
            QMessageBox.critical(self, "오류", f"데이터베이스 연결 중 오류가 발생했습니다: {str(e)}")
            sys.exit(1)  # 데이터베이스 연결 실패시 프로그램 종료

        # UI 초기화
        self.init_ui()

        # 초기화 완료 플래그
        self.initialized = False

    def create_tables(self):
        """데이터베이스 테이블 생성"""
        try:
            # 학교 정보 테이블
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS school_info
                                (school_name TEXT, grade INTEGER, class_num INTEGER,
                                PRIMARY KEY (school_name, grade, class_num))''')
            
            # 학생 정보 테이블
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS students
                                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                school_name TEXT, grade INTEGER, class_num INTEGER,
                                student_number INTEGER,
                                name TEXT, gender TEXT, eyestright TEXT,
                                FOREIGN KEY (school_name, grade, class_num)
                                REFERENCES school_info(school_name, grade, class_num))''')
            
            # 마지막 자리배치 테이블
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS last_layout
                                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                school_name TEXT, grade INTEGER, class_num INTEGER,
                                name TEXT, gender TEXT, eyestright TEXT,
                                row INTEGER, col INTEGER, fixed BOOLEAN,
                                layout_mode TEXT, num_columns INTEGER,
                                separate_gender BOOLEAN,
                                FOREIGN KEY (school_name, grade, class_num)
                                REFERENCES school_info(school_name, grade, class_num))''')
            
            # 설정 테이블
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS settings
                                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                school_name TEXT, grade INTEGER, class_num INTEGER,
                                layout_mode TEXT, num_columns INTEGER,
                                separate_gender BOOLEAN,
                                prevent_same_seat BOOLEAN,
                                prevent_same_seat_count INTEGER,
                                consider_eyesight BOOLEAN,
                                motto TEXT,
                                countdown_text TEXT,
                                FOREIGN KEY (school_name, grade, class_num)
                                REFERENCES school_info(school_name, grade, class_num))''')
            
            # 자리배치 이력 테이블
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS seat_history
                                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                school_name TEXT, grade INTEGER, class_num INTEGER,
                                name TEXT, row INTEGER, col INTEGER,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (school_name, grade, class_num)
                                REFERENCES school_info(school_name, grade, class_num))''')
            
            self.conn.commit()
            print("데이터베이스 테이블 확인 완료")
            
        except Exception as e:
            print(f"테이블 생성 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            self.conn.rollback()

    def showEvent(self, event):
        """윈도우가 처음 표시될 때 호출되는 이벤트 핸들러"""
        super().showEvent(event)
        
        # 이미 초기화되었다면 다시 실행하지 않음
        if getattr(self, 'initialized', False):
            return
            
        try:
            print("\n=== 프로그램 초기화 시작 ===")
            
            # 1. 학교 정보 로드
            if not self.load_school_info():
                print("학교 정보 로드 실패")
                return
            
            # 2. 설정 정보 로드
            print("설정 정보 로드 중...")
            self.load_settings()
            print(f"로드된 설정 - 레이아웃 모드: {self.layout_mode}, 열 수: {self.num_columns}")
            
            # 3. 학생 데이터 로드
            print("학생 데이터 로드 중...")
            self.load_student_data()
            
            # 학생 데이터가 제대로 로드되었는지 확인
            if not hasattr(self, 'all_students') or not self.all_students:
                print("학생 데이터가 로드되지 않았습니다.")
                QMessageBox.warning(self, "경고", "학생 데이터가 없습니다. 학생을 등록해주세요.")
            
            # 4. 마지막 자리 배치 로드
            print("마지막 자리 배치 로드 중...")
            if not self.load_last_layout():
                print("저장된 자리 배치가 없습니다.")
                # 저장된 자리 배치가 없을 때는 빈 레이아웃만 생성
                self.current_layout = []
                self.draw_seats(self.num_columns)
            
            # 5. 학생별 자리 기록 로드
            print("학생별 자리 기록 로드 중...")
            self.load_student_seat_history()
            
            # 6. 창 제목 최종 업데이트
            self.update_window_title()
            
            self.initialized = True
            print("=== 프로그램 초기화 완료 ===\n")
            
        except Exception as e:
            print(f"초기화 중 오류 발생: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "오류", f"초기화 중 오류가 발생했습니다: {str(e)}")
            self.close()

    def load_student_seat_history(self):
        """학생별 자리 기록 로드"""
        if not self.school_info['school_name']:
            return

        self.cursor.execute('''SELECT name, row, col FROM seat_history 
                            WHERE school_name=? AND grade=? AND class_num=?
                            ORDER BY created_at DESC''',
                           (self.school_info['school_name'], self.school_info['grade'], self.school_info['class_num']))
        
        for row in self.cursor.fetchall():
            name, row_num, col_num = row
            self.student_seat_history[name].append((row_num, col_num))

    def save_layout_to_db(self):
        """자리 배치 저장"""
        if not self.school_info['school_name']:
            print("학교 정보가 없어 저장할 수 없습니다.")
            return

        try:
            print("\n=== 자리 배치 저장 시작 ===")
            
            # 현재 시간을 저장 시점으로 사용
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"저장 시점: {current_time}")
            
            # 현재 레이아웃 저장
            for seat in self.current_layout:
                if seat['name']:  # 이름이 있는 경우만 저장
                    try:
                        self.cursor.execute('''INSERT INTO seat_history 
                                            (school_name, grade, class_num, name, row, col, created_at)
                                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                           (self.school_info['school_name'], 
                                            self.school_info['grade'], 
                                            self.school_info['class_num'],
                                            seat['name'], 
                                            seat['row'], 
                                            seat['col'],
                                            current_time))
                        print(f"학생 {seat['name']}의 자리 ({seat['row']}, {seat['col']}) 저장 완료")
                    except sqlite3.Error as e:
                        print(f"학생 {seat['name']}의 자리 저장 중 오류: {str(e)}")
            
            # 변경사항 커밋
            self.conn.commit()
            print("자리 배치 저장 완료")
            
        except Exception as e:
            print(f"자리 배치 저장 중 오류: {str(e)}")
            self.conn.rollback()
            raise

    def on_shuffle_button_clicked(self):
        """자리 섞기 버튼 클릭 시 실행"""
        try:
            print("\n=== 자리 섞기 버튼 클릭 ===")
            print(f"현재 고정 좌석: {self.fixed_seats}")
            
            # 수동 지정 모드 종료
            self.manual_designate_mode = False
            
            # 자리 섞기 전에 현재 레이아웃 저장
            self.save_layout_to_db()
            
            # 자리 섞기 실행 (효과음/애니메이션 포함)
            self.show_countdown()
            
        except Exception as e:
            print(f"자리 섞기 버튼 클릭 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "오류", f"자리 섞기 중 오류가 발생했습니다: {str(e)}")

    def show_countdown(self):
        """카운트다운 또는 동영상 실행 후 자리 섞기"""
        print("=== show_countdown 시작 ===")
        countdown_value = self.settings.get('countdown_text', '')
        print(f"카운트다운 값: {countdown_value}")
        
        try:
            # 기존 위젯들을 담을 임시 리스트
            widgets_to_remove = []
            if self.seat_frame.layout():
                layout = self.seat_frame.layout()
                for i in range(layout.count()):
                    widget = layout.itemAt(i).widget()
                    if widget:
                        widgets_to_remove.append(widget)
            for widget in widgets_to_remove:
                widget.hide()

            # 새 컨테이너 위젯 생성 (좌석 영역에 맞춤)
            container = QWidget(self.seat_frame)
            container.setObjectName("video_container")
            container.setStyleSheet("QWidget#video_container { background: black; }")
            # 좌석 영역에 맞게 위치와 크기 설정
            container.setGeometry(111, 148, 1024, 510)  # 좌석 영역 좌표에 맞춤
            video_layout = QVBoxLayout(container)
            video_layout.setContentsMargins(0, 0, 0, 0)
            video_layout.setSpacing(0)

            # 비디오 플레이어 생성
            video_widget = QVideoWidget(container)
            video_widget.resize(container.size())
            video_layout.addWidget(video_widget)

            # 오디오 출력 설정
            self.audio_output = QAudioOutput()
            self.audio_output.setVolume(1.0)

            # 미디어 플레이어 설정
            self.media_player = QMediaPlayer()
            self.media_player.setVideoOutput(video_widget)
            self.media_player.setAudioOutput(self.audio_output)
            self.media_player.mediaStatusChanged.connect(self.handle_media_status)
            
            # 동영상 파일 경로 설정 (countdown 폴더 내)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            countdown_dir = os.path.join(base_dir, 'countdown')
            
            # countdown 폴더가 없으면 생성
            if not os.path.exists(countdown_dir):
                os.makedirs(countdown_dir)
                print(f"countdown 폴더 생성됨: {countdown_dir}")
            
            if countdown_value:
                # 파일명에 확장자가 없으면 .mp4 추가
                if not countdown_value.lower().endswith(('.mp4', '.avi', '.mov', '.wmv')):
                    countdown_value = countdown_value + '.mp4'
                
                video_path = os.path.join(countdown_dir, countdown_value)
                print(f"시도할 동영상 파일 경로: {video_path}")
                
                if os.path.exists(video_path):
                    print(f"동영상 파일 재생: {video_path}")
                    self.media_player.setSource(QUrl.fromLocalFile(video_path))
                    self.media_player.play()
                else:
                    print(f"동영상 파일을 찾을 수 없습니다: {video_path}")
                    QMessageBox.warning(self, "경고", 
                        f"동영상 파일을 찾을 수 없습니다.\n"
                        f"경로: {video_path}\n\n"
                        f"확인사항:\n"
                        f"1. countdown 폴더에 파일이 있는지 확인\n"
                        f"2. 파일명이 정확한지 확인\n"
                        f"3. 파일 확장자가 .mp4인지 확인")
                    # 동영상이 없어도 효과음 재생
                    self.play_effect_sound()
                    return
            else:
                # 동영상 설정이 없으면 바로 효과음 재생
                self.play_effect_sound()
                return

            container.show()
            container.raise_()

            # 멤버변수로 보관
            self._video_container = container
            self._video_widgets_to_remove = widgets_to_remove
            
        except Exception as e:
            print(f"show_countdown 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            # 오류 발생 시에도 효과음 재생
            self.play_effect_sound()

    def handle_media_status(self, status):
        """미디어 상태 변경 처리"""
        print(f"미디어 상태 변경: {status}")
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            print("동영상 재생 완료, 효과음 재생 시작")
            self.play_effect_sound()

    def play_effect_sound(self):
        """효과음 재생"""
        try:
            print("효과음 재생 시작")
            
            # 비디오 컨테이너 제거
            if hasattr(self, '_video_container'):
                try:
                    self._video_container.deleteLater()
                except RuntimeError:
                    pass
                delattr(self, '_video_container')
            
            # 기존 위젯들 복원
            if hasattr(self, '_video_widgets_to_remove'):
                for widget in self._video_widgets_to_remove:
                    try:
                        widget.show()
                    except RuntimeError:
                        pass
                delattr(self, '_video_widgets_to_remove')
            
            # 배경화면 복원
            if hasattr(self, 'bg_label'):
                self.set_background_image()
                self.bg_label.show()
            
            # 효과음 파일 경로 설정
            base_dir = os.path.dirname(os.path.abspath(__file__))
            effect_path = os.path.join(base_dir, 'countdown', 'effect_1.m4a')
            
            if os.path.exists(effect_path):
                print(f"효과음 재생: {effect_path}")
                
                # 기존 효과음 플레이어 정리
                self.cleanup_effect_resources()
                
                # 새로운 효과음용 오디오 출력 설정
                self.effect_audio_output = QAudioOutput()
                self.effect_audio_output.setVolume(1.0)
                
                # 새로운 효과음용 미디어 플레이어 생성
                self.effect_player = QMediaPlayer()
                self.effect_player.setAudioOutput(self.effect_audio_output)
                self.effect_player.setSource(QUrl.fromLocalFile(effect_path))
                self.effect_player.mediaStatusChanged.connect(self.handle_effect_status)
                
                # 자리배치 시작
                self.start_shuffle_animation()
                
                # 효과음 재생
                if self.effect_player and self.effect_player.mediaStatus() != QMediaPlayer.MediaStatus.NoMedia:
                    self.effect_player.play()
                    print("효과음 재생 시작됨")
                else:
                    print("효과음 재생 실패: 미디어 플레이어가 준비되지 않았습니다.")
                    self.close_video_and_shuffle()
            else:
                print(f"효과음 파일을 찾을 수 없습니다: {effect_path}")
                self.close_video_and_shuffle()
                
        except Exception as e:
            print(f"효과음 재생 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            self.close_video_and_shuffle()

    def handle_effect_status(self, status):
        """효과음 상태 변경 처리"""
        try:
            print(f"효과음 상태 변경: {status}")
            if status == QMediaPlayer.MediaStatus.EndOfMedia:
                print("효과음 재생 완료")
                # 애니메이션 타이머 중지
                if hasattr(self, 'shuffle_timer'):
                    try:
                        self.shuffle_timer.stop()
                    except RuntimeError:
                        pass
                # 최종 레이아웃 적용
                self.current_layout = self.target_layout
                self.draw_seats(self.num_columns)
                # 모든 효과 제거
                if hasattr(self, 'seat_labels'):
                    for label in self.seat_labels.values():
                        try:
                            label.setGraphicsEffect(None)
                        except RuntimeError:
                            pass
                # 리소스 정리 및 자리 섞기
                QTimer.singleShot(200, self.cleanup_and_shuffle)
        except Exception as e:
            print(f"효과음 상태 처리 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            self.cleanup_and_shuffle()

    def start_shuffle_animation(self):
        """자리배치 애니메이션 시작"""
        # 기존 타이머 정리
        if hasattr(self, 'shuffle_timer'):
            self.shuffle_timer.stop()
        
        # 자리배치 데이터 준비
        self.prepare_shuffle_data()
        
        # 애니메이션 타이머 설정 (더 느리게)
        self.shuffle_timer = QTimer()
        self.shuffle_timer.timeout.connect(self.update_shuffle_animation)
        self.shuffle_timer.start(200)  # 200ms 간격으로 업데이트 (더 느린 애니메이션)
        
        # 현재 애니메이션 단계 초기화
        self.current_shuffle_step = 0
        self.total_shuffle_steps = 60  # 전체 애니메이션 단계 수 증가

    def prepare_shuffle_data(self):
        """자리배치 데이터 준비"""
        if not self.all_students:
            return
            
        # 현재 레이아웃 저장
        self.original_layout = self.current_layout.copy() if self.current_layout else []
        
        # 새로운 레이아웃 생성
        self.target_layout = []
        seated_students = [seat['name'] for seat in self.original_layout if seat['name']]
        random.shuffle(seated_students)
        
        # 학생 정보 가져오기
        student_info = {}
        for student in self.all_students:
            self.cursor.execute('''SELECT gender, eyestright FROM students 
                                WHERE school_name=? AND grade=? AND class_num=? AND name=?''',
                              (self.school_info['school_name'], self.school_info['grade'], 
                               self.school_info['class_num'], student))
            result = self.cursor.fetchone()
            if result:
                student_info[student] = {
                    'gender': result[0],
                    'eyestright': result[1]
                }
        
        student_index = 0
        for seat in self.original_layout:
            if seat['name']:
                student_name = seated_students[student_index]
                info = student_info.get(student_name, {'gender': '', 'eyestright': ''})
                self.target_layout.append({
                    'row': seat['row'],
                    'col': seat['col'],
                    'name': student_name,
                    'gender': info['gender'],
                    'eyestright': info['eyestright']
                })
                student_index += 1
            else:
                self.target_layout.append({
                    'row': seat['row'],
                    'col': seat['col'],
                    'name': '',
                    'gender': '',
                    'eyestright': ''
                })

    def update_shuffle_animation(self):
        """자리배치 애니메이션 업데이트"""
        if not hasattr(self, 'current_shuffle_step'):
            return
        
        self.current_shuffle_step += 1
        progress = self.current_shuffle_step / self.total_shuffle_steps
        
        # 현재 레이아웃 업데이트
        for i, seat in enumerate(self.original_layout):
            if seat['name']:
                # 현재 위치와 목표 위치 사이를 보간
                current_name = seat['name']
                target_name = self.target_layout[i]['name']
                
                # 랜덤하게 이름 변경 (셔플 효과)
                if random.random() < 0.2:  # 20% 확률로 이름 변경
                    self.current_layout[i]['name'] = random.choice(self.all_students)
                else:
                    # 점진적으로 목표 이름으로 변경
                    if random.random() < progress:
                        self.current_layout[i]['name'] = target_name
        
        # 화면 업데이트
        self.draw_seats(self.num_columns)
        
        # 애니메이션 완료 체크
        if self.current_shuffle_step >= self.total_shuffle_steps:
            self.shuffle_timer.stop()
            self.current_layout = self.target_layout
            self.draw_seats(self.num_columns)
            # 모든 효과 제거
            if hasattr(self, 'seat_labels'):
                for label in self.seat_labels.values():
                    label.setGraphicsEffect(None)

    def cleanup_and_shuffle(self):
        """효과음 정리 및 자리 섞기"""
        try:
            print("효과음 정리 및 자리 섞기 시작")
            
            # 효과음 관련 리소스 정리
            self.cleanup_effect_resources()
            
            # 배경화면 복원
            if hasattr(self, 'bg_label'):
                self.set_background_image()
                self.bg_label.show()
            
            # 자리배치 라벨들 다시 표시
            if hasattr(self, 'seat_labels'):
                for label in self.seat_labels.values():
                    try:
                        label.show()
                    except RuntimeError:
                        pass
            
            # 급훈 라벨 다시 표시
            if hasattr(self, 'motto_label'):
                try:
                    self.motto_label.show()
                except RuntimeError:
                    pass
            
            # UI 갱신 강제 수행
            QApplication.processEvents()
            
            print("자리 섞기 실행 전")
            # 자리 섞기 실행
            self.shuffle_seats()
            
        except Exception as e:
            print(f"자리 섞기 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()

    def close_video_and_shuffle(self):
        """동영상 종료 후 처리"""
        print("동영상 종료 처리 시작")
        self.cleanup_and_shuffle()

    def shuffle_seats(self):
        """자리 섞기"""
        try:
            print("\n=== 자리 섞기 시작 ===")
            print(f"고정된 좌석: {self.fixed_seats}")
            
            # 고정 좌석 정보 임시 저장
            fixed_seats_backup = self.fixed_seats.copy()
            
            # 학생 데이터 다시 로드
            self.load_student_data()
            
            # 학생 목록이 비어있으면 리턴
            if not self.all_students:
                print("학생 목록이 비어있습니다")
                return
            
            print(f"전체 학생 수: {len(self.all_students)}명")
            
            # 학생 정보 수집
            student_info = {}
            for student in self.all_students:
                self.cursor.execute('''SELECT gender, eyestright FROM students 
                                    WHERE school_name=? AND grade=? AND class_num=? AND name=?''',
                                  (self.school_info['school_name'], self.school_info['grade'], 
                                   self.school_info['class_num'], student))
                result = self.cursor.fetchone()
                if result:
                    gender, eyestright = result
                    student_info[student] = {'gender': gender, 'eyestright': eyestright}
            
            # 고정된 학생 목록 생성
            fixed_students = set()
            for student_name in fixed_seats_backup.values():
                fixed_students.add(student_name)
            
            # 이동 가능한 학생 목록 생성
            movable_students = [student for student in self.all_students if student not in fixed_students]
            print(f"이동 가능한 학생 수: {len(movable_students)}명")
            
            # 이동 가능한 학생 분류
            male_eyesight_issues = []
            female_eyesight_issues = []
            male_normal = []
            female_normal = []
            
            for student in movable_students:
                info = student_info[student]
                if info['gender'] == 'male':
                    if self.settings.get('consider_eyesight', False) and info['eyestright'] == '이상':
                        male_eyesight_issues.append(student)
                    else:
                        male_normal.append(student)
                else:  # female
                    if self.settings.get('consider_eyesight', False) and info['eyestright'] == '이상':
                        female_eyesight_issues.append(student)
                    else:
                        female_normal.append(student)
            
            # 학생 목록 섞기
            random.shuffle(male_eyesight_issues)
            random.shuffle(female_eyesight_issues)
            random.shuffle(male_normal)
            random.shuffle(female_normal)
            
            # 필요한 행 수 계산
            def calculate_required_rows(male_count, female_count, num_columns):
                if getattr(self, 'layout_mode', '열') == '분단':
                    # 분단 모드에서는 각 분단당 2명씩 배치
                    students_per_row = num_columns
                    total_students = male_count + female_count
                    # 남녀 학생 수의 차이를 고려하여 추가 행 계산
                    gender_diff = abs(male_count - female_count)
                    base_rows = (total_students + students_per_row - 1) // students_per_row
                    # 남녀 차이가 있는 경우에만 1행 추가
                    return base_rows + (1 if gender_diff > 0 else 0)
                else:
                    # 일반 모드
                    return (male_count + female_count + num_columns - 1) // num_columns
            
            # 남녀 학생 수 계산
            male_count = len(male_eyesight_issues) + len(male_normal)
            female_count = len(female_eyesight_issues) + len(female_normal)
            
            # 필요한 행 수 계산
            required_rows = calculate_required_rows(male_count, female_count, self.num_columns)
            print(f"필요한 행 수: {required_rows}행")
            
            # 새로운 레이아웃 생성
            new_layout = []
            for row in range(1, required_rows + 1):
                for col in range(1, self.num_columns + 1):
                    new_layout.append({
                        'row': row,
                        'col': col,
                        'name': '',
                        'gender': '',
                        'eyestright': ''
                    })
            
            # 고정 좌석 먼저 배치
            for row in range(1, required_rows + 1):
                for col in range(1, self.num_columns + 1):
                    if (row, col) in fixed_seats_backup:
                        student_name = fixed_seats_backup[(row, col)]
                        self.cursor.execute('''SELECT gender, eyestright FROM students 
                                            WHERE school_name=? AND grade=? AND class_num=? AND name=?''',
                                          (self.school_info['school_name'], self.school_info['grade'], 
                                           self.school_info['class_num'], student_name))
                        result = self.cursor.fetchone()
                        if result:
                            gender, eyestright = result
                            seat = next((s for s in new_layout if s['row'] == row and s['col'] == col), None)
                            if seat and not seat['name']:
                                seat['name'] = student_name
                                seat['gender'] = gender
                                seat['eyestright'] = eyestright
            
            # 남여자리구분 설정이 켜져있는 경우
            if self.settings.get('separate_gender', False):
                # 분단 모드인 경우
                if getattr(self, 'layout_mode', '열') == '분단':
                    # 각 분단별로 남학생/여학생 번갈아가며 배치
                    num_groups = (self.num_columns + 1) // 2
                    male_students = male_eyesight_issues + male_normal
                    female_students = female_eyesight_issues + female_normal
                    male_index = 0
                    female_index = 0
                    
                    for row in range(1, required_rows + 1):
                        for group in range(num_groups):
                            # 각 분단의 첫 번째 열
                            col1 = group * 2 + 1
                            # 각 분단의 두 번째 열
                            col2 = group * 2 + 2
                            
                            # 첫 번째 열에 남학생 배치
                            if (row, col1) not in fixed_seats_backup and male_index < len(male_students):
                                student = male_students[male_index]
                                info = student_info[student]
                                seat = next((s for s in new_layout if s['row'] == row and s['col'] == col1), None)
                                if seat and not seat['name']:
                                    seat['name'] = student
                                    seat['gender'] = info['gender']
                                    seat['eyestright'] = info['eyestright']
                                male_index += 1
                            
                            # 두 번째 열에 여학생 배치
                            if (row, col2) not in fixed_seats_backup and female_index < len(female_students):
                                student = female_students[female_index]
                                info = student_info[student]
                                seat = next((s for s in new_layout if s['row'] == row and s['col'] == col2), None)
                                if seat and not seat['name']:
                                    seat['name'] = student
                                    seat['gender'] = info['gender']
                                    seat['eyestright'] = info['eyestright']
                                female_index += 1
                else:
                    # 일반 열 모드 - 열별로 번갈아 남녀 배치
                    male_students = male_eyesight_issues + male_normal
                    female_students = female_eyesight_issues + female_normal
                    male_index = 0
                    female_index = 0

                    # 홀수 열(1,3,5...)은 남학생, 짝수 열(2,4,6...)은 여학생
                    for row in range(1, required_rows + 1):
                        for col in range(1, self.num_columns + 1):
                            if (row, col) not in fixed_seats_backup:
                                if col % 2 == 1:  # 홀수 열(남학생)
                                    if male_index < len(male_students):
                                        student = male_students[male_index]
                                        info = student_info[student]
                                        seat = next((s for s in new_layout if s['row'] == row and s['col'] == col), None)
                                        if seat and not seat['name']:
                                            seat['name'] = student
                                            seat['gender'] = info['gender']
                                            seat['eyestright'] = info['eyestright']
                                        male_index += 1
                                else:  # 짝수 열(여학생)
                                    if female_index < len(female_students):
                                        student = female_students[female_index]
                                        info = student_info[student]
                                        seat = next((s for s in new_layout if s['row'] == row and s['col'] == col), None)
                                        if seat and not seat['name']:
                                            seat['name'] = student
                                            seat['gender'] = info['gender']
                                            seat['eyestright'] = info['eyestright']
                                        female_index += 1
                    # 남거나 못 들어간 학생이 있으면 빈자리에 추가로 배치
                    for row in range(1, required_rows + 1):
                        for col in range(1, self.num_columns + 1):
                            if (row, col) not in fixed_seats_backup:
                                seat = next((s for s in new_layout if s['row'] == row and s['col'] == col), None)
                                if seat and not seat['name']:
                                    if male_index < len(male_students):
                                        student = male_students[male_index]
                                        info = student_info[student]
                                        seat['name'] = student
                                        seat['gender'] = info['gender']
                                        seat['eyestright'] = info['eyestright']
                                        male_index += 1
                                    elif female_index < len(female_students):
                                        student = female_students[female_index]
                                        info = student_info[student]
                                        seat['name'] = student
                                        seat['gender'] = info['gender']
                                        seat['eyestright'] = info['eyestright']
                                        female_index += 1
            else:
                # 남여 구분 없이 배치
                all_students = []
                if self.settings.get('consider_eyesight', False):
                    # 시력이상 학생을 먼저 배치
                    all_students.extend(male_eyesight_issues + female_eyesight_issues)
                    all_students.extend(male_normal + female_normal)
                else:
                    # 모든 학생을 섞어서 배치
                    all_students = male_eyesight_issues + female_eyesight_issues + male_normal + female_normal
                    random.shuffle(all_students)
                
                student_index = 0
                for row in range(1, required_rows + 1):
                    for col in range(1, self.num_columns + 1):
                        if (row, col) not in fixed_seats_backup and student_index < len(all_students):
                            student = all_students[student_index]
                            info = student_info[student]
                            seat = next((s for s in new_layout if s['row'] == row and s['col'] == col), None)
                            if seat and not seat['name']:
                                seat['name'] = student
                                seat['gender'] = info['gender']
                                seat['eyestright'] = info['eyestright']
                            student_index += 1
            
            # 배치된 학생 수 확인
            seated_students = len([seat for seat in new_layout if seat['name']])
            print(f"배치된 학생 수: {seated_students}명")
            print(f"전체 학생 수: {len(self.all_students)}명")
            
            # 모든 학생이 배치되었는지 확인
            if seated_students != len(self.all_students):
                print(f"경고: 배치된 학생 수({seated_students})가 전체 학생 수({len(self.all_students)})와 다릅니다.")
                # 필요한 경우 추가 행 생성
                if seated_students < len(self.all_students):
                    # 남녀 차이가 있는 경우에만 1행 추가
                    if abs(male_count - female_count) > 0:
                        for col in range(1, self.num_columns + 1):
                            new_layout.append({
                                'row': required_rows + 1,
                                'col': col,
                                'name': '',
                                'gender': '',
                                'eyestright': ''
                            })
            
            # 현재 레이아웃 업데이트
            self.current_layout = new_layout
            
            # 고정 좌석 정보 복원
            self.fixed_seats = fixed_seats_backup
            
            # 자리 배치 그리기
            self.draw_seats(self.num_columns)
            
            print(f"자리 섞기 완료 - 고정 좌석: {self.fixed_seats}")
            
        except Exception as e:
            print(f"자리 섞기 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "오류", f"자리 섞기 중 오류가 발생했습니다: {str(e)}")

    def on_save_layout_click(self):
        """현재 레이아웃 저장"""
        try:
            print("\n=== 자리 배치 저장 시작 ===")
            
            # 현재 시간을 저장 시점으로 사용
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"저장 시점: {current_time}")
            
            # 이전 자리배치 구조와 설정 확인
            self.cursor.execute('''SELECT layout_mode, num_columns, separate_gender FROM last_layout 
                                WHERE school_name=? AND grade=? AND class_num=? 
                                GROUP BY layout_mode, num_columns, separate_gender''',
                                (self.school_info['school_name'],
                                self.school_info['grade'],
                                self.school_info['class_num']))
            prev_layout = self.cursor.fetchone()
            
            # 현재 레이아웃 구조와 설정
            current_layout_mode = self.settings.get('layout_mode', '열')
            current_num_columns = self.num_columns
            current_separate_gender = self.settings.get('separate_gender', False)
            
            # 이전 레이아웃이 있고 구조나 설정이 다른 경우
            if prev_layout and (prev_layout[0] != current_layout_mode or 
                              prev_layout[1] != current_num_columns or 
                              prev_layout[2] != current_separate_gender):
                print("이전 레이아웃과 구조/설정이 다름 - 이전 이력 삭제")
                print(f"이전: 모드={prev_layout[0]}, 열={prev_layout[1]}, 남여구분={prev_layout[2]}")
                print(f"현재: 모드={current_layout_mode}, 열={current_num_columns}, 남여구분={current_separate_gender}")
                
                # 이전 이력 삭제
                self.cursor.execute('''DELETE FROM seat_history 
                                    WHERE school_name=? AND grade=? AND class_num=?''',
                                    (self.school_info['school_name'],
                                    self.school_info['grade'],
                                    self.school_info['class_num']))
                self.conn.commit()
                print("이전 자리배치 이력이 삭제되었습니다.")
            
            # 현재 레이아웃을 last_layout에 저장
            self.cursor.execute('''DELETE FROM last_layout 
                                WHERE school_name=? AND grade=? AND class_num=?''',
                                (self.school_info['school_name'],
                                self.school_info['grade'],
                                self.school_info['class_num']))
            
            # 현재 레이아웃 저장
            for seat in self.current_layout:
                if seat['name']:  # 빈 자리는 저장하지 않음
                    # 학생의 정보 가져오기
                    self.cursor.execute('''SELECT gender, eyestright FROM students 
                                        WHERE school_name=? AND grade=? AND class_num=? AND name=?''',
                                        (self.school_info['school_name'],
                                        self.school_info['grade'],
                                        self.school_info['class_num'],
                                        seat['name']))
                    student = self.cursor.fetchone()
                    gender = student[0] if student else ''
                    eyestright = student[1] if student else ''
                    
                    self.cursor.execute('''INSERT INTO last_layout 
                                        (school_name, grade, class_num, name, gender, eyestright, 
                                        row, col, fixed, layout_mode, num_columns, separate_gender)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                        (self.school_info['school_name'],
                                        self.school_info['grade'],
                                        self.school_info['class_num'],
                                        seat['name'],
                                        gender,
                                        eyestright,
                                        seat['row'],
                                        seat['col'],
                                        seat.get('fixed', False),
                                        current_layout_mode,
                                        current_num_columns,
                                        current_separate_gender))
            
            # 이전 레이아웃과 구조/설정이 같은 경우에만 이력 저장
            if not prev_layout or (prev_layout[0] == current_layout_mode and 
                                 prev_layout[1] == current_num_columns and 
                                 prev_layout[2] == current_separate_gender):
                print("이전 레이아웃과 구조/설정이 같음 - 이력 저장")
                for seat in self.current_layout:
                    if seat['name']:  # 빈 자리는 저장하지 않음
                        self.cursor.execute('''INSERT INTO seat_history 
                                            (school_name, grade, class_num, name, row, col, created_at)
                                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                            (self.school_info['school_name'],
                                            self.school_info['grade'],
                                            self.school_info['class_num'],
                                            seat['name'],
                                            seat['row'],
                                            seat['col'],
                                            current_time))
            else:
                print("새로운 레이아웃 구조/설정으로 이력 저장")
                for seat in self.current_layout:
                    if seat['name']:  # 빈 자리는 저장하지 않음
                        self.cursor.execute('''INSERT INTO seat_history 
                                            (school_name, grade, class_num, name, row, col, created_at)
                                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                            (self.school_info['school_name'],
                                            self.school_info['grade'],
                                            self.school_info['class_num'],
                                            seat['name'],
                                            seat['row'],
                                            seat['col'],
                                            current_time))
            
            self.conn.commit()
            print("자리 배치 저장 완료")
            QMessageBox.information(self, "저장 완료", "자리 배치가 저장되었습니다.")
            
        except Exception as e:
            print(f"자리 배치 저장 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            self.conn.rollback()
            QMessageBox.critical(self, "오류", f"자리 배치 저장 중 오류가 발생했습니다: {str(e)}")

    def ask_layout_mode(self):
        popup = QDialog(self)
        popup.setWindowTitle("배치 방식 선택")
        popup.setFixedSize(350, 300)
        popup.setModal(True)
        popup.setStyleSheet("background-color: #f0f0f0;")

        layout = QVBoxLayout(popup)

        # 제목 레이블
        title_label = QLabel("✨ 배치 방식을 선택하세요 ✨")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        layout.addSpacing(20)

        # 라디오 버튼 그룹
        button_group = QButtonGroup(popup)
        
        rb1 = QRadioButton("열 단위 배치")
        rb1.setStyleSheet("font-size: 11pt; font-weight: bold;")
        button_group.addButton(rb1, 1)
        layout.addWidget(rb1)

        # 열 수 입력 프레임
        column_frame = QFrame()
        column_layout = QHBoxLayout(column_frame)
        column_label = QLabel("열 수:")
        column_label.setStyleSheet("font-size: 11pt;")
        column_input = QLineEdit()
        column_input.setFixedWidth(50)
        column_input.setText(str(self.num_columns))  # 현재 설정된 열 수 표시
        column_layout.addWidget(column_label)
        column_layout.addWidget(column_input)
        column_layout.addStretch()
        layout.addWidget(column_frame)

        rb2 = QRadioButton("분단 단위 배치 (1분단 = 2열)")
        rb2.setStyleSheet("font-size: 11pt; font-weight: bold;")
        button_group.addButton(rb2, 2)
        layout.addWidget(rb2)

        # 분단 수 입력 프레임
        group_frame = QFrame()
        group_layout = QHBoxLayout(group_frame)
        group_label = QLabel("분단 수:")
        group_label.setStyleSheet("font-size: 11pt;")
        group_input = QLineEdit()
        group_input.setFixedWidth(50)
        group_input.setText(str(self.num_columns // 2))  # 현재 설정된 분단 수 표시
        group_layout.addWidget(group_label)
        group_layout.addWidget(group_input)
        group_layout.addStretch()
        layout.addWidget(group_frame)

        layout.addSpacing(20)

        def handle_selection():
            try:
                if rb1.isChecked():
                    num = int(column_input.text())
                    if num < 1 or num > 10:
                        raise ValueError("열 수는 1에서 10 사이여야 합니다.")
                    self.num_columns = num
                    self.layout_mode = '열'
                    self.current_layout = []  # 열 변경 시 기존 자리배치 초기화
                    # 설정 저장
                    self.save_settings()
                    QMessageBox.information(popup, "설정 완료", 
                                         f"{num}열로 설정되었습니다.\n'자리바꾸기' 버튼을 눌러 자리배치를 시작하세요.")
                    popup.accept()
                elif rb2.isChecked():
                    num = int(group_input.text())
                    if num < 1 or num > 5:
                        raise ValueError("분단 수는 1에서 5 사이여야 합니다.")
                    self.layout_mode = '분단'
                    self.num_columns = num * 2  # 분단 수 * 2 = 열 수
                    print(f"분단 모드 설정: {num}분단, {self.num_columns}열")
                    self.current_layout = []  # 분단 변경 시 기존 자리배치 초기화
                    # 설정 저장
                    self.save_settings()
                    QMessageBox.information(popup, "설정 완료", 
                                         f"{num}분단({num*2}열)으로 설정되었습니다.\n'자리바꾸기' 버튼을 눌러 자리배치를 시작하세요.")
                    popup.accept()
            except ValueError as e:
                QMessageBox.warning(popup, "입력 오류", str(e))

        # 확인 버튼
        confirm_button = QPushButton("확인")
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        confirm_button.clicked.connect(handle_selection)
        layout.addWidget(confirm_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # 현재 모드에 따라 기본값 선택
        if self.layout_mode == '분단':
            rb2.setChecked(True)
        else:
            rb1.setChecked(True)
        
        popup.exec()

    def on_manual_designate_click(self):
        """수동지정 버튼 클릭 시 실행"""
        try:
            # 자리배치 확인
            if not hasattr(self, 'current_layout') or not self.current_layout:
                print("자리 배치가 없습니다")
                QMessageBox.warning(self, "오류", "먼저 자리 배치를 생성하세요")
                return
                
            # 배치된 학생 확인
            seated_students = [seat for seat in self.current_layout if seat.get('name')]
            if not seated_students:
                print("배치된 학생이 없습니다")
                QMessageBox.warning(self, "오류", "먼저 자리 배치를 생성하세요")
                return
                
            print(f"현재 배치된 학생 수: {len(seated_students)}명")
            
            # 수동지정 모드 활성화
            self.manual_designate_mode = True
            
            # 모든 좌석 스타일 초기화
            if hasattr(self, 'seat_labels'):
                for label in self.seat_labels.values():
                    if (label.row, label.col) in self.fixed_seats:
                        label.setStyleSheet("background-color: yellow; border: 2px solid #f90; font-size: 12pt; min-width: 60px; min-height: 40px; max-width: 90px; max-height: 50px;")
                    else:
                        label.setStyleSheet("border: 1px solid #888; background: #fff; font-size: 12pt; min-width: 60px; min-height: 40px; max-width: 90px; max-height: 50px;")
            
            QMessageBox.information(self, "안내", "고정할 학생을 클릭하세요")
            print("=== 수동지정 모드 설정 완료 ===\n")
            
        except Exception as e:
            print(f"수동 자리 지정 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "오류", f"수동 자리 지정 중 오류가 발생했습니다: {str(e)}")

    def on_manual_swap_click(self):
        """수동 자리 교환"""
        try:
            if not self.current_layout:
                QMessageBox.warning(self, "오류", "먼저 자리 배치를 생성하세요")
                return
                
            # 이전 선택 초기화
            self.selected_seats_to_swap = []
            
            # 모든 좌석 스타일 초기화
            if hasattr(self, 'seat_labels'):
                for label in self.seat_labels.values():
                    if (label.row, label.col) in self.fixed_seats:
                        label.setStyleSheet("background-color: yellow; border: 2px solid #f90; font-size: 12pt; min-width: 60px; min-height: 40px; max-width: 90px; max-height: 50px;")
                    else:
                        label.setStyleSheet("border: 1px solid #888; background: #fff; font-size: 12pt; min-width: 60px; min-height: 40px; max-width: 90px; max-height: 50px;")
            
            # 수동바꾸기 모드 활성화
            self.manual_swap_mode = True
            print("수동바꾸기 모드 활성화됨")  # 디버그 메시지
            QMessageBox.information(self, "안내", "수동바꾸기 모드가 시작되었습니다.\n교환할 두 자리를 순서대로 클릭하세요.")
            
        except Exception as e:
            print(f"수동 자리 교환 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "오류", f"수동 자리 교환 중 오류가 발생했습니다: {str(e)}")

    def select_for_swap(self, row, col):
        """자리 교환을 위한 자리 선택"""
        try:
            if self.manual_designate_mode:
                # 수동지정 모드에서 자리 클릭 시 고정 좌석 추가
                seat = next((s for s in self.current_layout if s['row'] == row and s['col'] == col), None)
                if seat and seat['name']:
                    self.fixed_seats[(row, col)] = seat['name']
                    self.draw_seats(self.num_columns)
                    print(f"고정 좌석 추가: {seat['name']} at ({row}, {col})")
                return
            # 수동 바꾸기 모드가 아닌 경우 리턴
            if not getattr(self, 'manual_swap_mode', False):
                print("수동바꾸기 모드가 아닙니다")
                return

            # 현재 좌석이 유효한지 확인
            if not any(seat['row'] == row and seat['col'] == col for seat in self.current_layout):
                print(f"유효하지 않은 좌석: ({row}, {col})")
                return

            # 이미 선택된 자리가 있는지 확인
            if hasattr(self, 'selected_seat') and self.selected_seat is not None:
                # 같은 자리를 선택한 경우 선택 해제
                if self.selected_seat == (row, col):
                    self.selected_seat = None
                    # 선택 표시 제거
                    for seat in self.current_layout:
                        if seat['row'] == row and seat['col'] == col:
                            seat['selected'] = False
                    self.draw_seats(self.num_columns)
                    return
                
                # 남여자리구분이 설정된 경우 성별 확인
                if self.settings.get('separate_gender', False):
                    # 첫 번째 선택된 자리의 학생 정보
                    first_seat = next((seat for seat in self.current_layout 
                                    if seat['row'] == self.selected_seat[0] and 
                                    seat['col'] == self.selected_seat[1]), None)
                    # 두 번째 선택된 자리의 학생 정보
                    second_seat = next((seat for seat in self.current_layout 
                                     if seat['row'] == row and seat['col'] == col), None)
                    
                    # 두 자리 모두 학생이 있는 경우에만 성별 확인
                    if first_seat and second_seat and first_seat['name'] and second_seat['name']:
                        if first_seat['gender'] != second_seat['gender']:
                            QMessageBox.warning(self, "경고", "남여자리구분이 설정되어 있습니다. 해당자리로 이동 불가")
                            return
                
                # 자리 교환
                first_seat = next((seat for seat in self.current_layout 
                                if seat['row'] == self.selected_seat[0] and 
                                seat['col'] == self.selected_seat[1]), None)
                second_seat = next((seat for seat in self.current_layout 
                                 if seat['row'] == row and seat['col'] == col), None)
                
                if first_seat and second_seat:
                    # 이름 교환
                    first_seat['name'], second_seat['name'] = second_seat['name'], first_seat['name']
                    # 성별 교환
                    first_seat['gender'], second_seat['gender'] = second_seat['gender'], first_seat['gender']
                    # 시력 교환
                    first_seat['eyestright'], second_seat['eyestright'] = second_seat['eyestright'], first_seat['eyestright']
                    
                    # 선택 표시 제거
                    first_seat['selected'] = False
                    second_seat['selected'] = False
                    
                    # 자리 배치 다시 그리기
                    self.draw_seats(self.num_columns)
                    
                    # 자리 배치 저장
                    self.save_layout_to_db()
                    
                    # 선택 초기화
                    self.selected_seat = None
                    
                    # 교환 후 모드 종료
                    self.manual_swap_mode = False
                    print("수동바꾸기 모드 종료")
            else:
                # 첫 번째 자리 선택
                self.selected_seat = (row, col)
                # 선택 표시
                for seat in self.current_layout:
                    if seat['row'] == row and seat['col'] == col:
                        seat['selected'] = True
                self.draw_seats(self.num_columns)
                
        except Exception as e:
            print(f"자리 선택 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "오류", f"자리 선택 중 오류가 발생했습니다: {str(e)}")

    def on_settings_click(self):
        """설정 버튼 클릭 시 실행"""
        try:
            print("\n=== 설정 버튼 클릭 시작 ===")
            
            # 현재 설정 정보 가져오기
            self.cursor.execute('''SELECT consider_eyesight, separate_gender, prevent_same_seat,
                                        prevent_same_seat_count, motto, countdown_text
                                FROM settings 
                                WHERE school_name=? AND grade=? AND class_num=?''',
                              (self.school_info['school_name'],
                               self.school_info['grade'],
                               self.school_info['class_num']))
            result = self.cursor.fetchone()
            
            if result:
                current_settings = {
                    'consider_eyesight': bool(result[0]),
                    'separate_gender': bool(result[1]),
                    'prevent_same_seat': bool(result[2]),
                    'prevent_same_seat_count': result[3],
                    'motto': result[4] or '',
                    'countdown_text': result[5] or ''
                }
            else:
                current_settings = {
                    'consider_eyesight': False,
                    'separate_gender': True,
                    'prevent_same_seat': False,
                    'prevent_same_seat_count': 3,
                    'motto': '',
                    'countdown_text': ''
                }
            
            # 설정 대화상자 생성
            dialog = QDialog(self)
            dialog.setWindowTitle("설정")
            dialog.setFixedSize(400, 300)
            
            layout = QVBoxLayout()
            dialog.setLayout(layout)
            
            # 시력 고려
            eyesight_check = QCheckBox("시력 고려")
            eyesight_check.setChecked(self.settings.get('consider_eyesight', False))
            layout.addWidget(eyesight_check)
            
            # 남여자리구분
            gender_check = QCheckBox("남여자리구분")
            gender_check.setChecked(self.settings.get('separate_gender', True))
            layout.addWidget(gender_check)
            
            # 동일 자리 금지
            same_seat_check = QCheckBox("같은 자리 방지")
            same_seat_check.setChecked(current_settings['prevent_same_seat'])
            layout.addWidget(same_seat_check)
            
            # 동일 자리 금지 횟수
            count_layout = QHBoxLayout()
            count_label = QLabel("동일 자리 금지 횟수:")
            count_input = QLineEdit()
            count_input.setText(str(current_settings['prevent_same_seat_count']))
            count_input.setFixedWidth(50)
            count_layout.addWidget(count_label)
            count_layout.addWidget(count_input)
            layout.addLayout(count_layout)
            
            # 급훈
            motto_layout = QHBoxLayout()
            motto_label = QLabel("급훈:")
            motto_input = QLineEdit()
            motto_input.setText(current_settings['motto'])
            motto_layout.addWidget(motto_label)
            motto_layout.addWidget(motto_input)
            layout.addLayout(motto_layout)
            
            # 카운트다운 텍스트
            countdown_layout = QHBoxLayout()
            countdown_label = QLabel("카운트다운 텍스트:")
            countdown_input = QLineEdit()
            countdown_input.setText(current_settings['countdown_text'])
            countdown_layout.addWidget(countdown_label)
            countdown_layout.addWidget(countdown_input)
            layout.addLayout(countdown_layout)
            
            # 버튼
            button_layout = QHBoxLayout()
            save_btn = QPushButton("저장")
            cancel_btn = QPushButton("취소")
            button_layout.addWidget(save_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            
            # 저장 버튼 클릭 시
            def on_save():
                try:
                    # 설정 값 가져오기
                    new_settings = {
                        'consider_eyesight': eyesight_check.isChecked(),
                        'separate_gender': gender_check.isChecked(),
                        'prevent_same_seat': same_seat_check.isChecked(),
                        'prevent_same_seat_count': int(count_input.text()),
                        'motto': motto_input.text().strip(),
                        'countdown_text': countdown_input.text().strip()
                    }
                    
                    # 데이터베이스에 저장
                    self.cursor.execute('''UPDATE settings 
                                        SET consider_eyesight=?, separate_gender=?, prevent_same_seat=?,
                                            prevent_same_seat_count=?, motto=?, countdown_text=?
                                        WHERE school_name=? AND grade=? AND class_num=?''',
                                      (new_settings['consider_eyesight'],
                                       new_settings['separate_gender'],
                                       new_settings['prevent_same_seat'],
                                       new_settings['prevent_same_seat_count'],
                                       new_settings['motto'],
                                       new_settings['countdown_text'],
                                       self.school_info['school_name'],
                                       self.school_info['grade'],
                                       self.school_info['class_num']))
                    
                    if self.cursor.rowcount == 0:
                        # 설정이 없는 경우 새로 추가
                        self.cursor.execute('''INSERT INTO settings 
                                            (school_name, grade, class_num, consider_eyesight,
                                             separate_gender, prevent_same_seat, prevent_same_seat_count,
                                             motto, countdown_text)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                          (self.school_info['school_name'],
                                           self.school_info['grade'],
                                           self.school_info['class_num'],
                                           new_settings['consider_eyesight'],
                                           new_settings['separate_gender'],
                                           new_settings['prevent_same_seat'],
                                           new_settings['prevent_same_seat_count'],
                                           new_settings['motto'],
                                           new_settings['countdown_text']))
                    
                    self.conn.commit()
                    print("설정 저장 완료")
                    print(f"새로운 설정: {new_settings}")
                    
                    # 현재 설정 업데이트
                    self.settings.update(new_settings)
                    
                    # 급훈 라벨 업데이트
                    if hasattr(self, 'motto_label'):
                        self.motto_label.setText(new_settings['motto'])
                        self.motto_label.show()
                    
                    dialog.accept()
                    
                except Exception as e:
                    print(f"설정 저장 중 오류: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    QMessageBox.critical(dialog, "오류", f"설정 저장 중 오류가 발생했습니다: {str(e)}")
            
            save_btn.clicked.connect(on_save)
            cancel_btn.clicked.connect(dialog.reject)
            
            dialog.exec()
            
        except Exception as e:
            print(f"설정 버튼 클릭 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "오류", f"설정 창을 열 수 없습니다: {str(e)}")

    def on_register_student_click(self):
        """학생 등록"""
        if not self.school_info['school_name']:
            QMessageBox.warning(self, "오류", "먼저 학교 정보를 등록하세요")
            return

        popup = QDialog(self)
        popup.setWindowTitle("학생 등록")
        popup.setFixedSize(500, 400)
        
        layout = QVBoxLayout(popup)
        
        # 엑셀 파일 불러오기 버튼
        excel_btn = QPushButton("엑셀 파일에서 가져오기")
        excel_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(excel_btn)
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 입력 형식 안내 레이블
        format_label = QLabel("입력 형식: 학교,학년,반,번호,이름,성별(남/여),시력(정상/이상)")
        format_label.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(format_label)
        
        # 예시 레이블
        example_label = QLabel("예시: 서울초등학교,3,1,1,홍길동,남,정상")
        example_label.setStyleSheet("color: #999; font-size: 10pt; font-style: italic;")
        layout.addWidget(example_label)
        
        # 수동 입력 영역
        text_area = QTextEdit()
        text_area.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                font-size: 11pt;
            }
            QTextEdit:focus {
                border: 2px solid #4CAF50;
            }
        """)
        text_area.setPlaceholderText("여기에 학생 정보를 입력하세요...")
        text_area.setAcceptRichText(False)  # 일반 텍스트만 허용
        text_area.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)  # 줄바꿈 비활성화
        layout.addWidget(text_area)
        
        def save_manual_wrapper():
            success_count, error_count = self.save_manual(text_area)
            if success_count > 0:
                popup.accept()
                QMessageBox.information(self, "완료", f"학생 정보가 저장되었습니다\n성공: {success_count}건\n실패: {error_count}건")
            else:
                QMessageBox.warning(self, "실패", "저장된 학생이 없습니다.")
        
        def handle_excel():
            if self.load_from_excel():
                popup.accept()

        excel_btn.clicked.connect(handle_excel)

        # 수동 입력 저장 버튼
        save_button = QPushButton("수동 입력 저장")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_button.clicked.connect(save_manual_wrapper)
        layout.addWidget(save_button)

        popup.exec()

    def save_manual(self, text_area):
        """수동으로 입력한 학생 정보 저장"""
        success_count = 0
        error_count = 0
        
        # 텍스트 영역의 내용을 가져옴
        text = text_area.toPlainText()
        print(f"입력된 텍스트: {text}")  # 디버그 메시지
        
        # 줄 단위로 분리
        lines = text.strip().split('\n')
        print(f"분리된 줄 수: {len(lines)}")  # 디버그 메시지
        
        for line in lines:
            line = line.strip()
            print(f"처리 중인 줄: {line}")  # 디버그 메시지
            
            if not line:  # 빈 줄 무시
                continue
                
            try:
                # 쉼표로 구분된 값들을 분리
                values = [v.strip() for v in line.split(',')]
                print(f"분리된 값들: {values}")  # 디버그 메시지
                
                # 필수 값이 7개인지 확인
                if len(values) != 7:
                    print(f"잘못된 형식 (필드 수: {len(values)}): {line}")
                    error_count += 1
                    continue
                
                school_name, grade, class_num, number, name, gender, eyestright = values
                print(f"파싱된 값들: 학교={school_name}, 학년={grade}, 반={class_num}, 번호={number}, 이름={name}, 성별={gender}, 시력={eyestright}")  # 디버그 메시지
                
                # 숫자 형식 검증
                try:
                    grade = int(grade)
                    class_num = int(class_num)
                    number = int(number)
                except ValueError as e:
                    print(f"숫자 형식 오류: {str(e)}")
                    error_count += 1
                    continue
                
                # 성별 검증
                if gender not in ['남', '여']:
                    print(f"잘못된 성별: {gender}")
                    error_count += 1
                    continue
                
                # 시력 검증 (공백 제거)
                eyestright = eyestright.strip()
                if eyestright not in ['정상', '이상']:
                    print(f"잘못된 시력: {eyestright}")
                    error_count += 1
                    continue
                
                # DB에 저장 (시력은 문자열 그대로 저장)
                try:
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO students 
                        (school_name, grade, class_num, student_number, name, gender, eyestright)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (school_name, grade, class_num, number, name, gender, eyestright))
                    print(f"DB 저장 성공: {name}")  # 디버그 메시지
                    success_count += 1
                except Exception as e:
                    print(f"DB 저장 실패: {str(e)}")  # 디버그 메시지
                    error_count += 1
                    continue
                
            except Exception as e:
                print(f"처리 중 오류 발생: {str(e)}")
                error_count += 1
                continue
        
        # 변경사항 저장
        try:
            self.conn.commit()
            print("DB 커밋 성공")  # 디버그 메시지
        except Exception as e:
            print(f"DB 커밋 실패: {str(e)}")  # 디버그 메시지
        
        print(f"저장 결과: 성공={success_count}, 실패={error_count}")  # 디버그 메시지
        return success_count, error_count

    def on_reset_data_click(self):
        """데이터 초기화"""
        # 첫 번째 확인 창
        reply = QMessageBox.question(self, "확인", 
                                   "모든 학생정보가 초기화됩니다.\n정말로 수행하시겠습니까?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            return
            
        # 두 번째 선택 창
        dialog = QDialog(self)
        dialog.setWindowTitle("초기화 방식 선택")
        dialog.setFixedSize(300, 150)
        
        layout = QVBoxLayout(dialog)
        
        # 라디오 버튼 그룹
        button_group = QButtonGroup(dialog)
        
        rb_delete = QRadioButton("모든 데이터를 삭제")
        rb_delete.setChecked(True)
        button_group.addButton(rb_delete, 1)
        layout.addWidget(rb_delete)
        
        rb_new = QRadioButton("새학년 등록")
        button_group.addButton(rb_new, 2)
        layout.addWidget(rb_new)
        
        # 확인 버튼
        confirm_button = QPushButton("확인")
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        def handle_selection():
            try:
                if rb_delete.isChecked():
                    # 모든 데이터 삭제
                    self.cursor.execute("DELETE FROM students")
                    self.cursor.execute("DELETE FROM last_layout")
                    self.cursor.execute("DELETE FROM seat_history")
                    self.cursor.execute("DELETE FROM school_info")
                    self.cursor.execute("DELETE FROM settings")
                    self.conn.commit()
                    
                    # 메모리 데이터 초기화
                    self.male_students = []
                    self.female_students = []
                    self.all_students = []
                    self.current_layout = []
                    self.student_seat_history = defaultdict(list)
                    self.fixed_seats = {}  # 딕셔너리로 변경: {(row, col): student_name}
                    self.fixed_counts = dict()
                    
                    # UI 초기화
                    self.reset_seat_frame()
                    
                    QMessageBox.information(self, "완료", "모든 데이터가 삭제되었습니다.")
                    self.close()  # 프로그램 종료
                    
                else:  # 새학년 등록
                    dialog.accept()
                    if self.ask_school_info():
                        # 메모리 데이터 초기화
                        self.male_students = []
                        self.female_students = []
                        self.all_students = []
                        self.current_layout = []
                        self.student_seat_history = defaultdict(list)
                        self.fixed_seats = {}  # 딕셔너리로 변경: {(row, col): student_name}
                        self.fixed_counts = dict()
                        
                        # UI 초기화
                        self.reset_seat_frame()
                        
                        QMessageBox.information(self, "완료", "새로운 학년 정보가 등록되었습니다.")
                
            except Exception as e:
                print(f"초기화 중 오류 발생: {str(e)}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "오류", f"초기화 중 오류가 발생했습니다: {str(e)}")
        
        confirm_button.clicked.connect(handle_selection)
        layout.addWidget(confirm_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        dialog.exec()

    def on_view_db_click(self):
        """데이터베이스 내용을 보여주는 메서드"""
        if not self.school_info['school_name']:
            QMessageBox.warning(self, "오류", "먼저 학교 정보를 등록하세요")
            return
            
        self.show_students()

    def load_from_excel(self):
        """엑셀 파일에서 학생 정보 로드"""
        try:
            # 파일 선택 다이얼로그
            file_path, _ = QFileDialog.getOpenFileName(
                self, "엑셀 파일 선택", "", "Excel Files (*.xlsx *.xls)"
            )
            
            if not file_path:
                return
                
            # 엑셀 파일 읽기
            df = pd.read_excel(file_path)
            
            # 필수 컬럼 확인
            required_columns = ['학교', '학년', '반', '번호', '이름', '성별', '시력']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                QMessageBox.critical(self, "오류", f"다음 컬럼이 없습니다: {', '.join(missing_columns)}")
                return
            
            # 데이터 검증 및 변환
            success_count = 0
            error_count = 0
            
            for _, row in df.iterrows():
                try:
                    # 기본 정보 추출
                    school_name = str(row['학교']).strip()
                    grade = int(row['학년'])
                    class_num = int(row['반'])
                    number = int(row['번호'])
                    name = str(row['이름']).strip()
                    gender = str(row['성별']).strip()
                    eyestright = str(row['시력']).strip()
                    
                    # 성별 검증
                    if gender not in ['남', '여']:
                        print(f"잘못된 성별: {gender}")
                        error_count += 1
                        continue
                    
                    # 시력 검증 및 변환
                    if eyestright not in ['정상', '이상']:
                        print(f"잘못된 시력: {eyestright}")
                        error_count += 1
                        continue
                    
                    # 시력 값을 숫자로 변환 (정상=0, 이상=1)
                    eyestright_value = 0 if eyestright == '정상' else 1
                    
                    # DB에 저장 (성별은 그대로 '남'/'여'로 저장)
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO students 
                        (school_name, grade, class_num, student_number, name, gender, eyestright)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (school_name, grade, class_num, number, name, gender, eyestright_value))
                    
                    success_count += 1
                    
                except Exception as e:
                    print(f"행 처리 중 오류 발생: {str(e)}")
                    error_count += 1
                    continue
            
            # 변경사항 저장
            self.conn.commit()
            
            # 결과 메시지
            if success_count > 0:
                QMessageBox.information(self, "완료", 
                    f"학생 정보가 저장되었습니다.\n성공: {success_count}명\n실패: {error_count}명")
                
                # 학생 데이터 다시 로드
                self.load_student_data()
                
                # 현재 레이아웃이 있다면 업데이트
                if hasattr(self, 'current_layout') and self.current_layout:
                    self.draw_seats(self.num_columns)
            else:
                QMessageBox.warning(self, "경고", "저장된 학생 정보가 없습니다.")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 파일 처리 중 오류가 발생했습니다: {str(e)}")

    def create_desk_image(self, path):
        """책상 이미지 생성"""
        try:
            # 이미지 생성
            image = QImage(120, 80, QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)

            # QPainter 생성
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 펜 설정 (매우 진한 검은색)
            pen = QPen()
            pen.setColor(Qt.GlobalColor.black)  # 순수 검은색 사용
            pen.setWidth(4)  # 선 두께 증가
            pen.setStyle(Qt.PenStyle.SolidLine)  # 실선으로 설정
            painter.setPen(pen)

            # 책상 본체 (직사각형)
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawRect(10, 10, 100, 60)

            painter.end()

            # 이미지 저장
            image.save(path)
            
        except Exception as e:
            print(f"의자 이미지 생성 중 오류: {str(e)}")

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                elif item.layout():
                    self.clear_layout(item.layout())
            # QWidget에서 레이아웃을 분리하려면, 임시 위젯을 만들어서 setLayout 해주면 안전하게 분리됨
            QWidget().setLayout(layout)

    def reset_seat_frame(self):
        # 기존 seat_frame 제거
        if hasattr(self, 'seat_frame') and self.seat_frame is not None:
            # 기존 라벨들 정리
            if hasattr(self, 'seat_labels'):
                for label in self.seat_labels.values():
                    if label is not None:
                        label.deleteLater()
                self.seat_labels.clear()
            
            # 급훈 관련 위젯 정리
            if hasattr(self, 'motto_label') and self.motto_label is not None:
                self.motto_label.deleteLater()
            if hasattr(self, 'motto_frame') and self.motto_frame is not None:
                self.motto_frame.deleteLater()
            
            self.main_layout.removeWidget(self.seat_frame)
            self.seat_frame.deleteLater()
        
        # 새 seat_frame 생성
        self.seat_frame = SeatFrame()
        self.seat_frame.setMinimumSize(600, 400)
        
        # 배경 이미지를 위한 레이블 생성
        self.bg_label = QLabel(self.seat_frame)
        self.bg_label.setStyleSheet("border: none;")
        self.set_background_image()
        
        # 급훈 프레임 초기화
        self.motto_frame = QFrame(self.seat_frame)
        self.motto_frame.setGeometry(1072, 57, 72, 50)  # 위치와 크기 조정
        self.motto_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        
        # 급훈 라벨 초기화
        self.motto_label = QLabel(self.motto_frame)
        self.motto_label.setGeometry(2, 2, 68, 46)  # 크기 조정
        self.motto_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.motto_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 12pt;
                font-weight: bold;
                backgrou학d-color: transparent;
            }
        """)
        
        # seat_frame의 resizeEvent 오버라이드
        original_resize_event = self.seat_frame.resizeEvent
        def new_resize_event(event):
            self.set_background_image()
            # 급훈 프레임 위치 조정
            if hasattr(self, 'motto_frame'):
                self.motto_frame.setGeometry(1072, 57, 72, 50)
            if original_resize_event:
                original_resize_event(event)
        self.seat_frame.resizeEvent = new_resize_event
        
        self.main_layout.insertWidget(0, self.seat_frame)
        self.add_seat_frame_buttons()

    def add_seat_frame_buttons(self):
        # 모든 버튼 제거 (아무것도 추가하지 않음)
        self.seat_frame_buttons = []

    def draw_seats(self, num_columns):
        """자리 배치 그리기"""
        try:
            print("\n=== 자리 배치 그리기 시작 ===")
            print(f"현재 레이아웃: {self.current_layout}")
            
            # 기존 자리 레이블 제거
            if hasattr(self, 'seat_labels'):
                for label in self.seat_labels.values():
                    if label is not None:
                        label.deleteLater()
                self.seat_labels.clear()
            
            # 좌석 영역 정의
            seat_area = (134, 1110, 163, 638)  # (x1, x2, y1, y2)
            area_width = seat_area[1] - seat_area[0]
            area_height = seat_area[3] - seat_area[2]
            
            # 자리 크기와 간격
            seat_width = 90
            seat_height = 50
            max_col_gap = 20
            min_col_gap = 5
            group_gap = 60 if getattr(self, 'layout_mode', '열') == '분단' else 0
            num_groups = (num_columns + 1) // 2 if getattr(self, 'layout_mode', '열') == '분단' else 0
            available_width = area_width - (group_gap * (num_groups - 1))
            
            # 열 간격 계산
            col_gap = min(max_col_gap, 
                         max(min_col_gap, 
                             (available_width - (seat_width * num_columns)) // (num_columns - 1))) if num_columns > 1 else 0
            
            row_gap = 10  # 행 간격은 고정

            # 분단 모드일 때 열별 x좌표 미리 계산
            col_x_offsets = []
            if getattr(self, 'layout_mode', '열') == '분단':
                for col in range(1, num_columns + 1):
                    group_idx = (col - 1) // 2
                    in_group_idx = (col - 1) % 2
                    x_offset = group_idx * group_gap + (col - 1) * (seat_width + col_gap)
                    col_x_offsets.append(x_offset)
            else:
                for col in range(1, num_columns + 1):
                    col_x_offsets.append((col - 1) * (seat_width + col_gap))

            # 좌석 영역의 시작점 (중앙 정렬)
            total_width = col_x_offsets[-1] + seat_width
            start_x = seat_area[0] + (area_width - total_width) // 2

            # 행 수 계산
            num_rows = max(seat['row'] for seat in self.current_layout) if self.current_layout else 0
            total_height = (num_rows * seat_height) + ((num_rows - 1) * row_gap)
            
            # 수직 중앙 정렬을 위한 시작 y좌표 계산
            start_y = seat_area[2] + (area_height - total_height) // 2

            print(f"자리 배치 정보:")
            print(f"- 자리 크기: {seat_width}x{seat_height}")
            print(f"- 간격: 열={col_gap}, 행={row_gap}, 분단={group_gap if getattr(self, 'layout_mode', '열') == '분단' else 0}")
            print(f"- 시작 위치: ({start_x}, {start_y})")
            print(f"- 전체 너비: {total_width}")
            print(f"- 전체 높이: {total_height}")
            print(f"- 사용 가능한 너비: {available_width}")
            print(f"- 사용 가능한 높이: {area_height}")

            # 모든 가능한 좌석 위치에 대해 자리 생성
            for row in range(1, num_rows + 1):
                for col in range(1, num_columns + 1):
                    x = start_x + col_x_offsets[col - 1]
                    y = start_y + (row - 1) * (seat_height + row_gap)
                    
                    # 현재 좌표에 해당하는 자리 정보 찾기
                    seat = next((s for s in self.current_layout if s['row'] == row and s['col'] == col), None)
                    
                    # 자리 레이블 생성
                    seat_label = QLabel(self.seat_frame)
                    seat_label.setGeometry(x, y, seat_width, seat_height)
                    
                    # row와 col 속성 추가
                    seat_label.row = row
                    seat_label.col = col
                    
                    # 자리 스타일 설정
                    if (row, col) in self.fixed_seats:
                        seat_label.setStyleSheet("background-color: yellow; border: 2px solid #f90; font-size: 16pt; font-weight: 900; min-width: 60px; min-height: 40px; max-width: 90px; max-height: 50px; font-family: 'RIX모던고딕B';")
                    else:
                        # 여학생인 경우 항상 파란색으로 표시
                        if seat and seat.get('gender') == 'female':
                            seat_label.setStyleSheet("background-color: white; border: 1px solid #888; color: blue; font-size: 16pt; font-weight: 900; min-width: 60px; min-height: 40px; max-width: 90px; max-height: 50px; font-family: 'RIX모던고딕B';")
                        else:
                            seat_label.setStyleSheet("background-color: white; border: 1px solid #888; font-size: 16pt; font-weight: 900; min-width: 60px; min-height: 40px; max-width: 90px; max-height: 50px; font-family: 'RIX모던고딕B';")
                    
                    # 자리 내용 설정
                    if seat and seat['name']:
                        seat_label.setText(seat['name'])
                    else:
                        seat_label.setText("")  # 빈자리도 표시
                    
                    seat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # 자리 레이블 저장
                    self.seat_labels[(row, col)] = seat_label
                    seat_label.show()

            # 급훈 표시
            motto = self.settings.get('motto', '')
            if motto and hasattr(self, 'motto_label'):
                self.motto_label.setText(motto)
                self.motto_label.setStyleSheet("""
                    QLabel {
                        color: #333;
                        font-size: 12pt;
                        font-weight: bold;
                        background-color: transparent;
                        font-family: '궁서체';
                    }
                """)
                self.motto_label.show()
            
            print(f"4. 배치된 학생 수: {sum(1 for seat in self.current_layout if seat['name'])}")
            
            # 창 제목 업데이트 추가
            self.update_window_title()
            
        except Exception as e:
            print(f"자리 배치 그리기 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

    def shake_seats(self):
        """자리 흔들기 애니메이션"""
        try:
            print("\n=== 자리 흔들기 시작 ===")
            print(f"고정된 좌석: {self.fixed_seats}")
            
            # 현재 레이아웃의 좌석 정보 저장
            current_seats = []
            for seat in self.current_layout:
                if seat['name']:  # 학생이 배치된 좌석만 저장
                    current_seats.append({
                        'row': seat['row'],
                        'col': seat['col'],
                        'name': seat['name'],
                        'gender': seat['gender'],
                        'eyestright': seat['eyestright']
                    })
            
            # 고정 좌석 정보 저장
            fixed_seats_info = {}
            for (row, col), student_name in self.fixed_seats.items():
                seat = next((s for s in current_seats if s['row'] == row and s['col'] == col and s['name'] == student_name), None)
                if seat:
                    fixed_seats_info[(row, col)] = seat.copy()
            
            # 고정 좌석을 제외한 나머지 좌석만 섞기
            movable_seats = []
            for seat in current_seats:
                if (seat['row'], seat['col']) not in self.fixed_seats:
                    movable_seats.append(seat.copy())
            random.shuffle(movable_seats)
            
            # 새로운 레이아웃 생성
            new_layout = []
            movable_index = 0
            
            for row in range(1, self.num_rows + 1):
                for col in range(1, self.num_columns + 1):
                    if (row, col) in self.fixed_seats:
                        # 고정 좌석은 원래 정보 그대로 사용
                        new_layout.append(fixed_seats_info[(row, col)])
                    else:
                        # 이동 가능한 좌석은 섞인 순서대로 배치
                        if movable_index < len(movable_seats):
                            seat = movable_seats[movable_index]
                            new_layout.append({
                                'row': row,
                                'col': col,
                                'name': seat['name'],
                                'gender': seat['gender'],
                                'eyestright': seat['eyestright']
                            })
                            movable_index += 1
                        else:
                            new_layout.append({
                                'row': row,
                                'col': col,
                                'name': '',
                                'gender': '',
                                'eyestright': ''
                            })
            
            # 현재 레이아웃 업데이트
            self.current_layout = new_layout
            
            # 자리 배치 그리기
            self.draw_seats(self.num_columns)
            
            print(f"자리 흔들기 완료 - 고정 좌석: {self.fixed_seats}")
            
        except Exception as e:
            print(f"자리 흔들기 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

    def generate_layout(self, num_columns):
        """자리 배치 생성"""
        try:
            print("\n=== 자리 배치 생성 시작 ===")
            print(f"열 수: {num_columns}")
            
            # 학생 데이터 로드
            self.cursor.execute('''SELECT name, gender, eyestright FROM students 
                                WHERE school_name=? AND grade=? AND class_num=?
                                ORDER BY name''',
                                (self.school_info['school_name'],
                                self.school_info['grade'],
                                self.school_info['class_num']))
            students = self.cursor.fetchall()
            
            if not students:
                print("학생 데이터가 없습니다.")
                return []
            
            print(f"전체 학생 수: {len(students)}")
            
            # 설정 로드
            self.cursor.execute('''SELECT separate_gender, prevent_same_seat, prevent_same_seat_count 
                                FROM settings 
                                WHERE school_name=? AND grade=? AND class_num=?''',
                                (self.school_info['school_name'],
                                self.school_info['grade'],
                                self.school_info['class_num']))
            settings = self.cursor.fetchone()
            
            separate_gender = settings[0] if settings else False
            prevent_same_seat = settings[1] if settings else False
            prevent_same_seat_count = settings[2] if settings else 3
            
            print(f"남여구분: {separate_gender}")
            print(f"동일자리 금지: {prevent_same_seat}")
            print(f"동일자리 금지 횟수: {prevent_same_seat_count}")
            
            # 학생별 최근 자리 이력 로드
            student_history = {}
            if prevent_same_seat:
                for student in students:
                    self.cursor.execute('''SELECT row, col FROM seat_history 
                                        WHERE school_name=? AND grade=? AND class_num=? AND name=?
                                        ORDER BY created_at DESC LIMIT ?''',
                                        (self.school_info['school_name'],
                                        self.school_info['grade'],
                                        self.school_info['class_num'],
                                        student[0],
                                        prevent_same_seat_count))
                    history = self.cursor.fetchall()
                    student_history[student[0]] = [(h[0], h[1]) for h in history]
                    print(f"{student[0]}의 최근 자리 이력: {student_history[student[0]]}")
            
            # 남녀 학생 분리
            male_students = [s for s in students if s[1] == '남']
            female_students = [s for s in students if s[1] == '여']
            
            print(f"남학생 수: {len(male_students)}")
            print(f"여학생 수: {len(female_students)}")
            
            # 자리 배치 생성
            layout = []
            if separate_gender:
                # 남녀 구분 배치
                total_rows = (len(students) + num_columns - 1) // num_columns
                male_rows = (len(male_students) + num_columns - 1) // num_columns
                
                # 남학생 배치
                for i, student in enumerate(male_students):
                    row = i // num_columns
                    col = i % num_columns
                    if prevent_same_seat and student[0] in student_history:
                        forbidden_seats = student_history[student[0]]
                        while (row, col) in forbidden_seats:
                            row = (row + 1) % total_rows
                            col = (col + 1) % num_columns
                    layout.append({
                        'row': row,
                        'col': col,
                        'name': student[0],
                        'gender': student[1],
                        'eyestright': student[2]
                    })
                
                # 여학생 배치
                for i, student in enumerate(female_students):
                    row = male_rows + (i // num_columns)
                    col = i % num_columns
                    if prevent_same_seat and student[0] in student_history:
                        forbidden_seats = student_history[student[0]]
                        while (row, col) in forbidden_seats:
                            row = (row + 1) % total_rows
                            col = (col + 1) % num_columns
                    layout.append({
                        'row': row,
                        'col': col,
                        'name': student[0],
                        'gender': student[1],
                        'eyestright': student[2]
                    })
            else:
                # 남녀 혼합 배치
                total_rows = (len(students) + num_columns - 1) // num_columns
                for i, student in enumerate(students):
                    row = i // num_columns
                    col = i % num_columns
                    if prevent_same_seat and student[0] in student_history:
                        forbidden_seats = student_history[student[0]]
                        while (row, col) in forbidden_seats:
                            row = (row + 1) % total_rows
                            col = (col + 1) % num_columns
                    layout.append({
                        'row': row,
                        'col': col,
                        'name': student[0],
                        'gender': student[1],
                        'eyestright': student[2]
                    })
            
            print(f"배치된 학생 수: {len(layout)}")
            print("=== 자리 배치 생성 완료 ===\n")
            return layout
            
        except Exception as e:
            print(f"자리 배치 생성 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def set_background_image(self):
        if hasattr(self, 'seat_frame') and hasattr(self, 'bg_label'):
            bg_pixmap = QPixmap('CLASS_MAIN.PNG')
            if not bg_pixmap.isNull():
                w = self.seat_frame.width()
                h = self.seat_frame.height()
                scaled_pixmap = bg_pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                self.bg_label.setPixmap(scaled_pixmap)
                self.bg_label.setGeometry(0, 0, w, h)

    def show_students(self):
        """학생 목록 보기"""
        if not self.all_students:
            QMessageBox.information(self, "알림", "등록된 학생이 없습니다.")
            return
            
        # 옵션 선택 다이얼로그
        dialog = QDialog(self)
        dialog.setWindowTitle("학생 정보 보기")
        dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        # 제목 레이블
        title_label = QLabel("보기 옵션을 선택하세요")
        title_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 라디오 버튼 그룹
        button_group = QButtonGroup(dialog)
        
        rb1 = QRadioButton("학생정보")
        rb1.setStyleSheet("font-size: 11pt;")
        button_group.addButton(rb1, 1)
        layout.addWidget(rb1)
        
        rb2 = QRadioButton("자리배치이력")
        rb2.setStyleSheet("font-size: 11pt;")
        button_group.addButton(rb2, 2)
        layout.addWidget(rb2)
        
        # 기본값 선택
        rb1.setChecked(True)
        
        # 확인 버튼
        confirm_button = QPushButton("확인")
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        def handle_selection():
            if rb1.isChecked():
                self.show_student_info()
            else:
                self.show_seat_history()
            dialog.accept()
            
        confirm_button.clicked.connect(handle_selection)
        layout.addWidget(confirm_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.exec()

    def show_student_info(self):
        """학생 정보 보기"""
        dialog = QDialog(self)
        dialog.setWindowTitle("학생 목록")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # 테이블 위젯 생성
        table = QTableWidget()
        table.setColumnCount(9)  # 전출 버튼을 위한 열 추가
        table.setHorizontalHeaderLabels(["ID", "학교", "학년", "반", "번호", "이름", "성별", "시력", "전출"])
        
        # 정렬 상태를 저장할 변수
        table.sort_order = Qt.SortOrder.AscendingOrder
        
        try:
            # 데이터베이스에서 학생 정보 조회
            self.cursor.execute("""
                SELECT id, school_name, grade, class_num, student_number, name, gender, eyestright
                FROM students 
                WHERE school_name=? AND grade=? AND class_num=?
                ORDER BY name
            """, (self.school_info['school_name'], self.school_info['grade'], self.school_info['class_num']))
            
            rows = self.cursor.fetchall()
            
            # 데이터 추가
            table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                # ID, 학교, 학년, 반, 번호, 이름은 그대로 표시
                for j in range(6):
                    table.setItem(i, j, QTableWidgetItem(str(row[j])))
                
                # 성별 표시 (DB에 저장된 그대로 표시)
                gender_display = row[6] if row[6] in ['남', '여'] else "None"
                table.setItem(i, 6, QTableWidgetItem(gender_display))
                
                # 시력 표시 (문자열 그대로 표시)
                eyestright_display = row[7] if row[7] in ['정상', '이상'] else "None"
                print(f"시력 표시: DB값={row[7]}, 표시값={eyestright_display}")  # 디버그 메시지
                table.setItem(i, 7, QTableWidgetItem(eyestright_display))
                
                # 전출 버튼 추가
                transfer_btn = QPushButton("전출")
                transfer_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ff4444;
                        color: white;
                        border: none;
                        padding: 5px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #cc0000;
                    }
                """)
                
                # 버튼 클릭 이벤트 처리
                def create_click_handler(student_id, student_name):
                    def click_handler():
                        reply = QMessageBox.question(
                            dialog,
                            "전출 확인",
                            f"{student_name} 학생을 전출 처리하시겠습니까?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        )
                        
                        if reply == QMessageBox.StandardButton.Yes:
                            try:
                                # 학생 정보 삭제
                                self.cursor.execute("""
                                    DELETE FROM students 
                                    WHERE id=? AND school_name=? AND grade=? AND class_num=?
                                """, (student_id, self.school_info['school_name'], 
                                     self.school_info['grade'], self.school_info['class_num']))
                                
                                # 자리 배치에서도 삭제
                                self.cursor.execute("""
                                    DELETE FROM last_layout 
                                    WHERE name=? AND school_name=? AND grade=? AND class_num=?
                                """, (student_name, self.school_info['school_name'], 
                                     self.school_info['grade'], self.school_info['class_num']))
                                
                                # 자리 이력에서도 삭제
                                self.cursor.execute("""
                                    DELETE FROM seat_history 
                                    WHERE name=? AND school_name=? AND grade=? AND class_num=?
                                """, (student_name, self.school_info['school_name'], 
                                     self.school_info['grade'], self.school_info['class_num']))
                                
                                self.conn.commit()
                                
                                # 학생 데이터 다시 로드
                                self.load_student_data()
                                
                                # 현재 레이아웃이 있다면 업데이트
                                if self.current_layout:
                                    self.current_layout = [seat for seat in self.current_layout 
                                                         if seat['name'] != student_name]
                                    self.draw_seats(self.num_columns)
                                
                                QMessageBox.information(dialog, "완료", f"{student_name} 학생이 전출 처리되었습니다.")
                                
                                # 테이블 새로고침
                                self.show_student_info()
                                dialog.close()
                                
                            except sqlite3.Error as e:
                                self.conn.rollback()
                                QMessageBox.critical(dialog, "오류", f"전출 처리 중 오류가 발생했습니다: {str(e)}")
                    
                    return click_handler
                
                transfer_btn.clicked.connect(create_click_handler(row[0], row[5]))  # row[0]는 ID, row[5]는 이름
                table.setCellWidget(i, 8, transfer_btn)  # 8번째 열(인덱스 8)에 전출 버튼 추가
            
            # 컬럼 헤더 클릭 이벤트 처리
            def on_header_clicked(column):
                # 정렬 방향 전환
                table.sort_order = Qt.SortOrder.DescendingOrder if table.sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
                
                # 해당 컬럼 기준으로 정렬
                table.sortItems(column, table.sort_order)
                
                # 전출 버튼 컬럼은 정렬하지 않음
                if column == 7:
                    return
                
                # 정렬 방향 표시를 위해 헤더 텍스트 업데이트
                header_text = table.horizontalHeaderItem(column).text()
                if table.sort_order == Qt.SortOrder.AscendingOrder:
                    table.horizontalHeaderItem(column).setText(f"{header_text} ↑")
                else:
                    table.horizontalHeaderItem(column).setText(f"{header_text} ↓")
                
                # 다른 컬럼의 정렬 표시 제거
                for i in range(table.columnCount()):
                    if i != column:
                        text = table.horizontalHeaderItem(i).text()
                        text = text.replace(" ↑", "").replace(" ↓", "")
                        table.horizontalHeaderItem(i).setText(text)
            
            # 헤더 클릭 이벤트 연결
            table.horizontalHeader().sectionClicked.connect(on_header_clicked)
            
            # 컬럼 너비 자동 조정
            table.resizeColumnsToContents()
            
            layout.addWidget(table)
            dialog.setLayout(layout)
            dialog.exec()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "오류", f"데이터베이스 오류: {str(e)}")

    def show_seat_history(self):
        """자리 배치 이력 보기"""
        try:
            # 자리 배치 이력 조회
            self.cursor.execute('''
                SELECT 
                    row, col,
                    GROUP_CONCAT(name || ' (' || strftime('%Y-%m-%d', created_at) || ')') as history
                FROM seat_history
                WHERE school_name = ? AND grade = ? AND class_num = ?
                GROUP BY row, col
                ORDER BY row, col
            ''', (self.school_info['school_name'],
                 self.school_info['grade'],
                 self.school_info['class_num']))
            
            history_data = self.cursor.fetchall()
            
            if not history_data:
                QMessageBox.information(self, "알림", "저장된 자리 배치 이력이 없습니다.")
                return
            
            # 결과를 표시할 다이얼로그 생성
            dialog = QDialog(self)
            dialog.setWindowTitle("자리 배치 이력")
            dialog.setMinimumSize(800, 600)
            
            # 레이아웃 설정
            layout = QVBoxLayout()
            
            # 테이블 위젯 생성
            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["자리", "변경 이력"])
            
            # 데이터 채우기
            table.setRowCount(len(history_data))
            for i, (row, col, history) in enumerate(history_data):
                # 자리 정보 (열행 형식으로 변경)
                seat_item = QTableWidgetItem(f"{col}열 {row}행")
                seat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(i, 0, seat_item)
                
                # 이력 정보
                history_item = QTableWidgetItem(history)
                history_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(i, 1, history_item)
            
            # 컬럼 너비 조정
            table.setColumnWidth(0, 100)
            table.horizontalHeader().setStretchLastSection(True)
            
            # 테이블을 레이아웃에 추가
            layout.addWidget(table)
            
            # 닫기 버튼 추가
            close_button = QPushButton("닫기")
            close_button.clicked.connect(dialog.close)
            layout.addWidget(close_button)
            
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            print(f"자리 배치 이력 조회 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "오류", f"자리 배치 이력 조회 중 오류가 발생했습니다: {str(e)}")

    def load_last_layout(self):
        """마지막으로 저장된 자리 배치 불러오기"""
        if not self.school_info['school_name']:
            print("학교 정보가 없어 자리 배치를 불러올 수 없습니다.")
            return False

        try:
            print("\n=== 자리 배치 로드 시작 ===")
            # 마지막 저장 시간 확인
            self.cursor.execute('''SELECT MAX(created_at) FROM seat_history 
                                WHERE school_name=? AND grade=? AND class_num=?''',
                               (self.school_info['school_name'], self.school_info['grade'], 
                                self.school_info['class_num']))
            last_save_time = self.cursor.fetchone()[0]
            
            if not last_save_time:
                print("저장된 자리 배치가 없습니다.")
                # 빈 레이아웃 생성
                self.current_layout = []
                for row in range(1, 6):  # 기본 5행
                    for col in range(1, self.num_columns + 1):
                        self.current_layout.append({
                            'row': row,
                            'col': col,
                            'name': '',
                            'gender': '',
                            'eyestright': ''
                        })
                self.draw_seats(self.num_columns)
                return False

            print(f"마지막 저장 시간: {last_save_time}")
            # 저장된 자리 배치 불러오기 (마지막 저장 시간 기준)
            self.cursor.execute('''SELECT row, col, name FROM seat_history 
                                WHERE school_name=? AND grade=? AND class_num=? AND created_at=?
                                ORDER BY row, col''',
                               (self.school_info['school_name'], self.school_info['grade'], 
                                self.school_info['class_num'], last_save_time))
            saved_layout = self.cursor.fetchall()
            print(f"저장된 자리 배치 불러옴: {len(saved_layout)}개")

            if not saved_layout:
                print("저장된 자리 배치가 없습니다.")
                # 빈 레이아웃 생성
                self.current_layout = []
                for row in range(1, 6):  # 기본 5행
                    for col in range(1, self.num_columns + 1):
                        self.current_layout.append({
                            'row': row,
                            'col': col,
                            'name': '',
                            'gender': '',
                            'eyestright': ''
                        })
                self.draw_seats(self.num_columns)
                return False

            # 현재 레이아웃 초기화
            self.current_layout = []

            # 저장된 자리 배치 복원
            for row, col, name in saved_layout:
                # 학생 정보 가져오기
                self.cursor.execute('''SELECT gender, eyestright FROM students 
                                    WHERE school_name=? AND grade=? AND class_num=? AND name=?''',
                                   (self.school_info['school_name'], self.school_info['grade'], 
                                    self.school_info['class_num'], name))
                student_info = self.cursor.fetchone()
                
                if student_info:
                    gender, eyestright = student_info
                else:
                    gender, eyestright = '', ''

                self.current_layout.append({
                    'row': row,
                    'col': col,
                    'name': name,
                    'gender': gender,
                    'eyestright': eyestright
                })

            print(f"복원된 자리 배치: {len(self.current_layout)}개")
            # 자리 배치 그리기
            self.draw_seats(self.num_columns)
            return True

        except Exception as e:
            print(f"자리 배치 로드 중 오류 발생: {str(e)}")
            traceback.print_exc()
            # 오류 발생 시 빈 레이아웃 생성
            self.current_layout = []
            for row in range(1, 6):  # 기본 5행
                for col in range(1, self.num_columns + 1):
                    self.current_layout.append({
                        'row': row,
                        'col': col,
                        'name': '',
                        'gender': '',
                        'eyestright': ''
                    })
            self.draw_seats(self.num_columns)
            return False

    def init_ui(self):
        """UI 초기화"""
        # 우측 좌석 영역
        self.seat_frame = SeatFrame()
        self.seat_frame.setMinimumSize(600, 400)  # 최소 크기 설정
        
        # 배경 이미지를 위한 레이블 생성
        self.bg_label = QLabel(self.seat_frame)
        self.bg_label.setStyleSheet("border: none;")
        self.set_background_image()
        
        # 급훈 프레임 초기화
        self.motto_frame = QFrame(self.seat_frame)
        self.motto_frame.setGeometry(1072, 57, 72, 50)  # 위치와 크기 조정
        self.motto_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        
        # 급훈 라벨 초기화
        self.motto_label = QLabel(self.motto_frame)
        self.motto_label.setGeometry(2, 2, 68, 46)  # 크기 조정
        self.motto_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.motto_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 12pt;
                font-weight: bold;
                background-color: transparent;
                font-family: '궁서체';
            }
        """)
        
        # seat_frame의 resizeEvent 오버라이드
        original_resize_event = self.seat_frame.resizeEvent
        def new_resize_event(event):
            self.set_background_image()
            # 급훈 프레임 위치 조정
            if hasattr(self, 'motto_frame'):
                self.motto_frame.setGeometry(1072, 57, 72, 50)
            if original_resize_event:
                original_resize_event(event)
        self.seat_frame.resizeEvent = new_resize_event
        
        # 메인 레이아웃에 좌석 영역 추가
        self.main_layout.addWidget(self.seat_frame)
        self.main_layout.setStretch(1, 1)  # 좌석 영역이 더 많은 공간을 차지하도록 설정

    def load_school_info(self):
        """학교 정보 로드"""
        try:
            self.cursor.execute("SELECT school_name, grade, class_num FROM school_info LIMIT 1")
            result = self.cursor.fetchone()
            
            if not result:  # 데이터가 없으면 새로 입력받기
                return self.ask_school_info()
            
            # 데이터가 있으면 불러오기
            self.school_info = {
                'school_name': result[0],
                'grade': result[1],
                'class_num': result[2]
            }
            self.update_window_title()
            return True
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "오류", f"학교 정보 로드 중 오류가 발생했습니다: {str(e)}")
            return False

    def ask_school_info(self):
        """학교 정보 입력"""
        try:
            dialog = SchoolInfoDialog()
            dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                values = dialog.get_values()
                
                # 기존 데이터 삭제
                self.cursor.execute("DELETE FROM school_info")
                
                # 새 데이터 입력
                self.cursor.execute(
                    "INSERT INTO school_info (school_name, grade, class_num) VALUES (?, ?, ?)",
                    (values['school_name'], values['grade'], values['class_num'])
                )
                self.conn.commit()
                
                self.school_info = values
                self.update_window_title()
                
                QMessageBox.information(self, "완료", "학교 정보가 저장되었습니다.")
                return True
                
            else:  # 사용자가 취소한 경우
                self.close()  # 프로그램 종료
                return False
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "오류", f"저장 중 오류가 발생했습니다: {str(e)}")
            self.close()  # 오류 발생 시 프로그램 종료
            return False

    def update_window_title(self):
        """창 제목 업데이트"""
        # 전체 학생 수 계산
        total_students = len(self.all_students) if hasattr(self, 'all_students') else 0
        
        # 현재 배치된 학생 수 계산
        seated_count = len([s for s in self.current_layout if s.get('name') and s['name'].strip()]) if hasattr(self, 'current_layout') and self.current_layout else 0
        
        # 열 수 정보
        columns_str = f" / {self.num_columns}열"
        
        # 창 제목 업데이트
        self.setWindowTitle(f"{self.school_info['school_name']} {self.school_info['grade']}학년 {self.school_info['class_num']}반 자리 배치 - 총인원: {total_students}명 (배치: {seated_count}명){columns_str}")
        
        # 디버그 메시지
        print(f"전체 학생 수: {total_students}명")
        print(f"배치된 학생 수: {seated_count}명")
        print(f"현재 레이아웃 상태: {self.current_layout}")

    def load_settings(self):
        """설정 정보 로드"""
        if not self.school_info['school_name']:
            print("학교 정보가 없어 설정을 로드할 수 없습니다.")  # 디버그 메시지
            return
            
        print("설정 로드 시작")  # 디버그 메시지
        try:
            # 테이블 구조 확인 및 필요시 재생성
            try:
                self.cursor.execute("SELECT motto, countdown_text, layout_mode, num_columns FROM settings LIMIT 1")
            except sqlite3.OperationalError:
                print("settings 테이블 재생성")  # 디버그 메시지
                self.create_tables()
            
            self.cursor.execute('''SELECT consider_eyesight, separate_gender, prevent_same_seat, 
                                        prevent_same_seat_count, motto, countdown_text,
                                        layout_mode, num_columns
                                FROM settings 
                                WHERE school_name=? AND grade=? AND class_num=?''',
                            (self.school_info['school_name'], self.school_info['grade'], 
                             self.school_info['class_num']))
            
            result = self.cursor.fetchone()
            if result:
                new_settings = {
                    'consider_eyesight': bool(result[0]),
                    'separate_gender': bool(result[1]),
                    'prevent_same_seat': bool(result[2]),
                    'prevent_same_seat_count': result[3],
                    'motto': result[4] if result[4] is not None else '',
                    'countdown_text': result[5] if result[5] is not None else ''
                }
                print(f"DB에서 로드된 설정값: {new_settings}")  # 디버그 메시지
                self.settings = new_settings
                
                # 레이아웃 모드와 열 수 설정
                self.layout_mode = result[6] if result[6] is not None else '열'
                self.num_columns = result[7] if result[7] is not None else 4  # 기본값을 4열로 변경
                print(f"레이아웃 모드: {self.layout_mode}, 열 수: {self.num_columns}")  # 디버그 메시지
                
                print(f"설정값 업데이트 완료: {self.settings}")  # 디버그 메시지
            else:
                # 설정이 없으면 기본값 설정
                self.settings = {
                    'consider_eyesight': False,
                    'separate_gender': True,
                    'prevent_same_seat': False,
                    'prevent_same_seat_count': 3,
                    'motto': '',
                    'countdown_text': ''
                }
                self.layout_mode = '열'
                self.num_columns = 4  # 기본값을 4열로 변경
                print("기본 설정값 사용:", self.settings)  # 디버그 메시지
                
        except sqlite3.Error as e:
            print(f"설정 로드 중 SQLite 오류: {str(e)}")  # 디버그 메시지
            traceback.print_exc()
            # 오류 발생 시 기본값 사용
            self.settings = {
                'consider_eyesight': False,
                'separate_gender': True,
                'prevent_same_seat': False,
                'prevent_same_seat_count': 3,
                'motto': '',
                'countdown_text': ''
            }
            self.layout_mode = '열'
            self.num_columns = 4  # 기본값을 4열로 변경
            print("오류로 인한 기본 설정값 사용:", self.settings)  # 디버그 메시지
        except Exception as e:
            print(f"설정 로드 중 일반 오류: {str(e)}")  # 디버그 메시지
            traceback.print_exc()
            # 오류 발생 시 기본값 사용
            self.settings = {
                'consider_eyesight': False,
                'separate_gender': True,
                'prevent_same_seat': False,
                'prevent_same_seat_count': 3,
                'motto': '',
                'countdown_text': ''
            }
            self.layout_mode = '열'
            self.num_columns = 4  # 기본값을 4열로 변경
            print("오류로 인한 기본 설정값 사용:", self.settings)  # 디버그 메시지

    def load_student_data(self):
        """학생 데이터 로드"""
        if not self.school_info['school_name']:
            print("학교 정보가 없어 학생 데이터를 로드할 수 없습니다.")
            return
            
        print("\n=== 학생 데이터 로드 시작 ===")
        try:
            # 학생 목록 조회
            self.cursor.execute('''SELECT name, gender FROM students 
                                WHERE school_name=? AND grade=? AND class_num=?
                                ORDER BY name''',
                            (self.school_info['school_name'], self.school_info['grade'], 
                             self.school_info['class_num']))
            
            # 학생 목록 초기화
            self.male_students = []
            self.female_students = []
            self.all_students = []
            
            # 학생 데이터 분류
            for row in self.cursor.fetchall():
                name, gender = row
                self.all_students.append(name)
                if gender == 'male':
                    self.male_students.append(name)
                else:
                    self.female_students.append(name)
            
            print(f"로드된 전체 학생 수: {len(self.all_students)}명")
            print(f"남학생: {len(self.male_students)}명, 여학생: {len(self.female_students)}명")
            print(f"전체 학생 목록: {self.all_students}")
            
            # 현재 레이아웃의 학생 수 확인
            if hasattr(self, 'current_layout'):
                current_students = [seat['name'] for seat in self.current_layout if seat['name']]
                print(f"현재 레이아웃의 학생 수: {len(current_students)}명")
                print(f"현재 레이아웃의 학생 목록: {current_students}")
            
            # 창 제목 업데이트
            self.update_window_title()
            
        except sqlite3.Error as e:
            print(f"학생 데이터 로드 중 오류: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "오류", f"학생 데이터 로드 중 오류가 발생했습니다: {str(e)}")

    def save_settings(self):
        """설정 정보 저장"""
        if not self.school_info['school_name']:
            print("학교 정보가 없어 설정을 저장할 수 없습니다.")
            return
            
        try:
            # 기존 설정 삭제
            self.cursor.execute('''DELETE FROM settings 
                                WHERE school_name=? AND grade=? AND class_num=?''',
                               (self.school_info['school_name'], self.school_info['grade'], 
                                self.school_info['class_num']))
            
            # 새 설정 저장
            self.cursor.execute('''INSERT INTO settings 
                                (school_name, grade, class_num, consider_eyesight, separate_gender,
                                prevent_same_seat, prevent_same_seat_count, motto, countdown_text,
                                layout_mode, num_columns)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                               (self.school_info['school_name'], self.school_info['grade'], 
                                self.school_info['class_num'],
                                int(self.settings.get('consider_eyesight', False)),
                                int(self.settings.get('separate_gender', True)),
                                int(self.settings.get('prevent_same_seat', False)),
                                self.settings.get('prevent_same_seat_count', 3),
                                self.settings.get('motto', ''),
                                self.settings.get('countdown_text', ''),
                                getattr(self, 'layout_mode', '열'),
                                getattr(self, 'num_columns', 4)))
            
            # 변경사항 커밋
            self.conn.commit()
            print("설정 저장 완료")
            
        except Exception as e:
            print(f"설정 저장 중 오류 발생: {str(e)}")
            traceback.print_exc()
            self.conn.rollback()
            raise

    def start_effect_sound(self, effect_path):
        """효과음 재생 시작"""
        try:
            # 새로운 효과음용 오디오 출력 설정
            self.effect_audio_output = QAudioOutput()
            self.effect_audio_output.setVolume(1.0)
            
            # 새로운 효과음용 미디어 플레이어 생성
            self.effect_player = QMediaPlayer()
            self.effect_player.setAudioOutput(self.effect_audio_output)
            self.effect_player.setSource(QUrl.fromLocalFile(effect_path))
            self.effect_player.mediaStatusChanged.connect(self.handle_effect_status)
            
            # 자리배치 시작
            self.start_shuffle_animation()
            
            # 효과음 재생
            if self.effect_player and self.effect_player.mediaStatus() != QMediaPlayer.MediaStatus.NoMedia:
                self.effect_player.play()
                print("효과음 재생 시작됨")
            else:
                print("효과음 재생 실패: 미디어 플레이어가 준비되지 않았습니다.")
                self.close_video_and_shuffle()
                
        except Exception as e:
            print(f"효과음 시작 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            self.close_video_and_shuffle()

    def handle_effect_status(self, status):
        """효과음 상태 변경 처리"""
        try:
            print(f"효과음 상태 변경: {status}")
            if status == QMediaPlayer.MediaStatus.EndOfMedia:
                print("효과음 재생 완료")
                # 애니메이션 타이머 중지
                if hasattr(self, 'shuffle_timer'):
                    try:
                        self.shuffle_timer.stop()
                    except RuntimeError:
                        pass
                # 최종 레이아웃 적용
                self.current_layout = self.target_layout
                self.draw_seats(self.num_columns)
                # 모든 효과 제거
                if hasattr(self, 'seat_labels'):
                    for label in self.seat_labels.values():
                        try:
                            label.setGraphicsEffect(None)
                        except RuntimeError:
                            pass
                # 리소스 정리 및 자리 섞기
                QTimer.singleShot(200, self.cleanup_and_shuffle)
        except Exception as e:
            print(f"효과음 상태 처리 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            self.cleanup_and_shuffle()

    def cleanup_effect_resources(self):
        """효과음 관련 리소스 정리"""
        try:
            print("효과음 리소스 정리 시작")
            
            # 효과음 플레이어 정리
            if hasattr(self, 'effect_player'):
                try:
                    if self.effect_player is not None:
                        self.effect_player.stop()
                        self.effect_player.setSource(QUrl())
                        self.effect_player.deleteLater()
                except RuntimeError:
                    pass
                finally:
                    self.effect_player = None
            
            # 효과음 오디오 출력 정리
            if hasattr(self, 'effect_audio_output'):
                try:
                    if self.effect_audio_output is not None:
                        self.effect_audio_output.deleteLater()
                except RuntimeError:
                    pass
                finally:
                    self.effect_audio_output = None
            
            # 미디어 플레이어 정리
            if hasattr(self, 'media_player'):
                try:
                    if self.media_player is not None:
                        self.media_player.stop()
                        self.media_player.setSource(QUrl())
                        self.media_player.deleteLater()
                except RuntimeError:
                    pass
                finally:
                    self.media_player = None
            
            # 오디오 출력 정리
            if hasattr(self, 'audio_output'):
                try:
                    if self.audio_output is not None:
                        self.audio_output.deleteLater()
                except RuntimeError:
                    pass
                finally:
                    self.audio_output = None
            
            # UI 갱신 강제 수행
            QApplication.processEvents()
            
            print("효과음 리소스 정리 완료")
            
        except Exception as e:
            print(f"효과음 리소스 정리 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    try:
        print("프로그램 시작")
        app = QApplication(sys.argv)
        print("QApplication 생성 완료")
        window = SeatChangeApp()  # SeatLayoutApp에서 SeatChangeApp으로 수정
        print("SeatChangeApp 생성 완료")
        window.show()
        print("윈도우 표시 완료")
        sys.exit(app.exec())
    except Exception as e:
        print(f"프로그램 실행 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()