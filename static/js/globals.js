/* 글로벌 함수 정의 (fetchStudents, renderSeats) */
(function() {
    if (typeof window.fetchStudents !== 'function') {
        window.fetchStudents = async function() {
            if (!window.schoolInfo) return [];
            try {
                const query = new URLSearchParams({
                    school_id: window.schoolInfo.school_id || '',
                    school_name: window.schoolInfo.school_name || '',
                    grade: window.schoolInfo.grade || '',
                    class_num: window.schoolInfo.class_num || ''
                }).toString();
                const res = await fetch(`/api/students?${query}`);
                return await res.json();
            } catch(err) {
                console.error('[globals] fetchStudents 오류:', err);
                return [];
            }
        };
    }

    if (typeof window.renderSeats !== 'function') {
        window.renderSeats = function(layout) {
            layout = layout || window.currentLayout;
            if (!layout || !layout.length) return;
            window.currentLayout = layout;
            if (typeof window.drawSeats === 'function') {
                window.drawSeats();
            } else if (typeof window.updateSeatingChart === 'function') {
                window.updateSeatingChart(layout);
            }
        };
    }
})();

// 동적 로드: saveAllChanges 오버라이드 스크립트
(function(){
  const s=document.createElement('script');
  s.src='/static/js/custom.js';
  document.head.appendChild(s);
})();

// 동적 로드: school_id 보정 스크립트
(function(){
  const s=document.createElement('script');
  s.src='/static/js/ensure_school_id.js';
  document.head.appendChild(s);
})(); 