; SDCostStress problem p06_cf01
(define (problem p06_cf01)
  (:domain sdcost-stress)
  (:init
    (cost-state-2)
    (= (total-cost) 0))
  (:goal (and (op-1-done)
             (op-3-done)
             (op-4-done)
             (op-6-done)))
  (:metric minimize (total-cost))
)
