(define (domain toy-expressive-logistics)
  (:requirements :strips :action-costs :conditional-effects)

  (:predicates
    (at-truck-loc1)
    (at-truck-loc2)
    (in-truck)
    (box-in-transit)
    (delivered))

  (:functions (total-cost))

  ; Load box onto truck at loc1.
  (:action load-at-loc1
    :parameters ()
    :precondition (at-truck-loc1)
    :effect (and
      (in-truck)
      (increase (total-cost) 1)))

  ; Drive from loc1 to loc2.
  ; Conditional effect: if box is already loaded, mark box-in-transit.
  (:action move-loc1-to-loc2
    :parameters ()
    :precondition (at-truck-loc1)
    :effect (and
      (at-truck-loc2)
      (not (at-truck-loc1))
      (when (in-truck) (box-in-transit))
      (increase (total-cost) 2)))

  ; Drive back from loc2 to loc1.
  ; Conditional effect: clear box-in-transit when returning empty.
  (:action move-loc2-to-loc1
    :parameters ()
    :precondition (at-truck-loc2)
    :effect (and
      (at-truck-loc1)
      (not (at-truck-loc2))
      (when (box-in-transit) (not (box-in-transit)))
      (increase (total-cost) 2)))

  ; Deliver box at loc2.
  (:action deliver-at-loc2
    :parameters ()
    :precondition (and (at-truck-loc2) (in-truck))
    :effect (and
      (delivered)
      (not (in-truck))
      (not (box-in-transit))
      (increase (total-cost) 1)))
)
