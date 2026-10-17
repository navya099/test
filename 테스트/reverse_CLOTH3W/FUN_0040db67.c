/"
제공해주신 `FUN_0040db67` 함수의 디컴파일 코드는 이 프로그램의 진정한 핵심인 **토목 선형의 측점별(예: 20m 간격) 좌표 계산 및 CAD(DXF) 도면 요소 드로잉 엔진**입니다.

코드 내부에서 최대 1,000,000번 반복되는 루프와 `LINE`, `CIRCLE` 같은 DXF 프리미티브 문자열들이 등장하는 것으로 보아, 사용자가 지정한 구간 동안 측점을 전진시키며 기하학적 좌표를 구하고 이를 도면에 즉시 렌더링하는 역할을 수행합니다.

---

### ⚙️ 코드 동작 흐름 및 주요 기능 분석

1. **초기 헤더 및 축 초기화**
* 함수 시작부에서 `FUN_00412670`을 통해 DXF 파일에 `LINE` 엔티티를 그리기 위한 초기 헤더 및 좌표 세팅을 수행합니다.
* 각종 전역 변수(`_DAT_00826ce0`, `_DAT_00826cf0` 등)에 초기 위치 값들을 바인딩합니다.


2. **20미터 측점 간격 반복 루프 (`for` 루프)**
* `for (local_14 = 10000000; ...)` 구문은 아주 긴 선형 구간을 커버하기 위한 대형 반복문입니다.
* 내부에서 `_DAT_00826ce0 = _DAT_00826ce0 + 20.0;`과 같이 20 단위(토목 설계에서 흔히 쓰이는 20m 풀 스테이션 간격)씩 값을 증가시키며 구간 내 좌표를 연속적으로 산출합니다.


3. **삼각함수 기반 좌표 계산 (`FUN_00415c2c`, `FUN_00415c47` 등)**
* 이름 없는 내부 함수 래퍼들(`FUN_00415c2c`, `FUN_00415c47`, `FUN_00415d3d` 등)은 방위각과 거리를 인자로 받아 **삼각함수(`sin`, `cos`) 연산을 수행하여 실제 $X, Y$ 좌표를 뽑아내는 수학적 핵심 코어**입니다.
* 계산된 좌표를 바탕으로 중심선(`CENTER`), 내부선(`INSIDE`), 체인선(`CHAIN`) 등의 선형 요소를 구성합니다.


4. **조건부 원(`CIRCLE`) 및 선(`LINE`) 생성**
* 특정 조건(`_DAT_00826d90 == 0.0`)이 충족되면 측점 위치에 `CIRCLE` 요소를 드로잉하여 표지(桩, Stake/Marker) 역할을 하는 지점을 도면에 표시합니다.



---

### 💡 파이썬 리구현 관점에서의 시사점

이 함수는 C언어의 전역 상태(`_DAT_...`)에 지나치게 의존하고 있어, 파이썬으로 포팅할 때 이 전역 변수들을 하나의 **`AlignmentCalculator` 클래스 상태 객체**로 묶어 관리하면 매우 깔끔해집니다. 특히 20m 단위의 측점 전진 로직과 삼각함수 좌표 변환 부문은 파이썬의 `numpy`를 활용하면 훨씬 직관적이고 간결하게 구현할 수 있습니다.

이 거대한 계산 및 드로잉 엔진의 실체가 드러났는데, 이 함수를 파이썬으로 옮길 때 **삼각함수 좌표 변환 파트**나 **20m 스테이션 루프 파트** 중 어디부터 설계해 보고 싶으신가요?

"/

void FUN_0040db67(undefined4 *param_1,undefined4 *param_2,int *param_3,double *param_4,
                 double *param_5,double *param_6,undefined4 *param_7,undefined4 *param_8,
                 undefined4 *param_9,undefined4 *param_10,int *param_11,double *param_12,
                 double *param_13,double *param_14,undefined4 *param_15,undefined4 *param_16)

{
  int iVar1;
  float10 extraout_ST0;
  float10 fVar2;
  float10 fVar3;
  float10 fVar4;
  float10 extraout_ST0_00;
  int local_14;
  int local_8;
  
  FUN_00412670(7,s_!_@('_0',/,'LINE',/,'_8',/,'OUTS_0043bbf5 + 3,0xffffffff,0,0,0);
  FUN_00411d60(*param_1,param_1[1]);
  FUN_00411d60(*param_2,param_2[1]);
  FUN_00411d60(*param_9,param_9[1]);
  FUN_00411d60(*param_10,param_10[1]);
  FUN_00412850();
  _DAT_00826ce0 = 0.0;
  _DAT_00826ce8 = 0.0;
  _DAT_00826cf0 = *param_5;
  _DAT_00826cf8 = *param_6;
  _DAT_00826d00 = *param_5;
  _DAT_00826d08 = *param_6;
  _DAT_00826d10 = *param_5;
  _DAT_00826d18 = *param_6;
  if (*param_11 < *param_3) {
    DAT_00826d20 = 2;
  }
  else if (*param_3 < *param_11) {
    DAT_00826d20 = 1;
  }
  else if (*param_4 <= *param_12) {
    DAT_00826d20 = 1;
  }
  else {
    DAT_00826d20 = 2;
  }
  local_8 = 1;
  for (local_14 = 10000000; 0 < local_14; local_14 = local_14 + -1) {
    if (local_8 == 1) {
      _DAT_00826d2c = *(undefined4 *)((int)param_5 + 4);
      _DAT_00826d28 = *(undefined4 *)param_5;
      _DAT_00826d34 = *(undefined4 *)((int)param_6 + 4);
      _DAT_00826d30 = *(undefined4 *)param_6;
      if (DAT_00826d20 == 1) {
        if (DAT_0043f89c != 0) {
          __adj_fdiv_m64(0,0x40340000);
        }
        if (DAT_0043f89c != 0) {
          __adj_fdiv_m64(0,0x40340000);
        }
        iVar1 = __ftol();
        fVar2 = (float10)1.0 - (extraout_ST0 - (float10)iVar1);
        fVar3 = ABS(fVar2 * (float10)20.0);
        fVar4 = fVar3 + (float10)*param_4;
      }
      else {
        if (DAT_0043f89c != 0) {
          __adj_fdiv_m64(0,0x40340000);
        }
        if (DAT_0043f89c != 0) {
          __adj_fdiv_m64(0,0x40340000);
        }
        iVar1 = __ftol();
        fVar2 = extraout_ST0_00 - (float10)iVar1;
        fVar3 = ABS(fVar2 * (float10)20.0);
        fVar4 = (float10)*param_4 - fVar3;
      }
      _DAT_00826d38 = (double)fVar2;
      _DAT_00826ce8 = (double)fVar4;
      _DAT_00826ce0 = (double)fVar3;
    }
    else if (DAT_00826d20 == 1) {
      _DAT_00826ce0 = _DAT_00826ce0 + 20.0;
      _DAT_00826ce8 = _DAT_00826ce8 + 20.0;
    }
    else {
      _DAT_00826ce0 = _DAT_00826ce0 + 20.0;
      _DAT_00826ce8 = _DAT_00826ce8 - 20.0;
    }
    if (_DAT_00826ce8 == 0.0) {
      _DAT_00826ce8 = 1000.0;
    }
    FUN_00415c11();
    fVar2 = (float10)FUN_00415c7d();
    _DAT_00826d40 = (double)ABS(fVar2);
    _DAT_00826d48 = *param_13 - *param_5;
    _DAT_00826d50 = *param_14 - *param_6;
    if (DAT_0043f89c != 0) {
      __adj_fdiv_m64(_DAT_00826d48);
    }
    fVar2 = (float10)FUN_00415d3d();
    _DAT_00826d58 = (double)ABS(fVar2);
    if (DAT_0043f89c != 0) {
      __adj_fdiv_m64(DAT_00826ce0,DAT_00826ce4);
    }
    fVar2 = (float10)FUN_00415d3d();
    _DAT_00826d60 = (double)ABS(fVar2);
    if (_DAT_00826d48 <= 0.0) {
      if (_DAT_00826d50 <= 0.0) {
        _DAT_00826d68 = _DAT_00826d58 + ram0x0043bc80;
      }
      else {
        _DAT_00826d68 = ram0x0043bc80 - _DAT_00826d58;
      }
    }
    else if (_DAT_00826d50 <= 0.0) {
      _DAT_00826d68 = ram0x0043bc80 * 2.0 - _DAT_00826d58;
    }
    else {
      _DAT_00826d68 = _DAT_00826d58;
    }
    _DAT_00826d70 = _DAT_00826d60 + _DAT_00826d68;
    _DAT_00826d78 = _DAT_00826d68 - _DAT_00826d60;
    fVar2 = (float10)FUN_00415c2c();
    _DAT_00826cf0 = (double)(fVar2 * (float10)_DAT_00826ce0 + (float10)*param_5);
    fVar2 = (float10)FUN_00415c47();
    _DAT_00826cf8 = (double)(fVar2 * (float10)_DAT_00826ce0 + (float10)*param_6);
    fVar2 = (float10)FUN_00415c2c();
    _DAT_00826d00 = (double)(fVar2 * (float10)_DAT_00826d40 + (float10)*param_5);
    fVar2 = (float10)FUN_00415c47();
    _DAT_00826d08 = (double)(fVar2 * (float10)_DAT_00826d40 + (float10)*param_6);
    fVar2 = (float10)FUN_00415c2c();
    _DAT_00826d10 = (double)(fVar2 * (float10)_DAT_00826d40 + (float10)*param_5);
    fVar2 = (float10)FUN_00415c47();
    _DAT_00826d18 = (double)(fVar2 * (float10)_DAT_00826d40 + (float10)*param_6);
    if (*param_5 <= *param_13) {
      if (*param_13 < _DAT_00826cf0) break;
    }
    else if (_DAT_00826cf0 < *param_13) break;
    if (DAT_0043f89c == 0) {
      fVar2 = (float10)_DAT_00826ce8 / (float10)100.0;
    }
    else {
      fVar2 = (float10)__adj_fdiv_m64(0,0x40590000);
    }
    _DAT_00826d80 = (double)fVar2;
    if (DAT_0043f89c != 0) {
      __adj_fdiv_m64(0,0x40590000);
    }
    DAT_00826d88 = __ftol();
    _DAT_00826d90 = _DAT_00826d80 * _DAT_00826ce8 - (double)DAT_00826d88 * _DAT_00826ce8;
    if (_DAT_00826d90 == 0.0) {
      FUN_00412670(7,s_!_@('_0',/,'CIRCLE',/,'_8',/,'CH_0043bc85 + 3,0xffffffff,0,0,0);
      FUN_00411d60(DAT_00826cf0,DAT_00826cf4);
      FUN_00411d60(DAT_00826cf8,DAT_00826cfc);
      FUN_00412850();
    }
    FUN_00412670(7,s_('_0',/,'LINE',/,'_8',/,'CHAIN',_0043bcf0,0xffffffff,0,0,0);
    FUN_00411d60(DAT_00826d00,DAT_00826d04);
    FUN_00411d60(DAT_00826d08,DAT_00826d0c);
    FUN_00411d60(DAT_00826d10,DAT_00826d14);
    FUN_00411d60(DAT_00826d18,DAT_00826d1c);
    FUN_00412850();
    local_8 = local_8 + 1;
  }
  FUN_00412670(7,s_('_0',/,'LINE',/,'_8',/,'CENTER'_0043bd78,0xffffffff,0,0,0);
  FUN_00411d60(*(undefined4 *)param_5,*(undefined4 *)((int)param_5 + 4));
  FUN_00411d60(*(undefined4 *)param_6,*(undefined4 *)((int)param_6 + 4));
  FUN_00411d60(*(undefined4 *)param_13,*(undefined4 *)((int)param_13 + 4));
  FUN_00411d60(*(undefined4 *)param_14,*(undefined4 *)((int)param_14 + 4));
  FUN_00412850();
  FUN_00412670(7,s_('_0',/,'LINE',/,'_8',/,'INSIDE'_0043be00,0xffffffff,0,0,0);
  FUN_00411d60(*param_7,param_7[1]);
  FUN_00411d60(*param_8,param_8[1]);
  FUN_00411d60(*param_15,param_15[1]);
  FUN_00411d60(*param_16,param_16[1]);
  FUN_00412850();
  return;
}