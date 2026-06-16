; AxiomStress problem p01_d002
(define (problem p01_d002)
  (:domain axiom-stress)
  (:init
    (base-0)
    (base-1)
    (base-3)
    (base-12)
    (= (total-cost) 0))
  (:goal (derived-1))
  (:metric minimize (total-cost))
)
