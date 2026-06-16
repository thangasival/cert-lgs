; CEffStress problem p02_f005
(define (problem p02_f005)
  (:domain ceff-stress)
  (:init
    (f1)
    (f9)
    (f4)
    (f14)
    (f11)
    (= (total-cost) 0))
  (:goal (f0))
  (:metric minimize (total-cost))
)
