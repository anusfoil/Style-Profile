# Expression Style Profile

Expression Style Profile (ESP) is a set of extracted attributes from symbolic piano performance files. From an alignment with the score, the attributes analyzes expressive details from hands asynchrony to rubato patterns.All attributes are in piece-level. 

An analysis workflow is as follows: 
![workflow](docs/workflow.png)

## Expression categories 

#### Asynchrony 
```sp_asynchrony_delta```: [-1, 1]

```sp_asynchrony_cor_onset```: 

```sp_asynchrony_cor_vel```

```sp_asynchrony_cor_parts```


#### Articulation
```sp_articulation_ratio```


#### Tempo 
```sp_tempo_std```: std of all local tempo.

#### Dynamics 
```sp_dynamics_agreement```: The amount of 

```sp_dynamics_consistency_std```: 

#### Phrasing 
```sp_rubato_```

#### Textural 

## Stats on ATEPP dataset

#### Issues & Losses 

There are numerous 

|  |  |
| ----------- | ----------- |
| #. pieces with xml score      |        |
| #. pieces aligned             |  2730  |
| #. valid alignment            |    |
| #. pieces with scores parsed by partitura |        |
| #. pieces with dynamics       |        |

## Significance and analysis

