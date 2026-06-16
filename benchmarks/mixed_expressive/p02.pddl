; MixedExpressive problem p02
(define (problem p02)
  (:domain mixed-expressive)
  (:init
    (b0)
    (b1)
    (b2)
    (b5)
    (cf1)
    (= (total-cost) 0))
  (:goal (d2))
  (:metric minimize (total-cost))
)
