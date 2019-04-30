#! /usr/bin/env python

import sys
import requests
import bs4
import getpass
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import os
import csv
from selenium.webdriver.firefox.options import Options

# For entering login credentials
def login_credentials():
    login_blurb = """
    Please enter login credentials. 
    JGI IMG does not support anonymous dowloads,
    Accounts are free and can be found at:
    https://img.jgi.doe.gov/cgi-bin/mer/main.cgi
    """
    print(login_blurb)
    usrname = input("Enter Username/Email:")
    pswd = getpass.getpass("Enter Password:")
    input_payload = {'login':usrname, 'password':pswd}
    return input_payload

# Find taxon page and status page
def find_status_url(taxon_ID):
    try:
        time.sleep(1)
        taxon_url = "https://img.jgi.doe.gov/cgi-bin/mer/main.cgi?section=TaxonDetail&page=taxonDetail&taxon_oid="
        taxon_page = pst.get(taxon_url+taxon_ID)
        taxontext = bs4.BeautifulSoup(taxon_page.text, "lxml")
        tst1 = taxontext.find("a", class_="genome-btn download-btn")
        return tst1.attrs['href']
    except:
        print("Error: Invalid taxon ID")

# Find download xml. 
def find_download_xml(from_status_url):
    status_page = pst.get(from_status_url)
    time.sleep(.5)
    status_html = bs4.BeautifulSoup(status_page.text, "xml")
    download_url = status_html.find('a', text='Download').attrs['href']
    download_page = pst.get(base_url+download_url)
    download_html = bs4.BeautifulSoup(download_page.text, "xml")
    try: 
        xml_path = download_html.find('a', id='downloadForm:xmlLink').attrs['href'][2:]
        time.sleep(.5)
        xml_page = pst.get(base_url+'/portal'+xml_path)
        xml_text = bs4.BeautifulSoup(xml_page.text, 'xml')
        file_details = {}
        file_paths = {}
        for file_tags in xml_text.find_all('file'):
            file_details.update({file_tags.attrs['filename']:file_tags.attrs['size']})
            file_paths.update({file_tags.attrs['filename']:file_tags.attrs['url']})
        return file_details, file_paths, False
    except:
        return False, False, (base_url+download_url)

# Agree to terms of service using headless browser
def agree_to_terms(terms_page):
    usage_blurb = '''
    Do you agree to JGI IMG data-usage policy:
    https://img.jgi.doe.gov/cgi-bin/mer/main.cgi?section=Help&page=policypage\n
    '''
    print(usage_blurb)
    usage_confirmation = input("""
    'y' for yes
    'n' for no
    """)
    if usage_confirmation == 'y':
        next
    elif usage_confirmation == 'n':
        sys.exit("Exiting program")
    else:
        sys.exit("Invalid entry.")
    service_blurb = """
    Confirming data usage policy
    """
    print(service_blurb)
    options = Options()
    options.headless = True
    browser = webdriver.Firefox(options=options)
    url = "https://img.jgi.doe.gov/cgi-bin/mer/main.cgi"
    browser.get(url) 
    time.sleep(1)
    loginButton=browser.find_element_by_class_name("smdefbutton")
    loginButton.click()
    time.sleep(1)
    uN=browser.find_element_by_id("login")
    uN.send_keys(payload['login'])
    uS=browser.find_element_by_id("password")
    uS.send_keys(payload['password'])
    lButton=browser.find_element_by_name("commit")
    lButton.click()
    time.sleep(1)
    browser.get(terms_page)
    box = browser.find_element_by_id("acceptedCheckBox")
    box.click()
    AgreeButton = browser.find_element_by_name("data_usage_policy:okButton")
    time.sleep(1)
    AgreeButton.click()
    browser.close()

def construct_file_list():
    file_names = []
    file_name = []
    print("Input file name or 'd' for done\n")
    while file_name != "d":
        file_name = input("File name:")
        try:
            file_paths[file_name]
            file_names.append(file_name)
        except KeyError:
            if file_name == 'd':
                print("End of list\n")
            else:
                print("Error: Not a valid file name\n")
        except:
            next
    return file_names

def confirm_download():
    confirmation = 'n'
    while confirmation == 'n':
        file_names = []
        file_names = construct_file_list()
        print(spacer+"\nFiles to download:\n")
        print(file_names)
        confirmation = input("""
        Proceed with download?
        'y' for yes,
        'n' for no (reconstruct list),
        's' to save file names and paths,
        'q' for quit
        """)
    return confirmation, file_names

def download_files(input_file):
    file_to_write = pst.get(base_url+file_paths[input_file])
    time.sleep(.5)
    open(taxon_number+"_"+input_file, 'wb').write(file_to_write.content)

spacer = """
--------------------------------
--------------------------------
"""

#Creating session and signing on
payload=login_credentials()
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
base_url = 'https://genome.jgi.doe.gov'
signon_url = 'https://signon-old.jgi.doe.gov/signon/create'
pst = requests.Session()
pst.headers.update(headers)
pst.post(signon_url, data=payload)

taxon_number = input("Enter in genome ID number:") 

status_url = find_status_url(taxon_number)

file_details, file_paths, terms_path = find_download_xml(status_url)

if terms_path != False:
    try:
        agree_to_terms(terms_path)
        file_details, file_paths, terms_path = find_download_xml(status_url)
    except:
        sys.exit("Could not find file for %s \nPath: %s"%(taxon_number, terms_path))
else:
    next

xml_blurb = '''
The following files are availablee 
for Genome ID %s
''' %taxon_number

print(xml_blurb)
for item in file_details:
    print(item+"........."+file_details[item])

confirmation, file_names = confirm_download()

if confirmation == 'y':
    for input_file in file_names:
        print("Downloading:%s"%input_file)
        download_files(input_file)
        print("Download Complete")
elif confirmation == 's':
    path_save = open((taxon_number+"_file_paths.txt"), 'w')
    for input_file in file_names:
        path_save.write(input_file+"\n"+file_paths[input_file])  
elif confirmation == 'q':
    sys.exit("exiting program")
else:
    print("invalid entry, try again")	
