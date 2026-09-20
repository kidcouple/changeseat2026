import json
import os
import random
import unittest
from datetime import datetime

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import (  # noqa: E402
    PairHistory,
    SeatHistory,
    Setting,
    Student,
    app,
    db,
)
from import_recovery_data import transform_layout  # noqa: E402


SCHOOL = "셔플알고리즘테스트학교"
GRADE = 1
CLASS_NUM = 6
DISABLED = ["5-1", "5-6"]


class ShuffleAlgorithmTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.engine.dispose()

    def setUp(self):
        random.seed(20260920)
        with app.app_context():
            db.drop_all()
            db.create_all()
            for number in range(1, 29):
                db.session.add(
                    Student(
                        school_name=SCHOOL,
                        grade=GRADE,
                        class_num=CLASS_NUM,
                        student_number=number,
                        name=f"학생{number:02d}",
                        gender="남" if number % 2 else "여",
                        eyestright="이상" if number <= 4 else "정상",
                        is_transferred=False,
                    )
                )
            db.session.add(
                Setting(
                    school_name=SCHOOL,
                    grade=GRADE,
                    class_num=CLASS_NUM,
                    num_columns=6,
                    use_aisle_gap=True,
                    consider_eyesight=True,
                    separate_gender=False,
                    prevent_same_seat=True,
                    prevent_same_seat_count=5,
                    prevent_same_pair=True,
                    disabled_seats=json.dumps(DISABLED),
                    forced_seats="[]",
                )
            )
            db.session.commit()

    def shuffle(self, forced=None):
        response = self.client.post(
            "/api/shuffle",
            json={
                "school": SCHOOL,
                "grade": GRADE,
                "class_num": CLASS_NUM,
                "num_columns": 6,
                "disabled_seats": DISABLED,
                "forced_seats": forced or [],
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.get_json()["layout"]

    def test_first_candidate_is_random_not_student_number_order(self):
        with app.app_context():
            setting = Setting.query.one()
            setting.consider_eyesight = False
            setting.prevent_same_seat = False
            setting.prevent_same_pair = True
            db.session.commit()

        layouts = [self.shuffle() for _ in range(5)]
        sequences = [
            [
                seat["name"]
                for seat in sorted(layout, key=lambda seat: (seat["row"], seat["col"]))
            ]
            for layout in layouts
        ]
        number_order = [f"학생{number:02d}" for number in range(1, 29)]
        self.assertTrue(all(sequence != number_order for sequence in sequences))
        self.assertEqual(len({tuple(sequence) for sequence in sequences}), 5)

    def test_eyesight_students_only_rotate_in_front_reserved_range(self):
        expected_front_positions = {(1, 1), (1, 2), (1, 3), (1, 4)}
        priority_names = {f"학생{number:02d}" for number in range(1, 5)}
        observed_orders = set()

        for _ in range(10):
            layout = self.shuffle()
            priority_layout = [
                seat for seat in layout if seat["name"] in priority_names
            ]
            self.assertEqual(
                {(seat["row"], seat["col"]) for seat in priority_layout},
                expected_front_positions,
            )
            observed_orders.add(
                tuple(
                    seat["name"]
                    for seat in sorted(
                        priority_layout, key=lambda seat: (seat["row"], seat["col"])
                    )
                )
            )

        self.assertGreater(len(observed_orders), 1)

    def test_recent_seat_and_pair_history_are_avoided(self):
        positions = [
            (row, col)
            for row in range(1, 6)
            for col in range(1, 7)
            if f"{row}-{col}" not in DISABLED
        ]
        previous_layout = [
            {"name": f"학생{index:02d}", "row": row, "col": col}
            for index, (row, col) in enumerate(positions, start=1)
        ]
        previous_positions = {
            seat["name"]: (seat["row"], seat["col"]) for seat in previous_layout
        }
        previous_pairs = set()

        with app.app_context():
            created_at = datetime(2026, 9, 18, 12, 0, 0)
            db.session.add(
                SeatHistory(
                    school_name=SCHOOL,
                    grade=GRADE,
                    class_num=CLASS_NUM,
                    layout_data=json.dumps(previous_layout, ensure_ascii=False),
                    created_at=created_at,
                )
            )
            seat_map = {
                (seat["row"], seat["col"]): seat["name"] for seat in previous_layout
            }
            for row in range(1, 6):
                for first_col in (1, 3, 5):
                    first = seat_map.get((row, first_col))
                    second = seat_map.get((row, first_col + 1))
                    if first and second:
                        previous_pairs.add(frozenset((first, second)))
                        db.session.add(
                            PairHistory(
                                school_name=SCHOOL,
                                grade=GRADE,
                                class_num=CLASS_NUM,
                                name=first,
                                pair_name=second,
                                created_at=created_at,
                            )
                        )
                        db.session.add(
                            PairHistory(
                                school_name=SCHOOL,
                                grade=GRADE,
                                class_num=CLASS_NUM,
                                name=second,
                                pair_name=first,
                                created_at=created_at,
                            )
                        )
            db.session.commit()

        layout = self.shuffle()
        self.assertEqual(
            sum(
                previous_positions[seat["name"]] == (seat["row"], seat["col"])
                for seat in layout
            ),
            0,
        )

        seat_map = {(seat["row"], seat["col"]): seat["name"] for seat in layout}
        current_pairs = {
            frozenset((first, second))
            for row in range(1, 6)
            for first_col in (1, 3, 5)
            if (first := seat_map.get((row, first_col)))
            and (second := seat_map.get((row, first_col + 1)))
        }
        self.assertFalse(previous_pairs & current_pairs)

    def test_forced_seat_is_preserved_without_duplicates(self):
        layout = self.shuffle(
            forced=[{"name": "학생28", "row": 3, "col": 3}]
        )
        names = [seat["name"] for seat in layout]
        self.assertEqual(len(names), 28)
        self.assertEqual(len(set(names)), 28)
        forced = next(seat for seat in layout if seat["name"] == "학생28")
        self.assertEqual((forced["row"], forced["col"]), (3, 3))

    def test_stale_or_invalid_forced_seats_are_ignored(self):
        layout = self.shuffle(
            forced=[
                {"name": "삭제된학생", "row": 2, "col": 2},
                {"name": "학생28", "row": 1, "col": 1},
                {"name": "학생27", "row": 99, "col": 99},
            ]
        )
        names = [seat["name"] for seat in layout]
        self.assertEqual(len(names), 28)
        self.assertEqual(len(set(names)), 28)
        self.assertNotIn("삭제된학생", names)

    def test_gender_separation_minimizes_same_gender_pairs(self):
        with app.app_context():
            setting = Setting.query.one()
            setting.consider_eyesight = False
            setting.prevent_same_seat = False
            setting.prevent_same_pair = False
            setting.separate_gender = True
            db.session.commit()

        layout = self.shuffle()
        seat_map = {(seat["row"], seat["col"]): seat["name"] for seat in layout}
        with app.app_context():
            genders = {
                student.name: student.gender for student in Student.query.all()
            }
        same_gender_pairs = 0
        for row in range(1, 6):
            for first_col in (1, 3, 5):
                first = seat_map.get((row, first_col))
                second = seat_map.get((row, first_col + 1))
                if first and second and genders[first] == genders[second]:
                    same_gender_pairs += 1
        self.assertEqual(same_gender_pairs, 0)

    def test_bulk_registration_updates_instead_of_duplicating(self):
        response = self.client.post(
            "/api/students/bulk",
            json={
                "school_name": SCHOOL,
                "grade": GRADE,
                "class_num": CLASS_NUM,
                "students": [
                    {
                        "student_number": 1,
                        "name": "학생01",
                        "gender": "남",
                        "eyestright": "정상",
                    }
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertEqual(Student.query.count(), 28)
            student = Student.query.filter_by(student_number=1).one()
            self.assertEqual(student.eyestright, "정상")

    def test_invalid_shuffle_request_returns_clear_400(self):
        response = self.client.post(
            "/api/shuffle",
            json={
                "school": SCHOOL,
                "grade": GRADE,
                "class_num": CLASS_NUM,
                "num_columns": 0,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_recovery_layout_flips_original_bottom_desk_to_web_top(self):
        transformed = transform_layout(
            {
                "board_position": "bottom",
                "layout": [
                    {"name": "앞자리", "row": 5, "col": 2},
                    {"name": "뒷자리", "row": 1, "col": 2},
                ],
            }
        )
        by_name = {seat["name"]: seat for seat in transformed}
        self.assertEqual(by_name["앞자리"]["row"], 1)
        self.assertEqual(by_name["뒷자리"]["row"], 5)


if __name__ == "__main__":
    unittest.main()
