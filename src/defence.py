"""What a shot chart can and cannot tell you about a defense.

A defense does four things. It makes the other team shoot from bad places, it
makes them miss from good ones, it takes the ball away before they shoot at all,
and it keeps them off the offensive glass. A file of shot attempts can see the
first two directly, sees the third and fourth only as a shortfall in attempts,
and cannot see free throws at all.

So the decomposition here is deliberately narrow and says so. Every team-season's
opponents are described by the mix of zones they shot from and the rate they
converted in each, and the difference from league average splits in two:

    points allowed per shot  -  league average
        = (what their shot locations were worth at league rates)   <- location
        + (what they actually scored, minus that)                  <- conversion

Location is the part a scheme controls most directly. Conversion is contest
quality, rim protection and luck, in proportions this data cannot separate.

The third thing gets its own number. Both teams in a game see roughly the same
number of possessions, so a team that shoots more often than its opponents is
either taking the ball away or getting it back off the rim. The attempt
differential is that, per game, and it is the only trace turnovers leave here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ZONES = ["Restricted Area", "In The Paint (Non-RA)", "Mid-Range",
         "Corner 3", "Above the Break 3"]


def zone5(zone: pd.Series) -> pd.Categorical:
    """Collapse the file's zone labels to the five that are era-stable."""
    z = zone.astype(str).replace({"Left Corner 3": "Corner 3",
                                  "Right Corner 3": "Corner 3"})
    return pd.Categorical(z, categories=ZONES, ordered=True)


def league_zone_value(shots: pd.DataFrame) -> pd.DataFrame:
    """Points per attempt in each zone, season by season.

    Re-estimated every season on purpose. The value of a corner three in 2004-05
    is not the value of one in 2024-25, and a decomposition that used a pooled
    rate would price two decades of rule changes as defense.
    """
    g = shots.groupby(["season", "zone5"], observed=True)
    out = g.agg(att=("points", "size"), pts=("points", "sum"),
                made=("made", "sum")).reset_index()
    out["pps"] = out["pts"] / out["att"]
    out["fg"] = out["made"] / out["att"]
    return out


def profile(shots: pd.DataFrame, side: str) -> pd.DataFrame:
    """Attempts and points by zone for each team-season, on one side of the ball.

    `side` is "off" for shots a team took and "def" for shots it faced.
    """
    key = "team" if side == "off" else "opponent"
    g = shots.groupby(["season", key, "zone5"], observed=True)
    out = (g.agg(att=("points", "size"), pts=("points", "sum"), made=("made", "sum"))
           .reset_index().rename(columns={key: "team"}))
    out["side"] = side
    return out


def decompose(prof: pd.DataFrame, zone_value: pd.DataFrame,
              games: pd.DataFrame) -> pd.DataFrame:
    """Split a team-season's points allowed per shot into location and conversion."""
    d = prof.merge(zone_value[["season", "zone5", "pps"]], on=["season", "zone5"],
                   how="left", suffixes=("", "_league"))
    total = d.groupby(["season", "team"], observed=True).agg(
        att=("att", "sum"), pts=("pts", "sum"),
        expected=("att", lambda s: np.nan)).reset_index()

    # Expected points: what this opponent mix was worth at league rates.
    d["exp_pts"] = d["att"] * d["pps"]
    exp = (d.groupby(["season", "team"], observed=True)["exp_pts"].sum()
           .rename("exp_pts").reset_index())
    total = total.drop(columns="expected").merge(exp, on=["season", "team"])

    league = (zone_value.groupby("season")
              .apply(lambda g: g["pts"].sum() / g["att"].sum(), include_groups=False)
              .rename("league_pps").reset_index())
    out = total.merge(league, on="season").merge(games, on=["season", "team"])

    out["pps"] = out["pts"] / out["att"]
    out["expected_pps"] = out["exp_pts"] / out["att"]
    # Points per 100 shots faced, against that season's league average. Negative
    # is good defence throughout.
    out["location"] = 100 * (out["expected_pps"] - out["league_pps"])
    out["conversion"] = 100 * (out["pps"] - out["expected_pps"])
    out["total"] = out["location"] + out["conversion"]
    out["att_per_game"] = out["att"] / out["games"]
    return out


def zone_shares(prof: pd.DataFrame) -> pd.DataFrame:
    """Share of attempts in each zone, wide, one row per team-season."""
    tot = prof.groupby(["season", "team"], observed=True)["att"].transform("sum")
    # Field goal percentage is makes over attempts. Deriving it from points would
    # inflate the three-point zones by half, which is the sort of mistake that
    # produces a 57% corner three and gets published.
    d = prof.assign(share=prof["att"] / tot, fg=prof["made"] / prof["att"])
    share = d.pivot_table(index=["season", "team"], columns="zone5", values="share",
                          observed=True)
    share.columns = [f"share_{c}" for c in share.columns]
    conv = d.pivot_table(index=["season", "team"], columns="zone5", values="fg",
                         observed=True)
    conv.columns = [f"fg_{c}" for c in conv.columns]
    return pd.concat([share, conv], axis=1).reset_index()


def conversion_by_zone(prof_def: pd.DataFrame,
                       zone_value: pd.DataFrame) -> pd.DataFrame:
    """Split the conversion half of a defense into the five zones it happened in.

    Each zone contributes (its share of the attempts faced) x (how far below
    league its conversion was) x (what a make there is worth), which sums back to
    the conversion component. Useful for one reason above all: two of the five
    zones are three-point zones, and opponent three-point percentage is the least
    repeatable thing in basketball.
    """
    d = prof_def.merge(zone_value[["season", "zone5", "fg"]].rename(columns={"fg": "fg_lg"}),
                       on=["season", "zone5"], how="left")
    d["fg"] = d["made"] / d["att"]
    d["value"] = np.where(d["zone5"].isin(["Corner 3", "Above the Break 3"]), 3.0, 2.0)
    share = d["att"] / d.groupby(["season", "team"], observed=True)["att"].transform("sum")
    d["contribution"] = 100 * share * (d["fg"] - d["fg_lg"]) * d["value"]
    d["is_three"] = d["value"] == 3
    return d[["season", "team", "zone5", "att", "fg", "fg_lg", "is_three", "contribution"]]


def opponent_accuracy(conv: pd.DataFrame) -> pd.DataFrame:
    """Opponent two-point and three-point percentage, and each one's contribution."""
    acc = (conv.groupby(["season", "team", "is_three"], observed=True)
           .agg(att=("att", "sum"), contribution=("contribution", "sum"))
           .reset_index())
    return acc


def rank_within_season(d: pd.DataFrame, col: str, ascending: bool = True) -> pd.Series:
    """Rank 1 is the best defense, so lower is better by default."""
    return d.groupby("season")[col].rank(ascending=ascending, method="min")
