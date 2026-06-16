; MixedExpressive problem p14
(define (problem p14)
  (:domain mixed-expressive)
  (:init
    (b0)
    (b1)
    (b2)
    (b6)
    (b7)
    (cf0)
    (= (total-cost) 0))
  (:goal (d1))
  (:metric minimize (total-cost))
)
