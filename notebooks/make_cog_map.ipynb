{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "3cbf315f",
   "metadata": {},
   "outputs": [],
   "source": [
    "%load_ext autoreload\n",
    "%autoreload 2"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "0a11ee4b",
   "metadata": {},
   "outputs": [],
   "source": [
    "import gtsa"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "a58e583b",
   "metadata": {},
   "source": [
    "### Plot a single COG"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "a070d8c0",
   "metadata": {},
   "outputs": [],
   "source": [
    "cog_url = 'http://petrichor.s3.us-west-2.amazonaws.com/baker/orthos/ortho_1947-09-14_EE_reproj_COG.tif'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "73ce0a7f",
   "metadata": {},
   "outputs": [],
   "source": [
    "gtsa.plotting.plot_cog(cog_url   = cog_url,\n",
    "                       zoom_start = 10)"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "f8738564",
   "metadata": {},
   "source": [
    "### Plot multiple cogs"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "8d63f866",
   "metadata": {},
   "outputs": [],
   "source": [
    "s3_bucket_name = 'petrichor'\n",
    "folder = 'baker/orthos/'"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "61fff947",
   "metadata": {},
   "outputs": [],
   "source": [
    "cog_urls = gtsa.io.parse_urls_from_S3_bucket(s3_bucket_name,\n",
    "                                             aws_server_url = 's3.us-west-2.amazonaws.com',\n",
    "                                             folder = folder)\n",
    "\n",
    "dates = gtsa.io.parse_timestamps(cog_urls,\n",
    "                                 date_string_pattern='....-..-..')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "d6ecd1b6",
   "metadata": {},
   "outputs": [],
   "source": [
    "map_center_lon = -121.78096499929248\n",
    "map_center_lat = 48.75153547423788\n",
    "    \n",
    "gtsa.plotting.plot_cogs(cog_urls,\n",
    "                        dates,\n",
    "                        map_center_lon      = map_center_lon,\n",
    "                        map_center_lat      = map_center_lat,\n",
    "                        zoom_start=12,\n",
    "                        overview_cog_index  = 0,\n",
    "                        print_info          = True,\n",
    "                       )"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "7ce040b7",
   "metadata": {},
   "source": [
    "### Plot multiple sites"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "8bb3868d",
   "metadata": {},
   "outputs": [],
   "source": [
    "s3_bucket_name = 'petrichor'\n",
    "sites = gtsa.io._get_test_sites(s3_bucket_name)\n",
    "folders = [gtsa.io.Path(s, 'orthos').as_posix() for s in sites]\n",
    "\n",
    "cog_urls_by_site = [gtsa.io.parse_urls_from_S3_bucket(s3_bucket_name,\n",
    "                                                     aws_server_url = 's3.us-west-2.amazonaws.com',\n",
    "                                                     folder = f) for f in folders]\n",
    "\n",
    "cog_dates_by_site = [gtsa.io.parse_timestamps(c) for c in cog_urls_by_site]\n",
    "sites"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "f53aec13",
   "metadata": {},
   "outputs": [],
   "source": [
    "site_marker_names = {'baker': 'Mount Baker',\n",
    "                     'gnp': 'Glacier National Park',\n",
    "                     'helens': 'Mount Saint Helens',\n",
    "                     'hinman': 'Hinman Glacier',\n",
    "                     'rainier': 'Mount Rainier',\n",
    "                     'scg': 'South Cascade Glacier',\n",
    "                     'tetons': 'Grand Teton Glacier',\n",
    "                    }"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "9f75594c",
   "metadata": {},
   "outputs": [],
   "source": [
    "cog_overview_indices = {'baker': 0,\n",
    "                        'gnp': 0,\n",
    "                        'helens': 0,\n",
    "                        'hinman': 10,\n",
    "                        'rainier': 1,\n",
    "                        'scg': 0,\n",
    "                        'tetons': 0,\n",
    "                        }"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "d44cf81f",
   "metadata": {},
   "outputs": [],
   "source": [
    "site_marker_coords = {'baker': (48.7767, -121.8144),\n",
    "                      'gnp': (48.7596, -113.7870),\n",
    "                      'helens': (46.1914, -122.1956),\n",
    "                      'hinman': (47.5752, -121.2307),\n",
    "                      'rainier': (46.8523, -121.7603),\n",
    "                      'scg': (48.3717, -121.0660),\n",
    "                      'tetons': (43.7422, -110.7925),\n",
    "                     }"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "c26c1171",
   "metadata": {},
   "outputs": [],
   "source": [
    "map_center_lon = -116.4544259369602\n",
    "map_center_lat = 46.2537663566596\n",
    "\n",
    "m = gtsa.plotting.plot_cogs_sites(sites,\n",
    "                                  cog_urls_by_site,\n",
    "                                  cog_dates_by_site,\n",
    "                                  site_marker_coords   = site_marker_coords,\n",
    "                                  site_marker_names    = site_marker_names,\n",
    "                                  cog_overview_indices = cog_overview_indices,\n",
    "                                  map_center_lon       = map_center_lon,\n",
    "                                  map_center_lat       = map_center_lat,\n",
    "                                  zoom_start           = 6,\n",
    "                                  print_info          = True,\n",
    "                             )"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "13599b29",
   "metadata": {},
   "outputs": [],
   "source": [
    "m.save('conus_sites.html')"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "bf9dd639",
   "metadata": {},
   "source": [
    "Example https://staff.washington.edu/knuth/downloads/conus_sites.html"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "7de3da35",
   "metadata": {},
   "source": [
    "### Known issues\n",
    "- collapsable navigation menu by site would be preferred but is not natively supported by folium\n",
    "- duplicate dates as COG names in the drop down will overwrite. stopgap solution is to prefix sith the site id\n",
    "- the All Sites legend entry is a stopgap solution to only show a single COG to start\n",
    "- if COGs are not added to a featuregroup that has show = False, they get burned in to the map somehow, which appears to be a bug"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python [conda env:gtsa]",
   "language": "python",
   "name": "conda-env-gtsa-py"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.11.3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
