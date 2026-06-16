; Problem p03 — medium: 3 cities, 2 trucks, 1 airplane, 3 packages
(define (problem logistics-p03)
  (:domain logistics-expressive)

  (:objects
    city1 city2 city3              - city
    loc1a loc1b loc1c              - location
    loc2a loc2b                    - location
    loc3a loc3b                    - location
    truck1 truck2                  - truck
    plane1                         - airplane
    pkg1 pkg2 pkg3                 - package
  )

  (:init
    (in-city loc1a city1) (in-city loc1b city1) (in-city loc1c city1)
    (in-city loc2a city2) (in-city loc2b city2)
    (in-city loc3a city3) (in-city loc3b city3)
    (airport loc1c) (airport loc2b) (airport loc3b)
    (at-truck   truck1 loc1a)
    (at-truck   truck2 loc2a)
    (at-airplane plane1 loc1c)
    (at-package pkg1 loc1a)
    (at-package pkg2 loc2a)
    (at-package pkg3 loc3a)
    (low-fuel plane1)
    (= (total-cost) 0)
  )

  (:goal (and (at-package pkg1 loc3a)
              (at-package pkg2 loc1a)
              (at-package pkg3 loc2a)))

  (:metric minimize (total-cost))
)
