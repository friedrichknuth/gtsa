# Geospatial Time Series Analysis
Methods to compute continuous per-pixel raster change from temporally and spatially sparse measurements.

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

Below are example functionalities provided by gtsa. Each example is accompanied by a jupyter notebook and python script. The notebooks help illustrate the steps performed in the corresponding script.

- Stack single band rasters and chunk along the time dimension for efficient regression analysis
    - notebooks/create_stacks.py
    - scripts/create_stacks.py

- Run memory-efficient regression analysis methods using dask
    - notebooks/fit_regression_to_stack.ipynb
    - scripts/run_regression.py
    
- Convert single band GeoTIFFs to Cloud Optimized GeoTIFFs (COGs) for efficient visualization, e.g. as seen in this [interactive map](https://staff.washington.edu/knuth/downloads/conus_sites.html).
    - notebooks/make_cog_map.ipynb
    - scripts/create_cogs.py