import requests
import json
import time

BASE_URL = "http://127.0.0.1:8080"
SCHOOL_INFO = {'school': '위례한빛중학교', 'grade': 1, 'class_num': 3}

def test():
    success = 0
    fail = 0
    for i in range(20):
        print(f"Iteration {i}...", end=" ", flush=True)
        r = requests.post(f"{BASE_URL}/api/shuffle", json={
            **SCHOOL_INFO,
            'num_columns': 6,
            'use_aisle_gap': True,
            'consider_eyesight': True,
            'separate_gender': True,
            'prevent_same_seat': True,
            'prevent_same_seat_count': 3
        })
        if r.status_code == 200:
            success += 1
            print("SUCCESS")
            # SAVE to history to increase difficulty
            requests.post(f"{BASE_URL}/api/seat_history", params=SCHOOL_INFO, json=r.json()['layout'])
            time.sleep(0.5)
        else:
            fail += 1
            print(f"FAIL: {r.status_code} - {r.json().get('error', 'Unknown Error')}")
    
    print(f"\nFinal: Success {success}, Fail {fail}")

if __name__ == "__main__":
    test()
