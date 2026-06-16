from __future__ import annotations

from pathlib import Path
from typing import Any

from cert_lgs.certification.certifier import CertificationLayer
from cert_lgs.learning.model import GuidanceModel
from cert_lgs.planner.parser import parse_task
from cert_lgs.planner.transition_system import TransitionSystem
from cert_lgs.planner.types import Action, Plan, PlanStep, PlannerResult, SymbolicStateSet, TransitionRelation


class SymbolicSearchPlanner:
    """Expressive symbolic-search planner with certified learned guidance.

    Uses uniform-cost (Dijkstra) search over explicit state sets.  Learned
    proposals affect state/transition ordering but every correctness-relevant
    decision is routed through CertificationLayer before execution.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        domain_dirs = config.get("benchmark", {}).get("domains", ["benchmarks/toy_expressive"])
        self.task = parse_task(Path(domain_dirs[0]))
        # Build transition system from real Action objects if available.
        if self.task.actions:
            self.transition_system = TransitionSystem(self.task.actions)
            self._action_map: dict[str, Action] = {a.name: a for a in self.task.actions}
        else:
            self.transition_system = TransitionSystem(self.task.transitions)
            self._action_map = {}

    # ------------------------------------------------------------------
    # Main solving entry point
    # ------------------------------------------------------------------

    def solve_with_guidance(
        self,
        guide: GuidanceModel,
        certifier: CertificationLayer,
    ) -> PlannerResult:
        if self.task.actions:
            return self._real_search(guide, certifier)
        return self._legacy_search(guide, certifier)

    # ------------------------------------------------------------------
    # Real UCS search over explicit states
    # ------------------------------------------------------------------

    def _real_search(
        self,
        guide: GuidanceModel,
        certifier: CertificationLayer,
    ) -> PlannerResult:
        certifier.set_task(self.task)  # enable non-trivial h_cert in C3
        initial_atoms = self.task.initial_atoms
        goal_atoms = self.task.goal_atoms

        open_list: list[SymbolicStateSet] = [
            SymbolicStateSet(name="I", states=initial_atoms, g_cost=0.0)
        ]
        # Maps frozenset[atoms] → (g_cost, parent_atoms | None, action_name | None)
        parent_map: dict[frozenset, tuple[float, frozenset | None, str | None]] = {
            initial_atoms: (0.0, None, None)
        }
        expanded = 0
        incumbent_cost = float("inf")
        best_plan: Plan | None = None

        while open_list:
            # --- Learned guidance proposals ---
            proposals = guide.propose(
                open_list=open_list,
                transitions=self.task.transitions,
                goal_atoms=self.task.goal_atoms,
            )
            closed_snapshot = [
                SymbolicStateSet("c", atoms, g)
                for atoms, (g, _, _) in parent_map.items()
            ]
            certified = certifier.filter_proposals(
                proposals=proposals,
                open_list=open_list,
                closed=closed_snapshot,
                incumbent_cost=incumbent_cost,
            )

            # --- Select state: lowest g-cost (UCS); guidance may reorder ---
            selected = certified.select_state(open_list)
            open_list.remove(selected)

            current_atoms = selected.states
            current_g = parent_map[current_atoms][0]
            expanded += 1

            # --- Expand: apply all applicable actions ---
            for action_name, succ_atoms, action_cost in self.transition_system.successors(
                current_atoms
            ):
                new_g = current_g + action_cost
                transition = TransitionRelation(
                    name=action_name, action_schema=action_name, cost=action_cost
                )
                succ_sss = SymbolicStateSet(
                    name=f"{selected.name}:{action_name}",
                    states=succ_atoms,
                    g_cost=new_g,
                )

                action_obj = self._action_map.get(action_name)
                if not certifier.valid_transition(selected, transition, succ_sss, action=action_obj):
                    continue

                # Skip if already reached with equal or lower cost.
                existing_g = parent_map.get(succ_atoms, (float("inf"),))[0]
                if new_g >= existing_g:
                    continue

                # Goal check.
                if goal_atoms.issubset(succ_atoms):
                    if new_g < incumbent_cost:
                        incumbent_cost = new_g
                        parent_map[succ_atoms] = (new_g, current_atoms, action_name)
                        steps = self._extract_plan(parent_map, succ_atoms)
                        candidate = Plan(steps=steps)
                        if certifier.valid_plan(candidate):
                            best_plan = candidate
                    continue

                # Bound / dominance check.
                closed_for_check = [
                    SymbolicStateSet("c", a, g) for a, (g, _, _) in parent_map.items()
                ]
                if not certifier.safe_to_enqueue(succ_sss, closed_for_check, incumbent_cost):
                    continue

                parent_map[succ_atoms] = (new_g, current_atoms, action_name)
                open_list.append(succ_sss)

            # Early termination: all remaining open states cannot improve incumbent.
            if best_plan is not None and all(
                s.g_cost >= incumbent_cost for s in open_list
            ):
                break

        return PlannerResult(
            status="solved" if best_plan else "unsolvable",
            plan=best_plan,
            plan_cost=best_plan.cost if best_plan else None,
            expanded=expanded,
            certificates_checked=certifier.checked,
            certificates_rejected=certifier.rejected,
            diagnostics=certifier.diagnostics(),
        )

    def _extract_plan(
        self,
        parent_map: dict,
        goal_atoms: frozenset,
    ) -> list[PlanStep]:
        steps: list[PlanStep] = []
        current = goal_atoms
        while True:
            g, parent_atoms, action_name = parent_map[current]
            if parent_atoms is None:
                break
            parent_g = parent_map[parent_atoms][0]
            steps.append(PlanStep(action=action_name, cost=g - parent_g))
            current = parent_atoms
        steps.reverse()
        return steps

    # ------------------------------------------------------------------
    # Legacy stub search (used when no real actions are available)
    # ------------------------------------------------------------------

    def _legacy_search(
        self,
        guide: GuidanceModel,
        certifier: CertificationLayer,
    ) -> PlannerResult:
        open_list: list[SymbolicStateSet] = [self.task.initial]
        closed: list[SymbolicStateSet] = []
        expanded = 0
        best_plan: Plan | None = None
        incumbent_cost = float("inf")

        while open_list and expanded < 100:
            proposals = guide.propose(
                open_list=open_list,
                transitions=self.task.transitions,
                goal_atoms=self.task.goal_atoms,
            )
            certified = certifier.filter_proposals(
                proposals=proposals,
                open_list=open_list,
                closed=closed,
                incumbent_cost=incumbent_cost,
            )

            selected_state = certified.select_state(open_list)
            selected_transition = certified.select_transition(self.task.transitions)

            successor = self.transition_system.expand(selected_state, selected_transition)

            if certifier.valid_transition(selected_state, selected_transition, successor):
                if certifier.safe_to_enqueue(successor, closed, incumbent_cost):
                    open_list.append(successor)

            if selected_state in open_list:
                open_list.remove(selected_state)
            closed.append(selected_state)
            expanded += 1

        return PlannerResult(
            status="unknown",
            plan=best_plan,
            plan_cost=None,
            expanded=expanded,
            certificates_checked=certifier.checked,
            certificates_rejected=certifier.rejected,
            diagnostics=certifier.diagnostics(),
        )
