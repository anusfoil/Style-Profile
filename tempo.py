from utils import parse_match
import matplotlib.pyplot as plt

from utils import calculate_tempo

def tempo_attributes(match):
    return {
            "st_tempo_std": match['tempo'].std()
        }

def plot_tempo(match):
    plt.step(match['score_time'], match['tempo'])
    plt.grid()
    plt.show()
    return 

if __name__ == "__main__":

    # this contains repeats (in perf but not in score).
    match = parse_match("../Datasets/ATEPP-1.1/Johann_Sebastian_Bach/Das_Wohltemperierte_Klavier_Book2/Book_2,_BWV_870-893:_Prelude_in_A_minor_BWV_889/02966_match.txt")
    match = calculate_tempo(match)
    hook()
    # plot_tempo(match)