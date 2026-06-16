; Problem p01 — small: 2 cities, 2 locations each, 1 truck, 1 airplane, 1 package
(define (problem logistics-p01)
  (:domain logistics-expressive)

  (:objects
    city1 city2           - city
    loc1a loc1b           - location
    loc2a loc2b           - location
    truck1                - truck
    plane1                - airplane
    pkg1                  - package
  )

  (:init
    ; city membership
    (in-city loc1a city1)
    (in-city loc1b city1)
    (in-city loc2a city2)
    (in-city loc2b city2)
    ; airports
    (airport loc1b)
    (airport loc2b)
    ; initial positions
    (at-truck   truck1 loc1a)
    (at-airplane plane1 loc1b)
    (at-package pkg1   loc1a)
    ; cost counter
    (= (total-cost) 0)
  )

  (:goal (and (at-package pkg1 loc2a)))

  (:metric minimize (total-cost))
)
