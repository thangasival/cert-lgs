; Distribution-shift problem p09_train
; Cities: 2, Packages: 3, Trucks: 2, Topology: chain
(define (problem p09_train)
  (:domain distribution-shift)
  (:objects
    city0 city1 - city
    loc0_0 loc0_1 loc0_2 loc1_0 loc1_1 loc1_2 - location
    truck0 truck1 - truck
    pkg0 pkg1 pkg2 - package)
  (:init
    (in-city loc0_0 city0)
    (in-city loc0_1 city0)
    (in-city loc0_2 city0)
    (in-city loc1_0 city1)
    (in-city loc1_1 city1)
    (in-city loc1_2 city1)
    (adjacent loc0_0 loc0_1)
    (adjacent loc0_1 loc0_0)
    (adjacent loc0_1 loc0_2)
    (adjacent loc0_2 loc0_1)
    (adjacent loc1_0 loc1_1)
    (adjacent loc1_1 loc1_0)
    (adjacent loc1_1 loc1_2)
    (adjacent loc1_2 loc1_1)
    (congested loc0_2)
    (at-truck truck0 loc0_0)
    (at-truck truck1 loc1_0)
    (at-package pkg0 loc1_0)
    (at-package pkg1 loc1_1)
    (at-package pkg2 loc1_0)
    (= (total-cost) 0))
  (:goal (and (at-package pkg0 loc1_0)
             (at-package pkg1 loc0_0)
             (at-package pkg2 loc1_0)))
  (:metric minimize (total-cost))
)
