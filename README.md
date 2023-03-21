# Glacier Time Series Analysis
Methods to compute continuous glacier change from temporally and spatially sparse elevation measurements.

## Installation

Download and install [Miniconda](https://docs.conda.io/en/latest/miniconda.html)  

After installing Miniconda set up [Mamba](https://mamba.readthedocs.io/en/latest/installation.html) (optional but recommended)
```
$ conda install mamba -n base -c conda-forge
```
Clone the repo and set up the conda environment  

```
$ git clone https://github.com/friedrichknuth/gtsa.git
$ cd ./gtsa
$ mamba env create -f environment.yml
$ conda activate gtsa
$ pip install -e .
```

## Data
Analysis ready DEM and ortho data are staged [here](https://drive.google.com/drive/folders/1AMqnuMVYCa0xzwDOiowGAwd8iV63kSjf).  

These data can also be programmatically downloaded with the utility below. Note that Google will temporarily restrict frequent repetitive file access via this utility. Manual download via the link above will continue to work.
```
$ conda activate gtsa
$ cd ./gtsa/scripts
$ python -u download_staged_data.py -site rainier -historicals Y -earthdem Y
```

Other auxiliary data are staged [here](https://drive.google.com/drive/folders/19luPMbR8j-Jm05Z1nMCD4q_BGHNC5vHa)

## Content

__./gtsa__  
Python library with custom functions for this analysis.

__./notebooks__  
Jupyter notebooks that describe the analysis steps, show plots, and tell the data story.

__./scripts__  
Utilities to download data and produce all relevant figures.

## Contributing

Example [workflow](https://github.com/geohackweek/sample_project_repository/wiki/Git-workflow-for-teams) to create a branch, push/preserve dev code, and send a PRs to main when ready for review and sharing.

## Drafting
[Google doc](https://docs.google.com/document/d/1IzehjabAB6lK7_1bGqfejESAwazdfVmTTvTMFRw6MAw/edit?usp=sharing) for general notes and ideas

[Google slides](https://docs.google.com/presentation/d/1t9JFpwyUoKOKqUrn7iRAAerpMa51owGOK7c7gT1UBQ8/edit?usp=sharing) document to share draft figures

[JoG template](https://www.overleaf.com/8531784554dhzrkzksdbws) on Overleaf for drafting
