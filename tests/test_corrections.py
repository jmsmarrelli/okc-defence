import sys
from pathlib import Path
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from run_02_defence import accuracy_split

def test_accuracy_is_centered_at_attempt_weighted_season_baseline():
    rows=[]
    for season in range(2021,2025):
        for team,att,offset in [("A",100,-.03),("B",300,.01)]:
            for three,base in [(False,.5),(True,.3)]:
                rows.append(dict(season=season,team=team,is_three=three,att=att,
                    fg=base+.01*(season-2021)+offset,contribution=offset))
    out,_=accuracy_split(pd.DataFrame(rows))
    for col in ["opp_two_pct_relative","opp_three_pct_relative"]:
        assert np.allclose(out.loc[out.team=="A",col],-.03)
        assert np.allclose(out.loc[out.team=="B",col],.01)
