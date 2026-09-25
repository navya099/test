
(vl-load-com)

(defun c:PROFCSV
  (/ ent align profiles profile names i idx
     sta endsta step elev result file path count)

  ;; 1. Select alignment
  (setq ent (car (entsel "\nSelect Civil 3D alignment: ")))

  (cond
    ((null ent)
     (princ "\nCancelled.")
    )

    ((/= (cdr (assoc 0 (entget ent))) "AECC_ALIGNMENT")
     (princ "\nSelected object is not an alignment.")
    )

    (T
     (setq align (vlax-ename->vla-object ent))
     (setq profiles (vlax-get-property align 'Profiles))

     ;; 2. List profiles
     (setq names nil)

     (vlax-for p profiles
       (setq names
         (append names
           (list (vlax-get-property p 'Name))
         )
       )
     )

     (if (null names)
       (princ "\nNo profiles found.")
       (progn
         (setq i 0)
         (foreach name names
           (princ
             (strcat
               "\n[" (itoa i) "] " name
             )
           )
           (setq i (1+ i))
         )

         ;; 3. Select profile
         (setq idx (getint "\nProfile number: "))

         (if (and idx (>= idx 0) (< idx (length names)))
           (progn
             (setq profile
               (vlax-invoke-method
                 profiles 'Item (nth idx names)
               )
             )

             ;; 4. Station range
             (setq sta
               (max
                 (vlax-get-property align 'StartingStation)
                 (vlax-get-property profile 'StartingStation)
               )
             )

             (setq endsta
               (min
                 (vlax-get-property align 'EndingStation)
                 (vlax-get-property profile 'EndingStation)
               )
             )

             (initget 6)
             (setq step
               (getreal "\nStation interval <20.0>: ")
             )

             (if (null step) (setq step 20.0))

             ;; 5. CSV export
             (setq path
               (getfiled
                 "Save profile elevations"
                 "profile_elevations.csv"
                 "csv"
                 1
               )
             )

             (if path
               (progn
                 (setq file (open path "w"))
                 (write-line "Station,Elevation" file)
                 (setq count 0)

                 (while (<= sta (+ endsta 0.000001))
                   (setq result
                     (vl-catch-all-apply
                       'vlax-invoke-method
                       (list profile 'ElevationAt sta)
                     )
                   )

                   (if (not (vl-catch-all-error-p result))
                     (progn
                       (write-line
                         (strcat
                           (rtos sta 2 3)
                           ","
                           (rtos result 2 6)
                         )
                         file
                       )
                       (setq count (1+ count))
                     )
                   )

                   (setq sta (+ sta step))
                 )

                 (close file)

                 (princ
                   (strcat
                     "\nExported "
                     (itoa count)
                     " stations."
                   )
                 )
               )
             )
           )
           (princ "\nInvalid profile number.")
         )
       )
     )
    )
  )

  (princ)
)