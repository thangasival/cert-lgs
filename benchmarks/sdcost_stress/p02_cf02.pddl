; SDCostStress problem p02_cf02
(define (problem p02_cf02)
  (:domain sdcost-stress)
  (:init
    (cost-state-0)
    (cost-state-2)
    (= (total-cost) 0))
  (:goal (and (op-2-done)
             (op-3-done)
             (op-7-done)
             (op-0-done)))
  (:metric minimize (total-cost))
)
