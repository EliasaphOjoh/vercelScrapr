#!/usr/bin/env python
import os
import re
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from rake_nltk import Rake
import nltk

# Download NLTK stopwords and punkt if not already downloaded
nltk.download('stopwords')
nltk.download('punkt')

# Function to read URLs from a file
def read_urls(file_path):
    with open(file_path, 'r') as file:
        urls = file.readlines()
    return [url.strip() for url in urls]

# Function to scrape articles
def scrape_article(url):
    try:
        # Using Newspaper3k
        article = Article(url)
        article.download()
        article.parse()

        # Extract images
        images = article.images  # Get all images in the article

        return {
            'title': article.title,
            'content': article.html,
            'url': url,
            'images': list(images)
        }
    except Exception as e:
        print(f"Error scraping {url} with Newspaper3k: {e}")

    try:
        # Using Requests and BeautifulSoup
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to retrieve {url}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract the article content
        article_content = soup.find('article')  # Assuming the article content is within <article> tags
        if not article_content:
            print("Article tag not found.")
            return None

        elements = article_content.find_all(['p', 'img'])  # Extract paragraphs and images

        return {
            'title': soup.find('title').get_text(),
            'content': elements,
            'url': url,
            'images': [img['src'] for img in soup.find_all('img', src=True)]
        }
    except Exception as e:
        print(f"Error scraping {url} with BeautifulSoup: {e}")

    try:
        # Using Selenium for dynamic content
        options = Options()
        options.headless = True
        service = Service('path/to/chromedriver')  # Specify the correct path to your chromedriver
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        content = driver.page_source
        soup = BeautifulSoup(content, 'html.parser')

        # Extract the article content
        article_content = soup.find('article')  # Assuming the article content is within <article> tags
        if not article_content:
            print("Article tag not found.")
            return None

        elements = article_content.find_all(['p', 'img'])  # Extract paragraphs and images

        driver.quit()

        return {
            'title': soup.find('title').get_text(),
            'content': elements,
            'url': url,
            'images': [img.get_attribute('src') for img in driver.find_elements_by_tag_name('img')]
        }
    except Exception as e:
        print(f"Error scraping {url} with Selenium: {e}")

    return None

# Function to extract keyword from title
def extract_keyword(title):
    rake = Rake()
    rake.extract_keywords_from_text(title)
    keywords = rake.get_ranked_phrases()
    if keywords:
        keyword = keywords[0]  # Take the highest-ranked keyword
        keyword = re.sub(r'\W+', '', keyword)  # Remove non-alphanumeric characters
        return keyword
    return "article"

# Function to download an image and return its local path
def download_image(img_url, img_dir, img_count):
    try:
        response = requests.get(img_url, stream=True)
        if response.status_code == 200:
            img_extension = os.path.splitext(img_url)[1].split('?')[0]  # Handle URLs with query strings
            img_name = f"image{img_count}{img_extension}"
            img_path = os.path.join(img_dir, img_name)
            with open(img_path, 'wb') as img_file:
                for chunk in response.iter_content(1024):
                    img_file.write(chunk)
            return img_path
        else:
            print(f"Failed to download image: {img_url}")
            return None
    except Exception as e:
        print(f"Error downloading image {img_url}: {e}")
        return None

# Function to save article as HTML file
def save_article_as_html(article, output_dir='articles', images_dir='images'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    keyword = extract_keyword(article['title'])
    article_file_path = os.path.join(output_dir, f"{keyword}.html")

    # Prepare CSS content
    css_content = """
    <style>
    body {
        background-color: lightblue;
    }
    h1 {
        color: green;
        font-size: 45px;
    }
    p {
        font-size: 20px;
    }
    </style>
    """

    # Prepare HTML content with embedded images
    html_content = f"""
    <html>
    <head>
        <title>{article['title']}</title>
        {css_content}
    </head>
    <body>
        <h1>{article['title']}</h1>
    """

    img_count = 1
    img_dir = os.path.join(images_dir, keyword)
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    # Parse content if it's a string
    if isinstance(article['content'], str):
        soup = BeautifulSoup(article['content'], 'html.parser')
        elements = soup.find_all(['p', 'img'])
    else:
        elements = article['content']

    for element in elements:
        if element.name == 'p':
            html_content += f"<p>{element.get_text()}</p>"
        elif element.name == 'img' and element.get('src'):
            img_url = element['src']
            img_path = download_image(img_url, img_dir, img_count)
            if img_path:
                img_tag = f'<img src="{os.path.join("../", img_path)}" alt="Image {img_count}">\n'
                html_content += img_tag
                img_count += 1

    html_content += """
    </body>
    </html>
    """

    # Save HTML file
    with open(article_file_path, 'w', encoding='utf-8') as file:
        file.write(html_content)

    print(f"Saved: {article_file_path}")

# Main script
file_path = 'urls.txt'
if not os.path.exists(file_path):
    print(f"File {file_path} does not exist. Please create the file with the list of URLs.")
else:
    urls = read_urls(file_path)
    articles = []
    for url in urls:
        article = scrape_article(url)
        if article:
            articles.append(article)
            save_article_as_html(article)

    print("All articles have been processed.")
