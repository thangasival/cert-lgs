; MixedExpressive problem p08
(define (problem p08)
  (:domain mixed-expressive)
  (:init
    (b0)
    (b1)
    (b2)
    (b3)
    (cf1)
    (= (total-cost) 0))
  (:goal (d0))
  (:metric minimize (total-cost))
)
