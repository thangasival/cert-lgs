; MixedExpressive problem p07
(define (problem p07)
  (:domain mixed-expressive)
  (:init
    (b0)
    (b1)
    (b4)
    (b5)
    (b7)
    (cf1)
    (= (total-cost) 0))
  (:goal (d1))
  (:metric minimize (total-cost))
)
