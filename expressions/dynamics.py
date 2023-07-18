import numpy as np
from scipy import stats
# from utils import *

OLS = ["pp", "p", "mp", "mf", "f", "ff"]

def dynamics_correspondence(match):
    """Find the velocity for each marking position
        TODO: try the three-beat window as shown in Kosta paper
        returns: [("p", 42), ("ff", 78.3), ...] """
    dynamics = []
    cur_marking = []
    for idx, row in match.iterrows():
        if row['dynamics_marking'] in OLS:
            if not cur_marking:
                cur_marking = [row['dynamics_marking'], [row['onset_velocity']]]
            elif cur_marking[0] == row['dynamics_marking']:
                cur_marking[1].append(row['onset_velocity'])
            else:
                dynamics.append([cur_marking[0], np.mean(cur_marking[1])])
                cur_marking = [row['dynamics_marking'], [row['onset_velocity']]]
    return dynamics

def dynamics_attributes(match):
    dynamics = dynamics_correspondence(match)
    if len(dynamics) < 2:
        return {
        "sp_dynamics_agreement": np.nan,
        "sp_dynamics_consistency_std": np.nan
    }

    # agreement: compare each adjacent pair of markings with their expected order, average
    tau_total = 0
    for marking1, marking2 in zip(dynamics, dynamics[1:]):
        m1, v1 = marking1
        m2, v2 = marking2
        if (v1 == v2): # preventing correlation returning nan when the values are constant
            v2 = v2 + 1e-5
        tau, _ = stats.kendalltau([v1, v2], [OLS.index(m1), OLS.index(m2)])
        assert(tau == tau) # not nan
        tau_total += tau
    
    # consistency: how much fluctuations does each marking have 
    consistency = match.groupby("dynamics_marking").std()['onset_velocity'].mean()

    return {
        "sp_dynamics_agreement": (tau_total / (len(dynamics)-1)),
        "sp_dynamics_consistency_std": consistency
    }

if __name__ == "__main__":
    match = parse_match("../Datasets/ATEPP-1.1/Wolfgang_Amadeus_Mozart/Piano_Sonata_No._17_in_B-Flat_Major,_K._570/I._Allegro/05511_match.csv")
    dynamics_attributes(match)
