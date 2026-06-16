; MixedExpressive problem p15
(define (problem p15)
  (:domain mixed-expressive)
  (:init
    (b0)
    (b1)
    (b3)
    (b4)
    (b5)
    (cf1)
    (= (total-cost) 0))
  (:goal (d3))
  (:metric minimize (total-cost))
)
