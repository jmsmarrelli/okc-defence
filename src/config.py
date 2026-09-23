"""Paths, seasons, and the teams this project is pointed at."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FIG = ROOT / "figures"
OUT = ROOT / "output"

for d in (RAW, PROC, FIG, OUT):
    d.mkdir(parents=True, exist_ok=True)

# Season label is the year the season ends: 2025 == 2024-25, which is where the
# public shot mirror this project reads currently stops.
FIRST_SEASON = 2004
LAST_SEASON = 2025
SEASONS = list(range(FIRST_SEASON, LAST_SEASON + 1))

SUBJECT = "OKC"
SUBJECT_NAME = "Oklahoma City Thunder"
SUBJECT_SEASON = 2025

# The rest of the Western top tier, for context rather than for a headline.
PEERS = ["SAS", "DEN", "HOU", "MIN", "LAL", "GSW"]

RIM_Y = 5.25
HEAVE_DIST = 30.0
HEAVE_SECS = 2.0

# Coordinates were recorded differently before 2010-11 - most attempts at the rim
# carry the rim's own coordinate rather than the shooter's. Nothing in this
# project uses fine coordinates, only the five coarse zone labels, which are
# unaffected. The constant is here so the boundary is visible in one place.
COORD_ERA_START = 2011

MIN_FGA = 1500          # a team-season needs this many attempts to be ranked
SEED = 20240117
