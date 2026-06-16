; MixedExpressive problem p06
(define (problem p06)
  (:domain mixed-expressive)
  (:init
    (b0)
    (b1)
    (b3)
    (b4)
    (b5)
    (cf1)
    (= (total-cost) 0))
  (:goal (d2))
  (:metric minimize (total-cost))
)
