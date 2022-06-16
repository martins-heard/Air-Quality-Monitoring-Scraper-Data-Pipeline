FROM python:3.8
COPY . .
RUN pip install -r requirements.txt

#install chrome
RUN curl https://intoli.com/install-google-chrome.sh | bash
RUN sudo mv /usr/bin/google-chrome-stable /usr/bin/google-chrome

# install chromedriver
RUN wget https://chromedriver.storage.googleapis.com/98.0.4758.102/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip.1
RUN sudo mv chromedriver /usr/bin/chromedriver

RUN python3 --version
RUN pip3 --version

CMD ["python", "Airquality_scraper.py",__main__.py]
EXPOSE 4444