
(load "quaint-codec.el")
(load "quaint-data.el")

;; We don't automatically turn on quaint-use-codec in emacs version
;; 22 and earlier, and we don't bother with encoding Unicode
;; characters, should they be typed in (maybe that's fixable?
;; (char-to-string exotic-unicode-character) fails in emacs 22).
(setq quaint-emacs-recent-enough (>= emacs-major-version 23))

;;;;;;;;;;;;;;;;;;;
;; CUSTOMIZATION ;;
;;;;;;;;;;;;;;;;;;;

;;;###autoload
(defgroup quaint nil
  "Customization group for the Quaint programming language."
  :group 'languages)

;;;###autoload
(defcustom quaint-use-codec
  ;; Unicode works weird in emacs 22 and earlier, so we default to t
  ;; only if the version is recent enough. Users can override this.
  quaint-emacs-recent-enough
  "*Use the quaint codec when starting the quaint-mode?"
  :type 'boolean :group 'quaint)

;;;###autoload
(defcustom quaint-indent
  4
  "*Number of spaces to indent with"
  :type 'integer :group 'quaint)

;;;###autoload
(defcustom quaint-definition-constructors
  '("def")
  "*Keywords starting definitions."
  :type '(repeat string) :group 'quaint)

;;;###autoload
(defcustom quaint-major-constructors
  '("if" "elif" "else" "unless"
    "for" "while" "map"
    "`lambda`")
  "*Keywords starting important control structures."
  :type '(repeat string) :group 'quaint)


;;;;;;;;;;;
;; FACES ;;
;;;;;;;;;;;

;;;###autoload
(defgroup quaint-faces nil
  "Faces used to highlight the Quaint language."
  :group 'quaint)

(defun quaint-stock-face (light dark &optional bold)
  (if bold
      `((((class color) (background light))
         (:foreground ,light :weight bold))
        (((class color) (background dark))
         (:foreground ,dark :weight bold))
        (t
         (:foreground "black" :background "white" :weight bold)))
    `((((class color) (background light))
       (:foreground ,light))
      (((class color) (background dark))
       (:foreground ,dark))
      (t
       (:foreground "black" :background "white")))))

;; Constructor faces

(defface quaint-font-lock-constructor
  (quaint-stock-face "black" "white" t)
  "Face for control structures ('a' in 'a b: c')."
  :group 'quaint-faces)

(defface quaint-font-lock-major-constructor
  (quaint-stock-face "purple" "cyan" t)
  "Face for major control structures like if, else, for, etc."
  :group 'quaint-faces)

(defface quaint-font-lock-definition
  (quaint-stock-face "dark green" "green")
  "Face for definitions, e.g. the color of 'f' in 'def f[x]: ...'"
  :group 'quaint-faces)

;; Operator faces

(defface quaint-font-lock-c3op
  (quaint-stock-face "blue" "light blue")
  "Face for category 3 operators (+ - * / % etc.)"
  :group 'quaint-faces)

(defface quaint-font-lock-c4op
  (quaint-stock-face "dark blue" "deep sky blue")
  "Face for category 4 operators (← :: ∧ ∨ etc.)"
  :group 'quaint-faces)

;; Token faces

(defface quaint-font-lock-symbol
  (quaint-stock-face "dark red" "red")
  "Face for tokens like .x"
  :group 'quaint-faces)

(defface quaint-font-lock-symbol
  (quaint-stock-face "dark orange" "orange")
  "Face for tokens like $x, @x"
  :group 'quaint-faces)

(defface quaint-font-lock-symbol
  (quaint-stock-face "black" "white")
  "Face for tokens like x#"
  :group 'quaint-faces)

(defface quaint-font-lock-number
  (quaint-stock-face "dark cyan" "dark cyan")
  "Face for numeric tokens"
  :group 'quaint-faces)

;; Bracket face

(defface quaint-font-lock-bracket
  (quaint-stock-face "black" "white" t)
  "Face for brackets () [] {}"
  :group 'quaint-faces)

;; Special faces

(defface quaint-font-lock-assignment
  (quaint-stock-face "goldenrod4" "goldenrod1")
  "Face for variable assignment, i.e. 'a' in 'a ← x'"
  :group 'quaint-faces)

(defface quaint-font-lock-interpolation
  (quaint-stock-face "goldenrod4" "goldenrod1")
  "Face for variable interpolation inside strings"
  :group 'quaint-faces)

;; Error faces

(defface quaint-font-lock-warning
  (quaint-stock-face "red" "red" t)
  "Face warning for potentially invalid constructs"
  :group 'quaint-faces)

(defface quaint-font-lock-invalid
  `((((class color))
     (:foreground "white" :background "red" :weight bold))
    (t
     (:foreground "white" :background "black" :weight bold)))
  "Face for invalid characters"
  :group 'quaint-faces)


;;;;;;;;;;;;;;;;;;;;;;;;;
;; REGULAR EXPRESSIONS ;;
;;;;;;;;;;;;;;;;;;;;;;;;;

(setq quaint-id-regexp
      (regexp-opt quaint-id-characters))
(setq quaint-c1op-regexp
      (regexp-opt quaint-c1op-characters))
(setq quaint-c2op-regexp
      (regexp-opt quaint-c2op-characters))
(setq quaint-list-sep-regexp
      (regexp-opt quaint-list-sep-characters))
;; (setq quaint-c3op-regexp
;;       (regexp-opt quaint-c3op-characters))
;; (setq quaint-c4op-regexp
;;       (regexp-opt quaint-c4op-characters))
(setq quaint-opchar-regexp
      (concat quaint-c1op-regexp
              "\\|"
              quaint-c2op-regexp
              "\\|"
              quaint-list-sep-regexp))
              ;; "\\|"
              ;; quaint-c4op-regexp))

(setq quaint-word-regexp
      (concat quaint-id-regexp "+"))
;; (setq quaint-c34op-regexp
;;       (concat "\\(?:\\("
;;               quaint-c4op-regexp
;;               "\\)\\|\\("
;;               quaint-c3op-regexp
;;               "\\)\\)+"))
(setq quaint-escaped-char-literal-regexp
      (concat "'`esc`\\(" quaint-codec-regexp "\\|.\\)"))
(setq quaint-char-literal-regexp
      (concat "'\\(" quaint-codec-regexp "\\|.\\)"))

(setq quaint-bracket-openers '(?\( ?\[ ?\{))
(setq quaint-bracket-closers '(?\) ?\] ?\}))


;;;;;;;;;;;;;;;
;; UTILITIES ;;
;;;;;;;;;;;;;;;

(defun beginning-of-line-p (&optional pos)
  (save-excursion
    (if pos (goto-char pos))
    (skip-chars-backward " ")
    (bolp)))

(defun end-of-line-p (&optional pos)
  (save-excursion
    (if pos (goto-char pos))
    (skip-chars-forward " ")
    (or (eolp)
        (looking-at ";;"))))

(defun inside-encoding-p (&optional pos)
  (unless pos (setq pos (point)))
  (save-excursion
    (save-match-data
      (goto-char pos)
      (beginning-of-line)
      (catch 'return
        (while t
          (cond
           ((= (point) pos) (throw 'return nil))
           ((> (point) pos) (throw 'return t))
           (t (quaint-forward-char 1))))))))

(defun quaint-re-search-forward (regexp &optional limit noerror repeat)
  (let ((rval nil))
    (setq rval (re-search-forward regexp limit noerror repeat))
    (while (and rval (inside-encoding-p))
      (goto-char (+ (match-beginning 0) 1))
      (setq rval (re-search-forward regexp limit noerror repeat)))
    rval))

(defun quaint-re-search-backward (regexp &optional limit noerror repeat)
  (let ((rval nil))
    (setq rval (re-search-backward regexp limit noerror repeat))
    (while (and rval (inside-encoding-p))
      (goto-char (- (match-end 0) 1))
      (setq rval (re-search-backward regexp limit noerror repeat)))
    rval))

(defun quaint-next-operator (&optional pos)
  (unless pos (setq pos (point)))
  (save-excursion
    (let ((line-span 1))
      (goto-char pos)
      (catch 'return
        (while t
          (let ((value (quaint-forward-sexp-helper)))
            (cond
             ((equal value 'cont)
              (setq line-span (1+ line-span)))
             ((equal value 'comment)
              t)
             ((equal value 'operator)
              (throw 'return (and (<= (count-lines pos (point)) line-span)
                                  quaint-last-token)))
             (t (throw 'return nil)))))))))

(defun quaint-prev-operator (&optional pos)
  (unless pos (setq pos (point)))
  (save-excursion
    (goto-char pos)
    (let ((line-span (if (bolp) 0 1)))
      (catch 'return
        (while t
          (let ((value (quaint-backward-sexp-helper)))
            (cond
             ((equal value 'cont)
              (setq line-span (1+ line-span)))
             ((equal value 'comment)
              t)
             ((equal value 'operator)
              (throw 'return (and (<= (count-lines pos (point)) line-span)
                                  quaint-last-token)))
             (t (throw 'return nil)))))))))

(defun quaint-looking-at-suffix ()
  (save-excursion
    (save-match-data
      (and (not (string-match "^\\(,\\|;\\|:\\)+$" quaint-last-token))
           (or (string-match "^#+$" quaint-last-token)
               (and (not (memq (char-before) '(?\  ?\n)))
                    (progn (quaint-forward-operator-strict)
                           (or (memq (char-after) '(?\  ?\n))
                               (looking-at "\\\\")))))))))


;;;;;;;;;;;;
;; MOTION ;;
;;;;;;;;;;;;

(defun quaint-forward-char (&optional count)
  (interactive "p")
  (let ((orig (point)))
    (dotimes (i count)
      ;; (save-match-data
      (if (looking-at quaint-codec-regexp)
          (goto-char (match-end 0))
        (forward-char)))
    (- (point) orig)))

(defun quaint-backward-char (&optional count)
  (interactive "p")
  (let ((orig (point)))
    (dotimes (i count)
      ;; (save-match-data
      (let ((orig (point)))
        (cond
         ((equal (char-before) ?`)
          (backward-char)
          (condition-case nil
              (save-match-data
                (search-backward "`")
                (if (looking-at quaint-codec-named-code-regexp)
                    (goto-char (match-beginning 0))
                  (goto-char (- orig 1))))
            (error nil)))
         ((> (point) 2)
          (let ((consec 1))
            (save-excursion
              (backward-char 2)
              (condition-case nil
                  (while (looking-at quaint-codec-digraph-regexp)
                    (setq consec (+ consec 1))
                    (backward-char))
                (error nil)))
            (backward-char (- 2 (mod consec 2)))))
         (t
          (backward-char)))))
    (- orig (point))))

(setq quaint-last-token nil)

(defun quaint-last-token-range (start end)
  (setq quaint-last-token
        (buffer-substring-no-properties start end)))

(defun quaint-forward-word-strict (&optional skip-chars skip-underscore)
  (skip-chars-forward (or skip-chars "_ \n"))
  (let ((success nil)
        (orig (point)))
    (while (and (looking-at quaint-id-regexp)
                (or skip-underscore
                    (not (equal (match-string 0) "_"))))
      (setq success t)
      (quaint-forward-char 1))
    (and success
         (quaint-last-token-range orig (point)))))

(defun quaint-backward-word-strict (&optional skip-chars skip-underscore)
  (skip-chars-backward (or skip-chars "_ \n"))
  (let ((success nil)
        (orig (point)))
    (condition-case nil
        (progn
          (quaint-backward-char 1)
          (while (and (looking-at quaint-id-regexp)
                      (or skip-underscore
                          (not (equal (match-string 0) "_"))))
            (setq success t)
            (quaint-backward-char 1))
          (quaint-forward-char 1)
          success)
      (error success))
    (and success
         (quaint-last-token-range (point) orig))))


(defun quaint-forward-operator-strict (&optional skip-chars)
  (skip-chars-forward (or skip-chars " \n"))
  (let ((success nil)
        (orig (point)))
    (while (and (looking-at quaint-opchar-regexp)
                (not (save-match-data (looking-at "<<")))
                (not (save-match-data (looking-at ">>"))))
      (setq success t)
      (quaint-forward-char 1))
    (and success
         (quaint-last-token-range (point) orig))))

(defun quaint-backward-operator-strict (&optional skip-chars)
  (skip-chars-backward (or skip-chars " \n"))
  (let ((success nil)
        (orig (point)))
    (condition-case nil
        (progn
          (quaint-backward-char 1)
          (while (and (looking-at quaint-opchar-regexp)
                      (not (save-match-data (looking-at "<<")))
                      (not (save-match-data (looking-at ">>"))))
            (setq success t)
            (quaint-backward-char 1))
          (quaint-forward-char 1)
          success)
      (error success))
    (and success
         (quaint-last-token-range (point) orig))))


(defun quaint-forward-string-strict (&optional skip-chars)
  (skip-chars-forward (or skip-chars " \n"))
  (let ((orig (point)))
    (when
        (cond
         ((eq (char-after) ?\')
          (forward-char)
          (if (save-match-data (looking-at "`esc`"))
              (quaint-forward-char 1))
          (quaint-forward-char 1)
          t)
         ((eq (char-after) ?\")
          (forward-sexp)
          t)
         ((looking-at "<<")
          (goto-char (quaint-find-closing-guillemets))
          t)
         (t
          nil))
      (quaint-last-token-range orig (point)))))

(defun quaint-backward-string-strict (&optional skip-chars)
  (skip-chars-backward (or skip-chars " \n"))
  (let ((orig (point)))
    (quaint-backward-char 1)
    (when
        (cond
         ((or (looking-back "'")
              (looking-back "'`esc`"))
          (goto-char (match-beginning 0))
          t)
         ((eq (char-after) ?\")
          (forward-char)
          (backward-sexp)
          t)
         ((looking-at ">>")
          (goto-char (quaint-find-opening-guillemets (+ (point) 2)))
          t)
         (t
          (quaint-forward-char 1)
          nil))
      (quaint-last-token-range orig (point)))))
    


(defun quaint-forward-list-strict (&optional skip-chars)
  (skip-chars-forward (or skip-chars " \n"))
  (let ((orig (point)))
    (if (not (memq (char-after) quaint-bracket-openers))
        nil
      (forward-list)
      (quaint-last-token-range orig (point)))))

(defun quaint-backward-list-strict (&optional skip-chars)
  (skip-chars-backward (or skip-chars " \n"))
  (let ((orig (point)))
    (if (not (memq (char-before) quaint-bracket-closers))
        nil
      (backward-list)
      (quaint-last-token-range orig (point)))))


(defun quaint-forward-comment-strict (&optional skip-chars)
  (skip-chars-forward (or skip-chars " \n"))
  (let* ((state (syntax-ppss))
         (in-comment (nth 4 state))
         (comment-start (nth 8 state)))
    (when in-comment
      (goto-char comment-start))
    (if (not (looking-at ";;\\|;("))
        nil
      (forward-comment (point))
      t)))

(defun quaint-backward-comment-strict (&optional skip-chars)
  (skip-chars-backward (or skip-chars " \n"))
  (backward-char 1)
  (let* ((state (syntax-ppss))
         (in-comment (nth 4 state))
         (comment-start (nth 8 state)))
    (if in-comment
        (progn
          (goto-char comment-start)
          t)
      (forward-char 1)
      nil)))


(defun quaint-forward-sexp-helper (&optional skip-chars)
  (unless skip-chars (setq skip-chars " \n"))
  (let ((x nil)
        (orig (point)))
    (let ((rval (or
                 (progn (setq x 'nil)
                        (skip-chars-forward skip-chars)
                        (setq orig (point))
                        (and (eobp)
                             (setq quaint-last-token "")))
                 (progn (setq x 'comment)  (quaint-forward-comment-strict skip-chars))
                 (progn (setq x 'string)   (quaint-forward-string-strict skip-chars))
                 (progn (setq x 'word)     (quaint-forward-word-strict skip-chars t))
                 (progn (setq x 'operator) (quaint-forward-operator-strict skip-chars))
                 (progn (setq x 'list)     (quaint-forward-list-strict skip-chars))
                 (progn (setq x 'cont)     (when (looking-at "\\\\")
                                             (quaint-forward-char 1)
                                             (quaint-last-token-range orig (point))))
                 (progn (setq x 'nil)      (when (memq (char-after) quaint-bracket-closers)
                                             (quaint-last-token-range (point) (+ (point) 1))))
                 (progn (setq x 'other)    (quaint-forward-char 1)
                        (quaint-last-token-range orig (point))))))
      x)))

(defun quaint-backward-sexp-helper (&optional skip-chars)
  (unless skip-chars (setq skip-chars " \n"))
  (let ((x nil)
        (orig (point)))
    (let ((rval (or
                 (progn (setq x 'nil)
                        (skip-chars-backward skip-chars)
                        (setq orig (point))
                        (and (bobp)
                             (setq quaint-last-token "")))
                 (progn (setq x 'comment)  (quaint-backward-comment-strict skip-chars))
                 (progn (setq x 'string)   (quaint-backward-string-strict skip-chars))
                 (progn (setq x 'word)     (quaint-backward-word-strict skip-chars t))
                 (progn (setq x 'operator) (quaint-backward-operator-strict skip-chars))
                 (progn (setq x 'list)     (quaint-backward-list-strict skip-chars))
                 (progn (setq x 'cont)     (when (looking-back "\\\\")
                                             (quaint-backward-char 1)
                                             (quaint-last-token-range orig (point))))
                 (progn (setq x 'nil)      (when (memq (char-before) quaint-bracket-openers)
                                             (quaint-last-token-range (- (point) 1) (point))))
                 (progn (setq x 'other)    (quaint-backward-char 1)
                        (quaint-last-token-range orig (point))))))
      x)))


(defun quaint-forward-word (&optional count)
  (interactive "p")
  (dotimes (i count)
    (let ((skip " \n<>\"'()[]{}"))
      (while (not (quaint-forward-word-strict skip))
        (unless (quaint-forward-operator-strict skip)
          (quaint-forward-char 1))))))

(defun quaint-backward-word (&optional count)
  (interactive "p")
  (dotimes (i count)
    (let ((skip " \n<>\"'()[]{}"))
      (while (not (quaint-backward-word-strict skip))
        (unless (quaint-backward-operator-strict skip)
          (quaint-backward-char 1))))))

(defun quaint-forward-sexp (&optional count)
  (interactive "p")
  (dotimes (i count)
    (quaint-forward-sexp-helper)))

(defun quaint-backward-sexp (&optional count)
  (interactive "p")
  (dotimes (i count)
    (quaint-backward-sexp-helper)))


;;;;;;;;;;;;;;
;; DELETION ;;
;;;;;;;;;;;;;;

(defun quaint-kill-word (&optional count)
  (interactive "p")
  (let ((orig (point)))
    (quaint-forward-word count)
    (kill-region orig (point))))

(defun quaint-kill-backward-word (&optional count)
  (interactive "p")
  (let ((orig (point)))
    (quaint-backward-word count)
    (kill-region orig (point))))


(defun quaint-delete-char (&optional count)
  (interactive "p")
  (let ((orig (point)))
    (quaint-forward-char count)
    (delete-region orig (point))))

(defun quaint-delete-backward-char (&optional count)
  (interactive "p")
  (let ((orig (point)))
    (cond
     ((beginning-of-line-p)
      (delete-backward-char 1)
      (while (and (equal (char-before) ?\ )
                  (not (zerop (mod (current-column) quaint-indent))))
        (delete-backward-char 1)))
     (t
      (quaint-backward-char count)
      (delete-region (point) orig)))))


;;;;;;;;;;;;;;;;;;;;;;
;; FIND CONSTRUCTOR ;;
;;;;;;;;;;;;;;;;;;;;;;

(defun quaint-find-constructor (&optional pos nocont)
  (unless pos (setq pos (point)))
  (save-excursion
    (save-match-data
      (let ((line-span (if (bolp) 0 1))
            (end-of-constructor nil)
            (len 0)
            (rval pos))
        (goto-char pos)
        (catch 'return
          (while t
            (let* ((value (quaint-backward-sexp-helper))
                   (last-token quaint-last-token))
              (cond

               ;; There is a suffix operator like in "a b# c: d", and
               ;; in this case we remember where the suffix op is
               ;; located (we will highlight up to there) and we keep
               ;; going until we find some infix or prefix
               ;; operator. Note that we keep going conservatively,
               ;; i.e. "a + b* c: d" will only highlight "b*" even
               ;; though "*" might have lower priority than "+".
               ((and (equal value 'operator)
                     (quaint-looking-at-suffix))
                (setq end-of-constructor (+ (point) (length last-token))))

               ;; There is an operator there. We stop.
               ((and (equal value 'operator)
                     (not (string-match "^\\(\\.\\|\\$\\|@\\)+$" last-token)))
                (throw 'return (cons rval (or end-of-constructor (+ rval len)))))

               ;; There is a line continuation. We extend the
               ;; line-span to tolerate going up to the line where the
               ;; continuation is located.
               ((and (equal value 'cont)
                     (not nocont))
                (setq line-span (count-lines pos (point))))

               ;; We ignore comments completely.
               ((equal value 'comment)
                t)

               ;; Parens/bracket start. We stop.
               ((equal value 'nil)
                (throw 'return (cons rval (or end-of-constructor (+ rval len)))))

               ;; A bit convoluted, but this is a () sexp that ends on
               ;; the same line we were, but may start on another
               ;; line. We extend line-span.
               ((and (member value '(list string))
                     (not (> (count-lines pos (+ (point) (length last-token))) line-span)))
                (setq line-span (count-lines pos (point)))
                (setq rval (point))
                (setq len (length last-token)))

               ;; We check if we're still on the same line, or a
               ;; previous line if the line-span was extended. If we
               ;; are too far, we stop.
               ((> (count-lines pos (point)) line-span)
                (throw 'return (cons rval (or end-of-constructor (+ rval len)))))

               ;; Anything else we skip over.
               (t
                (setq rval (point))
                (setq len (length last-token)))))))))))


;;;;;;;;;;;;
;; INDENT ;;
;;;;;;;;;;;;

(defun quaint-current-indent (&optional pos)
  "Yields the indent of this particular line."
  (save-excursion
    (if pos (goto-char pos))
    (beginning-of-line)
    (let ((n 0))
      (while (eq (char-after) ?\ )
        (setq n (+ n 1))
        (forward-char))
      n)))

(defun quaint-count-lines (start end)
  (if (= start end)
      1
    (count-lines start end)))

;; (defun quaint-count-lines (start end)
;;   (when (> start end)
;;     (let ((tmp start))
;;       (setq start end)
;;       (setq end tmp)))
;;   (let ((span (count-lines start end)))
;;     (if (eq (char-before end) ?\n)
;;         (+ span 1)
;;       span)))

(defun quaint-analyze-line (&optional pos line-span)
  "Analyze the current line. This goes to the end of the line and
moves backward one sexp at a time until it arrives at the
beginning of a line. Then, it checks if the previous line ends
with a continuation character. If so, it keeps going. It stops at
the beginning of the buffer, at the beginning of a line (such
that the previous line does not end with a continuation
character), or at the beginning of a sexp.

Returns: (pos is-cont is-continuator hard-stop no-cont-pos)

pos is the beginning of the logical line, going past all sexps
and continuation characters, but after the indent. is-cont is t
if this line is the continuation of another. is-continuator is t
if this line is continuated by the following line, hard-stop is t
if we stopped at an opening bracket ([{ or at the beginning of
the buffer. no-cont-pos is the beginning of the logical line,
excluding any line continuations. This might not be the current
line, if a string or a list spans several lines."

  ;; line span: how many lines back are we willing to go?
  (unless line-span (setq line-span 1))
  (unless pos (setq pos (point)))
  (save-excursion
    (save-match-data
      (goto-char pos)
      (end-of-line)
      (let ((rval pos)
            (rval-no-cont pos)
            (is-continuator nil)
            (is-cont nil)
            (hard-stop nil))
        (catch 'inner
          (while t
            (let* ((value (quaint-backward-sexp-helper))
                   (last-token quaint-last-token))
              (cond

               ((equal value 'cont)
                ;; A continuation character extends the line span
                (if (<= (quaint-count-lines pos (point)) 1)
                    (setq is-continuator t)
                  (setq rval-no-cont rval)
                  (setq is-cont t))
                (setq rval (point))
                (setq line-span (quaint-count-lines pos (point))))

               ((equal value 'comment)
                ;; We skip comments
                t)

               ((equal value 'nil)
                ;; bob or ([{
                (setq hard-stop t)
                (throw 'inner nil))

               ((and (member value '(list string))
                     (not (> (quaint-count-lines pos (+ (point) (length last-token))) line-span)))
                ;; A multi-line string or list that ends on this line
                ;; leads to adjusting the line-span
                (setq line-span (quaint-count-lines pos (point)))
                (setq rval (point)))

               ((> (quaint-count-lines pos (point)) line-span)
                ;; Did we go too many lines back?
                (throw 'inner nil))

               (t
                ;; Normal tokens
                (setq rval (point)))))))
        (list rval is-cont is-continuator hard-stop rval-no-cont)))))

(defun quaint-proper-indent (&optional pos)
  (unless pos (setq pos (point)))
  (save-excursion
    (save-match-data
      (goto-char pos)
      (beginning-of-line)
      (catch 'return

        (when (bobp)
          (throw 'return '(-1 0 0)))
        (backward-char)

        (let* ((analysis (quaint-analyze-line nil 0))
               (position (nth 0 analysis))
               (is-cont (or (nth 1 analysis) (nth 2 analysis)))
               (hard-stop (nth 3 analysis)))

          (when is-cont
            ;; We are indenting a continuation line
            (goto-char position)
            (if hard-stop
                ;; We indent at the current column if we are right at
                ;; the beginning of a sexp
                (let ((cc (current-column)))
                  (throw 'return (list position cc (+ cc quaint-indent))))
              ;; Else, we copy the indent of the first line of the
              ;; continuation
              (let ((ci (quaint-current-indent)))
                (throw 'return (list position ci (+ ci quaint-indent))))))

          ;; (when (equal (quaint-next-operator) "~")
          ;;   )

          (let* ((state (syntax-ppss))
                 (last-parens (nth 1 state)))

            ;; Check our nesting level
            (if (not last-parens)
                ;; There is no nesting. We are top level.
                (throw 'return (list -1 0 0)))

            (goto-char (1+ last-parens))
            (let ((cc (current-column)))
              (if (not (end-of-line-p))
                  ;; We are at the start of a sexp, but we are not at
                  ;; the end of a line, so we will indent the next
                  ;; lines at the exact same column we are at. I.e. we
                  ;; indent at the level of "x" if we see "(x\n"
                  (throw 'return (list last-parens cc cc))
                ;; We are at the end of a line. Now, we check the
                ;; expression before the sexp. If we see "x + a b
                ;; (\n" then we want to indent the next line at the
                ;; level of "a" plus the normal indent offset, and
                ;; the closing ) will be at the level of a.
                (unless (bobp)
                  (backward-char)
                  (when (equal (quaint-prev-operator) ":")
                    (quaint-backward-operator-strict))
                  (goto-char (car (quaint-find-constructor nil t)))
                  (when (equal (quaint-prev-operator) "~")
                    (quaint-backward-operator-strict)))
                (setq cc (current-column))
                (throw 'return (list last-parens cc (+ cc quaint-indent)))))))))))

(defun quaint-compute-indent (&optional pos)
  (unless pos (setq pos (point)))
  (save-excursion
    (goto-char pos)
    (let ((this-indent (quaint-proper-indent)))
      ;; We get the indent data for this line. However, we will not
      ;; necessarily use it, because perhaps the user has manually
      ;; indented the previous line, and we want to copy that indent.
      (beginning-of-line)
      (skip-chars-backward " \n")
      (let ((analysis (quaint-analyze-line nil 1)))
        ;; We analyze the previous line
        (if (nth 2 analysis)
            ;; It is a continuator! We will place ourselves at the
            ;; beginning, but we will not follow up the lines the
            ;; previous line might be continuating, i.e. seeing "a\ \n
            ;; b\" we position ourselves on b, because we want to copy
            ;; the indent of b, not the indent of a.
            (goto-char (nth 4 analysis))
          ;; It is not a continuator. We will simply go to the
          ;; beginning of the logical line. This time if we see "a\ \n
          ;; b\ \n c" then we go to "a". Note that the analysis went
          ;; over sexps when appropriate, so when we see "a [b\nc]" we
          ;; also go to "a".
          (goto-char (nth 0 analysis))))
      (let ((prev (point))
            (prev-indent (quaint-proper-indent)))
        ;; The logic here is that (quaint-proper-indent) returns the
        ;; "baseline" of the indent as well as the indent of a closing
        ;; bracket and the indent of a normal line. If the baselines
        ;; are the same for the previous line and this line, then it
        ;; seems safe to use the previous line's indent.
        (goto-char pos)
        (beginning-of-line)
        (skip-chars-forward " ")
        (let (;; Are the baselines equal?
              (equal-spec (equal this-indent prev-indent))
              ;; Does this line start with a closing bracket?
              (closing (memq (char-after) quaint-bracket-closers)))
          (if (not equal-spec)
              ;; The baselines are different, so we ignore prev
              (if closing
                  (nth 1 this-indent)
                (nth 2 this-indent))
            ;; The baselines are identical. What we do here is that we
            ;; look at the indent of the previous line. If the current
            ;; line is a normal line, we copy its indent. If, on the
            ;; other hand, it starts with a closing bracket, then we
            ;; subtract to the previous line's indent, so that it
            ;; looks right.
            (goto-char prev)
            (let ((ci (quaint-current-indent)))
              (if closing
                  (- (+ ci (nth 1 this-indent)) (nth 2 this-indent))
                ci))))))))

(defun quaint-indent-line ()
  (interactive)
  (let ((orig (point))
        (new-indent (quaint-compute-indent))
        (current-indent (quaint-current-indent)))
    (if (/= new-indent current-indent)
        ;; Different indent. We just delete the whole indent there was
        ;; before and add back the right amount of spaces. If we were
        ;; in the indent zone, we'll end up right after the indent
        ;; thanks to the insertion semantics. If the point was located
        ;; elsewhere on the line there is no change.
        (save-excursion
          (beginning-of-line)
          (delete-char current-indent)
          (dotimes (i new-indent)
            (insert-before-markers " ")))
      ;; Same indent as before. We just move the point to avoid
      ;; marking the buffer as modified.
      (beginning-of-line)
      (forward-char new-indent)
      (if (> orig (point)) (goto-char orig)))))





(defvar quaint-mode-map
  (let ((map (make-sparse-keymap)))
    (define-key map "\C-c\C-u" 'quaint-codec-mode)
    (define-key map "\C-?" 'quaint-delete-backward-char)
    (define-key map "\C-d" 'quaint-delete-char)
    (define-key map "\M-;" 'quaint-comment-dwim)
    (define-key map "\C-c\C-e" 'quaint-encode-region)
    (define-key map "\C-j" 'quaint-newline)
    (define-key map [C-return] 'quaint-newline)
    (define-key map "(" 'quaint-electric-opening-parens)
    (define-key map "[" 'quaint-electric-opening-bracket)
    (define-key map "{" 'quaint-electric-opening-brace)
    (define-key map ")" 'quaint-electric-closing-parens)
    (define-key map "]" 'quaint-electric-closing-bracket)
    (define-key map "}" 'quaint-electric-closing-brace)

    (define-key map "\C-c\C-j" 'hypertest)
    (define-key map "\C-t" 'quaint-forward-char)
    (define-key map "\C-c\C-t" 'quaint-backward-char)
    (define-key map [C-right] 'quaint-forward-word)
    (define-key map [C-left] 'quaint-backward-word)
    (define-key map "\C-\M-f" 'quaint-forward-sexp)
    (define-key map "\C-\M-b" 'quaint-backward-sexp)
    (define-key map [C-delete] 'quaint-kill-word)
    (define-key map [C-backspace] 'quaint-kill-backward-word)
    map))

(defun quaint-add-encoder (encoder)
  (let ((c (car encoder))
        (repl (cdr encoder)))
    (define-key quaint-mode-map (char-to-string c) repl)))

(if quaint-emacs-recent-enough
    (mapcar 'quaint-add-encoder quaint-codec-encode-list))


(defvar quaint-encoder-table
  (make-hash-table :test 'eq)
  "Hash table mapping unicode character code -> string encoding.")

(defun quaint-encoder-add-entry (entry)
  (let ((character (car entry))
        (encoding (cdr entry)))
    (puthash character encoding quaint-encoder-table)))

(mapcar 'quaint-encoder-add-entry quaint-codec-encode-list)


(defvar quaint-mode-syntax-table
  (let ((table (make-syntax-table)))

    ;; Backslash does NOT escape anything
    (modify-syntax-entry ?\\ "." table)

    ;; Strings: ""
    (modify-syntax-entry ?\" "\"" table)

    ;; Comments: ; ... \n or ;* ... *; or ;( ... );
    (modify-syntax-entry ?\; ". 124b" table)
    (modify-syntax-entry ?*  ". 23n" table)
    (modify-syntax-entry ?\n "> b" table)

    ;; Brackets: () [] {}
    (modify-syntax-entry ?\( "() 2n" table)
    (modify-syntax-entry ?\) ")( 3n" table)
    (modify-syntax-entry ?\{ "(}" table)
    (modify-syntax-entry ?\} "){" table)
    (modify-syntax-entry ?\[ "(]" table)
    (modify-syntax-entry ?\] ")[" table)

    ;; Symbols. Should be "_" but then x_2 highlights 2 as a number.
    (modify-syntax-entry ?_ "w" table)

    ;; Operator characters
    (modify-syntax-entry ?? "." table)
    (modify-syntax-entry ?! "." table)
    (modify-syntax-entry ?< "." table)
    (modify-syntax-entry ?> "." table)
    (modify-syntax-entry ?= "." table)
    (modify-syntax-entry ?+ "." table)
    (modify-syntax-entry ?- "." table)
    (modify-syntax-entry ?* "." table)
    (modify-syntax-entry ?/ "." table)
    (modify-syntax-entry ?% "." table)
    (modify-syntax-entry ?$ "." table)
    (modify-syntax-entry ?& "." table)
    (modify-syntax-entry ?| "." table)
    (modify-syntax-entry ?. "." table)
    (modify-syntax-entry ?@ "." table)
    (modify-syntax-entry ?~ "." table)
    (modify-syntax-entry ?, "." table)

    table))




;;;;;;;;;;;;;;
;; Keywords ;;
;;;;;;;;;;;;;;

(defvar quaint-mode-keywords
  `(;; Single character syntax
    ;; 'x is like "x". Note that this has to work for, say, '\lambda\
    ;; as well, so we use quaint-codec-regexp to grab a full
    ;; character if possible. Note: '`esc`c is understood as 'c,
    ;; '`esc``br` as the unicode character ⏎ (whereas '`br` is \n).
    (,quaint-escaped-char-literal-regexp
     . font-lock-string-face)
    (,quaint-char-literal-regexp
     . font-lock-string-face)

    ;; Brackets
    ("[(){}]\\|\\[\\|\\]" . 'quaint-font-lock-bracket)

    ;; Numbers
    ("\\(?:^\\|[^0-9rR]\\)\\(\\.[0-9][0-9_]*\\([eE]\\+?-?[0-9_]+\\)?\\)"
     1 'quaint-font-lock-number) ;; start with dec pt .1, .999e99
    ("\\<[0-9][0-9_]*[rR][a-zA-Z0-9_]*\\(\\.[a-zA-Z0-9_]+\\)?\\>"
     . 'quaint-font-lock-number) ;; radix notation 2r1001, 16rDEAD.BEEF
    ("\\<[0-9][0-9_]*\\(\\.[0-9_]+\\)?\\([eE]\\+?-?[0-9_]+\\)?\\>"
     . 'quaint-font-lock-number) ;; decimal notation 104, 342.1, 10e-10

    ;; Declaration
    ;; Color var in: var <- value, var# <- value or var :: type
    ;; var is only colored if the character just before is one of [({,;
    ;; modulo whitespace. This is nice, as it highlights only b in
    ;; a, b <- value, which will look odd to the user if he or she meant
    ;; [a, b] <- value.
    (,(concat "\\(?:^\\|[\\|[({,;]\\) *\\(\\(?:"
              quaint-id-regexp
              "\\)*\\(?: *#\\)?\\) *\\(<-\\|::\\)")
     1 'quaint-font-lock-assignment)

    ;; Variable interpolation in strings: "\Up\(this) is interpolated"
    ("$([^)]*)"
     0 'quaint-font-lock-interpolation t)

    ;; Symbol: .blabla
    (,(concat "\\. *\\(" quaint-id-regexp "\\)+")
     . 'quaint-font-lock-symbol)

    ;; Prefixes: @blabla or $blabla (or @   blabla)
    (,(concat "[@$] *\\(" quaint-id-regexp "\\)*")
     . 'quaint-font-lock-prefix)

    ;; Suffixes: blabla# (or blabla         #)
    (,(concat "\\(" quaint-id-regexp "\\)* *#")
     . 'quaint-font-lock-suffix)

    ;; Operators
    ;; All contiguous operator characters are aggregated together.
    ;; Category 3 (c3) operators are colored differently from category
    ;; 4 (c4) operators. Characters in c3 can serve in c4 operators,
    ;; as long as there is at least one c4 character. So for example
    ;; + is c3, <- is c4, +<- is c4 too (as a whole).
    ;; Note: the order matters, c4op has to be matched before c3op
    ;; because the individual c4op digraph characters are in c3op.
    ;; If the order is reversed <-, <= will get the c3 coloring.
    ;; The ":" operator leads to special highlighting.
    (,quaint-c2op-regexp
     (0 (cond

         ;; First case is the ":" operator. In the expression "a b:
         ;; c", which means a(:){b, c} we want to highlight "a" (the
         ;; control structure)
         ((equal (match-string 0) ":")
          (let* (;; pos <- the start of the identifier to highlight
                 ;(pos (quaint-backward-primary-sexp (match-beginning 0)))
                 (constructor-range (quaint-find-constructor (match-beginning 0)))
                 (constructor-start (car constructor-range))
                 (constructor-end (cdr constructor-range))
                 (state (syntax-ppss))
                 ;; Are we in a string or a comment?
                 (inactive-region (or (nth 3 state) (nth 4 state))))
            (if inactive-region
                ;; If we are in a string or a comment, we don't want to
                ;; highlight something weird, or override the string
                ;; highlighting (we highlight the control structure with
                ;; put-text-property directly, so it overrides string
                ;; highlighting - maybe there's a better way to do it?)
                nil
              (save-excursion
                (goto-char constructor-start)
                (;when (looking-at quaint-word-regexp)
                 let ((text (buffer-substring-no-properties constructor-start constructor-end)))
                  (cond
                   ;; A. The identifier starts a definition, i.e. "def"
                   ((member text quaint-definition-constructors)
                    ;; We highlight "def" (or whatever definition constructor this is)
                    (put-text-property ;(match-beginning 0) (match-end 0)
                                       constructor-start constructor-end
                                       'face 'quaint-font-lock-major-constructor)
                    (goto-char constructor-end) ; (match-end 0))
                    (skip-chars-forward " ") ;; we align ourselves on the next expression
                    (if (looking-at quaint-word-regexp)
                        ;; We highlight the second term, e.g. in "def f[x]:"
                        ;; we highlight f.
                        (put-text-property ;constructor-start constructor-end
                                           (match-beginning 0) (match-end 0)
                                           'face 'quaint-font-lock-definition)))
                   ;; B. The identifier is important, i.e. "if", "else", "for", "\lambda\"
                   ((member text quaint-major-constructors)
                    (put-text-property constructor-start constructor-end
                                       ;(match-beginning 0) (match-end 0)
                                       'face 'quaint-font-lock-major-constructor))
                   ;; C. The identifier is unknown, but we still
                   ;; highlight it, albeit differently than if it was
                   ;; known (default is bold black, which is less
                   ;; visible).
                   (t
                    (put-text-property constructor-start constructor-end
                                       ;(match-beginning 0) (match-end 0)
                                       'face 'quaint-font-lock-constructor)))))
              ;; The highlighted term might not be on the same line as
              ;; the ":", so it's important to set the
              ;; font-lock-multiline property on the whole range.
              (put-text-property constructor-start (point) 'font-lock-multiline t)
              (if (end-of-line-p (point))
                  'quaint-font-lock-warning
                'quaint-font-lock-constructor))))

         ;; ((match-string 1)
         ;;  ;; Second case are category 4 operators. Characters in
         ;;  ;; categories 3 and 4 can be mixed together, but if there is
         ;;  ;; at least one c4 character, the whole op is promoted to c4
         ;;  ;; and we use the c4 face.
         ;;  'quaint-font-lock-c4op)

         (t
          ;; Third case, there are only c3 characters, so it's a c3 op.
          'quaint-font-lock-c3op))))

    ("`esc`" 0 'quaint-font-lock-major-constructor t)
    ("`br`"  0 'quaint-font-lock-major-constructor t)
    ("`tab`" 0 'quaint-font-lock-major-constructor t)

    ("." 0 (let ((c (char-before)))
             (if (or (= c ?\t)
                     (> (char-before) 127))
                 'quaint-font-lock-invalid
               nil)))
    )
  "Keywords for highlighting.")


(defvar quaint-mode-syntactic-keywords
  `(
    ;; this does not work for some reason
    ;; ;; `esc`x cancels the meaning of x
    ;; (,(concat "`esc`\\(" quaint-codec-regexp "\\|.\\)")
    ;;  0 "w")

    ;; 'x is like "x", but we put class w and will highlight it with
    ;; keywords. FIXME: '" causes havoc inside strings, but fuck it.
    ;; Just use '' instead of "'". Actually, just check with the
    ;; parser if we are in a string?
    (,(concat "'\\(" quaint-codec-regexp "\\|.\\)") 0
     (let* ((state (syntax-ppss (- (point) 1)))
            (inactive (or (nth 3 state) (nth 4 state))))
       (if inactive
           nil
         "w")))

    ;; Capture operators as punctuation, before lumping them all
    ;; together as words with the rule just after that.
    (,(concat "\\(?:\\("
              quaint-c2op-regexp
              ;; "\\)\\|\\("
              ;; quaint-c3op-regexp
              "\\)\\)") 0
              (progn (if (equal (length (match-string 0)) 1)
                         nil
                       ".")))

    ;; \xxx\ encodes a single character, and there might be single
    ;; quotes inside (e.g. \a"\ encodes ä) so we turn off all
    ;; syntactic properties in the construct. TODO: This does not work
    ;; all that well, it feels like the first character of the
    ;; construct does not actually change class, i.e. 1\lambda\2 sees
    ;; a word boundary between 1 and \lambda\. Seriously, this thing
    ;; is ass, but it will do for now.
    (,quaint-codec-named-code-regexp 0 "w")

    ;; << ... >> encodes a string. It is multiline and can nest,
    ;; i.e. << a << b >> c << d >> e >> is a single string.
    ("\\(?:^\\|[^']\\)\\(<\\)<" 1
     (let* ((state (syntax-ppss))
            (in-string (nth 3 state))
            (string-start (nth 8 state)))
       (if (and in-string (/= string-start (match-beginning 0)))
           nil ;; do nothing if we are in a string already
         (let ((end-pos (condition-case nil
                            (quaint-find-closing-guillemets (match-beginning 0))
                          (error nil))))
           (when end-pos
             ;; We put a text property on the closing guillemets
             ;; ">>" immediately; if we don't, the fontification of
             ;; the next opening guillemets "<<" will fail because
             ;; emacs' parser will say that they are within this
             ;; string.
             (put-text-property (- end-pos 1) end-pos 'syntax-table '(15 . nil))
             ;; font-lock-multiline should ensure that editing in the
             ;; middle of a multiline string won't mess things up
             (put-text-property (- (point) 2) (+ end-pos 2) 'font-lock-multiline t)))
         "|")))

    (">\\(>\\)" 1
     (let* ((state (syntax-ppss (- (point) 1)))
            (in-string (nth 3 state))
            (string-start (nth 8 state)))
       (if in-string
           (let ((end-pos (condition-case nil
                              (quaint-find-closing-guillemets string-start)
                            (error nil))))
             (if (and end-pos (equal end-pos (+ (point) 1)))
                 "|"
               nil))
         nil)))
    )
  "Syntactic keywords for quaint.")


(defun quaint-find-closing-guillemets (&optional start)
  ;; If start is before the opening guillemets in a <<>>-type string,
  ;; this returns the position right after the corresponding >>,
  ;; skipping ahead nested strings and interpolated expressions.  This
  ;; raises an error if the string is unclosed.
  (unless start (setq start (point)))
  (save-excursion
    (goto-char (+ start 2))
    (while
        (let* ((lim (save-excursion (quaint-re-search-forward ">>" (+ start 1000) nil))) ;; may raise error
               (open (save-excursion (quaint-re-search-forward "<<" lim t)))
               (interpol (save-excursion (quaint-re-search-forward "$(" (or open lim) t))))
          (cond
           (interpol
            ;; Note: this assumes that the <<>>s are balanced inside
            ;; the interpolator, but the syntax table seems to handle
            ;; <<>>s inside ""s, so it should be fine for
            ;; syntactically correct programs.
            (goto-char (- interpol 1))
            (forward-list) ;; may raise error
            t)
           (open
            (let ((subexpr-end
                   (save-excursion
                     (goto-char (- open 2))
                     ;; check for the only way to have a literal << in <<>> strings
                     (if (looking-back "`esc`")
                         open
                       (quaint-find-closing-guillemets (- open 2))))))
              (goto-char subexpr-end)
              t))
           (t
            (goto-char lim)
            nil))))
    (point)))

(defun quaint-find-opening-guillemets (&optional end)
  (unless end (setq end (point)))
  (save-excursion
    (goto-char end)
    (catch 'done
      (while t
        (search-backward "<<")
        (if (= (quaint-find-closing-guillemets) end)
            (throw 'done (point)))))))


(define-derived-mode quaint-mode fundamental-mode
  :syntax-table quaint-mode-syntax-table
  ;(kill-all-local-variables)
  (setq font-lock-defaults
        '(quaint-mode-keywords
          nil
          nil
          nil
          nil
          (font-lock-syntactic-keywords . quaint-mode-syntactic-keywords)
          (indent-line-function . quaint-indent-line)
          ))

  (if quaint-use-codec
      (quaint-codec-mode t))

  (setq major-mode 'quaint-mode)
  (setq mode-name "Quaint"))

(defun quaint-comment-dwim (&optional arg)
  "If no region is selected, inserts a comment at the
`comment-column'. If an uncommented region is selected, it is
commented: if the region falls in the middle of code, the region
is surrounded with ;(...);, else each line is prefixed
with ;;. If a commented region is selected, the region is
uncommented."
  ;; All this function does that comment-dwim doesn't is use the
  ;; nested ;(); comment format when commenting inside code (as
  ;; opposed to commenting whole lines, which prefixes them with
  ;; ;;). There is probably a better way to do this?

  ;; FIXME: (very minor) selecting any region starting with a comment
  ;; will fall back to the standard comment-dwim, even when we'd
  ;; rather use quaint-comment-region (e.g. selecting ";(a); b" will
  ;; produce ";; ;(a); b" instead of the preferable ";( ;(a); b
  ;; );"). This is probably not worth fixing, unless there's an easy
  ;; way to tell comment-dwim to use quaint-comment-region instead
  ;; of comment-region.
  (interactive "*P")
  (let ((comment-start ";; ")
        (comment-end ""))
    (if (and transient-mark-mode mark-active)
        (let ((orig (point))
              (beg (region-beginning))
              (end (region-end)))
          (save-excursion
            (goto-char beg)
            (if (not (looking-at "[ \n]*;\\(;\\|(\\)"))
                (quaint-comment-region beg end)
              (goto-char orig)
              (comment-dwim arg))))
      (comment-dwim arg))))

(defun quaint-comment-region (beg end)
  (interactive)
  (if
      (save-excursion
        (goto-char beg)
        (when (or (beginning-of-line-p)
                  (end-of-line-p))
          (goto-char end)
          (when (or (beginning-of-line-p)
                    (end-of-line-p))
            t)))
      (let ((comment-start ";; ")
            (comment-end ""))
        (comment-region beg end))
    (save-excursion
      (goto-char end)
      (skip-chars-backward " \n")
      (insert-before-markers " );")
      (goto-char beg)
      (skip-chars-forward " \n")
      (insert ";( "))))

(defun quaint-encode-range (beg end)
  (when (> beg end)
    (let ((tmp beg))
      (setq beg end)
      (setq end tmp)))
  (save-excursion
    (goto-char beg)
    (if (inside-encoding-p)
        (error "The region to encode does not start at an encoding boundary."))
    (let ((m (make-marker))
          (inside-encoding nil))
      (set-marker m end)
      (while (or (< (point) m)
                 inside-encoding)
        (let ((c (char-after)))
          (cond
           ;; Unicode characters must be encoded.
           ((> c 127)
            (delete-char 1)
            (insert-before-markers (gethash c quaint-encoder-table)))
           ;; All slashes are assumed to be literal, so they are doubled
           ((= c ?`)
            (setq inside-encoding (not inside-encoding))
            (delete-char 1)
            (insert-before-markers "``"))
           ;; Digraphs are escaped, e.g. <- becomes `<``-`
           ((looking-at quaint-codec-digraph-regexp)
            (delete-char 1)
            (insert-before-markers "`" (char-to-string c) "`")
            (setq c (char-after))
            (delete-char 1)
            (insert-before-markers "`" (char-to-string c) "`"))
           ;; Other characters are ignored
           (t
            (forward-char))))))
    (point)))

(defun quaint-encode-region (&optional count)
  "Encode the region using the Quaint encoding. Unicode
characters are encoded, e.g. λ as `lambda` and ← as
<-. Expressions that normally encode characters are encoded as
well, e.g. `lambda` will become ``lambda`` and <- will
become `<``-`. If this command is executed right after a
yank (paste), the whole pasted region will be encoded."
  (interactive "p")
  (if (and transient-mark-mode mark-active)      
      (goto-char (quaint-encode-range (region-beginning) (region-end)))
    (if (eq last-command 'yank)
        (goto-char (quaint-encode-range (point) (mark)))
      (goto-char (quaint-encode-range (point) (+ (point) count))))))

(defun quaint-newline ()
  "Inserts a new line and indents it. If the point is right after
  the \":\" operator, this inserts \"(\", then a newline, then
  \")\" on the line right after that, and then places the point
  on the new line between the brackets. If anything was after the
  colon, it will be placed on its own line and the point will be
  placed after it."
  (interactive)
  (cond
   ((or (bobp) (eobp))
    (insert "\n"))
   (t
    (while (= (char-before) ?\ )
      (delete-backward-char 1))
    (while (= (char-after) ?\ )
      (delete-char 1))
    (if (not (equal (quaint-prev-operator) ":"))
        (insert "\n")
      (insert " (\n")
      (quaint-indent-line)
      (if (end-of-line-p)
          (insert "\n)")
        (end-of-line)
        (insert "\n\n)"))
      (quaint-indent-line)
      (beginning-of-line)
      (backward-char))
    (quaint-indent-line))))

(defun quaint-electric-closing-delimiter (delim)
  ;; (if (and (looking-at (concat "[ \n]*" delim))
  ;;          (= (quaint-compute-indent (match-end 0))
  ;;             (quaint-current-indent (match-end 0))))
  ;;     (goto-char (match-end 0))
    (insert delim)
    (quaint-indent-line))

(defun quaint-electric-closing-parens ()
  (interactive)
  (quaint-electric-closing-delimiter ")"))

(defun quaint-electric-closing-bracket ()
  (interactive)
  (quaint-electric-closing-delimiter "]"))

(defun quaint-electric-closing-brace ()
  (interactive)
  (quaint-electric-closing-delimiter "}"))



(defun quaint-electric-opening-delimiter (open close)
  (insert open))
  ;; (insert close)
  ;; (backward-char))

(defun quaint-electric-opening-parens ()
  (interactive)
  (quaint-electric-opening-delimiter "(" ")"))

(defun quaint-electric-opening-bracket ()
  (interactive)
  (quaint-electric-opening-delimiter "["  "]"))

(defun quaint-electric-opening-brace ()
  (interactive)
  (quaint-electric-opening-delimiter "{"  "}"))


(provide 'quaint-mode)


;; What to do
;; x Replace \in\ by ∈, etc.
;;   x Make it so that inputting ∈ produces \in\ internally, etc.
;;   x Option to always show expanded version
;;   x Option to never show expanded version
;;   - Option to show the expanded version for the current line
;; x Different colors for:
;;   x Identifier characters
;;   x Strict operator characters
;;   x Lazy operator characters
;;   x Illegal characters
;; x Comments
;;   x ;; ... \n
;;   x ;* ... *;
;; x Strings
;;   x ""
;;   x «» (nested)
;;   x Variable interpolation: ⇑()
;; x Bold face or different color for X in X: Y
;; x Indent rules
;; x Electric parens?

;; FIXME: (very minor) a (b \nc):+ ... does not highlight "a", which
;; is the proper behavior since ":+" is not a special operator, but
;; when the + is removed, "a" is not automatically highlighted. It is
;; highlighted eventually, or if one deletes and reinserts ":". Not
;; sure if there is an easy fix (nor if this ever even occurs in real
;; situations). Extending the range of the font-lock-multiline
;; property did not seem to fix. Same kind of problem happens before
;; the structure, e.g. removing "+" in "a [b\nc] + d:"

;; FIXED with font-lock-multiline? FIXME: there is an issue when
;; editing a multiline <<>> string, which seems to prevent the
;; highlighting of other <<>> strings after it. Re-fontifying the
;; buffer works, and so does modifying lines that are after, or close
;; to the end of the construct.

;; FIXME: (minor) \esc\<< and \esc\>> should not open or close quotes,
;; i.e. <<a b c \esc\>> d e>> is a well-formed complete quote. \esc\<<
;; is escaped properly, it's the closing form that's not handled.
