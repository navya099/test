for (local_78 = 3; bVar20 = ((uint)pcVar11 & 0x400) != 0, 0 < local_78; local_78 = local_78 + -1
        ) {
      uVar10 = local_18 - 2;
      if ((int)uVar10 < 0) {
        pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)bVar20 * 0x400 |
                               (uint)(in_IF & 1) * 0x200 | (uint)(in_TF & 1) * 0x100 |
                               (uint)((int)uVar10 < 0) * 0x80 | (uint)(uVar10 == 0) * 0x40 |
                               (uint)(bVar16 & 1) * 0x10 |
                               (uint)((POPCOUNT(uVar10 & 0xff) & 1U) == 0) * 4 |
                               (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 |
                               (uint)(in_VIF & 1) * 0x80000 | (uint)(in_AC & 1) * 0x40000);
        if (DAT_0043f89c == 0) {
          fVar38 = (float10)(double)CONCAT44(DAT_00441f4c,DAT_00441f48) / (float10)2.0;
        }
        else {
          pcStack_208 = (char *)0x40000000;
          fVar38 = (float10)__adj_fdiv_m64(0);
        }
        in_NT = ((uint)pcStack_204 & 0x4000) != 0;
        bVar18 = ((uint)pcStack_204 & 0x800) != 0;
        bVar20 = ((uint)pcStack_204 & 0x400) != 0;
        in_IF = ((uint)pcStack_204 & 0x200) != 0;
        in_TF = ((uint)pcStack_204 & 0x100) != 0;
        in_ID = ((uint)pcStack_204 & 0x200000) != 0;
        in_AC = ((uint)pcStack_204 & 0x40000) != 0;
        in_VIP = 0;
        in_VIF = 0;
        _DAT_00664ee8 = (double)(fVar38 + (float10)(double)CONCAT44(DAT_00441f2c,DAT_00441f28));
        DAT_00664ef0._4_4_ = DAT_00441f34;
        DAT_00664ef0._0_4_ = DAT_00441f30;
        pcStack_204 = (char *)&DAT_00664f68;
        pcStack_208 = (char *)&DAT_00664f50;
        //수치해석함수ㅜ호출
        thunk_FUN_004081cf(&DAT_00664ee8,&DAT_00664ef0,&DAT_00664f08,&DAT_00664f20,&DAT_00664f38);
      }
      else {
        bVar18 = 0;
        if (uVar10 == 0) {
          _DAT_00664f10 = DAT_00664f08 - (double)CONCAT44(DAT_00441f44,DAT_00441f40);
          _DAT_00664f70 = (double)CONCAT44(DAT_00441f2c,DAT_00441f28) - _DAT_00664f10;
          pcStack_204 = (char *)&DAT_00664f28;
          pcStack_208 = (char *)&DAT_00664f58;
          thunk_FUN_004084cd(&DAT_00664f10,&DAT_00664f70,&DAT_00664ef8,&DAT_00664f40);
        }
        else {
          _DAT_00664f18 =
               DAT_00664f08 -
               ((double)CONCAT44(DAT_00441f44,DAT_00441f40) +
               (double)CONCAT44(DAT_00441f3c,DAT_00441f38));
          pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)bVar20 * 0x400 |
                                 (uint)(in_IF & 1) * 0x200 | (uint)(in_TF & 1) * 0x100 |
                                 (uint)((int)uVar10 < 0) * 0x80 | (uint)(uVar10 == 0) * 0x40 |
                                 (uint)(bVar16 & 1) * 0x10 |
                                 (uint)((POPCOUNT(uVar10 & 0xff) & 1U) == 0) * 4 |
                                 (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 |
                                 (uint)(in_VIF & 1) * 0x80000 | (uint)(in_AC & 1) * 0x40000);
          if (DAT_0043f89c == 0) {
            fVar38 = (float10)(double)CONCAT44(DAT_00441f4c,DAT_00441f48) / (float10)2.0;
          }
          else {
            pcStack_208 = (char *)0x40000000;
            fVar38 = (float10)__adj_fdiv_m64(0);
          }
          in_NT = ((uint)pcStack_204 & 0x4000) != 0;
          bVar18 = ((uint)pcStack_204 & 0x800) != 0;
          bVar20 = ((uint)pcStack_204 & 0x400) != 0;
          in_IF = ((uint)pcStack_204 & 0x200) != 0;
          in_TF = ((uint)pcStack_204 & 0x100) != 0;
          in_ID = ((uint)pcStack_204 & 0x200000) != 0;
          in_AC = ((uint)pcStack_204 & 0x40000) != 0;
          in_VIP = 0;
          in_VIF = 0;
          _DAT_00664f78 =
               (double)(((float10)(double)CONCAT44(DAT_00441f2c,DAT_00441f28) - fVar38) -
                       (float10)_DAT_00664f18);
          pcStack_204 = &DAT_00664f30;
          pcStack_208 = &DAT_00664f60;
          thunk_FUN_004084cd(&DAT_00664f18,&DAT_00664f78,&DAT_00664f00,&DAT_00664f48);
        }
      }
      pcStack_204 = (char *)0x402c9d;
      fVar38 = (float10)FUN_00415c47();
      *(double *)(&DAT_00664f78 + local_18 * 8) =
           (double)((float10)*(double *)(&DAT_00664f30 + local_18 * 8) -
                   fVar38 * (float10)*(double *)(&DAT_00664f00 + local_18 * 8));
      pcStack_204 = (char *)0x402cd0;
      FUN_00415c11();
      pcStack_204 = (char *)0x402ce5;
      FUN_00415c11();
      pcStack_204 = (char *)0x402cec;
      fVar38 = (float10)FUN_00415c7d();
      *(double *)(local_18 * 8 + 0x664f90) = (double)fVar38;
      *(double *)(local_18 * 8 + 0x664fa8) =
           *(double *)(&DAT_00664f00 + local_18 * 8) + *(double *)(&DAT_00664f60 + local_18 * 8);
      pcStack_204 = (char *)0x402d2d;
      fVar38 = (float10)FUN_00415c7d();
      *(double *)(local_18 * 8 + 0x664fc0) = (double)fVar38;
      dVar3 = *(double *)(&DAT_00664f18 + local_18 * 8);
      bVar16 = NAN(dVar3);
      bVar19 = dVar3 < 0.0;
      bVar24 = dVar3 == 0.0;
      bVar30 = 0;
      bVar27 = 0;
      if (!(bool)bVar24) {
        pcStack_204 = (char *)0x402d64;
        fVar38 = (float10)FUN_00415c62();
        pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)(bVar18 & 1) * 0x800 |
                               (uint)bVar20 * 0x400 | (uint)(in_IF & 1) * 0x200 |
                               (uint)(in_TF & 1) * 0x100 | (uint)(bVar30 & 1) * 0x80 |
                               (uint)(bVar24 & 1) * 0x40 | (uint)(bVar27 & 1) * 0x10 |
                               (uint)(bVar16 & 1) * 4 | (uint)(bVar19 & 1) |
                               (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 |
                               (uint)(in_VIF & 1) * 0x80000 | (uint)(in_AC & 1) * 0x40000);
        if (DAT_0043f89c == 0) {
          fVar38 = (float10)*(double *)(&DAT_00664f48 + local_18 * 8) / fVar38;
        }
        else {
          pcStack_208 = *(char **)(local_18 * 8 + 0x664f4c);
          fVar38 = (float10)__adj_fdivr_m64(*(undefined4 *)(&DAT_00664f48 + local_18 * 8));
        }
        in_NT = ((uint)pcStack_204 & 0x4000) != 0;
        bVar18 = ((uint)pcStack_204 & 0x800) != 0;
        bVar20 = ((uint)pcStack_204 & 0x400) != 0;
        in_IF = ((uint)pcStack_204 & 0x200) != 0;
        in_TF = ((uint)pcStack_204 & 0x100) != 0;
        in_ID = ((uint)pcStack_204 & 0x200000) != 0;
        in_AC = ((uint)pcStack_204 & 0x40000) != 0;
        in_VIP = 0;
        in_VIF = 0;
        *(double *)(local_18 * 8 + 0x664fd8) = (double)fVar38;
      }
      *(double *)(local_18 * 8 + 0x664ff0) =
           *(double *)(&DAT_00664f30 + local_18 * 8) - *(double *)(local_18 * 8 + 0x664fd8);
      dVar3 = *(double *)(&DAT_00664f18 + local_18 * 8);
      bVar16 = NAN(dVar3);
      bVar19 = dVar3 < 0.0;
      bVar24 = dVar3 == 0.0;
      bVar30 = 0;
      bVar27 = 0;
      if (!(bool)bVar24) {
        pcStack_204 = (char *)0x402de3;
        fVar38 = (float10)FUN_00415c47();
        pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)(bVar18 & 1) * 0x800 |
                               (uint)bVar20 * 0x400 | (uint)(in_IF & 1) * 0x200 |
                               (uint)(in_TF & 1) * 0x100 | (uint)(bVar30 & 1) * 0x80 |
                               (uint)(bVar24 & 1) * 0x40 | (uint)(bVar27 & 1) * 0x10 |
                               (uint)(bVar16 & 1) * 4 | (uint)(bVar19 & 1) |
                               (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 |
                               (uint)(in_VIF & 1) * 0x80000 | (uint)(in_AC & 1) * 0x40000);
        if (DAT_0043f89c == 0) {
          fVar38 = (float10)*(double *)(&DAT_00664f48 + local_18 * 8) / fVar38;
        }
        else {
          pcStack_208 = *(char **)(local_18 * 8 + 0x664f4c);
          fVar38 = (float10)__adj_fdivr_m64(*(undefined4 *)(&DAT_00664f48 + local_18 * 8));
        }
        in_NT = ((uint)pcStack_204 & 0x4000) != 0;
        bVar18 = ((uint)pcStack_204 & 0x800) != 0;
        bVar20 = ((uint)pcStack_204 & 0x400) != 0;
        in_IF = ((uint)pcStack_204 & 0x200) != 0;
        in_TF = ((uint)pcStack_204 & 0x100) != 0;
        in_ID = ((uint)pcStack_204 & 0x200000) != 0;
        in_AC = ((uint)pcStack_204 & 0x40000) != 0;
        in_VIP = 0;
        in_VIF = 0;
        *(double *)(local_18 * 8 + 0x665008) = (double)fVar38;
      }
      dVar3 = *(double *)(&DAT_00664f30 + local_18 * 8);
      bVar16 = NAN(dVar3);
      bVar19 = dVar3 < 0.0;
      bVar24 = dVar3 == 0.0;
      bVar30 = 0;
      bVar27 = 0;
      if (!(bool)bVar24) {
        pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)(bVar18 & 1) * 0x800 |
                               (uint)bVar20 * 0x400 | (uint)(in_IF & 1) * 0x200 |
                               (uint)(in_TF & 1) * 0x100 | (uint)bVar24 * 0x40 | (uint)bVar16 * 4 |
                               (uint)bVar19 | (uint)(in_ID & 1) * 0x200000 |
                               (uint)(in_VIP & 1) * 0x100000 | (uint)(in_VIF & 1) * 0x80000 |
                              (uint)(in_AC & 1) * 0x40000);
        if (DAT_0043f89c != 0) {
          pcStack_208 = *(char **)(local_18 * 8 + 0x664f34);
          __adj_fdiv_m64(*(undefined4 *)(&DAT_00664f30 + local_18 * 8));
        }
        in_NT = ((uint)pcStack_204 & 0x4000) != 0;
        bVar18 = ((uint)pcStack_204 & 0x800) != 0;
        bVar20 = ((uint)pcStack_204 & 0x400) != 0;
        in_IF = ((uint)pcStack_204 & 0x200) != 0;
        in_TF = ((uint)pcStack_204 & 0x100) != 0;
        bVar30 = ((uint)pcStack_204 & 0x80) != 0;
        bVar24 = ((uint)pcStack_204 & 0x40) != 0;
        bVar27 = ((uint)pcStack_204 & 0x10) != 0;
        bVar16 = ((uint)pcStack_204 & 4) != 0;
        bVar19 = ((uint)pcStack_204 & 1) != 0;
        in_ID = ((uint)pcStack_204 & 0x200000) != 0;
        in_AC = ((uint)pcStack_204 & 0x40000) != 0;
        in_VIP = 0;
        in_VIF = 0;
        pcStack_204 = (char *)0x402e6e;
        fVar38 = (float10)FUN_00415d3d();
        *(double *)(local_18 * 8 + 0x665020) = (double)fVar38;
      }
      pcStack_204 = (char *)0x402e87;
      fVar38 = (float10)FUN_00415c2c();
      pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)(bVar18 & 1) * 0x800 |
                             (uint)bVar20 * 0x400 | (uint)(in_IF & 1) * 0x200 |
                             (uint)(in_TF & 1) * 0x100 | (uint)(bVar30 & 1) * 0x80 |
                             (uint)(bVar24 & 1) * 0x40 | (uint)(bVar27 & 1) * 0x10 |
                             (uint)(bVar16 & 1) * 4 | (uint)(bVar19 & 1) |
                             (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 |
                             (uint)(in_VIF & 1) * 0x80000 | (uint)(in_AC & 1) * 0x40000);
      if (DAT_0043f89c == 0) {
        fVar38 = (float10)*(double *)(local_18 * 8 + 0x664fa8) / fVar38;
      }
      else {
        pcStack_208 = *(char **)(local_18 * 8 + 0x664fac);
        fVar38 = (float10)__adj_fdivr_m64(*(undefined4 *)(local_18 * 8 + 0x664fa8));
      }
      bVar25 = ((uint)pcStack_204 & 0x4000) != 0;
      bVar34 = ((uint)pcStack_204 & 0x800) != 0;
      uVar10 = (uint)pcStack_204 & 0x400;
      bVar32 = ((uint)pcStack_204 & 0x200) != 0;
      bVar30 = ((uint)pcStack_204 & 0x100) != 0;
      bVar27 = ((uint)pcStack_204 & 0x80) != 0;
      bVar24 = ((uint)pcStack_204 & 0x40) != 0;
      bVar19 = ((uint)pcStack_204 & 0x10) != 0;
      bVar18 = ((uint)pcStack_204 & 4) != 0;
      bVar16 = ((uint)pcStack_204 & 1) != 0;
      bVar35 = ((uint)pcStack_204 & 0x200000) != 0;
      bVar28 = ((uint)pcStack_204 & 0x40000) != 0;
      bVar33 = 0;
      bVar31 = 0;
      *(double *)(local_18 * 8 + 0x665038) =
           (double)(fVar38 - (float10)*(double *)(&DAT_00664f00 + local_18 * 8));
      pcStack_204 = (char *)0x402ed4;
      fVar38 = (float10)FUN_00415c62();
      *(double *)(local_18 * 8 + 0x665050) =
           (double)(fVar38 * (float10)*(double *)(local_18 * 8 + 0x664fa8) +
                   (float10)*(double *)(&DAT_00664f78 + local_18 * 8));
      pcStack_204 = (char *)((uint)(bVar25 & 1) * 0x4000 | (uint)(bVar34 & 1) * 0x800 |
                             (uint)(uVar10 != 0) * 0x400 | (uint)(bVar32 & 1) * 0x200 |
                             (uint)(bVar30 & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                             (uint)(bVar24 & 1) * 0x40 | (uint)(bVar19 & 1) * 0x10 |
                             (uint)(bVar18 & 1) * 4 | (uint)(bVar16 & 1) |
                             (uint)(bVar35 & 1) * 0x200000 | (uint)(bVar33 & 1) * 0x100000 |
                             (uint)(bVar31 & 1) * 0x80000 | (uint)(bVar28 & 1) * 0x40000);
      if (DAT_0043f89c != 0) {
        pcStack_208 = (char *)0x40000000;
        __adj_fdiv_m64(0);
      }
      bVar25 = ((uint)pcStack_204 & 0x4000) != 0;
      bVar34 = ((uint)pcStack_204 & 0x800) != 0;
      uVar10 = (uint)pcStack_204 & 0x400;
      bVar32 = ((uint)pcStack_204 & 0x200) != 0;
      bVar30 = ((uint)pcStack_204 & 0x100) != 0;
      bVar27 = ((uint)pcStack_204 & 0x80) != 0;
      bVar24 = ((uint)pcStack_204 & 0x40) != 0;
      bVar19 = ((uint)pcStack_204 & 0x10) != 0;
      bVar18 = ((uint)pcStack_204 & 4) != 0;
      bVar16 = ((uint)pcStack_204 & 1) != 0;
      bVar35 = ((uint)pcStack_204 & 0x200000) != 0;
      bVar28 = ((uint)pcStack_204 & 0x40000) != 0;
      bVar33 = 0;
      bVar31 = 0;
      pcStack_204 = (char *)0x402f21;
      fVar38 = (float10)FUN_00415c62();
      *(double *)(local_18 * 8 + 0x665068) =
           (double)(fVar38 * (float10)*(double *)(local_18 * 8 + 0x664fa8) +
                   (float10)*(double *)(&DAT_00664f78 + local_18 * 8));
      *(double *)(local_18 * 8 + 0x665080) =
           _DAT_00664e90 - *(double *)(&DAT_00664f18 + local_18 * 8) * 2.0;
      *(double *)(local_18 * 8 + 0x665098) =
           *(double *)(local_18 * 8 + 0x665080) * *(double *)(&DAT_00664f00 + local_18 * 8);
      *(double *)(local_18 * 8 + 0x6650b0) =
           *(double *)(&DAT_00664ee8 + local_18 * 8) * 2.0 + *(double *)(local_18 * 8 + 0x665098);
      pcStack_204 = (char *)(local_18 * 8 + 0x6650e8);
      pcStack_208 = (char *)(local_18 * 4 + 0x6650dc);
      thunk_FUN_004080cf(&DAT_00664f18 + local_18 * 8,local_18 * 4 + 0x6650cc);
      pcStack_204 = (char *)(local_18 * 8 + 0x665120);
      pcStack_208 = (char *)(local_18 * 4 + 0x665114);
      thunk_FUN_004080cf(local_18 * 8 + 0x665020,local_18 * 4 + 0x665104);
      pcStack_204 = (char *)(local_18 * 8 + 0x665158);
      pcStack_208 = (char *)(local_18 * 4 + 0x66514c);
      thunk_FUN_004080cf(local_18 * 8 + 0x665080,local_18 * 4 + 0x66513c);
      *(double *)(local_18 * 8 + 0x665170) =
           _DAT_00664ed8 - *(double *)(&DAT_00664f78 + local_18 * 8);
      pcStack_204 = (char *)((uint)(bVar25 & 1) * 0x4000 | (uint)(bVar34 & 1) * 0x800 |
                             (uint)(uVar10 != 0) * 0x400 | (uint)(bVar32 & 1) * 0x200 |
                             (uint)(bVar30 & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                             (uint)(bVar24 & 1) * 0x40 | (uint)(bVar19 & 1) * 0x10 |
                             (uint)(bVar18 & 1) * 4 | (uint)(bVar16 & 1) |
                             (uint)(bVar35 & 1) * 0x200000 | (uint)(bVar33 & 1) * 0x100000 |
                             (uint)(bVar31 & 1) * 0x80000 | (uint)(bVar28 & 1) * 0x40000);
      if (DAT_0043f89c == 0) {
        fVar38 = (float10)*(double *)(&DAT_00664ee8 + local_18 * 8) / (float10)2.0;
      }
      else {
        pcStack_208 = (char *)0x40000000;
        fVar38 = (float10)__adj_fdiv_m64(0);
      }
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
      if (DAT_0043f89c == 0) {
        fVar38 = (fVar38 * (float10)(double)CONCAT44(DAT_00441f2c,DAT_00441f28)) /
                 (float10)*(double *)(&DAT_00664f00 + local_18 * 8);
      }
      else {
        pcStack_208 = *(char **)(local_18 * 8 + 0x664f04);
        fVar38 = (float10)__adj_fdiv_m64(*(undefined4 *)(&DAT_00664f00 + local_18 * 8));
      }
      *(double *)(local_18 * 8 + 0x665188) = (double)(fVar38 + (float10)_DAT_00664ed8);
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
      if (DAT_0043f89c == 0) {
        fVar38 = (float10)*(double *)(&DAT_00664ee8 + local_18 * 8) / (float10)2.0;
      }
      else {
        pcStack_208 = (char *)0x40000000;
        fVar38 = (float10)__adj_fdiv_m64(0);
      }
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
      if (DAT_0043f89c == 0) {
        fVar38 = (fVar38 * (float10)(double)CONCAT44(DAT_00441f2c,DAT_00441f28)) /
                 (float10)*(double *)(&DAT_00664f00 + local_18 * 8);
      }
      else {
        pcStack_208 = *(char **)(local_18 * 8 + 0x664f04);
        fVar38 = (float10)__adj_fdiv_m64(*(undefined4 *)(&DAT_00664f00 + local_18 * 8));
      }
      pcVar11 = pcStack_204;
      in_NT = ((uint)pcStack_204 & 0x4000) != 0;
      in_IF = ((uint)pcStack_204 & 0x200) != 0;
      in_TF = ((uint)pcStack_204 & 0x100) != 0;
      in_ID = ((uint)pcStack_204 & 0x200000) != 0;
      in_AC = ((uint)pcStack_204 & 0x40000) != 0;
      in_VIP = 0;
      in_VIF = 0;
      *(double *)(local_18 * 8 + 0x6651a0) = (double)((float10)_DAT_00664ee0 - fVar38);
      *(double *)(local_18 * 8 + 0x6651b8) =
           *(double *)(&DAT_00664f78 + local_18 * 8) + _DAT_00664ee0;
      DAT_006651d8 = 2;
      DAT_006651dc = 1;
      (&DAT_006651dc)[local_18 * 2] = *(undefined4 *)(local_18 * 8 + 0x665174);
      (&DAT_006651d8)[local_18 * 2] = *(undefined4 *)(local_18 * 8 + 0x665170);
      for (; (*(double *)(&DAT_00655480 + DAT_006651dc * 2) <= *(double *)(local_18 * 8 + 0x665170)
             && (*(double *)(&DAT_00655480 + DAT_006651dc * 2) != 0.0));
          DAT_006651dc = DAT_006651dc + 1) {
      }
      for (; (iVar9 = DAT_006651dc, *(double *)(&DAT_00655480 + DAT_006651dc * 2) <= _DAT_00664ed8
             && (*(double *)(&DAT_00655480 + DAT_006651dc * 2) != 0.0));
          DAT_006651dc = DAT_006651dc + 1) {
        iVar14 = DAT_006651d8 * 3 + local_18;
        *(int *)((int)&DAT_006651c0 + iVar14 * 8 + 4) = (&DAT_00655484)[DAT_006651dc * 2];
        *(int *)(&DAT_006651c0 + iVar14) = (&DAT_00655480)[iVar9 * 2];
        DAT_006651d8 = DAT_006651d8 + 1;
      }
      iVar9 = DAT_006651d8 * 3 + local_18;
      *(undefined4 *)((int)&DAT_006651c0 + iVar9 * 8 + 4) = DAT_00664edc;
      *(undefined4 *)(&DAT_006651c0 + iVar9) = DAT_00664ed8;
      for (; (iVar9 = DAT_006651dc, DAT_006651d8 = DAT_006651d8 + 1,
             *(double *)(&DAT_00655480 + DAT_006651dc * 2) <= *(double *)(local_18 * 8 + 0x665188)
             && (*(double *)(&DAT_00655480 + DAT_006651dc * 2) != 0.0));
          DAT_006651dc = DAT_006651dc + 1) {
        iVar14 = DAT_006651d8 * 3 + local_18;
        *(int *)((int)&DAT_006651c0 + iVar14 * 8 + 4) = (&DAT_00655484)[DAT_006651dc * 2];
        *(int *)(&DAT_006651c0 + iVar14) = (&DAT_00655480)[iVar9 * 2];
      }
      iVar9 = DAT_006651d8 * 3 + local_18;
      *(undefined4 *)((int)&DAT_006651c0 + iVar9 * 8 + 4) = *(undefined4 *)(local_18 * 8 + 0x66518c)
      ;
      *(undefined4 *)(&DAT_006651c0 + iVar9) = *(undefined4 *)(local_18 * 8 + 0x665188);
      DAT_006651d8 = DAT_006651d8 + 1;
      iVar9 = DAT_006651d8 * 3 + local_18;
      *(undefined4 *)((int)&DAT_006651c0 + iVar9 * 8 + 4) = *(undefined4 *)(local_18 * 8 + 0x6651a4)
      ;
      *(undefined4 *)(&DAT_006651c0 + iVar9) = *(undefined4 *)(local_18 * 8 + 0x6651a0);
      DAT_006651d8 = DAT_006651d8 + 1;
      for (; (*(double *)(&DAT_00655480 + DAT_006651dc * 2) <= *(double *)(local_18 * 8 + 0x6651a0)
             && (*(double *)(local_18 * 8 + 0x665188) <=
                 *(double *)(&DAT_00655480 + DAT_006651dc * 2))); DAT_006651dc = DAT_006651dc + 1) {
      }
      for (; (iVar9 = DAT_006651dc, *(double *)(&DAT_00655480 + DAT_006651dc * 2) <= _DAT_00664ee0
             && (*(double *)(&DAT_00655480 + DAT_006651dc * 2) != 0.0));
          DAT_006651dc = DAT_006651dc + 1) {
        iVar14 = DAT_006651d8 * 3 + local_18;
        *(int *)((int)&DAT_006651c0 + iVar14 * 8 + 4) = (&DAT_00655484)[DAT_006651dc * 2];
        *(int *)(&DAT_006651c0 + iVar14) = (&DAT_00655480)[iVar9 * 2];
        DAT_006651d8 = DAT_006651d8 + 1;
      }
      iVar9 = DAT_006651d8 * 3 + local_18;
      *(undefined4 *)((int)&DAT_006651c0 + iVar9 * 8 + 4) = DAT_00664ee4;
      *(undefined4 *)(&DAT_006651c0 + iVar9) = DAT_00664ee0;
      for (; (iVar9 = DAT_006651dc, DAT_006651d8 = DAT_006651d8 + 1,
             *(double *)(&DAT_00655480 + DAT_006651dc * 2) <= *(double *)(local_18 * 8 + 0x6651b8)
             && (*(double *)(&DAT_00655480 + DAT_006651dc * 2) != 0.0));
          DAT_006651dc = DAT_006651dc + 1) {
        iVar14 = DAT_006651d8 * 3 + local_18;
        *(int *)((int)&DAT_006651c0 + iVar14 * 8 + 4) = (&DAT_00655484)[DAT_006651dc * 2];
        *(int *)(&DAT_006651c0 + iVar14) = (&DAT_00655480)[iVar9 * 2];
      }
      bVar16 = 0;
      *(int *)(local_18 * 4 + 0x693fdc) = DAT_006651d8;
      iVar9 = DAT_006651d8 * 3 + local_18;
      *(undefined4 *)((int)&DAT_006651c0 + iVar9 * 8 + 4) = *(undefined4 *)(local_18 * 8 + 0x6651bc)
      ;
      *(undefined4 *)(&DAT_006651c0 + iVar9) = *(undefined4 *)(local_18 * 8 + 0x6651b8);
      pcStack_204 = (char *)(&DAT_00693ff8 + local_18 * 2);
      pcStack_208 = (char *)(local_18 * 4 + 0x693fec);
      thunk_FUN_0040816c(local_18 * 8 + 0x665170);
      pcStack_204 = (char *)(local_18 * 8 + 0x694020);
      pcStack_208 = (char *)(local_18 * 4 + 0x694014);
      thunk_FUN_0040816c(local_18 * 8 + 0x665188);
      pcStack_204 = (char *)(local_18 * 8 + 0x694048);
      pcStack_208 = (char *)(local_18 * 4 + 0x69403c);
      thunk_FUN_0040816c(local_18 * 8 + 0x6651a0);
      pcStack_204 = (char *)(local_18 * 8 + 0x694070);
      pcStack_208 = (char *)(local_18 * 4 + 0x694064);
      thunk_FUN_0040816c(local_18 * 8 + 0x6651b8);
      local_18 = local_18 + 1;
    }