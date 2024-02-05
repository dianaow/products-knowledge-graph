# Imports specifics using Firefox web driver.
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options

# Imports for general selenium functionality.
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import os
import bs4
import time
import json
import re

def clean(string):
    # Remove Chinese characters, emojis, unicode, and special characters
    cleaned_string = re.sub('[^\w\s]', '', string)
    #cleaned_string = re.sub('[\u4e00-\u9fff]', '', cleaned_string)
    cleaned_string = re.sub(r'[\U0001D401-\U0001D419]', '', cleaned_string)
    cleaned_string = ''.join(char for char in cleaned_string if char.isascii())
    return cleaned_string.strip()

def extract_quantity_unit(text):
    match = re.search(r'(\d+(\.\d+)?)\s*(ml|g)', text)
    if match:
        quantity = match.group(1)
        unit = match.group(3)
        return float(quantity), unit
    else:
        return None, None
    
def product_is_multiple_items(text):
    special_substrings = ["bundle", "set", "+", "trial"]
    return any(substring in text.lower() for substring in special_substrings)


def get_data(file_path):
    """
    This function carries out the 'product urls extraction' pipeline, which is to extract url strings from a locally saved HTML page,
    then enters each url with headless selenium webdriver and extracts the HTML content within each url
    """
    urls = extract_urls(file_path)
    for url in urls:
        save_product_pages(url)

def extract_urls(file_path):
    
    page_contents = read_webpage_contents(file_path)

    soup = bs4.BeautifulSoup(page_contents, "html.parser")

    # Finds all occurrences of the specified <li> tag representing a product item tile
    all_a_tags = soup.find_all('li', class_='shopee-search-item-result__item')  

    # Extract the URLs from the 'href' attributes
    urls = ["https://shopee.sg" + a_tag.find('a')['href'] for a_tag in all_a_tags if a_tag.find('a')]

    return urls

def save_product_pages(url):
    """
    This function extracts the HTML content of a webpage with selenium webdriver
    """  
    # Creates an option for how the browser behaves. 
    opts = Options()
    opts.add_argument("--headless")

    # Creates firefox webdriver.
    driver = Firefox(options=opts)

    # Navigate to the link provided.
    driver.get(url)

    time.sleep(1)
    
    webpage_save_name = "productpages/" + clean(url).replace("https://shopee.sg", "").replace(" ", "_") + ".html"
    save_webpage(driver, webpage_save_name)
    print("Web page saved as {}".format(webpage_save_name))

    driver.quit()

def read_webpage_contents(file_path):
    """
    This function reads the HTML content of a webpage from a file
    """  
    with open(file_path, "r", encoding = "utf-8") as f:
        contents = f.read()
        return contents
    
def save_webpage(driver, file_name):
    """
    This function saves the HTML content of a webpage into a file
    """  
    html_contents = driver.page_source
    with open(file_name, "w", encoding = "utf8") as f:
        f.write(html_contents)

def get_kg():
    """
    This function carries out the 'product details extraction' pipeline, 
    which is to extract content within each locally saved HTML page of each product,
    then constructs a list of entities
    """
    current_id = 1
    
    # Retrieve all file names in the folder and sort them in alphabetical order
    folder_path = 'productpages'
    file_names = [folder_path + '/' + f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    file_names.sort()
    
    nodesAll = []
    for path in file_names:
        #try:
        if not product_is_multiple_items(path):
            nodes = extract_product_details(path, current_id)
            nodesAll.extend(nodes)
            current_id += 1
            print('Success in extracting product details from ' + path)
        #except:
            #print('Error in extracting product details from  ' + path)
            #continue
            
    # Save the Python object as a JSON file
    with open('kg.json', 'w') as json_file:
        json.dump(nodesAll, json_file)

    return nodesAll
    
def extract_product_details(file_path, current_id):
    """
    This function scrapes information from HTML content based on specified tags or classes.
    """
    page_contents = read_webpage_contents(file_path)

    item_info = bs4.BeautifulSoup(page_contents, "html.parser")

    nodes = []
    
    #title
    title_container = item_info.find(attrs = {"class": "WBVL_7"})
    product_title = title_container.text.strip() if title_container else ""
    cleaned_product_title = clean(product_title)

    #description
    if item_info.find_all('p', class_='QN2lPu'):
        product_highlights = [clean(li.text) for li in item_info.find_all('p', class_='QN2lPu') if (li.text != '' or li.text != ' ' or li.text != '\n')]
        #print(product_highlights)
        cleaned_product_highlights = []
        for index, p in enumerate(product_highlights):
            p0 = product_highlights[index-1] if(index > 0) else ""
            if('key ingredients' == p0.lower()):
                cleaned_product_highlights.append(p)
            elif('how to use' in p.lower() or 'ingredients' in p.lower() or 'expiration date' in p.lower() or 'expiry' in p.lower() or 'months' in p.lower() or 'shipped' in p.lower()):
                cleaned_product_highlights.append("")
            elif('how to use' in p0.lower() or 'ingredients' in p0.lower()):
                cleaned_product_highlights.append("")
            else:
                cleaned_product_highlights.append(p)
        cleaned_product_highlights = [item for item in cleaned_product_highlights if item]
        #print(cleaned_product_highlights)
    else:
        meta_description = item_info.find('meta', attrs={'name': 'description'})
        cleaned_product_highlights = [clean(meta_description['content'])]

    #price
    price_container = item_info.find(attrs = {"class": "G27FPf"})
    product_price = price_container.text.strip() if price_container else ""
    cleaned_price_string = re.sub(r'\$', '', product_price) # Remove dollar signs
    prices = [float(match) for match in re.findall(r'\d+\.\d+', cleaned_price_string)]
    min_price =  min(prices) if len(prices) > 0 else 0 # Extract minimum numerical value

    #details
    details = item_info.find_all('div', class_='Tq1nbH')
    specification_keys = [li.find('label').text.strip() for li in details]
    specification_values = [li.find('div').text.strip() if li.find('div') else li.find('a').text.strip() for li in details]

    #image url
    img_divs = item_info.find('div', class_='airUhU')
    img_src = img_divs.find_all('div')[1].find('img', class_='IMAW1w')['src'] if img_divs else ""
    
    #category
    cat_container = item_info.find('div', class_='idLK2l')
    if cat_container:
        cat_chain = cat_container.find_all('a')
        category = cat_chain[-1].text.strip() if cat_chain else ""
    else :
        category = ""

    #volume      
    vol, unit = extract_quantity_unit(cleaned_product_title)
    if((vol != None and unit != None) and (vol != "" or vol != " ")):
        volume = str(vol) + str(unit)
    else:
        volume = 0

    nodes.append({
        "product_id": current_id,
        "product_url": img_src,
        "product": category,
        "title": cleaned_product_title,
        "price":  min_price,
        "volume": volume,
        "description": ", ".join(cleaned_product_highlights)
    })
    
    for index, key in enumerate(specification_keys):
        value = specification_values[index]        
        if key == "Brand":
            nodes.append({
                "product_id": current_id,
                "relationship": "hasBrand",
                "entity_type": "brand",
                "entity_value": value, 
            })
        if (key == "Ingredient Preference" or key == "Ingredient"):
            ingredients = value.split(',') 
            for ingredient in ingredients:
                nodes.append({
                    "product_id": current_id,
                    "relationship": "hasIngredient",
                    "entity_type": "ingredient",
                    "entity_value": ingredient.strip()
            }) 
        if (key == 'Skin Care Benefits' or key == 'Benefits'):  
            points = value.split(',') 
            for point in points:     
                nodes.append({
                    "product_id": current_id,
                    "relationship": "hasBenefits",
                    "entity_type": "benefits",
                    "entity_value": point.strip()
                }) 
        if key == 'Skin Type':        
            nodes.append({
                "product_id": current_id,
                "relationship": "hasSkinType",
                "entity_type": "skintype",
                "entity_value": "all skin type" if "all skin type" in value.lower() else value
            })
        if (key == "Product Form" or key == 'Formulation'):
            nodes.append({
                "product_id": current_id,
                "relationship": "hasForm",
                "entity_type": "form",
                "entity_value": value
            })  
        # if (key == 'Volume' or key == 'Weight'):
        #     nodes.append({
        #         "product_id": current_id,
        #         "relationship": "hasVolume",
        #         "entity_type": "volume",
        #         "entity_value": value
        #     })

    return nodes


folder_path = 'productoverviewpages'
file_names = [folder_path + '/' + f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
file_names.sort()

nodesAll = []
for path in file_names:
    print(path)
    get_data(path)

get_kg()