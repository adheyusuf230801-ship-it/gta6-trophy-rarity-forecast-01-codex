"""Forecast trophy earn rates from the snapshots in each case."""

import json
import os
from datetime import datetime
from math import exp, expm1, floor, hypot, log, sqrt
from pathlib import Path
from statistics import median


Z_SCORES = (-1.645, -0.674, 0.0, 0.674, 1.645)
DAY_SECONDS = 86400


def log_odds(rate):
    bounded = min(99.99, max(0.01, rate))
    return log(bounded / (100.0 - bounded))


def logistic(value):
    if value >= 0:
        return 1 / (1 + exp(-value))
    odds = exp(value)
    return odds / (1 + odds)


def line_fit(points):
    """Return the least squares slope and residual RMS."""
    if len(points) < 3:
        return 0.0, 0.0
    x_bar = sum(x for x, _ in points) / len(points)
    y_bar = sum(y for _, y in points) / len(points)
    variance = sum((x - x_bar) ** 2 for x, _ in points)
    if variance == 0:
        return 0.0, 0.0
    slope = sum((x - x_bar) * (y - y_bar) for x, y in points) / variance
    residual = sqrt(sum((y - y_bar - slope * (x - x_bar)) ** 2
                        for x, y in points) / len(points))
    return slope, residual


def effective_days(days, tau):
    return -tau * expm1(-days / tau)


def ceiling(trophy):
    """Week-one participation prior for the trophy, as a fraction."""
    tier = trophy["tier"]
    description = trophy["description"].lower()
    if tier == "platinum" or trophy["points"] >= 300:
        return 0.008
    if tier == "gold" or trophy["points"] >= 90:
        return 0.018 if "100%" in description else 0.35
    if "chapter" in description:
        for chapter, limit in ((1, 0.80), (2, 0.64), (3, 0.51), (4, 0.42)):
            if f"chapter {chapter}" in description:
                return limit
    if tier == "silver":
        return 0.22
    return 0.60


def forecast(case):
    history = case["history"]
    last_time = datetime.fromisoformat(history[-1]["at"])
    time_left = (datetime.fromisoformat(case["target"]) - last_time).total_seconds()
    exposure = max(0.0, time_left / DAY_SECONDS)
    # Use the same growth window for both counts. Otherwise slowing only
    # the denominator first can create a rate trend absent in the data.
    growth_window = effective_days(exposure, 1.65)
    horizon = case["horizon_minutes"] / 1440
    recent = []
    for read in history:
        age = (datetime.fromisoformat(read["at"]) - last_time).total_seconds() / DAY_SECONDS
        if age >= -1:
            recent.append((age, read["players_tracked"], read["rates"]))

    tracked_now = recent[-1][1]
    population_slope, _ = line_fit([(x, log(n)) for x, n, _ in recent])
    population_slope = min(2.0, max(0.0, population_slope))
    tracked_future = tracked_now * exp(population_slope * growth_window)

    profiles = []
    for i, trophy in enumerate(case["trophies"]):
        samples = [(x, n, rates[i]) for x, n, rates in recent if rates[i] is not None]
        last_rate = next((read["rates"][i] for read in reversed(history)
                          if read["rates"][i] is not None), 0.0)
        rate_slope, residual = line_fit([(x, log_odds(r)) for x, _, r in samples])
        count_slope, _ = line_fit([(x, log(max(0.5, n * r / 100)))
                                  for x, n, r in samples])
        changes = sum(a[2] != b[2] for a, b in zip(samples, samples[1:]))
        moving = len(samples) >= 3 and changes > 0
        profiles.append((trophy, last_rate, rate_slope, count_slope, residual, moving, samples, changes))

    # Pool fractional rate growth, then map it back to each trophy's logit.
    population_trend = median([slope * (1 - rate / 100)
                               for _, rate, slope, _, _, moving, _, _ in profiles if moving] or [0.0])
    rows = []
    for trophy, rate, rate_slope, count_slope, residual, moving, samples, changes in profiles:
        center = log_odds(rate)
        span = samples[-1][0] - samples[0][0] if samples else 0
        if moving:
            fraction = rate / 100
            own_growth = rate_slope * (1 - fraction)
            # Frequent polling can repeat the same page. A trend supported
            # by only one refresh gets less weight than repeated movement.
            own_weight = 0.50 + 0.32 * min(1.0, changes / 5)
            pooled_growth = own_weight * own_growth + (1 - own_weight) * population_trend
            growth = max(0.0, 0.5 * (count_slope + population_slope + pooled_growth))
            earned = max(0.5, fraction * tracked_now)
            # Convert the participation prior to an absolute count capacity.
            capacity = max(earned * 1.001, ceiling(trophy) * tracked_future)
            share = earned / capacity
            speed = min(4.0, growth / (1 - share))
            earned_future = capacity * logistic(log(share / (1 - share))
                                                  + speed * growth_window)
            center = log_odds(100 * max(earned, earned_future) / tracked_future)

        # Short flat cases already get the walk spread. For longer
        # extrapolations allow extra fit uncertainty even on a plateau.
        floor_residual = 0.0
        if moving or horizon >= 0.5:
            floor_residual = 0.07 + 0.10 * (1 - span) + 0.08 / (1 + changes)
        sigma = hypot(0.5 * sqrt(horizon), max(residual, floor_residual))
        quantiles = []
        for z in Z_SCORES:
            percent = min(99.99, max(0.01, 100 * logistic(center + z * sigma)))
            quantiles.append(floor(percent * 10000 + 0.5) / 10000)
        rows.append({"id": trophy["id"], "q": quantiles})
    return {"trophies": rows}


def run():
    source = Path(os.getenv("MAKEFUN_INPUT_DIR", "/input"))
    destination = Path(os.getenv("MAKEFUN_OUTPUT_DIR", "/output"))
    destination.mkdir(parents=True, exist_ok=True)
    for case_file in sorted(source.glob("*.in")):
        case = json.loads(case_file.read_text(encoding="utf-8"))
        payload = json.dumps(forecast(case), separators=(",", ":"), allow_nan=False)
        destination.joinpath(case_file.with_suffix(".out").name).write_text(
            payload + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    run()
