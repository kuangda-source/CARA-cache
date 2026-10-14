"""Offline E0 algebra and independent receipt checks; no model or policy writes."""
import math


def near(actual, expected, label, rel=2e-8, absolute=1e-10):
    if not math.isfinite(actual) or not math.isclose(actual, expected, rel_tol=rel, abs_tol=absolute):
        raise ValueError(f"{label}: {actual!r} != {expected!r}")


def scalar_oracles(mc, mu, cross):
    """Absolute per-element moments of post-RF errors (candidate minus dense).

    Pc/Pu are global scalar, same-state OFFLINE oracles. Their coefficients
    use the omitted branch teacher and are not deployable online features.
    """
    if any(not math.isfinite(x) for x in (mc, mu, cross)) or min(mc, mu) < 0:
        raise ValueError("Finite nonnegative branch energies required")
    scale = max(mc, mu, abs(cross), 1e-30)
    if cross * cross > mc * mu + 1e-10 * scale * scale:
        raise ValueError("Branch Gram is not positive semidefinite")
    q = 64 * mc + 49 * mu - 112 * cross
    if q < -1e-9 * scale:
        raise ValueError("Negative guided energy")
    q = max(0.0, q)
    eta = cross / mc if mc > 0 else None
    zeta = cross / mu if mu > 0 else None
    pc = 49 * max(0.0, mu - cross * cross / mc) if mc > 0 else 49 * mu
    pu = 64 * max(0.0, mc - cross * cross / mu) if mu > 0 else 64 * mc
    for name, value in (("Pc", pc), ("Pu", pu)):
        if value > q + 1e-8 * max(q, scale):
            raise ValueError(f"{name} projection exceeds original guided error")
    return {
        "q_base": q, "eta_oracle": eta, "zeta_oracle": zeta,
        "q_Pc_oracle": pc, "q_Pu_oracle": pu,
        "Pc_gain_fraction": (q - pc) / q if q > 0 else None,
        "Pu_gain_fraction": (q - pu) / q if q > 0 else None,
        "rho": cross / math.sqrt(mc * mu) if mc > 0 and mu > 0 else None,
        "degeneracy": "ZERO_GUIDED_ERROR" if q == 0 else "ZERO_BRANCH_ENERGY" if min(mc, mu) == 0 else None,
        "oracle_only": True,
    }


def fixed_direction_error(mc, mu, cross, direction, coefficient):
    if not math.isfinite(coefficient):
        raise ValueError("Finite frozen coefficient required")
    scalar_oracles(mc, mu, cross)
    if direction == "Pc":
        return 49 * (mu - 2 * coefficient * cross + coefficient * coefficient * mc)
    if direction == "Pu":
        return 64 * (mc - 2 * coefficient * cross + coefficient * coefficient * mu)
    raise ValueError("Pc or Pu direction required")


def verify_h1_step(entry, parameters, lam):
    """Reconstruct J from receipt fields and the frozen table, not controller code."""
    step = entry["step"]
    policy = entry["source_policy"]
    d = policy["decision"]
    basis = policy["event_math"]
    state = d["state_before"]
    source, birth, floor = state[1:4]
    if step != d["step"] or basis["query_age"] != (step - birth if birth is not None else None):
        raise ValueError("Step/source age binding changed")
    table = basis["candidate_risk_and_price"]
    row = {
        "step": step, "physical_action": entry["action"],
        "actual_readout": entry["A_readout"]["readout_action"],
        "source": source, "source_birth": birth, "source_age": basis["query_age"],
        "protected": entry["protected"], "reason": d["reason"],
        "paid_packets": d["packets"], "local_proxy": d["local_proxy"], "gain": d["gain"],
        "root_floor": floor, "pre_action_accumulated": state[4],
        "legal_actions": [], "scores": None, "winner": None,
        "runner_up": None, "margin_seconds": None, "CAD_A_interval": None,
    }
    if table is None:
        if d["reason"].startswith("MATH_EVENT_TABLE_ABSOLUTE_H1:"):
            raise ValueError("Optimizer choice has no recorded legal scores")
        row["category"] = "PROTECTED" if entry["protected"] else "SUPPORT_OR_POLICY_FALLBACK"
        row["forced_action"] = d["action"]
        return row
    if entry["protected"] or not d["reason"].startswith("MATH_EVENT_TABLE_ABSOLUTE_H1:"):
        raise ValueError("Unmatched active-table decision")
    phase = "EARLY" if step < 25 else "LATE"
    fit = parameters["table_model"]["cells"][source + "_" + phase]
    if fit["status"] != "FIT" or floor < 0 or source == "D" and floor != 0:
        raise ValueError("Source/calibration cell mismatch")
    q_c = fit["C_scale"] * (d["local_proxy"] + floor) ** 2
    expected_q = {"C": q_c, "A": q_c * fit["A_ratios"]["FUSION_A"], "D": 0.0}
    if "P" in table:
        if not d["partial_ready"]:
            raise ValueError("P scored without legal partial readiness")
        expected_q["P"] = fit["actual_NEW_P_birth_mean"]
    if set(table) != set(expected_q):
        raise ValueError("Recorded legal action set changed")
    for a, v in table.items():
        price = parameters["source_A_cost_seconds"][source] if a == "A" else parameters["cost_seconds"][a]
        near(v["price"], price, a + " price")
        near(v["absolute_current_MSE"], expected_q[a], a + " calibrated MSE")
        near(v["gain_squared_risk"], d["gain"] ** 2 * expected_q[a], a + " g2q")
        near(v["score"], price + lam * d["gain"] ** 2 * expected_q[a], a + " J")
    order = sorted(table, key=lambda a: (table[a]["score"], {"C": 0, "A": 1, "P": 2, "D": 3}[a]))
    winner = order[0]
    if d["reason"].split(":")[-1] != winner or row["actual_readout"] != winner:
        raise ValueError("Actual readout differs from independently reconstructed argmin")
    physical = {"C": "CC", "A": "CC", "P": "PP", "D": "DD"}[winner]
    if entry["action"] != physical:
        raise ValueError("Physical action differs from semantic readout")
    row.update(category="OPTIMIZER", legal_actions=list(table), scores=table,
               winner=winner, runner_up=order[1], margin_seconds=table[order[1]]["score"] - table[winner]["score"])
    ratio = expected_q["A"] / expected_q["C"] if expected_q["C"] > 0 else None
    if ratio is not None and 0 < ratio < 1:
        lo = (table["A"]["price"] - table["C"]["price"]) / (1 - ratio)
        hi = (table["D"]["price"] - table["A"]["price"]) / ratio
        x = lam * d["gain"] ** 2 * expected_q["C"]
        row["CAD_A_interval"] = {"lower": lo, "upper": hi, "x": x,
                                 "distance_above_lower": x - lo, "distance_below_upper": hi - x,
                                 "CAD_only_not_P_comparison": True}
    return row
