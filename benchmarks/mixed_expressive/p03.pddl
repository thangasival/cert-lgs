; MixedExpressive problem p03
(define (problem p03)
  (:domain mixed-expressive)
  (:init
    (b0)
    (b1)
    (b4)
    (b6)
    (b7)
    (cf0)
    (= (total-cost) 0))
  (:goal (d3))
  (:metric minimize (total-cost))
)
