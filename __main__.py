
from Airquality_scraper import AURNScraper

AURN = AURNScraper()

# AURN.single_site_info('Sheffield Barnsley Road',download_imgs=True)

# AURN.all_sites_info()

my_sites = AURN.find_sites_by_distance(436276,389930,10000)
AURN.download_monitoring_data(my_sites,2019)
# AURN.upload_directory_to_s3('monitoring_files')

# AURN.pkl_to_json()
# AURN.upload_directory_to_s3('json_files')

# help(AURN)
# AURN._dataframe_API()