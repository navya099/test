LAB_004071bb:
            if (DAT_00441ed4 == 0) {
              pcStack_204 = (char *)0x0;
              pcStack_208 = (char *)0x0;
              FUN_00412670(6,s_(10X,'|',I2,'K',F7.3,'_|',F13.4,_00439f24,0xffffffff,0);
              pcStack_204 = *(char **)(local_2c * 4 + 0x7ebf14);
              pcStack_208 = (char *)0x4071ee;
              FUN_00411da0();
              pcStack_204 = *(char **)(local_2c * 8 + 0x7f3c14);
              pcStack_208 = *(char **)(local_2c * 8 + 0x7f3c10);
              FUN_00411d60();
              pcStack_204 = *(char **)(local_2c * 8 + 0x79dcf4);
              pcStack_208 = *(char **)(&DAT_0079dcf0 + local_2c * 8);
              FUN_00411d60();
              pcStack_204 = *(char **)(local_2c * 8 + 0x7ad6f4);
              pcStack_208 = *(char **)(local_2c * 8 + 0x7ad6f0);
              FUN_00411d60();
              pcStack_204 = (char *)0x407247;
              FUN_00412850();
            }
            else {
              pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)bVar20 * 0x400 |
                                     (uint)(in_IF & 1) * 0x200 | (uint)(in_TF & 1) * 0x100 |
                                     (uint)((int)DAT_00441ed4 < 0) * 0x80 |
                                     (uint)(DAT_00441ed4 == 0) * 0x40 | (uint)(bVar16 & 1) * 0x10 |
                                     (uint)((POPCOUNT(DAT_00441ed4 & 0xff) & 1U) == 0) * 4 |
                                     (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 |
                                     (uint)(in_VIF & 1) * 0x80000 | (uint)(in_AC & 1) * 0x40000);
              if (DAT_0043f89c == 0) {
                fVar38 = (float10)*(double *)(local_2c * 8 + 0x7f3c10) / (float10)20.0;
              }
              else {
                pcStack_208 = (char *)0x40340000;
                fVar38 = (float10)__adj_fdiv_m64(0);
              }
              _DAT_00814fa0 = (double)fVar38;
              pcStack_204 = (char *)((uint)(((uint)pcStack_204 & 0x4000) != 0) * 0x4000 |
                                     (uint)(((uint)pcStack_204 & 0x800) != 0) * 0x800 |
                                     (uint)(((uint)pcStack_204 & 0x400) != 0) * 0x400 |
                                     (uint)(((uint)pcStack_204 & 0x200) != 0) * 0x200 |
                                     (uint)(((uint)pcStack_204 & 0x100) != 0) * 0x100 |
                                     (uint)(((uint)pcStack_204 & 0x80) != 0) * 0x80 |
                                     (uint)(((uint)pcStack_204 & 0x40) != 0) * 0x40 |
                                     (uint)(((uint)pcStack_204 & 0x10) != 0) * 0x10 |
                                     (uint)(((uint)pcStack_204 & 4) != 0) * 4 |
                                     (uint)(((uint)pcStack_204 & 1) != 0) |
                                     (uint)(((uint)pcStack_204 & 0x200000) != 0) * 0x200000 |
                                    (uint)(((uint)pcStack_204 & 0x40000) != 0) * 0x40000);
              if (DAT_0043f89c != 0) {
                pcStack_208 = (char *)0x40340000;
                __adj_fdiv_m64(0);
              }
              in_NT = ((uint)pcStack_204 & 0x4000) != 0;
              bVar20 = ((uint)pcStack_204 & 0x400) != 0;
              in_IF = ((uint)pcStack_204 & 0x200) != 0;
              in_TF = ((uint)pcStack_204 & 0x100) != 0;
              in_ID = ((uint)pcStack_204 & 0x200000) != 0;
              in_AC = ((uint)pcStack_204 & 0x40000) != 0;
              in_VIP = 0;
              in_VIF = 0;
              pcStack_204 = (char *)0x4072b3;
              DAT_00814fa8 = __ftol();
              _DAT_00814fb0 =
                   *(double *)(local_2c * 8 + 0x7f3c10) * _DAT_00814fa0 -
                   *(double *)(local_2c * 8 + 0x7f3c10) * (double)DAT_00814fa8;
              bVar16 = 0;
              if (_DAT_00814fb0 == 0.0) {
                *(double *)((*(int *)(local_18 * 4 + 0x814f84) * 3 + local_18) * 8 + 0x58a218) =
                     (double)*(int *)(local_2c * 4 + 0x7ebf14);
                iVar9 = *(int *)(local_18 * 4 + 0x814f84) * 3 + local_18;
                *(undefined4 *)(iVar9 * 8 + 0x5b901c) = *(undefined4 *)(local_2c * 8 + 0x7f3c14);
                *(undefined4 *)(iVar9 * 8 + 0x5b9018) = *(undefined4 *)(local_2c * 8 + 0x7f3c10);
                iVar9 = *(int *)(local_18 * 4 + 0x814f84) * 3 + local_18;
                *(undefined4 *)(iVar9 * 8 + 0x5e7e1c) = *(undefined4 *)(local_2c * 8 + 0x7ad6f4);
                *(undefined4 *)(iVar9 * 8 + 0x5e7e18) = *(undefined4 *)(local_2c * 8 + 0x7ad6f0);
                iVar9 = *(int *)(local_18 * 4 + 0x814f84) * 3 + local_18;
                *(undefined4 *)(iVar9 * 8 + 0x616c1c) = *(undefined4 *)(local_2c * 8 + 0x79dcf4);
                *(undefined4 *)(iVar9 * 8 + 0x616c18) =
                     *(undefined4 *)(&DAT_0079dcf0 + local_2c * 8);
                piVar1 = (int *)(local_18 * 4 + 0x814f84);
                *piVar1 = *piVar1 + 1;
              }
            }
          }
          else {
            _DAT_00814f98 =
                 (double)((float)*(int *)(local_2c * 4 + 0x7ebf14) * 1000.0 +
                         (float)*(double *)(local_2c * 8 + 0x7f3c10));
            bVar16 = 0;
            if (((*(double *)(DAT_00655474 * 8 + 0x7dc508) <= _DAT_00814f98) ||
                (bVar16 = 0, _DAT_007bd100 <= *(double *)(DAT_00655474 * 8 + 0x7dc508))) ||
               (bVar16 = 0,
               (double)CONCAT44(DAT_0079dc3c,DAT_0079dc38) <=
               *(double *)(DAT_00655474 * 8 + 0x645a60) - _DAT_00814f98)) goto LAB_004071bb;
            if (DAT_00441ed4 == 0) {
              pcStack_204 = (char *)0x0;
              pcStack_208 = (char *)0x0;
              FUN_00412670(6,s_(10X,'|',I2,'K',F7.3,'_|',F13.4,_00439e8c,0xffffffff,0);
              pcStack_204 = *(char **)(local_2c * 4 + 0x7ebf14);
              pcStack_208 = (char *)0x406d47;
              FUN_00411da0();
              pcStack_204 = *(char **)(local_2c * 8 + 0x7f3c14);
              pcStack_208 = *(char **)(local_2c * 8 + 0x7f3c10);
              FUN_00411d60();
              pcStack_204 = *(char **)(local_2c * 8 + 0x79dcf4);
              pcStack_208 = *(char **)(&DAT_0079dcf0 + local_2c * 8);
              FUN_00411d60();
              pcStack_204 = *(char **)(local_2c * 8 + 0x7ad6f4);
              pcStack_208 = *(char **)(local_2c * 8 + 0x7ad6f0);
              FUN_00411d60();
              bVar19 = (undefined1 *)0xfffffff7 < &pcStack_208;
              bVar30 = SCARRY4((int)&pcStack_208,8);
              bVar27 = (int)&stack0xfffffe00 < 0;
              bVar24 = &stack0x00000000 == (undefined1 *)0x200;
              bVar18 = 1;
              pcStack_204 = (char *)0x406da0;
              FUN_00412850();
            }
            else {
              pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)bVar20 * 0x400 |
                                     (uint)(in_IF & 1) * 0x200 | (uint)(in_TF & 1) * 0x100 |
                                     (uint)((int)DAT_00441ed4 < 0) * 0x80 |
                                     (uint)(DAT_00441ed4 == 0) * 0x40 |
                                     (uint)((POPCOUNT(DAT_00441ed4 & 0xff) & 1U) == 0) * 4 |
                                     (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 |
                                     (uint)(in_VIF & 1) * 0x80000 | (uint)(in_AC & 1) * 0x40000);
              if (DAT_0043f89c == 0) {
                fVar38 = (float10)*(double *)(local_2c * 8 + 0x7f3c10) / (float10)20.0;
              }
              else {
                pcStack_208 = (char *)0x40340000;
                fVar38 = (float10)__adj_fdiv_m64(0);
              }
              _DAT_00814fa0 = (double)fVar38;
              pcStack_204 = (char *)((uint)(((uint)pcStack_204 & 0x4000) != 0) * 0x4000 |
                                     (uint)(((uint)pcStack_204 & 0x800) != 0) * 0x800 |
                                     (uint)(((uint)pcStack_204 & 0x400) != 0) * 0x400 |
                                     (uint)(((uint)pcStack_204 & 0x200) != 0) * 0x200 |
                                     (uint)(((uint)pcStack_204 & 0x100) != 0) * 0x100 |
                                     (uint)(((uint)pcStack_204 & 0x80) != 0) * 0x80 |
                                     (uint)(((uint)pcStack_204 & 0x40) != 0) * 0x40 |
                                     (uint)(((uint)pcStack_204 & 0x10) != 0) * 0x10 |
                                     (uint)(((uint)pcStack_204 & 4) != 0) * 4 |
                                     (uint)(((uint)pcStack_204 & 1) != 0) |
                                     (uint)(((uint)pcStack_204 & 0x200000) != 0) * 0x200000 |
                                    (uint)(((uint)pcStack_204 & 0x40000) != 0) * 0x40000);
              if (DAT_0043f89c != 0) {
                pcStack_208 = (char *)0x40340000;
                __adj_fdiv_m64(0);
              }
              in_NT = ((uint)pcStack_204 & 0x4000) != 0;
              bVar30 = ((uint)pcStack_204 & 0x800) != 0;
              bVar20 = ((uint)pcStack_204 & 0x400) != 0;
              in_IF = ((uint)pcStack_204 & 0x200) != 0;
              in_TF = ((uint)pcStack_204 & 0x100) != 0;
              in_ID = ((uint)pcStack_204 & 0x200000) != 0;
              in_AC = ((uint)pcStack_204 & 0x40000) != 0;
              in_VIP = 0;
              in_VIF = 0;
              pcStack_204 = (char *)0x406e0c;
              DAT_00814fa8 = __ftol();
              _DAT_00814fb0 =
                   *(double *)(local_2c * 8 + 0x7f3c10) * _DAT_00814fa0 -
                   *(double *)(local_2c * 8 + 0x7f3c10) * (double)DAT_00814fa8;
              bVar18 = NAN(_DAT_00814fb0);
              bVar19 = _DAT_00814fb0 < 0.0;
              bVar27 = 0;
              bVar16 = 0;
              bVar24 = 0;
              if (_DAT_00814fb0 == 0.0) {
                *(double *)((*(int *)(local_18 * 4 + 0x814f84) * 3 + local_18) * 8 + 0x58a218) =
                     (double)*(int *)(local_2c * 4 + 0x7ebf14);
                iVar9 = *(int *)(local_18 * 4 + 0x814f84) * 3 + local_18;
                *(undefined4 *)(iVar9 * 8 + 0x5b901c) = *(undefined4 *)(local_2c * 8 + 0x7f3c14);
                *(undefined4 *)(iVar9 * 8 + 0x5b9018) = *(undefined4 *)(local_2c * 8 + 0x7f3c10);
                iVar9 = *(int *)(local_18 * 4 + 0x814f84) * 3 + local_18;
                *(undefined4 *)(iVar9 * 8 + 0x5e7e1c) = *(undefined4 *)(local_2c * 8 + 0x7ad6f4);
                *(undefined4 *)(iVar9 * 8 + 0x5e7e18) = *(undefined4 *)(local_2c * 8 + 0x7ad6f0);
                uVar10 = *(int *)(local_18 * 4 + 0x814f84) * 3;
                bVar19 = CARRY4(uVar10,local_18);
                iVar9 = uVar10 + local_18;
                *(undefined4 *)(iVar9 * 8 + 0x616c1c) = *(undefined4 *)(local_2c * 8 + 0x79dcf4);
                *(undefined4 *)(iVar9 * 8 + 0x616c18) =
                     *(undefined4 *)(&DAT_0079dcf0 + local_2c * 8);
                puVar2 = (uint *)(local_18 * 4 + 0x814f84);
                bVar30 = SCARRY4(*puVar2,1);
                *puVar2 = *puVar2 + 1;
                bVar27 = (int)*puVar2 < 0;
                bVar24 = *puVar2 == 0;
                bVar18 = (POPCOUNT(*puVar2 & 0xff) & 1U) == 0;
              }
            }
            do {
              pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)(bVar30 & 1) * 0x800 |
                                     (uint)bVar20 * 0x400 | (uint)(in_IF & 1) * 0x200 |
                                     (uint)(in_TF & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                                     (uint)(bVar24 & 1) * 0x40 | (uint)(bVar16 & 1) * 0x10 |
                                     (uint)(bVar18 & 1) * 4 | (uint)(bVar19 & 1) |
                                     (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 |
                                     (uint)(in_VIF & 1) * 0x80000 | (uint)(in_AC & 1) * 0x40000);
              if (DAT_0043f89c != 0) {
                pcStack_208 = (char *)0x408f4000;
                __adj_fdiv_m64(0);
              }
              in_NT = ((uint)pcStack_204 & 0x4000) != 0;
              bVar20 = ((uint)pcStack_204 & 0x400) != 0;
              in_IF = ((uint)pcStack_204 & 0x200) != 0;
              in_TF = ((uint)pcStack_204 & 0x100) != 0;
              bVar16 = ((uint)pcStack_204 & 0x10) != 0;
              in_ID = ((uint)pcStack_204 & 0x200000) != 0;
              in_AC = ((uint)pcStack_204 & 0x40000) != 0;
              in_VIP = 0;
              in_VIF = 0;
              pcStack_204 = (char *)0x406f51;
              DAT_00814fb8 = __ftol();
              _DAT_00814fc0 = (double)DAT_00814fb8;
              _DAT_00814fc8 = *(double *)(DAT_00655474 * 8 + 0x7dc508) - _DAT_00814fc0 * 1000.0;
              if (DAT_00441ed4 == 0) {
                pcStack_204 = (char *)0x0;
                pcStack_208 = (char *)0x0;
                FUN_00412670(6,s_(10X,'|',I2,'K',F7.3,'_|',F13.4,_00439ed8,0xffffffff,0);
                pcStack_204 = (char *)DAT_00814fb8;
                pcStack_208 = (char *)0x406fb4;
                FUN_00411da0();
                pcStack_204 = (char *)DAT_00814fcc;
                pcStack_208 = DAT_00814fc8;
                FUN_00411d60();
                pcStack_204 = *(char **)(DAT_00655474 * 8 + 0x7bd10c);
                pcStack_208 = *(char **)(&DAT_007bd108 + DAT_00655474 * 8);
                FUN_00411d60();
                pcStack_204 = *(char **)(DAT_00655474 * 8 + 0x7ccb0c);
                pcStack_208 = *(char **)(DAT_00655474 * 8 + 0x7ccb08);
                FUN_00411d60();
                pcStack_204 = (char *)0x40700a;
                FUN_00412850();
              }
              else {
                pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)bVar20 * 0x400 |
                                       (uint)(in_IF & 1) * 0x200 | (uint)(in_TF & 1) * 0x100 |
                                       (uint)((int)DAT_00441ed4 < 0) * 0x80 |
                                       (uint)(DAT_00441ed4 == 0) * 0x40 | (uint)(bVar16 & 1) * 0x10
                                       | (uint)((POPCOUNT(DAT_00441ed4 & 0xff) & 1U) == 0) * 4 |
                                       (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000
                                       | (uint)(in_VIF & 1) * 0x80000 | (uint)(in_AC & 1) * 0x40000)
                ;
                if (DAT_0043f89c == 0) {
                  fVar38 = (float10)*(double *)(local_2c * 8 + 0x7f3c10) / (float10)20.0;
                }
                else {
                  pcStack_208 = (char *)0x40340000;
                  fVar38 = (float10)__adj_fdiv_m64(0);
                }
                _DAT_00814fa0 = (double)fVar38;
                pcStack_204 = (char *)((uint)(((uint)pcStack_204 & 0x4000) != 0) * 0x4000 |
                                       (uint)(((uint)pcStack_204 & 0x800) != 0) * 0x800 |
                                       (uint)(((uint)pcStack_204 & 0x400) != 0) * 0x400 |
                                       (uint)(((uint)pcStack_204 & 0x200) != 0) * 0x200 |
                                       (uint)(((uint)pcStack_204 & 0x100) != 0) * 0x100 |
                                       (uint)(((uint)pcStack_204 & 0x80) != 0) * 0x80 |
                                       (uint)(((uint)pcStack_204 & 0x40) != 0) * 0x40 |
                                       (uint)(((uint)pcStack_204 & 0x10) != 0) * 0x10 |
                                       (uint)(((uint)pcStack_204 & 4) != 0) * 4 |
                                       (uint)(((uint)pcStack_204 & 1) != 0) |
                                       (uint)(((uint)pcStack_204 & 0x200000) != 0) * 0x200000 |
                                      (uint)(((uint)pcStack_204 & 0x40000) != 0) * 0x40000);
                if (DAT_0043f89c != 0) {
                  pcStack_208 = (char *)0x40340000;
                  __adj_fdiv_m64(0);
                }
                in_NT = ((uint)pcStack_204 & 0x4000) != 0;
                bVar20 = ((uint)pcStack_204 & 0x400) != 0;
                in_IF = ((uint)pcStack_204 & 0x200) != 0;
                in_TF = ((uint)pcStack_204 & 0x100) != 0;
                in_ID = ((uint)pcStack_204 & 0x200000) != 0;
                in_AC = ((uint)pcStack_204 & 0x40000) != 0;
                in_VIP = 0;
                in_VIF = 0;
                pcStack_204 = (char *)0x407076;
                DAT_00814fa8 = __ftol();
                _DAT_00814fb0 =
                     *(double *)(local_2c * 8 + 0x7f3c10) * _DAT_00814fa0 -
                     *(double *)(local_2c * 8 + 0x7f3c10) * (double)DAT_00814fa8;
                if (_DAT_00814fb0 == 0.0) {
                  *(double *)((*(int *)(local_18 * 4 + 0x814f84) * 3 + local_18) * 8 + 0x58a218) =
                       (double)DAT_00814fb8;
                  iVar9 = *(int *)(local_18 * 4 + 0x814f84) * 3 + local_18;
                  *(undefined4 *)(iVar9 * 8 + 0x5b901c) = DAT_00814fcc;
                  *(char **)(iVar9 * 8 + 0x5b9018) = DAT_00814fc8;
                  iVar9 = DAT_00655474;
                  iVar14 = *(int *)(local_18 * 4 + 0x814f84) * 3 + local_18;
                  *(undefined4 *)(iVar14 * 8 + 0x5e7e1c) =
                       *(undefined4 *)(DAT_00655474 * 8 + 0x7ccb0c);
                  *(undefined4 *)(iVar14 * 8 + 0x5e7e18) = *(undefined4 *)(iVar9 * 8 + 0x7ccb08);
                  iVar9 = DAT_00655474;
                  iVar14 = *(int *)(local_18 * 4 + 0x814f84) * 3 + local_18;
                  *(undefined4 *)(iVar14 * 8 + 0x616c1c) =
                       *(undefined4 *)(DAT_00655474 * 8 + 0x7bd10c);
                  *(undefined4 *)(iVar14 * 8 + 0x616c18) =
                       *(undefined4 *)(&DAT_007bd108 + iVar9 * 8);
                  piVar1 = (int *)(local_18 * 4 + 0x814f84);
                  *piVar1 = *piVar1 + 1;
                }
              }
              bVar30 = SCARRY4(DAT_00655474,1);
              DAT_00655474 = DAT_00655474 + 1;
              dVar6 = *(double *)(DAT_00655474 * 8 + 0x645a60) - _DAT_00814f98;
              dVar3 = (double)CONCAT44(DAT_0079dc3c,DAT_0079dc38);
              bVar18 = NAN(dVar6) || NAN(dVar3);
              bVar24 = dVar6 == dVar3;
              bVar27 = 0;
              bVar16 = 0;
              bVar19 = 1;
            } while (dVar6 < dVar3);
          }
          local_2c = local_2c + 1;
        }
        piVar1 = (int *)(local_18 * 4 + 0x814f84);
        *piVar1 = *piVar1 + -1;
        DAT_00814fd0 = 0;
        local_30 = DAT_006651dc;
        for (local_164 = *(int *)(local_18 * 4 + 0x6940dc) - DAT_006651dc; 0 < local_164;
            local_164 = local_164 + -1) {
          DAT_00814fd0 = DAT_00814fd0 + 1;
          if (DAT_006651dc == local_30) {
            if (DAT_00441ed4 == 0) {
              pcStack_204 = (char *)0x0;
              pcStack_208 = (char *)0x0;
              FUN_00412670(6,s_(10X,'|',I2,'K',F7.3,'_|',F13.4,_00439f70,0xffffffff,0);
              pcStack_204 = *(char **)((local_30 * 3 + local_18) * 4 + 0x6f1d80);
              pcStack_208 = (char *)0x40747d;
              FUN_00411da0();
              iVar9 = local_30 * 3 + local_18;
              pcStack_204 = *(char **)(iVar9 * 8 + 0x709474);
              pcStack_208 = *(char **)(iVar9 * 8 + 0x709470);
              FUN_00411d60();
              pcStack_204 = *(char **)(DAT_00814fd0 * 8 + 0x77e814);
              pcStack_208 = *(char **)(&DAT_0077e810 + DAT_00814fd0 * 8);
              FUN_00411d60();
              pcStack_204 = *(char **)(DAT_00814fd0 * 8 + 0x78e214);
              pcStack_208 = *(char **)(DAT_00814fd0 * 8 + 0x78e210);
              FUN_00411d60();
              pcStack_204 = (char *)0x3;
              pcStack_208 = &DAT_00803620 + (DAT_00803618 + -1) * 3;
              FUN_00411e80();
              pcStack_204 = (char *)0x4074f9;
              FUN_00412850();
            }
            else {
              (&DAT_00441fc0)[*(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18] =
                   *(undefined4 *)((local_30 * 3 + local_18) * 4 + 0x6f1d80);
              iVar9 = local_30 * 3 + local_18;
              iVar14 = *(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18;
              *(undefined4 *)(iVar14 * 8 + 0x4596cc) = *(undefined4 *)(iVar9 * 8 + 0x709474);
              *(undefined4 *)(iVar14 * 8 + 0x4596c8) = *(undefined4 *)(iVar9 * 8 + 0x709470);
              iVar9 = DAT_00814fd0;
              iVar14 = *(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18;
              *(undefined4 *)(iVar14 * 8 + 0x4884d4) = *(undefined4 *)(DAT_00814fd0 * 8 + 0x78e214);
              *(undefined4 *)(iVar14 * 8 + 0x4884d0) = *(undefined4 *)(iVar9 * 8 + 0x78e210);
              iVar9 = DAT_00814fd0;
              iVar14 = *(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18;
              *(undefined4 *)(iVar14 * 8 + 0x4b72dc) = *(undefined4 *)(DAT_00814fd0 * 8 + 0x77e814);
              *(undefined4 *)(iVar14 * 8 + 0x4b72d8) = *(undefined4 *)(&DAT_0077e810 + iVar9 * 8);
              pcStack_204 = (char *)0x3;
              pcStack_208 = (char *)0x1;
              FUN_00413b00(&DAT_00814fd8 +
                           (*(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18 + -4) * 3,1,3,
                           &DAT_00803620 + (DAT_00803618 + -1) * 3);
              piVar1 = (int *)(local_18 * 4 + 0x4596cc);
              *piVar1 = *piVar1 + 1;
            }
            DAT_00803618 = DAT_00803618 + 1;
          }
          else if (*(int *)(local_18 * 4 + 0x6940dc) + -1 == local_30) {
            if (DAT_00441ed4 == 0) {
              pcStack_204 = (char *)0x0;
              pcStack_208 = (char *)0x0;
              FUN_00412670(6,s_(10X,'|',I2,'K',F7.3,'_|',F13.4,_00439fbc,0xffffffff,0);
              pcStack_204 = *(char **)(local_18 * 4 + 0x694064);
              pcStack_208 = (char *)0x407655;
              FUN_00411da0();
              pcStack_204 = *(char **)(local_18 * 8 + 0x694074);
              pcStack_208 = *(char **)(local_18 * 8 + 0x694070);
              FUN_00411d60();
              pcStack_204 = *(char **)(DAT_00814fd0 * 8 + 0x77e814);
              pcStack_208 = *(char **)(&DAT_0077e810 + DAT_00814fd0 * 8);
              FUN_00411d60();
              pcStack_204 = *(char **)(DAT_00814fd0 * 8 + 0x78e214);
              pcStack_208 = *(char **)(DAT_00814fd0 * 8 + 0x78e210);
              FUN_00411d60();
              pcStack_204 = (char *)0x3;
              pcStack_208 = &DAT_00803620 + (DAT_00803618 + -1) * 3;
              FUN_00411e80();
              pcStack_204 = (char *)0x4076cb;
              FUN_00412850();
            }
            else {
              (&DAT_00441fc0)[*(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18] =
                   *(undefined4 *)(local_18 * 4 + 0x694064);
              iVar9 = *(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18;
              *(undefined4 *)(iVar9 * 8 + 0x4596cc) = *(undefined4 *)(local_18 * 8 + 0x694074);
              *(undefined4 *)(iVar9 * 8 + 0x4596c8) = *(undefined4 *)(local_18 * 8 + 0x694070);
              iVar9 = DAT_00814fd0;
              iVar14 = *(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18;
              *(undefined4 *)(iVar14 * 8 + 0x4884d4) = *(undefined4 *)(DAT_00814fd0 * 8 + 0x78e214);
              *(undefined4 *)(iVar14 * 8 + 0x4884d0) = *(undefined4 *)(iVar9 * 8 + 0x78e210);
              iVar9 = DAT_00814fd0;
              iVar14 = *(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18;
              *(undefined4 *)(iVar14 * 8 + 0x4b72dc) = *(undefined4 *)(DAT_00814fd0 * 8 + 0x77e814);
              *(undefined4 *)(iVar14 * 8 + 0x4b72d8) = *(undefined4 *)(&DAT_0077e810 + iVar9 * 8);
              pcStack_204 = (char *)0x3;
              pcStack_208 = (char *)0x1;
              FUN_00413b00(&DAT_00814fd8 +
                           (*(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18 + -4) * 3,1,3,
                           &DAT_00803620 + (DAT_00803618 + -1) * 3);
              piVar1 = (int *)(local_18 * 4 + 0x4596cc);
              *piVar1 = *piVar1 + 1;
            }
          }
          else {
            bVar16 = 0;
            if (*(double *)((local_30 * 3 + local_18) * 8 + 0x709470) ==
                (double)CONCAT44(DAT_006940ac,DAT_006940a8)) {
              if (DAT_00441ed4 == 0) {
                pcStack_204 = (char *)0x0;
                pcStack_208 = (char *)0x0;
                FUN_00412670(6,s_(10X,'|',I2,'K',F7.3,'_|',F13.4,_0043a008,0xffffffff,0);
                pcStack_204 = *(char **)((local_30 * 3 + local_18) * 4 + 0x6f1d80);
                pcStack_208 = (char *)0x407826;
                FUN_00411da0();
                iVar9 = local_30 * 3 + local_18;
                pcStack_204 = *(char **)(iVar9 * 8 + 0x709474);
                pcStack_208 = *(char **)(iVar9 * 8 + 0x709470);
                FUN_00411d60();
                pcStack_204 = *(char **)(DAT_00814fd0 * 8 + 0x77e814);
                pcStack_208 = *(char **)(&DAT_0077e810 + DAT_00814fd0 * 8);
                FUN_00411d60();
                pcStack_204 = *(char **)(DAT_00814fd0 * 8 + 0x78e214);
                pcStack_208 = *(char **)(DAT_00814fd0 * 8 + 0x78e210);
                FUN_00411d60();
                pcStack_204 = (char *)0x3;
                pcStack_208 = &DAT_00803620 + (DAT_00803618 + -1) * 3;
                FUN_00411e80();
                pcStack_204 = (char *)0x4078a2;
                FUN_00412850();
              }
              else {
                (&DAT_00441fc0)[*(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18] =
                     *(undefined4 *)((local_30 * 3 + local_18) * 4 + 0x6f1d80);
                iVar9 = local_30 * 3 + local_18;
                iVar14 = *(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18;
                *(undefined4 *)(iVar14 * 8 + 0x4596cc) = *(undefined4 *)(iVar9 * 8 + 0x709474);
                *(undefined4 *)(iVar14 * 8 + 0x4596c8) = *(undefined4 *)(iVar9 * 8 + 0x709470);
                iVar9 = DAT_00814fd0;
                iVar14 = *(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18;
                *(undefined4 *)(iVar14 * 8 + 0x4884d4) =
                     *(undefined4 *)(DAT_00814fd0 * 8 + 0x78e214);
                *(undefined4 *)(iVar14 * 8 + 0x4884d0) = *(undefined4 *)(iVar9 * 8 + 0x78e210);
                iVar9 = DAT_00814fd0;
                iVar14 = *(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18;
                *(undefined4 *)(iVar14 * 8 + 0x4b72dc) =
                     *(undefined4 *)(DAT_00814fd0 * 8 + 0x77e814);
                *(undefined4 *)(iVar14 * 8 + 0x4b72d8) = *(undefined4 *)(&DAT_0077e810 + iVar9 * 8);
                pcStack_204 = (char *)0x3;
                pcStack_208 = (char *)0x1;
                FUN_00413b00(&DAT_00814fd8 +
                             (*(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18 + -4) * 3,1,3,
                             &DAT_00803620 + (DAT_00803618 + -1) * 3);
                piVar1 = (int *)(local_18 * 4 + 0x4596cc);
                *piVar1 = *piVar1 + 1;
              }
              DAT_00803618 = DAT_00803618 + 1;
            }
            else if (DAT_00441ed4 == 0) {
              pcStack_204 = (char *)0x0;
              pcStack_208 = (char *)0x0;
              FUN_00412670(6,s_(10X,'|',I2,'K',F7.3,'_|',F13.4,_0043a054,0xffffffff,0);
              pcStack_204 = *(char **)((local_30 * 3 + local_18) * 4 + 0x6f1d80);
              pcStack_208 = (char *)0x4079f0;
              FUN_00411da0();
              iVar9 = local_30 * 3 + local_18;
              pcStack_204 = *(char **)(iVar9 * 8 + 0x709474);
              pcStack_208 = *(char **)(iVar9 * 8 + 0x709470);
              FUN_00411d60();
              pcStack_204 = *(char **)(DAT_00814fd0 * 8 + 0x77e814);
              pcStack_208 = *(char **)(&DAT_0077e810 + DAT_00814fd0 * 8);
              FUN_00411d60();
              pcStack_204 = *(char **)(DAT_00814fd0 * 8 + 0x78e214);
              pcStack_208 = *(char **)(DAT_00814fd0 * 8 + 0x78e210);
              FUN_00411d60();
              pcStack_204 = (char *)0x407a53;
              FUN_00412850();
            }
            else {
              (&DAT_00441fc0)[*(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18] =
                   *(undefined4 *)((local_30 * 3 + local_18) * 4 + 0x6f1d80);
              iVar9 = local_30 * 3 + local_18;
              iVar14 = *(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18;
              *(undefined4 *)(iVar14 * 8 + 0x4596cc) = *(undefined4 *)(iVar9 * 8 + 0x709474);
              *(undefined4 *)(iVar14 * 8 + 0x4596c8) = *(undefined4 *)(iVar9 * 8 + 0x709470);
              iVar9 = DAT_00814fd0;
              iVar14 = *(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18;
              *(undefined4 *)(iVar14 * 8 + 0x4884d4) = *(undefined4 *)(DAT_00814fd0 * 8 + 0x78e214);
              *(undefined4 *)(iVar14 * 8 + 0x4884d0) = *(undefined4 *)(iVar9 * 8 + 0x78e210);
              iVar9 = DAT_00814fd0;
              iVar14 = *(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18;
              *(undefined4 *)(iVar14 * 8 + 0x4b72dc) = *(undefined4 *)(DAT_00814fd0 * 8 + 0x77e814);
              *(undefined4 *)(iVar14 * 8 + 0x4b72d8) = *(undefined4 *)(&DAT_0077e810 + iVar9 * 8);
              pcStack_204 = (char *)0x3;
              pcStack_208 = (char *)0x1;
              FUN_00413b00(&DAT_00814fd8 +
                           (*(int *)(local_18 * 4 + 0x4596cc) * 3 + local_18 + -4) * 3,1,3,
                           &DAT_0043a0a0);
              piVar1 = (int *)(local_18 * 4 + 0x4596cc);
              *piVar1 = *piVar1 + 1;
            }
          }
          local_30 = local_30 + 1;
        }
        piVar1 = (int *)(local_18 * 4 + 0x4596cc);
        *piVar1 = *piVar1 + -1;
        local_18 = local_18 + 1;
      }
    }
    else {
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,s_(/,/,/,T28,'END_OF_CALCULATION.'_00439a3c,0xffffffff,0);
      pcStack_204 = (char *)0x404c96;
      FUN_00412850();
      pcStack_204 = (char *)0x1;
      pcStack_208 = &DAT_00439a64;
      cVar8 = FUN_00414280(&DAT_00441f78,10);
      if (cVar8 != '\0') goto LAB_00404ce1;
      pcStack_204 = (char *)0x1;
      pcStack_208 = &DAT_00439a68;
      cVar8 = FUN_00414280(&DAT_00441f78,10);
      if (cVar8 != '\0') goto LAB_00404ce1;
    }
    if (DAT_00441ed4 != 0) {
      DAT_00441ed4 = 0;
      DAT_00826918 = DAT_00803638;
      local_34 = 2;
      for (local_170 = 2; 0 < local_170; local_170 = local_170 + -1) {
        DAT_0082691c = *(int *)(local_34 * 4 + 0x803634);
        if (DAT_00826918 < DAT_0082691c) {
          DAT_00826918 = DAT_0082691c;
        }
        local_34 = local_34 + 1;
      }
      DAT_00826920 = DAT_004596d0;
      local_38 = 2;
      for (local_17c = 2; 0 < local_17c; local_17c = local_17c + -1) {
        DAT_00826924 = *(int *)(local_38 * 4 + 0x4596cc);
        if (DAT_00826920 < DAT_00826924) {
          DAT_00826920 = DAT_00826924;
        }
        local_38 = local_38 + 1;
      }
      DAT_00826928 = DAT_00814f88;
      local_3c = 2;
      for (local_188 = 2; 0 < local_188; local_188 = local_188 + -1) {
        DAT_0082692c = *(int *)(local_3c * 4 + 0x814f84);
        if (DAT_00826928 < DAT_0082692c) {
          DAT_00826928 = DAT_0082692c;
        }
        local_3c = local_3c + 1;
      }
      pcStack_204 = (char *)0x1;
      pcStack_208 = &DAT_0043a0a4;
      cVar8 = FUN_00414280(&DAT_00645a38,10);
      if (cVar8 == '\0') {
        pcStack_204 = (char *)0x1;
        pcStack_208 = &DAT_0043a0a8;
        cVar8 = FUN_00414280(&DAT_00645a38,10);
        if (cVar8 != '\0') goto LAB_00407db4;
      }
      else {