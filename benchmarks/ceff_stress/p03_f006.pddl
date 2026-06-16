; CEffStress problem p03_f006
(define (problem p03_f006)
  (:domain ceff-stress)
  (:init
    (f13)
    (f16)
    (f17)
    (f3)
    (f5)
    (f6)
    (= (total-cost) 0))
  (:goal (f0))
  (:metric minimize (total-cost))
)
