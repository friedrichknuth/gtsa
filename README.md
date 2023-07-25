# Geospatial Time Series Analysis
Methods to stack geospatial rasters and make memory-efficient computations along the time axis. 

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

## Examples

### Processing

#### Stack single band rasters and chunk along the time dimension for efficient data retrieval
From command line
```
create_stack --help
```
Python examples in 
```
notebooks/processing/01_create_stacks.ipynb`
```

#### Run memory-efficient time series analysis methods using dask
From command line
```
gtsa --help
```
Python examples in 
```
notebooks/processing/02_time_series_computations.ipynb`
```

### Visualization


#### Convert single band rasters to Cloud Optimized GeoTIFFs (COGs)
From command line
```
create_cogs --help
```

Python examples in 
```
notebooks/visualization/01_create_cogs.ipynb
```

#### Create interactive folium map for efficient visualization
From command line
```
create_cog_map --help
```

Python examples in 
```
notebooks/visualization/02_create_cog_map.ipynb
```

## Download sample data
From command line
```
download_data --help
```

Example

```
download_data --site south-cascade \
              --outdir data \
              --product dem \
              --include_refdem \
              --max_workers 8 \
              --verbose \
              --overwrite
```

## Data citations

Knuth. F. and D. Shean. (2022). Historical digital elevation models (DEMs) and orthoimage mosaics for North American Glacier Aerial Photography (NAGAP) program, version 1.0 [Data set]. Zenodo. https://doi.org/10.5281/zenodo.7297154 

Knuth, F., Shean, D., Bhushan, S., Schwat, E., Alexandrov, O., McNeil, C., Dehecq, A., Florentine, C. and O’Neel, S., 2023. Historical Structure from Motion (HSfM): Automated processing of historical aerial photographs for long-term topographic change analysis. Remote Sensing of Environment, 285, p.113379. https://doi.org/10.1016/j.rse.2022.113379 

