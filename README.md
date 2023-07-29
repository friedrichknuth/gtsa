# Geospatial Time Series Analysis
Methods to stack geospatial rasters and run memory-efficient computations.  
[![DOI](https://zenodo.org/badge/505980033.svg)](https://zenodo.org/badge/latestdoi/505980033)

<img src="./tests/img/intro-light.png#gh-light-mode-only" align="right" width="510px">
<img src="./tests/img/intro-dark.png#gh-dark-mode-only" align="right" width="510px">
<h2>Motivation</h2>
Sometimes your data is larger than your local memory and not everyone has access to high-performance computing environments. This excludes individuals from participating in studies with the objective to process larger-than-memory datasets. 
<br><br>
When data cubes are too large to load into memory, <a href="https://zarr.readthedocs.io/">Zarr</a> and <a href="https://www.dask.org/">dask</a> enable chunked storage and parallelized data retrieval. GTSA streamlines this process for geospatial raster datasets, enabling memory efficient comptutations along both the spatial <b>and</b> temporal axes.
<br clear="right"/>

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

## Python examples
See [Jupyter Notebooks](./notebooks) for example Python code.

## Command Line examples

See `command --help` for more information about each command listed below.

### Processing

#### Stack single-band rasters and chunk along the analysis dimension
<img src="./tests/img/stacking-light.png#gh-light-mode-only" align="left" width="500px">
<img src="./tests/img/stacking-dark.png#gh-dark-mode-only" align="left" width="500px">
<pre><code> create_stack --datadir data/dems/south-cascade \
             --date_string_format %Y%m%d \
             --date_string_pattern _........_ \
             --date_string_pattern_offset 1 \
             --outdir data/dems/south-cascade \
             --dask_enabled \
             --overwrite
</code></pre>
<br clear="left"/>

#### Run memory-efficient time series analysis methods using dask

Basic `--compute` options include `count`, `min`, `max`, `mean`, `std`, `median`, `sum`, and `nmad`.
```
computation=count
gtsa --input_file data/dems/south-cascade/temporal/stack.zarr \
     --compute $computation \
     --outdir data/dems/south-cascade/outputs \
     --workers 8\
     --dask_enabled \
     --overwrite \ 
     --test_run
```
Linear regression
```
gtsa --input_file data/dems/south-cascade/temporal/stack.zarr \
     --compute polyfit \
     --degree 1 \
     --frequency 1Y \
     --outdir data/dems/south-cascade/outputs \
     --dask_enabled
```
Higher-order polynomial fits
```
degree=3 
gtsa --input_file data/dems/south-cascade/temporal/stack.zarr \
     --compute polyfit \
     --degree $degree \
     --frequency 1Y \
     --outdir data/dems/south-cascade/outputs \
     --dask_enabled
```
### Visualization

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

See rendered interactive map [examples here](https://nbviewer.org/github/friedrichknuth/gtsa/blob/main/notebooks/visualization/02_create_cog_map.ipynb). 

## Sample data

#### Download sample Digital Elevation Model (DEM) data
```
download_data --site south-cascade \
              --outdir data \
              --product dem \
              --include_refdem \
              --workers 8 \
              --overwrite        
```

#### Download sample orthoimage data
```
download_data --site south-cascade \
              --outdir data \
              --product ortho \
              --workers 8 \
              --overwrite        
```

## Data citations

Knuth. F. and D. Shean. (2022). Historical digital elevation models (DEMs) and orthoimage mosaics for North American Glacier Aerial Photography (NAGAP) program, version 1.0 [Data set]. Zenodo. https://doi.org/10.5281/zenodo.7297154 

Knuth, F., Shean, D., Bhushan, S., Schwat, E., Alexandrov, O., McNeil, C., Dehecq, A., Florentine, C. and O’Neel, S., 2023. Historical Structure from Motion (HSfM): Automated processing of historical aerial photographs for long-term topographic change analysis. Remote Sensing of Environment, 285, p.113379. https://doi.org/10.1016/j.rse.2022.113379 

## Similar software
- NASA Ames Stereo Pipeline: [dem_mosaic](https://stereopipeline.readthedocs.io/en/latest/tools/dem_mosaic.html)

## Complimentary software 
- [xDEM](https://xdem.readthedocs.io)
- [xarray-spatial](https://xarray-spatial.org/)