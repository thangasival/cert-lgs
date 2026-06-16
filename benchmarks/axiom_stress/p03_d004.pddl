; AxiomStress problem p03_d004
(define (problem p03_d004)
  (:domain axiom-stress)
  (:init
    (base-0)
    (base-1)
    (base-3)
    (base-8)
    (base-10)
    (base-12)
    (= (total-cost) 0))
  (:goal (derived-3))
  (:metric minimize (total-cost))
)
