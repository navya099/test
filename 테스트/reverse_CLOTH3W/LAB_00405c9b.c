LAB_00405c9b:
          uVar12 = (undefined2)((uint)pcVar11 >> 0x10);
          pcVar11 = (char *)((uint)CONCAT21(uVar12,0.0 < _DAT_0079dcc0) << 8);
          if (0.0 < _DAT_0079dcc0) {
            bVar22 = 0.0 < _DAT_0079dcc8;
            uVar13 = (ushort)(_DAT_0079dcc8 == 0.0);
            pcVar11 = (char *)CONCAT22(uVar12,(ushort)bVar22 << 8 | (ushort)NAN(_DAT_0079dcc8) << 10
                                              | uVar13 << 0xe);
            if (!bVar22 && uVar13 == 0) {
              pcStack_204 = (char *)((uint)in_NT * 0x4000 | (uint)bVar21 * 0x800 |
                                     (uint)bVar20 * 0x400 | (uint)in_IF * 0x200 |
                                     (uint)in_TF * 0x100 | (uint)(uVar13 != 0) * 0x40 |
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
              pcStack_204 = (char *)0x405e9a;
              fVar38 = (float10)FUN_00415d3d();
              _DAT_0079dce8 = (double)(fVar38 + (float10)_DAT_0079dce0);
              goto LAB_00405f32;
            }
          }
          uVar13 = (ushort)((uint)pcVar11 >> 0x10);
          pcVar11 = (char *)((uint)uVar13 << 0x10);
          if (_DAT_0079dcc0 < 0.0) {
            pcVar11 = (char *)CONCAT22(uVar13,(ushort)(0.0 < _DAT_0079dcc8) << 8 |
                                              (ushort)NAN(_DAT_0079dcc8) << 10 |
                                              (ushort)(_DAT_0079dcc8 == 0.0) << 0xe);
            if (0.0 < _DAT_0079dcc8) {
              pcStack_204 = (char *)((uint)in_NT * 0x4000 | (uint)bVar21 * 0x800 |
                                     (uint)bVar20 * 0x400 | (uint)in_IF * 0x200 |
                                     (uint)in_TF * 0x100 |
                                     (uint)((_DAT_0079dcc8 == 0.0) != 0) * 0x40 |
                                     (uint)(NAN(_DAT_0079dcc8) != 0) * 4 | 1 |
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
              pcStack_204 = (char *)0x405ee0;
              fVar38 = (float10)FUN_00415d3d();
              _DAT_0079dce8 = (double)(fVar38 + (float10)_DAT_0079dcd0);
              goto LAB_00405f32;
            }
          }
          if (_DAT_0079dcc0 < 0.0) {
            bVar22 = 0.0 < _DAT_0079dcc8;
            uVar13 = (ushort)(_DAT_0079dcc8 == 0.0);
            if (!bVar22 && uVar13 == 0) {
              pcStack_204 = (char *)((uint)in_NT * 0x4000 | (uint)bVar21 * 0x800 |
                                     (uint)bVar20 * 0x400 | (uint)in_IF * 0x200 |
                                     (uint)in_TF * 0x100 | (uint)(uVar13 != 0) * 0x40 |
                                     (uint)(NAN(_DAT_0079dcc8) != 0) * 4 | (uint)bVar22 |
                                     (uint)in_ID * 0x200000 | (uint)in_AC * 0x40000);
              if (DAT_0043f89c != 0) {
                pcStack_208 = (char *)CONCAT22((short)((uint)pcVar11 >> 0x10),
                                               (ushort)bVar22 << 8 |
                                               (ushort)NAN(_DAT_0079dcc8) << 10 | uVar13 << 0xe);
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
              pcStack_204 = (char *)0x405f26;
              fVar38 = (float10)FUN_00415d3d();
              _DAT_0079dce8 =
                   (double)(fVar38 + (float10)(double)CONCAT44(DAT_0079dcdc,DAT_0079dcd8));
              goto LAB_00405f32;
            }
          }
          if ((_DAT_0079dcc0 == 0.0) && (0.0 < _DAT_0079dcc8)) {
            _DAT_0079dce8 = _DAT_0079dce0;
          }
          if ((_DAT_0079dcc0 == 0.0) && (_DAT_0079dcc8 < 0.0)) {
            _DAT_0079dce8 = _DAT_0079dcd0;
          }
          if ((0.0 < _DAT_0079dcc0) && (_DAT_0079dcc8 == 0.0)) {
            _DAT_0079dce8 = 0.0;
          }
          if ((_DAT_0079dcc0 < 0.0) && (_DAT_0079dcc8 == 0.0)) {
            _DAT_0079dce8 = (double)CONCAT44(DAT_0079dcdc,DAT_0079dcd8);
          }
          bVar16 = 0;
        }