LAB_00404ce1:
      DAT_00439078 = 0x60000000;
      DAT_0043907c = 0x400921fb;
      DAT_0073ff94 = 0x400921fb;
      DAT_0073ff90 = 0x60000000;
      DAT_0073ff98 = 0;
      DAT_0073ff9c = 0;
      DAT_0073ffa0 = 0;
      if (_DAT_00441f98 < 0.0) {
        _DAT_00441f98 = _DAT_00441f98 + 360.0;
      }
      bVar21 = NAN(_DAT_00441fa0);
      bVar22 = _DAT_00441fa0 < 0.0;
      bVar23 = _DAT_00441fa0 == 0.0;
      if (bVar22) {
        _DAT_00441fa0 = _DAT_00441f98 + 360.0;
      }
      pcStack_204 = (char *)((uint)(in_NT & 1) * 0x4000 | (uint)bVar20 * 0x400 |
                             (uint)(in_IF & 1) * 0x200 | (uint)(in_TF & 1) * 0x100 |
                             (uint)bVar23 * 0x40 | (uint)bVar21 * 4 | (uint)bVar22 |
                             (uint)(in_ID & 1) * 0x200000 | (uint)(in_VIP & 1) * 0x100000 |
                             (uint)(in_VIF & 1) * 0x80000 | (uint)(in_AC & 1) * 0x40000);
      if (DAT_0043f89c == 0) {
        fVar38 = (float10)_DAT_00441f98 / (float10)180.0;
      }
      else {
        pcStack_208 = (char *)0x40668000;
        fVar38 = (float10)__adj_fdiv_m64(0);
      }
      _DAT_00441f98 = (double)(fVar38 * (float10)(double)CONCAT44(DAT_0043907c,DAT_00439078));
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
        fVar38 = (float10)_DAT_00441fa0 / (float10)180.0;
      }
      else {
        pcStack_208 = (char *)0x40668000;
        fVar38 = (float10)__adj_fdiv_m64(0);
      }
      bVar26 = ((uint)pcStack_204 & 0x4000) != 0;
      bVar23 = ((uint)pcStack_204 & 0x800) != 0;
      bVar22 = ((uint)pcStack_204 & 0x400) != 0;
      bVar21 = ((uint)pcStack_204 & 0x200) != 0;
      bVar20 = ((uint)pcStack_204 & 0x100) != 0;
      bVar36 = ((uint)pcStack_204 & 0x200000) != 0;
      bVar29 = ((uint)pcStack_204 & 0x40000) != 0;
      _DAT_00441fa0 = (double)(fVar38 * (float10)(double)CONCAT44(DAT_0043907c,DAT_00439078));
      if ((_DAT_00441f98 <= (double)CONCAT44(DAT_0073ff9c,DAT_0073ff98)) ||
         ((double)CONCAT44(DAT_0073ff94,DAT_0073ff90) <= _DAT_00441f98)) {
        _DAT_0073ffa8 = _DAT_00441f98 - (double)CONCAT44(DAT_0073ff94,DAT_0073ff90);
        bVar37 = NAN(_DAT_00441fa0) || NAN(_DAT_00441f98);
        bVar17 = _DAT_00441fa0 == _DAT_00441f98;
        bVar15 = false;
        if (_DAT_00441fa0 < _DAT_00441f98) {
          bVar37 = NAN(_DAT_00441fa0) || NAN(_DAT_0073ffa8);
          bVar15 = _DAT_00441fa0 < _DAT_0073ffa8;
          bVar17 = _DAT_00441fa0 == _DAT_0073ffa8;
          if (_DAT_0073ffa8 < _DAT_00441fa0) {
            pcStack_204 = (char *)((uint)bVar26 * 0x4000 | (uint)bVar23 * 0x800 |
                                   (uint)bVar22 * 0x400 | (uint)bVar21 * 0x200 |
                                   (uint)bVar20 * 0x100 | (uint)bVar17 * 0x40 | (uint)bVar37 * 4 |
                                   (uint)bVar15 | (uint)bVar36 * 0x200000 | (uint)bVar29 * 0x40000);
            if (DAT_0043f89c == 0) {
              fVar38 = (float10)(double)CONCAT44(DAT_0073ff94,DAT_0073ff90) / (float10)2.0;
            }
            else {
              pcStack_208 = (char *)0x40000000;
              fVar38 = (float10)__adj_fdiv_m64(0);
            }
            _DAT_0073ffa8 = (double)((float10)_DAT_00441f98 - fVar38);
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
              fVar38 = (float10)(double)CONCAT44(DAT_0073ff94,DAT_0073ff90) / (float10)2.0;
            }
            else {
              pcStack_208 = (char *)0x40000000;
              fVar38 = (float10)__adj_fdiv_m64(0);
            }
            in_NT = ((uint)pcStack_204 & 0x4000) != 0;
            bVar20 = ((uint)pcStack_204 & 0x400) != 0;
            in_IF = ((uint)pcStack_204 & 0x200) != 0;
            in_TF = ((uint)pcStack_204 & 0x100) != 0;
            bVar16 = ((uint)pcStack_204 & 0x10) != 0;
            in_ID = ((uint)pcStack_204 & 0x200000) != 0;
            in_AC = ((uint)pcStack_204 & 0x40000) != 0;
            _DAT_0073ffb0 = (double)((float10)_DAT_00441fa0 - fVar38);
            DAT_0073ffa0 = 8;
            goto LAB_0040506f;
          }
        }
        pcStack_204 = (char *)((uint)bVar26 * 0x4000 | (uint)bVar23 * 0x800 | (uint)bVar22 * 0x400 |
                               (uint)bVar21 * 0x200 | (uint)bVar20 * 0x100 | (uint)bVar17 * 0x40 |
                               (uint)bVar37 * 4 | (uint)bVar15 | (uint)bVar36 * 0x200000 |
                              (uint)bVar29 * 0x40000);
        if (DAT_0043f89c == 0) {
          fVar38 = (float10)(double)CONCAT44(DAT_0073ff94,DAT_0073ff90) / (float10)2.0;
        }
        else {
          pcStack_208 = (char *)0x40000000;
          fVar38 = (float10)__adj_fdiv_m64(0);
        }
        _DAT_0073ffa8 = (double)(fVar38 + (float10)_DAT_00441f98);
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
          fVar38 = (float10)(double)CONCAT44(DAT_0073ff94,DAT_0073ff90) / (float10)2.0;
        }
        else {
          pcStack_208 = (char *)0x40000000;
          fVar38 = (float10)__adj_fdiv_m64(0);
        }
        in_NT = ((uint)pcStack_204 & 0x4000) != 0;
        bVar20 = ((uint)pcStack_204 & 0x400) != 0;
        in_IF = ((uint)pcStack_204 & 0x200) != 0;
        in_TF = ((uint)pcStack_204 & 0x100) != 0;
        bVar16 = ((uint)pcStack_204 & 0x10) != 0;
        in_ID = ((uint)pcStack_204 & 0x200000) != 0;
        in_AC = ((uint)pcStack_204 & 0x40000) != 0;
        _DAT_0073ffb0 = (double)(fVar38 + (float10)_DAT_00441fa0);
      }
      else {
        _DAT_0073ffa8 = (double)CONCAT44(DAT_0073ff94,DAT_0073ff90) + _DAT_00441f98;
        bVar37 = NAN(_DAT_00441fa0) || NAN(_DAT_0073ffa8);
        bVar17 = _DAT_00441fa0 == _DAT_0073ffa8;
        bVar15 = false;
        if (_DAT_00441fa0 < _DAT_0073ffa8) {
          bVar37 = NAN(_DAT_00441fa0) || NAN(_DAT_00441f98);
          bVar15 = _DAT_00441fa0 < _DAT_00441f98;
          bVar17 = _DAT_00441fa0 == _DAT_00441f98;
          if (_DAT_00441f98 < _DAT_00441fa0) {
            pcStack_204 = (char *)((uint)bVar26 * 0x4000 | (uint)bVar23 * 0x800 |
                                   (uint)bVar22 * 0x400 | (uint)bVar21 * 0x200 |
                                   (uint)bVar20 * 0x100 | (uint)bVar17 * 0x40 | (uint)bVar37 * 4 |
                                   (uint)bVar15 | (uint)bVar36 * 0x200000 | (uint)bVar29 * 0x40000);
            if (DAT_0043f89c == 0) {
              fVar38 = (float10)(double)CONCAT44(DAT_0073ff94,DAT_0073ff90) / (float10)2.0;
            }
            else {
              pcStack_208 = (char *)0x40000000;
              fVar38 = (float10)__adj_fdiv_m64(0);
            }
            _DAT_0073ffa8 = (double)((float10)_DAT_0073ffa8 - fVar38);
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
              fVar38 = (float10)(double)CONCAT44(DAT_0073ff94,DAT_0073ff90) / (float10)2.0;
            }
            else {
              pcStack_208 = (char *)0x40000000;
              fVar38 = (float10)__adj_fdiv_m64(0);
            }
            in_NT = ((uint)pcStack_204 & 0x4000) != 0;
            bVar20 = ((uint)pcStack_204 & 0x400) != 0;
            in_IF = ((uint)pcStack_204 & 0x200) != 0;
            in_TF = ((uint)pcStack_204 & 0x100) != 0;
            bVar16 = ((uint)pcStack_204 & 0x10) != 0;
            in_ID = ((uint)pcStack_204 & 0x200000) != 0;
            in_AC = ((uint)pcStack_204 & 0x40000) != 0;
            _DAT_0073ffb0 = (double)(fVar38 + (float10)_DAT_00441fa0);
            goto LAB_0040506f;
          }
        }
        DAT_0073ffa0 = 8;
        pcStack_204 = (char *)((uint)bVar26 * 0x4000 | (uint)bVar23 * 0x800 | (uint)bVar22 * 0x400 |
                               (uint)bVar21 * 0x200 | (uint)bVar20 * 0x100 | (uint)bVar17 * 0x40 |
                               (uint)bVar37 * 4 | (uint)bVar15 | (uint)bVar36 * 0x200000 |
                              (uint)bVar29 * 0x40000);
        if (DAT_0043f89c == 0) {
          fVar38 = (float10)(double)CONCAT44(DAT_0073ff94,DAT_0073ff90) / (float10)2.0;
        }
        else {
          pcStack_208 = (char *)0x40000000;
          fVar38 = (float10)__adj_fdiv_m64(0);
        }
        _DAT_0073ffa8 = (double)((float10)_DAT_00441f98 - fVar38);
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
          fVar38 = (float10)(double)CONCAT44(DAT_0073ff94,DAT_0073ff90) / (float10)2.0;
        }
        else {
          pcStack_208 = (char *)0x40000000;
          fVar38 = (float10)__adj_fdiv_m64(0);
        }
        in_NT = ((uint)pcStack_204 & 0x4000) != 0;
        bVar20 = ((uint)pcStack_204 & 0x400) != 0;
        in_IF = ((uint)pcStack_204 & 0x200) != 0;
        in_TF = ((uint)pcStack_204 & 0x100) != 0;
        bVar16 = ((uint)pcStack_204 & 0x10) != 0;
        in_ID = ((uint)pcStack_204 & 0x200000) != 0;
        in_AC = ((uint)pcStack_204 & 0x40000) != 0;
        _DAT_0073ffb0 = (double)((float10)_DAT_00441fa0 - fVar38);
      }