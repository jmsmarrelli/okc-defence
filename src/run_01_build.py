"""Stage 1 - twenty-two seasons of shots into per-team profiles, both sides.

    python src/run_01_build.py

For every season file: attach the defending team to every attempt, collapse the
zone labels to the five that mean the same thing across the sample, and total
attempts and points by zone for each team on offence and on defence.

Writes data/processed/profiles.csv, data/processed/games.csv,
output/league_zone_value.csv and output/coverage.csv.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import HEAVE_DIST, HEAVE_SECS, OUT, PROC, RAW, SEASONS  # noqa: E402
import defence as D  # noqa: E402

COLS = ["SEASON_1", "GAME_ID", "GAME_DATE", "TEAM_NAME", "PLAYER_ID", "PLAYER_NAME",
        "HOME_TEAM", "AWAY_TEAM", "SHOT_MADE", "SHOT_TYPE", "BASIC_ZONE",
        "SHOT_DISTANCE", "QUARTER", "MINS_LEFT", "SECS_LEFT"]


def team_abbreviations(df: pd.DataFrame) -> pd.Series:
    """Recover each franchise's three-letter code without hard-coding a table.

    Every row names the two abbreviations in the game, so a team's own code is
    the one present in every game it played. Intersecting over a season leaves
    one survivor, and it survives relocations and rebrands with no maintenance.
    """
    pairs = df[["TEAM_NAME", "HOME_TEAM", "AWAY_TEAM"]].drop_duplicates()
    out = {}
    for team, grp in pairs.groupby("TEAM_NAME", observed=True):
        common = set(grp.iloc[0][["HOME_TEAM", "AWAY_TEAM"]])
        for _, row in grp.iloc[1:].iterrows():
            common &= {row["HOME_TEAM"], row["AWAY_TEAM"]}
            if len(common) == 1:
                break
        if len(common) != 1:
            raise ValueError(f"could not resolve an abbreviation for {team}: {common}")
        out[team] = common.pop()
    return pd.Series(out, name="team_abbrev")


def load_season(season: int) -> tuple[pd.DataFrame, dict]:
    path = RAW / f"NBA_{season}_Shots.csv"
    if not path.exists():
        raise SystemExit(f"missing {path}. See data/README.md.")
    raw = pd.read_csv(path, usecols=COLS, low_memory=False)

    abbrev = team_abbreviations(raw)
    team = raw["TEAM_NAME"].map(abbrev)
    # The defending team is the other one named on the row.
    opponent = np.where(team == raw["HOME_TEAM"], raw["AWAY_TEAM"], raw["HOME_TEAM"])

    secs_left = raw["MINS_LEFT"] * 60 + raw["SECS_LEFT"]
    heave = (raw["SHOT_DISTANCE"] >= HEAVE_DIST) & (secs_left <= HEAVE_SECS)
    backcourt = raw["BASIC_ZONE"].astype(str).eq("Backcourt")

    keep = ~(heave | backcourt)
    d = pd.DataFrame({
        "season": season,
        "game_id": raw["GAME_ID"].to_numpy(),
        "team": team.to_numpy(),
        "opponent": opponent,
        "zone5": D.zone5(raw["BASIC_ZONE"]),
        "points": np.where(raw["SHOT_MADE"].to_numpy(),
                           np.where(raw["SHOT_TYPE"].eq("3PT Field Goal"), 3, 2), 0),
        "made": raw["SHOT_MADE"].to_numpy().astype(int),
    })[keep.to_numpy()]

    audit = {"season": season, "rows": int(len(raw)), "kept": int(len(d)),
             "dropped_heave": int(heave.sum()), "dropped_backcourt": int(backcourt.sum()),
             "games": int(d["game_id"].nunique()), "teams": int(d["team"].nunique())}
    return d, audit


def main() -> None:
    frames, audit = [], []
    for season in SEASONS:
        t0 = time.time()
        d, a = load_season(season)
        frames.append(d)
        a["seconds"] = round(time.time() - t0, 1)
        audit.append(a)
        print(f"  {season}: {a['kept']:,} attempts, {a['games']:,} games "
              f"({a['seconds']}s)", flush=True)
    shots = pd.concat(frames, ignore_index=True)

    zone_value = D.league_zone_value(shots)
    zone_value.round(5).to_csv(OUT / "league_zone_value.csv", index=False)

    prof = pd.concat([D.profile(shots, "off"), D.profile(shots, "def")],
                     ignore_index=True)
    prof.to_csv(PROC / "profiles.csv", index=False)

    # Games played, counted from each side so the two agree.
    games = pd.concat([
        shots[["season", "team", "game_id"]],
        shots[["season", "opponent", "game_id"]].rename(columns={"opponent": "team"}),
    ]).drop_duplicates().groupby(["season", "team"], observed=True).size()
    games = games.rename("games").reset_index()
    games.to_csv(PROC / "games.csv", index=False)

    cov = pd.DataFrame(audit)
    cov.to_csv(OUT / "coverage.csv", index=False)

    print(f"\n{len(shots):,} attempts, {shots['game_id'].nunique():,} games, "
          f"{len(games)} team-seasons")
    print(f"games per team-season: {games['games'].min()}-{games['games'].max()}")
    print()
    print(cov.to_string(index=False))


if __name__ == "__main__":
    main()
