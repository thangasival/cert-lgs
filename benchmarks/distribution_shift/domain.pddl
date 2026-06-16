; Distribution-Shift domain (Group 3 benchmark for Cert-LGS)
; Same action schema as logistics_expressive but with wider object types,
; used to test whether certified guidance generalises from small (train-size)
; to large (test-size) problem instances.
;
; Train split: problems with ≤ 2 cities, ≤ 3 packages (p01–p10)
; Test split:  problems with ≥ 4 cities, ≥ 5 packages (p11–p20)
; OOD split:  problems with ≥ 6 cities, novel structure (p21–p25)

(define (domain distribution-shift)
  (:requirements :typing :conditional-effects :derived-predicates :action-costs)

  (:types
    location - object
    city     - object
    vehicle  - object
    truck    - vehicle
    package  - object
  )

  (:predicates
    (at-truck   ?t - truck    ?l - location)
    (at-package ?p - package  ?l - location)
    (in-truck   ?p - package  ?t - truck)
    (in-city    ?l - location ?c - city)
    (adjacent   ?l1 - location ?l2 - location)
    (congested  ?l - location)          ; causes cost penalty (SDAC)
    (hub        ?l - location)          ; derived: is a hub location
    (reachable  ?p - package ?l - location)
  )

  ; Hub: a location that is directly adjacent to at least two others
  (:derived (hub ?l - location)
    (exists (?l2 - location ?l3 - location)
      (and (adjacent ?l ?l2)
           (adjacent ?l ?l3)
           (not (= ?l2 ?l3))))
  )

  ; Reachability via truck co-location
  (:derived (reachable ?p - package ?l - location)
    (exists (?t - truck ?l2 - location ?c - city)
      (and (at-package ?p ?l2)
           (at-truck   ?t ?l2)
           (in-city    ?l2 ?c)
           (in-city    ?l  ?c)))
  )

  (:functions (total-cost))

  (:action load-truck
    :parameters (?p - package ?t - truck ?l - location)
    :precondition (and (at-package ?p ?l) (at-truck ?t ?l))
    :effect (and (in-truck ?p ?t) (not (at-package ?p ?l))
                 (increase (total-cost) 1)))

  (:action unload-truck
    :parameters (?p - package ?t - truck ?l - location)
    :precondition (and (in-truck ?p ?t) (at-truck ?t ?l))
    :effect (and (at-package ?p ?l) (not (in-truck ?p ?t))
                 (increase (total-cost) 1)))

  ; Drive with conditional congestion penalty
  (:action drive
    :parameters (?t - truck ?from - location ?to - location)
    :precondition (and (at-truck ?t ?from) (adjacent ?from ?to))
    :effect (and (at-truck ?t ?to) (not (at-truck ?t ?from))
                 (increase (total-cost) 1)
                 (when (congested ?to) (increase (total-cost) 2))))
)
