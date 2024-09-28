---
Title: Web Scrapping
Created: 12th September 2024 17:09
Last Modified: 12th September 2024 17:09
tags:
  - ML
cssclasses:
---
## Importing libraries and setting up variables

```python
import requests
from bs4 import BeautifulSoup

base_url = 'https://www.moneycontrol.com/news/business/companies/page-{}/'
num_pages = 2  # Number of pages to scrape
head = []  # List to store headlines
entire_art = []  # List to store article content
```
This section imports the necessary libraries and sets up variables for the base URL, number of pages to scrape, and lists to store headlines and article content.

## Looping through pages

```python
for page_num in range(1, num_pages + 1):
    url = base_url.format(page_num)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
```
This loop goes through each page, constructs the URL, sends a GET request, and creates a BeautifulSoup object from the response.

## Finding the main content div

```python
    div_left = soup.find('div', {'id': 'left', 'class': 'fleft'})
    if div_left:
        ul_category = div_left.find('ul', id='cagetory')
        if ul_category:
            headlines = ul_category.find_all('a')
```
This section locates the main content div and the list of headlines within it.

## Processing each headline
```python
    for headline in headlines:
        headline_text = headline.text.strip()
        article_url = headline['href']
```
This loop extracts the text and URL for each headline.

## Fetching and processing article content

### **1. Initiating the Request

```python
article_response = requests.get(article_url, allow_redirects=False)
```

- This line sends a GET request to the article URL.
- `allow_redirects=False` prevents automatic following of redirects. This is important for controlling the scraping process and avoiding infinite redirect loops.

### **2. Handling Redirects

```python
if article_response.is_redirect or article_response.is_permanent_redirect:
    print(f"Redirect encountered for URL: {article_url}")
    continue
```

- This checks if the response is a redirect (temporary or permanent).
- If a redirect is encountered, it logs the URL and skips to the next article.
- This helps avoid issues with redirects that might lead to unexpected content or errors.

### **3. Checking Response Status

```python
if article_response.status_code == 200:
    # Process the article
else:
    print(f"Failed to fetch article for URL: {article_url} with status code {article_response.status_code}")
```

- A status code of 200 indicates a successful request.
- Any other status code is treated as a failure, and the error is logged.

### **4. Parsing the Article HTML

```python
article_soup = BeautifulSoup(article_response.text, 'html.parser')
```

- This creates a new BeautifulSoup object from the article's HTML content.
- It allows for easy navigation and searching of the HTML structure.

### **5. Extracting Article Content

```python
article_div = article_soup.find('div', class_='arti-flow')
if article_div:
    paragraphs = article_div.find_all('p')
    article_content = ' '.join([para.text for para in paragraphs])
    entire_art.append(article_content)
else:
    print("No article content found.")
```

- This searches for a div with class 'arti-flow', which is assumed to contain the main article content.
- If found, it extracts all paragraph (`<p>`) tags within this div.
- The text from all paragraphs is joined into a single string, representing the full article content.
- If the 'arti-flow' div is not found, it logs that no content was found.

### **6. Storing the Headline

```python
head.append(headline_text)
```

- This adds the headline text to the `head` list.
- Note: There's a duplicate line later in the code that does this again, which might be unintentional.

## Error handling for missing elements:
```python
    else:
        print(f"No <ul> with id 'cagetory' found on page {page_num}.")
else:
    print(f"No <div> with id 'left' and class 'fleft' found on page {page_num}.")
```
These lines print error messages if the expected HTML structure is not found.

This script scrapes headlines and article content from multiple pages of the MoneyControl website, handling various potential issues like redirects and missing content. The scraped data is stored in the `head` and `entire_art` lists.

Would you like me to elaborate on any specific part of this web scraping code?
