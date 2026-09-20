import glob
import json
import os
from datetime import datetime

from app import (
    PairHistory,
    SeatHistory,
    Setting,
    Student,
    app,
    db,
    parse_layout,
    utc_now,
)


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "업데이트해야함")
SCHOOL_NAME = os.environ.get("RECOVERY_SCHOOL_NAME", "위례중앙중학교").strip()
GRADE = int(os.environ.get("RECOVERY_GRADE", "1"))
CLASS_NUM = int(os.environ.get("RECOVERY_CLASS_NUM", "6"))


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def import_students():
    global SCHOOL_NAME, GRADE, CLASS_NUM
    roster_path = os.path.join(DATA_DIR, "1-6반 명렬표.json")
    roster = load_json(roster_path)
    SCHOOL_NAME = os.environ.get("RECOVERY_SCHOOL_NAME", roster.get("school_name") or SCHOOL_NAME).strip()
    GRADE = int(os.environ.get("RECOVERY_GRADE", roster.get("school_year") or GRADE))
    CLASS_NUM = int(os.environ.get("RECOVERY_CLASS_NUM", roster.get("class_num") or CLASS_NUM))
    imported = 0

    for item in roster["students"]:
        if item["status"] != "active" or not item.get("name"):
            continue

        student = Student.query.filter_by(
            school_name=SCHOOL_NAME,
            grade=GRADE,
            class_num=CLASS_NUM,
            student_number=item["number"],
        ).first()
        if not student:
            student = Student(
                school_name=SCHOOL_NAME,
                grade=GRADE,
                class_num=CLASS_NUM,
                student_number=item["number"],
                is_transferred=False,
            )
            db.session.add(student)
        student.name = item["name"]
        student.gender = item["gender"]
        student.eyestright = item.get("eyestright") or item.get("eyesight") or student.eyestright or "정상"
        student.is_transferred = False
        imported += 1

    return imported


def ensure_settings():
    setting = Setting.query.filter_by(
        school_name=SCHOOL_NAME, grade=GRADE, class_num=CLASS_NUM
    ).first()
    if not setting:
        setting = Setting(
            school_name=SCHOOL_NAME,
            grade=GRADE,
            class_num=CLASS_NUM,
            num_columns=6,
            use_aisle_gap=True,
            consider_eyesight=True,
            separate_gender=True,
            prevent_same_seat=True,
            prevent_same_seat_count=5,
            prevent_same_pair=True,
            disabled_seats=json.dumps(["5-1", "5-6"], ensure_ascii=False),
            forced_seats="[]",
        )
        db.session.add(setting)
    elif set(parse_layout(setting.disabled_seats)) == {"1-1", "1-6"}:
        # 기존 복구본은 교탁 방향을 반대로 해석해 빈자리를 1행에 저장했다.
        setting.disabled_seats = json.dumps(["5-1", "5-6"], ensure_ascii=False)
    return setting


def transform_layout(source):
    """원본(교탁 아래) 좌표를 웹(교탁 위, 1행이 앞줄) 좌표로 변환."""
    source_layout = source.get("layout", [])
    max_row = max((int(seat["row"]) for seat in source_layout), default=0)
    flip_rows = source.get("board_position") == "bottom"
    return [
        {
            "name": seat["name"],
            "row": max_row + 1 - int(seat["row"]) if flip_rows else int(seat["row"]),
            "col": int(seat["col"]),
        }
        for seat in source_layout
    ]


def import_layouts(active_names=None):
    paths = sorted(glob.glob(os.path.join(DATA_DIR, "1-6반 자리배치도(*).json")))
    imported = 0
    active_names = set(active_names or [])
    if not active_names:
        active_names = {
            student.name
            for student in Student.query.filter_by(
                school_name=SCHOOL_NAME,
                grade=GRADE,
                class_num=CLASS_NUM,
                is_transferred=False,
            ).all()
            if student.name
        }

    for path in paths:
        source = load_json(path)
        start_date = source["period"]["start"]
        created_at = datetime.fromisoformat(f"{start_date}T12:00:00")
        layout = transform_layout(source)
        layout = [seat for seat in layout if seat.get("name") in active_names]

        history = SeatHistory.query.filter_by(
            school_name=SCHOOL_NAME,
            grade=GRADE,
            class_num=CLASS_NUM,
            created_at=created_at,
        ).first()
        if not history:
            history = SeatHistory(
                school_name=SCHOOL_NAME,
                grade=GRADE,
                class_num=CLASS_NUM,
                created_at=created_at,
            )
            db.session.add(history)
        history.layout_data = json.dumps(layout, ensure_ascii=False)

        PairHistory.query.filter_by(
            school_name=SCHOOL_NAME,
            grade=GRADE,
            class_num=CLASS_NUM,
            created_at=created_at,
        ).delete(synchronize_session=False)

        seat_map = {(seat["row"], seat["col"]): seat["name"] for seat in layout}
        for row in range(1, 6):
            for first_col in (1, 3, 5):
                first_name = seat_map.get((row, first_col))
                second_name = seat_map.get((row, first_col + 1))
                if first_name and second_name:
                    db.session.add(
                        PairHistory(
                            school_name=SCHOOL_NAME,
                            grade=GRADE,
                            class_num=CLASS_NUM,
                            name=first_name,
                            pair_name=second_name,
                            created_at=created_at,
                        )
                    )
                    db.session.add(
                        PairHistory(
                            school_name=SCHOOL_NAME,
                            grade=GRADE,
                            class_num=CLASS_NUM,
                            name=second_name,
                            pair_name=first_name,
                            created_at=created_at,
                        )
                    )
        imported += 1

    return imported


def main():
    if not os.path.isdir(DATA_DIR):
        raise RuntimeError(f"복구 데이터 폴더를 찾을 수 없습니다: {DATA_DIR}")

    with app.app_context():
        db.create_all()
        student_count = import_students()
        setting = ensure_settings()
        layout_count = import_layouts()
        setting.last_active_at = utc_now()
        db.session.commit()
        print(
            f"Recovery import complete: {SCHOOL_NAME} "
            f"{GRADE}-{CLASS_NUM}, students={student_count}, layouts={layout_count}"
        )


if __name__ == "__main__":
    main()
