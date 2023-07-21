from bs4 import BeautifulSoup
from pathlib import Path
import requests
import psutil
from tqdm import tqdm
import concurrent
import gdown


def download_data(payload):
    """
    Executes request for url and output file name contained in paylod.

    Input
    payload : tuple : tuple of url, filename
    """

    url, out = payload
    r = requests.get(url)
    open(out, "wb").write(r.content)
    return out


def thread_downloads(payload, max_workers=None):
    """
    Executes multithreaded requests for urls and output file names contained in payload.

    Inputs
    payload          : list : list of url, filename tuples
    max_workers      : int  : number of threads to execture concurrent requests with. defaults to virtually available cores -1

    """

    if not max_workers:
        max_workers = psutil.cpu_count(logical=True) - 1

    with tqdm(total=len(payload)) as pbar:
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        future_to_url = {pool.submit(download_data, x): x for x in payload}
        for future in concurrent.futures.as_completed(future_to_url):
            pbar.update(1)


def download_historical_data(
    site="mount-baker",
    product="dem",
    output_directory="data",
    include_refdem=False,
    overwrite=False,
    max_workers=None,
    verbose=True,
):
    """
    Downloads 1m DEMs from https://zenodo.org/record/7297154

    Inputs
    site    : str : 'mount-baker' or 'south-cascade'
    product : str : 'dem' or 'ortho'
    """

    if site != "mount-baker" and site != "south-cascade":
        print("site must be either 'baker' or 'south-cascade'")
        return

    if product != "dem" and product != "ortho":
        print("product must be either 'dem' or 'ortho'")
        return

    else:
        if product == "dem":
            product_key = "1m_dem"

        elif product == "ortho":
            product_key = "ortho"

        if include_refdem:
            download_reference_dems(
                site=site,
                output_directory=output_directory,
                overwrite=overwrite,
                verbose=verbose,
            )

        if not max_workers:
            max_workers = psutil.cpu_count(logical=True) - 1

        base = "https://zenodo.org/"
        url = base + "record/7297154"

        reqs = requests.get(url)
        soup = BeautifulSoup(reqs.text, "html.parser")

        output_directory = Path(output_directory, product + "s", site)
        output_directory.mkdir(parents=True, exist_ok=True)

        urls = []
        for link in soup.find_all("a"):
            url = link.get("href")
            if url:
                if product_key in url and site in url:
                    urls.append(base + url[1:])
        urls = sorted(set(urls))
        outputs = [
            Path(output_directory, url.split("/")[-1].split("?")[0]) for url in urls
        ]

        payload = []
        omissions = []
        for i, v in enumerate(outputs):
            if v.exists() and not overwrite:
                omissions.append(str(v))
            else:
                zipped = list(zip([urls[i], str(v)]))
                payload.append((zipped[0][0], zipped[1][0]))

        if omissions and verbose:
            print("Skipping existing files:")
            for i in omissions:
                print(i)
        if verbose:
            if overwrite:
                print("overwrite set to True")
            else:
                print("overwrite set to False")

        if payload:
            if verbose:
                print("Downloading data from https://zenodo.org/record/7297154")
                print('Site:',site)
                print('Using', max_workers, 'cores')
                print("Downloading:")
                for i in payload:
                    print(i[0])
                print("Writing to", str(output_directory))

            thread_downloads(
                payload,
                max_workers=max_workers,
            )
        if not payload and omissions and verbose:
            print("All files already exist")
        elif not omissions and not payload:
            print("No files available for download at", url)


def download_reference_dems(
    site="mount-baker",
    output_directory="data",
    overwrite=False,
    verbose=True,
):
    """
    Downloads reference DEMs for DEMs at https://zenodo.org/record/7297154

    input options:
    site : 'mount-baker' or 'south-cascade'
    """

    if site != "mount-baker" and site != "south-cascade":
        print("site must be either 'baker' or 'south-cascade'")
        return

    scg = "1m1DSnZ7tNIko6iU4WuPFsDODLkHX-E-6"
    scg_fn = "WV_south-cascade_20151014_1m_dem.tif"
    baker = "1SXwGmjkjp3oCuF64XM9j894YJBR8bzs9"
    baker_fn = "WADNR_mount-baker_20150827_1m_dem.tif"

    output_directory = Path(output_directory, "dems", site)
    output_directory.mkdir(parents=True, exist_ok=True)

    if site == "mount-baker":
        blob_id = baker
        output = Path(output_directory, baker_fn)
    elif site == "south-cascade":
        blob_id = scg
        output = Path(output_directory, scg_fn)
    else:
        print("site must be specified as either 'baker' or 'south-cascade'")
        return

    if verbose:
        if overwrite:
            print("overwrite set to True")
        else:
            print("overwrite set to False")

    if output.exists() and not overwrite:
        if verbose:
            print("Reference DEM file exists")
            print(output.as_posix())

    else:
        if verbose:
            print("Downloading reference dem for", site)
        gdown.download(id=blob_id, output=output.as_posix(), quiet=not verbose)

    return
