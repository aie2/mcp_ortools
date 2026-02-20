#!/usr/bin/env python3
"""MCP server that solves linear programs with OR-Tools."""

from __future__ import annotations

from typing import Dict, Mapping, Sequence, Literal
from typing_extensions import TypedDict

from mcp.server.fastmcp import FastMCP
from ortools.linear_solver import pywraplp

Direction = Literal["max", "min"]
Sense = Literal["<=", ">=", "=="]


class VariableBound(TypedDict, total=False):
    lower: float
    upper: float


class Objective(TypedDict, total=False):
    coefficients: Mapping[str, float]
    direction: Direction
    offset: float


class Constraint(TypedDict, total=False):
    coefficients: Mapping[str, float]
    sense: Sense
    rhs: float
    name: str


server = FastMCP("ortools-lp")


def _create_solver(name: str) -> pywraplp.Solver:
    solver = pywraplp.Solver.CreateSolver(name.upper())
    if solver is None:
        raise ValueError(f"Solver backend '{name}' is not available")
    return solver


def _build_variables(
    solver: pywraplp.Solver, definitions: Mapping[str, VariableBound]
) -> Dict[str, pywraplp.Variable]:
    if not definitions:
        raise ValueError("At least one variable must be provided")
    result: Dict[str, pywraplp.Variable] = {}
    for name, bounds in definitions.items():
        lower = float(bounds.get("lower", 0.0))
        upper_bound = bounds.get("upper")
        upper = float(upper_bound) if upper_bound is not None else solver.infinity()
        if lower > upper:
            raise ValueError(
                f"Variable '{name}' has inconsistent bounds: lower={lower} > upper={upper}"
            )
        result[name] = solver.NumVar(lower, upper, name)
    return result


def _set_objective(
    solver: pywraplp.Solver,
    objective: Objective,
    variables: Mapping[str, pywraplp.Variable],
) -> None:
    if not objective:
        raise ValueError("An objective definition is required")
    coefficients = objective.get("coefficients")
    if not coefficients:
        raise ValueError("Objective must define coefficients for at least one variable")

    target = solver.Objective()
    for var_name, coefficient in coefficients.items():
        if var_name not in variables:
            raise ValueError(f"Objective references unknown variable '{var_name}'")
        target.SetCoefficient(variables[var_name], float(coefficient))

    target.SetOffset(float(objective.get("offset", 0.0)))
    direction = str(objective.get("direction", "max")).lower()
    if direction == "max":
        target.SetMaximization()
    elif direction == "min":
        target.SetMinimization()
    else:
        raise ValueError("Objective direction must be either 'max' or 'min'")


def _build_constraints(
    solver: pywraplp.Solver,
    constraints: Sequence[Constraint],
    variables: Mapping[str, pywraplp.Variable],
) -> None:
    for index, constraint in enumerate(constraints):
        sense = constraint.get("sense")
        rhs_raw = constraint.get("rhs")
        if sense not in {"<=", ">=", "=="}:
            raise ValueError(f"Unsupported constraint sense '{sense}'")
        if rhs_raw is None:
            raise ValueError("Each constraint must define an 'rhs' value")
        rhs = float(rhs_raw)
        if sense == "<=":
            low, high = -solver.infinity(), rhs
        elif sense == ">=":
            low, high = rhs, solver.infinity()
        else:
            low = high = rhs

        coefficients = constraint.get("coefficients")
        if not coefficients:
            raise ValueError("Constraints must define at least one coefficient")

        ct_name = constraint.get("name") or f"constraint_{index}"
        ct = solver.Constraint(low, high, ct_name)
        for var_name, coefficient in coefficients.items():
            if var_name not in variables:
                raise ValueError(
                    f"Constraint '{ct_name}' references unknown variable '{var_name}'"
                )
            ct.SetCoefficient(variables[var_name], float(coefficient))


@server.tool()
def solve_linear_program(
    *,
    objective: Objective,
    constraints: Sequence[Constraint],
    variables: Mapping[str, VariableBound],
    solver_name: str = "GLOP",
) -> Dict[str, object]:
    """Solve an LP described with JSON-friendly dictionaries."""

    solver = _create_solver(solver_name)
    var_refs = _build_variables(solver, variables)
    _set_objective(solver, objective, var_refs)
    _build_constraints(solver, constraints, var_refs)

    status = solver.Solve()
    statuses = {
        pywraplp.Solver.OPTIMAL: "OPTIMAL",
        pywraplp.Solver.FEASIBLE: "FEASIBLE",
        pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
        pywraplp.Solver.UNBOUNDED: "UNBOUNDED",
        pywraplp.Solver.ABNORMAL: "ABNORMAL",
    }

    result: Dict[str, object] = {
        "status": statuses.get(status, "UNKNOWN"),
        "wall_time_ms": solver.wall_time(),
        "iterations": solver.iterations(),
        "solver_name": solver_name,
    }

    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        values = {name: var.solution_value() for name, var in var_refs.items()}
        reduced_costs = {name: var.reduced_cost() for name, var in var_refs.items()}
        result.update(
            {
                "objective_value": solver.Objective().Value(),
                "variables": values,
                "reduced_costs": reduced_costs,
            }
        )

    return result


if __name__ == "__main__":
    server.run()
