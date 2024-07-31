import os
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse, parse_qs, urljoin

def extract_data(page_source, product_list):
    # Parse the page source with BeautifulSoup
    page = BeautifulSoup(page_source, 'html.parser')

    # Extract the desired information from the parsed HTML
    products = page.find_all('a', {'data-view-id': 'product_list_item'})
    print(f'Found {len(products)} products on the page.')

    for product in products:
        try:
            product_url = urljoin('https://tiki.vn', product.get('href'))
            # print(f'Product URL: {product_url}')
            product_img = product.find('img').get('srcset').split(' 1x,')[0].strip()
            # print(f'Product image: {product_img}')

            # Find all badges of a product
            badges = []
            if product.find('img', {'srcset': 'https://salt.tikicdn.com/ts/upload/0f/59/82/795de6da98a5ac81ce46fb5078b65870.png'}):
                badges.append('Top deal')
            if product.find('img', {'srcset': 'https://salt.tikicdn.com/ts/tka/69/cf/22/1be823299ae34c7ddcd922e73abd4909.png'}):
                badges.append('Authentic')
            print(f'Product available badges: {badges}')

            product_price = product.find('div', {'class': 'price-discount__price'}).text
            print(f'Product price: {product_price}')

            product_brand = product.find('div', {'class': 'style__AboveProductNameStyled-sc-m30gte-0 hjPFIz above-product-name-info'}).text
            print(f'Product brand: {product_brand}')

            product_name = product.find('h3', {'class': 'style__NameStyled-sc-139nb47-8 ibOlar'}).text
            print(f'Product name: {product_name}')

            product_sold_count = product.find('span', {'class': 'quantity has-border'}).text.split('Đã bán ')[1]
            print(f'Product sold count: {product_sold_count}')

            rating_div = product.find('div', {'class': 'styles__StyledStars-sc-1rfnefa-0 kXehhl'}).find('div', style=lambda value: value and 'width' in value)
            num_full_stars = len(rating_div.find_all('svg', {'xmlns': 'http://www.w3.org/2000/svg'}))
            width_percentage = float(rating_div['style'].split('width: ')[1].split('%')[0])
            product_rating = num_full_stars*width_percentage/100.0
            print(f'Product rating: {product_rating}')

            product_delivery_info = product.find('div', {'class': 'style__DeliveryInfoStyled-sc-1gk0d20-1 dYmOFw delivery-info'}).text
            print(f'Product delivery info: {product_delivery_info}')

            product_tags = []
            product_tags_elements = product.find_all('div', {'class': 'style__TextBoxStyled-sc-lvrlm0-1 jtqrwI'})
            for tag in product_tags_elements:
                product_tags.append(tag.text)
            print(f'Product tag: {product_tags}')

            data = {
                'url': product_url,
                'img': product_img,
                'badges': badges,
                'price': product_price,
                'brand': product_brand,
                'name': product_name,
                'sold_count': product_sold_count,
                'rating': product_rating,
                'delivery_info': product_delivery_info,
                'tags': product_tags
            }

            product_list.append(data)
        except Exception as e:
            print(f'Error: {e}')

# Set up Selenium webdriver
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run Chrome in headless mode
options.add_argument('--disable-gpu')  # Disable GPU acceleration
options.add_argument('--no-sandbox')  # Bypass OS security
options.add_argument('--incognito')  # Enable incognito mode
options.add_argument('--ignore-certificate-errors')  # Ignore certificate errors
options.add_argument('--ignore-ssl-errors')  # Ignore SSL errors
options.add_argument('--disable-dev-shm-usage')  # Disable shared memory usage
driver = webdriver.Chrome(options=options)  # Use Chrome webdriver


TIKI_URL = 'https://tiki.vn/search?q=b%C3%A0n+ph%C3%ADm+c%C6%A1&rating=4'

# Get the page source
driver.get(TIKI_URL) 
time.sleep(5)

product_list = []
WAIT_TIME = 2
while True:
    try:
        # Extract data from the current page
        page_source = driver.page_source
        extract_data(page_source, product_list)

        # Find the next button and navigate to the next page
        next_button = driver.find_element(By.XPATH, '//a[@data-view-id="product_list_pagination_item" and contains(@class, "arrow undefined")]')
        if next_button.is_enabled() and next_button.is_displayed():
            next_page_url = next_button.get_attribute('href')
            
            # Parse the URL to get the page number
            parsed_url = urlparse(next_page_url)
            page_number = parse_qs(parsed_url.query).get('page', ['1'])[0]

            print(f'Navigating to page {page_number}...')
            driver.get(next_page_url)
            time.sleep(2)
        else:
            print('Reached the last page.')
            break
    except Exception as e:
        print(f"Next page button not found.")
        break

page_source = driver.page_source

# Close the webdriver
driver.quit()

df = pd.DataFrame.from_dict(product_list)

# Save the data to a CSV file
dest = os.path.join("data", "tiki_products.csv")
if os.path.exists(dest):
    # If this file already exists, append to it
    df.to_csv(dest, mode="a", index=False, header=False)
else:
    # Else, create a new file and write to it
    df.to_csv(dest, mode="w", index=False, header=False)