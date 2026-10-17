/"
제공해주신 `LAB_00405f32` 코드 블록은 도로 및 철도 선형 설계 프로그램에서 **특정 선형 구간(예: 곡선부나 완화곡선 시작점 등)의 초기 기준 좌표를 삼각함수 연산으로 산출하고, 다음 단계인 세부 좌표 생성 루프(`LAB_0040609a`)로 진입하기 전 상태를 초기화하는 분기 제어 루틴**입니다.

이 레이블의 핵심 역할을 요약해 드립니다:

1. **기준 좌표 및 각도 계산 (`FUN_00415c2c`, `FUN_00415c47`)**
* 방위각과 거리 변수들을 더하여 기본 각도를 맞춘 뒤, 삼각함수 래퍼 함수들을 호출해 해당 지점의 시점 $X, Y$ 좌표(`_DAT_0079dcf8`, `_DAT_007ad6f8`)를 계산합니다.


2. **반복문을 통한 구간별 데이터 확장**
* `while (local_128 = local_128 + -1, 0 < local_128)` 루프를 통해 구간 내 세부 지점들의 좌표를 연속적으로 계산하여 배열 버퍼(`_DAT_0079dcf0`, `_DAT_007ad6f0` 등)에 차곡차곡 채워 넣습니다.


3. **다음 연산 단계로의 연결 (`goto LAB_0040609a`)**
* 하단의 조건 검사(`FUN_00414280`)를 거쳐, 조건이 충족되면 앞서 보았던 세부 좌표 및 측점 정렬/출력 루틴인 `LAB_0040609a`로 곧바로 제어를 넘겨줍니다.



즉, 이 블록은 **핵심 계산 엔진 내부에서 개별 선형 구간의 시작 좌표를 확정하고, 전체 측점 배열을 채우는 전 단계의 준비 작업을 수행하는 핵심 허브**입니다!
"/

LAB_00405f32:
        _DAT_0079dcf0 = _DAT_0079dc60 + _DAT_0079dce8;
        pcStack_204 = (char *)0x405f49;
        fVar38 = (float10)FUN_00415c2c();
        _DAT_0079dcf8 =
             (double)(fVar38 * (float10)*(double *)(&DAT_00664f00 + local_18 * 8) +
                     (float10)_DAT_0079dc28);
        pcStack_204 = (char *)0x405f6a;
        fVar38 = (float10)FUN_00415c47();
        _DAT_007ad6f8 =
             (double)(fVar38 * (float10)*(double *)(&DAT_00664f00 + local_18 * 8) +
                     (float10)_DAT_0079dc30);
        local_128 = DAT_0079dc98 + 1;
        local_14 = 2;
        while (local_128 = local_128 + -1, 0 < local_128) {
          _DAT_0079dcf0 = _DAT_0079dcf0 + _DAT_0079dc68;
          pcStack_204 = (char *)0x405fe4;
          fVar38 = (float10)FUN_00415c2c();
          *(double *)(&DAT_0079dcf0 + local_14 * 8) =
               (double)(fVar38 * (float10)*(double *)(&DAT_00664f00 + local_18 * 8) +
                       (float10)_DAT_0079dc28);
          pcStack_204 = (char *)0x406009;
          fVar38 = (float10)FUN_00415c47();
          *(double *)(local_14 * 8 + 0x7ad6f0) =
               (double)(fVar38 * (float10)*(double *)(&DAT_00664f00 + local_18 * 8) +
                       (float10)_DAT_0079dc30);
          local_14 = local_14 + 1;
        }
        DAT_007bd0f8 = 1;
        _DAT_007bd100 =
             (double)((float)*(int *)(local_18 * 4 + 0x69403c) * 1000.0 +
                     (float)*(double *)(local_18 * 8 + 0x694048));
        pcStack_204 = (char *)0x1;
        pcStack_208 = &DAT_00439ab8;
        cVar8 = FUN_00414280(&DAT_00645a58,10);
        if (cVar8 == '\0') {
          pcStack_204 = (char *)0x1;
          pcStack_208 = &DAT_00439abc;
          cVar8 = FUN_00414280(&DAT_00645a58,10);
          if (cVar8 != '\0') goto LAB_0040609a;
        }
        else {