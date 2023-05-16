import geopandas as gpd
import matplotlib
import numpy as np
from IPython.display import HTML
from matplotlib import animation
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from mpl_toolkits.axes_grid1 import make_axes_locatable
import folium
from folium import plugins

from gtsa import geospatial

def plot_cogs_sites(site_names,
                    cog_urls_by_site,
                    cog_names_by_site,
                    html_file_name       = None,
                    site_marker_coords   = None,
                    site_marker_names    = None,
                    cog_overview_indices = None,
                    map_center_lon       = None,
                    map_center_lat       = None,
                    cogs_attribution     = 'gtsa',
                    tiler                = 'https://titiler.xyz/cog/tiles/{z}/{x}/{y}',
                    expression           = 'expression=b1&rescale=0,255',
                    folium_map_object    = None,
                    zoom_start           = 10,
                    basemap_tiles        = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                    basemap_opacity      = 0.8,
                    basemap_attribution  = 'Google Earth',
                    minimap              = True,
                    layer_control        = True,
                    fullscreen           = True,
                    print_info           = False,
                    ):
    
    if not folium_map_object:
        if not map_center_lon or not map_center_lat:
            centroids = [geospatial._get_rasters_centroid(urls) for urls in cog_urls_by_site]
            lats = np.array(centroids)[:,1]
            lons = np.array(centroids)[:,0]
            map_center_lat = (np.max(lats) - np.min(lats))/2 + np.min(lats)
            map_center_lon = (np.max(lons) - np.min(lons))/2 + np.min(lons)
    
    m = folium_map_object
    if not m:
        m = _initialize_folium_map(map_center_lon,
                                   map_center_lat,
                                   zoom_start = zoom_start,
                                   opacity = basemap_opacity,
                                   basemap_tiles = basemap_tiles,
                                   basemap_attribution = basemap_attribution)
    cog_feature_group = folium.FeatureGroup(show=False, name='All sites')
    cog_feature_group.add_to(m) 
    
    for i, cog_urls in enumerate(cog_urls_by_site):
        site = site_names[i]
        cog_names = cog_names_by_site[i]
        overview_cog_index = cog_overview_indices[site]
        feature_group = folium.FeatureGroup(site_marker_names[site])
        feature_group.add_to(m)
        
        for j,cog_url in enumerate(cog_urls):
            virtual_tiles = f"{tiler}?url={cog_url}"
            if expression:
                virtual_tiles = f"{virtual_tiles}&{expression}"

            if j == overview_cog_index:
                show = True
                folium.TileLayer(tiles=virtual_tiles, 
                                 overlay=True, 
                                 show = show,
                                 name=site+'_'+cog_names[j], 
                                 attr=cogs_attribution).add_to(m)
            else:
                show = False
                folium.TileLayer(tiles=virtual_tiles, 
                                 overlay=True, 
                                 show = show,
                                 name=site+'_'+cog_names[j], 
                                 attr=cogs_attribution).add_to(m).add_to(cog_feature_group)
            
        site_icon = plugins.BeautifyIcon(prefix='fa',
                                         icon="mountain", 
                                         icon_color='blue',
                                         background_color='transparent',
                                         border_color='transparent', 
                                         inner_icon_style="color:blue;font-size:300%")

        folium.Marker(location=site_marker_coords[site], 
                      popup=site_marker_names[site],
                      name=site_marker_names[site],
                      icon=site_icon).add_to(m).add_to(feature_group)
    
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
        minimap = plugins.MiniMap(position="bottomleft",)
        m.add_child(minimap)
    
    if print_info:
        print('map center:', map_center_lon, map_center_lat)
    
    if html_file_name:
        m.save(html_file_name)
    
    return m



def plot_cogs(cog_urls,
              cog_names,
              html_file_name      = None,
              map_center_lon      = None,
              map_center_lat      = None,
              overview_cog_index  = 0,
              cogs_attribution    = 'gtsa',
              tiler               = 'https://titiler.xyz/cog/tiles/{z}/{x}/{y}',
              expression          = 'expression=b1&rescale=0,255',
              folium_map_object   = None,
              zoom_start          = 10,
              basemap_tiles       = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
              basemap_opacity     = 0.8,
              basemap_attribution = 'Google Earth',
              minimap             = True,
              layer_control       = True,
              fullscreen          = True,
              print_info          = False,
             ):
    
    if not folium_map_object:
        if not map_center_lon or not map_center_lat:
            map_center_lon, map_center_lat = geospatial._get_rasters_centroid(cog_urls)
    
    m = folium_map_object
    if not m:
        m = _initialize_folium_map(map_center_lon,
                                   map_center_lat,
                                   zoom_start = zoom_start,
                                   opacity = basemap_opacity,
                                   basemap_tiles = basemap_tiles,
                                   basemap_attribution = basemap_attribution)
        
    for i,cog_url in enumerate(cog_urls):
        show = False
        if i == overview_cog_index:
            show = True
        virtual_tiles = f"{tiler}?url={cog_url}"
        if expression:
            virtual_tiles = f"{virtual_tiles}&{expression}"
            
        folium.TileLayer(tiles=virtual_tiles, 
                         overlay=True, 
                         show = show,
                         name=cog_names[i], 
                         attr=cogs_attribution).add_to(m)
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
        minimap = plugins.MiniMap(position="bottomleft",)
        m.add_child(minimap)
        
    if print_info:
        print('map center:', map_center_lon, map_center_lat)
    
    if html_file_name:
        m.save(html_file_name)
    
    return m
    
    

def plot_cog(cog_url, 
             html_file_name      = None,
             cog_name            = 'my raster',
             cog_attribution     = 'gtsa',
             tiler               = 'https://titiler.xyz/cog/tiles/{z}/{x}/{y}',
             expression          = 'expression=b1&rescale=0,255',
             folium_map_object   = None,
             zoom_start          = 11,
             basemap_tiles       = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
             basemap_opacity     = 0.8,
             basemap_attribution = 'Google Earth'):
    
    '''
    Plots Cloud Optimized GeoTIFFs (COG) on interactive Folium map.
    '''
    #TODO add check that cog is in EPSG:4326
    
    map_center_lon, map_center_lat = geospatial._get_raster_centroid(cog_url)
    
    virtual_tiles = f"{tiler}?url={cog_url}"
    if expression:
        virtual_tiles = f"{virtual_tiles}&{expression}"
    
    m = folium_map_object
    if not m:
        m = _initialize_folium_map(map_center_lon,
                                   map_center_lat,
                                   zoom_start = zoom_start,
                                   opacity = basemap_opacity,
                                   basemap_tiles = basemap_tiles,
                                   basemap_attribution = basemap_attribution)

    folium.TileLayer(tiles=virtual_tiles, 
                     overlay=True, 
                     show = True,
                     name=cog_name, 
                     attr=cog_attribution).add_to(m)
    
    if html_file_name:
        m.save(html_file_name)
    
    return m


def _initialize_folium_map(lon,
                           lat,
                           zoom_start          = 10,
                           opacity             = 0.8,
                           basemap_tiles       = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                           basemap_attribution = 'Google Earth'):
    m = folium.Map(
        location=(lat, lon),
        tiles=False,
        zoom_start=zoom_start,
        control_scale = True,
        )
    folium.TileLayer(basemap_tiles, 
                     attr=basemap_attribution,
                     opacity=opacity,
                     name=basemap_attribution).add_to(m)
    
    return m

def plot_array_gallery(array_3d, 
                       titles_list=None, 
                       figsize=(10, 15), 
                       vmin=None, vmax=None, 
                       cmap="viridis",
                       ticks_on=False):

    if not vmin:
        vmin = int(np.nanmin(array_3d) - 50)
    if not vmax:
        vmax = int(np.nanmax(array_3d) + 50)

    rows, columns = get_row_column(len(array_3d))
    fig = plt.figure(figsize=(10, 15))

    for i in range(rows * columns):
        try:
            array = array_3d[i]
            ax = plt.subplot(rows, columns, i + 1, aspect="auto")
            ax.imshow(array, interpolation="none", cmap=cmap, vmin=vmin, vmax=vmax)
            if not ticks_on:
                ax.set_xticks(())
                ax.set_yticks(())
            if titles_list:
                ax.set_title(titles_list[i])
        except:
            pass
    plt.tight_layout()


def plot_time_series_gallery(
    x_values,
    y_values,
    labels=None,
    predictions_df_list=None,
    std_df_list=None,
    x_ticks_off=False,
    y_ticks_off=False,
    sharex=True,
    sharey=True,
    ylim=None, 
    y_label='Elevation (m)',
    x_label='Time',
    figsize=(15, 10),
    legend=True,
    linestyle="none",
    legend_labels=[
        "Observations",
    ],
    random_choice = False,
    output_file = None,
):

    rows, columns = get_row_column(len(x_values))

    fig = plt.figure(figsize=figsize)
    axes = []
    for i in range(rows * columns):
        try:
            x, y = x_values[i], y_values[i]
            ax = plt.subplot(rows, columns, i + 1, aspect="auto")
            ax.plot(x, y, marker="o", c="b", linestyle=linestyle, label=legend_labels[0])
            if random_choice:
                random_index = np.random.choice(np.arange(x.size))
                ax.plot(x[random_index], y[random_index], marker="o", c="r", linestyle=linestyle)
            if x_ticks_off:
                ax.set_xticks(())
            if y_ticks_off:
                ax.set_yticks(())
            axes.append(ax)
        except:
            pass
    if not isinstance(predictions_df_list, type(None)):
        for idx, df in enumerate(predictions_df_list):
            try:
                std_df = std_df_list[idx]
            except:
                std_df = None

            for i, series in df.iteritems():
                ax = axes[i]
                try:
                    series.plot(ax=ax, c="C" + str(idx + 1), label=legend_labels[idx + 1])
                except:
                    series.plot(ax=ax, c="C" + str(idx + 1), label="Observations")
                if not isinstance(std_df, type(None)):
                    x = series.index.values
                    y = series.values
                    std_prediction = std_df[i].values
                    ax.fill_between(
                        x,
                        y - 1.96 * std_prediction,
                        y + 1.96 * std_prediction,
                        alpha=0.2,
                        label=legend_labels[idx + 2],
                        color="C" + str(idx + 1),
                    )

    if labels:
        for i, ax in enumerate(axes):
            ax.set_title(labels[i])

    if legend:
        axes[0].legend(loc='lower left')
        
    if y_label:
        for ax in axes:
            if ax in axes[::columns]:
                ax.set_ylabel(y_label)
                
    if x_label:
        for ax in axes[-columns:]:
            ax.set_xlabel(x_label)
                
    if sharex:
        mins = []
        maxs = []
        for ax in axes:
            xmin, xmax = ax.get_xlim()
            mins.append(xmin)
            maxs.append(xmax)
        xmin = min(mins)
        xmax = max(maxs)
        for ax in axes:
            if ax in axes[-columns:]:
                ax.set_xlim(xmin,xmax)
            else:
                ax.set_xlim(xmin,xmax)
                ax.set_xticks(())
    if sharey:
        mins = []
        maxs = []
        for ax in axes:
            ymin, ymax = ax.get_ylim()
            mins.append(ymin)
            maxs.append(ymax)
#             ax.axhline(0,color='k',alpha=0.2)
        ymin = min(mins)
        ymax = max(maxs)
        for ax in axes:
            if ax in axes[::columns]:
                ax.set_ylim(ymin,ymax)
            else:
                ax.set_ylim(ymin,ymax)
                ax.set_yticks(())
    if ylim:
        for ax in axes:
            ax.set_ylim(ylim[0],ylim[1])
    
    else:
        for ax in axes:
            ax.axhline(0,color='k',alpha=0.2)
            
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, bbox_inches='tight')


def plot_timelapse(
    array, 
    figsize=(10, 10), 
    points=None, 
    titles_list=None, 
    frame_rate=200, 
    vmin=None, 
    vmax=None, 
    cmap=None,
    alpha=None,
    show=True,
    output_file=None,
):
    """
    array with shape (time, x, y)
    """
    if not vmin:
        vmin = np.nanmin(array) + 50
    if not vmax:
        vmax = np.nanmax(array) - 50


    
    fig, ax = plt.subplots(figsize=(10, 10))
#     fig.set_size_inches(10, 10, True)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    im = ax.imshow(array[0, :, :],
                   interpolation="none", 
                   alpha=alpha, 
                   vmin=vmin, vmax=vmax, 
                   cmap=cmap)
#     ax.set_facecolor("black")
    cbar = plt.colorbar(im,cax=cax,extend='both')
    cbar.set_label('Elevation difference (m)')
    if points:
        (p,) = ax.plot(points[0], 
                       points[1], 
                       marker="o", 
                       color="b", 
                       linestyle="none")
#     plt.tight_layout()
    plt.close()

    def vid_init():
        im.set_data(array[0, :, :])
        if points:
            p.set_data(points[0], points[1])

    def vid_animate(i):
        im.set_data(array[i, :, :])
        if points:
            p.set_data(points[0], points[1])
        if titles_list:
            ax.set_title(titles_list[i], size=15)
            ax.set_xticks([])
            ax.set_yticks([])

    anim = animation.FuncAnimation(fig, 
                                   vid_animate, 
                                   init_func=vid_init, 
                                   frames=array.shape[0], interval=frame_rate)
    
    FFMpegWriter = animation.writers['ffmpeg']
    writer = FFMpegWriter(fps=10, bitrate=5000)
    
    if output_file:
        anim.save(output_file, writer=writer)
    if show:
        return HTML(anim.to_html5_video())

def plot_count_std(
    count_nmad_ma_stack,
    count_vmin=1,
    count_vmax=50,
    count_cmap="gnuplot",
    std_vmin=0,
    std_vmax=20,
    std_cmap="cividis",
    points=None,
    alpha=None,
    ticks_off=False,
):

    fig, axes = plt.subplots(1, 2, figsize=(15, 10))

    ax = axes[0]
    cmap = plt.cm.get_cmap(count_cmap, count_vmax)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)

    plt.colorbar(
        ax.imshow(
            count_nmad_ma_stack[0], vmin=count_vmin, vmax=count_vmax, interpolation="none", cmap=cmap, alpha=alpha
        ),
        cax=cax,
        extend="max",
    ).set_label(label="DEM count", size=12)
    if points:
        (p,) = ax.plot(points[0], points[1], marker="o", color="b", linestyle="none")
        legend_elements = []
        legend_elements.append(Line2D([0], [0], color="b", label="Observations", marker="o", linestyle="none"))
        ax.legend(handles=legend_elements, loc="best")

    ax = axes[1]
    cmap = plt.cm.get_cmap(std_cmap)

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)

    plt.colorbar(
        ax.imshow(count_nmad_ma_stack[1], vmin=std_vmin, vmax=std_vmax, interpolation="none", alpha=alpha, cmap=cmap),
        cax=cax,
        extend="max",
    ).set_label(label="STD [m]", size=12)

    if points:
        (p,) = ax.plot(points[0], points[1], marker="o", color="b", linestyle="none")

    if ticks_off:
        for ax in axes:
            ax.set_xticks(())
            ax.set_yticks(())

def xr_plot_count_std_glacier(
    count_da,
    std_da,
    glacier_gdf=None,
    flowline_gdf=None,
    points=None,
    plot_to_glacier_extent=False,
    count_vmin=1,
    count_vmax=50,
    count_cmap="gnuplot",
    std_vmin=0,
    std_vmax=20,
    std_cmap="cividis",
    alpha=None,
    ticks_off=False,
):
    fig, axes = plt.subplots(1, 2, figsize=(15, 10))

    ax = axes[0]
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    cmap = plt.cm.get_cmap(count_cmap, count_vmax)
    norm = matplotlib.colors.Normalize(vmin=count_vmin, vmax=count_vmax)
    cbar = matplotlib.colorbar.ColorbarBase(cax, cmap=cmap, norm=norm, extend="max", alpha=alpha)
    cbar.set_label(label="DEM count", size=12)
    count_da.plot(ax=ax, cmap=cmap, add_colorbar=False, alpha=alpha, vmin=count_vmin, vmax=count_vmax)

    legend_elements = []
    if isinstance(glacier_gdf, type(gpd.GeoDataFrame())):
        legend_elements.append(Line2D([0], [0], color="k", label="Glacier Outline"))
    if isinstance(flowline_gdf, type(gpd.GeoDataFrame())):
        legend_elements.append(Line2D([0], [0], color="orange", label="Flowlines"))
    if points:
        legend_elements.append(Line2D([0], [0], color="b", label="Observations", marker="o", linestyle="none"))
    if legend_elements:
        ax.legend(handles=legend_elements, loc="best")

    ax = axes[1]
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    cmap = plt.cm.get_cmap(std_cmap)
    norm = matplotlib.colors.Normalize(vmin=std_vmin, vmax=std_vmax)
    cbar = matplotlib.colorbar.ColorbarBase(cax, cmap=cmap, norm=norm, extend="max", alpha=alpha)
    cbar.set_label(label="STD [m]", size=12)
    std_da.plot(ax=ax, cmap=cmap, add_colorbar=False, alpha=alpha, vmin=std_vmin, vmax=std_vmax)

    if ticks_off:
        for ax in axes:
            ax.set_xticks(())
            ax.set_yticks(())

    for ax in axes:
        ax.set_aspect('equal')
        ax.set_title("")
        if points:
            (p,) = ax.plot(points[0], points[1], marker="o", color="b", linestyle="none")
        if isinstance(glacier_gdf, type(gpd.GeoDataFrame())):
            glacier_gdf.plot(ax=ax, facecolor="none", legend=True)
        if isinstance(flowline_gdf, type(gpd.GeoDataFrame())):
            flowline_gdf.plot(ax=ax, color="orange", legend=True)
        if plot_to_glacier_extent:
            glacier_bounds = glacier_gdf.bounds.values[0]
            ax.set_xlim(glacier_bounds[0], glacier_bounds[2])
            ax.set_ylim(glacier_bounds[1], glacier_bounds[3])
    plt.tight_layout()

            
def xr_plot_count_nmad_before_after_coreg(
    count_da,
    nmad_da_before,
    nmad_da_after,
    glacier_gdf=None,
    flowline_gdf=None,
    points=None,
    plot_to_glacier_extent=False,
    count_vmin=1,
    count_vmax=None,
    count_cmap="gnuplot",
    nmad_vmin=0,
    nmad_vmax=None,
    nmad_cmap="cividis",
    alpha=None,
    ticks_off=False,
    outfig = None,
):
    
    if not count_vmax:
        count_vmax = np.nanpercentile(count_da.values, 98.0)

    if not nmad_vmax:
        nmad_vmax = np.nanpercentile(nmad_da_before.values, 98.0)
        
    fig, axes = plt.subplots(1, 3, figsize=(20, 10))

    # plot count
    ax = axes[0]
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    cmap = plt.cm.get_cmap(count_cmap, count_vmax)
    norm = matplotlib.colors.Normalize(vmin=count_vmin, vmax=count_vmax)
    cbar = matplotlib.colorbar.ColorbarBase(cax, cmap=cmap, norm=norm, extend="max", alpha=alpha)
    count_da.plot(ax=ax, cmap=cmap, add_colorbar=False, alpha=alpha, vmin=count_vmin, vmax=count_vmax)
    ax.set_title("DEM count", size=12)

    # add legend elements
    legend_elements = []
    if isinstance(glacier_gdf, type(gpd.GeoDataFrame())):
        legend_elements.append(Line2D([0], [0], color="k", label="Glacier Outline"))
    if isinstance(flowline_gdf, type(gpd.GeoDataFrame())):
        legend_elements.append(Line2D([0], [0], color="orange", label="Flowlines"))
    if points:
        legend_elements.append(Line2D([0], [0], color="b", label="Observations", marker="o", linestyle="none"))
    if legend_elements:
        ax.legend(handles=legend_elements, loc="best")

    # plot nmad before coreg
    ax = axes[1]
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    cmap = plt.cm.get_cmap(nmad_cmap)
    norm = matplotlib.colors.Normalize(vmin=nmad_vmin, vmax=nmad_vmax)
    cbar = matplotlib.colorbar.ColorbarBase(cax, cmap=cmap, norm=norm, extend="max", alpha=alpha)
    nmad_da_before.plot(ax=ax, cmap=cmap, add_colorbar=False, alpha=alpha, vmin=nmad_vmin, vmax=nmad_vmax)
    ax.set_title("NMAD before coreg [m]", size=12)

    # plot nmad after coreg
    ax = axes[2]
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    cmap = plt.cm.get_cmap(nmad_cmap)
    norm = matplotlib.colors.Normalize(vmin=nmad_vmin, vmax=nmad_vmax)
    cbar = matplotlib.colorbar.ColorbarBase(cax, cmap=cmap, norm=norm, extend="max", alpha=alpha)
    nmad_da_after.plot(ax=ax, cmap=cmap, add_colorbar=False, alpha=alpha, vmin=nmad_vmin, vmax=nmad_vmax)
    ax.set_title("NMAD after coreg [m]", size=12)
    
    if ticks_off:
        for ax in axes:
            ax.set_xticks(())
            ax.set_yticks(())

    for ax in axes:
        ax.set_aspect('equal')
        if points:
            (p,) = ax.plot(points[0], points[1], marker="o", color="b", linestyle="none")
        if isinstance(glacier_gdf, type(gpd.GeoDataFrame())):
            glacier_gdf.plot(ax=ax, facecolor="none", legend=True)
        if isinstance(flowline_gdf, type(gpd.GeoDataFrame())):
            flowline_gdf.plot(ax=ax, color="orange", legend=True)
        if plot_to_glacier_extent:
            glacier_bounds = glacier_gdf.bounds.values[0]
            ax.set_xlim(glacier_bounds[0], glacier_bounds[2])
            ax.set_ylim(glacier_bounds[1], glacier_bounds[3])
            
    plt.tight_layout()
    
    if outfig:
        plt.savefig(outfig, dpi=200)
        

###########  Miscellaneous
def check_if_number_even(n):
    """
    checks if int n is an even number
    """
    if (n % 2) == 0:
        return True
    else:
        return False


def make_number_even(n):
    """
    adds 1 to int n if odd number
    """
    if check_if_number_even(n):
        return n
    else:
        return n + 1


def get_row_column(n):
    """
    returns largest factor pair for int n
    makes rows the larger number
    """
    max_pair = max([(i, n / i) for i in range(1, int(n ** 0.5) + 1) if n % i == 0])
    rows = int(max(max_pair))
    columns = int(min(max_pair))

    # in case n is odd
    # check if you get a smaller pair by adding 1 to make number even
    if not check_if_number_even(n):
        n = make_number_even(n)
        max_pair = max([(i, n / i) for i in range(1, int(n ** 0.5) + 1) if n % i == 0])
        alt_rows = int(max(max_pair))
        alt_columns = int(min(max_pair))

        if (rows, columns) > (alt_rows, alt_columns):
            return (alt_rows, alt_columns)
        else:
            return (rows, columns)
    return (rows, columns)


def float_x_y_to_int_tuple(x_floats, y_floats):
    """
    Used to create labels for time series plots
    """
    x_int = [int(i) for i in x_floats]
    y_int = [int(i) for i in y_floats]
    x_y_tuples = list(zip(x_int, y_int))
    return x_y_tuples