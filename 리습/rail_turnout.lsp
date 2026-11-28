;;; Railroad yard drafting for Windows AutoCAD with AutoLISP and ActiveX.
;;; RAILMAKE creates a sample block. RAILSETUP registers an existing sample.
;;; RAILYARD offsets tracks.
;;; RAILTURN connects parallel tracks. RAILFAN connects a diagonal lead to multiple tracks.

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

(defun rr:line-data (data / a b)
  (setq a (cdr (assoc 10 data))
        b (cdr (assoc 11 data)))
  (if (and (equal (caddr a) (caddr b) rr:tol)
           (rr:unit (rr:sub b a)))
    data
    (rr:msg "Select a nonzero horizontal LINE.")
  )
)

(defun rr:line (message / data)
  (if (setq data (rr:pick message "LINE")) (rr:line-data data))
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

(defun rr:register (label sample origin forward pi-point tip / record previous)
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
)

(defun c:RAILSETUP (/ sample label origin facing pi-point tip forward branch)
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
      (rr:register label sample origin forward pi-point tip)
      (rr:msg (strcat "Registered " rr:last-calibration " for this drawing session."))
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
(defun rr:edit (action args / doc space rr:new rr:changed result original object restored)
  (setq doc (rr:doc)
        space (vla-get-ModelSpace doc)
        result (vl-catch-all-apply 'vla-StartUndoMark (list doc)))
  (if (vl-catch-all-error-p result)
    (rr:msg (vl-catch-all-error-message result))
    (progn
      (setq result (vl-catch-all-apply action (cons space args)))
      (if (or (null result) (vl-catch-all-error-p result))
        (progn
          (foreach original rr:changed
            (setq restored (vl-catch-all-apply 'entmod (list original)))
            (if (or (null restored) (vl-catch-all-error-p restored))
              (rr:msg "Could not restore a target track. Use UNDO to roll back this edit.")
            )
          )
          (foreach object rr:new
            (if (vl-catch-all-error-p (vl-catch-all-apply 'vla-Delete (list object)))
              (rr:msg "Could not remove a generated object. Use UNDO to roll back this edit.")
            )
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

(defun rr:block-graphic (object)
  (rr:new-on-layer object "0")
  (vla-put-Color object 1)
  object
)

(defun rr:draw-block (space name label origin pi-point tip layer
                      / zero block lead mark mark-x tick x top label-point lettering insert data)
  (setq zero '(0.0 0.0 0.0)
        block (vla-Add (vla-get-Blocks (rr:doc)) (vlax-3d-point zero) name)
        rr:new (cons block rr:new)
        lead (car pi-point)
        mark-x (* 0.245 lead)
        mark (list mark-x 0.0 0.0)
        tick (* 0.0825 lead)
        top (list (car tip) 0.0 0.0)
        label-point (vlax-3d-point (list lead (* -0.21 lead) 0.0)))
  (rr:block-graphic (vla-AddLine block (vlax-3d-point zero) (vlax-3d-point pi-point)))
  (foreach x (list 0.0 mark-x lead)
    (rr:block-graphic
      (vla-AddLine block (vlax-3d-point (list x (- tick) 0.0))
                         (vlax-3d-point (list x tick 0.0))))
  )
  (rr:block-graphic (vla-AddCircle block (vlax-3d-point mark) tick))
  ;; Repeating the last corner creates a triangular, filled 2D solid.
  (rr:block-graphic
    (vla-AddSolid block (vlax-3d-point pi-point) (vlax-3d-point top)
              (vlax-3d-point tip) (vlax-3d-point tip)))
  (rr:block-graphic (vla-AddLine block (vlax-3d-point pi-point) (vlax-3d-point tip)))
  (setq lettering (rr:block-graphic (vla-AddText block label label-point (* 0.18 lead))))
  (vla-put-Alignment lettering 10) ; acAlignmentMiddleCenter
  (vla-put-TextAlignmentPoint lettering label-point)
  (setq insert (rr:new-on-layer
                 (vla-InsertBlock space (vlax-3d-point origin) name 1.0 1.0 1.0 0.0) layer)
        data (entget (vlax-vla-object->ename insert)))
  (if data data (rr:msg "Could not read the generated block reference."))
)

(defun rr:positive-real (message)
  (initget 6)
  (getreal message)
)

(defun rr:turnout-rise (run / mode degrees radians ratio)
  (initget "Ratio Angle")
  (setq mode (getkword "\nSpecify divergence by [Ratio/Angle] <Ratio>: "))
  (if (equal mode "Angle")
    (progn
      (while (and (setq degrees (rr:positive-real "\nDivergence angle from the main axis in degrees: "))
                  (>= degrees 90.0))
        (rr:msg "Enter an angle greater than 0 and less than 90 degrees.")
      )
      (if degrees
        (progn
          (setq radians (* degrees (/ pi 180.0)))
          (* run (/ (sin radians) (cos radians)))
        )
      )
    )
    (if (setq ratio (rr:positive-real "\nDivergence 1:N, enter N (e.g. 8): "))
      (/ run ratio)
    )
  )
)

(defun c:RAILMAKE (/ layer label hand default-name name lead run rise origin pi-point tip branch sample)
  (cond
    ((not (rr:model-p)) (rr:msg "Switch to model space."))
    ((not (and (rr:layer-open-p (setq layer (getvar "CLAYER"))) (rr:layer-open-p "0")))
     (rr:msg "Unlock/thaw the current layer and layer 0."))
    (T
      (setq label (getstring T "\nDisplayed turnout label <F8>: "))
      (if (= label "") (setq label "F8"))
      (initget "Left Right")
      (setq hand (getkword "\nTurnout hand, looking forward along +X [Left/Right] <Right>: ")
            default-name (strcat label (if (equal hand "Left") "-L" "-R"))
            name (getstring T (strcat "\nBlock and calibration name <" default-name ">: ")))
      (if (= name "") (setq name default-name))
      (cond
        ((not (and (snvalid name) (/= (substr name 1 1) "*")))
         (rr:msg "Enter a valid named block name."))
        ((tblsearch "BLOCK" name)
         (rr:msg "That block already exists. Use RAILSETUP on it or choose a new name."))
        ((not (setq lead (rr:positive-real "\nDistance along the main axis from datum to PI: "))))
        ((not (setq run (rr:positive-real "\nPI to branch tip, measured along the main axis: "))))
        ((or (<= lead rr:tol) (<= run rr:tol))
         (rr:msg "The main-axis lengths are too small."))
        ((not (setq rise (rr:turnout-rise run))))
        ((not (setq origin (rr:point "\nPick an insertion point for the sample block: "))))
        (T
          (setq pi-point (list lead 0.0 0.0)
                tip (list (+ lead run) (if (equal hand "Left") rise (- rise)) 0.0)
                branch (rr:unit (rr:sub (rr:add origin tip) (rr:add origin pi-point))))
          (cond
            ((not (and branch (> (car branch) 0.0) (> (abs (cadr branch)) rr:angle-tol)))
             (rr:msg "The input lengths or divergence do not produce a usable branch direction."))
            ((setq sample (rr:edit 'rr:draw-block (list name label origin pi-point tip layer)))
             (rr:register name sample origin '(1.0 0.0 0.0) (rr:add origin pi-point) (rr:add origin tip))
             (rr:msg (strcat "Created and registered " rr:last-calibration ". Use RAILTURN or RAILFAN.")))
          )
        )
      )
    )
  )
  (princ)
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

(defun rr:forward-axis (a b forward / axis)
  (setq axis (rr:unit (rr:sub b a)))
  (if (< (rr:dot axis forward) 0.0) (rr:scale axis -1.0) axis)
)

(defun rr:setback (branch target radius)
  (/ (* radius (abs (rr:cross branch target))) (+ 1.0 (rr:dot branch target)))
)

(defun rr:target-fit (point cut-end kept-end direction)
  (cond
    ((not (rr:between (rr:dot (rr:sub point cut-end) direction) (distance cut-end kept-end)))
     "The target tangent point lies outside the selected LINE.")
    ((<= (distance point kept-end) rr:tol)
     "No target track would remain in the forward direction.")
  )
)

;; The intersection uses infinite lines. Both tangent points must fit the real track pieces.
(defun rr:track-fillet (tip branch target-start target-end forward radius
                  / target kept-end cut-end turn along setback joint first-point last-point center a b problem)
  (setq target (rr:unit (rr:sub target-end target-start)))
  (if (< (rr:dot target forward) 0.0)
    (setq target (rr:scale target -1.0)
          kept-end target-start
          cut-end target-end)
    (setq kept-end target-end
          cut-end target-start)
  )
  (setq turn (rr:cross branch target))
  (cond
    ((or (<= (abs turn) rr:angle-tol) (<= (rr:dot branch target) 0.0))
     "The divergent line must approach the target at a forward angle.")
    (T
      (setq along (/ (rr:cross (rr:sub cut-end tip) target) turn)
            setback (rr:setback branch target radius)
            joint (rr:add tip (rr:scale branch along))
            first-point (rr:sub joint (rr:scale branch setback))
            last-point (rr:add joint (rr:scale target setback)))
      (cond
        ((< (- along setback) (- rr:tol))
         "The radius or target side would put the first tangent point before the turnout tip.")
        ((setq problem (rr:target-fit last-point cut-end kept-end target)) problem)
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

(defun rr:fillet (tip branch target-start target-end forward radius)
  (if (> (abs (rr:cross forward (rr:forward-axis target-start target-end forward))) rr:angle-tol)
    "Source and target tracks must be parallel."
    (rr:track-fillet tip branch target-start target-end forward radius)
  )
)

(defun rr:draw-turn (space sample matrix pi-point target fillet radius trim-code layer mirror-axis / object copy)
  (setq object (vlax-ename->vla-object sample)
        copy (if mirror-axis
               (vla-Mirror object (vlax-3d-point (car mirror-axis))
                                  (vlax-3d-point (cadr mirror-axis)))
               (vla-Copy object))
        rr:new (cons copy rr:new))
  (vla-TransformBy copy (vlax-tmatrix matrix))
  (rr:new-line space pi-point (car fillet) layer)
  (if (caddr fillet)
    (rr:new-on-layer
      (vla-AddArc space (vlax-3d-point (caddr fillet)) radius (nth 3 fillet) (nth 4 fillet))
      layer)
  )
  (if trim-code
    (if (entmod (subst (cons trim-code (cadr fillet)) (assoc trim-code target) target))
      (progn (setq rr:changed (cons target rr:changed)) T)
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
                    (list sample matrix pi-point target fillet radius trim-code layer nil))
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

(defun rr:registered-sample (template / sample data)
  (if (and (setq sample (handent (cdr (assoc 'handle template))))
           (setq data (entget sample))
           (equal (rr:pose data) (cdr (assoc 'pose template)) rr:tol))
    sample
    (rr:msg "The sample block changed or was erased. Register it again with RAILSETUP.")
  )
)

(defun c:RAILTURN (/ template sample source target position facing)
  (cond
    ((not (rr:model-p)) (rr:msg "Switch to model space."))
    ((not rr:calibrations) (rr:msg "Run RAILSETUP first."))
    ((not (setq template (rr:choose-calibration))))
    ((not (setq sample (rr:registered-sample template))))
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

;; At station zero, advance from the tip to the virtual intersection. Moving
;; that point along the lead until it meets the target gives the turnout station.
(defun rr:fan-geometry (lead-start lead-end pi-zero tip-zero start end radius clearance
                        / forward target branch skew straight station length offset origin pi-point join problem fillet)
  (setq forward (rr:unit (rr:sub lead-end lead-start))
        target (rr:forward-axis start end forward)
        branch (rr:unit (rr:sub tip-zero pi-zero))
        skew (rr:cross forward target)
        length (distance lead-start lead-end)
        straight (<= (abs (rr:cross branch target)) rr:angle-tol))
  (cond
    ((<= (abs skew) rr:angle-tol)
     "The lead must cross the target alignment at an angle.")
    ((<= (rr:dot forward target) rr:angle-tol)
     "The target needs a forward direction along the lead.")
    ((< (* skew (rr:cross forward branch)) 0.0)
     'wrong-hand)
    ((<= (rr:dot branch target) 0.0)
     "The turnout branch angle must allow a tangent curve into the target.")
    ((and (not straight) (<= radius rr:tol))
     "Enter a positive curve radius for this turnout and target angle.")
    (T
      (setq offset (rr:scale branch (+ clearance (if straight 0.0 (rr:setback branch target radius))))
            station (/ (rr:cross (rr:sub start (rr:add tip-zero offset)) target) skew))
      (if (and (rr:between station length)
               (rr:between (+ station (rr:dot (rr:sub pi-zero lead-start) forward)) length)
               (rr:between (+ station (rr:dot (rr:sub tip-zero lead-start) forward)) length))
        (progn
          (setq offset (rr:scale forward station)
                origin (rr:add lead-start offset)
                pi-point (rr:add pi-zero offset)
                fillet
                (if straight
                  (progn
                    (setq join (rr:add (rr:add tip-zero offset) (rr:scale branch clearance))
                          problem (if (> (rr:dot (rr:sub end start) target) 0.0)
                                    (rr:target-fit join start end target)
                                    (rr:target-fit join end start target)))
                    (if problem problem (list join join nil))
                  )
                  (rr:track-fillet (rr:add tip-zero offset) branch start end forward radius)
                ))
          (if (eq (type fillet) 'STR) fillet (list origin pi-point fillet))
        )
        "The turnout datum, PI or tip projects outside the selected lead LINE."
      )
    )
  )
)

(defun rr:reflect-point (point datum forward)
  (rr:sub point (rr:scale (rr:left forward) (* 2.0 (rr:cross forward (rr:sub point datum)))))
)

(defun rr:plan-fan (template lead-start lead-end selection radius clearance trim mirror
                    / forward sample-forward rotation datum matrix pi-point tip mirror-axis pi-zero
                      tip-zero index data start end axis yard-axis layer result plans problem)
  (setq forward (rr:unit (rr:sub lead-end lead-start))
        sample-forward (cdr (assoc 'forward template))
        rotation (- (rr:angle forward) (rr:angle sample-forward))
        datum (cdr (assoc 'origin template))
        pi-point (cdr (assoc 'pi template))
        tip (cdr (assoc 'tip template)))
  (if mirror
    (setq mirror-axis (list datum (rr:add datum (rr:scale sample-forward (distance pi-point tip))))
          pi-point (rr:reflect-point pi-point datum sample-forward)
          tip (rr:reflect-point tip datum sample-forward))
  )
  (setq matrix (rr:matrix datum lead-start rotation)
        pi-zero (rr:transform-point matrix pi-point)
        tip-zero (rr:transform-point matrix tip)
        index 0)
  (while (and (< index (sslength selection)) (not problem))
    (setq data (entget (ssname selection (+ 0.0 index)))
          start (cdr (assoc 10 data))
          end (cdr (assoc 11 data))
          layer (cdr (assoc 8 data))
          axis (rr:unit (rr:sub end start)))
    (cond
      ((not (and axis (rr:horizontal-p (list lead-start start end))))
       (setq problem "Select nonzero target LINEs at the same elevation as the lead."))
      ((and yard-axis (> (abs (rr:cross yard-axis axis)) rr:angle-tol))
       (setq problem "The selected yard tracks must be parallel to each other."))
      ((not (rr:layer-open-p layer))
       (setq problem "Unlock/thaw the target track layer."))
      (T
        (if (not yard-axis) (setq yard-axis axis))
        (setq result (rr:fan-geometry lead-start lead-end pi-zero tip-zero start end radius clearance))
        (if (not (listp result))
          (setq problem result)
          (setq plans (cons (list data (rr:matrix datum (car result) rotation)
                                  (cadr result) (caddr result)
                                  (if trim (if (> (rr:dot axis forward) 0.0) 10 11))
                                  layer mirror-axis)
                            plans))
        )
      )
    )
    (setq index (1+ index))
  )
  (cond
    ((not problem) (reverse plans))
    ((eq problem 'wrong-hand)
     (rr:msg (strcat "Target [" (cdr (assoc 5 data)) "]: The sample branches to the opposite side."))
     (if (and (not mirror)
              (progn
                (initget "Yes No")
                (equal "Yes" (getkword "\nMirror turnout copies about the main axis and retry? [Yes/No] <No>: "))))
       (rr:plan-fan template lead-start lead-end selection radius clearance trim T)
       (rr:msg "Check the selected lead direction or use the opposite turnout block. No tracks changed.")
     ))
    (T (rr:msg (strcat "Target [" (cdr (assoc 5 data)) "]: " problem " No tracks changed.")))
  )
)

(defun rr:draw-fan (space sample plans radius / plan success)
  (setq success T)
  (while (and success plans)
    (setq plan (car plans)
          success (rr:draw-turn space sample (nth 1 plan) (nth 2 plan) (nth 0 plan)
                                (nth 3 plan) radius (nth 4 plan) (nth 5 plan) (nth 6 plan))
          plans (cdr plans))
  )
  success
)

(defun c:RAILFAN (/ template sample lead front selection a b axis direction radius clearance trim plans)
  (cond
    ((not (rr:model-p)) (rr:msg "Switch to model space."))
    ((not rr:calibrations) (rr:msg "Run RAILSETUP first."))
    ((not (setq template (rr:choose-calibration))))
    ((not (setq sample (rr:registered-sample template))))
    ((not (and (rr:layer-open-p (getvar "CLAYER"))
               (rr:layer-open-p (cdr (assoc 8 (entget sample))))))
     (rr:msg "Unlock/thaw the current and sample block layers."))
    ((not (setq lead (rr:line "\nSelect the common diagonal lead LINE: "))))
    ((not (setq front (rr:point "\nPick the forward endpoint of the common lead: "))))
    ((progn
       (setq a (cdr (assoc 10 lead))
             b (cdr (assoc 11 lead))
             axis (rr:unit (rr:sub b a))
             direction (- (rr:dot (rr:sub front a) axis) (* 0.5 (distance a b))))
       (<= (abs direction) rr:tol))
     (rr:msg "Pick one end of the lead to set the forward direction."))
    ((not (progn
            (prompt "\nSelect all target yard track LINEs, then press Enter.")
            (setq selection (ssget '((0 . "LINE") (410 . "Model")))))))
    ((ssmemb (cdr (assoc -1 lead)) selection)
     (rr:msg "Select only the target tracks in the selection set."))
    (T
      (initget 6)
      (setq radius (getreal (strcat "\nCurve radius in drawing units "
                                    (if rr:last-radius (strcat "<" (rtos rr:last-radius 2 6) ">")
                                      "<Straight only>")
                                    ": ")))
      (if (not radius) (setq radius (if rr:last-radius rr:last-radius 0.0)))
      (initget 4)
      (setq clearance (getreal "\nStraight length after each turnout tip <0>: "))
      (initget "Trim Keep")
      (setq trim (not (equal "Keep" (getkword "\nTarget tracks [Trim/Keep] <Trim>: "))))
      (if (and (setq plans (rr:plan-fan template (if (> direction 0.0) a b) (if (> direction 0.0) b a)
                                       selection radius (if clearance clearance 0.0) trim nil))
               (rr:edit 'rr:draw-fan (list sample plans radius)))
        (progn
          (if (> radius rr:tol) (setq rr:last-radius radius))
          (rr:msg (strcat (itoa (sslength selection)) " turnout connections created on the common lead."))
        )
      )
    )
  )
  (princ)
)

(prompt "\nRail drafting loaded. Commands: RAILMAKE, RAILSETUP, RAILYARD, RAILTURN, RAILFAN.")
(princ)
