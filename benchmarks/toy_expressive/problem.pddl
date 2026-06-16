(define (problem toy-logistics-1)
  (:domain toy-expressive-logistics)
  (:objects)
  (:init
    (at-truck-loc1)
    (= (total-cost) 0))
  (:goal (delivered))
  (:metric minimize (total-cost)))
