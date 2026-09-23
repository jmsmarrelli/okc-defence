# Method notes

What the two channels are, why the attempt differential is allowed to stand in
for a turnover, and how much of any of it survives to next season.

## The decomposition

Every attempt a team faced is labeled with one of five zones. Against that
season's league-average points per attempt in each zone, the points a team
allowed per shot split in two:

    points allowed per shot  -  league average
        = (what their opponents' locations were worth at league rates)   <- location
        + (what their opponents actually scored, minus that)             <- conversion

Multiplied by 100 it reads as points per hundred attempts faced. Negative is
good defense in both terms and in their sum, throughout.

**League rates are re-estimated every season.** A corner three was worth 1.16
points in 2024-25 and 1.09 in 2004-05, and a decomposition run against a pooled
rate would price two decades of rule changes and shot-selection change as
defense.

**Five zones, not coordinates.** The raw files have two defects that make finer
descriptions unusable across the sample: the action-type vocabulary was rewritten
between 2007 and 2009, and the shot coordinates were recorded differently before
2010-11, with three season files published on a different scale entirely. Both
are documented at length in the sibling `nba-shot-value` repository. The five
`BASIC_ZONE` labels have meant the same thing throughout, so they are all this
project uses.

## The attempt differential

This is the load-bearing piece and it deserves its own scrutiny.

A steal writes no row into a shot file. What it writes is the absence of one.
Both teams in a game see the same possessions to within one, so

    (own attempts per game) - (opponent attempts per game)

is the shortfall a defense created: possessions the opponent never got to shoot
on, plus possessions the defense got twice. It mixes **turnovers forced** with
**the offensive rebounding battle**, and nothing here separates them.

Converting it to points uses that season's league-average points per attempt: a
denied attempt is worth what an average attempt was worth. That is the right
order of magnitude and it is not exact, because the attempts a defense denies
are not a random sample of attempts.

**What it is not.** It is not a turnover rate. A team with a poor offensive
rebounding rate of its own will show a worse attempt differential than its
defense deserves, and this project makes no attempt to correct for that, because
correcting it needs rebounding data the file does not carry.

## Why points per *game* rather than per possession

Because there is no possession count in a shot file, and inventing one from
attempts would be circular in a project whose second channel is attempts.

The cost is real: a fast team looks like it denies more points a game than the
same team playing slow, so the leaderboard has a mild pace tilt. It is a tilt and
not a confound — the league's pace range across a season is roughly ten per
cent — and the alternative was worse.

## Stability, and what it licenses

Every component is run against the same team's next season, across the 624
consecutive team-season pairs in the sample. Opponent shooting percentages are
first expressed against that season's league average:

| Component | Repeats at |
|---|---|
| Shot locations forced | 0.66 |
| Opponent two-point percentage | 0.58 |
| Points denied per game | 0.51 |
| Conversion suppressed | 0.51 |
| Attempt differential | 0.44 |
| Opponent three-point percentage | **0.19** |

The centering matters. League two-point percentage climbed from .460 to .545 over
these twenty-two seasons, and a raw year-to-year correlation picks that climb up
as if every team were repeating itself: uncentred, opponent two-point
percentage "repeats" at 0.85. Measured against the league it is 0.58. The
three-point side barely moves either way (0.16 raw, 0.19 centered), because
league three-point accuracy hardly changed.

The last row is the one that matters and it is not news to anyone who has looked
at defensive statistics before; it is here because it changes what can be said
about this particular season. Splitting the conversion channel by whether the
shot was worth three puts **−2.81 of Oklahoma City's −5.37 on the two-point side
and −2.57 on the three-point side**, and the second of those numbers is a
property of the season more than of the team.

This is a bound, not an identification. It says how much of a *typical* team's
conversion edge carries forward. It cannot say which of Oklahoma City's
individual possessions were contest quality and which were a shooter missing an
open look.

## Why "points denied" rather than a rating

The composite adds the two channels and reports one number in points a game. It
is deliberately not called a defensive rating, because it is not one: no free
throws, no possessions, no pace adjustment.

What it has instead is that it is built from what a defense *did* — the
locations it forced, the conversion it allowed, the attempts it denied — rather
than from what its opponents happened to score. Those are different objects and
the difference is the point of building it.

## Where this is weakest

**Fouling is invisible.** A defense that concedes free throws instead of shots
looks better here than it is, and the effect is not small: free throws are about
a fifth of scoring. Any team whose shot defense looks unusually good should be
checked against its free-throw rate allowed before anyone believes it. That
check cannot be run from this file.

**The subject is one season.** Twenty-two seasons of context around a single
team-season is the right shape for the question "how unusual was that", and the
wrong shape for "how good is this team". The season-by-season table is there so
the reader can see how much of it is new.

**Opponent quality is not controlled.** A defense that played a soft schedule
looks better here. Over 82 games the schedule mostly evens out, and this is a
real limitation on any single-season comparison — particularly between
conferences, which do not play each other equally.

**Regular season only, 2003-04 to 2024-25**, which is where the shot mirror
currently ends. Nothing in this repository is about a playoff series, and a
seven-game series against one opponent is not the thing an 82-game average
predicts well.
