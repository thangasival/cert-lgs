; MixedExpressive problem p05
(define (problem p05)
  (:domain mixed-expressive)
  (:init
    (b0)
    (b1)
    (b3)
    (b4)
    (cf2)
    (= (total-cost) 0))
  (:goal (d1))
  (:metric minimize (total-cost))
)
