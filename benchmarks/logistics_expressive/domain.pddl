; Expressive Logistics Domain (Group 1 benchmark for Cert-LGS)
; Features: parameterised actions, conditional effects, :derived predicates (axioms),
;           state-dependent action costs (:action-costs / increase).
; Requires: :typing :conditional-effects :derived-predicates :action-costs

(define (domain logistics-expressive)
  (:requirements :typing :conditional-effects :derived-predicates :action-costs)

  (:types
    location - object
    city     - object
    truck    - object
    airplane - object
    package  - object
    vehicle  - object
    truck    - vehicle
    airplane - vehicle
  )

  (:predicates
    ; physical positions
    (at-truck     ?t - truck    ?l - location)
    (at-airplane  ?a - airplane ?l - location)
    (at-package   ?p - package  ?l - location)

    ; load state
    (in-truck     ?p - package  ?t - truck)
    (in-airplane  ?p - package  ?a - airplane)

    ; city membership
    (in-city      ?l - location ?c - city)
    (airport      ?l - location)         ; l is the airport of its city

    ; fuel status (affects cost via conditional effect)
    (low-fuel     ?v - vehicle)

    ; derived / axiom predicates
    (reachable-by-truck   ?p - package  ?l - location)
    (reachable-by-air     ?p - package  ?l - location)
    (delivered            ?p - package  ?l - location)
  )

  ; ── Derived predicates (axioms) ──────────────────────────────────────────
  ; A package is reachable by truck from its current city if the destination
  ; is in the same city as any truck that is co-located with the package.
  (:derived (reachable-by-truck ?p - package ?l - location)
    (exists (?t - truck ?l2 - location ?c - city)
      (and (in-city ?l2 ?c)
           (in-city ?l  ?c)
           (at-package ?p ?l2)
           (at-truck   ?t ?l2)))
  )

  ; A package is reachable by air if there is an airplane at an airport in
  ; the same city as the package.
  (:derived (reachable-by-air ?p - package ?l - location)
    (exists (?a - airplane ?l2 - location ?c - city)
      (and (airport ?l2)
           (in-city ?l2 ?c)
           (at-package  ?p ?l2)
           (at-airplane ?a ?l2)))
  )

  ; Package is considered delivered once it reaches the goal location.
  (:derived (delivered ?p - package ?l - location)
    (at-package ?p ?l)
  )

  ; ── Functions (for action costs) ─────────────────────────────────────────
  (:functions
    (total-cost)
  )

  ; ── Actions ──────────────────────────────────────────────────────────────

  ; Load package onto a truck at the same location.
  (:action load-truck
    :parameters (?p - package ?t - truck ?l - location)
    :precondition (and (at-package ?p ?l)
                       (at-truck   ?t ?l))
    :effect (and (in-truck   ?p ?t)
                 (not (at-package ?p ?l))
                 (increase (total-cost) 1))
  )

  ; Unload package from truck at current location.
  (:action unload-truck
    :parameters (?p - package ?t - truck ?l - location)
    :precondition (and (in-truck  ?p ?t)
                       (at-truck  ?t ?l))
    :effect (and (at-package  ?p ?l)
                 (not (in-truck ?p ?t))
                 (increase (total-cost) 1))
  )

  ; Load package onto airplane.
  (:action load-airplane
    :parameters (?p - package ?a - airplane ?l - location)
    :precondition (and (at-package  ?p ?l)
                       (at-airplane ?a ?l)
                       (airport     ?l))
    :effect (and (in-airplane   ?p ?a)
                 (not (at-package ?p ?l))
                 (increase (total-cost) 1))
  )

  ; Unload package from airplane.
  (:action unload-airplane
    :parameters (?p - package ?a - airplane ?l - location)
    :precondition (and (in-airplane  ?p ?a)
                       (at-airplane  ?a ?l)
                       (airport      ?l))
    :effect (and (at-package     ?p ?l)
                 (not (in-airplane ?p ?a))
                 (increase (total-cost) 1))
  )

  ; Drive truck within same city.
  ; Conditional effect: costs 3 if low-fuel, else 2.
  (:action drive-truck
    :parameters (?t - truck ?from - location ?to - location ?c - city)
    :precondition (and (at-truck  ?t ?from)
                       (in-city   ?from ?c)
                       (in-city   ?to   ?c))
    :effect (and (at-truck      ?t ?to)
                 (not (at-truck ?t ?from))
                 ; conditional: base cost increase
                 (increase (total-cost) 2)
                 ; conditional effect: extra fuel penalty when low
                 (when (low-fuel ?t)
                   (increase (total-cost) 1)))
  )

  ; Fly airplane between airports.
  ; Conditional effect: costs 10 if low-fuel, else 5.
  (:action fly-airplane
    :parameters (?a - airplane ?from - location ?to - location)
    :precondition (and (at-airplane ?a ?from)
                       (airport     ?from)
                       (airport     ?to))
    :effect (and (at-airplane      ?a ?to)
                 (not (at-airplane ?a ?from))
                 (increase (total-cost) 5)
                 (when (low-fuel ?a)
                   (increase (total-cost) 5)))
  )

  ; Refuel vehicle at any location — removes low-fuel flag.
  (:action refuel
    :parameters (?v - vehicle ?l - location)
    :precondition (and (low-fuel ?v))
    :effect (and (not (low-fuel ?v))
                 (increase (total-cost) 1))
  )
)
