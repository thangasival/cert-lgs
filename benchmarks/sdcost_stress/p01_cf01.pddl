; SDCostStress problem p01_cf01
(define (problem p01_cf01)
  (:domain sdcost-stress)
  (:init
    (cost-state-0)
    (= (total-cost) 0))
  (:goal (and (op-0-done)
             (op-5-done)
             (op-2-done)
             (op-1-done)))
  (:metric minimize (total-cost))
)
