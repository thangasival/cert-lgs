; MixedExpressive problem p11
(define (problem p11)
  (:domain mixed-expressive)
  (:init
    (b0)
    (b1)
    (b4)
    (b5)
    (b7)
    (cf1)
    (= (total-cost) 0))
  (:goal (d2))
  (:metric minimize (total-cost))
)
