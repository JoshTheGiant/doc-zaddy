; Define some facts
(define-atom greeting "Hello from MeTTa!")
(define-atom agent-type "autonomous")

; Define a rule
(= (get-greeting) (greeting))

; Query
!(get-greeting)