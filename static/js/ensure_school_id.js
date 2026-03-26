/* ensure_school_id.js: schoolInfo.school_id 가 숫자가 아니면 자동 보정 */
(async function(){
  if(typeof window==='undefined') return;
  /* 개발 환경에서는 매번 fresh 테스트를 위해 schoolInfo를 지웁니다 */
  if(['localhost','127.0.0.1'].includes(window.location.hostname)){
    try{
      localStorage.removeItem('schoolInfo');
      delete window.schoolInfo;
      console.log('[dev] localStorage.schoolInfo 초기화 완료');
    }catch(e){
      console.warn('[dev] schoolInfo 초기화 실패', e);
    }
  }
  window.ensureNumericSchoolId = async function(){
    if(!window.schoolInfo || !window.schoolInfo.school_id){
      // localStorage에 schoolInfo가 없으면 supabase에서 첫 학교 자동 세팅
      try{
        const res = await fetch('/api/school_list');
        const list = await res.json();
        if(list && list.length > 0){
          window.schoolInfo = {
            school_id: list[0].school_id,
            school_name: list[0].school_name,
            grade: list[0].grade,
            class_num: list[0].class_num
          };
          localStorage.setItem('schoolInfo', JSON.stringify(window.schoolInfo));
          console.log('[ensureNumericSchoolId] schoolInfo set from supabase:', window.schoolInfo);
        }else{
          console.warn('[ensureNumericSchoolId] no school found in supabase');
        }
      }catch(e){
        console.error('[ensureNumericSchoolId] error', e);
      }
      return;
    }
    if(/^\d+$/.test(String(window.schoolInfo.school_id))) return; // already numeric
    try{
      const res = await fetch('/api/school_list');
      const list = await res.json();
      const normalize = v => String(v).replace(/학년|반|\s/g,'');
      const f = list.find(s =>
        s.school_name === window.schoolInfo.school_name &&
        normalize(s.grade) === normalize(window.schoolInfo.grade) &&
        normalize(s.class_num) === normalize(window.schoolInfo.class_num)
      );
      if(f){
        window.schoolInfo.school_id = f.school_id;
        localStorage.setItem('schoolInfo', JSON.stringify(window.schoolInfo));
        console.log('[ensureNumericSchoolId] school_id fixed to', f.school_id);
      }else{
        console.warn('[ensureNumericSchoolId] matching school not found');
      }
    }catch(e){
      console.error('[ensureNumericSchoolId] error', e);
    }
  };

  // 실행 시도 (지연해서 여러 번 시도)
  let tries = 0;
  const timer = setInterval(() => {
    tries++;
    if(tries>5){ clearInterval(timer); return; }
    if(window.schoolInfo){
      window.ensureNumericSchoolId();
      clearInterval(timer);
    }
    // localStorage에도 없으면 강제 fetch
    if(!window.schoolInfo && tries===1){
      window.ensureNumericSchoolId();
    }
  }, 500);
})(); 