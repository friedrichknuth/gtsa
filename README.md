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
## Examples

Plotting 
- Create an [interactive map](https://staff.washington.edu/knuth/downloads/conus_sites.html) that efficiently visualizes many large rasters.


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
Main python library with custom functions developed for these analysis methods.

__./notebooks__  
Example Jupyter notebooks that describe the analysis steps and showcase functionality.

__./scripts__  
Utilities to download data, process at scale, and produce standard figures.

## Contributing

Example [workflow](https://github.com/friedrichknuth/gtsa/wiki/Git-workflow-for-teams) to create a branch, push/preserve dev code, and send a PRs to main when ready for review and sharing.
