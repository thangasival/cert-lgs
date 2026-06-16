; SDCostStress problem p03_cf03
(define (problem p03_cf03)
  (:domain sdcost-stress)
  (:init
    (cost-state-0)
    (cost-state-3)
    (cost-state-4)
    (= (total-cost) 0))
  (:goal (and (op-6-done)
             (op-1-done)
             (op-2-done)
             (op-0-done)))
  (:metric minimize (total-cost))
)
