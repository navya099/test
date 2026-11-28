;;; Railroad yard drafting for Windows AutoCAD with AutoLISP and ActiveX.
;;; RAILSETUP registers a sample. RAILYARD offsets tracks. RAILTURN connects tracks.

(vl-load-com)

(setq rr:tol 1e-6
      rr:angle-tol 1e-7)

(defun rr:add (a b) (mapcar '+ a b))
(defun rr:sub (a b) (mapcar '- a b))
(defun rr:scale (v n) (mapcar '(lambda (x) (* x n)) v))
(defun rr:dot (a b) (apply '+ (mapcar '* a b)))
(defun rr:cross (a b) (- (* (car a) (cadr b)) (* (cadr a) (car b))))
(defun rr:left (v) (list (- (cadr v)) (car v) 0.0))
(defun rr:flat (v) (list (car v) (cadr v) 0.0))

(defun rr:unit (v / length)
  (setq v (rr:flat v)
        length (sqrt (rr:dot v v)))
  (if (> length rr:tol) (rr:scale v (/ 1.0 length)))
)

(defun rr:angle (v / a)
  (setq a (atan (cadr v) (car v)))
  (if (< a 0.0) (+ a (* 2.0 pi)) a)
)

(defun rr:between (x max-distance)
  (and (>= x (- rr:tol)) (<= x (+ max-distance rr:tol)))
)

(defun rr:msg (message)
  (prompt (strcat "\n" message))
  nil
)

(defun rr:model-p ()
  (or (= 1 (getvar "TILEMODE")) (> (getvar "CVPORT") 1))
)

(defun rr:doc () (vla-get-ActiveDocument (vlax-get-acad-object)))

(defun rr:layer-open-p (layer / flags)
  (setq flags (cdr (assoc 70 (tblsearch "LAYER" layer))))
  (and flags (= 0 (logand flags 5)))
)

(defun rr:pick (message class / selection data)
  (if (setq selection (entsel message))
    (progn
      (setq data (entget (car selection)))
      (if (and (= class (cdr (assoc 0 data)))
               (= "MODEL" (strcase (cdr (assoc 410 data)))))
        data
        (rr:msg (strcat "Select a model-space " class " entity."))
      )
    )
  )
)

(defun rr:line (message / data a b)
  (if (setq data (rr:pick message "LINE"))
    (progn
      (setq a (cdr (assoc 10 data))
            b (cdr (assoc 11 data)))
      (if (and (equal (caddr a) (caddr b) rr:tol)
               (rr:unit (rr:sub b a)))
        data
        (rr:msg "Select a nonzero horizontal LINE.")
      )
    )
  )
)

(defun rr:point (message / point)
  (if (setq point (getpoint message)) (trans point 1 0))
)

(defun rr:horizontal-p (points / elevation)
  (setq elevation (caddr (car points)))
  (vl-every '(lambda (p) (equal (caddr p) elevation rr:tol)) points)
)

(defun rr:pose (data)
  (mapcar '(lambda (code) (assoc code data)) '(2 10 41 42 43 50 70 71 210))
)

(defun c:RAILSETUP (/ sample label origin facing pi-point tip forward branch record previous)
  (cond
    ((not (rr:model-p)) (rr:msg "Switch to model space."))
    ((not (setq sample (rr:pick "\nSelect the sample turnout block: " "INSERT"))))
    ((or (> (cond ((cdr (assoc 70 sample))) (1)) 1)
         (> (cond ((cdr (assoc 71 sample))) (1)) 1))
     (rr:msg "Select a single block reference."))
    ((not
       (and (setq origin (rr:point "\nSnap to the block placement datum on its main axis: "))
            (setq facing (rr:point "\nSnap to a second point in the turnout forward direction: "))
            (setq pi-point (rr:point "\nSnap to the theoretical intersection (PI): "))
            (setq tip (rr:point "\nSnap to the divergent end of the turnout: ")))))
    ((not (rr:horizontal-p (list origin facing pi-point tip)))
     (rr:msg "The four calibration points must be at the same WCS elevation."))
    ((not (and (setq forward (rr:unit (rr:sub facing origin)))
               (setq branch (rr:unit (rr:sub tip pi-point)))))
     (rr:msg "The direction and branch segment each need two distinct points."))
    ((or (<= (rr:dot forward branch) 0.0)
         (<= (abs (rr:cross forward branch)) rr:angle-tol))
     (rr:msg "PI-to-tip must diverge in the chosen forward direction."))
    ((= "" (setq label (getstring T "\nCalibration name (e.g. F8-L): "))))
    (T
      (setq label (strcase label)
            record (list label
                         (cons 'handle (cdr (assoc 5 sample)))
                         (cons 'pose (rr:pose sample))
                         (cons 'origin origin)
                         (cons 'forward forward)
                         (cons 'pi pi-point)
                         (cons 'tip tip))
            previous (assoc label rr:calibrations)
            rr:calibrations
            (cons record (if previous (vl-remove previous rr:calibrations) rr:calibrations))
            rr:last-calibration label)
      (rr:msg (strcat "Registered " label " for this drawing session."))
    )
  )
  (princ)
)

(defun rr:choose-calibration (/ record label answer choices)
  (foreach record rr:calibrations
    (setq label (car record)
          choices (if choices (strcat choices ", " label) label))
  )
  (setq answer (getstring T (strcat "\nCalibration (" choices ") <" rr:last-calibration ">: ")))
  (if (= answer "") (setq answer rr:last-calibration))
  (if (setq record (assoc (strcase answer) rr:calibrations))
    (progn (setq rr:last-calibration (car record)) (cdr record))
    (rr:msg "Calibration name not found.")
  )
)

;; Edits run without input after validation. Roll back created objects on a COM error.
(defun rr:edit (action args / doc space rr:new result object)
  (setq doc (rr:doc)
        space (vla-get-ModelSpace doc)
        result (vl-catch-all-apply 'vla-StartUndoMark (list doc)))
  (if (vl-catch-all-error-p result)
    (rr:msg (vl-catch-all-error-message result))
    (progn
      (setq result (vl-catch-all-apply action (cons space args)))
      (if (or (null result) (vl-catch-all-error-p result))
        (foreach object rr:new
          (if (vl-catch-all-error-p (vl-catch-all-apply 'vla-Delete (list object)))
            (rr:msg "Could not remove a generated object. Use UNDO to roll back this edit.")
          )
        )
      )
      (vla-EndUndoMark doc)
      (if (vl-catch-all-error-p result)
        (rr:msg (vl-catch-all-error-message result))
        result
      )
    )
  )
)

(defun rr:new-on-layer (object layer)
  (setq rr:new (cons object rr:new))
  (vla-put-Layer object layer)
  object
)

(defun rr:new-line (space a b layer)
  (rr:new-on-layer (vla-AddLine space (vlax-3d-point a) (vlax-3d-point b)) layer)
)

(defun rr:draw-yard (space a b step count layer / i offset)
  (setq i 1)
  (repeat count
    (setq offset (rr:scale step i))
    (rr:new-line space (rr:add a offset) (rr:add b offset) layer)
    (setq i (1+ i))
  )
  T
)

(defun c:RAILYARD (/ data a b axis layer side side-distance count spacing)
  (cond
    ((not (rr:model-p)) (rr:msg "Switch to model space."))
    ((not (setq data (rr:line "\nSelect the straight main track: "))))
    ((not (and (rr:layer-open-p (getvar "CLAYER"))
               (rr:layer-open-p (setq layer (cdr (assoc 8 data))))))
     (rr:msg "Unlock/thaw the current layer and main track layer."))
    ((not (setq side (rr:point "\nPick the side for the yard tracks: "))))
    ((progn
       (setq a (cdr (assoc 10 data))
             b (cdr (assoc 11 data))
             axis (rr:unit (rr:sub b a))
             side-distance (rr:cross axis (rr:sub side a)))
       (<= (abs side-distance) rr:tol))
     (rr:msg "Pick a point to either side of the main track."))
    ((not (progn (initget 6) (setq count (getint "\nNumber of parallel tracks: ")))))
    ((not (progn (initget 6) (setq spacing (getreal "\nTrack centerline spacing in drawing units: ")))))
    ((<= spacing rr:tol) (rr:msg "Track spacing is too small."))
    ((rr:edit 'rr:draw-yard
       (list a b (rr:scale (rr:left axis) (if (< side-distance 0.0) (- spacing) spacing))
             count layer))
     (rr:msg (strcat (itoa count) " parallel tracks created.")))
  )
  (princ)
)

(defun rr:matrix (from to rotation / cosine sine x y)
  (setq cosine (cos rotation)
        sine (sin rotation)
        x (car from)
        y (cadr from))
  (list (list cosine (- sine) 0.0 (+ (- (car to) (* cosine x)) (* sine y)))
        (list sine cosine 0.0 (- (cadr to) (* sine x) (* cosine y)))
        (list 0.0 0.0 1.0 (- (caddr to) (caddr from)))
        '(0.0 0.0 0.0 1.0))
)

(defun rr:transform-point (matrix point)
  (mapcar '(lambda (row) (+ (rr:dot (list (car row) (cadr row) (caddr row)) point)
                           (cadddr row)))
          (list (car matrix) (cadr matrix) (caddr matrix)))
)

;; The intersection uses infinite lines. Both tangent points must fit the real track pieces.
(defun rr:fillet (tip branch target-start target-end forward radius
                  / target length kept-end cut-end turn along setback joint first-point last-point center a b)
  (setq target (rr:unit (rr:sub target-end target-start))
        length (distance target-start target-end))
  (if (< (rr:dot target forward) 0.0)
    (setq target (rr:scale target -1.0)
          kept-end target-start
          cut-end target-end)
    (setq kept-end target-end
          cut-end target-start)
  )
  (setq turn (rr:cross branch target))
  (cond
    ((> (abs (rr:cross forward target)) rr:angle-tol)
     "Source and target tracks must be parallel.")
    ((or (<= (abs turn) rr:angle-tol) (<= (rr:dot branch target) 0.0))
     "The divergent line must approach the target at a forward angle.")
    (T
      (setq along (/ (rr:cross (rr:sub cut-end tip) target) turn)
            setback (/ (* radius (abs turn)) (+ 1.0 (rr:dot branch target)))
            joint (rr:add tip (rr:scale branch along))
            first-point (rr:sub joint (rr:scale branch setback))
            last-point (rr:add joint (rr:scale target setback)))
      (cond
        ((< (- along setback) (- rr:tol))
         "The radius or target side would put the first tangent point before the turnout tip.")
        ((not (rr:between (rr:dot (rr:sub last-point cut-end) target) length))
         "The target tangent point lies outside the selected LINE.")
        ((<= (distance last-point kept-end) rr:tol)
         "No target track would remain in the forward direction.")
        (T
          (setq center (rr:add first-point (rr:scale (rr:left branch) (if (> turn 0.0) radius (- radius))))
                a (rr:angle (rr:sub first-point center))
                b (rr:angle (rr:sub last-point center)))
          (list first-point last-point center (if (> turn 0.0) a b) (if (> turn 0.0) b a))
        )
      )
    )
  )
)

(defun rr:draw-turn (space sample matrix pi-point target fillet radius trim-code layer / copy)
  (setq copy (vla-Copy (vlax-ename->vla-object sample))
        rr:new (cons copy rr:new))
  (vla-TransformBy copy (vlax-tmatrix matrix))
  (rr:new-line space pi-point (car fillet) layer)
  (rr:new-on-layer
    (vla-AddArc space (vlax-3d-point (caddr fillet)) radius (nth 3 fillet) (nth 4 fillet))
    layer)
  (if trim-code
    (if (entmod (subst (cons trim-code (cadr fillet)) (assoc trim-code target) target))
      T
      (rr:msg "Could not trim the target LINE.")
    )
    T
  )
)

(defun rr:apply-turn (template sample source target position facing
                     / a b start end axis forward station origin radius matrix pi-point tip
                       branch fillet trim-code choice layer)
  (setq a (cdr (assoc 10 source))
        b (cdr (assoc 11 source))
        start (cdr (assoc 10 target))
        end (cdr (assoc 11 target))
        axis (rr:unit (rr:sub b a))
        station (rr:dot (rr:sub position a) axis)
        origin (rr:add a (rr:scale axis station))
        facing (rr:dot (rr:sub facing origin) axis)
        forward (if (< facing 0.0) (rr:scale axis -1.0) axis)
        layer (cdr (assoc 8 target)))
  (cond
    ((not (rr:horizontal-p (list a b start end)))
     (rr:msg "Source and target track elevations must match."))
    ((not (rr:between station (distance a b)))
     (rr:msg "Pick a turnout datum within the source LINE."))
    ((<= (abs facing) rr:tol)
     (rr:msg "Pick the forward direction along the source track."))
    ((not (and (rr:layer-open-p (getvar "CLAYER"))
               (rr:layer-open-p layer)
               (rr:layer-open-p (cdr (assoc 8 (entget sample))))))
     (rr:msg "Unlock/thaw the current, target, and sample block layers."))
    (T
      (initget 6)
      (setq radius
        (getreal (strcat "\nCurve radius in drawing units"
                         (if rr:last-radius (strcat " <" (rtos rr:last-radius 2 6) ">") "")
                         ": ")))
      (if (not radius) (setq radius rr:last-radius))
      (cond
        ((not radius))
        ((<= radius rr:tol) (rr:msg "Curve radius is too small."))
        (T
          (setq matrix (rr:matrix (cdr (assoc 'origin template)) origin
                                  (- (rr:angle forward) (rr:angle (cdr (assoc 'forward template)))))
                pi-point (rr:transform-point matrix (cdr (assoc 'pi template)))
                tip (rr:transform-point matrix (cdr (assoc 'tip template)))
                branch (rr:unit (rr:sub tip pi-point))
                fillet (rr:fillet tip branch start end forward radius))
          (if (eq (type fillet) 'STR)
            (rr:msg fillet)
            (progn
              (initget "Trim Keep")
              (setq choice (getkword "\nTarget track [Trim/Keep] <Trim>: ")
                    trim-code (if (not (equal choice "Keep"))
                                (if (> (rr:dot (rr:sub end start) forward) 0.0) 10 11)))
              (if (rr:edit 'rr:draw-turn
                    (list sample matrix pi-point target fillet radius trim-code layer))
                (progn
                  (setq rr:last-radius radius)
                  (rr:msg "Turnout block, divergent LINE and tangent ARC created.")
                )
              )
            )
          )
        )
      )
    )
  )
)

(defun c:RAILTURN (/ template sample source target position facing)
  (cond
    ((not (rr:model-p)) (rr:msg "Switch to model space."))
    ((not rr:calibrations) (rr:msg "Run RAILSETUP first."))
    ((not (setq template (rr:choose-calibration))))
    ((not
       (and (setq sample (handent (cdr (assoc 'handle template))))
            (entget sample)
            (equal (rr:pose (entget sample)) (cdr (assoc 'pose template)) rr:tol)))
     (rr:msg "The sample block changed or was erased. Register it again with RAILSETUP."))
    ((not (setq source (rr:line "\nSelect the source track LINE: "))))
    ((not (setq position (rr:point "\nPick the turnout datum on the source track: "))))
    ((not (setq facing (rr:point "\nPick a point toward the turnout forward end: "))))
    ((not (setq target (rr:line "\nSelect the parallel target track LINE: "))))
    ((equal (cdr (assoc -1 source)) (cdr (assoc -1 target)))
     (rr:msg "Use two different track lines."))
    (T (rr:apply-turn template sample source target position facing))
  )
  (princ)
)

(prompt "\nRail drafting loaded. Commands: RAILSETUP, RAILYARD, RAILTURN.")
(princ)
