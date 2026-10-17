/*
제시해주신 코드는 복잡한 부동소수점 연산을 반복하여 정밀한 해를 찾아내는 수치 반복법(Iterative Numerical Method, 예: 뉴턴-랩슨법 또는 근사 수렴 계산)을 수행하는 핵심 함수(`FUN_004081cf`)입니다.

함수의 구조와 주요 동작 의미를 알기 쉽게 정리해 드리겠습니다.

---

### 1. 함수의 전체 구조와 목적

* **매개변수 (`param_1` ~ `param_7`):** 포인터 형태로 전달된 여러 개의 실수 값을 입력받아 계산 결과를 갱신하고 저장합니다.
* **수렴(Convergence) 루프:** 내부의 `while(true)` 문을 돌며 특정 조건을 만족할 때까지 정밀한 계산을 반복합니다. 수치 해석이나 궤도 계산, 좌표 변환 알고리즘에서 오차를 줄여나갈 때 흔히 사용되는 전형적인 구조입니다.

---

### 2. 주요 연산 흐름

* **초기 오프셋 설정:**
함수 초입에서 입력값과 상수(`0.5` 등)를 이용해 첫 번째 기준값(`*param_7`)을 계산하고, 반복 횟수를 카운트하기 위한 변수(`_DAT_008269a8`)를 `1`로 초기화합니다.
* **저수준 플래그 및 FPU 보정:**
앞서 보았던 것과 같이 연산 도중 CPU 상태 플래그를 비트 연산(`uVar15` 조합)으로 철저하게 유지·관리하며, 구형 컴파일러의 FPU 나눗셈 오차를 방지하기 위한 `__adj_fdivr_m64` 등의 보정 함수들이 반복문 안팎으로 촘촘히 배치되어 있습니다.
* **복잡한 수식 연산:**
나눗셈, 뺄셈, 그리고 내부 유틸리티 함수(`FUN_00415c11`, `FUN_00415c7d` 등) 호출을 통해 파라미터 값들을 지속적으로 업데이트합니다.

---

### 3. 반복문의 탈출 조건 (핵심 로직)

루프 하단에는 다음과 같은 수렴 판정 로직이 존재합니다.

```c
fVar16 = (float10)*param_7 - fVar16;
_DAT_008269b8 = (double)fVar16;
if (fVar16 <= (float10)9.999999717180685e-10) break;

```

* **오차 검사:** 직전 값과 현재 값의 차이(오차, `fVar16`)를 계산합니다.
* **탈출 조건:** 이 오차가 `9.999999717180685e-10`(대략 $10^{-9}$ 수준의 매우 작은 값) **이하로 떨어지면 충분히 정확한 해가 구해진 것으로 판단하여 `break`로 반복문을 탈출**합니다.
* **값 갱신:** 아직 오차가 크다면 두 값의 평균을 다시 새로운 기준값(`*param_7`)으로 잡고, 반복 카운터(`_DAT_008269a8`)를 1씩 증가시키며 다음 루프를 실행합니다.

---

### 💡 요약

이 함수는 **특정 방정식이나 기하학적 문제를 풀기 위해, 오차가 $10^{-9}$ 미만이 될 때까지 값을 쪼개고 수정해가며 정답을 찾아가는 고정밀 수렴 계산(Iteration) 루틴**입니다. 과학 계산 프로그램이나 정밀 측정 장비의 내부 라이브러리에서 볼 수 있는 전형적인 코드입니다.
*/
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_004081cf(double *param_1,double *param_2,double *param_3,double *param_4,double *param_5,
                 double *param_6,double *param_7)

{
  undefined4 uVar1;
  byte in_CF;
  byte bVar2;
  byte in_PF;
  byte bVar3;
  byte in_AF;
  byte bVar4;
  byte in_ZF;
  byte bVar5;
  byte in_SF;
  byte bVar6;
  byte in_TF;
  byte bVar7;
  byte in_IF;
  byte bVar8;
  byte in_OF;
  byte bVar9;
  byte in_NT;
  byte bVar10;
  byte in_AC;
  byte bVar11;
  byte bVar12;
  byte in_ID;
  byte bVar13;
  byte bVar14;
  uint uVar15;
  float10 fVar16;
  float10 extraout_ST0;
  float10 extraout_ST1;
  float10 extraout_ST1_00;
  float10 fVar17;
  float10 extraout_ST1_01;
  float10 extraout_ST1_02;
  float10 extraout_ST1_03;
  
  FUN_00415c11();
  uVar15 = (uint)(in_NT & 1) * 0x4000 | (uint)(in_OF & 1) * 0x800 | (uint)(in_IF & 1) * 0x200 |
           (uint)(in_TF & 1) * 0x100 | (uint)(in_SF & 1) * 0x80 | (uint)(in_ZF & 1) * 0x40 |
           (uint)(in_AF & 1) * 0x10 | (uint)(in_PF & 1) * 4 | (uint)(in_CF & 1) |
           (uint)(in_ID & 1) * 0x200000 | (uint)(in_AC & 1) * 0x40000;
  if (DAT_0043f89c != 0) {
    __adj_fdiv_m64(0,0x40180000);
  }
  bVar10 = (uVar15 & 0x4000) != 0;
  bVar9 = (uVar15 & 0x800) != 0;
  bVar8 = (uVar15 & 0x200) != 0;
  bVar7 = (uVar15 & 0x100) != 0;
  bVar6 = (uVar15 & 0x80) != 0;
  bVar5 = (uVar15 & 0x40) != 0;
  bVar4 = (uVar15 & 0x10) != 0;
  bVar3 = (uVar15 & 4) != 0;
  bVar2 = (uVar15 & 1) != 0;
  bVar13 = (uVar15 & 0x200000) != 0;
  bVar11 = (uVar15 & 0x40000) != 0;
  FUN_00415c11();
  fVar16 = (float10)FUN_00415c7d();
  *param_7 = (double)((extraout_ST1 - fVar16) * (float10)0.5);
  _DAT_008269a8 = 1;
  while( true ) {
    *param_3 = *param_1 - *param_7;
    uVar15 = (uint)(bVar10 & 1) * 0x4000 | (uint)(bVar9 & 1) * 0x800 |
             (uint)((uVar15 & 0x400) != 0) * 0x400 | (uint)(bVar8 & 1) * 0x200 |
             (uint)(bVar7 & 1) * 0x100 | (uint)(bVar6 & 1) * 0x80 | (uint)(bVar5 & 1) * 0x40 |
             (uint)(bVar4 & 1) * 0x10 | (uint)(bVar3 & 1) * 4 | (uint)(bVar2 & 1) |
             (uint)(bVar13 & 1) * 0x200000 | (uint)(bVar11 & 1) * 0x40000;
    if (DAT_0043f89c == 0) {
      fVar16 = (float10)*param_2 / ((float10)*param_3 * (float10)2.0);
    }
    else {
      fVar16 = (float10)__adj_fdivr_m64(*(undefined4 *)param_2,*(undefined4 *)((int)param_2 + 4));
    }
    bVar10 = (uVar15 & 0x4000) != 0;
    bVar9 = (uVar15 & 0x800) != 0;
    bVar8 = (uVar15 & 0x200) != 0;
    bVar7 = (uVar15 & 0x100) != 0;
    bVar6 = (uVar15 & 0x80) != 0;
    bVar5 = (uVar15 & 0x40) != 0;
    bVar4 = (uVar15 & 0x10) != 0;
    bVar3 = (uVar15 & 4) != 0;
    bVar2 = (uVar15 & 1) != 0;
    bVar14 = (uVar15 & 0x200000) != 0;
    bVar11 = (uVar15 & 0x40000) != 0;
    bVar12 = 0;
    bVar13 = 0;
    *param_4 = (double)fVar16;
    FUN_00415c11();
    uVar1 = FUN_00415c11();
    uVar15 = (uint)(bVar10 & 1) * 0x4000 | (uint)(bVar9 & 1) * 0x800 |
             (uint)((uVar15 & 0x400) != 0) * 0x400 | (uint)(bVar8 & 1) * 0x200 |
             (uint)(bVar7 & 1) * 0x100 | (uint)(bVar6 & 1) * 0x80 | (uint)(bVar5 & 1) * 0x40 |
             (uint)(bVar4 & 1) * 0x10 | (uint)(bVar3 & 1) * 4 | (uint)(bVar2 & 1) |
             (uint)(bVar14 & 1) * 0x200000 | (uint)(bVar12 & 1) * 0x100000 |
             (uint)(bVar13 & 1) * 0x80000 | (uint)(bVar11 & 1) * 0x40000;
    if (DAT_0043f89c != 0) {
      FUN_00423257(uVar1,uVar15);
    }
    bVar10 = (uVar15 & 0x4000) != 0;
    bVar9 = (uVar15 & 0x800) != 0;
    bVar8 = (uVar15 & 0x200) != 0;
    bVar7 = (uVar15 & 0x100) != 0;
    bVar6 = (uVar15 & 0x80) != 0;
    bVar5 = (uVar15 & 0x40) != 0;
    bVar4 = (uVar15 & 0x10) != 0;
    bVar3 = (uVar15 & 4) != 0;
    bVar2 = (uVar15 & 1) != 0;
    bVar14 = (uVar15 & 0x200000) != 0;
    bVar11 = (uVar15 & 0x40000) != 0;
    bVar12 = 0;
    bVar13 = 0;
    FUN_00415c11();
    uVar1 = FUN_00415c11();
    uVar15 = (uint)(bVar10 & 1) * 0x4000 | (uint)(bVar9 & 1) * 0x800 |
             (uint)((uVar15 & 0x400) != 0) * 0x400 | (uint)(bVar8 & 1) * 0x200 |
             (uint)(bVar7 & 1) * 0x100 | (uint)(bVar6 & 1) * 0x80 | (uint)(bVar5 & 1) * 0x40 |
             (uint)(bVar4 & 1) * 0x10 | (uint)(bVar3 & 1) * 4 | (uint)(bVar2 & 1) |
             (uint)(bVar14 & 1) * 0x200000 | (uint)(bVar12 & 1) * 0x100000 |
             (uint)(bVar13 & 1) * 0x80000 | (uint)(bVar11 & 1) * 0x40000;
    if (DAT_0043f89c != 0) {
      FUN_00423257(uVar1,uVar15);
    }
    bVar10 = (uVar15 & 0x4000) != 0;
    bVar9 = (uVar15 & 0x800) != 0;
    bVar8 = (uVar15 & 0x200) != 0;
    bVar7 = (uVar15 & 0x100) != 0;
    bVar6 = (uVar15 & 0x80) != 0;
    bVar5 = (uVar15 & 0x40) != 0;
    bVar4 = (uVar15 & 0x10) != 0;
    bVar3 = (uVar15 & 4) != 0;
    bVar2 = (uVar15 & 1) != 0;
    bVar14 = (uVar15 & 0x200000) != 0;
    bVar11 = (uVar15 & 0x40000) != 0;
    bVar12 = 0;
    bVar13 = 0;
    fVar16 = (float10)FUN_00415c11();
    fVar16 = fVar16 * (float10)599040.0;
    uVar1 = FUN_00415c11();
    uVar15 = (uint)(bVar10 & 1) * 0x4000 | (uint)(bVar9 & 1) * 0x800 |
             (uint)((uVar15 & 0x400) != 0) * 0x400 | (uint)(bVar8 & 1) * 0x200 |
             (uint)(bVar7 & 1) * 0x100 | (uint)(bVar6 & 1) * 0x80 | (uint)(bVar5 & 1) * 0x40 |
             (uint)(bVar4 & 1) * 0x10 | (uint)(bVar3 & 1) * 4 | (uint)(bVar2 & 1) |
             (uint)(bVar14 & 1) * 0x200000 | (uint)(bVar12 & 1) * 0x100000 |
             (uint)(bVar13 & 1) * 0x80000 | (uint)(bVar11 & 1) * 0x40000;
    if (DAT_0043f89c == 0) {
      fVar17 = extraout_ST0 / extraout_ST1_00;
    }
    else {
      fVar17 = (float10)FUN_00423257(uVar1,uVar15);
      fVar16 = extraout_ST1_01;
    }
    bVar10 = (uVar15 & 0x4000) != 0;
    bVar9 = (uVar15 & 0x800) != 0;
    bVar8 = (uVar15 & 0x200) != 0;
    bVar7 = (uVar15 & 0x100) != 0;
    bVar6 = (uVar15 & 0x80) != 0;
    bVar5 = (uVar15 & 0x40) != 0;
    bVar4 = (uVar15 & 0x10) != 0;
    bVar3 = (uVar15 & 4) != 0;
    bVar2 = (uVar15 & 1) != 0;
    bVar14 = (uVar15 & 0x200000) != 0;
    bVar11 = (uVar15 & 0x40000) != 0;
    bVar12 = 0;
    bVar13 = 0;
    *param_5 = (double)((fVar16 - fVar17) * (float10)*param_2);
    FUN_00415c11();
    uVar1 = FUN_00415c11();
    uVar15 = (uint)(bVar10 & 1) * 0x4000 | (uint)(bVar9 & 1) * 0x800 |
             (uint)((uVar15 & 0x400) != 0) * 0x400 | (uint)(bVar8 & 1) * 0x200 |
             (uint)(bVar7 & 1) * 0x100 | (uint)(bVar6 & 1) * 0x80 | (uint)(bVar5 & 1) * 0x40 |
             (uint)(bVar4 & 1) * 0x10 | (uint)(bVar3 & 1) * 4 | (uint)(bVar2 & 1) |
             (uint)(bVar14 & 1) * 0x200000 | (uint)(bVar12 & 1) * 0x100000 |
             (uint)(bVar13 & 1) * 0x80000 | (uint)(bVar11 & 1) * 0x40000;
    if (DAT_0043f89c != 0) {
      FUN_00423257(uVar1,uVar15);
    }
    bVar10 = (uVar15 & 0x4000) != 0;
    bVar9 = (uVar15 & 0x800) != 0;
    bVar8 = (uVar15 & 0x200) != 0;
    bVar7 = (uVar15 & 0x100) != 0;
    bVar6 = (uVar15 & 0x80) != 0;
    bVar5 = (uVar15 & 0x40) != 0;
    bVar4 = (uVar15 & 0x10) != 0;
    bVar3 = (uVar15 & 4) != 0;
    bVar2 = (uVar15 & 1) != 0;
    bVar14 = (uVar15 & 0x200000) != 0;
    bVar11 = (uVar15 & 0x40000) != 0;
    bVar12 = 0;
    bVar13 = 0;
    FUN_00415c11();
    uVar1 = FUN_00415c11();
    uVar15 = (uint)(bVar10 & 1) * 0x4000 | (uint)(bVar9 & 1) * 0x800 |
             (uint)((uVar15 & 0x400) != 0) * 0x400 | (uint)(bVar8 & 1) * 0x200 |
             (uint)(bVar7 & 1) * 0x100 | (uint)(bVar6 & 1) * 0x80 | (uint)(bVar5 & 1) * 0x40 |
             (uint)(bVar4 & 1) * 0x10 | (uint)(bVar3 & 1) * 4 | (uint)(bVar2 & 1) |
             (uint)(bVar14 & 1) * 0x200000 | (uint)(bVar12 & 1) * 0x100000 |
             (uint)(bVar13 & 1) * 0x80000 | (uint)(bVar11 & 1) * 0x40000;
    if (DAT_0043f89c != 0) {
      FUN_00423257(uVar1,uVar15);
    }
    bVar10 = (uVar15 & 0x4000) != 0;
    bVar9 = (uVar15 & 0x800) != 0;
    bVar8 = (uVar15 & 0x200) != 0;
    bVar7 = (uVar15 & 0x100) != 0;
    bVar6 = (uVar15 & 0x80) != 0;
    bVar5 = (uVar15 & 0x40) != 0;
    bVar4 = (uVar15 & 0x10) != 0;
    bVar3 = (uVar15 & 4) != 0;
    bVar2 = (uVar15 & 1) != 0;
    bVar14 = (uVar15 & 0x200000) != 0;
    bVar11 = (uVar15 & 0x40000) != 0;
    bVar12 = 0;
    bVar13 = 0;
    FUN_00415c11();
    uVar1 = FUN_00415c11();
    uVar15 = (uint)(bVar10 & 1) * 0x4000 | (uint)(bVar9 & 1) * 0x800 |
             (uint)((uVar15 & 0x400) != 0) * 0x400 | (uint)(bVar8 & 1) * 0x200 |
             (uint)(bVar7 & 1) * 0x100 | (uint)(bVar6 & 1) * 0x80 | (uint)(bVar5 & 1) * 0x40 |
             (uint)(bVar4 & 1) * 0x10 | (uint)(bVar3 & 1) * 4 | (uint)(bVar2 & 1) |
             (uint)(bVar14 & 1) * 0x200000 | (uint)(bVar12 & 1) * 0x100000 |
             (uint)(bVar13 & 1) * 0x80000 | (uint)(bVar11 & 1) * 0x40000;
    if (DAT_0043f89c != 0) {
      FUN_00423257(uVar1,uVar15);
    }
    bVar10 = (uVar15 & 0x4000) != 0;
    bVar9 = (uVar15 & 0x800) != 0;
    bVar8 = (uVar15 & 0x200) != 0;
    bVar7 = (uVar15 & 0x100) != 0;
    bVar6 = (uVar15 & 0x80) != 0;
    bVar5 = (uVar15 & 0x40) != 0;
    bVar4 = (uVar15 & 0x10) != 0;
    bVar3 = (uVar15 & 4) != 0;
    bVar2 = (uVar15 & 1) != 0;
    bVar14 = (uVar15 & 0x200000) != 0;
    bVar11 = (uVar15 & 0x40000) != 0;
    bVar12 = 0;
    bVar13 = 0;
    fVar16 = (float10)FUN_00415c11();
    uVar15 = (uint)(bVar10 & 1) * 0x4000 | (uint)(bVar9 & 1) * 0x800 |
             (uint)((uVar15 & 0x400) != 0) * 0x400 | (uint)(bVar8 & 1) * 0x200 |
             (uint)(bVar7 & 1) * 0x100 | (uint)(bVar6 & 1) * 0x80 | (uint)(bVar5 & 1) * 0x40 |
             (uint)(bVar4 & 1) * 0x10 | (uint)(bVar3 & 1) * 4 | (uint)(bVar2 & 1) |
             (uint)(bVar14 & 1) * 0x200000 | (uint)(bVar12 & 1) * 0x100000 |
             (uint)(bVar13 & 1) * 0x80000 | (uint)(bVar11 & 1) * 0x40000;
    if (DAT_0043f89c == 0) {
      fVar16 = fVar16 / ((float10)*param_3 * (float10)6.0);
      fVar17 = extraout_ST1_02;
    }
    else {
      fVar16 = (float10)FUN_00423257(param_3,uVar15);
      fVar17 = extraout_ST1_03;
    }
    bVar4 = (uVar15 & 0x4000) != 0;
    bVar3 = (uVar15 & 0x200) != 0;
    bVar2 = (uVar15 & 0x100) != 0;
    bVar6 = (uVar15 & 0x200000) != 0;
    bVar5 = (uVar15 & 0x40000) != 0;
    *param_6 = (double)(fVar16 * fVar17);
    fVar16 = (float10)FUN_00415c2c();
    fVar16 = (float10)*param_6 - ((float10)1.0 - fVar16) * (float10)*param_3;
    _DAT_008269b0 = (double)fVar16;
    fVar16 = (float10)*param_7 - fVar16;
    _DAT_008269b8 = (double)fVar16;
    if (fVar16 <= (float10)9.999999717180685e-10) break;
    uVar15 = (uint)(bVar4 & 1) * 0x4000 | (uint)((uVar15 & 0x400) != 0) * 0x400 |
             (uint)(bVar3 & 1) * 0x200 | (uint)(bVar2 & 1) * 0x100 |
             (uint)(fVar16 < (float10)9.999999717180685e-10) | (uint)(bVar6 & 1) * 0x200000 |
             (uint)(bVar5 & 1) * 0x40000;
    if (DAT_0043f89c == 0) {
      fVar16 = ((float10)*param_7 + (float10)_DAT_008269b0) / (float10)2.0;
    }
    else {
      fVar16 = (float10)__adj_fdiv_m64(0,0x40000000);
    }
    bVar10 = (uVar15 & 0x4000) != 0;
    bVar8 = (uVar15 & 0x200) != 0;
    bVar7 = (uVar15 & 0x100) != 0;
    bVar4 = (uVar15 & 0x10) != 0;
    bVar2 = (uVar15 & 1) != 0;
    bVar13 = (uVar15 & 0x200000) != 0;
    bVar11 = (uVar15 & 0x40000) != 0;
    *param_7 = (double)fVar16;
    bVar9 = SCARRY4(_DAT_008269a8,1);
    _DAT_008269a8 = _DAT_008269a8 + 1;
    bVar6 = (int)_DAT_008269a8 < 0;
    bVar5 = _DAT_008269a8 == 0;
    bVar3 = (POPCOUNT(_DAT_008269a8 & 0xff) & 1U) == 0;
  }
  return;
}

