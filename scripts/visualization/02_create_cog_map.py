import gtsa

cog_url = 'http://conus-historicals.s3.amazonaws.com/baker/orthos/ortho_1947-09-14_EE_reproj_COG.tif'

s3_bucket_name = 'conus-historicals'
folder_path = 'baker/orthos'

m = gtsa.plotting.plot_cog(cog_url   = cog_url,
                       zoom_start = 11)
m

m.save('mount_baker_1947-09-14.html')


cog_urls = gtsa.io.parse_urls_from_S3_bucket(s3_bucket_name,
                                             folder = folder_path,
                                             aws_server_url = 's3.amazonaws.com')

dates = gtsa.io.parse_timestamps(cog_urls,
                                 date_string_pattern='....-..-..')


map_center_lon = -121.8144
map_center_lat = 48.7767

m = gtsa.plotting.plot_cogs(cog_urls,
                        dates,
                        map_center_lon      = map_center_lon,
                        map_center_lat      = map_center_lat,
                        zoom_start          = 11,
                        overview_cog_index  = 0,
                        print_info          = True,
                       )
m.save('mount_baker_all.html')


sites = ['baker','scg']
folders = [gtsa.io.Path(s, 'orthos').as_posix() for s in sites]

site_marker_names = ['Mount Baker', 'South Cascade']
site_marker_coords = [(48.7767, -121.8144), (48.3717, -121.0660)]
cog_overview_indices = [0,0]

map_center = (48.5485, -121.4045)

payload = {}
payload['map_center'] = map_center
payload['sites'] = {}

for i, site in enumerate(sites):
    payload['sites'][site] = {'marker_name':site_marker_names[i],
                              'marker_coords': site_marker_coords[i],
                     'overview_index': cog_overview_indices[i],
                     'cog_urls': gtsa.io.parse_urls_from_S3_bucket(s3_bucket_name,
                                                                   folder = folders[i],
                                                                   aws_server_url = 's3.amazonaws.com'),
                             }
    payload['sites'][site]['dates'] = gtsa.io.parse_timestamps(payload['sites'][site]['cog_urls'])
    payload['sites'][site]['cog_names'] = [site +'_'+ x for x in payload['sites'][site]['dates']]

m = gtsa.plotting.plot_cogs_sites(payload,
                                  zoom_start           = 9,
                                  print_info          = True,
                             )

m.save('mount_baker-south_cascade.html')