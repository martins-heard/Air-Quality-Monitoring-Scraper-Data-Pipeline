from setuptools import setup
from setuptools import find_packages

setup(
    name='Aurn_Air_Quality_Monitoring_Data_Scraper',
    version='0.0.1', 
    description='''Data scraping class for retrieving site information for all the monitoring sites
                 on the AURN website. It can also retrieve monitoring data for a specified year for
                 a multiple locations. and retrieve site information and images of a site for single
                 locations.''',
    url='https://github.com/martins-heard/Web-Scraping-Data-Pipeline.git', # Link to gitbub repo
    author='Martin Sheard',
    license='MIT',
    packages=find_packages(), # Only one main module but does contain tests
    install_requires=['selenium', 'time', 'collections', 'urllib','pandas', 'os', 'inquirer'], # All external libraries
)