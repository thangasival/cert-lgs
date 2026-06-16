; Problem p02 — small: 2 cities, 2 packages, low-fuel conditional-effect active
(define (problem logistics-p02)
  (:domain logistics-expressive)

  (:objects
    city1 city2           - city
    loc1a loc1b           - location
    loc2a loc2b           - location
    truck1                - truck
    plane1                - airplane
    pkg1 pkg2             - package
  )

  (:init
    (in-city loc1a city1) (in-city loc1b city1)
    (in-city loc2a city2) (in-city loc2b city2)
    (airport loc1b) (airport loc2b)
    (at-truck   truck1 loc1a)
    (at-airplane plane1 loc1b)
    (at-package pkg1 loc1a)
    (at-package pkg2 loc1b)
    ; truck starts with low fuel — tests conditional-effect cost branch
    (low-fuel truck1)
    (= (total-cost) 0)
  )

  (:goal (and (at-package pkg1 loc2a)
              (at-package pkg2 loc2b)))

  (:metric minimize (total-cost))
)
