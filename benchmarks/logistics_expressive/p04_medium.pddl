; Problem p04 — medium: 4 cities, 3 trucks, 2 airplanes, 5 packages
(define (problem logistics-p04)
  (:domain logistics-expressive)

  (:objects
    city1 city2 city3 city4           - city
    loc1a loc1b loc1c                 - location
    loc2a loc2b                       - location
    loc3a loc3b                       - location
    loc4a loc4b                       - location
    truck1 truck2 truck3              - truck
    plane1 plane2                     - airplane
    pkg1 pkg2 pkg3 pkg4 pkg5          - package
  )

  (:init
    (in-city loc1a city1) (in-city loc1b city1) (in-city loc1c city1)
    (in-city loc2a city2) (in-city loc2b city2)
    (in-city loc3a city3) (in-city loc3b city3)
    (in-city loc4a city4) (in-city loc4b city4)
    (airport loc1c) (airport loc2b) (airport loc3b) (airport loc4b)
    (at-truck   truck1 loc1a)
    (at-truck   truck2 loc2a)
    (at-truck   truck3 loc3a)
    (at-airplane plane1 loc1c)
    (at-airplane plane2 loc3b)
    (at-package pkg1 loc1a)
    (at-package pkg2 loc1b)
    (at-package pkg3 loc2a)
    (at-package pkg4 loc3a)
    (at-package pkg5 loc4a)
    (low-fuel truck2)
    (low-fuel plane2)
    (= (total-cost) 0)
  )

  (:goal (and (at-package pkg1 loc4a)
              (at-package pkg2 loc3a)
              (at-package pkg3 loc4a)
              (at-package pkg4 loc1a)
              (at-package pkg5 loc2a)))

  (:metric minimize (total-cost))
)
