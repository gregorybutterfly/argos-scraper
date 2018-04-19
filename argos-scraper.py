import requests
from bs4 import BeautifulSoup
import json
import os

class HttpRequest:
    """The class is responsible for getting raw data from a given url.

    - Get an url from the App Class
    - Grab the content of a given url (self.raw_content)
    - Generate links for NEXT result pages (self.get_search_result_pages)

    """

    def __init__(self, url):
        # generated link:  http://www.argos.co.uk/search/ + keyword
        self.url = url
        # Requests object with raw data
        self.raw_content = self.get_http_request(self.url)

    def set_headers(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36 Core/1.47.933.400 QQBrowser/9.4.8699.400',
        }

    def get_http_request(self, url):
        """Get the content of a given url
        """

        headers = self.set_headers()

        return requests.get(url, headers=headers).content

    def get_search_result_pages(self):
        """Grabs all pages from search results of a given keyword and store them under self.ALL_PAGES
        """

        headers = self.set_headers()

        # pagination number to increment every loop
        num = 1
        # all valid pages with products
        all_pages = []

        while True:
            # generate url to next page
            url = requests.get(self.url).url + '/opt/page:' + str(num) + '/'
            # grab the url and check if result not empty
            r = requests.get(url, headers=headers).content
            if "error-page".lower() in str(r.lower()):
                # break the loop if results NOT FOUND/empty
                break
            elif "no-results" in str(r.lower()):
                break
            else:
                print(url)
                # append valid page link to all_pages and increment num to generate next page url
                all_pages.append(url)
                num += 1


        return all_pages

class FileSystem:

    def is_dir(self):

        products = 'Products'

        if not os.path.exists(os.path.join(os.path.dirname(__file__), products)):
            os.mkdir(os.path.join(os.path.dirname(__file__), products))
        else:
            print('path found: {}'.format(products))

class App(HttpRequest, FileSystem):
    """Main class

    - Takes a keyword and a raw_url and combines them together to get the search results page url.
    - Super calls the parent class 'HttpRequests' with previously generated url (self.search_link).
    - HttpRequests sends back self.raw_content that will be used to generate BeautifulSoup object.
    - Grab additional content by looping over the rest of search results. Produce links to valid pages (self.pages).
    - Get price, description, link... and save it inside of dict, under (self.content_all_pages)
    - Export created dict to json files
    """

    def __init__(self, keyword, raw_url):

        self.is_dir()

        # keyword
        self.keyword = keyword
        # search results page url
        self.raw_url = raw_url
        # generated link from keyword and raw_url:  http://www.argos.co.uk/search/ + keyword
        self.search_link = self.generate_search_link()
        # calls parent class with generated url
        super().__init__(self.search_link)
        # Generates BeautifulSoup object
        self.content = self.soup_object(self.raw_content)
        # Grab all valid search result pages
        self.pages = self.get_search_result_pages()
        # Grab the content of all pages
        self.content_all_pages = self.get_all_pages_content()

    def generate_search_link(self):
        # http://www.argos.co.uk/search/ + keyword
        return self.raw_url + self.keyword

    def soup_object(self, raw_content):
        return BeautifulSoup(raw_content, 'html.parser')

    def get_all_pages_content(self):
        """
        Go through all links in self.pages and grab the content of each product.
        Produce dict of items that can be exported to various data formats.

        """

        items = {}

        for page in self.pages:
            self.raw_content = self.get_http_request(page)
            self.content = self.soup_object(self.raw_content)

            # list of all products
            product_list = self.content.findAll('div', {'class': 'ac-product-card'})
            # product name
            for product in product_list:
                product_name = product.find('div', {'class': 'ac-product-name'}).text
                # link for product page
                product_link = product.find('a', {'class': 'ac-product-link'})['href']
                # Id of a product
                product_id = product_link.split('/')[-1]
                # Rating of a product
                try:
                    product_rating = product.find('div', {'class': 'ac-star-rating'})['data-star-rating']
                except TypeError:
                    # No product rating found
                    product_rating = 0
                # Price of a product
                product_price = product.find('div', {'class': 'ac-product-price'}).text

                """
                print('\nProduct Name: {}'
                      '\nProduct Id: {}'
                      '\nProduct Price: {}'
                      '\nProduct Rating: {}'
                      '\nProduct Link: {}\n'.format(product_name, product_id, product_price, product_rating, 'http://www.argos.co.uk' + product_link))
                """

                items[product_id] = {
                    'Product Name': product_name,
                    'Price': product_price,
                    'Rating': product_rating,
                    'Link': 'http://www.argos.co.uk' + product_link,
                    'Search term': self.keyword,
                }

        return items

    def get_product_page(self, productLink):
        """Grab individual product page content

        http://www.argos.co.uk/product/6836429
        """
        if "/product" in productLink:
            product_id = productLink.split("/")[-1]
        else:
            raise KeyError('No product link detected')

        conntent = self.get_http_request(productLink)
        soup = self.soup_object(conntent)

        product_name = soup.find('h1', {'class': 'h1 product-name-main'}).text
        product_description = soup.find('div', {'itemprop':'description'}).text
        product_price = soup.find('li', {'itemprop':'price'}).text

        self.content_all_pages[product_id]['Description'] = product_description

    def export_json(self):
        # Dump the data to json file if True
        with open('products.json', 'w') as f:
            json.dump(self.content_all_pages, f, indent=4, separators=(',', ':'), ensure_ascii=False)


# GRAB SEARCH RESULTS FOR ALL PRODUCTS
ArgosQuery = App('ipad','http://www.argos.co.uk/search/')

# GRAB PRODUCT SUBPAGE
ArgosQuery.get_product_page('http://www.argos.co.uk/product/6836429')

# EXPORT THE DATA
ArgosQuery.export_json()
