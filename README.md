# Geospatial Time Series Analysis
Methods to stack geospatial rasters and run memory-efficient computations. [![DOI](https://zenodo.org/badge/505980033.svg)](https://zenodo.org/badge/latestdoi/505980033)


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

## Command Line examples

See `command --help` for more information about each command listed below.

### Processing

#### Download sample Digital Elevation Model (DEM) data
```
download_data --site south-cascade \
              --outdir data \
              --product dem \
              --include_refdem \
              --workers 8 \
              --overwrite        
```

#### Stack single-band rasters and chunk along the time dimension
```
create_stack --datadir data/dems/south-cascade \
             --date_string_format %Y%m%d \ # %Y-%m-%d
             --date_string_pattern _........_ \ # ....-..-..
             --date_string_pattern_offset 1 \ # 0
             --outdir data/dems/south-cascade \
             --dask_enabled \
             --overwrite
```

#### Run memory-efficient time series analysis methods using dask

```
c=count # count, mean, std, min, max, median, sum or nmad
gtsa --input_file data/dems/south-cascade/temporal/stack.zarr \
     --compute $c \
     --outdir data/dems/south-cascade/outputs \
     --workers 8\
     --dask_enabled \
     --overwrite \ 
     --test_run

# Linear regression
gtsa --input_file data/dems/south-cascade/temporal/stack.zarr \
     --compute polyfit \
     --degree 1 \
     --frequency 1Y \
     --outdir data/dems/south-cascade/outputs \
     --dask_enabled

# Higher order polynomial fits
d=3 
gtsa --input_file data/dems/south-cascade/temporal/stack.zarr \
     --compute polyfit \
     --degree $d \
     --frequency 1Y \
     --outdir data/dems/south-cascade/outputs \
     --dask_enabled
```

### Visualization

See rendered interactive map [examples here](https://nbviewer.org/github/friedrichknuth/gtsa/blob/main/notebooks/visualization/02_create_cog_map.ipynb). 

#### Download sample orthoimage data
```
download_data --site south-cascade \
              --outdir data \
              --product ortho \
              --workers 8 \
              --overwrite        
```

#### Convert single-band rasters to Cloud Optimized GeoTIFFs (COGs)
```
create_cogs --datadir data/orthos/south-cascade \
            --outdir data/orthos/south-cascade/cogs \
            --workers 8 \
            --overwrite
```

#### Create interactive folium map for efficient visualization
```
create_cog_map --pipeline notebooks/visualization/pipeline.json \
               --output_file map.html \
               --zoom_start 11 \ 
               --overwrite
```

## Python examples
See Jupyter Notebooks in `notebooks/` for example Python code.

## Data citations

Knuth. F. and D. Shean. (2022). Historical digital elevation models (DEMs) and orthoimage mosaics for North American Glacier Aerial Photography (NAGAP) program, version 1.0 [Data set]. Zenodo. https://doi.org/10.5281/zenodo.7297154 

Knuth, F., Shean, D., Bhushan, S., Schwat, E., Alexandrov, O., McNeil, C., Dehecq, A., Florentine, C. and O’Neel, S., 2023. Historical Structure from Motion (HSfM): Automated processing of historical aerial photographs for long-term topographic change analysis. Remote Sensing of Environment, 285, p.113379. https://doi.org/10.1016/j.rse.2022.113379 

