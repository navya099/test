(defun c:ExportBrokenChainCoords ( / ent obj startsta endsta inc numberlist sta file 
                                     v-east v-north res east-val north-val 
                                     real-sta dist param deriv bearing-val brokenchain)
  (vl-load-com)
  
  (setq ent (entsel "\nSelect an Alignment: "))
  (if (and ent (setq obj (vlax-ename->vla-object (car ent))))
    (progn
      (if (= (vla-get-ObjectName obj) "AeccDbAlignment")
        (progn
          (setq brokenchain (getreal "\nEnter the broken chain station offset (e.g., 1265.85): "))
          (if (not brokenchain) (setq brokenchain 0.0))

          ;; 1. 표기용 기준 스테이션 범위 설정 (원본에 오프셋을 더한 범위)
          (setq startsta (+ (vlax-get obj 'StartingStation) brokenchain))
          (setq endsta   (+ (vlax-get obj 'EndingStation) brokenchain))
          (setq inc 25.0)
          
          ;; 2. 1275, 1300, 1325... 형태의 표기용 리스트 생성
          (setq numberlist (make-25-list startsta endsta inc))

          (setq file (open "C:\\Temp\\coords.csv" "w"))
          (if (not file)
            (progn (princ "\nError: C:\\Temp 폴더 확인") (exit))
          )
          
          (write-line "Display_Station,Real_Station,Northing,Easting,Bearing(Rad)" file)

          (foreach sta numberlist
            ;; 3. [핵심] 실제 내부 스테이션 계산 (표기용 - 오프셋)
            (setq real-sta (- sta brokenchain))

            (setq v-east (vlax-make-variant 0.0 vlax-vbDouble))
            (setq v-north (vlax-make-variant 0.0 vlax-vbDouble))

            ;; 4. 실제 스테이션으로 좌표 추출
            (setq res
              (vl-catch-all-apply
                'vlax-invoke-method
                (list obj 'PointLocation 
                      (vlax-make-variant real-sta vlax-vbDouble)
                      (vlax-make-variant 0.0 vlax-vbDouble) 
                      'v-east          
                      'v-north         
                )
              )
            )

            ;; 5. Bearing 계산 (내부 실거리 기준)
            (setq dist (- real-sta (vlax-get obj 'StartingStation)))
            (setq param (vlax-curve-getParamAtDist obj dist))
            (setq deriv (vlax-curve-getFirstDeriv obj param))
            (setq bearing-val (- (/ pi 2.0) (atan (cadr deriv) (car deriv))))

            (if (vl-catch-all-error-p res)
              (princ (strcat "\nError at Display Station " (rtos sta 2 2)))
              (progn
                (setq east-val (if (= (type v-east) 'VARIANT) (vlax-variant-value v-east) v-east))
                (setq north-val (if (= (type v-north) 'VARIANT) (vlax-variant-value v-north) v-north))

                (write-line
                  (strcat (rtos sta 2 2) ","              ; 표기용 (1275, 1300...)
                          (rtos real-sta 2 4) ","        ; 실제 내부값 (9.15...)
                          (rtos north-val 2 4) "," 
                          (rtos east-val 2 4) "," 
                          (rtos bearing-val 2 8))
                  file
                )
              )
            )
          )

          (close file)
          (princ (strcat "\n[완료] " (itoa (length numberlist)) "개의 데이터가 C:\\Temp\\coords.csv에 저장되었습니다."))
        )
      )
    )
  )
  (princ)
)

;; 배수 리스트 생성 함수 (동일)
(defun make-25-list (start end inc / lst val)
  (setq lst '())
  (setq val (* inc (fix (if (<= (rem start inc) 1e-6) 
                            (/ start inc) 
                            (1+ (/ start inc))))))
  (while (<= val (+ end 1e-6))
    (setq lst (cons val lst))
    (setq val (+ val inc))
  )
  (reverse lst)
)