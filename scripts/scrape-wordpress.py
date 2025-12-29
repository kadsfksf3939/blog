#!/usr/bin/env python3
"""
WordPress Blog Scraper for IIPMR Blog Migration
Scrapes posts from https://iipmr.com/blog/ and saves them for Hugo conversion
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import os
from datetime import datetime
import time
import re

BLOG_URL = "https://iipmr.com/blog/"
OUTPUT_DIR = "wordpress-scraped"
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
POSTS_FILE = os.path.join(OUTPUT_DIR, "posts.json")

# Create output directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)


def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    return text.strip()


def slugify(text):
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')


def download_image(image_url, slug):
    """Download image and return local filename"""
    try:
        # Skip if not an actual URL
        if not image_url or not image_url.startswith('http'):
            return None

        # Get file extension
        parsed = urlparse(image_url)
        filename = os.path.basename(parsed.path)
        if not filename:
            filename = f"{slug}-image.jpg"

        # Download image
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        # Save image
        filepath = os.path.join(IMAGES_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"  Downloaded image: {filename}")
        return filename
    except Exception as e:
        print(f"  Failed to download image {image_url}: {e}")
        return None


def scrape_blog_listing():
    """Scrape main blog page to get all post URLs"""
    print(f"Scraping blog listing from {BLOG_URL}...")

    try:
        response = requests.get(BLOG_URL, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        posts = []

        # This blog uses PageLayer page builder
        # Posts are in .pagelayer-cta-heading containers

        # Find all CTA (Call-to-Action) sections which contain blog posts
        cta_sections = soup.find_all('div', class_=lambda x: x and 'pagelayer-cta' in str(x))

        print(f"  Found {len(cta_sections)} CTA sections")

        for i, cta in enumerate(cta_sections):
            # Extract title and link
            heading = cta.find(class_=lambda x: x and 'pagelayer-cta-heading' in str(x))
            if not heading:
                # Try finding any link in the CTA section
                link = cta.find('a', href=True)
                if link:
                    url = link.get('href')
                    # Only include blog posts (exclude external YouTube links)
                    if 'youtube.com' in url or 'youtu.be' in url:
                        continue
                    # Make sure it's a full URL
                    full_url = urljoin(BLOG_URL, url)
                    # Extract title from link text or surrounding text
                    title = clean_text(link.get_text())
                    if not title:
                        # Try to find title in CTA section
                        title_elem = cta.find(['h1', 'h2', 'h3', 'h4'])
                        if title_elem:
                            title = clean_text(title_elem.get_text())
                else:
                    continue
            else:
                link = heading.find('a')
                if not link or not link.get('href'):
                    # If no link in heading, try finding any link
                    link = cta.find('a', href=True)
                    if not link:
                        continue

                url = link.get('href')
                # Only include blog posts (exclude external YouTube links)
                if 'youtube.com' in url or 'youtu.be' in url:
                    continue

                # Make sure it's a full URL
                full_url = urljoin(BLOG_URL, url)
                title = clean_text(link.get_text())

            if i < 3:  # Debug: print first 3 posts
                print(f"  Debug CTA {i}: URL={full_url}, Title={title}")

            # Extract featured image
            featured_image = ""
            img_div = cta.find(class_=lambda x: x and 'pagelayer-cta-image' in str(x))
            if img_div:
                # Check for background image in style
                style = img_div.get('style', '')
                if 'background-image' in style:
                    # Extract URL from background-image: url(...)
                    match = re.search(r'url\(["\']?([^"\')]+)["\']?\)', style)
                    if match:
                        featured_image = match.group(1)
                        featured_image = urljoin(BLOG_URL, featured_image)

                # Also check for img tag
                if not featured_image:
                    img = img_div.find('img')
                    if img:
                        featured_image = img.get('src', '') or img.get('data-src', '')
                        if featured_image:
                            featured_image = urljoin(BLOG_URL, featured_image)

            # Extract excerpt/subheading
            excerpt = ""
            subheading = cta.find(class_=lambda x: x and 'pagelayer-cta-subheading' in str(x))
            if subheading:
                excerpt = clean_text(subheading.get_text())

            # Extract categories from badges
            categories = []
            badges = cta.find_all(class_=lambda x: x and 'pagelayer-badge' in str(x))
            for badge in badges:
                cat_text = clean_text(badge.get_text())
                if cat_text:
                    categories.append(cat_text)

            posts.append({
                'url': full_url,
                'title': title,
                'featured_image': featured_image,
                'excerpt': excerpt,
                'categories': categories
            })

        # Also try to find posts in service sections (alternative layout)
        service_sections = soup.find_all('div', class_=lambda x: x and 'pagelayer-service' in str(x))

        print(f"  Found {len(service_sections)} service sections")

        for service in service_sections:
            heading = service.find(class_=lambda x: x and 'pagelayer-service-heading' in str(x))
            if not heading:
                continue

            link = heading.find('a')
            if not link or not link.get('href'):
                continue

            url = link.get('href')
            if 'youtube.com' in url or 'youtu.be' in url:
                continue

            full_url = urljoin(BLOG_URL, url)

            # Check if we already have this URL
            if any(p['url'] == full_url for p in posts):
                continue

            title = clean_text(link.get_text())

            # Extract featured image
            featured_image = ""
            img_div = service.find(class_=lambda x: x and 'pagelayer-service-image' in str(x))
            if img_div:
                img = img_div.find('img')
                if img:
                    featured_image = img.get('src', '') or img.get('data-src', '')
                    if featured_image:
                        featured_image = urljoin(BLOG_URL, featured_image)

            # Extract excerpt
            excerpt = ""
            details = service.find(class_=lambda x: x and 'pagelayer-service-details' in str(x))
            if details:
                excerpt = clean_text(details.get_text())

            # Extract categories from badges
            categories = []
            badges = service.find_all(class_=lambda x: x and 'pagelayer-badge' in str(x))
            for badge in badges:
                cat_text = clean_text(badge.get_text())
                if cat_text:
                    categories.append(cat_text)

            posts.append({
                'url': full_url,
                'title': title,
                'featured_image': featured_image,
                'excerpt': excerpt,
                'categories': categories
            })

        print(f"Found {len(posts)} posts on blog listing page")
        return posts

    except Exception as e:
        print(f"Error scraping blog listing: {e}")
        import traceback
        traceback.print_exc()
        return []


def extract_youtube_urls(soup):
    """Extract YouTube video URLs from page"""
    youtube_urls = []

    # Look for iframe embeds
    iframes = soup.find_all('iframe', src=lambda x: x and 'youtube.com' in x)
    for iframe in iframes:
        youtube_urls.append(iframe['src'])

    # Look for direct YouTube links
    links = soup.find_all('a', href=lambda x: x and ('youtube.com' in x or 'youtu.be' in x))
    for link in links:
        youtube_urls.append(link['href'])

    return youtube_urls


def scrape_post_content(post_url, post_info):
    """Scrape individual post for full content"""
    print(f"\nScraping post: {post_url}")

    try:
        response = requests.get(post_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract post content
        # Try multiple selectors for the main content area
        content_selectors = [
            'article .entry-content',
            'article .post-content',
            '.post-content',
            '.entry-content',
            'article',
            '.content'
        ]

        content_elem = None
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                break

        if not content_elem:
            print(f"  Warning: Could not find content for {post_url}")
            content_html = ""
        else:
            content_html = str(content_elem)

        # Extract title if not already found
        title = post_info.get('title', '')
        if not title:
            title_elem = soup.find(['h1', 'h2'], class_=lambda x: x and 'title' in str(x).lower())
            if not title_elem:
                title_elem = soup.find('h1')
            if title_elem:
                title = clean_text(title_elem.get_text())

        # Extract date
        date = None
        date_elem = soup.find(['time', 'span'], class_=lambda x: x and ('date' in str(x).lower() or 'time' in str(x).lower()))
        if date_elem:
            date_str = date_elem.get('datetime') or date_elem.get_text()
            # Try to parse date
            try:
                # Common WordPress date formats
                for fmt in ['%Y-%m-%d', '%B %d, %Y', '%d %B %Y', '%m/%d/%Y']:
                    try:
                        date = datetime.strptime(clean_text(date_str), fmt).strftime('%Y-%m-%d')
                        break
                    except:
                        continue
            except:
                pass

        if not date:
            # Use current date as fallback
            date = datetime.now().strftime('%Y-%m-%d')

        # Extract categories/tags
        categories = post_info.get('categories', [])
        if not categories:
            cat_elems = soup.find_all(['a', 'span'], class_=lambda x: x and ('categor' in str(x).lower() or 'tag' in str(x).lower()))
            categories = [clean_text(cat.get_text()) for cat in cat_elems if clean_text(cat.get_text())]
            # Remove duplicates
            categories = list(set(categories))

        # Extract featured image if not already found
        featured_image = post_info.get('featured_image', '')
        if not featured_image:
            img = soup.find('img', class_=lambda x: x and 'featured' in str(x).lower())
            if not img:
                # Just get first image in content
                if content_elem:
                    img = content_elem.find('img')
            if img:
                featured_image = img.get('src', '') or img.get('data-src', '')
                if featured_image:
                    featured_image = urljoin(post_url, featured_image)

        # Extract YouTube embeds
        youtube_urls = extract_youtube_urls(soup)

        # Create slug from title
        slug = slugify(title) if title else slugify(post_url.split('/')[-2])

        # Download featured image
        image_filename = None
        if featured_image:
            image_filename = download_image(featured_image, slug)

        # Download images in content
        if content_elem:
            for img in content_elem.find_all('img'):
                img_url = img.get('src', '') or img.get('data-src', '')
                if img_url:
                    full_img_url = urljoin(post_url, img_url)
                    download_image(full_img_url, slug)

        post_data = {
            'url': post_url,
            'title': title,
            'slug': slug,
            'date': date,
            'content_html': content_html,
            'excerpt': post_info.get('excerpt', ''),
            'categories': categories,
            'featured_image_url': featured_image,
            'featured_image_filename': image_filename,
            'youtube_urls': youtube_urls
        }

        print(f"  Title: {title}")
        print(f"  Date: {date}")
        print(f"  Categories: {', '.join(categories)}")
        print(f"  YouTube videos: {len(youtube_urls)}")

        return post_data

    except Exception as e:
        print(f"  Error scraping post content: {e}")
        return None


def main():
    print("=" * 80)
    print("IIPMR WordPress Blog Scraper")
    print("=" * 80)

    # Scrape blog listing
    posts_list = scrape_blog_listing()

    if not posts_list:
        print("\nNo posts found. Exiting.")
        return

    print(f"\n{'='*80}")
    print(f"Scraping {len(posts_list)} posts...")
    print(f"{'='*80}")

    # Scrape each post
    all_posts = []
    for i, post_info in enumerate(posts_list, 1):
        print(f"\n[{i}/{len(posts_list)}]", end=" ")
        post_data = scrape_post_content(post_info['url'], post_info)

        if post_data:
            all_posts.append(post_data)

        # Be polite - don't hammer the server
        time.sleep(1)

    # Save all posts to JSON
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_posts, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"Scraping complete!")
    print(f"Scraped {len(all_posts)} posts")
    print(f"Data saved to: {POSTS_FILE}")
    print(f"Images saved to: {IMAGES_DIR}")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
