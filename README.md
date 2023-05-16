# Geospatial Time Series Analysis
Methods to compute continuous surface elevation change from temporally and spatially sparse elevation measurements.

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
$ python -u download_staged_data.py -site rainier -earthdem -hsfm
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
