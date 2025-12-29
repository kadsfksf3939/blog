#!/usr/bin/env python3
"""Debug script to analyze the blog page structure"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BLOG_URL = "https://iipmr.com/blog/"

response = requests.get(BLOG_URL, timeout=30)
soup = BeautifulSoup(response.content, 'html.parser')

# Find all links on the page
all_links = soup.find_all('a', href=True)
print(f"Total links on page: {len(all_links)}\n")

# Group links by type
youtube_links = []
blog_links = []
other_links = []

for link in all_links:
    href = link.get('href')
    full_url = urljoin(BLOG_URL, href)
    text = link.get_text().strip()

    if 'youtube.com' in href or 'youtu.be' in href:
        youtube_links.append((full_url, text))
    elif '/blog/' in href or 'iipmr.com' in href:
        blog_links.append((full_url, text))
    else:
        other_links.append((full_url, text))

print(f"YouTube links: {len(youtube_links)}")
for url, text in youtube_links[:5]:
    print(f"  - {text[:50]}: {url[:80]}")

print(f"\nBlog links: {len(blog_links)}")
for url, text in blog_links[:10]:
    print(f"  - {text[:50]}: {url[:80]}")

print(f"\nOther links: {len(other_links)}")
for url, text in other_links[:5]:
    print(f"  - {text[:50]}: {url[:80]}")

# Find CTA sections and see what they contain
cta_sections = soup.find_all('div', class_=lambda x: x and 'pagelayer-cta' in str(x))
print(f"\n\nCTA sections: {len(cta_sections)}")
if len(cta_sections) > 0:
    print("\nFirst CTA section analysis:")
    first_cta = cta_sections[0]
    links_in_cta = first_cta.find_all('a', href=True)
    print(f"  Links in first CTA: {len(links_in_cta)}")
    for link in links_in_cta:
        print(f"    - {link.get_text().strip()[:50]}: {link.get('href')[:80]}")
