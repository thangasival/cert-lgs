; MixedExpressive problem p01
(define (problem p01)
  (:domain mixed-expressive)
  (:init
    (b0)
    (b1)
    (b2)
    (b5)
    (cf0)
    (= (total-cost) 0))
  (:goal (d1))
  (:metric minimize (total-cost))
)
