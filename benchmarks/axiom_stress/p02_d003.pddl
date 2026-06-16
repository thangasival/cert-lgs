; AxiomStress problem p02_d003
(define (problem p02_d003)
  (:domain axiom-stress)
  (:init
    (base-0)
    (base-1)
    (base-2)
    (base-4)
    (base-6)
    (= (total-cost) 0))
  (:goal (derived-2))
  (:metric minimize (total-cost))
)
