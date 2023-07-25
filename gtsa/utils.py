"""Various utilities"""

from __future__ import annotations

from pathlib import Path
import psutil
from tqdm import tqdm
import concurrent
from datetime import datetime, timedelta
import numpy as np
import rioxarray
from rasterio.enums import Resampling

import gtsa


def decyear_to_date_time(
    decyear: float, leapyear=True, 
) -> datetime.datetime:
    """
    Convert a decimal year to a datetime object.
    If leapyear set to True, use the actual number of days in the year, otherwise, use the average value of 365.25.
    """
    # Get integer year and decimals
    year = int(np.trunc(decyear))
    decimals = decyear - year

    # Convert to date and time
    base = datetime(year, 1, 1)
    ndays = base.replace(year=base.year + 1) - base

    # Calculate final date, taking into account leap years or average 365.25 days
    if leapyear:
        date_time = base + timedelta(seconds=ndays.total_seconds() * decimals)
    else:
        date_time = base + timedelta(seconds=365.25 * 24 * 3600 * decimals)

    return date_time


def date_time_to_decyear(date_time: float, leapyear=True) -> float:
    """
    Convert a datetime object to a decimal year.
    If leapyear set to True, use the actual number of days in the year, otherwise, use the average value of 365.25.
    """
    base = datetime(date_time.year, 1, 1)
    ddate = date_time - base

    if leapyear:
        ndays = (datetime(date_time.year + 1, 1, 1) - base).days
    else:
        ndays = 365.25

    decyear = date_time.year + ddate.total_seconds() / (ndays * 24 * 3600)

    return decyear


def resample_dem(
    dem_file_name, res=1, out_file_name=None, overwrite=True, verbose=True
):
    """
    Inputs
    dem_file_name : str  : path to dem file
    res           : int  : target resolution
    out_file_name : str  : desired output file path and name
    overwrite     : bool : Option to overwrite existing file
    verbose       : bool : Print information

    Assumes crs is in UTM
    """
    res = str(res)

    if not out_file_name:
        out_file_name = "_".join(
            [str(Path(dem_file_name).with_suffix("")), res + "m.tif"]
        )

    Path(out_file_name).parent.mkdir(parents=True, exist_ok=True)

    if Path(out_file_name).exists() and not overwrite:
        return out_file_name

    if overwrite:
        Path(out_file_name).unlink(missing_ok=True)

    call = [
        "gdalwarp",
        "-r",
        "cubic",
        "-tr",
        res,
        res,
        "-co",
        "TILED=YES",
        "-co",
        "COMPRESS=LZW",
        "-co",
        "BIGTIFF=IF_SAFER",
        "-dstnodata",
        "-9999",
        dem_file_name,
        out_file_name,
    ]

    gtsa.io.run_command(call, verbose=verbose)
    return out_file_name


def create_cogs(
    files,
    output_directory=None,
    crs="EPSG:4326",
    suffix="_COG.tif",
    overwrite=False,
    workers=None,
    verbose=True,
):
    """
    Inputs
    files            : list : Path to .tif files
    output_directory : str  : Path to write COGs. Default is parent path of first file in files
    crs              : str  : EPSG code. 4326 is currently required for visualization with folium and TiTiler
    suffix           : str  : Suffix with extension for output file names
    overwrite        : bool : Option to overwrite existing files. If False, these will be skipped
    workers      : int  : nuber of threads to use. Default is virtual cores -1
    verbose          : bool : Print information
    """

    if not workers:
        workers = psutil.cpu_count(logical=True) - 1

    if len(files) < workers:
        print("Reducing workers to one per input file")
        workers = len(payload)

    if not output_directory:
        output_directory = Path(Path(files[0].parent), "cogs")
    else:
        output_directory = Path(output_directory)

    output_directory.mkdir(parents=True, exist_ok=True)

    existing_outputs = []
    payload = []

    def to_raster(payload):
        ds, out, crs = payload
        ds = ds.rio.reproject(crs, resampling=Resampling.cubic)

        ds.rio.to_raster(
            out,
            driver="cog",
            lock=True,
            compress="deflate",
            blocksize=512,
        )

    for fn in files:
        out_fn = Path(output_directory, fn.with_suffix("").name + suffix)
        if out_fn.exists() and not overwrite:
            existing_outputs.append(out_fn.as_posix())

        else:
            out_fn.unlink(missing_ok=True)
            ds = rioxarray.open_rasterio(fn)
            payload.append((ds, out_fn, crs))

    if existing_outputs and verbose:
        print("The following files already exist:")
        for i in existing_outputs:
            print(i)
        print("overwrite set to", overwrite)

    if payload:
        if verbose:
            print("Processing", len(payload), "rasters with", workers, "workers")
        with tqdm(total=len(payload)) as pbar:
            pool = concurrent.futures.ThreadPoolExecutor(workers=workers)
            futures = {pool.submit(to_raster, x): x for x in payload}
            for future in concurrent.futures.as_completed(futures):
                pbar.update(1)

    files = sorted(output_directory.glob("*" + suffix))
    return [x.as_posix() for x in files]
