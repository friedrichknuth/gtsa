# Glacier Time Series Analysis
Methods to compute continuous glacier change from temporally and spatially sparse elevation measurements.

## Notes
 - Current objective is to develop a robust Gaussian Process regression and kernel that is suitable for sparse historical DEM data.
 - This is a merely a testing and development repo.
 - Relevant code can be pushed to a dedicated public time-series analysis repo, [geoutils](https://github.com/GlacioHack/geoutils), [xDEM](https://github.com/GlacioHack/xdem) and/or the [KH-9 analysis](https://github.com/adehecq/kh9_glacier_global) effort.

## Installation
```
$ git clone https://github.com/friedrichknuth/gtsa.git
$ cd ./gtsa
$ mamba env create -f environment.yml
$ conda activate gtsa
$ pip install -e .
```

## Data
Analysis ready DEMs are staged [here](https://drive.google.com/drive/folders/1AMqnuMVYCa0xzwDOiowGAwd8iV63kSjf).  

Example download with provided script:
```
$ conda activate gtsa
$ cd ./gtsa/scripts
$ python -u download_staged_data.py -site rainier -hsfm -earthdem
```
Additional auxiliary data are staged [here](https://drive.google.com/drive/folders/19luPMbR8j-Jm05Z1nMCD4q_BGHNC5vHa)

## Content

__./gtsa__  
Python library with custom functions for this analysis.

__./notebooks__  
Jupyter notebooks that describe the analysis steps, show plots, and tell the data story.

__./scripts__  
Utilities to download data and produce all relevant figures.

## Contributing

Example [workflow](https://github.com/friedrichknuth/gtsa/wiki/Git-workflow-for-teams) to create a branch, push/preserve dev code, and send a PRs to main when ready for review and sharing.

## Drafting
[Google doc](https://docs.google.com/document/d/1IzehjabAB6lK7_1bGqfejESAwazdfVmTTvTMFRw6MAw/edit?usp=sharing) for general notes and ideas

[Google slides](https://docs.google.com/presentation/d/1t9JFpwyUoKOKqUrn7iRAAerpMa51owGOK7c7gT1UBQ8/edit?usp=sharing) document to share draft figures

[JoG template](https://www.overleaf.com/8531784554dhzrkzksdbws) on Overleaf for drafting
