/"
제공해주신 `LAB_0040609a` 코드 블록은 도로 및 철도 선형 설계 프로그램에서 **세부 좌표를 산출하고 측점(Stationing)을 관리하는 핵심 연산 루틴**입니다.

이 레이블의 주요 역할과 동작을 한국어로 정리해 드립니다:

* **정밀 좌표 및 보간 계산**: `DAT_00645a64` 데이터셋을 기반으로 반복문을 실행하며, 삼각함수 래퍼 함수들(`FUN_00415c2c`, `FUN_00415c47`)을 호출해 실제 $X, Y$ 좌표를 정밀하게 계산한 뒤 메모리 버퍼(`DAT_007bd108`, `DAT_007ccb08` 등)에 저장합니다.


* **실행 모드 분기 (`DAT_00441ed4`)**:
* 값이 `0`일 경우, 상세한 텍스트와 표 형식의 결과 데이터를 화면이나 출력 파일에 포맷팅하여 보여줍니다.


* 그 외의 경우, 계산된 기하학적 요소와 데이터들을 대규모 내부 배열(예: `DAT_004e6128`)에 곧바로 기록하여 CAD 출력이나 다음 단계 연산에 대비합니다.




* **트레이 및 구간(Segment) 관리**: 인덱스 변수들(`local_18`, `local_28`)을 활용해 직선, 원호, 완화곡선 등 선형의 각 구간을 체계적으로 순회하며 데이터를 동기화하고 관리합니다.



즉, 이 블록은 선형의 수학적 제원들을 바탕으로 **실제 도면과 데이터에 쓰일 수 있는 수많은 측점별 좌표를 완성하고 분배하는 중추적인 역할**을 수행합니다.
"
/

LAB_0040609a:
          local_14 = 1;
          DAT_00694168 = 1;
          for (local_134 = DAT_00645a64; 0 < (int)local_134; local_134 = local_134 - 1) {
            bVar16 = 0;
            if ((_DAT_0079dc50 < *(double *)(local_14 * 8 + 0x645a60)) &&
               (bVar16 = 0, *(double *)(DAT_00694168 * 8 + 0x645a60) < _DAT_007bd100)) {
              bVar21 = _DAT_0079dc68 < 0.0;
              bVar22 = _DAT_0079dc68 == 0.0;
              if (bVar21 || bVar22) {
                pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)bVar20 * 0x400 |
                                       (uint)(in_IF & 1) * 0x200 | (uint)(in_TF & 1) * 0x100 |
                                       (uint)bVar22 * 0x40 | (uint)NAN(_DAT_0079dc68) * 4 |
                                       (uint)bVar21 | (uint)(in_ID & 1) * 0x200000 |
                                       (uint)(in_VIP & 1) * 0x100000 | (uint)(in_VIF & 1) * 0x80000
                                      | (uint)(in_AC & 1) * 0x40000);
                if (DAT_0043f89c == 0) {
                  fVar38 = ((float10)*(double *)(DAT_00694168 * 8 + 0x645a60) -
                           (float10)_DAT_0079dc50) /
                           (float10)(double)CONCAT44(DAT_00441f2c,DAT_00441f28);
                }
                else {
                  pcStack_208 = DAT_00441f2c;
                  fVar38 = (float10)__adj_fdiv_m64(DAT_00441f28);
                }
                fVar38 = -fVar38 + (float10)_DAT_0079dce8;
              }
              else {
                pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)bVar20 * 0x400 |
                                       (uint)(in_IF & 1) * 0x200 | (uint)(in_TF & 1) * 0x100 |
                                       (uint)bVar22 * 0x40 | (uint)NAN(_DAT_0079dc68) * 4 |
                                       (uint)bVar21 | (uint)(in_ID & 1) * 0x200000 |
                                       (uint)(in_VIP & 1) * 0x100000 | (uint)(in_VIF & 1) * 0x80000
                                      | (uint)(in_AC & 1) * 0x40000);
                if (DAT_0043f89c == 0) {
                  fVar38 = ((float10)*(double *)(DAT_00694168 * 8 + 0x645a60) -
                           (float10)_DAT_0079dc50) /
                           (float10)(double)CONCAT44(DAT_00441f2c,DAT_00441f28);
                }
                else {
                  pcStack_208 = DAT_00441f2c;
                  fVar38 = (float10)__adj_fdiv_m64(DAT_00441f28);
                }
                fVar38 = fVar38 + (float10)_DAT_0079dce8;
              }
              _DAT_007bd108 = (double)fVar38;
              in_ID = ((uint)pcStack_204 & 0x200000) != 0;
              in_VIP = 0;
              in_VIF = 0;
              in_AC = ((uint)pcStack_204 & 0x40000) != 0;
              in_NT = ((uint)pcStack_204 & 0x4000) != 0;
              bVar20 = ((uint)pcStack_204 & 0x400) != 0;
              in_IF = ((uint)pcStack_204 & 0x200) != 0;
              in_TF = ((uint)pcStack_204 & 0x100) != 0;
              bVar16 = ((uint)pcStack_204 & 0x10) != 0;
              pcStack_204 = (char *)0x4061d1;
              fVar38 = (float10)FUN_00415c2c();
              *(double *)(&DAT_007bd108 + local_14 * 8) =
                   (double)(fVar38 * (float10)*(double *)(&DAT_00664f00 + local_18 * 8) +
                           (float10)_DAT_0079dc28);
              pcStack_204 = (char *)0x4061f6;
              fVar38 = (float10)FUN_00415c47();
              *(double *)(local_14 * 8 + 0x7ccb08) =
                   (double)(fVar38 * (float10)*(double *)(&DAT_00664f00 + local_18 * 8) +
                           (float10)_DAT_0079dc30);
              iVar9 = DAT_007bd0f8;
              *(uint *)(DAT_007bd0f8 * 8 + 0x7dc50c) = (&DAT_00645a64)[local_14 * 2];
              *(undefined4 *)(iVar9 * 8 + 0x7dc508) = *(undefined4 *)(local_14 * 8 + 0x645a60);
              DAT_007bd0f8 = DAT_007bd0f8 + 1;
              local_14 = local_14 + 1;
            }
            DAT_00694168 = DAT_00694168 + 1;
          }
        }
        DAT_007ebf10 = local_14 + -1;
        DAT_007ebf18 = *(undefined4 *)
                        (((*(int *)(local_18 * 4 + 0x73828c) + -1) * 3 + local_18) * 4 + 0x6f1d80);
        DAT_007f3c18 = (*(double *)(local_18 * 8 + 0x694020) +
                       (double)CONCAT44(DAT_0079dc3c,DAT_0079dc38)) -
                       ((double)CONCAT44(DAT_0079dc3c,DAT_0079dc38) - _DAT_0079dc48);
        local_140 = DAT_0079dc98 + 1;
        local_24 = 2;
        while (local_140 = local_140 + -1, 0 < local_140) {
          *(double *)(local_24 * 8 + 0x7f3c10) =
               *(double *)(local_24 * 8 + 0x7f3c08) + (double)CONCAT44(DAT_0079dc3c,DAT_0079dc38);
          *(int *)(local_24 * 4 + 0x7ebf14) = (&DAT_007ebf10)[local_24];
          bVar16 = 0;
          if (1000.0 <= *(double *)(local_24 * 8 + 0x7f3c10)) {
            *(double *)(local_24 * 8 + 0x7f3c10) = *(double *)(local_24 * 8 + 0x7f3c10) - 1000.0;
            *(int *)(local_24 * 4 + 0x7ebf14) = (&DAT_007ebf10)[local_24] + 1;
          }
          local_24 = local_24 + 1;
        }
        if (DAT_00441ed4 != 1) {
          if (local_18 == 1) {
            pcStack_204 = (char *)0x0;
            pcStack_208 = (char *)0x0;
            FUN_00412670(6,&DAT_00439ac0,0xffffffff,0);
            pcStack_204 = (char *)0x4063a1;
            FUN_00412850();
          }
          if (local_18 == 2) {
            pcStack_204 = (char *)0x0;
            pcStack_208 = (char *)0x0;
            FUN_00412670(6,&DAT_00439b98,0xffffffff,0);
            pcStack_204 = (char *)0x4063c7;
            FUN_00412850();
          }
          if (local_18 == 3) {
            pcStack_204 = (char *)0x0;
            pcStack_208 = (char *)0x0;
            FUN_00412670(6,&DAT_00439c6c,0xffffffff,0);
            pcStack_204 = (char *)0x4063ed;
            FUN_00412850();
          }
        }
        DAT_00803618 = 1;
        pcStack_204 = (char *)0x3;
        pcStack_208 = (char *)0x1;
        FUN_00413b00(&DAT_00803620,1,3,&DAT_00439d40);
        pcStack_204 = (char *)0x3;
        pcStack_208 = (char *)0x1;
        FUN_00413b00(&DAT_00803623,1,3,&DAT_00439d44);
        pcStack_204 = (char *)0x3;
        pcStack_208 = (char *)0x1;
        FUN_00413b00(&DAT_00803626,1,3,&DAT_00439d48);
        pcStack_204 = (char *)0x3;
        pcStack_208 = (char *)0x1;
        FUN_00413b00(&DAT_00803629,1,3,&DAT_00439d4c);
        pcStack_204 = (char *)0x3;
        pcStack_208 = (char *)0x1;
        FUN_00413b00(&DAT_0080362c,1,3,&DAT_00439d50);
        pcStack_204 = (char *)0x3;
        pcStack_208 = (char *)0x1;
        FUN_00413b00(&DAT_0080362f,1,3,&DAT_00439d54);
        *(undefined4 *)(local_18 * 4 + 0x803634) = 1;
        *(undefined4 *)(local_18 * 4 + 0x4596cc) = 1;
        local_14c = *(int *)(local_18 * 4 + 0x73828c);
        local_28 = 1;
        while (local_14c = local_14c + -1, 0 < local_14c) {
          if (*(int *)(local_18 * 4 + 0x73828c) + -1 == local_28) {
            if (DAT_00441ed4 == 0) {
              pcStack_204 = (char *)0x0;
              pcStack_208 = (char *)0x0;
              FUN_00412670(6,s_(10X,'|',I2,'K',F7.3,'_|',F13.4,_00439d58,0xffffffff,0);
              pcStack_204 = *(char **)((local_28 * 3 + local_18) * 4 + 0x6f1d80);
              pcStack_208 = (char *)0x406546;
              FUN_00411da0();
              iVar9 = local_28 * 3 + local_18;
              pcStack_204 = *(char **)(iVar9 * 8 + 0x709474);
              pcStack_208 = *(char **)(iVar9 * 8 + 0x709470);
              FUN_00411d60();
              pcStack_204 = *(char **)(local_28 * 8 + 0x75f3e4);
              pcStack_208 = *(char **)(local_28 * 8 + 0x75f3e0);
              FUN_00411d60();
              pcStack_204 = *(char **)(local_28 * 8 + 0x76ede4);
              pcStack_208 = *(char **)(local_28 * 8 + 0x76ede0);
              FUN_00411d60();
              pcStack_204 = (char *)0x3;
              pcStack_208 = &DAT_00803620 + (DAT_00803618 + -1) * 3;
              FUN_00411e80();
              pcStack_204 = (char *)0x4065be;
              FUN_00412850();
            }
            else {
              *(undefined4 *)
               (&DAT_004e6128 + (*(int *)(local_18 * 4 + 0x803634) * 3 + local_18) * 4) =
                   *(undefined4 *)((local_28 * 3 + local_18) * 4 + 0x6f1d80);
              iVar9 = local_28 * 3 + local_18;
              iVar14 = *(int *)(local_18 * 4 + 0x803634) * 3 + local_18;
              *(undefined4 *)(iVar14 * 8 + 0x4fd81c) = *(undefined4 *)(iVar9 * 8 + 0x709474);
              *(undefined4 *)(iVar14 * 8 + 0x4fd818) = *(undefined4 *)(iVar9 * 8 + 0x709470);
              iVar9 = *(int *)(local_18 * 4 + 0x803634) * 3 + local_18;
              *(undefined4 *)(iVar9 * 8 + 0x52c61c) = *(undefined4 *)(local_28 * 8 + 0x76ede4);
              *(undefined4 *)(iVar9 * 8 + 0x52c618) = *(undefined4 *)(local_28 * 8 + 0x76ede0);
              iVar9 = *(int *)(local_18 * 4 + 0x803634) * 3 + local_18;
              *(undefined4 *)(iVar9 * 8 + 0x55b41c) = *(undefined4 *)(local_28 * 8 + 0x75f3e4);
              *(undefined4 *)(iVar9 * 8 + 0x55b418) = *(undefined4 *)(local_28 * 8 + 0x75f3e0);
              pcStack_204 = (char *)0x3;
              pcStack_208 = (char *)0x1;
              FUN_00413b00(&DAT_00803648 +
                           (*(int *)(local_18 * 4 + 0x803634) * 3 + local_18 + -4) * 3,1,3,
                           &DAT_00803620 + (DAT_00803618 + -1) * 3);
              piVar1 = (int *)(local_18 * 4 + 0x803634);
              *piVar1 = *piVar1 + 1;
            }
            DAT_00803618 = DAT_00803618 + 1;
          }
          else if (local_28 == 1) {
            if (DAT_00441ed4 == 0) {
              pcStack_204 = (char *)0x0;
              pcStack_208 = (char *)0x0;
              FUN_00412670(6,s_(10X,'|',I2,'K',F7.3,'_|',F13.4,_00439da4,0xffffffff,0);
              pcStack_204 = *(char **)((local_18 + 3) * 4 + 0x6f1d80);
              pcStack_208 = (char *)0x406712;
              FUN_00411da0();
              pcStack_204 = *(char **)((local_18 + 3) * 8 + 0x709474);
              pcStack_208 = *(char **)((local_18 + 3) * 8 + 0x709470);
              FUN_00411d60();
              pcStack_204 = (char *)DAT_0075f3ec;
              pcStack_208 = DAT_0075f3e8;
              FUN_00411d60();
              pcStack_204 = (char *)DAT_0076edec;
              pcStack_208 = DAT_0076ede8;
              FUN_00411d60();
              pcStack_204 = (char *)0x3;
              pcStack_208 = &DAT_00803620 + (DAT_00803618 + -1) * 3;
              FUN_00411e80();
              pcStack_204 = (char *)0x40678a;
              FUN_00412850();
            }
            else {
              *(undefined4 *)
               (&DAT_004e6128 + (*(int *)(local_18 * 4 + 0x803634) * 3 + local_18) * 4) =
                   *(undefined4 *)((local_18 + 3) * 4 + 0x6f1d80);
              iVar9 = *(int *)(local_18 * 4 + 0x803634) * 3 + local_18;
              *(undefined4 *)(iVar9 * 8 + 0x4fd81c) = *(undefined4 *)((local_18 + 3) * 8 + 0x709474)
              ;
              *(undefined4 *)(iVar9 * 8 + 0x4fd818) = *(undefined4 *)((local_18 + 3) * 8 + 0x709470)
              ;
              iVar9 = *(int *)(local_18 * 4 + 0x803634) * 3 + local_18;
              *(undefined4 *)(iVar9 * 8 + 0x52c61c) = DAT_0076edec;
              *(char **)(iVar9 * 8 + 0x52c618) = DAT_0076ede8;
              iVar9 = *(int *)(local_18 * 4 + 0x803634) * 3 + local_18;
              *(undefined4 *)(iVar9 * 8 + 0x55b41c) = DAT_0075f3ec;
              *(char **)(iVar9 * 8 + 0x55b418) = DAT_0075f3e8;
              pcStack_204 = (char *)0x3;
              pcStack_208 = (char *)0x1;
              FUN_00413b00(&DAT_00803648 +
                           (*(int *)(local_18 * 4 + 0x803634) * 3 + local_18 + -4) * 3,1,3,
                           &DAT_00803620 + (DAT_00803618 + -1) * 3);
              piVar1 = (int *)(local_18 * 4 + 0x803634);
              *piVar1 = *piVar1 + 1;
            }
            DAT_00803618 = DAT_00803618 + 1;
          }
          else {
            bVar16 = 0;
            if (*(double *)((local_28 * 3 + local_18) * 8 + 0x709470) ==
                (double)CONCAT44(DAT_0069409c,DAT_00694098)) {
              if (DAT_00441ed4 == 0) {
                pcStack_204 = (char *)0x0;
                pcStack_208 = (char *)0x0;
                FUN_00412670(6,s_(10X,'|',I2,'K',F7.3,'_|',F13.4,_00439df0,0xffffffff,0);
                pcStack_204 = *(char **)((local_28 * 3 + local_18) * 4 + 0x6f1d80);
                pcStack_208 = (char *)0x4068f3;
                FUN_00411da0();
                iVar9 = local_28 * 3 + local_18;
                pcStack_204 = *(char **)(iVar9 * 8 + 0x709474);
                pcStack_208 = *(char **)(iVar9 * 8 + 0x709470);
                FUN_00411d60();
                pcStack_204 = *(char **)(local_28 * 8 + 0x75f3e4);
                pcStack_208 = *(char **)(local_28 * 8 + 0x75f3e0);
                FUN_00411d60();
                pcStack_204 = *(char **)(local_28 * 8 + 0x76ede4);
                pcStack_208 = *(char **)(local_28 * 8 + 0x76ede0);
                FUN_00411d60();
                pcStack_204 = (char *)0x3;
                pcStack_208 = &DAT_00803620 + (DAT_00803618 + -1) * 3;
                FUN_00411e80();
                pcStack_204 = (char *)0x40696b;
                FUN_00412850();
              }
              else {
                *(undefined4 *)
                 (&DAT_004e6128 + (*(int *)(local_18 * 4 + 0x803634) * 3 + local_18) * 4) =
                     *(undefined4 *)((local_28 * 3 + local_18) * 4 + 0x6f1d80);
                iVar9 = local_28 * 3 + local_18;
                iVar14 = *(int *)(local_18 * 4 + 0x803634) * 3 + local_18;
                *(undefined4 *)(iVar14 * 8 + 0x4fd81c) = *(undefined4 *)(iVar9 * 8 + 0x709474);
                *(undefined4 *)(iVar14 * 8 + 0x4fd818) = *(undefined4 *)(iVar9 * 8 + 0x709470);
                iVar9 = *(int *)(local_18 * 4 + 0x803634) * 3 + local_18;
                *(undefined4 *)(iVar9 * 8 + 0x52c61c) = *(undefined4 *)(local_28 * 8 + 0x76ede4);
                *(undefined4 *)(iVar9 * 8 + 0x52c618) = *(undefined4 *)(local_28 * 8 + 0x76ede0);
                iVar9 = *(int *)(local_18 * 4 + 0x803634) * 3 + local_18;
                *(undefined4 *)(iVar9 * 8 + 0x55b41c) = *(undefined4 *)(local_28 * 8 + 0x75f3e4);
                *(undefined4 *)(iVar9 * 8 + 0x55b418) = *(undefined4 *)(local_28 * 8 + 0x75f3e0);
                pcStack_204 = (char *)0x3;
                pcStack_208 = (char *)0x1;
                FUN_00413b00(&DAT_00803648 +
                             (*(int *)(local_18 * 4 + 0x803634) * 3 + local_18 + -4) * 3,1,3,
                             &DAT_00803620 + (DAT_00803618 + -1) * 3);
                piVar1 = (int *)(local_18 * 4 + 0x803634);
                *piVar1 = *piVar1 + 1;
              }
              DAT_00803618 = DAT_00803618 + 1;
            }
            else if (DAT_00441ed4 == 0) {
              pcStack_204 = (char *)0x0;
              pcStack_208 = (char *)0x0;
              FUN_00412670(6,s_(10X,'|',I2,'K',F7.3,'_|',F13.4,_00439e3c,0xffffffff,0);
              pcStack_204 = *(char **)((local_28 * 3 + local_18) * 4 + 0x6f1d80);
              pcStack_208 = (char *)0x406ab5;
              FUN_00411da0();
              iVar9 = local_28 * 3 + local_18;
              pcStack_204 = *(char **)(iVar9 * 8 + 0x709474);
              pcStack_208 = *(char **)(iVar9 * 8 + 0x709470);
              FUN_00411d60();
              pcStack_204 = *(char **)(local_28 * 8 + 0x75f3e4);
              pcStack_208 = *(char **)(local_28 * 8 + 0x75f3e0);
              FUN_00411d60();
              pcStack_204 = *(char **)(local_28 * 8 + 0x76ede4);
              pcStack_208 = *(char **)(local_28 * 8 + 0x76ede0);
              FUN_00411d60();
              pcStack_204 = (char *)0x406b14;
              FUN_00412850();
            }
            else {
              *(undefined4 *)
               (&DAT_004e6128 + (*(int *)(local_18 * 4 + 0x803634) * 3 + local_18) * 4) =
                   *(undefined4 *)((local_28 * 3 + local_18) * 4 + 0x6f1d80);
              iVar9 = local_28 * 3 + local_18;
              iVar14 = *(int *)(local_18 * 4 + 0x803634) * 3 + local_18;
              *(undefined4 *)(iVar14 * 8 + 0x4fd81c) = *(undefined4 *)(iVar9 * 8 + 0x709474);
              *(undefined4 *)(iVar14 * 8 + 0x4fd818) = *(undefined4 *)(iVar9 * 8 + 0x709470);
              iVar9 = *(int *)(local_18 * 4 + 0x803634) * 3 + local_18;
              *(undefined4 *)(iVar9 * 8 + 0x52c61c) = *(undefined4 *)(local_28 * 8 + 0x76ede4);
              *(undefined4 *)(iVar9 * 8 + 0x52c618) = *(undefined4 *)(local_28 * 8 + 0x76ede0);
              iVar9 = *(int *)(local_18 * 4 + 0x803634) * 3 + local_18;
              *(undefined4 *)(iVar9 * 8 + 0x55b41c) = *(undefined4 *)(local_28 * 8 + 0x75f3e4);
              *(undefined4 *)(iVar9 * 8 + 0x55b418) = *(undefined4 *)(local_28 * 8 + 0x75f3e0);
              pcStack_204 = (char *)0x3;
              pcStack_208 = (char *)0x1;
              FUN_00413b00(&DAT_00803648 +
                           (*(int *)(local_18 * 4 + 0x803634) * 3 + local_18 + -4) * 3,1,3,
                           &DAT_00439e88);
              piVar1 = (int *)(local_18 * 4 + 0x803634);
              *piVar1 = *piVar1 + 1;
            }
          }
          local_28 = local_28 + 1;
        }
        piVar1 = (int *)(local_18 * 4 + 0x803634);
        *piVar1 = *piVar1 + -1;
        DAT_00655474 = 1;
        *(undefined4 *)(local_18 * 4 + 0x814f84) = 1;
        local_2c = 1;
        for (local_158 = DAT_0079dc98 + 1; 0 < local_158; local_158 = local_158 + -1) {
          if (DAT_007ebf10 == 0) {