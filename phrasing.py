from scipy.optimize import least_squares
import matplotlib.pyplot as plt
from utils import *


def phrase_end(match):
    """input a match file, output the tempo in the final measures of the phrase """
    
    return 


def freiberg_kinematic(params, xdata, ydata):
    w, q = params
    return ydata - (1 + (w ** q - 1) * xdata) ** (1/q)

def phrasing_attributes(match):
    """
    rubato:
        Model the final tempo curve (last 2 measures) using Friberg & Sundberg’s kinematic model: (https://www.researchgate.net/publication/220723460_Evidence_for_Pianist-specific_Rubato_Style_in_Chopin_Nocturnes)
        v(x) = (1 + (w^q − 1) * x)^(1/q), 
        w: the final tempo (normalized between 0 and 1, assuming)
        q: variation in curvature
    """

    # last 4 beats
    final_beat = match['score_time'].max()
    cadence = match[match['score_time'] >= final_beat - 4]
    cadence = cadence[~cadence['tempo'].isnull()]
    xdata, ydata = cadence['score_time'], cadence['tempo']

    # xdata = np.linspace(0, 1, 7)
    # # ydata = np.array([42.99, 41.81, 42, 43.22, 41.92, 39.28, 41.5])
    # ydata = np.array([123.87, 102.4, 60.47, 76.04, 59.08, 66.78, 36.31])


    # normalize x and y. y: initial tempo as 1
    xdata = (xdata - xdata.min()) * (1 / (xdata.max() - xdata.min()))
    ydata = (ydata - 0) * (1 / (ydata.max() - 0))

    params_init = np.array([0.5, -1])
    res = least_squares(freiberg_kinematic, params_init, args=(xdata, ydata), method="lm")
    
    w, q = res.x

    plt.scatter(xdata, ydata, marker="+", c="red")
    xline = np.linspace(0, 1, 100)
    plt.plot(xline, (1 + (w ** q - 1) * xline) ** (1/q))
    plt.ylim(0, 1.2)
    plt.title(f"Friberg & Sundberg kinematic rubato curve with w={round(w, 2)} and q={round(q, 2)}")
    plt.show()

    return {
        "sp_phrasing_rubato_w": w,
        "sp_phrasing_rubato_q": q,
    }

if __name__ == "__main__":
    match = parse_match("../Datasets/ATEPP-1.1/Wolfgang_Amadeus_Mozart/Piano_Sonata_No.13_in_B_flat,_K.333/1._Allegro/05312_match.csv")
    # match = parse_match("tmp.csv")
    phrasing_attributes(match)
