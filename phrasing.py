from scipy.optimize import least_squares

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


    xdata = np.linspace(0, 1, 6)
    # ydata = np.array([42.99, 41.81, 42, 43.22, 41.92, 39.28, 41.5])
    ydata = np.array([42.99, 42.81, 42.4, 41.92, 39.68, 38.5])

    # normalize x and y. y: initial tempo as 1
    xdata = (xdata - xdata.min()) * (1 / (xdata.max() - xdata.min()))
    ydata = (ydata - ydata.min()) * (1 / (ydata.max() - ydata.min()))

    params_init = np.array([0, 0])
    res = least_squares(freiberg_kinematic, params_init, args=(xdata, ydata))
    
    w, q = res.x
    # res.cost, res.optimality

    return {
        "sp_phrasing_rubato_w": w,
        "sp_phrasing_rubato_q": q,
    }

if __name__ == "__main__":
    # match = parse_match("../Datasets/ATEPP-1.1/Wolfgang_Amadeus_Mozart/Piano_Sonata_No._17_in_B-Flat_Major,_K._570/I._Allegro/05511_match.csv")
    phrasing_attributes()
