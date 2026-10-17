LAB_0040506f:
      in_VIP = 0;
      in_VIF = 0;
      local_18 = 1;
      for (local_f8 = 3; 0 < local_f8; local_f8 = local_f8 + -1) {
        if (local_18 == 1) {
          pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)bVar20 * 0x400 |
                                 (uint)(in_IF & 1) * 0x200 | (uint)(in_TF & 1) * 0x100 | 0x40 |
                                 (uint)(bVar16 & 1) * 0x10 | 4 | (uint)(in_ID & 1) * 0x200000 |
                                 (uint)(in_VIP & 1) * 0x100000 | (uint)(in_VIF & 1) * 0x80000 |
                                (uint)(in_AC & 1) * 0x40000);
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
          pcStack_204 = (char *)0x4050f3;
          fVar38 = (float10)FUN_00415c62();
          pcStack_204 = (char *)((uint)(bVar25 & 1) * 0x4000 | (uint)(bVar34 & 1) * 0x800 |
                                 (uint)(uVar10 != 0) * 0x400 | (uint)(bVar32 & 1) * 0x200 |
                                 (uint)(bVar30 & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                                 (uint)(bVar24 & 1) * 0x40 | (uint)(bVar19 & 1) * 0x10 |
                                 (uint)(bVar18 & 1) * 4 | (uint)(bVar16 & 1) |
                                 (uint)(bVar35 & 1) * 0x200000 | (uint)(bVar33 & 1) * 0x100000 |
                                 (uint)(bVar31 & 1) * 0x80000 | (uint)(bVar28 & 1) * 0x40000);
          if (DAT_0043f89c == 0) {
            fVar39 = (float10)(double)CONCAT44(DAT_00441f4c,DAT_00441f48) / (float10)2.0;
          }
          else {
            pcStack_208 = (char *)0x40000000;
            fVar39 = (float10)__adj_fdiv_m64(0);
            fVar38 = extraout_ST1_00;
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
          _DAT_0073ffb8 =
               (double)((((float10)DAT_006940b0 * (float10)1000.0 + fVar39 * fVar38 +
                         (float10)(double)CONCAT44(DAT_006940bc,DAT_006940b8)) -
                        (float10)DAT_00693ff0 * (float10)1000.0) - (float10)_DAT_00694000);
          pcStack_204 = (char *)0x40516e;
          FUN_00415c2c();
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
          pcStack_204 = (char *)0x4051c7;
          FUN_00415c62();
          pcStack_204 = (char *)0x4051da;
          fVar38 = (float10)FUN_00415c2c();
          pcStack_204 = (char *)((uint)(bVar25 & 1) * 0x4000 | (uint)(bVar34 & 1) * 0x800 |
                                 (uint)(uVar10 != 0) * 0x400 | (uint)(bVar32 & 1) * 0x200 |
                                 (uint)(bVar30 & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                                 (uint)(bVar24 & 1) * 0x40 | (uint)(bVar19 & 1) * 0x10 |
                                 (uint)(bVar18 & 1) * 4 | (uint)(bVar16 & 1) |
                                 (uint)(bVar35 & 1) * 0x200000 | (uint)(bVar33 & 1) * 0x100000 |
                                 (uint)(bVar31 & 1) * 0x80000 | (uint)(bVar28 & 1) * 0x40000);
          if (DAT_0043f89c == 0) {
            fVar39 = (fVar38 * (float10)(double)CONCAT44(DAT_00441f4c,DAT_00441f48)) / (float10)2.0;
            fVar38 = extraout_ST1_01;
          }
          else {
            pcStack_208 = (char *)0x40000000;
            fVar39 = (float10)__adj_fdiv_m64(0);
            fVar38 = extraout_ST1_02;
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
          _DAT_0073ffc0 =
               (double)(fVar39 + fVar38 + (float10)(double)CONCAT44(DAT_00441f8c,DAT_00441f88));
          pcStack_204 = (char *)0x40521d;
          FUN_00415c47();
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
          pcStack_204 = (char *)0x405276;
          FUN_00415c62();
          pcStack_204 = (char *)0x405289;
          fVar38 = (float10)FUN_00415c47();
          pcStack_204 = (char *)((uint)(bVar25 & 1) * 0x4000 | (uint)(bVar34 & 1) * 0x800 |
                                 (uint)(uVar10 != 0) * 0x400 | (uint)(bVar32 & 1) * 0x200 |
                                 (uint)(bVar30 & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                                 (uint)(bVar24 & 1) * 0x40 | (uint)(bVar19 & 1) * 0x10 |
                                 (uint)(bVar18 & 1) * 4 | (uint)(bVar16 & 1) |
                                 (uint)(bVar35 & 1) * 0x200000 | (uint)(bVar33 & 1) * 0x100000 |
                                 (uint)(bVar31 & 1) * 0x80000 | (uint)(bVar28 & 1) * 0x40000);
          if (DAT_0043f89c == 0) {
            fVar39 = (fVar38 * (float10)(double)CONCAT44(DAT_00441f4c,DAT_00441f48)) / (float10)2.0;
            fVar38 = extraout_ST1_03;
          }
          else {
            pcStack_208 = (char *)0x40000000;
            fVar39 = (float10)__adj_fdiv_m64(0);
            fVar38 = extraout_ST1_04;
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
          _DAT_0073ffc8 =
               (double)(fVar39 + fVar38 + (float10)(double)CONCAT44(DAT_00441f94,DAT_00441f90));
        }
        if (local_18 == 2) {
          _DAT_0073ffb8 =
               (double)((((float)DAT_006940b0 * 1000.0 +
                         (float)(double)CONCAT44(DAT_006940bc,DAT_006940b8)) -
                        (float)DAT_00693ff4 * 1000.0) - (float)_DAT_00694008);
          _DAT_0073ffc0 = (double)CONCAT44(DAT_00441f8c,DAT_00441f88);
          _DAT_0073ffc8 = (double)CONCAT44(DAT_00441f94,DAT_00441f90);
        }
        if (local_18 == 3) {
          pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)bVar20 * 0x400 |
                                 (uint)(in_IF & 1) * 0x200 | (uint)(in_TF & 1) * 0x100 | 0x40 |
                                 (uint)(bVar16 & 1) * 0x10 | 4 | (uint)(in_ID & 1) * 0x200000 |
                                 (uint)(in_VIP & 1) * 0x100000 | (uint)(in_VIF & 1) * 0x80000 |
                                (uint)(in_AC & 1) * 0x40000);
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
          pcStack_204 = (char *)0x405378;
          fVar38 = (float10)FUN_00415c62();
          pcStack_204 = (char *)((uint)(bVar25 & 1) * 0x4000 | (uint)(bVar34 & 1) * 0x800 |
                                 (uint)(uVar10 != 0) * 0x400 | (uint)(bVar32 & 1) * 0x200 |
                                 (uint)(bVar30 & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                                 (uint)(bVar24 & 1) * 0x40 | (uint)(bVar19 & 1) * 0x10 |
                                 (uint)(bVar18 & 1) * 4 | (uint)(bVar16 & 1) |
                                 (uint)(bVar35 & 1) * 0x200000 | (uint)(bVar33 & 1) * 0x100000 |
                                 (uint)(bVar31 & 1) * 0x80000 | (uint)(bVar28 & 1) * 0x40000);
          if (DAT_0043f89c == 0) {
            fVar39 = (float10)(double)CONCAT44(DAT_00441f4c,DAT_00441f48) / (float10)2.0;
          }
          else {
            pcStack_208 = (char *)0x40000000;
            fVar39 = (float10)__adj_fdiv_m64(0);
            fVar38 = extraout_ST1_05;
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
          _DAT_0073ffb8 =
               (double)(((((float10)DAT_006940b0 * (float10)1000.0 +
                          (float10)(double)CONCAT44(DAT_006940bc,DAT_006940b8)) - fVar39 * fVar38) -
                        (float10)DAT_00693ff8 * (float10)1000.0) - (float10)_DAT_00694010);
          pcStack_204 = (char *)0x4053f9;
          FUN_00415c2c();
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
          pcStack_204 = (char *)0x405452;
          FUN_00415c62();
          pcStack_204 = (char *)0x40545f;
          fVar38 = (float10)FUN_00415c2c();
          pcStack_204 = (char *)((uint)(bVar25 & 1) * 0x4000 | (uint)(bVar34 & 1) * 0x800 |
                                 (uint)(uVar10 != 0) * 0x400 | (uint)(bVar32 & 1) * 0x200 |
                                 (uint)(bVar30 & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                                 (uint)(bVar24 & 1) * 0x40 | (uint)(bVar19 & 1) * 0x10 |
                                 (uint)(bVar18 & 1) * 4 | (uint)(bVar16 & 1) |
                                 (uint)(bVar35 & 1) * 0x200000 | (uint)(bVar33 & 1) * 0x100000 |
                                 (uint)(bVar31 & 1) * 0x80000 | (uint)(bVar28 & 1) * 0x40000);
          if (DAT_0043f89c == 0) {
            fVar39 = (fVar38 * (float10)(double)CONCAT44(DAT_00441f4c,DAT_00441f48)) / (float10)2.0;
            fVar38 = extraout_ST1_06;
          }
          else {
            pcStack_208 = (char *)0x40000000;
            fVar39 = (float10)__adj_fdiv_m64(0);
            fVar38 = extraout_ST1_07;
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
          _DAT_0073ffc0 =
               (double)(fVar39 + fVar38 + (float10)(double)CONCAT44(DAT_00441f8c,DAT_00441f88));
          pcStack_204 = (char *)0x4054a8;
          FUN_00415c47();
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
          pcStack_204 = (char *)0x405501;
          FUN_00415c62();
          pcStack_204 = (char *)0x40550e;
          fVar38 = (float10)FUN_00415c47();
          pcStack_204 = (char *)((uint)(bVar25 & 1) * 0x4000 | (uint)(bVar34 & 1) * 0x800 |
                                 (uint)(uVar10 != 0) * 0x400 | (uint)(bVar32 & 1) * 0x200 |
                                 (uint)(bVar30 & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                                 (uint)(bVar24 & 1) * 0x40 | (uint)(bVar19 & 1) * 0x10 |
                                 (uint)(bVar18 & 1) * 4 | (uint)(bVar16 & 1) |
                                 (uint)(bVar35 & 1) * 0x200000 | (uint)(bVar33 & 1) * 0x100000 |
                                 (uint)(bVar31 & 1) * 0x80000 | (uint)(bVar28 & 1) * 0x40000);
          if (DAT_0043f89c == 0) {
            fVar39 = (fVar38 * (float10)(double)CONCAT44(DAT_00441f4c,DAT_00441f48)) / (float10)2.0;
            fVar38 = extraout_ST1_08;
          }
          else {
            pcStack_208 = (char *)0x40000000;
            fVar39 = (float10)__adj_fdiv_m64(0);
            fVar38 = extraout_ST1_09;
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
          _DAT_0073ffc8 =
               (double)(fVar39 + fVar38 + (float10)(double)CONCAT44(DAT_00441f94,DAT_00441f90));
        }
        _DAT_0073ffd0 = (double)CONCAT44(DAT_0073ff94,DAT_0073ff90) + _DAT_00441f98;
        pcStack_204 = (char *)0x405562;
        fVar38 = (float10)FUN_00415c2c();
        _DAT_0073ffd8 = (double)(fVar38 * (float10)_DAT_0073ffb8 + (float10)_DAT_0073ffc0);
        pcStack_204 = (char *)0x40557f;
        fVar38 = (float10)FUN_00415c47();
        _DAT_0073ffe0 = (double)(fVar38 * (float10)_DAT_0073ffb8 + (float10)_DAT_0073ffc8);
        local_104 = *(int *)(local_18 * 4 + 0x73828c);
        local_14 = 1;
        while (local_104 = local_104 + -1, 0 < local_104) {
          pcStack_204 = (char *)0x4055ee;
          fVar38 = (float10)FUN_00415c2c();
          *(double *)(&DAT_0073ffe0 + local_14 * 8) =
               (double)(fVar38 * (float10)*(double *)(&DAT_00694170 + (local_14 * 3 + local_18) * 2)
                       + (float10)_DAT_0073ffd8);
          pcStack_204 = (char *)0x405619;
          fVar38 = (float10)FUN_00415c47();
          *(double *)(local_14 * 8 + 0x74f9e0) =
               (double)(fVar38 * (float10)*(double *)(&DAT_00694170 + (local_14 * 3 + local_18) * 2)
                       + (float10)_DAT_0073ffe0);
          local_14 = local_14 + 1;
        }
        local_110 = *(int *)(local_18 * 4 + 0x73828c);
        local_14 = 1;
        while (local_110 = local_110 + -1, 0 < local_110) {
          pcStack_204 = (char *)0x40569b;
          fVar38 = (float10)FUN_00415c2c();
          *(double *)(local_14 * 8 + 0x75f3e0) =
               (double)(fVar38 * (float10)*(double *)((local_14 * 3 + local_18) * 8 + 0x6c2f70) +
                       (float10)*(double *)(&DAT_0073ffe0 + local_14 * 8));
          pcStack_204 = (char *)0x4056ca;
          fVar38 = (float10)FUN_00415c47();
          *(double *)(local_14 * 8 + 0x76ede0) =
               (double)(fVar38 * (float10)*(double *)((local_14 * 3 + local_18) * 8 + 0x6c2f70) +
                       (float10)*(double *)(local_14 * 8 + 0x74f9e0));
          local_14 = local_14 + 1;
        }
        pcStack_204 = (char *)0x4056fe;
        fVar38 = (float10)FUN_00415c2c();
        _DAT_0077e7e8 = (double)(fVar38 * (float10)_DAT_0073ffb8 + (float10)_DAT_0073ffc0);
        pcStack_204 = (char *)0x40571b;
        fVar38 = (float10)FUN_00415c47();
        _DAT_0077e7f0 = (double)(fVar38 * (float10)_DAT_0073ffb8 + (float10)_DAT_0073ffc8);
        DAT_006651dc = *(int *)(local_18 * 4 + 0x73828c);
        DAT_0077e7f8 = 0;
        local_14 = DAT_006651dc;
        for (local_11c = (*(int *)(local_18 * 4 + 0x6940dc) - DAT_006651dc) + 2; 0 < local_11c;
            local_11c = local_11c + -1) {
          _DAT_0077e800 = _DAT_0073ffb8 - *(double *)(&DAT_00694170 + (local_14 * 3 + local_18) * 2)
          ;
          DAT_0077e7f8 = DAT_0077e7f8 + 1;
          pcStack_204 = (char *)0x4057c6;
          fVar38 = (float10)FUN_00415c2c();
          _DAT_0077e808 = (double)(fVar38 * (float10)_DAT_0077e800 + (float10)_DAT_0073ffc0);
          pcStack_204 = (char *)0x4057e3;
          fVar38 = (float10)FUN_00415c47();
          _DAT_0077e810 = (double)(fVar38 * (float10)_DAT_0077e800 + (float10)_DAT_0073ffc8);
          pcStack_204 = (char *)0x405800;
          fVar38 = (float10)FUN_00415c2c();
          *(double *)(&DAT_0077e810 + DAT_0077e7f8 * 8) =
               (double)(fVar38 * (float10)*(double *)((local_14 * 3 + local_18) * 8 + 0x6c2f70) +
                       (float10)_DAT_0077e808);
          pcStack_204 = (char *)0x40582d;
          fVar38 = (float10)FUN_00415c47();
          *(double *)(DAT_0077e7f8 * 8 + 0x78e210) =
               (double)(fVar38 * (float10)*(double *)((local_14 * 3 + local_18) * 8 + 0x6c2f70) +
                       (float10)_DAT_0077e810);
          local_14 = local_14 + 1;
        }
        pcStack_204 = (char *)0x40585f;
        fVar38 = (float10)FUN_00415c2c();
        _DAT_0079dc18 =
             (double)((float10)(double)CONCAT44(DAT_00441f8c,DAT_00441f88) -
                     fVar38 * (float10)_DAT_00664ec0);
        pcStack_204 = (char *)0x40587c;
        fVar38 = (float10)FUN_00415c47();
        _DAT_0079dc20 =
             (double)((float10)(double)CONCAT44(DAT_00441f94,DAT_00441f90) -
                     fVar38 * (float10)_DAT_00664ec0);
        pcStack_204 = (char *)0x405899;
        fVar38 = (float10)FUN_00415c2c();
        _DAT_0079dc28 =
             (double)(fVar38 * (float10)(double)CONCAT44(DAT_00441f2c,DAT_00441f28) +
                     (float10)_DAT_0079dc18);
        pcStack_204 = (char *)0x4058b6;
        fVar38 = (float10)FUN_00415c47();
        _DAT_0079dc30 =
             (double)(fVar38 * (float10)(double)CONCAT44(DAT_00441f2c,DAT_00441f28) +
                     (float10)_DAT_0079dc20);
        bVar19 = 0;
        bVar30 = 0;
        bVar27 = (int)DAT_00441ed4 < 0;
        bVar24 = (POPCOUNT(DAT_00441ed4 & 0xff) & 1U) == 0;
        bVar18 = 0;
        if (DAT_00441ed4 == 0) {
          pcStack_204 = (char *)0x0;
          pcStack_208 = (char *)0x0;
          FUN_00412670(6,s_(3X,'center_CORDINATION_of_circl_00439a6c,0xffffffff,0);
          pcStack_204 = (char *)DAT_0079dc2c;
          pcStack_208 = DAT_0079dc28;
          FUN_00411d60();
          pcStack_204 = (char *)DAT_0079dc34;
          pcStack_208 = DAT_0079dc30;
          FUN_00411d60();
          bVar19 = (undefined1 *)0xfffffff7 < &pcStack_208;
          bVar30 = SCARRY4((int)&pcStack_208,8);
          bVar27 = (int)&stack0xfffffe00 < 0;
          bVar18 = &stack0x00000000 == (undefined1 *)0x200;
          bVar24 = 1;
          pcStack_204 = (char *)0x405919;
          FUN_00412850();
        }
        DAT_0079dc3c = DAT_00441f6c;
        DAT_0079dc38 = DAT_00441f68;
        pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)(bVar30 & 1) * 0x800 |
                               (uint)bVar20 * 0x400 | (uint)(in_IF & 1) * 0x200 |
                               (uint)(in_TF & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                               (uint)(bVar18 & 1) * 0x40 | (uint)(bVar16 & 1) * 0x10 |
                               (uint)(bVar24 & 1) * 4 | (uint)(bVar19 & 1) |
                               (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 |
                               (uint)(in_VIF & 1) * 0x80000 | (uint)(in_AC & 1) * 0x40000);
        if (DAT_0043f89c != 0) {
          pcStack_208 = DAT_00441f6c;
          __adj_fdiv_m64(DAT_00441f68);
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
        pcStack_204 = (char *)0x405981;
        DAT_0079dc40 = __ftol();
        fVar4 = (float)(double)CONCAT44(DAT_0079dc3c,DAT_0079dc38) -
                (((float)*(int *)(local_18 * 4 + 0x694014) * 1000.0 +
                 (float)*(double *)(local_18 * 8 + 0x694020)) -
                (float)DAT_0079dc40 * (float)(double)CONCAT44(DAT_0079dc3c,DAT_0079dc38));
        _DAT_0079dc48 = (double)fVar4;
        fVar5 = (float)*(int *)(local_18 * 4 + 0x694014) * 1000.0 +
                (float)*(double *)(local_18 * 8 + 0x694020);
        _DAT_0079dc50 = (double)fVar5;
        _DAT_0079dc58 = (double)(fVar5 + fVar4);
        pcStack_204 = (char *)((uint)(bVar25 & 1) * 0x4000 | (uint)(bVar34 & 1) * 0x800 |
                               (uint)(uVar10 != 0) * 0x400 | (uint)(bVar32 & 1) * 0x200 |
                               (uint)(bVar30 & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                               (uint)(bVar24 & 1) * 0x40 | (uint)(bVar19 & 1) * 0x10 |
                               (uint)(bVar18 & 1) * 4 | (uint)(bVar16 & 1) |
                               (uint)(bVar35 & 1) * 0x200000 | (uint)(bVar33 & 1) * 0x100000 |
                               (uint)(bVar31 & 1) * 0x80000 | (uint)(bVar28 & 1) * 0x40000);
        if (DAT_0043f89c == 0) {
          fVar38 = (float10)fVar4 / (float10)(double)CONCAT44(DAT_00441f2c,DAT_00441f28);
        }
        else {
          pcStack_208 = DAT_00441f2c;
          fVar38 = (float10)__adj_fdiv_m64(DAT_00441f28);
        }
        _DAT_0079dc60 = (double)fVar38;
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
          fVar38 = (float10)(double)CONCAT44(DAT_0079dc3c,DAT_0079dc38) /
                   (float10)(double)CONCAT44(DAT_00441f2c,DAT_00441f28);
        }
        else {
          pcStack_208 = DAT_00441f2c;
          fVar38 = (float10)__adj_fdiv_m64(DAT_00441f28);
        }
        _DAT_0079dc68 = (double)fVar38;
        _DAT_0079dc70 =
             (double)((((float)*(int *)(local_18 * 4 + 0x69403c) * 1000.0 +
                       (float)*(double *)(local_18 * 8 + 0x694048)) -
                      (float)*(int *)(local_18 * 4 + 0x694014) * 1000.0) -
                     (float)*(double *)(local_18 * 8 + 0x694020));
        *(char **)(local_18 * 8 + 0x79dc74) = DAT_00441f2c;
        *(char **)(&DAT_0079dc70 + local_18 * 8) = DAT_00441f28;
        DAT_0079dc94 = DAT_0079dc3c;
        DAT_0079dc90 = DAT_0079dc38;
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
          pcStack_208 = DAT_0079dc3c;
          __adj_fdiv_m64(DAT_0079dc38);
        }
        bVar24 = ((uint)pcStack_204 & 0x4000) != 0;
        uVar10 = (uint)pcStack_204 & 0x400;
        bVar19 = ((uint)pcStack_204 & 0x200) != 0;
        bVar18 = ((uint)pcStack_204 & 0x100) != 0;
        bVar16 = ((uint)pcStack_204 & 0x10) != 0;
        bVar34 = ((uint)pcStack_204 & 0x200000) != 0;
        bVar27 = ((uint)pcStack_204 & 0x40000) != 0;
        bVar32 = 0;
        bVar30 = 0;
        pcStack_204 = (char *)0x405b23;
        DAT_0079dc98 = __ftol();
        if (DAT_0073ffa0 == 8) {
          _DAT_0079dc60 = -_DAT_0079dc60;
          _DAT_0079dc68 = -_DAT_0079dc68;
        }
        iVar9 = *(int *)(local_18 * 4 + 0x73828c);
        DAT_0079dc9c = iVar9 - 1;
        _DAT_0079dca4 = *(undefined4 *)(DAT_0079dc9c * 8 + 0x76ede4);
        _DAT_0079dca0 = *(undefined4 *)(DAT_0079dc9c * 8 + 0x76ede0);
        _DAT_0079dcac = DAT_0079dc34;
        _DAT_0079dca8 = DAT_0079dc30;
        _DAT_0079dcb4 = *(undefined4 *)(DAT_0079dc9c * 8 + 0x75f3e4);
        _DAT_0079dcb0 = *(undefined4 *)(DAT_0079dc9c * 8 + 0x75f3e0);
        _DAT_0079dcbc = DAT_0079dc2c;
        _DAT_0079dcb8 = DAT_0079dc28;
        _DAT_0079dcc0 = (double)CONCAT44(_DAT_0079dca4,_DAT_0079dca0) - _DAT_0079dc30;
        _DAT_0079dcc8 = (double)CONCAT44(_DAT_0079dcb4,_DAT_0079dcb0) - _DAT_0079dc28;
        DAT_0073ff90 = 0x60000000;
        DAT_0073ff94 = 0x400921fb;
        _DAT_0079dcd0 = 4.71238911151886;
        DAT_0079dcdc = 0x400921fb;
        uVar12 = 0x6000;
        DAT_0079dcd8 = 0x60000000;
        pcStack_204 = (char *)((uint)(bVar24 & 1) * 0x4000 | (uint)SBORROW4(iVar9,1) * 0x800 |
                               (uint)(uVar10 != 0) * 0x400 | (uint)(bVar19 & 1) * 0x200 |
                               (uint)(bVar18 & 1) * 0x100 | (uint)((int)DAT_0079dc9c < 0) * 0x80 |
                               (uint)(DAT_0079dc9c == 0) * 0x40 | (uint)(bVar16 & 1) * 0x10 |
                               (uint)((POPCOUNT(DAT_0079dc9c & 0xff) & 1U) == 0) * 4 |
                               (uint)(DAT_0073ffa0 < 8) | (uint)(bVar34 & 1) * 0x200000 |
                               (uint)(bVar32 & 1) * 0x100000 | (uint)(bVar30 & 1) * 0x80000 |
                              (uint)(bVar27 & 1) * 0x40000);
        if (DAT_0043f89c == 0) {
          fVar38 = (float10)3.1415927410125732 / (float10)2.0;
        }
        else {
          pcStack_208 = (char *)0x40000000;
          fVar38 = (float10)__adj_fdiv_m64(0);
          uVar12 = extraout_var;
        }
        in_NT = ((uint)pcStack_204 & 0x4000) != 0;
        bVar21 = ((uint)pcStack_204 & 0x800) != 0;
        bVar20 = ((uint)pcStack_204 & 0x400) != 0;
        in_IF = ((uint)pcStack_204 & 0x200) != 0;
        in_TF = ((uint)pcStack_204 & 0x100) != 0;
        in_ID = ((uint)pcStack_204 & 0x200000) != 0;
        in_AC = ((uint)pcStack_204 & 0x40000) != 0;
        in_VIP = 0;
        in_VIF = 0;
        _DAT_0079dce0 = (double)fVar38;
        DAT_0073ff98 = 0;
        DAT_0073ff9c = 0;
        pcVar11 = (char *)((uint)CONCAT21(uVar12,0.0 < _DAT_0079dcc0) << 8);
        if (0.0 < _DAT_0079dcc0) {
          bVar22 = 0.0 < _DAT_0079dcc8;
          pcVar11 = (char *)CONCAT22(uVar12,(ushort)bVar22 << 8 | (ushort)NAN(_DAT_0079dcc8) << 10 |
                                            (ushort)(_DAT_0079dcc8 == 0.0) << 0xe);
          if (!bVar22) goto LAB_00405c9b;
          pcStack_204 = (char *)((uint)in_NT * 0x4000 | (uint)bVar21 * 0x800 | (uint)bVar20 * 0x400
                                 | (uint)in_IF * 0x200 | (uint)in_TF * 0x100 |
                                 (uint)((_DAT_0079dcc8 == 0.0) != 0) * 0x40 |
                                 (uint)(NAN(_DAT_0079dcc8) != 0) * 4 | (uint)bVar22 |
                                 (uint)in_ID * 0x200000 | (uint)in_AC * 0x40000);
          if (DAT_0043f89c != 0) {
            pcStack_208 = pcVar11;
            FUN_00423257();
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
          pcStack_204 = (char *)0x405e5a;
          fVar38 = (float10)FUN_00415d3d();
          _DAT_0079dce8 = (double)fVar38;
        }
        else {