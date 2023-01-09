import numpy as np
from utils import parse_match
import matplotlib.pyplot as plt

from utils import calculate_tempo

def tempo_attributes(match):
    return {
            "st_tempo_std": match['tempo'].std()
        }

def plot_tempo(match, smoothing_window=0):

    tempo = match['tempo']
    if smoothing_window:
        kernel = np.ones(smoothing_window) / smoothing_window
        tempo = np.convolve(tempo, kernel, mode='same')

    plt.step(match['score_time'], tempo)
    plt.grid()
    plt.xlabel("beats")
    plt.ylabel("bpm")
    plt.title(f"Tempo curve with smoothing window {smoothing_window}")
    plt.show()
    return 

if __name__ == "__main__":

    # this contains repeats (in perf but not in score).
    match = parse_match("../Datasets/ATEPP-1.1//Franz_Schubert/Piano_Sonata_No.17_in_D,_D.850/1._Allegro_vivace/04150_match.txt")
    match = calculate_tempo(match)
    # match.to_csv("../Datasets/ATEPP-1.1/Wolfgang_Amadeus_Mozart/Piano_Sonata_No.13_in_B_flat,_K.333/1._Allegro/05311_match.csv")
    plot_tempo(match)