# Method and revision notes


Oklahoma City's 2024–25 shot-file results combine low opponent scoring per attempt with more field-goal attempts than its opponents. Those are useful components to describe, but their sum is not a defensive rating.

The decomposition compares each team's opponents with that season's league field-goal rates. Location measures the value of the observed zone mix; conversion measures the remaining difference in scoring from those zones. Neither component identifies a defensive scheme's causal contribution.

![Shot efficiency and attempt balance](../figures/01_two_channels.png)

## Correct definition of the combined measure

**Net field-goal edge** = opponent field-goal points below league shot rates + the team's net attempt advantage valued at the league's points per attempt.

Attempt balance includes both teams' offense, defense, rebounding, turnovers and free-throw trips. Additional offensive rebounds can improve this measure without any change to opponent shot defense. It excludes free-throw points, pace adjustment and opponent-strength adjustment. Use it as a descriptive field-goal balance, not a ranking of total defense.

[Result table](../output/okc_path.csv)

![Historical net field-goal edges](../figures/02_denied.png)

## Does opponent accuracy persist?

The revised comparison subtracts the attempt-weighted league 2P% or 3P% within each season before correlating consecutive team-seasons. Raw correlations are retained for comparison.

[Result table](../output/accuracy_stability.csv)

The large raw two-point correlation partly reflects the league's changing accuracy over time. The season-relative association remains positive, but correlation does not tell us what fraction is defensive skill. Roster continuity, opponent mix and sampling variation also matter. This is a retrospective persistence check, not an evaluated next-season forecast.

![Season-relative persistence](../figures/05_stability.png)

## Basketball use

The zone profile directs attention to where opponent efficiency differed from league rates. Film and possession-level data are needed to distinguish contested finishes, rotations, transition defense and opponent shooting variance. A complete defensive evaluation must also account for free throws, turnovers, rebounds and possession counts.

The sample ends in 2024–25; team labels and rankings refer to that historical sample.


The result tables are linked and rendered in the main article. Full algorithms and thresholds are in `src/`; source bytes are recorded in `data/source_manifest.json`.
