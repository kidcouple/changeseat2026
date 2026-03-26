window.saveAllChanges = async function(btn){
    const modal = btn.closest('.modal');
    if(!modal) return;

    if(typeof schoolInfo==='undefined' || !schoolInfo || !schoolInfo.school_name){
        alert('학교 정보가 없습니다. 학교 정보를 먼저 설정해주세요.');
        return;
    }

    // school_id 가 정확한지 항상 검증 (없거나 형식이 이상하거나 다른 학급일 수도 있음)
    const needVerifyId = !schoolInfo.school_id || !/^\d+$/.test(String(schoolInfo.school_id));
    if(needVerifyId){
        try{
            const res = await fetch('/api/school_list');
            const schools = await res.json();
            const normalize = v => String(v).replace(/학년|반|\s/g,'');
            let found = schools.find(s=>
                s.school_name === schoolInfo.school_name &&
                normalize(s.grade) === normalize(schoolInfo.grade) &&
                normalize(s.class_num) === normalize(schoolInfo.class_num)
            );
            if(!found){
                // 학교명만 일치하는 첫 레코드 선택 (학년/반 불일치 허용)
                found = schools.find(s=>s.school_name===schoolInfo.school_name);
            }
            if(!found && schools.length){
                // 최후: 첫 번째 항목이라도 사용
                found = schools[0];
                console.warn('[saveAllChanges] fallback to first school in list', found);
            }
            if(found){
                schoolInfo.school_id = found.school_id;
                localStorage.setItem('schoolInfo', JSON.stringify(schoolInfo));
            }else{
                alert('학교 정보를 확인할 수 없습니다. 다시 선택해주세요.');
                return;
            }
        }catch(e){
            console.error('school_id fetch error',e);
            alert('학교 정보를 확인할 수 없습니다. 네트워크 오류.');
            return;
        }
    }
    // 숫자인 경우에도 현재 학급(학교명+학년+반)과 매칭되는지 확인
    if(!needVerifyId){
        try{
            const res = await fetch('/api/school_list');
            const schools = await res.json();
            const normalize = v=>String(v).replace(/학년|반|\s/g,'');
            const matched = schools.find(s=>
                s.school_id == schoolInfo.school_id &&
                s.school_name === schoolInfo.school_name &&
                normalize(s.grade) === normalize(schoolInfo.grade) &&
                normalize(s.class_num) === normalize(schoolInfo.class_num)
            );
            if(!matched){
                // 현재 id 가 엉뚱한 학급이면 제대로 된 id 를 다시 찾음
                const found = schools.find(s=>
                    s.school_name === schoolInfo.school_name &&
                    normalize(s.grade) === normalize(schoolInfo.grade) &&
                    normalize(s.class_num) === normalize(schoolInfo.class_num)
                );
                if(found){
                    schoolInfo.school_id = found.school_id;
                    localStorage.setItem('schoolInfo', JSON.stringify(schoolInfo));
                    console.log('[saveAllChanges] school_id corrected to', found.school_id);
                }else{
                    console.warn('[saveAllChanges] matching school not found');
                }
            }
        }catch(e){
            console.error('school_id verify error', e);
        }
    }

    const rows = modal.querySelectorAll('tbody tr');
    const updatesArr = [];
    rows.forEach(row => {
        let number = row.id.replace('row-','');
        if (/^\d+$/.test(number)) {
            number = String(parseInt(number, 10));
        }
        const name     = row.querySelector('.stu-name').textContent;
        const gender   = row.querySelector('.stu-gender').textContent;
        const eyesight = row.querySelector('.eye-check').checked ? '이상' : '정상';
        const transfer = row.querySelector('.transfer-check').checked;
        updatesArr.push({ number, name, gender, eyesight, transfer });
    });

    if (updatesArr.length === 0) {
        alert('변경할 항목이 없습니다.');
        return;
    }

    // bulk update API 호출
    fetch('/api/students/bulk_update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            school_name: schoolInfo.school_name,
            grade: schoolInfo.grade,
            class_num: schoolInfo.class_num,
            updates: updatesArr
        })
    })
    .then(response => response.json())
    .then(res => {
        if(res.success){
            alert('변경 사항이 저장되었습니다.');
            // 전출 처리된 학생은 목록에서 제거
            rows.forEach((row, idx) => {
                if (updatesArr[idx].transfer) row.remove();
            });
        }else{
            alert('저장 실패: '+(res.error||'알 수 없음'));
        }
    })
    .catch(err => {
        console.error('일괄 저장 오류:', err);
        alert('저장 중 오류: ' + err.message);
    });
}; 