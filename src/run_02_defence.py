"""Stage 2 - split every defence in two, and find out what kind Oklahoma City is.

    python src/run_02_defence.py

Writes output/defences.csv, output/okc_path.csv, output/okc_zones.csv,
output/stability.csv, output/conversion_by_zone.csv,
output/opponent_accuracy.csv, output/accuracy_stability.csv, output/leaders.csv
and figures 01-05.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (FIG, MIN_FGA, OUT, PEERS, PROC, SUBJECT, SUBJECT_SEASON,  # noqa: E402
                    SEASONS)
import defence as D  # noqa: E402
import labels as L  # noqa: E402
import style as S  # noqa: E402

S.apply()

OKC = S.SERIES[1]     # the subject gets the one warm colour in the palette


def season_label(season: int) -> str:
    return f"{season - 1}-{str(season)[2:]}"


def build(prof: pd.DataFrame, zone_value: pd.DataFrame,
          games: pd.DataFrame) -> pd.DataFrame:
    """Every team-season, with both channels priced in points per game."""
    dfn = D.decompose(prof[prof["side"] == "def"], zone_value, games)
    off = D.decompose(prof[prof["side"] == "off"], zone_value, games)
    d = dfn.merge(off[["season", "team", "att_per_game"]]
                  .rename(columns={"att_per_game": "own_att_per_game"}),
                  on=["season", "team"])
    d = d[d["att"] >= MIN_FGA].reset_index(drop=True)

    # Both teams in a game see roughly the same number of possessions, so a team
    # that shoots more often than its opponents has either taken the ball away or
    # got it back off the rim. This is the only trace either leaves in a file of
    # shot attempts.
    d["att_diff"] = d["own_att_per_game"] - d["att_per_game"]

    # Two channels, both in points per game, so they can be added.
    d["pts_from_shots"] = d["att_per_game"] * d["total"] / 100
    d["pts_from_attempts"] = -d["att_diff"] * d["league_pps"]
    d["net_fg_edge"] = -(d["pts_from_shots"] + d["pts_from_attempts"])

    for col, asc in (("location", True), ("conversion", True), ("total", True),
                     ("att_diff", False), ("net_fg_edge", False)):
        d[f"rank_{col}"] = D.rank_within_season(d, col, ascending=asc)
    return d


def year_over_year(frame: pd.DataFrame, col: str) -> tuple[float, int]:
    """Correlation between a team's value this season and its value next season."""
    s = frame.sort_values(["team", "season"])
    nxt = s.groupby("team")[col].shift(-1)
    gap = s.groupby("team")["season"].shift(-1) - s["season"]
    ok = (gap == 1) & nxt.notna()
    return float(np.corrcoef(s.loc[ok, col], nxt[ok])[0, 1]), int(ok.sum())


def stability(d: pd.DataFrame) -> pd.DataFrame:
    """How much of each component a team keeps from one season to the next.

    Persistence is descriptive. Roster continuity, common trends, schedule and
    sampling noise all affect this correlation; it is not a skill fraction.
    """
    rows = []
    for col in ("location", "conversion", "total", "att_diff", "net_fg_edge"):
        r, n = year_over_year(d, col)
        rows.append({"component": col, "pairs": n, "year_over_year_r": r})
    return pd.DataFrame(rows)


def accuracy_split(conv: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Opponent accuracy on twos and on threes, and how much either repeats.

    Report both raw and season-relative accuracy persistence. Neither separates
    causal defensive skill from personnel, schedule and sampling variation.
    """
    acc = D.opponent_accuracy(conv)
    made = (conv.assign(made=lambda x: x["fg"] * x["att"])
            .groupby(["season", "team", "is_three"], observed=True)
            .agg(made=("made", "sum"), att=("att", "sum")).reset_index())
    made["opp_fg"] = made["made"] / made["att"]
    wide = made.pivot_table(index=["season", "team"], columns="is_three",
                            values="opp_fg", observed=True)
    wide.columns = ["opp_two_pct", "opp_three_pct"]
    contrib = acc.pivot_table(index=["season", "team"], columns="is_three",
                              values="contribution", observed=True)
    contrib.columns = ["from_twos", "from_threes"]
    out = pd.concat([wide, contrib], axis=1).reset_index()

    # Remove the league's evolving accuracy separately for twos and threes.
    league = made.groupby(["season", "is_three"])[["made", "att"]].sum()
    league["fg"] = league["made"] / league["att"]
    for flag, col in [(False, "opp_two_pct"), (True, "opp_three_pct")]:
        baseline = league.xs(flag, level="is_three")["fg"]
        out[col + "_relative"] = out[col] - out["season"].map(baseline)

    rows = []
    for col, label in (("opp_two_pct_relative", "Opponent 2P%, season-relative"),
                       ("opp_three_pct_relative", "Opponent 3P%, season-relative"),
                       ("opp_two_pct", "Opponent two-point percentage"),
                       ("opp_three_pct", "Opponent three-point percentage"),
                       ("from_twos", "Conversion denied on twos"),
                       ("from_threes", "Conversion denied on threes")):
        r, n = year_over_year(out, col)
        rows.append({"component": col, "label": label, "pairs": n,
                     "year_over_year_r": r, "sd": float(out[col].std())})
    return out, pd.DataFrame(rows)


def fig_two_channels(d: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.8, 6.2))
    subj = (d["team"] == SUBJECT) & (d["season"] == SUBJECT_SEASON)
    ax.scatter(-d.loc[~subj, "pts_from_shots"], -d.loc[~subj, "pts_from_attempts"],
               s=15, color=S.NEUTRAL, alpha=0.8, linewidths=0, zorder=2)
    ax.scatter(-d.loc[subj, "pts_from_shots"], -d.loc[subj, "pts_from_attempts"],
               s=90, color=OKC, zorder=5, edgecolors=S.SURFACE, lw=1.4)
    ax.axhline(0, color=S.INK_3, lw=0.9, zorder=3)
    ax.axvline(0, color=S.INK_3, lw=0.9, zorder=3)

    mark = d.nlargest(6, "net_fg_edge").copy()
    best_shots = d.nsmallest(3, "total")
    mark = pd.concat([mark, best_shots]).drop_duplicates(subset=["season", "team"])
    mark = mark[~((mark["team"] == SUBJECT) & (mark["season"] == SUBJECT_SEASON))]
    L.place(ax, -mark["pts_from_shots"].to_numpy(),
            -mark["pts_from_attempts"].to_numpy(),
            [f"{r.team} {season_label(int(r.season))}" for r in mark.itertuples()],
            fontsize=8.6, colour=S.INK_2)
    row = d[subj].iloc[0]
    ax.annotate(f"{SUBJECT} {season_label(SUBJECT_SEASON)}",
                (-row["pts_from_shots"], -row["pts_from_attempts"]),
                xytext=(-12, 14), textcoords="offset points", ha="right",
                fontsize=11, color=OKC, fontweight="semibold")

    ax.set_xlabel("Opponent scoring below league shot rates (points/game)")
    ax.set_ylabel("Net attempt advantage at league value (points/game)")
    ax.set_title("Opponent shot efficiency and the net attempt advantage", loc="left")
    S.strip(ax)
    S.caption(fig, 'All team-seasons in the source sample. Opponent scoring is compared with season league field-goal rates. Attempt balance depends on both teams’ offense, defense, rebounds, turnovers and free-throw trips. These are descriptive shot-file components, not defensive rating.')
    fig.tight_layout()
    fig.savefig(FIG / "01_two_channels.png")
    plt.close(fig)


def fig_denied(d: pd.DataFrame) -> None:
    top = d.nlargest(15, "net_fg_edge").sort_values("net_fg_edge").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9.0, 6.2))
    colours = [OKC if (r.team == SUBJECT and r.season == SUBJECT_SEASON) else S.SILVER
               for r in top.itertuples()]
    shots = -top["pts_from_shots"]
    ax.barh(top.index, shots, color=colours, height=0.62, zorder=2,
            label="opponent shot efficiency")
    # A negative first segment is a defence that gave up more per shot than
    # average and denied attempts anyway. Drawn to the left of zero rather than
    # hidden, and the second segment starts wherever the first one ended.
    ax.barh(top.index, -top["pts_from_attempts"], left=shots,
            color=[S.NEUTRAL if c == S.SILVER else "#f4b393" for c in colours],
            height=0.62, zorder=2, label="net attempt advantage")
    ax.axvline(0, color=S.INK_3, lw=0.9, zorder=4)
    for i, r in top.iterrows():
        ax.text(r["net_fg_edge"] + 0.14, i, f"{r['net_fg_edge']:.1f}", va="center", fontsize=8.8,
                color=S.INK if colours[i] == OKC else S.INK_2,
                fontweight="semibold" if colours[i] == OKC else "normal")
    ax.set_yticks(top.index, [f"{r.team}  {season_label(int(r.season))}"
                              for r in top.itertuples()])
    ax.set_ylim(-0.75, len(top) - 0.25)
    ax.set_xlim(min(-0.6, shots.min() * 1.25), top["net_fg_edge"].max() * 1.14)
    ax.grid(axis="y", visible=False)
    S.strip(ax, keep=("bottom",))
    ax.tick_params(axis="y", labelsize=8.8)
    ax.set_xlabel("Net field-goal edge (points per game)")
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax.set_title("Largest net field-goal edges in this sample", loc="left")
    S.caption(fig, 'Net field-goal edge adds opponent scoring below league shot rates to the net attempt advantage priced at league value. It combines offense and defense, excludes free throws, and does not adjust for pace or opponent strength. It cannot rank overall defenses.')
    fig.tight_layout()
    fig.savefig(FIG / "02_denied.png")
    plt.close(fig)


def fig_okc_path(d: pd.DataFrame) -> None:
    p = d[(d["team"] == SUBJECT) & (d["season"] >= 2019)].sort_values("season")
    fig, ax = plt.subplots(figsize=(9.4, 5.0))
    x = np.arange(len(p))
    w = 0.27
    bars = [("location", "opponent shot locations", S.SERIES[0]),
            ("conversion", "opponent conversion", OKC),
            ("att_diff_pts", "net attempt advantage", S.SERIES[2])]
    p = p.assign(att_diff_pts=-p["pts_from_attempts"] / p["att_per_game"] * 100)
    for i, (col, label, colour) in enumerate(bars):
        vals = -p[col] if col != "att_diff_pts" else p[col]
        ax.bar(x + (i - 1) * w, vals, w, color=colour, zorder=3, label=label)
    ax.axhline(0, color=S.INK_3, lw=0.9, zorder=4)
    ax.set_xticks(x, [season_label(int(s)) for s in p["season"]])
    ax.set_ylabel("Components per 100 opponent shots")
    ax.set_title("Oklahoma City’s shot efficiency and attempt balance", loc="left")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    S.strip(ax)
    ax.grid(axis="x", visible=False)
    S.caption(fig, 'Positive values favor Oklahoma City on these shot-file measures. Attempt balance includes offensive contributions. The chart describes components; it does not identify the causal effects of defensive scheme or individual defenders.')
    fig.tight_layout()
    fig.savefig(FIG / "03_okc_components.png")
    plt.close(fig)


def fig_zones(zones: pd.DataFrame, league: pd.DataFrame) -> None:
    z = zones.merge(league, on="zone5", suffixes=("", "_lg"))
    order = D.ZONES
    z["zone5"] = pd.Categorical(z["zone5"], categories=order, ordered=True)
    z = z.sort_values("zone5").reset_index(drop=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.6))
    x = np.arange(len(z))
    w = 0.36
    ax1.bar(x - w / 2, 100 * z["share"], w, color=OKC, zorder=3, label="faced by Oklahoma City")
    ax1.bar(x + w / 2, 100 * z["share_lg"], w, color=S.SILVER, zorder=3, label="league")
    ax1.set_ylabel("Share of opponent attempts")
    ax1.set_title("Where they let you shoot from", loc="left", fontsize=11)
    ax2.bar(x - w / 2, 100 * z["fg"], w, color=OKC, zorder=3)
    ax2.bar(x + w / 2, 100 * z["fg_lg"], w, color=S.SILVER, zorder=3)
    ax2.set_ylabel("Opponent field goal percentage")
    ax2.set_title("And what you did with it", loc="left", fontsize=11)
    for ax, top in ((ax1, 42), (ax2, 72)):
        ax.set_xticks(x, ["Rim", "Paint", "Mid", "Corner 3", "Above break"])
        ax.tick_params(axis="x", labelsize=8.6)
        ax.set_ylim(0, top)
        ax.set_yticks(range(0, top, 10), [f"{v}%" for v in range(0, top, 10)])
        S.strip(ax)
        ax.grid(axis="x", visible=False)
    ax1.legend(frameon=False, fontsize=9, loc="upper right")
    S.caption(fig, 'Oklahoma City and the league in the subject season. Opponent shot locations and conversion are observed outcomes. Scheme, personnel, opponent mix and randomness cannot be separated with these files.')
    fig.tight_layout()
    fig.savefig(FIG / "04_zone_profile.png")
    plt.close(fig)


def fig_stability(st: pd.DataFrame, acc_st: pd.DataFrame) -> None:
    names = {"location": "Opponent shot locations", "conversion": "Opponent conversion",
             "att_diff": "Attempt differential", "net_fg_edge": "Net field-goal edge"}
    d = st[st["component"].isin(names)].copy()
    d["label"] = d["component"].map(names)
    keep = acc_st[acc_st["component"].isin(["opp_two_pct_relative", "opp_three_pct_relative"])]
    d = pd.concat([d, keep[["component", "label", "pairs", "year_over_year_r"]]],
                  ignore_index=True)
    d = d.sort_values("year_over_year_r").reset_index(drop=True)
    highlight = {"Opponent 2P%, season-relative", "Opponent 3P%, season-relative"}
    fig, ax = plt.subplots(figsize=(9.0, 4.4))
    ax.barh(d.index, d["year_over_year_r"], height=0.56, zorder=2,
            color=[OKC if lab in highlight else S.SILVER for lab in d["label"]])
    for i, r in d.iterrows():
        ax.text(r["year_over_year_r"] + 0.012, i, f"{r['year_over_year_r']:.2f}",
                va="center", fontsize=9, color=S.INK_2)
    ax.set_yticks(d.index, d["label"])
    ax.set_ylim(-0.7, len(d) - 0.3)
    ax.set_xlim(0, 0.85)
    ax.grid(axis="y", visible=False)
    S.strip(ax, keep=("bottom",))
    ax.tick_params(axis="y", labelsize=9.2)
    ax.set_xlabel("Correlation with the same team's next season")
    ax.set_title("How components correlate across consecutive seasons", loc="left")
    S.caption(fig, 'Consecutive team-season correlations. The highlighted accuracy measures subtract each season’s attempt-weighted league 2P% or 3P% before comparing years. Correlation is not the fraction caused by defensive skill and does not establish next-season forecast accuracy.')
    fig.tight_layout()
    fig.savefig(FIG / "05_stability.png")
    plt.close(fig)


def main() -> None:
    prof = pd.read_csv(PROC / "profiles.csv")
    games = pd.read_csv(PROC / "games.csv")
    zone_value = pd.read_csv(OUT / "league_zone_value.csv")

    d = build(prof, zone_value, games)
    d.round(5).to_csv(OUT / "defences.csv", index=False)

    okc = d[d["team"] == SUBJECT].sort_values("season")
    okc.round(5).to_csv(OUT / "okc_path.csv", index=False)

    st = stability(d)
    st.round(4).to_csv(OUT / "stability.csv", index=False)

    conv = D.conversion_by_zone(prof[prof["side"] == "def"], zone_value)
    conv.round(5).to_csv(OUT / "conversion_by_zone.csv", index=False)
    acc, acc_st = accuracy_split(conv)
    acc.round(5).to_csv(OUT / "opponent_accuracy.csv", index=False)
    acc_st.round(4).to_csv(OUT / "accuracy_stability.csv", index=False)

    leaders = d.nlargest(25, "net_fg_edge")
    leaders.round(4).to_csv(OUT / "leaders.csv", index=False)

    # The subject's opponent profile, zone by zone, against that season's league.
    dp = prof[(prof["side"] == "def") & (prof["season"] == SUBJECT_SEASON)]
    zones = (dp[dp["team"] == SUBJECT]
             .assign(share=lambda x: x["att"] / x["att"].sum(),
                     fg=lambda x: x["made"] / x["att"])
             [["zone5", "att", "share", "fg"]])
    lg = zone_value[zone_value["season"] == SUBJECT_SEASON].copy()
    lg["share"] = lg["att"] / lg["att"].sum()
    zones.round(5).to_csv(OUT / "okc_zones.csv", index=False)

    fig_two_channels(d)
    fig_denied(d)
    fig_okc_path(d)
    fig_zones(zones, lg[["zone5", "share", "fg"]])
    fig_stability(st, acc_st)

    subj = d[(d["team"] == SUBJECT) & (d["season"] == SUBJECT_SEASON)].iloc[0]
    print(f"{len(d)} team-seasons, {season_label(SEASONS[0])} to {season_label(SEASONS[-1])}\n")
    print(f"--- {SUBJECT} {season_label(SUBJECT_SEASON)} ---")
    for col, name in (("location", "opponent shot locations"),
                      ("conversion", "opponent conversion"),
                      ("total", "both, per 100 shots faced")):
        print(f"{name:32s} {-subj[col]:+6.2f}   league rank {int(subj[f'rank_{col}'])} of 30")
    print(f"{'attempt differential per game':32s} {subj['att_diff']:+6.2f}   "
          f"league rank {int(subj['rank_att_diff'])} of 30")
    print(f"{'net field-goal edge':32s} {subj['net_fg_edge']:+6.2f}   "
          f"league rank {int(subj['rank_net_fg_edge'])} of 30, "
          f"and {int((d['net_fg_edge'] > subj['net_fg_edge']).sum()) + 1} of {len(d)} all time")

    print("\n--- most net field-goal edge, whole sample ---")
    print(leaders.head(10)[["season", "team", "pts_from_shots", "pts_from_attempts",
                            "net_fg_edge"]]
          .to_string(index=False, float_format=lambda v: f"{v:.2f}"))

    print("\n--- the best shot defences, and what they gave up in attempts ---")
    print(d.nsmallest(8, "total")[["season", "team", "location", "conversion", "total",
                                   "att_diff"]]
          .to_string(index=False, float_format=lambda v: f"{v:.2f}"))

    both = d[(d["total"] < -4) & (d["att_diff"] > 3)].sort_values("net_fg_edge", ascending=False)
    print(f"\n--- team-seasons clearing -4 on the shot chart and +3 in attempts: "
          f"{len(both)} in {len(SEASONS)} seasons ---")
    print(both[["season", "team", "total", "att_diff", "net_fg_edge"]]
          .to_string(index=False, float_format=lambda v: f"{v:.2f}"))

    print("\n--- how much of each component a team keeps year to year ---")
    print(st.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(acc_st[["label", "pairs", "year_over_year_r", "sd"]]
          .to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    a = acc[(acc["team"] == SUBJECT) & (acc["season"] == SUBJECT_SEASON)].iloc[0]
    lg3 = conv[(conv["season"] == SUBJECT_SEASON) & conv["is_three"]]
    print(f"\n--- where {SUBJECT}'s conversion edge came from ---")
    print(f"from twos   {a['from_twos']:+.2f} per 100 shots faced "
          f"(opponents shot {100 * a['opp_two_pct']:.1f}%)")
    print(f"from threes {a['from_threes']:+.2f} per 100 shots faced "
          f"(opponents shot {100 * a['opp_three_pct']:.1f}% against a league "
          f"{100 * (lg3['fg'] * lg3['att']).sum() / lg3['att'].sum():.1f}%)")
    z = conv[(conv["team"] == SUBJECT) & (conv["season"] == SUBJECT_SEASON)]
    print(z[["zone5", "att", "fg", "fg_lg", "contribution"]]
          .to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    print(f"\n--- {season_label(SUBJECT_SEASON)}, the Western top tier ---")
    peers = d[(d["season"] == SUBJECT_SEASON) & (d["team"].isin([SUBJECT] + PEERS))]
    print(peers.sort_values("net_fg_edge", ascending=False)
          [["team", "location", "conversion", "total", "att_diff", "net_fg_edge"]]
          .to_string(index=False, float_format=lambda v: f"{v:.2f}"))

    print(f"\n--- {SUBJECT}, season by season ---")
    print(okc[["season", "location", "conversion", "total", "att_diff", "net_fg_edge",
               "rank_net_fg_edge"]].tail(8)
          .to_string(index=False, float_format=lambda v: f"{v:.2f}"))


if __name__ == "__main__":
    main()
