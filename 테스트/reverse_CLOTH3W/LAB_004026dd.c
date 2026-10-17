LAB_004026dd:
    pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)bVar20 * 0x400 |
                           (uint)(in_IF & 1) * 0x200 | (uint)(in_TF & 1) * 0x100 |
                           (uint)bVar21 * 0x80 | (uint)bVar22 * 0x40 | (uint)(bVar16 & 1) * 0x10 |
                           (uint)bVar23 * 4 | (uint)(in_ID & 1) * 0x200000 |
                           (uint)(in_VIP & 1) * 0x100000 | (uint)(in_VIF & 1) * 0x80000 |
                          (uint)(in_AC & 1) * 0x40000);
    if (DAT_0043f89c == 0) {
      fVar38 = ((float10)(double)CONCAT44(DAT_00441f74,DAT_00441f70) -
               (float10)(double)CONCAT44(DAT_00441f64,DAT_00441f60)) /
               (float10)(double)CONCAT44(DAT_00441f6c,DAT_00441f68);
    }
    else {
      pcStack_208 = DAT_00441f6c;
      fVar38 = (float10)__adj_fdiv_m64(DAT_00441f68);
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
    _DAT_00655468 = (double)(fVar38 + (float10)1.0);
    pcStack_204 = (char *)0x402735;
    DAT_00655470 = __ftol();
    uVar7 = DAT_00645a64;
    DAT_00655474 = 1;
    DAT_00655478 = 2;
    _DAT_0065547c = 0;
    *(undefined4 *)(&DAT_00645a68 + DAT_00645a64) = 0;
    *(undefined4 *)((int)&DAT_00645a68 + uVar7 * 8 + 4) = 0x4197d784;
    DAT_00655480 = 1;
    local_14 = 1;
    for (local_6c = DAT_00655470; 0 < local_6c; local_6c = local_6c + -1) {
      if (DAT_00655478 == 8) {
        DAT_00655484 = (local_14 - _DAT_0065547c) + -1;
        *(double *)(&DAT_00655480 + local_14 * 2) =
             (double)DAT_00655484 * (double)CONCAT44(DAT_00441f6c,DAT_00441f68) +
             (double)CONCAT44(DAT_00441f64,DAT_00441f60);
        DAT_00655478 = 2;
      }
      else {
        *(double *)(&DAT_00655480 + local_14 * 2) =
             (double)(DAT_00655480 + -1) * (double)CONCAT44(DAT_00441f6c,DAT_00441f68) +
             (double)CONCAT44(DAT_00441f64,DAT_00441f60);
      }
      iVar9 = DAT_00655474;
      bVar16 = 0;
      if (*(double *)(DAT_00655474 * 8 + 0x645a60) < *(double *)(&DAT_00655480 + local_14 * 2)) {
        (&DAT_00655484)[local_14 * 2] = (&DAT_00645a64)[DAT_00655474 * 2];
        (&DAT_00655480)[local_14 * 2] = *(undefined4 *)(iVar9 * 8 + 0x645a60);
        DAT_00655474 = DAT_00655474 + 1;
        _DAT_0065547c = _DAT_0065547c + 1;
        DAT_00655478 = 8;
        DAT_00655480 = DAT_00655480 + -1;
      }
      DAT_00655480 = DAT_00655480 + 1;
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(0xffff7b30,0,0,0);
      pcStack_204 = (char *)(&DAT_00655484)[local_14 * 2];
      pcStack_208 = (char *)(&DAT_00655480)[local_14 * 2];
      FUN_00412940();
      pcStack_204 = (char *)0x4028cc;
      FUN_00412850();
      local_14 = local_14 + 1;
    }
    _DAT_00664e88 = local_18 - 1;
    pcStack_204 = (char *)((uint)(bVar24 & 1) * 0x4000 | (uint)SBORROW4(local_18,1) * 0x800 |
                           (uint)(uVar10 != 0) * 0x400 | (uint)(bVar19 & 1) * 0x200 |
                           (uint)(bVar18 & 1) * 0x100 | (uint)((int)_DAT_00664e88 < 0) * 0x80 |
                           (uint)(_DAT_00664e88 == 0) * 0x40 | (uint)(bVar16 & 1) * 0x10 |
                           (uint)((POPCOUNT(_DAT_00664e88 & 0xff) & 1U) == 0) * 4 |
                           (uint)(bVar34 & 1) * 0x200000 | (uint)(bVar32 & 1) * 0x100000 |
                           (uint)(bVar30 & 1) * 0x80000 | (uint)(bVar27 & 1) * 0x40000);
    if (DAT_0043f89c == 0) {
      fVar38 = (float10)(double)CONCAT44(DAT_00441f5c,DAT_00441f58) / (float10)180.0;
    }
    else {
      pcStack_208 = (char *)0x40668000;
      fVar38 = (float10)__adj_fdiv_m64(0);
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
    _DAT_00664e90 = (double)(fVar38 * (float10)3.1415927410125732);
    pcStack_204 = (char *)0x40291b;
    DAT_00664e98 = __ftol();
    _DAT_00664ea0 = (double)DAT_00664e98;
    _DAT_00664ea8 = ((double)CONCAT44(DAT_00441f5c,DAT_00441f58) - (double)DAT_00664e98) * 100.0;
    pcStack_204 = (char *)0x40294e;
    DAT_00664eb0 = __ftol();
    _DAT_00664eb8 = (_DAT_00664ea8 - (double)DAT_00664eb0) * 100.0;
    pcStack_204 = (char *)((uint)(bVar25 & 1) * 0x4000 | (uint)(bVar34 & 1) * 0x800 |
                           (uint)(uVar10 != 0) * 0x400 | (uint)(bVar32 & 1) * 0x200 |
                           (uint)(bVar30 & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                           (uint)(bVar24 & 1) * 0x40 | (uint)(bVar19 & 1) * 0x10 |
                           (uint)(bVar18 & 1) * 4 | (uint)(bVar16 & 1) |
                           (uint)(bVar35 & 1) * 0x200000 | (uint)(bVar33 & 1) * 0x100000 |
                           (uint)(bVar31 & 1) * 0x80000 | (uint)(bVar28 & 1) * 0x40000);
    if (DAT_0043f89c == 0) {
      fVar38 = (float10)DAT_00664eb0 / (float10)60.0;
    }
    else {
      pcStack_208 = (char *)0x42700000;
      fVar38 = (float10)__adj_fdiv_m32();
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
      fVar39 = (float10)_DAT_00664eb8 / (float10)3600.0;
    }
    else {
      pcStack_208 = (char *)0x40ac2000;
      fVar39 = (float10)__adj_fdiv_m64(0);
      fVar38 = extraout_ST1;
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
      fVar38 = ((fVar39 + fVar38 + (float10)_DAT_00664ea0) *
               (float10)(double)CONCAT44(DAT_0043907c,DAT_00439078)) / (float10)180.0;
    }
    else {
      pcStack_208 = (char *)0x40668000;
      fVar38 = (float10)__adj_fdiv_m64(0);
    }
    _DAT_00664e90 = (double)fVar38;
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
    pcStack_204 = (char *)0x402a30;
    fVar38 = (float10)FUN_00415c62();
    _DAT_00664ec0 = (double)(fVar38 * (float10)(double)CONCAT44(DAT_00441f2c,DAT_00441f28));
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
    pcStack_204 = (char *)0x402a6b;
    fVar38 = (float10)FUN_00415c2c();
    pcStack_204 = (char *)((uint)(bVar25 & 1) * 0x4000 | (uint)(bVar34 & 1) * 0x800 |
                           (uint)(uVar10 != 0) * 0x400 | (uint)(bVar32 & 1) * 0x200 |
                           (uint)(bVar30 & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                           (uint)(bVar24 & 1) * 0x40 | (uint)(bVar19 & 1) * 0x10 |
                           (uint)(bVar18 & 1) * 4 | (uint)(bVar16 & 1) |
                           (uint)(bVar35 & 1) * 0x200000 | (uint)(bVar33 & 1) * 0x100000 |
                           (uint)(bVar31 & 1) * 0x80000 | (uint)(bVar28 & 1) * 0x40000);
    if (DAT_0043f89c == 0) {
      fVar38 = (float10)1.0 / fVar38;
    }
    else {
      pcStack_208 = (char *)0x3ff00000;
      fVar38 = (float10)__adj_fdivr_m64(0);
    }
    in_NT = ((uint)pcStack_204 & 0x4000) != 0;
    in_IF = ((uint)pcStack_204 & 0x200) != 0;
    in_TF = ((uint)pcStack_204 & 0x100) != 0;
    bVar16 = ((uint)pcStack_204 & 0x10) != 0;
    in_ID = ((uint)pcStack_204 & 0x200000) != 0;
    in_AC = ((uint)pcStack_204 & 0x40000) != 0;
    in_VIP = 0;
    in_VIF = 0;
    _DAT_00664ec8 =
         (double)(fVar38 * (float10)(double)CONCAT44(DAT_00441f2c,DAT_00441f28) -
                 (float10)(double)CONCAT44(DAT_00441f2c,DAT_00441f28));
    _DAT_00664ed0 = _DAT_00664e90 * (double)CONCAT44(DAT_00441f2c,DAT_00441f28);
    _DAT_00664ed8 = (double)CONCAT44(DAT_00441f54,DAT_00441f50) - _DAT_00664ec0;
    _DAT_00664ee0 = _DAT_00664ed8 + _DAT_00664ed0;
    local_18 = 1;
    pcVar11 = pcStack_204;
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
    pcStack_204 = (char *)&DAT_00694098;
    pcStack_208 = (char *)&DAT_00694090;
    thunk_FUN_0040816c(&DAT_00664ed8);
    pcStack_204 = (char *)&DAT_006940a8;
    pcStack_208 = (char *)&DAT_006940a0;
    thunk_FUN_0040816c(&DAT_00664ee0);
    pcStack_204 = (char *)&DAT_006940b8;
    pcStack_208 = (char *)&DAT_006940b0;
    thunk_FUN_0040816c(&DAT_00441f50);
    if (DAT_00441ed4 != 1) {
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_00439080,0xffffffff,0);
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,s_(7X,'IP_NO._=_',I5,/,4X,80('='),_004390c0,0xffffffff,0);
      pcStack_204 = (char *)DAT_00441f20;
      pcStack_208 = (char *)0x40361e;
      FUN_00411da0();
      pcStack_204 = DAT_00441f2c;
      pcStack_208 = DAT_00441f28;
      FUN_00411d60();
      pcStack_204 = (char *)DAT_00441f34;
      pcStack_208 = DAT_00441f30;
      FUN_00411d60();
      pcStack_204 = (char *)DAT_00664e98;
      pcStack_208 = (char *)0x403654;
      FUN_00411da0();
      pcStack_204 = (char *)DAT_00664eb0;
      pcStack_208 = (char *)0x403662;
      FUN_00411da0();
      pcStack_204 = (char *)DAT_00664ebc;
      pcStack_208 = DAT_00664eb8;
      FUN_00411d60();
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,s_(7X,'D_=',F9.3,'_m',13X,'A"_=',F_0043912c,0xffffffff,0);
      pcStack_204 = (char *)DAT_00441f4c;
      pcStack_208 = DAT_00441f48;
      FUN_00411d60();
      pcStack_204 = (char *)DAT_00441f44;
      pcStack_208 = DAT_00441f40;
      FUN_00411d60();
      pcStack_204 = (char *)DAT_00441f3c;
      pcStack_208 = DAT_00441f38;
      FUN_00411d60();
      pcStack_204 = (char *)DAT_00664ec4;
      pcStack_208 = DAT_00664ec0;
      FUN_00411d60();
      pcStack_204 = (char *)DAT_00664ed4;
      pcStack_208 = DAT_00664ed0;
      FUN_00411d60();
      pcStack_204 = (char *)DAT_00664ecc;
      pcStack_208 = DAT_00664ec8;
      FUN_00411d60();
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,s_(7X,'IP_=',I3,'_Km',F10.4,8X,'BC_004391ac,0xffffffff,0);
      pcStack_204 = (char *)DAT_006940b0;
      pcStack_208 = (char *)0x403734;
      FUN_00411da0();
      pcStack_204 = (char *)DAT_006940bc;
      pcStack_208 = DAT_006940b8;
      FUN_00411d60();
      pcStack_204 = (char *)DAT_00694090;
      pcStack_208 = (char *)0x403756;
      FUN_00411da0();
      pcStack_204 = (char *)DAT_0069409c;
      pcStack_208 = DAT_00694098;
      FUN_00411d60();
      pcStack_204 = (char *)DAT_006940a0;
      pcStack_208 = (char *)0x403778;
      FUN_00411da0();
      pcStack_204 = (char *)DAT_006940ac;
      pcStack_208 = DAT_006940a8;
      FUN_00411d60();
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,s_(4X,80('='),/,T33,'OUTSIDE',T54,_004391f8,0xffffffff,0);
      local_18 = 1;
      for (local_7c = 3; 0 < local_7c; local_7c = local_7c + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x664f04);
        pcStack_208 = *(char **)(&DAT_00664f00 + local_18 * 8);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_00439268,0xffffffff,0);
      local_18 = 1;
      for (local_80 = 3; 0 < local_80; local_80 = local_80 + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x664eec);
        pcStack_208 = *(char **)(&DAT_00664ee8 + local_18 * 8);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_004392a0,0xffffffff,0);
      local_18 = 1;
      for (local_84 = 3; 0 < local_84; local_84 = local_84 + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x664f64);
        pcStack_208 = *(char **)(&DAT_00664f60 + local_18 * 8);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_004392d8,0xffffffff,0);
      local_18 = 1;
      for (local_88 = 3; 0 < local_88; local_88 = local_88 + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x664f34);
        pcStack_208 = *(char **)(&DAT_00664f30 + local_18 * 8);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_00439310,0xffffffff,0);
      local_18 = 1;
      for (local_8c = 3; 0 < local_8c; local_8c = local_8c + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x664f4c);
        pcStack_208 = *(char **)(&DAT_00664f48 + local_18 * 8);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,s_(4X,80('-'),/,9X,'THETA_',T28,I3_00439348,0xffffffff,0);
      local_18 = 1;
      for (local_90 = 3; 0 < local_90; local_90 = local_90 + -1) {
        pcStack_204 = *(char **)(local_18 * 4 + 0x6650cc);
        pcStack_208 = (char *)0x4039d3;
        FUN_00411da0();
        pcStack_204 = *(char **)(local_18 * 4 + 0x6650dc);
        pcStack_208 = (char *)0x4039e5;
        FUN_00411da0();
        pcStack_204 = *(char **)(local_18 * 8 + 0x6650ec);
        pcStack_208 = *(char **)(local_18 * 8 + 0x6650e8);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_004393ac,0xffffffff,0);
      local_18 = 1;
      for (local_94 = 3; 0 < local_94; local_94 = local_94 + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x664f7c);
        pcStack_208 = *(char **)(&DAT_00664f78 + local_18 * 8);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_004393e4,0xffffffff,0);
      local_18 = 1;
      for (local_98 = 3; 0 < local_98; local_98 = local_98 + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x664fac);
        pcStack_208 = *(char **)(local_18 * 8 + 0x664fa8);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_0043941c,0xffffffff,0);
      local_18 = 1;
      for (local_9c = 3; 0 < local_9c; local_9c = local_9c + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x664f94);
        pcStack_208 = *(char **)(local_18 * 8 + 0x664f90);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,s_(4X,80('-'),/,9X,'TAU_',T28,I3,'_00439454,0xffffffff,0);
      local_18 = 1;
      for (local_a0 = 3; 0 < local_a0; local_a0 = local_a0 + -1) {
        pcStack_204 = *(char **)(local_18 * 4 + 0x665104);
        pcStack_208 = (char *)0x403b97;
        FUN_00411da0();
        pcStack_204 = *(char **)(local_18 * 4 + 0x665114);
        pcStack_208 = (char *)0x403ba9;
        FUN_00411da0();
        pcStack_204 = *(char **)(local_18 * 8 + 0x665124);
        pcStack_208 = *(char **)(local_18 * 8 + 0x665120);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_004394b8,0xffffffff,0);
      local_18 = 1;
      for (local_a4 = 3; 0 < local_a4; local_a4 = local_a4 + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x664fdc);
        pcStack_208 = *(char **)(local_18 * 8 + 0x664fd8);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_004394f0,0xffffffff,0);
      local_18 = 1;
      for (local_a8 = 3; 0 < local_a8; local_a8 = local_a8 + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x66500c);
        pcStack_208 = *(char **)(local_18 * 8 + 0x665008);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_00439528,0xffffffff,0);
      local_18 = 1;
      for (local_ac = 3; 0 < local_ac; local_ac = local_ac + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x664ff4);
        pcStack_208 = *(char **)(local_18 * 8 + 0x664ff0);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_00439560,0xffffffff,0);
      local_18 = 1;
      for (local_b0 = 3; 0 < local_b0; local_b0 = local_b0 + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x66503c);
        pcStack_208 = *(char **)(local_18 * 8 + 0x665038);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_00439598,0xffffffff,0);
      local_18 = 1;
      for (local_b4 = 3; 0 < local_b4; local_b4 = local_b4 + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x665054);
        pcStack_208 = *(char **)(local_18 * 8 + 0x665050);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_004395d0,0xffffffff,0);
      local_18 = 1;
      for (local_b8 = 3; 0 < local_b8; local_b8 = local_b8 + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x66506c);
        pcStack_208 = *(char **)(local_18 * 8 + 0x665068);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,s_(4X,80('-'),/,9X,'SIGMA_',T28,I3_00439608,0xffffffff,0);
      local_18 = 1;
      for (local_bc = 3; 0 < local_bc; local_bc = local_bc + -1) {
        pcStack_204 = *(char **)(local_18 * 4 + 0x66513c);
        pcStack_208 = (char *)0x403e93;
        FUN_00411da0();
        pcStack_204 = *(char **)(local_18 * 4 + 0x66514c);
        pcStack_208 = (char *)0x403ea5;
        FUN_00411da0();
        pcStack_204 = *(char **)(local_18 * 8 + 0x66515c);
        pcStack_208 = *(char **)(local_18 * 8 + 0x665158);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_0043966c,0xffffffff,0);
      local_18 = 1;
      for (local_c0 = 3; 0 < local_c0; local_c0 = local_c0 + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x66509c);
        pcStack_208 = *(char **)(local_18 * 8 + 0x665098);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_004396a4,0xffffffff,0);
      local_18 = 1;
      for (local_c4 = 3; 0 < local_c4; local_c4 = local_c4 + -1) {
        pcStack_204 = *(char **)(local_18 * 8 + 0x6650b4);
        pcStack_208 = *(char **)(local_18 * 8 + 0x6650b0);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_004396dc,0xffffffff,0);
      local_18 = 1;
      for (local_c8 = 3; 0 < local_c8; local_c8 = local_c8 + -1) {
        pcStack_204 = *(char **)(local_18 * 4 + 0x693fec);
        pcStack_208 = (char *)0x403fef;
        FUN_00411da0();
        pcStack_204 = *(char **)(local_18 * 8 + 0x693ffc);
        pcStack_208 = (char *)(&DAT_00693ff8)[local_18 * 2];
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_0043972c,0xffffffff,0);
      local_18 = 1;
      for (local_cc = 3; 0 < local_cc; local_cc = local_cc + -1) {
        pcStack_204 = *(char **)(local_18 * 4 + 0x694014);
        pcStack_208 = (char *)0x404069;
        FUN_00411da0();
        pcStack_204 = *(char **)(local_18 * 8 + 0x694024);
        pcStack_208 = *(char **)(local_18 * 8 + 0x694020);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,&DAT_0043977c,0xffffffff,0);
      local_18 = 1;
      for (local_d0 = 3; 0 < local_d0; local_d0 = local_d0 + -1) {
        pcStack_204 = *(char **)(local_18 * 4 + 0x69403c);
        pcStack_208 = (char *)0x4040e3;
        FUN_00411da0();
        pcStack_204 = *(char **)(local_18 * 8 + 0x69404c);
        pcStack_208 = *(char **)(local_18 * 8 + 0x694048);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(6,s_(4X,80('-'),/,9X,'E.T.C_',6X,I4,_004397cc,0xffffffff,0);
      local_18 = 1;
      for (local_d4 = 3; 0 < local_d4; local_d4 = local_d4 + -1) {
        pcStack_204 = *(char **)(local_18 * 4 + 0x694064);
        pcStack_208 = (char *)0x40415d;
        FUN_00411da0();
        pcStack_204 = *(char **)(local_18 * 8 + 0x694074);
        pcStack_208 = *(char **)(local_18 * 8 + 0x694070);
        FUN_00411d60();
        local_18 = local_18 + 1;
      }
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(0xffff7b30,s_(A\)(A\)_DO_YOU_WANT_UNIT_DISTRI_0043982c,4,0);
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(0xffff7b30,s_(A\)(A\)_DO_YOU_WANT_UNIT_DISTRI_0043982c + 4,4,0);
      pcStack_204 = (char *)0x2a;
      pcStack_208 = s_(A\)(A\)_DO_YOU_WANT_UNIT_DISTRI_0043982c + 8;
      FUN_00411e80();
      pcStack_204 = "j";
      FUN_00412850();
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00415940(0xffff7f18,&DAT_00439860,0xffffffff,0,0);
      pcStack_204 = (char *)0xa;
      pcStack_208 = &DAT_006940c0;
      FUN_004123a0();
      pcStack_204 = (char *)0x404202;
      FUN_00415bb0();
      pcStack_204 = (char *)0x1;
      pcStack_208 = &DAT_00439864;
      cVar8 = FUN_00414280(&DAT_006940c0,10);
      if (cVar8 == '\0') {
        pcStack_204 = (char *)0x1;
        pcStack_208 = &DAT_00439868;
        cVar8 = FUN_00414280(&DAT_006940c0,10);
        if (cVar8 == '\0') {
          pcStack_204 = (char *)0x0;
          pcStack_208 = (char *)0x0;
          FUN_00412670(0xffff7b30,s_(A\)_END_OF_CALCULATION_0043986c,4,0);
          pcStack_204 = (char *)0x1a;
          pcStack_208 = s_(A\)_END_OF_CALCULATION_0043986c + 4;
          FUN_00411e80();
          pcStack_204 = (char *)0x404276;
          FUN_00412850();
          DAT_00441ed4 = 1;
          goto LAB_00401fa8;
        }
      }
    }
    local_18 = 1;
    for (local_e0 = 3; 0 < local_e0; local_e0 = local_e0 + -1) {
      if (local_18 == 1) {
        pcStack_204 = (char *)0x7;
        pcStack_208 = (char *)0x1;
        FUN_00413b00(&DAT_006940d0,1,10,s_OUTSIDE_0043988c);
      }
      if (local_18 == 2) {
        pcStack_204 = (char *)0x6;
        pcStack_208 = (char *)0x1;
        FUN_00413b00(&DAT_006940d0,1,10,s_CENTER_00439894);
      }
      if (local_18 == 3) {
        pcStack_204 = (char *)0x6;
        pcStack_208 = (char *)0x1;
        FUN_00413b00(&DAT_006940d0,1,10,s_INSIDE_0043989c);
      }
      if (DAT_00441ed4 == 0) {
        pcStack_204 = (char *)0x0;
        pcStack_208 = (char *)0x0;
        FUN_00412670(6,s_('',/,/,/,/,/,/,/,/,T24,'UNIT_DI_004398a4,0xffffffff,0);
        pcStack_204 = (char *)DAT_00441f20;
        pcStack_208 = (char *)0x404362;
        FUN_00411da0();
        pcStack_204 = (char *)0xa;
        pcStack_208 = &DAT_006940d0;
        FUN_00411e80();
        pcStack_204 = "j";
        FUN_00412850();
        pcStack_204 = (char *)0x0;
        pcStack_208 = (char *)0x0;
        FUN_00412670(6,s_(80('='),/,3X,'R_=',F9.3,'_m',14_00439908,0xffffffff,0);
        pcStack_204 = *(char **)(local_18 * 8 + 0x664f04);
        pcStack_208 = *(char **)(&DAT_00664f00 + local_18 * 8);
        FUN_00411d60();
        pcStack_204 = *(char **)(local_18 * 8 + 0x664eec);
        pcStack_208 = *(char **)(&DAT_00664ee8 + local_18 * 8);
        FUN_00411d60();
        pcStack_204 = *(char **)(local_18 * 8 + 0x664f4c);
        pcStack_208 = *(char **)(&DAT_00664f48 + local_18 * 8);
        FUN_00411d60();
        pcStack_204 = (char *)0x4043e6;
        FUN_00412850();
      }
      pcStack_204 = (char *)0x0;
      pcStack_208 = (char *)0x0;
      FUN_00412670(0xffff7b30,&DAT_004399a8,0xffffffff,0);
      pcStack_204 = *(char **)(local_18 * 4 + 0x693fdc);
      pcStack_208 = (char *)0x404414;
      FUN_00411da0();
      pcStack_204 = (char *)0x40441c;
      FUN_00412850();
      local_ec = *(int *)(local_18 * 4 + 0x693fdc);
      local_20 = 1;
      for (; 0 < local_ec; local_ec = local_ec + -1) {
        if (*(int *)(local_18 * 4 + 0x693fdc) == local_20) {
          *(int *)(local_18 * 4 + 0x6940dc) = local_20 + -1;
        }
        if (((double)(&DAT_006651c0)[local_20 * 3 + local_18] < _DAT_00664ed8) ||
           (_DAT_00664ee0 < (double)(&DAT_006651c0)[local_20 * 3 + local_18])) {
          iVar9 = local_20 * 3 + local_18;
          _DAT_006940f4 = *(undefined4 *)((int)&DAT_006651c0 + iVar9 * 8 + 4);
          _DAT_006940f0 = *(undefined4 *)(&DAT_006651c0 + iVar9);
          if ((double)(&DAT_006651c0)[local_20 * 3 + local_18] < _DAT_00664ed8) {
            _DAT_006940fc = *(undefined4 *)(local_18 * 8 + 0x665174);
            _DAT_006940f8 = *(undefined4 *)(local_18 * 8 + 0x665170);
          }
          bVar16 = SCARRY4(local_20 * 3,local_18);
          if (_DAT_00664ee0 < (double)(&DAT_006651c0)[local_20 * 3 + local_18]) {
            _DAT_006940fc = *(undefined4 *)(local_18 * 8 + 0x6651bc);
            _DAT_006940f8 = *(undefined4 *)(local_18 * 8 + 0x6651b8);
          }
          pcStack_204 = &DAT_00664f18 + local_18 * 8;
          pcStack_208 = &DAT_00664ee8 + local_18 * 8;
          thunk_FUN_00408871(&DAT_006940f8,&DAT_006940f0,&DAT_00694100,&DAT_00694108,&DAT_00694110,
                             &DAT_00694118);
          if ((double)CONCAT44(_DAT_00694114,_DAT_00694110) < 9.999999717180685e-10) {
            _DAT_00694110 = 0xe0000000;
            _DAT_00694114 = 0x3e112e0b;
          }
          dVar3 = (double)CONCAT44(DAT_0069411c,DAT_00694118);
          bVar18 = NAN(dVar3);
          bVar19 = dVar3 < 0.0;
          bVar24 = dVar3 == 0.0;
          bVar30 = 0;
          bVar27 = 0;
          if ((bool)bVar24) {
            DAT_00694118 = 0xe0000000;
            DAT_0069411c = (char *)0x3e112e0b;
          }
          pcStack_204 = (char *)0x40460e;
          fVar38 = (float10)FUN_00415c11();
          pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)(bVar16 & 1) * 0x800 |
                                 (uint)bVar20 * 0x400 | (uint)(in_IF & 1) * 0x200 |
                                 (uint)(in_TF & 1) * 0x100 | (uint)(bVar30 & 1) * 0x80 |
                                 (uint)(bVar24 & 1) * 0x40 | (uint)(bVar27 & 1) * 0x10 |
                                 (uint)(bVar18 & 1) * 4 | (uint)(bVar19 & 1) |
                                 (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 |
                                 (uint)(in_VIF & 1) * 0x80000 | (uint)(in_AC & 1) * 0x40000);
          if (DAT_0043f89c == 0) {
            fVar38 = fVar38 / (float10)(double)CONCAT44(DAT_0069411c,DAT_00694118);
          }
          else {
            pcStack_208 = DAT_0069411c;
            fVar38 = (float10)__adj_fdiv_m64(DAT_00694118);
          }
          bVar19 = ((uint)pcStack_204 & 0x4000) != 0;
          bVar21 = ((uint)pcStack_204 & 0x400) != 0;
          bVar18 = ((uint)pcStack_204 & 0x200) != 0;
          bVar16 = ((uint)pcStack_204 & 0x100) != 0;
          bVar20 = ((uint)pcStack_204 & 0x10) != 0;
          bVar27 = ((uint)pcStack_204 & 0x200000) != 0;
          bVar24 = ((uint)pcStack_204 & 0x40000) != 0;
          _DAT_00694120 = (double)fVar38;
          if (local_18 == 1) {
            pcStack_204 = (char *)((uint)bVar19 * 0x4000 | (uint)bVar21 * 0x400 |
                                   (uint)bVar18 * 0x200 | (uint)bVar16 * 0x100 | 0x40 |
                                   (uint)bVar20 * 0x10 | 4 | (uint)bVar27 * 0x200000 |
                                  (uint)bVar24 * 0x40000);
            if (DAT_0043f89c == 0) {
              fVar38 = (float10)(double)CONCAT44(DAT_00441f4c,DAT_00441f48) / (float10)2.0;
            }
            else {
              pcStack_208 = (char *)0x40000000;
              fVar38 = (float10)__adj_fdiv_m64(0);
            }
            bVar19 = ((uint)pcStack_204 & 0x4000) != 0;
            bVar30 = ((uint)pcStack_204 & 0x800) != 0;
            bVar21 = ((uint)pcStack_204 & 0x400) != 0;
            bVar18 = ((uint)pcStack_204 & 0x200) != 0;
            bVar16 = ((uint)pcStack_204 & 0x100) != 0;
            bVar27 = ((uint)pcStack_204 & 0x200000) != 0;
            bVar24 = ((uint)pcStack_204 & 0x40000) != 0;
            _DAT_00694128 = (double)(fVar38 - (float10)(double)CONCAT44(DAT_0069410c,DAT_00694108));
          }
          else {
            bVar30 = SBORROW4(local_18,2);
            uVar10 = local_18 - 2;
            if (uVar10 == 0) {
              _DAT_00694128 = (double)CONCAT44(DAT_0069410c,DAT_00694108);
            }
            else {
              pcStack_204 = (char *)((uint)bVar19 * 0x4000 | (uint)bVar30 * 0x800 |
                                     (uint)bVar21 * 0x400 | (uint)bVar18 * 0x200 |
                                     (uint)bVar16 * 0x100 | (uint)((int)uVar10 < 0) * 0x80 |
                                     (uint)(uVar10 == 0) * 0x40 | (uint)bVar20 * 0x10 |
                                     (uint)((POPCOUNT(uVar10 & 0xff) & 1U) == 0) * 4 |
                                     (uint)(local_18 < 2) | (uint)bVar27 * 0x200000 |
                                    (uint)bVar24 * 0x40000);
              if (DAT_0043f89c == 0) {
                fVar38 = (float10)(double)CONCAT44(DAT_00441f4c,DAT_00441f48) / (float10)2.0;
              }
              else {
                pcStack_208 = (char *)0x40000000;
                fVar38 = (float10)__adj_fdiv_m64(0);
              }
              bVar19 = ((uint)pcStack_204 & 0x4000) != 0;
              bVar30 = ((uint)pcStack_204 & 0x800) != 0;
              bVar21 = ((uint)pcStack_204 & 0x400) != 0;
              bVar18 = ((uint)pcStack_204 & 0x200) != 0;
              bVar16 = ((uint)pcStack_204 & 0x100) != 0;
              bVar27 = ((uint)pcStack_204 & 0x200000) != 0;
              bVar24 = ((uint)pcStack_204 & 0x40000) != 0;
              _DAT_00694128 =
                   (double)(fVar38 + (float10)(double)CONCAT44(DAT_0069410c,DAT_00694108));
            }
          }
        }
        else {
          if ((double)(&DAT_006651c0)[local_20 * 3 + local_18] <=
              *(double *)(local_18 * 8 + 0x665188)) {
            _DAT_00694134 = DAT_00664edc;
            _DAT_00694130 = DAT_00664ed8;
          }
          if (*(double *)(local_18 * 8 + 0x6651a0) <=
              (double)(&DAT_006651c0)[local_20 * 3 + local_18]) {
            _DAT_00694134 = DAT_00664ee4;
            _DAT_00694130 = DAT_00664ee0;
          }
          iVar9 = local_20 * 3 + local_18;
          _DAT_006940f4 = *(undefined4 *)((int)&DAT_006651c0 + iVar9 * 8 + 4);
          _DAT_006940f0 = *(undefined4 *)(&DAT_006651c0 + iVar9);
          _DAT_0069413c = *(undefined4 *)(local_18 * 8 + 0x66518c);
          _DAT_00694138 = *(undefined4 *)(local_18 * 8 + 0x665188);
          _DAT_00694144 = *(undefined4 *)(local_18 * 8 + 0x6651a4);
          _DAT_00694140 = *(undefined4 *)(local_18 * 8 + 0x6651a0);
          pcStack_204 = &DAT_00694150;
          pcStack_208 = &DAT_00694148;
          thunk_FUN_00408b48(&DAT_00694138,&DAT_00694140,&DAT_006940f0,&DAT_00694130,&DAT_00441f28,
                             local_18 * 8 + 0x664fa8,&DAT_00664f78 + local_18 * 8,
                             &DAT_00664f18 + local_18 * 8,&DAT_00664ee8 + local_18 * 8,&DAT_00694110
                             ,&DAT_00694100,&DAT_00694108);
          bVar16 = 0;
          if ((double)CONCAT44(_DAT_00694114,_DAT_00694110) < 9.999999717180685e-10) {
            _DAT_00694110 = 0xe0000000;
            _DAT_00694114 = 0x3e112e0b;
          }
          bVar18 = local_18 == 0;
          bVar30 = SBORROW4(local_18,1);
          uVar10 = local_18 - 1;
          bVar27 = (int)uVar10 < 0;
          bVar24 = uVar10 == 0;
          bVar19 = (POPCOUNT(uVar10 & 0xff) & 1U) == 0;
          if ((bool)bVar24) {
            pcStack_204 = (char *)0x40484e;
            fVar38 = (float10)FUN_00415c2c();
            pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)(bVar30 & 1) * 0x800 |
                                   (uint)bVar20 * 0x400 | (uint)(in_IF & 1) * 0x200 |
                                   (uint)(in_TF & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                                   (uint)(bVar24 & 1) * 0x40 | (uint)(bVar16 & 1) * 0x10 |
                                   (uint)(bVar19 & 1) * 4 | (uint)(bVar18 & 1) |
                                   (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 |
                                   (uint)(in_VIF & 1) * 0x80000 | (uint)(in_AC & 1) * 0x40000);
            if (DAT_0043f89c == 0) {
              fVar38 = (float10)(double)CONCAT44(DAT_0069410c,DAT_00694108) / fVar38;
            }
            else {
              pcStack_208 = DAT_0069410c;
              fVar38 = (float10)__adj_fdivr_m64(DAT_00694108);
            }
            bVar19 = ((uint)pcStack_204 & 0x4000) != 0;
            bVar30 = ((uint)pcStack_204 & 0x800) != 0;
            bVar21 = ((uint)pcStack_204 & 0x400) != 0;
            bVar18 = ((uint)pcStack_204 & 0x200) != 0;
            bVar16 = ((uint)pcStack_204 & 0x100) != 0;
            bVar27 = ((uint)pcStack_204 & 0x200000) != 0;
            bVar24 = ((uint)pcStack_204 & 0x40000) != 0;
            _DAT_00694128 =
                 (double)(((float10)_DAT_00694148 -
                          (float10)(double)CONCAT44(DAT_00441f2c,DAT_00441f28)) - fVar38);
          }
          else {
            pcStack_204 = (char *)0x404896;
            fVar38 = (float10)FUN_00415c2c();
            pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)(bVar30 & 1) * 0x800 |
                                   (uint)bVar20 * 0x400 | (uint)(in_IF & 1) * 0x200 |
                                   (uint)(in_TF & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                                   (uint)(bVar24 & 1) * 0x40 | (uint)(bVar16 & 1) * 0x10 |
                                   (uint)(bVar19 & 1) * 4 | (uint)(bVar18 & 1) |
                                   (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 |
                                   (uint)(in_VIF & 1) * 0x80000 | (uint)(in_AC & 1) * 0x40000);
            if (DAT_0043f89c == 0) {
              fVar38 = (float10)(double)CONCAT44(DAT_0069410c,DAT_00694108) / fVar38;
            }
            else {
              pcStack_208 = DAT_0069410c;
              fVar38 = (float10)__adj_fdivr_m64(DAT_00694108);
            }
            bVar19 = ((uint)pcStack_204 & 0x4000) != 0;
            bVar30 = ((uint)pcStack_204 & 0x800) != 0;
            bVar21 = ((uint)pcStack_204 & 0x400) != 0;
            bVar18 = ((uint)pcStack_204 & 0x200) != 0;
            bVar16 = ((uint)pcStack_204 & 0x100) != 0;
            bVar27 = ((uint)pcStack_204 & 0x200000) != 0;
            bVar24 = ((uint)pcStack_204 & 0x40000) != 0;
            _DAT_00694128 =
                 (double)(((float10)(double)CONCAT44(DAT_00441f2c,DAT_00441f28) -
                          (float10)_DAT_00694148) + fVar38);
          }
        }
        bVar35 = 0;
        bVar33 = 0;
        dVar3 = (double)CONCAT44(_DAT_00694114,_DAT_00694110);
        bVar32 = NAN(dVar3);
        bVar34 = dVar3 < 9.999999717180685e-10;
        bVar25 = dVar3 == 9.999999717180685e-10;
        bVar31 = 0;
        bVar28 = 0;
        if ((bool)bVar34) {
          _DAT_00694110 = 0xe0000000;
          _DAT_00694114 = 0x3e112e0b;
        }
        pcStack_204 = (char *)0x404902;
        fVar38 = (float10)FUN_00415c47();
        pcStack_204 = (char *)((uint)(bVar19 & 1) * 0x4000 | (uint)(bVar30 & 1) * 0x800 |
                               (uint)bVar21 * 0x400 | (uint)(bVar18 & 1) * 0x200 |
                               (uint)(bVar16 & 1) * 0x100 | (uint)(bVar31 & 1) * 0x80 |
                               (uint)(bVar25 & 1) * 0x40 | (uint)(bVar28 & 1) * 0x10 |
                               (uint)(bVar32 & 1) * 4 | (uint)(bVar34 & 1) |
                               (uint)(bVar27 & 1) * 0x200000 | (uint)(bVar35 & 1) * 0x100000 |
                               (uint)(bVar33 & 1) * 0x80000 | (uint)(bVar24 & 1) * 0x40000);
        if (DAT_0043f89c == 0) {
          fVar38 = (float10)1.0 / fVar38;
        }
        else {
          pcStack_208 = (char *)0x3ff00000;
          fVar38 = (float10)__adj_fdivr_m64(0);
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
        _DAT_00694158 = (double)(fVar38 * (float10)(double)CONCAT44(DAT_0069410c,DAT_00694108));
        pcStack_204 = (char *)0x40493d;
        fVar38 = (float10)FUN_00415c62();
        pcStack_204 = (char *)((uint)(bVar25 & 1) * 0x4000 | (uint)(bVar34 & 1) * 0x800 |
                               (uint)(uVar10 != 0) * 0x400 | (uint)(bVar32 & 1) * 0x200 |
                               (uint)(bVar30 & 1) * 0x100 | (uint)(bVar27 & 1) * 0x80 |
                               (uint)(bVar24 & 1) * 0x40 | (uint)(bVar19 & 1) * 0x10 |
                               (uint)(bVar18 & 1) * 4 | (uint)(bVar16 & 1) |
                               (uint)(bVar35 & 1) * 0x200000 | (uint)(bVar33 & 1) * 0x100000 |
                               (uint)(bVar31 & 1) * 0x80000 | (uint)(bVar28 & 1) * 0x40000);
        if (DAT_0043f89c == 0) {
          fVar38 = (float10)1.0 / fVar38;
        }
        else {
          pcStack_208 = (char *)0x3ff00000;
          fVar38 = (float10)__adj_fdivr_m64(0);
        }
        in_NT = ((uint)pcStack_204 & 0x4000) != 0;
        bVar20 = ((uint)pcStack_204 & 0x400) != 0;
        in_IF = ((uint)pcStack_204 & 0x200) != 0;
        in_TF = ((uint)pcStack_204 & 0x100) != 0;
        in_ID = ((uint)pcStack_204 & 0x200000) != 0;
        in_AC = ((uint)pcStack_204 & 0x40000) != 0;
        in_VIP = 0;
        in_VIF = 0;
        _DAT_00694160 =
             (double)((float10)(double)CONCAT44(DAT_00694104,DAT_00694100) -
                     fVar38 * (float10)(double)CONCAT44(DAT_0069410c,DAT_00694108));
        pcStack_204 = (char *)&DAT_00694170;
        pcStack_208 = (char *)&DAT_00694168;
        thunk_FUN_0040816c(&DAT_006940f0);
        pcStack_204 = (char *)&DAT_00694180;
        pcStack_208 = (char *)&DAT_0069417c;
        thunk_FUN_004080cf(&DAT_00694110,&DAT_00694178);
        _DAT_00694188 =
             (*(double *)(local_18 * 8 + 0x665170) - _DAT_00665180) +
             (double)CONCAT44(DAT_00694104,DAT_00694100);
        iVar9 = local_20 * 3 + local_18;
        (&DAT_00694174)[iVar9 * 2] = DAT_00694104;
        (&DAT_00694170)[iVar9 * 2] = DAT_00694100;
        iVar9 = local_20 * 3 + local_18;
        *(char **)(iVar9 * 8 + 0x6c2f74) = DAT_0069410c;
        *(char **)(iVar9 * 8 + 0x6c2f70) = DAT_00694108;
        *(int *)((local_20 * 3 + local_18) * 4 + 0x6f1d80) = DAT_00694168;
        iVar9 = local_20 * 3 + local_18;
        *(undefined4 *)(iVar9 * 8 + 0x709474) = DAT_00694174;
        *(char **)(iVar9 * 8 + 0x709470) = DAT_00694170;
        if (*(double *)(local_18 * 8 + 0x665188) == (double)CONCAT44(_DAT_006940f4,_DAT_006940f0)) {
          *(int *)(local_18 * 4 + 0x73828c) = local_20 + 1;
        }
        bVar16 = 0;
        if (*(double *)(local_18 * 8 + 0x665188) == (double)CONCAT44(_DAT_006940f4,_DAT_006940f0)) {
          if (DAT_00441ed4 == 0) {
            pcStack_204 = (char *)0x0;
            pcStack_208 = (char *)0x0;
            FUN_00412670(6,s_(I3,'+',F7.3,F11.3,F10.3,2F11.3,_004399ac,0xffffffff,0);
            pcStack_204 = (char *)DAT_00694168;
            pcStack_208 = (char *)0x404aae;
            FUN_00411da0();
            pcStack_204 = (char *)DAT_00694174;
            pcStack_208 = DAT_00694170;
            FUN_00411d60();
            pcStack_204 = (char *)DAT_00694104;
            pcStack_208 = DAT_00694100;
            FUN_00411d60();
            pcStack_204 = DAT_0069410c;
            pcStack_208 = DAT_00694108;
            FUN_00411d60();
            pcStack_204 = (char *)DAT_0069415c;
            pcStack_208 = DAT_00694158;
            FUN_00411d60();
            pcStack_204 = (char *)DAT_00694164;
            pcStack_208 = DAT_00694160;
            FUN_00411d60();
            pcStack_204 = (char *)DAT_0069412c;
            pcStack_208 = DAT_00694128;
            FUN_00411d60();
            pcStack_204 = (char *)DAT_00694178;
            pcStack_208 = (char *)0x404b34;
            FUN_00411da0();
            pcStack_204 = (char *)DAT_0069417c;
            pcStack_208 = (char *)0x404b42;
            FUN_00411da0();
            pcStack_204 = (char *)DAT_00694184;
            pcStack_208 = DAT_00694180;
            FUN_00411d60();
            pcStack_204 = (char *)0x404b5e;
            FUN_00412850();
          }
        }
        else if (DAT_00441ed4 == 0) {
          pcStack_204 = (char *)0x0;
          pcStack_208 = (char *)0x0;
          FUN_00412670(6,s_(I3,'+',F7.3,F11.3,F10.3,2F11.3,_004399f4,0xffffffff,0);
          pcStack_204 = (char *)DAT_00694168;
          pcStack_208 = (char *)0x404b97;
          FUN_00411da0();
          pcStack_204 = (char *)DAT_00694174;
          pcStack_208 = DAT_00694170;
          FUN_00411d60();
          pcStack_204 = (char *)DAT_00694104;
          pcStack_208 = DAT_00694100;
          FUN_00411d60();
          pcStack_204 = DAT_0069410c;
          pcStack_208 = DAT_00694108;
          FUN_00411d60();
          pcStack_204 = (char *)DAT_0069415c;
          pcStack_208 = DAT_00694158;
          FUN_00411d60();
          pcStack_204 = (char *)DAT_00694164;
          pcStack_208 = DAT_00694160;
          FUN_00411d60();
          pcStack_204 = (char *)DAT_0069412c;
          pcStack_208 = DAT_00694128;
          FUN_00411d60();
          pcStack_204 = (char *)DAT_00694178;
          pcStack_208 = (char *)0x404c1d;
          FUN_00411da0();
          pcStack_204 = (char *)DAT_0069417c;
          pcStack_208 = (char *)0x404c2b;
          FUN_00411da0();
          pcStack_204 = (char *)DAT_00694184;
          pcStack_208 = DAT_00694180;
          FUN_00411d60();
          pcStack_204 = (char *)0x404c47;
          FUN_00412850();
        }
        local_20 = local_20 + 1;
      }
      *(int *)(local_18 * 4 + 0x6940dc) = local_20;
      local_18 = local_18 + 1;
    }
    if (DAT_00441ed4 == 1) {