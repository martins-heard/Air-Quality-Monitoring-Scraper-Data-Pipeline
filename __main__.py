
from Airquality_scraper import AURNScraper

AURN = AURNScraper()
'''Retrieve site information for a single site'''
# AURN.single_site_info('Sheffield Barnsley Road',download_imgs=True)
''' Retrieve site information for multiple sites'''
# AURN.all_sites_info()
'''Find sites within a distance of specified coordinates'''
# my_sites = AURN.find_sites_by_distance(X=436276,Y=389930,distance_m=10000)
'''Download monitoring data CSV files for specified sites and year'''
# AURN.download_monitoring_data(my_sites,2019)
'''Upload specified folder to AWS S3 storage'''
# AURN.upload_directory_to_s3(folder='monitoring_files',bucket_name='your_bucket')

# AURN.pkl_to_json()
# AURN.upload_directory_to_s3('json_files')

# help(AURN)
# AURN._dataframe_API()