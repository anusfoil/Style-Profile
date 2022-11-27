# Expression Style Profile

Expression Style Profile (ESP) is a set of extracted attributes from symbolic piano performance files. From an alignment with the score, the attributes analyzes expressive details from hands asynchrony to rubato patterns. All attributes are in piece-level. 

An analysis workflow is as follows: 
![workflow](docs/workflow.png)

## Expression categories 

#### Asynchrony 

For each piece, all same-onset group with more than 3 events are considered, and their performed onset asynchrony are studied with the following attributes.
```sp_asynchrony_delta```: The average amount of asynchrony time (in seconds) of the same-onset group played in the piece.

```sp_asynchrony_cor_pitch```: The Pearson's correlation of the notes' onsets with their pitch. 

```sp_asynchrony_cor_vel```: The Pearson's correlation of the notes' onsets with their velocity. See [this paper]{https://asa.scitation.org/doi/10.1121/1.1376133}. 

```sp_asynchrony_cor_voice```: The Pearson's correlation of the notes' onsets with their voice rank (parsed from score, might not be accurate).


#### Articulation
```sp_articulation_ratio```: We simplfily the notion of articulation into the amount of indicated duration being performed. 


#### Tempo 
By aligning the beat onto performance, the IBI (inter-beat-interval) can be computed in a local level where we have on-beat events.  

```sp_tempo_std```: std of all local tempo, characterizes the overall tempo fluctuation in a performance. Note this is strongly correlated with composition itself, improvement is required regards to the 

#### Dynamics 
We parsed dynamics markings (*pp, p, mp, mf, f, ff*) from the score using the [partitura](https://partitura.readthedocs.io/en/latest/index.html) package, and align them with the performed events. The attributes are inspired from this [Dynamics and relativity paper](https://www.tandfonline.com/doi/abs/10.1080/09298215.2018.1486430?journalCode=nnmr20), and we also take a 3-beat window in computation same as the paper.  

```sp_dynamics_agreement```: The amount of dynamics agreement with the ordinal *pp < p < mp < mf < f < ff*. Averaged across all pair of consecutive markings. 

```sp_dynamics_consistency_std```: How consistent each dyanmics class is throughout the piece. Final value is averaged across all classes. 

TODO: incorporate gradual dynamics marking such as *crescendo*. 

#### Phrasing 

Rubato w and q: inspired from [this paper](https://www.researchgate.net/publication/220723460_Evidence_for_Pianist-specific_Rubato_Style_in_Chopin_Nocturnes), where a kinematic model ($v(x) = (1 + (w^q - 1)x^{1/q})$) is used to characterize the rubato at the phrase end (where usually fits to *ritardandi*). 

```sp_phrasing_rubato_w```: the final tempo from the kinematic model. 

```sp_phrasing_rubato_q```: account for variation of curvature from the kinematic model.

#### Textural 

## Stats on ATEPP dataset

#### Issues & Losses 

|  |  |
| ----------- | ----------- |
| #. total pieces                           |  11672 |
| #. pieces with xml score                  |  6838  |
| #. pieces aligned                         |  4138  |
| #. valid alignment (<50% err)             |  3752  |
| #. pieces with scores parsed by partitura |        |
| #. pieces with dynamics marking           |  3434  |

## Significance and analysis

#### Performer significance: ANOVA

