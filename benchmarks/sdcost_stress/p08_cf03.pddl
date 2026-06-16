; SDCostStress problem p08_cf03
(define (problem p08_cf03)
  (:domain sdcost-stress)
  (:init
    (cost-state-0)
    (cost-state-1)
    (cost-state-2)
    (= (total-cost) 0))
  (:goal (and (op-1-done)
             (op-2-done)
             (op-4-done)
             (op-5-done)))
  (:metric minimize (total-cost))
)
