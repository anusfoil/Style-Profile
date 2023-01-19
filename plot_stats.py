import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from params import *
import hook

legend_position = {
    "sp_async_delta": 0.7, 
    "sp_async_cor_onset": 0.35, 
    "sp_async_cor_vel": 0.35, 
    "sp_async_voice_std": 0.7,
    "sp_duration_percentage": 0.7, 
    "sp_key_overlap_ratio": 0.35, 
    "sp_kor_repeated": 0.8, 
    "sp_kor_staccato": 0.7, 
    "sp_kor_legato": 0.4,
    "sp_tempo_std": 0.8,
    "sp_dynamics_agreement": 0.8, 
    "sp_dynamics_consistency_std": 0.8,
    "sp_phrasing_rubato_w": 0.9, 
    "sp_phrasing_rubato_q" : 0.75
}

def plot_by_performer(meta_attributes):

    artists_counts=meta_attributes['artist'].value_counts() # remove class with few data
    filtered_labels = artists_counts[artists_counts>200].index
    labels = ['Vladimir Ashkenazy', 'Sviatoslav Richter', 'Claudio Arrau', 'Vladimir Horowitz', 
                'Daniel Barenboim', 'Emil Gilels', 'Glenn Gould']
    meta_attributes = meta_attributes[meta_attributes['artist'].isin(labels)]

    sns.set_style("darkgrid")
    for attri in ALL_ATTRIBUTES:
        ax = sns.displot(meta_attributes, x=attri, hue="artist", kind="kde", height=4, aspect=5/4)
        if attri == "sp_phrasing_rubato_q": 
            ax.set(xlim=(-1e4, 1e4))
        sns.move_legend(ax, "center right", bbox_to_anchor=(legend_position[attri], .5))
        # plt.legend(loc='center right', title='Team')
        plt.savefig(f"analysis/ATEPP/{attri}.png")
        # plt.show()


def plot_by_dataset():
    atepp_attributes = pd.read_csv(ATEPP_ATTRIBUTES)
    asap_attributes = pd.read_csv(ASAP_ATTRIBUTES)
    vienna422_attributes = pd.read_csv(VIENNA422_ATTRIBUTES)

    all_datasets = pd.concat([atepp_attributes, asap_attributes, vienna422_attributes])
    all_datasets['dataset'] = ""
    all_datasets.iloc[0:3550,  -1] = "ATEPP"
    all_datasets.iloc[3550:4277, -1] = "ASAP"
    all_datasets.iloc[4277:4365, -1] = "VIENNA422"
    all_datasets.index = range(0,len(all_datasets))

    sns.set_style("darkgrid")
    # for attri in ALL_ATTRIBUTES:
    attri = ALL_ATTRIBUTES[12]
    ax = sns.histplot(all_datasets, x=attri, hue="dataset", stat='density', common_norm=False)
    if attri == "sp_async_delta":
        ax.set(xlim=(0, 0.2))
    if attri == "sp_phrasing_rubato_q": 
        ax.set(xlim=(-1e4, 1e4))
    # sns.move_legend(ax, "center right", bbox_to_anchor=(legend_position[attri], .5))
    # plt.legend(loc='center right', title='Team')
    # plt.savefig(f"analysis/cross_datasets/{attri}.png")
    plt.show()
        # hook()


if __name__ == "__main__":
    # plot_by_performer(pd.read_csv(ATEPP_ATTRIBUTES))
    plot_by_dataset()
    pass