# Web-Scraping-Data-Pipeline

## Introduction
This pipeline retrieves air quality monitoring site information from the Automatic Urban and Rural Network (AURN) 
Defra website. The site information such as Site ID, X and Y Coordinates, Environment Type and Web Link are collected
and stored in a dataframe or pickle file (All_Sites_Outputs.pkl) and can be used to download the air quality monitoring
data in a .csv format for a specific year. 
This class has the capacity to retrieve site information for one site, or all sites in the network. It can then download
the csv files from sites within a radius of a user defined X and Y coordinate, for a user defined year.
The tool also has the capacity to upload files to AWS S3 storage. 

 ## How to Use
 The main script is in the Airquality_scraper.py file but the user can call the desired methods using the __main__.py
 file. The method uses the 'AURN_API.json' file to retrieve site information so make sure this is saved with the 
 Airquality_scraper.py and __main__.py file. The __main__.py file has all the methods commented out and the user can uncomment
 the ones they wish to use.

 ## Example
 ### Example 1 - Retrieve site information for a single site: 
    AURN = AURNScraper()
    AURN.single_site_info(site_name='Port Talbot Margam', download_imgs=True)

 ### Example 2 - Retrieve site information for multiple sites and download files:
    Step 1 - Update or create the 'All_Sites_Outputs.pkl' to obtain information for all sites in the AURN network. 
        AURN = AURNScraper()
        AURN.all_sites_info()
    Step 2 - Find sites within specified distance from specified coordinates:
        sites_for_download = AURN.find_sites_by_distance(X=394366, Y=807397, 
                            distance_m=50000) 
    Step 3 - Download monitoring data for chosen sites:
        AURN.download_monitoring_data(sites_for_download)
    
    A folder called 'monitoring_files' will then be saved in your directory. 

## Upload to AWS S3
Use the upload_directory_to_s3() method and enter the folder name you wish to upload to S3 e.g. 'monitoring_files' or
'image_files'

