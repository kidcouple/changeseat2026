"""자동 배치 옵션 시나리오 검증.

시나리오 5개 x 10회 = 50회. 지정석·강제지정은 다른 옵션보다 우선한다.
실제 /api/shuffle 를 호출하고, 이전처럼 고정 시드만으로 통과시키지 않는다.
"""

import json
import os
import random
from collections import defaultdict
from datetime import datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import PairHistory, SeatHistory, Setting, Student, app, db  # noqa: E402


SCHOOL = "옵션시나리오학교"
GRADE = 1
CLASS_NUM = 6
COLS = 6
ROWS = 5
DISABLED = ["5-1", "5-6"]
TRIALS = 10
EYESIGHT_NAMES = {f"학생{n:02d}" for n in range(1, 5)}
NUMBER_ORDER = [f"학생{n:02d}" for n in range(1, 29)]

POSITIONS = [
    (row, col)
    for row in range(1, ROWS + 1)
    for col in range(1, COLS + 1)
    if f"{row}-{col}" not in DISABLED
]


def student_name(number):
    return f"학생{number:02d}"


def gender_of(name):
    number = int(name.replace("학생", ""))
    return "남" if number % 2 else "여"


def is_eyesight(name):
    return name in EYESIGHT_NAMES


def pairs_of(layout):
    seat_map = {(seat["row"], seat["col"]): seat["name"] for seat in layout}
    pairs = []
    for row in range(1, ROWS + 1):
        for first_col in (1, 3, 5):
            first = seat_map.get((row, first_col))
            second = seat_map.get((row, first_col + 1))
            if first and second:
                pairs.append((first, second))
    return pairs


def sequence_of(layout):
    return [
        seat["name"]
        for seat in sorted(layout, key=lambda seat: (seat["row"], seat["col"]))
    ]


def available_after(forced):
    occupied = {(item["row"], item["col"]) for item in forced}
    return [
        position for position in POSITIONS if position not in occupied
    ]


def reserved_front_for(remaining_eyesight_count, forced, spread_pairs=False):
    available = available_after(forced)
    if remaining_eyesight_count <= 0:
        return set()
    if not spread_pairs:
        return set(available[:remaining_eyesight_count])
    grouped = {}
    for row, col in available:
        grouped.setdefault((row, col if col % 2 == 1 else col - 1), []).append(
            (row, col)
        )
    chosen = []
    for seats in grouped.values():
        if len(chosen) >= remaining_eyesight_count:
            break
        chosen.append(seats[0])
    if len(chosen) < remaining_eyesight_count:
        chosen_set = set(chosen)
        for seats in grouped.values():
            for seat in seats:
                if seat not in chosen_set:
                    chosen.append(seat)
                    if len(chosen) >= remaining_eyesight_count:
                        return set(chosen)
    return set(chosen[:remaining_eyesight_count])


def seed_histories(count=3):
    """학생 i는 최근 count회 동안 서로 다른 자리에 앉았고, 그때의 짝도 기록한다."""
    for offset in range(count):
        created_at = datetime(2026, 9, 1, 12, 0, 0) + timedelta(days=offset)
        layout = []
        for index, (row, col) in enumerate(POSITIONS):
            number = ((index - offset * 3) % 28) + 1
            layout.append(
                {"name": student_name(number), "row": row, "col": col}
            )
        db.session.add(
            SeatHistory(
                school_name=SCHOOL,
                grade=GRADE,
                class_num=CLASS_NUM,
                layout_data=json.dumps(layout, ensure_ascii=False),
                created_at=created_at,
            )
        )
        for first, second in pairs_of(layout):
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


def load_recent_seats(count=3):
    recent = defaultdict(set)
    rows = (
        SeatHistory.query.filter_by(
            school_name=SCHOOL, grade=GRADE, class_num=CLASS_NUM
        )
        .order_by(SeatHistory.created_at.desc())
        .limit(count)
        .all()
    )
    for history in rows:
        for seat in json.loads(history.layout_data):
            recent[seat["name"]].add((seat["row"], seat["col"]))
    return recent


def load_recent_pairs(count=3):
    recent = defaultdict(set)
    names = [student_name(n) for n in range(1, 29)]
    for name in names:
        rows = (
            PairHistory.query.filter_by(
                school_name=SCHOOL,
                grade=GRADE,
                class_num=CLASS_NUM,
                name=name,
            )
            .order_by(PairHistory.created_at.desc())
            .limit(count)
            .all()
        )
        recent[name] = {row.pair_name for row in rows}
    return recent


class ScenarioRunner:
    def __init__(self):
        self.client = app.test_client()
        self.failures = []
        self.passed = 0
        self.total = 0
        self.layout_fingerprints = defaultdict(set)

    def reset_db(self, **setting_flags):
        db.drop_all()
        db.create_all()
        for number in range(1, 29):
            db.session.add(
                Student(
                    school_name=SCHOOL,
                    grade=GRADE,
                    class_num=CLASS_NUM,
                    student_number=number,
                    name=student_name(number),
                    gender=gender_of(student_name(number)),
                    eyestright="이상" if number <= 4 else "정상",
                    is_transferred=False,
                )
            )
        flags = {
            "num_columns": COLS,
            "use_aisle_gap": True,
            "consider_eyesight": False,
            "separate_gender": False,
            "prevent_same_seat": False,
            "prevent_same_seat_count": 3,
            "prevent_same_pair": False,
            "disabled_seats": json.dumps(DISABLED),
            "forced_seats": "[]",
        }
        flags.update(setting_flags)
        db.session.add(
            Setting(school_name=SCHOOL, grade=GRADE, class_num=CLASS_NUM, **flags)
        )
        db.session.commit()

    def shuffle(self, forced=None, designated=None):
        payload = {
            "school": SCHOOL,
            "grade": GRADE,
            "class_num": CLASS_NUM,
            "num_columns": COLS,
            "disabled_seats": DISABLED,
            "designated_seats": designated or [],
            "forced_seats": forced or [],
        }
        response = self.client.post("/api/shuffle", json=payload)
        if response.status_code != 200:
            raise AssertionError(
                f"shuffle HTTP {response.status_code}: {response.get_data(as_text=True)}"
            )
        layout = response.get_json()["layout"]
        names = [seat["name"] for seat in layout]
        if len(names) != 28:
            raise AssertionError(f"배치 인원 {len(names)}명 (기대 28)")
        if len(set(names)) != 28:
            raise AssertionError("학생 중복 배치")
        if sequence_of(layout) == NUMBER_ORDER:
            raise AssertionError("번호 순서대로 배치됨")
        return layout

    def check(self, scenario, trial, condition, message):
        if not condition:
            raise AssertionError(message)

    def run_trial(self, scenario, trial, fn):
        self.total += 1
        try:
            layout = fn()
            self.passed += 1
            self.layout_fingerprints[scenario].add(tuple(sequence_of(layout)))
            print(f"  [{scenario}] {trial:02d}/10 PASS")
        except AssertionError as error:
            self.failures.append((scenario, trial, str(error)))
            print(f"  [{scenario}] {trial:02d}/10 FAIL - {error}")

    def assert_forced(self, layout, forced):
        by_name = {seat["name"]: seat for seat in layout}
        for item in forced:
            seat = by_name.get(item["name"])
            if seat is None:
                raise AssertionError(f"지정/강제 학생 {item['name']} 누락")
            if (seat["row"], seat["col"]) != (item["row"], item["col"]):
                raise AssertionError(
                    f"{item['name']}이 지정 위치 ({item['row']},{item['col']})에 "
                    f"있지 않고 ({seat['row']},{seat['col']})"
                )

    def assert_eyesight(self, layout, forced=None, spread_pairs=False):
        forced = forced or []
        forced_names = {item["name"] for item in forced}
        remaining = [name for name in EYESIGHT_NAMES if name not in forced_names]
        reserved = reserved_front_for(len(remaining), forced, spread_pairs)
        actual = {
            (seat["row"], seat["col"])
            for seat in layout
            if seat["name"] in remaining
        }
        if actual != reserved:
            raise AssertionError(
                f"시력 우선 좌석 불일치 기대={sorted(reserved)} 실제={sorted(actual)}"
            )
        for seat in layout:
            if seat["name"] in forced_names:
                continue
            if (
                not is_eyesight(seat["name"])
                and (seat["row"], seat["col"]) in reserved
            ):
                raise AssertionError(
                    f"시력 정상 {seat['name']}이 앞자리 예약석 "
                    f"({seat['row']},{seat['col']})에 앉음"
                )

    def assert_gender(self, layout, forced=None):
        forced_names = {item["name"] for item in (forced or [])}
        conflicts = []
        for first, second in pairs_of(layout):
            if first in forced_names and second in forced_names:
                continue
            if gender_of(first) == gender_of(second):
                conflicts.append(f"{first}-{second}")
        if conflicts:
            raise AssertionError(f"같은 성별 짝: {', '.join(conflicts)}")

    def assert_same_seat(self, layout, recent, forced=None):
        forced_names = {item["name"] for item in (forced or [])}
        repeats = []
        for seat in layout:
            if seat["name"] in forced_names:
                continue
            if (seat["row"], seat["col"]) in recent.get(seat["name"], set()):
                repeats.append(
                    f"{seat['name']}@({seat['row']},{seat['col']})"
                )
        if repeats:
            raise AssertionError(f"이전 자리 재배치: {', '.join(repeats)}")

    def assert_same_pair(self, layout, recent, forced=None):
        forced_names = {item["name"] for item in (forced or [])}
        repeats = []
        for first, second in pairs_of(layout):
            if first in forced_names and second in forced_names:
                continue
            if second in recent.get(first, set()):
                repeats.append(f"{first}-{second}")
        if repeats:
            raise AssertionError(f"이전 짝 재배치: {', '.join(repeats)}")


def main():
    runner = ScenarioRunner()
    with app.app_context():
        print("=== 시나리오 1. 시력 우선만 ===")
        runner.reset_db(consider_eyesight=True)
        for trial in range(1, TRIALS + 1):
            def body(trial=trial):
                random.seed(71000 + trial * 17)
                layout = runner.shuffle()
                runner.assert_eyesight(layout)
                return layout
            runner.run_trial("시력 우선", trial, body)

        print("=== 시나리오 2. 남여 구분만 ===")
        runner.reset_db(separate_gender=True)
        for trial in range(1, TRIALS + 1):
            def body(trial=trial):
                random.seed(72000 + trial * 19)
                layout = runner.shuffle()
                runner.assert_gender(layout)
                return layout
            runner.run_trial("남여 구분", trial, body)

        print("=== 시나리오 3. 이전 자리 방지 최근 3회 ===")
        runner.reset_db(prevent_same_seat=True, prevent_same_seat_count=3)
        seed_histories(3)
        recent_seats = load_recent_seats(3)
        for trial in range(1, TRIALS + 1):
            def body(trial=trial):
                random.seed(73000 + trial * 23)
                layout = runner.shuffle()
                runner.assert_same_seat(layout, recent_seats)
                return layout
            runner.run_trial("이전 자리 방지", trial, body)

        print("=== 시나리오 4. 동일 짝 금지 최근 3회 ===")
        runner.reset_db(prevent_same_pair=True, prevent_same_seat_count=3)
        seed_histories(3)
        recent_pairs = load_recent_pairs(3)
        for trial in range(1, TRIALS + 1):
            def body(trial=trial):
                random.seed(74000 + trial * 29)
                layout = runner.shuffle()
                runner.assert_same_pair(layout, recent_pairs)
                return layout
            runner.run_trial("동일 짝 금지", trial, body)

        print("=== 시나리오 5. 4옵션 전부 + 지정석/강제지정 우선 ===")
        runner.reset_db(
            consider_eyesight=True,
            separate_gender=True,
            prevent_same_seat=True,
            prevent_same_seat_count=3,
            prevent_same_pair=True,
        )
        seed_histories(3)
        recent_seats = load_recent_seats(3)
        recent_pairs = load_recent_pairs(3)
        # 지정석: 시력 정상 여학생을 교탁 앞 (1,1)에 고정
        # 강제지정: 시력 이상 남학생을 맨 뒤 (5,3)에 고정
        # 지정석: 이전 자리인 (2,2)에 학생08 고정 — 이전자리 방지보다 우선
        # 강제지정: 남-남 짝을 (4,1)-(4,2)에 고정 — 남여 구분/동일짝보다 우선
        designated = [
            {"name": "학생28", "row": 1, "col": 1},
            {"name": "학생08", "row": 2, "col": 2},
        ]
        forced = [
            {"name": "학생01", "row": 5, "col": 3},
            {"name": "학생11", "row": 4, "col": 1},
            {"name": "학생13", "row": 4, "col": 2},
            {"name": "학생28", "row": 3, "col": 3},
            {"name": "학생27", "row": 1, "col": 1},
        ]
        locked = designated + [
            {"name": "학생01", "row": 5, "col": 3},
            {"name": "학생11", "row": 4, "col": 1},
            {"name": "학생13", "row": 4, "col": 2},
        ]
        for trial in range(1, TRIALS + 1):
            def body(trial=trial):
                random.seed(75000 + trial * 31)
                layout = runner.shuffle(forced=forced, designated=designated)
                runner.assert_forced(layout, locked)
                runner.assert_eyesight(layout, locked, spread_pairs=True)
                runner.assert_gender(layout, locked)
                runner.assert_same_seat(layout, recent_seats, locked)
                runner.assert_same_pair(layout, recent_pairs, locked)
                by_name = {seat["name"]: seat for seat in layout}
                if (by_name["학생28"]["row"], by_name["학생28"]["col"]) != (1, 1):
                    raise AssertionError("지정석이 강제지정에 밀림")
                if (by_name["학생27"]["row"], by_name["학생27"]["col"]) == (1, 1):
                    raise AssertionError("강제지정이 지정석 자리를 차지함")
                if (by_name["학생01"]["row"], by_name["학생01"]["col"]) == (1, 1):
                    raise AssertionError("강제지정 시력 학생이 앞자리로 되돌아감")
                return layout
            runner.run_trial("지정석/강제 + 4옵션", trial, body)

    print("\n======== 결과 ========")
    print(f"총 {runner.total}회 중 PASS {runner.passed}, FAIL {len(runner.failures)}")
    for scenario, fingerprints in runner.layout_fingerprints.items():
        print(f"  {scenario}: 서로 다른 배치 {len(fingerprints)}개")
    if runner.failures:
        print("\n실패 상세:")
        for scenario, trial, message in runner.failures:
            print(f"  - {scenario} #{trial}: {message}")
        raise SystemExit(1)
    print("50회 모두 통과")


if __name__ == "__main__":
    main()
