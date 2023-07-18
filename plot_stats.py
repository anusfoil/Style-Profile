import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from numpy.lib.recfunctions import append_fields
from params import *
from process_datasets import *

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


def plot_by_dataset(dataset="ASAP", attri="articulation_feature.kor", level="note"):
    """plot the overall distribution of each attributes from the dataset. 
    load the performance features as numpy structured array list, with optional metadata.
    Save figure to

    Args:
        dataset (str): dataset to use. Defaults to "ASAP".
    """
    pf, meta_dict = load_dataset_pf(dataset=dataset, return_metadata=True)

    if level == "piece":
        # get piece-level attributes and append the metadata
        pf_piece_concat = pd.concat([pd.DataFrame(feats).mean().to_frame().T for feats in pf], ignore_index=True)
        pf_piece_concat['composer'] = meta_dict['composer']
        pf_piece_concat['performer'] = meta_dict['performer']
        pf_plot_data = pf_piece_concat
    elif level == "note":
        pf = [append_fields(feats, "composer", [meta_dict['composer'][i]] * len(feats), dtypes="U256", usemask=False) for i, feats in enumerate(pf)]
        pf = [append_fields(feats, "performer", [meta_dict['performer'][i]]* len(feats), dtypes="U256", usemask=False) for i, feats in enumerate(pf)]
        pf_note_concat = pd.concat([pd.DataFrame(feats) for feats in pf])
        pf_plot_data = pf_note_concat     

    sns.set_style("darkgrid")
    g = sns.FacetGrid(pf_piece_concat, col="composer", hue="performer")
    g.map(sns.histplot, attri, stat='density', common_norm=False)
    
    for attri in pf[0].dtype.names:
        g.map(sns.histplot, attri, stat='density', common_norm=False)
        # sns.histplot(pf_piece_concat, x=attri, stat='density', common_norm=False)
        plt.show()
        hook()
    # sns.move_legend(ax, "center right", bbox_to_anchor=(legend_position[attri], .5))
    # plt.legend(loc='center right', title='Team')
    # plt.savefig(f"analysis/cross_datasets/{attri}.png")
    plt.show()


if __name__ == "__main__":
    plot_by_dataset(dataset="ASAP", attri='asynchrony_feature.delta')
