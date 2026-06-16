; SDCostStress problem p07_cf02
(define (problem p07_cf02)
  (:domain sdcost-stress)
  (:init
    (cost-state-2)
    (cost-state-4)
    (= (total-cost) 0))
  (:goal (and (op-2-done)
             (op-4-done)
             (op-5-done)
             (op-6-done)))
  (:metric minimize (total-cost))
)
