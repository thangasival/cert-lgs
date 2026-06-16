; CEffStress problem p01_f004
(define (problem p01_f004)
  (:domain ceff-stress)
  (:init
    (f3)
    (f0)
    (f8)
    (f7)
    (= (total-cost) 0))
  (:goal (f1))
  (:metric minimize (total-cost))
)
