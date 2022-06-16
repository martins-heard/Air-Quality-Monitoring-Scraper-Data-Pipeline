import os
import json
import time
import uuid
import boto3
import numpy
import psycopg2
import inquirer
import pandas as pd
import urllib.request
from selenium import webdriver
from collections import defaultdict
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AURNScraper:
    """ 
    This class will navigate the website to collect air quality monitoring site information 
    from an individual site or all sites. For a single site the information will be stored as 
    a dictionary and site images can be downloaded. For all sites the information will be saved 
    as a .pkl file. From this database sites can be selected by distance from user specified 
    coordinates to retrieve the air quality monitoring data for a specified year. Below is a 
    step by step example.

    Example
    -------
    Example 1 - Retrieve site information for a single site: 
        AURN = AURNScraper()
        AURN.single_site_info(site_name='Port Talbot Margam', download_imgs=True)

    Example 2 - Retrieve site information for multiple sites and download files:
        Step 1 - Update or create the 'All_Sites_Outputs.pkl' to obtain information for all sites in the AURN network. 
            AURN = AURNScraper()
            AURN.all_sites_info()
        Step 2 - Find sites within specified distance from specified coordinates:
            sites_for_download = AURN.find_sites_by_distance(X=394366, Y=807397, 
                                distance_m=50000) 
        Step 3 - Download monitoring data for chosen sites:
            AURN.download_monitoring_data(sites_for_download)

    Parameters
    ----------
    url : str
        URL address to the AURN website 
    """
    def __init__(self, url: str ='https://uk-air.defra.gov.uk/interactive-map'):
        self.url = url
        current_dir = os.getcwd()
        self.new_dir = os.path.join(current_dir, r'monitoring_files')
        if not os.path.exists(self.new_dir):
            os.makedirs(self.new_dir)
        chromeOptions = webdriver.ChromeOptions()
        prefs = {"download.default_directory" : self.new_dir}
        chromeOptions.add_experimental_option("prefs",prefs)
        chromeOptions.add_argument('--headless')
        chromeOptions.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome(options=chromeOptions)
        self.driver.get(url)

# accept cookies
    def _accept_cookies(self):
        """ 
        This is a private method which accepts cookies when the webpage is initiated.
        """
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'global-cookie-message')))
        cookie_window = self.driver.find_element_by_xpath("//div[@id='global-cookie-message']")
        cookie_window.find_element_by_xpath(".//button[@name='submit']").click()

# find specified site
    def single_site_info(self, site_name: str, download_imgs:bool = False) -> dict:
        """ 
        Returns site information (Environment type, X and Y Coordinates, Location and URL link) 
        for a specified single site.

        Parameters
        ----------
        site_name : str
            site name as per the AURN website
        
        download_imgs : bool
            Choose if you want to download pictures of this site. If set to True, images will be 
            downloaded to current directory. The default value is False.

        Returns
        -------
        Dictionary
            {'Site': f'{site_name}', 'Site Info: ': {'Env_Type': '[env type]', 'X_and_Y': '[coordinates]', 
            'Location': '[location]', 'Web Link': f'{site_info_link}'}}
        """
        site_info_dict = {'Name': [], 'Environment Type': [], 'Coordinates':[], 'Address':[], 'Web Link': [], 'Image Names':[]}
        self._accept_cookies()
        api_df = self._dataframe_API()
        my_site = api_df.loc[api_df['site_name'] == site_name, 'site info link'].iloc[0]
        site_info = self._retrieve_site_info(site_name, my_site, download_imgs)
        site_info_dict['Name'].append(site_name)
        site_info_dict['Environment Type'].append(site_info[0])
        site_info_dict['Coordinates'].append(site_info[1])
        site_info_dict['Address'].append(site_info[2])
        site_info_dict['Web Link'].append(site_info[3])
        site_info_dict['Image Names'].append(self._check_for_image_download(site_name))
        print(site_info_dict)
        return site_info_dict
    
    def _retrieve_site_info(self, site_name, this_site, retrieve_img=False):
        """ 
        This is a private method which collates the site information for each site.
        """

        self.driver.get(this_site)
        #retrieve data in dictionary: Site Name, Location, Environment Type, eastings, northings, pollutants measured?
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'tab_info')))
        tab_info = self.driver.find_element_by_xpath("//div[@id='tab_info']")
        my_tags = tab_info.find_elements_by_tag_name('p')
        for info in my_tags:
            if 'Environment Type' in info.text:
                env_type = info.text.split(': ')[1]
            elif 'Easting/Northing' in info.text:
                try:
                    X_co = int(info.text.split(': ')[1].split(', ')[0])
                    Y_co = int(info.text.split(': ')[1].split(', ')[1])
                    site_xy = [X_co, Y_co]
                except:
                    site_xy = info.text.split(': ')[1]
            elif 'Site Address' in info.text:
                site_address = info.text.split(': ')[1]
        if retrieve_img == True:
            self._retrieve_images(site_name)
        return [env_type, site_xy, site_address, this_site]
    
    def _retrieve_images(self, site_name, folder_name='image_files'):
        """
        This is a private method which downloads images for a single site if the
        user specifies to do this.
        """
        current_dir = os.getcwd()
        new_dir = os.path.join(current_dir, r'{f}'.format(f = folder_name))
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        site_photos = self.driver.find_element_by_xpath("//div[@class='carousel-inner']")
        all_photos = site_photos.find_elements_by_xpath("./div[@class='item']/*")
        filenumber = 0
        for link in all_photos:
            filename = f"{site_name}{filenumber}"
            if os.path.exists(f'{new_dir}/{filename}.jpg')==True: # Do not download if image already exists
                print(f"{filename} already exists. Image not replaced.")
            else:
                src = link.get_attribute('src')
                urllib.request.urlretrieve(src,f"{new_dir}/{filename}.jpg")
                filenumber += 1
        print ("Number of images downloaded: ", filenumber)
        return "Number of images downloaded: ", filenumber

    def all_sites_info(self) -> dict:
        """ 
        Returns site information (Environment type, X and Y Coordinates, Location and URL link) 
        for all sites on the AURN website.

        Parameters
        ----------
        N/A

        Returns
        -------
        Dictionary
            {'Site': f'{site_name}', 'Site Info: ': {'Env_Type': '[env type]', 'X_and_Y': '[coordinates]', 
            'Location': '[location]', 'Web Link': f'{site_info_link}'}}
            
            All_Sites_Output.pkl: Output file of all sites
        """
        try: # If All_Sites_Ouput.pkl already exists ask user if they want to overwrite it
            if os.path.isfile('All_Sites_Outputs.pkl') == True:
                question = {inquirer.Confirm('confirmed',
                    message="It looks like an output file with all the sites in has already been created. Do you want to overwrite this?",
                    default=True),}
                ans = inquirer.prompt(question)
            if ans['confirmed']==False:
                print("Ok. Method has ended.")
                return
        except: # Above question won't work unless file being called is a .py file
            pass
        self._accept_cookies()
        site_info_dict = {'UUID': [],'Name': [], 'Environment Type': [], 'Coordinates':[], 'Address':[], 'Web Link': [], 'Image Names':[]}
        api_df = self._dataframe_API()
        #print(api_df.head())
        for i in range(len(api_df)):
            try:
                name_of = api_df['site_name'].iloc[i]
                # print("string", name_of)
                site_info_dict['UUID'].append(uuid.uuid4())
                site_info_dict['Name'].append(name_of)
                api_site_link = api_df['site info link'].iloc[i]
                # print(api_site_link)
                site_info = self._retrieve_site_info(name_of, api_site_link)
                site_info_dict['Environment Type'].append(site_info[0])
                site_info_dict['Coordinates'].append(site_info[1])
                site_info_dict['Address'].append(site_info[2])
                site_info_dict['Web Link'].append(site_info[3])
                site_info_dict['Image Names'].append(self._check_for_image_download(name_of))
                # print(site_info_dict)
            except IndexError:
                print("Index Error", i)
                print (site_info_dict)
                pass
            except Exception as E:
                print("Error",E , i)
                pass
            except:
                print("Error", i)
                pass
            finally:
                #self.pad_dict_list(site_info_dict)
                site_info_df = pd.DataFrame.from_dict(site_info_dict,orient='index')
                site_info_df = site_info_df.transpose()
        self.driver.quit()    
        #site_info_df = pd.DataFrame.from_dict(site_info_dict)
        site_info_df.to_pickle("All_Sites_Outputs.pkl")
        return site_info_df
        
    # find all sites within x distance
    def find_sites_by_distance(self, X: float, Y: float, distance_m: int) -> pd.DataFrame:
        """ 
        This method will find all the sites within a specified distance of specified
        X and Y coordinates.

        Example
        -------
        sites_for_download = AURN.find_sites_by_distance(X=394366, Y=807397, distance_m=50000)  

        Parameters
        ----------
        X : float
            The X axis coordinate of your specified point.

        Y : float
            The Y axis coordinate of your specified point.

        distance_m : int
            The distance from your specified point from which site information will be obtained. 

        Returns
        -------
        df : pd.DataFrame
            A dataframe of all the sites within the specified distance of the specified 
            coordinates.
        """
        try:
            all_sites_file = pd.read_pickle(r'All_Sites_Outputs.pkl')
        except:
            print("All_Sites_Ouputs.pkl not in current directory. Move this file to current directory or run 'all_sites_info' method to retrieve data")
            return
        if 'X' not in all_sites_file and 'Y' not in all_sites_file:
            all_sites_file.insert(2, 'X', 0)
            all_sites_file.insert(3, 'Y', 0)
            all_sites_file.insert(5, 'distance from point', 0)

        all_sites_file['X'] = all_sites_file['Coordinates'].str[0]
        all_sites_file['Y'] = all_sites_file['Coordinates'].str[1]
        ans = ((((X-all_sites_file['X'])**2)+((Y-all_sites_file['Y'])**2))**0.5)
        all_sites_file['distance from point'] = ans
        df = all_sites_file[all_sites_file['distance from point']< distance_m]
        print(f"Below are all sites within {distance_m / 1000}km of specified points")
        print(df)
        return df
    
    #download data
    def download_monitoring_data(self, dataframe: pd.DataFrame, year: int):
        """ 
        This will download All Hourly Pollutant Data for a specified year 
        from the AURN website for all sites in a specified dataframe.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Dataframe of sites you wish to download data for. Format of this parameter
            should match the output of the 'find_sites_by_distance' method.

        year : int
            The year you wish to download data for. 

        Returns
        -------
        download_report : dict
            Dictionary of how many files were successfully downloaded and which (if any)
            sites were unsuccessfully downloaded.
            
        Downloaded Data : .csv files
            The downloaded data will appear in the current directory as individual csv 
            files.
        """
        self._accept_cookies()
        download_report = {'Successful Downloads Count': 0, 'Unsuccessful Download list': []}
        for index, row in dataframe.iterrows():
            self.driver.get(row['Web Link'])
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@class='scrtabs-tab-scroll-arrow scrtabs-tab-scroll-arrow-left']")))
            path = self.driver.find_element_by_xpath("//ul[@class='nav nav-tabs nav-tabs-responsive']")
            networks = path.find_element_by_xpath("./li[@id='li_tab_networks']")
            tag_a = networks.find_element_by_tag_name("a")
            self.driver.execute_script("arguments[0].click();", tag_a)
            tab_networks = path.find_element_by_xpath("//div[@id='tab_networks']")
            formatted_data = tab_networks.find_element_by_link_text('Pre-Formatted Data Files')
            self.driver.execute_script("arguments[0].click();", formatted_data)
            table = self.driver.find_elements_by_xpath("//div[@class='table-responsive']/*")
            element = table[0]
            all_years = element.find_elements_by_tag_name('a')
            downloads_before_loop = download_report['Successful Downloads Count']
            for AURN_year, loop_no in zip(all_years, range(len(all_years))):
                if AURN_year.text == str(year):
                    linkname = AURN_year.get_attribute('href')
                    split_list = linkname.split('/')
                    name = split_list[len(split_list)-1].split('?')[0]
                    if os.path.exists(f'{self.new_dir}/{name}') == True:
                        print(f'{name} monitoring file already exists. File not replaced.')
                    else:
                        self.driver.execute_script("arguments[0].click();", AURN_year)
                        download_report['Successful Downloads Count'] += 1
                if (loop_no+1) == len(all_years):
                    if downloads_before_loop == download_report['Successful Downloads Count']:
                        download_report['Unsuccessful Download list'].append(row['Name'])
        print(download_report)
        return download_report
    
    # convert pkl records to json file
    def pkl_to_json(self, folder_name : str='json_files'):
        ''' 
        This will convert individual records in the All_Sites_Outputs.pkl file into json records
        and save these in the "json files" directory or create this directory if it doesn't 
        already exist.

        Parameters
        ----------
        folder_name : str
            Name of folder you wish to save json files in. The default is "json files"
        
        Returns
        -------
        json files : .json
            Individual records from All_Sites_Outputs.pkl as .json.       
        '''
        current_dir = os.getcwd()
        new_dir = os.path.join(current_dir, r'{f}'.format(f = folder_name))
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        
        output_file = pd.read_pickle(r'All_Sites_Outputs.pkl')
        for index, row in output_file.iterrows():
            site_name = output_file.iloc[index]['Name']
            output_file.iloc[index].to_json(r'{nd}/{si}.json'.format(nd = new_dir, si = site_name))
        print(f'individual record of output file have been converted to json files in {new_dir}')
    
    def upload_directory_to_s3(self, folder : str, bucketname : str):
        ''' 
        This method will upload the contents of your chosen folder to an AWS S3 bucket.
        Chosen folder is likely to be either "image_files", "json_files", "monitoring_files".

        Parameters
        ----------
        folder : str
            The name of the folder from which you wish to upload the contents to AWS S3 bucket.

        Returns
        -------
        Folder contents inputted to AWS S3 bucket. 

        '''
        current_dir = os.getcwd()
        path = os.path.join(current_dir,folder)
        s3_client = boto3.client('s3')
        for root,dirs,files in os.walk(path):
            for file in files:
                s3_client.upload_file(os.path.join(root,file),bucketname,file)
        return
    
    def _check_for_image_download(self, site_name : str) -> list:
        '''
        This is a private method which checks if images have already been downloaded
        for a site which is then appended to the outputs table or dictionary.
        '''
        current_dir = os.getcwd()
        image_dir = os.path.join(current_dir, r'{f}'.format(f = 'image_files'))    
        contin = True
        val = 0
        image_name_list = []
        while contin == True:
            if os.path.exists(f'{image_dir}/{site_name}{val}.jpg'):
                image_name_list.append(f'{site_name}{val}')
                val += 1
            else:
                contin = False
        if len(image_name_list) == 0:
            image_name_list.append("No Downloaded Images")
        return image_name_list

    def _check_site_in_RDS(self, site_name):
        '''
        This is a private method that checks if the information for a site is 
        already stored on RDS '''
        connection = psycopg2.connect(user='postgres',
                                password='mysecretpassword',
                                host='airqualityscraper.clbqzprnzcak.eu-west-2.rds.amazonaws.com',
                                port=5432,
                                # server='scraper_data',
                                database='postgres')
        cursor = connection.cursor()
        postgreSQL_select_Query = f"""Select "Name" FROM aq_data WHERE "Name" IN ('{site_name}');"""
        cursor.execute(postgreSQL_select_Query)
        my_val = cursor.fetchall()
        if site_name in my_val[0]:
            return True
        else:
            return False
    
    def _dataframe_API(self,API_loc="AURN_API.json"):
        '''
        This is a private method that converts the json API with the
        link to all AURN sites into a usable dataframe.
        '''
        json_file_path = API_loc
        with open(json_file_path, 'r') as j:
            contents = json.loads(j.read())
        my_list = []
        for i in contents.keys():
            #print(f"key: {i}", len(contents[i]))
            df = pd.DataFrame(contents[i])
            #df.replace("", numpy.NaN, inplace=True)
            my_list.append(df)
        df = pd.concat(my_list, axis=0)
        df.drop(columns=['exception','parameter_ids',
                'network_name', 'network_id','site_status',
                'overall_index','environment_id','country_id']
                ,axis=0, inplace=True)
        site_info_link = 'https://uk-air.defra.gov.uk/networks/site-info?uka_id='
        df['site info link'] = site_info_link + df['uka_id']
        df = df[['site_name', 'site info link']]
        return df
