import numpy as np
import folium
from folium import plugins

from gtsa import geospatial


def plot_cogs_sites(
    payload,
    html_file_name=None,
    cogs_attribution="gtsa",
    tiler="https://titiler.xyz/cog/tiles/WebMercatorQuad/{z}/{x}/{y}",
    expression="expression=b1&rescale=0,255",
    folium_map_object=None,
    zoom_start=10,
    basemap_tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    basemap_opacity=0.8,
    basemap_attribution="Google Earth",
    minimap=True,
    layer_control=True,
    fullscreen=True,
    verbose=False,
):
    site_names = list(payload["sites"].keys())
    cog_urls_by_site = [payload["sites"][i]["cog_urls"] for i in site_names]
    cog_names_by_site = [payload["sites"][i]["cog_names"] for i in site_names]
    site_marker_coords = [payload["sites"][i]["marker_coords"] for i in site_names]
    site_marker_names = [payload["sites"][i]["marker_name"] for i in site_names]
    cog_overview_indices = [payload["sites"][i]["overview_index"] for i in site_names]
    map_center_lat, map_center_lon = payload["map_center"]

    if not folium_map_object:
        if not map_center_lon or not map_center_lat:
            centroids = [
                geospatial._get_rasters_centroid(urls) for urls in cog_urls_by_site
            ]
            lats = np.array(centroids)[:, 1]
            lons = np.array(centroids)[:, 0]
            map_center_lat = (np.max(lats) - np.min(lats)) / 2 + np.min(lats)
            map_center_lon = (np.max(lons) - np.min(lons)) / 2 + np.min(lons)

    m = folium_map_object
    if not m:
        m = _initialize_folium_map(
            map_center_lon,
            map_center_lat,
            zoom_start=zoom_start,
            opacity=basemap_opacity,
            basemap_tiles=basemap_tiles,
            basemap_attribution=basemap_attribution,
        )
    cog_feature_group = folium.FeatureGroup(show=False, name="All sites")
    cog_feature_group.add_to(m)

    for i, cog_urls in enumerate(cog_urls_by_site):
        site = site_names[i]
        cog_names = cog_names_by_site[i]
        overview_cog_index = cog_overview_indices[i]
        feature_group = folium.FeatureGroup(site_marker_names[i])
        feature_group.add_to(m)

        for j, cog_url in enumerate(cog_urls):
            virtual_tiles = f"{tiler}?url={cog_url}"
            if expression:
                virtual_tiles = f"{virtual_tiles}&{expression}"

            if j == overview_cog_index:
                show = True
                folium.TileLayer(
                    tiles=virtual_tiles,
                    overlay=True,
                    show=show,
                    name=cog_names[j],
                    attr=cogs_attribution,
                ).add_to(m)
            else:
                show = False
                folium.TileLayer(
                    tiles=virtual_tiles,
                    overlay=True,
                    show=show,
                    name=cog_names[j],
                    attr=cogs_attribution,
                ).add_to(m).add_to(cog_feature_group)

        site_icon = plugins.BeautifyIcon(
            prefix="fa",
            icon="mountain",
            icon_color="blue",
            background_color="transparent",
            border_color="transparent",
            inner_icon_style="color:blue;font-size:300%",
        )

        folium.Marker(
            location=site_marker_coords[i],
            popup=site_marker_names[i],
            name=site_marker_names[i],
            icon=site_icon,
        ).add_to(m).add_to(feature_group)

    if fullscreen:
        plugins.Fullscreen(
            position="topleft",
            title="Expand me",
            title_cancel="Exit me",
            force_separate_button=True,
        ).add_to(m)

    if layer_control:
        folium.LayerControl(collapsed=True).add_to(m)

    if minimap:
        minimap = plugins.MiniMap(
            position="bottomleft",
        )
        m.add_child(minimap)

    plugins.Draw(export=True,
                 position = 'topleft').add_to(m)

    if verbose:
        print("map center:", map_center_lon, map_center_lat)

    if html_file_name:
        m.save(html_file_name)

    return m


def plot_cogs(
    cog_urls,
    cog_names,
    html_file_name=None,
    map_center_lon=None,
    map_center_lat=None,
    overview_cog_index=0,
    cogs_attribution="gtsa",
    tiler="https://titiler.xyz/cog/tiles/WebMercatorQuad/{z}/{x}/{y}",
    expression="expression=b1&rescale=0,255",
    folium_map_object=None,
    zoom_start=10,
    basemap_tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    basemap_opacity=0.8,
    basemap_attribution="Google Earth",
    minimap=True,
    layer_control=True,
    fullscreen=True,
    verbose=False,
):
    if not folium_map_object:
        if not map_center_lon or not map_center_lat:
            map_center_lon, map_center_lat = geospatial._get_rasters_centroid(cog_urls)

    m = folium_map_object
    if not m:
        m = _initialize_folium_map(
            map_center_lon,
            map_center_lat,
            zoom_start=zoom_start,
            opacity=basemap_opacity,
            basemap_tiles=basemap_tiles,
            basemap_attribution=basemap_attribution,
        )

    for i, cog_url in enumerate(cog_urls):
        show = False
        if i == overview_cog_index:
            show = True
        virtual_tiles = f"{tiler}?url={cog_url}"
        if expression:
            virtual_tiles = f"{virtual_tiles}&{expression}"

        folium.TileLayer(
            tiles=virtual_tiles,
            overlay=True,
            show=show,
            name=cog_names[i],
            attr=cogs_attribution,
        ).add_to(m)
    if fullscreen:
        plugins.Fullscreen(
            position="topleft",
            title="Expand me",
            title_cancel="Exit me",
            force_separate_button=True,
        ).add_to(m)

    if layer_control:
        folium.LayerControl(collapsed=True).add_to(m)

    if minimap:
        minimap = plugins.MiniMap(
            position="bottomleft",
        )
        m.add_child(minimap)

    plugins.Draw(export=True,
                 position = 'topleft').add_to(m)
    
    if verbose:
        print("map center:", map_center_lon, map_center_lat)

    if html_file_name:
        m.save(html_file_name)

    return m


def plot_cog(
    cog_url,
    html_file_name=None,
    cog_name="my raster",
    cog_attribution="gtsa",
    tiler="https://titiler.xyz/cog/tiles/WebMercatorQuad/{z}/{x}/{y}",
    expression="expression=b1&rescale=0,255",
    folium_map_object=None,
    zoom_start=11,
    basemap_tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    basemap_opacity=0.8,
    basemap_attribution="Google Earth",
):
    """
    Plots Cloud Optimized GeoTIFFs (COG) on interactive Folium map.
    """
    # TODO add check that cog is in EPSG:4326

    map_center_lon, map_center_lat = geospatial._get_raster_centroid(cog_url)

    virtual_tiles = f"{tiler}?url={cog_url}"
    if expression:
        virtual_tiles = f"{virtual_tiles}&{expression}"

    m = folium_map_object
    if not m:
        m = _initialize_folium_map(
            map_center_lon,
            map_center_lat,
            zoom_start=zoom_start,
            opacity=basemap_opacity,
            basemap_tiles=basemap_tiles,
            basemap_attribution=basemap_attribution,
        )

    folium.TileLayer(
        tiles=virtual_tiles,
        overlay=True,
        show=True,
        name=cog_name,
        attr=cog_attribution,
    ).add_to(m)

    plugins.Draw(export=True,
                 position = 'topleft').add_to(m)

    if html_file_name:
        m.save(html_file_name)

    return m


def _initialize_folium_map(
    lon,
    lat,
    zoom_start=10,
    opacity=0.8,
    basemap_tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    basemap_attribution="Google Earth",
):
    m = folium.Map(
        location=(lat, lon),
        tiles=False,
        zoom_start=zoom_start,
        control_scale=True,
    )
    folium.TileLayer(
        basemap_tiles,
        attr=basemap_attribution,
        opacity=opacity,
        name=basemap_attribution,
    ).add_to(m)

    return m
