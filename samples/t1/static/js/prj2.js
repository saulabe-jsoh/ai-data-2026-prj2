const canvas = document.getElementById('cameraScreen');
    const ctx = canvas.getContext('2d');

    // 시스템 중심점 (십자선)
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    // 조류(표적) 초기 상태
    let bird = { x: 150, y: 120, targetX: 150, targetY: 120 };
    
    // 제어 상태 변수
    let isTracking = false;
    let pGain = 0.05;
    let noiseLevel = 2;
    let baseAlt = 300;

    // UI 요소 매핑
    const pGainSlider = document.getElementById('pGain');
    const noiseSlider = document.getElementById('noise');
    const baseAltSlider = document.getElementById('baseAlt');
    const btnToggle = document.getElementById('toggleTracking');

    // 슬라이더 변경 이벤트 연동
    pGainSlider.addEventListener('input', (e) => { pGain = parseFloat(e.target.value); document.getElementById('pGainVal').innerText = pGain; });
    noiseSlider.addEventListener('input', (e) => { noiseLevel = parseInt(e.target.value); document.getElementById('noiseVal').innerText = noiseLevel; });
    baseAltSlider.addEventListener('input', (e) => { baseAlt = parseInt(e.target.value); document.getElementById('baseAltVal').innerText = baseAlt; });

    btnToggle.addEventListener('click', () => {
        isTracking = !isTracking;
        btnToggle.innerText = isTracking ? "자동 추적(AVT) 중지" : "자동 추적(AVT) 시작";
        btnToggle.style.backgroundColor = isTracking ? "#ef4444" : "#10b981";
    });

    document.getElementById('triggerIntrusion').addEventListener('click', () => {
        bird.x = Math.random() * (canvas.width - 100) + 50;
        bird.y = Math.random() * (canvas.height - 100) + 50;
    });

    canvas.addEventListener('click', (e) => {
        const rect = canvas.getBoundingClientRect();
        bird.x = e.clientX - rect.left;
        bird.y = e.clientY - rect.top;
    });

    // 시뮬레이션 메인 루프
    function simulate() {
        // 1. 바람 및 난기류에 의한 조류의 자율 미세 이동 (노이즈 추가)
        if (noiseLevel > 0) {
            bird.x += (Math.random() - 0.5) * noiseLevel;
            bird.y += (Math.random() - 0.5) * noiseLevel;
        }

        // 2. 파이썬 AVT 제어 계산 루프 (오차 판별 및 서보 모터 이동 보정)
        let errorX = bird.x - centerX;
        let errorY = bird.y - centerY;

        if (isTracking) {
            // 오차값에 이득(Gain)을 곱해 중심방향으로 카메라 프레임을 이동시킴 (상대적으로 표적이 중심으로 들어옴)
            bird.x -= errorX * pGain;
            bird.y -= errorY * pGain;
            document.getElementById('motorStatus').innerText = "보정 구동 중";
            document.getElementById('motorStatus').style.color = "#34d399";
        } else {
            document.getElementById('motorStatus').innerText = "고정(정지)";
            document.getElementById('motorStatus').style.color = "#9ca3af";
        }

        // 실시간 오차 갱신 표시
        document.getElementById('errorX').innerText = Math.round(errorX) + " px";
        document.getElementById('errorY').innerText = Math.round(errorY) + " px";

        // 3. LRF 충족 조건 연산 (오차가 일정 범위 이내로 정렬되었는가?)
        const totalError = Math.sqrt(errorX*errorX + errorY*errorY);
        const lrfStatusEl = document.getElementById('lrfStatus');
        
        if (totalError < 15) { // 오차 반경 15픽셀 이내 진입 시 Lock-on 성공
            lrfStatusEl.innerText = "LOCK-ON (조사)";
            lrfStatusEl.style.color = "#10b981";
            
            // 임의의 카메라 매핑 거리를 물리적 거리 공식으로 투영 계산 (예시 기하학 역산)
            // 정중앙에 가까울수록 레이저의 각도가 정렬되어 정확한 왜곡 없는 거리가 도출된다고 가정
            let calculatedDistance = Math.sqrt(baseAlt*baseAlt + 8000*8000) + (totalError * 2);
            document.getElementById('lrfDist').innerText = Math.round(calculatedDistance) + " m";
            document.getElementById('calcAlt').innerText = Math.round(baseAlt + (errorY * 0.5)) + " m";
        } else {
            lrfStatusEl.innerText = "조준 실패 (오차 과다)";
            lrfStatusEl.style.color = "#ef4444";
            document.getElementById('lrfDist').innerText = "- m";
            document.getElementById('calcAlt').innerText = "- m";
        }

        // 4. 스크린 렌더링 (화면 그리기)
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // 열화상 모드 가상 스캔 가이드 격자선
        ctx.strokeStyle = '#111827';
        ctx.lineWidth = 1;
        for(let i=0; i<canvas.width; i+=40) { ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, canvas.height); ctx.stroke(); }
        for(let j=0; j<canvas.height; j+=40) { ctx.beginPath(); ctx.moveTo(0, j); ctx.lineTo(canvas.width, j); ctx.stroke(); }

        // 중앙 고정 십자선 (카메라 센서 중심선)
        ctx.strokeStyle = isTracking ? '#3b82f6' : '#6b7280';
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(centerX - 30, centerY); ctx.lineTo(centerX + 30, centerY); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(centerX, centerY - 30); ctx.lineTo(centerX, centerY + 30); ctx.stroke();
        // 중앙 타겟팅 원
        ctx.beginPath(); ctx.arc(centerX, centerY, 15, 0, 2 * Math.PI); ctx.stroke();

        // 표적(새 떼) 그리기
        ctx.fillStyle = '#ef4444';
        ctx.beginPath();
        ctx.arc(bird.x, bird.y, 8, 0, 2 * Math.PI);
        ctx.fill();
        // 새 무리 느낌을 주기 위한 가상 보조 점들
        ctx.fillStyle = 'rgba(239, 68, 68, 0.5)';
        ctx.beginPath(); ctx.arc(bird.x - 12, bird.y + 8, 4, 0, 2 * Math.PI); ctx.fill();
        ctx.beginPath(); ctx.arc(bird.x + 15, bird.y - 5, 5, 0, 2 * Math.PI); ctx.fill();

        // 추적선 시각화 (오차가 존재할 때 연결 점선 배치)
        if (totalError > 15) {
            ctx.strokeStyle = 'rgba(239, 68, 68, 0.4)';
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 4]);
            ctx.beginPath(); ctx.moveTo(centerX, centerY); ctx.lineTo(bird.x, bird.y); ctx.stroke();
            ctx.setLineDash([]);
        } else if (isTracking) {
            // Lock-on 시 LRF 레이저 빔 가시화 효과 (중앙에서 타겟으로 초록선 조사)
            ctx.strokeStyle = 'rgba(16, 185, 129, 0.8)';
            ctx.lineWidth = 2;
            ctx.beginPath(); ctx.moveTo(centerX, centerY); ctx.lineTo(bird.x, bird.y); ctx.stroke();
        }

        requestAnimationFrame(simulate);
    }

    // 시뮬레이션 개시
    simulate();