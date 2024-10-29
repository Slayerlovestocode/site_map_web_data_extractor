


import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
from urllib.parse import urljoin, urlparse
import mysql.connector
from mysql.connector import Error
import json

# MySQL connection setup
def create_connection(host, user, password, database):
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        if connection.is_connected():
            print("Connection to MySQL DB successful")
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def insert_data(connection, data):
    try:
        cursor = connection.cursor()
        # Convert the Counter object to JSON string
        data['keywords'] = json.dumps(data['keywords'])

        # Ensure the status is valid
        if data['status'] not in ['pending', 'complete']:
            print(f"Invalid status '{data['status']}' for URL {data['url']}. Setting to 'pending'.")
            data['status'] = 'pending'  # Default to 'pending' if invalid

        query = """
        INSERT INTO scraped_data (type, url, meta_title, meta_description, keywords, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data['type'],
            data['url'],
            data['meta_title'],
            data['meta_description'],
            data['keywords'],
            data['status']
        ))

        connection.commit()
        print(f"Data inserted for URL: {data['url']}")
    except Error as e:
        print(f"Failed to insert data for URL {data['url']}: {e}")
    finally:
        cursor.close()

def fetch_homepage(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to fetch homepage: {response.status_code}")

def find_sitemap_url(homepage_content, base_url):
    soup = BeautifulSoup(homepage_content, 'html.parser')
    sitemap_links = [
        urljoin(base_url, link['href'])
        for link in soup.find_all('a', href=True)
        if 'sitemap' in link['href']
    ]
    return sitemap_links[0] if sitemap_links else None

def check_common_sitemap_urls(base_url):
    common_sitemaps = [
        'sitemap.xml',
        'sitemap_index.xml',
        'sitemap/sitemap.xml',
        'sitemap.xml.gz'
    ]

    for sitemap in common_sitemaps:
        sitemap_url = urljoin(base_url, sitemap)
        try:
            response = requests.head(sitemap_url)
            if response.status_code == 200:
                return sitemap_url
        except requests.RequestException:
            continue
    return None

def fetch_sitemap(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to fetch sitemap: {response.status_code}")

def parse_sitemap(xml_content):
    soup = BeautifulSoup(xml_content, 'xml')
    urls = [loc.text for loc in soup.find_all('loc')]
    return urls

def fetch_page_links(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            if 'xml' in response.headers.get('Content-Type', ''):
                soup = BeautifulSoup(response.text, 'xml')
                return [
                    link.text for link in soup.find_all('loc')
                    if not (
                        'https://cdn.shopify.com' in link.text or 
                        '?v=' in link.text or 
                        '?variant=' in link.text or
                        'twitter.com' in link.text or
                        'facebook.com' in link.text or
                        'pinterest.com' in link.text
                    )
                ]
            else:
                soup = BeautifulSoup(response.text, 'html.parser')
                return [
                    urljoin(url, link['href']) for link in soup.find_all('a', href=True)
                    if not (
                        'https://cdn.shopify.com' in link['href'] or 
                        '?v=' in link['href'] or 
                        '?variant=' in link['href'] or
                        'twitter.com' in link['href'] or
                        'facebook.com' in link['href'] or
                        'pinterest.com' in link['href']
                    )
                ]
        else:
            raise Exception(f"Failed to fetch page: {response.status_code}")
    except Exception as e:
        print(f"Error fetching page links from {url}: {e}")
        return []

def check_robots_txt(base_url):
    robots_url = urljoin(base_url, 'robots.txt')
    try:
        response = requests.get(robots_url)
        if response.status_code == 200:
            return response.text
    except requests.RequestException:
        return None
    return None

def extract_sitemap_from_robots_txt(robots_content):
    for line in robots_content.splitlines():
        if line.startswith('Sitemap:'):
            return line.split(':', 1)[1].strip()
    return None

def get_clean_text_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.title.string if soup.title else 'No Title'
        meta_description = soup.find('meta', attrs={'name': 'description'})
        meta_description_content = meta_description['content'] if meta_description else 'No Description'
        text = soup.get_text(separator=' ')
        clean_text = ' '.join(text.split())

        return clean_text.lower(), title, meta_description_content
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the page: {e}")
        return None, None, None

def count_words(text, word_list):
    word_counter = Counter()
    for word in word_list:
        word_count = len(re.findall(rf'\b{re.escape(word.lower())}\b', text))
        word_counter[word] = word_count
    return word_counter

def categorize_link(link):
    if '/page' in link:
        return "Page"
    elif '/collection' in link:
        return "Collection"
    elif '/blog' in link:
        return "Blog"
    elif '/article' in link:
        return "Article"
    elif '/product' in link:
        return "Product"
    else:
        return "Other"

def is_valid_url(url, base_domain):
    parsed_url = urlparse(url)
    return parsed_url.netloc.endswith(base_domain)  # Check if the netloc ends with the base domain

def main(db_config):
    # Ask user for the website URL
    website_url = input("Enter the website URL: ").strip()
    
    # Extract the base domain
    parsed_url = urlparse(website_url)
    base_domain = parsed_url.netloc
    print(f"Base domain extracted: {base_domain}")

    # Ask user for keywords
    word_list = input("Enter the keywords or phrases (separated by commas): ").split(',')
    word_list = [word.strip() for word in word_list]  # Clean up whitespaces
    print(f"Keywords: {word_list}")

    # Connect to MySQL database
    connection = create_connection(
        db_config['host'],
        db_config['user'],
        db_config['password'],
        db_config['database']
    )

    # Fetch the homepage content
    homepage_content = fetch_homepage(website_url)

    # Try to find the sitemap URL from the homepage
    sitemap_url = find_sitemap_url(homepage_content, website_url)

    if not sitemap_url:
        print("No sitemap link found on the homepage. Checking common sitemap URLs...")
        sitemap_url = check_common_sitemap_urls(website_url)

    if not sitemap_url:
        print("No common sitemap URL found. Checking robots.txt...")
        robots_content = check_robots_txt(website_url)
        if robots_content:
            sitemap_url = extract_sitemap_from_robots_txt(robots_content)

    if sitemap_url:
        print(f"Found sitemap URL: {sitemap_url}")
        sitemap_content = fetch_sitemap(sitemap_url)
        urls = parse_sitemap(sitemap_content)

        all_links = set(urls)  # Using a set to avoid duplicates
        links_to_process = list(all_links)  # Use a list for safe iteration

        # Process each URL from the list
        while links_to_process:
            url = links_to_process.pop(0)
            print(f"Processing URL: {url}")

            if is_valid_url(url, base_domain):  # Check if the URL is valid
                # Fetch additional links from the page and add to all_links and links_to_process
                page_links = fetch_page_links(url)
                new_links = set(page_links) - all_links
                all_links.update(new_links)
                links_to_process.extend(new_links)

                # Process each link and extract text, metadata, and word counts
                page_text, title, meta_description = get_clean_text_from_url(url)
                if page_text:
                    word_count = count_words(page_text, word_list)
                    category = categorize_link(url)

                    data = {
                        'type': category,
                        'url': url,
                        'meta_title': title,
                        'meta_description': meta_description,
                        'keywords': word_count,
                        'status': 'pending'
                    }

                    # Insert data into MySQL database
                    insert_data(connection, data)
            else:
                print(f"Skipping invalid URL: {url}")

    else:
        print("No sitemap URL could be found.")

    if connection:
        connection.close()

if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'Karan@123',
        'database': 'web_scraper_v2'
    }
    main(db_config)
