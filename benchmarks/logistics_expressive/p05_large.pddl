; Problem p05 — large: 5 cities, 4 trucks, 3 airplanes, 8 packages
; Multiple conditional effects active; tests axiom-closure at scale.
(define (problem logistics-p05)
  (:domain logistics-expressive)

  (:objects
    city1 city2 city3 city4 city5              - city
    loc1a loc1b loc1c                          - location
    loc2a loc2b loc2c                          - location
    loc3a loc3b                                - location
    loc4a loc4b                                - location
    loc5a loc5b                                - location
    truck1 truck2 truck3 truck4                - truck
    plane1 plane2 plane3                       - airplane
    pkg1 pkg2 pkg3 pkg4 pkg5 pkg6 pkg7 pkg8   - package
  )

  (:init
    (in-city loc1a city1) (in-city loc1b city1) (in-city loc1c city1)
    (in-city loc2a city2) (in-city loc2b city2) (in-city loc2c city2)
    (in-city loc3a city3) (in-city loc3b city3)
    (in-city loc4a city4) (in-city loc4b city4)
    (in-city loc5a city5) (in-city loc5b city5)
    (airport loc1c) (airport loc2c) (airport loc3b) (airport loc4b) (airport loc5b)
    ; trucks
    (at-truck truck1 loc1a)
    (at-truck truck2 loc2a)
    (at-truck truck3 loc3a)
    (at-truck truck4 loc4a)
    ; airplanes
    (at-airplane plane1 loc1c)
    (at-airplane plane2 loc2c)
    (at-airplane plane3 loc5b)
    ; packages spread across cities
    (at-package pkg1 loc1a)
    (at-package pkg2 loc1b)
    (at-package pkg3 loc2a)
    (at-package pkg4 loc2b)
    (at-package pkg5 loc3a)
    (at-package pkg6 loc4a)
    (at-package pkg7 loc5a)
    (at-package pkg8 loc5b)
    ; multiple vehicles with low fuel
    (low-fuel truck1)
    (low-fuel truck3)
    (low-fuel plane2)
    (= (total-cost) 0)
  )

  (:goal (and (at-package pkg1 loc5a)
              (at-package pkg2 loc4a)
              (at-package pkg3 loc5a)
              (at-package pkg4 loc3a)
              (at-package pkg5 loc2a)
              (at-package pkg6 loc1a)
              (at-package pkg7 loc1a)
              (at-package pkg8 loc2a)))

  (:metric minimize (total-cost))
)
