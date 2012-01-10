;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; POPULATE HASH TABLE ;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;

;; quaint-codec-data.el must provide:
;; - quaint-codec-digraphs-list: a list of cons of (digraph . character)
;; - quaint-codec-named-codes-list: a list of cons of (name . character)
;; The two lists are used to build a translation hash and the entries
;; of quaint-codec-digraphs-list are glued together with regexp-opt
;; to form a matcher.

(load "quaint-codec-data.el")

(defvar quaint-codec-table
  (make-hash-table :test 'equal)
  "Hash table mapping string encoding -> unicode character code.")

(defun quaint-codec-add-entry (entry &optional add_delims)
  "Add an entry to `quaint-codec-table'. entry must be a cons
  of (name . character), and add_delims is t if the name
  must be mapped to `name`, nil if the name is to be added
  as-is."
  (let ((name (car entry))
        (character (cdr entry)))
    (puthash (if add_delims (concat
                             quaint-codec-delim-start
                             name
                             quaint-codec-delim-end) name)
             character quaint-codec-table)))

(defun quaint-codec-add-digraph (entry)
  (quaint-codec-add-entry entry))

(defun quaint-codec-add-named-code (entry)
  (quaint-codec-add-entry entry 't))

(defun quaint-codec-populate-codec-table ()
  (mapcar 'quaint-codec-add-digraph quaint-codec-digraphs-list)
  (mapcar 'quaint-codec-add-named-code quaint-codec-named-codes-list))

(quaint-codec-populate-codec-table)


;;;;;;;;;;;;;;;;;;;;;
;;; CODEC MATCHER ;;;
;;;;;;;;;;;;;;;;;;;;;

(defvar quaint-codec-named-code-regexp
  "`[a-zA-Z0-9\"'^<>=~|/\\-\\\\]*`"
  "Regular expression matching characters encoded like
`.*`. Not all characters are valid. Valid characters are
letters a-z and A-Z, numbers 0-9, \" (umlaut), ' (acute),
\\ (grave), ^ (circumflex), and <>=~|/- to specifically encode
characters that may be grouped in a digraph otherwise.")

(defvar quaint-codec-digraph-regexp
  (regexp-opt (mapcar 'car quaint-codec-digraphs-list))
  "Regular expression to match a digraph in quaint")

(defvar quaint-codec-regexp
  (concat quaint-codec-named-code-regexp
          "\\|"
          (regexp-opt (mapcar 'car quaint-codec-digraphs-list)))
  "Regular expression matching encoded characters, i.e. `.*`
  or individual digraphs such as <-, <>, etc.")

(defvar quaint-codec-code
  `((,quaint-codec-regexp
     (0
      (let ((character (gethash (match-string 0) quaint-codec-table nil)))
        (if (not character)
            font-lock-warning-face
          (compose-region 
           (match-beginning 0)
           (match-end 0)
           character)
          (if (equal character ?`)
              font-lock-warning-face
            nil))))))
  "Entry for font-lock-keywords that decodes encoded characters
  into their corresponding Unicode character. The hash table
  `quaint-codec-table' is used to look up the character to
  replace the expression with. If `xxx` is matched, where xxx
  is an invalid name for a Unicode character and is thus not
  found in the hash, the expression is highlighted with
  font-lock-warning-face. Also, ``, which encodes a single
  backquote (`), is highlighted with font-lock-warning-face, to
  distinguish it from single unmatched backslashes. It might be
  preferable to highlight single unmatched backslashes instead!")


;;;;;;;;;;;;;;;;;;;
;;; BOILERPLATE ;;;
;;;;;;;;;;;;;;;;;;;

;; Modified code found at:
;; http://www.emacswiki.org/emacs/pretty-lambdada.el

;;;###autoload
(defgroup quaint-codec nil
  "Special minor mode for the quaint codec. Displays `lambda`
as λ (the backslashes are mandatory), <- as ←, <> as ♦, etc. True
unicode characters are also encoded that way for saving
purposes."
  :group 'convenience :group 'programming)

;; ;;;###autoload
;; (defcustom quaint-codec-auto-modes
;;   '(quaint-mode)
;;   "*Modes affected by `quaint-codec-for-modes'."
;;   :type '(repeat symbol) :group 'quaint-codec)

;; ;;;###autoload
;; (defun quaint-codec-for-modes (&optional turn-off)
;;   "Use `quaint-codec-mode' for modes in `quaint-codec-auto-modes'.
;; `C-u' to turn off."
;;   (interactive "P")
;;   (let (hook-var)
;;     (cond (turn-off
;;            (dolist (m  quaint-codec-auto-modes)
;;              (remove-hook (setq hook-var (intern (concat (symbol-name m) "-hook")))
;;                           'turn-on-quaint-codec-mode)
;;              (add-hook hook-var 'turn-off-quaint-codec-mode))
;;            (when (memq major-mode quaint-codec-auto-modes)
;;              (turn-off-quaint-codec-mode))) ; Current buffer
;;           (t
;;            (dolist (m  quaint-codec-auto-modes)
;;              (remove-hook (setq hook-var (intern (concat (symbol-name m) "-hook")))
;;                           'turn-off-quaint-codec-mode)
;;              (add-hook hook-var 'turn-on-quaint-codec-mode))
;;            (when (memq major-mode quaint-codec-auto-modes)
;;              (turn-on-quaint-codec-mode)))))) ; Current buffer

;;;###autoload
(define-minor-mode quaint-codec-mode
  "Buffer-local minor mode for the quaint codec. Displays `lambda`
as λ (the backslashes are mandatory), <- as ←, <> as ♦, etc. True
unicode characters are also encoded that way for saving
purposes.
With ARG, turn mode on if ARG is positive, off otherwise."
  :init-value nil
  (cond (quaint-codec-mode
         (quaint-codec)
         (font-lock-fontify-buffer))
        (t
         (font-lock-remove-keywords
          nil quaint-codec-code)
         (save-excursion
           (goto-char (point-min))
           (while (re-search-forward quaint-codec-regexp nil t)
             (decompose-region (match-beginning 0) (match-end 0)))))))

;;;###autoload
(define-globalized-minor-mode global-quaint-codec-mode
    quaint-codec-mode turn-on-quaint-codec-mode
  "Global minor mode for the quaint codec. Displays `lambda`
as λ (the backslashes are mandatory), <- as ←, <> as ♦, etc. True
unicode characters are also encoded that way for saving purposes.
With ARG, turn mode on if ARG is positive, off otherwise.")

(defun quaint-codec (&optional mode)
  "Displays `lambda` as λ (the backslashes are mandatory), <-
as ←, <> as ♦, etc. True unicode characters are also encoded that
way for saving purposes.
Non-nil optional arg means use quaint-codec display in that MODE.
nil means use quaint-codec display for the current mode."
  (font-lock-add-keywords
   mode quaint-codec-code))

(defun turn-on-quaint-codec-mode  () (quaint-codec-mode  1))
(defun turn-off-quaint-codec-mode () (quaint-codec-mode -1))
