# Data

One CSV per season at `data/raw/NBA_<season>_Shots.csv`, where `<season>` is the
year the season ended: `NBA_2025_Shots.csv` is 2024-25.

## Getting the files

```bash
git clone --depth 1 https://github.com/DomSamangy/NBA_Shots_04_24.git /tmp/nba_shots
mkdir -p data/raw
for z in /tmp/nba_shots/NBA_*_Shots.csv.zip; do unzip -o -q "$z" -d data/raw/; done
```

About 850 MB unzipped, twenty-two seasons, 4.4 million attempts. `data/raw/` and
`data/processed/` are gitignored; everything the analysis cites is written to
`output/` and committed.

The mirror currently ends with 2024-25 and carries the regular season only —
every game id in the 2024-25 file is a `0022400xxx`. Nothing here is about a
playoff series.

## What a shot file cannot see

This matters more in a project about defense than in one about offense, so it is
stated at the top rather than buried in the caveats.

**No free throws.** A defense that fouls is invisible here.

**No possessions.** There is no pace, so nothing can be expressed per hundred
possessions. The two channels are expressed per shot faced and per game instead,
which is what the file actually supports.

**No turnovers, directly.** A steal leaves no row. What it leaves is an
*absence* of rows, and since both teams in a game see roughly the same number of
possessions, a team that shoots more often than its opponents has either taken
the ball away or got it back off the offensive glass. The attempt differential
is that shortfall, and it is the closest this data comes to the thing Oklahoma
City is famous for.

**No rebounding split.** The attempt differential mixes turnovers forced with
offensive rebounds grabbed and conceded, and nothing here separates them.

## Two defects in the raw files, and what this project does about them

**The action-type vocabulary was rewritten mid-sample.** "Pull-up jump shot" and
"step back jump shot" do not exist in the 2003-04 file. Nothing in this project
reads `ACTION_TYPE`.

**Coordinates were recorded differently before 2010-11**, and three season files
are published on a different coordinate scale entirely. Nothing in this project
reads `LOC_X` or `LOC_Y`. Both problems are documented at length in the sibling
`nba-shot-value` repository; here the answer is simply that the five `BASIC_ZONE`
labels have meant the same thing throughout, and they are all this project uses.

## Filters applied in stage 1

| Filter | Rows dropped |
|---|---|
| Heaves: 30 feet or more with two seconds or less on the clock | 18,580 across the sample |
| Backcourt attempts | 9,337 |

Both are shots nobody chose, and a defense should be credited with neither.

## Columns used

| Column | Used for |
|---|---|
| `SEASON_1` | the season, labeled by ending year |
| `GAME_ID` | counting games |
| `TEAM_NAME`, `HOME_TEAM`, `AWAY_TEAM` | who shot, and therefore who defended |
| `BASIC_ZONE` | the five zones the whole analysis runs on |
| `SHOT_TYPE`, `SHOT_MADE` | points |
| `SHOT_DISTANCE`, `QUARTER`, `MINS_LEFT`, `SECS_LEFT` | the heave filter |
