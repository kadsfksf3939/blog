#!/usr/bin/env python3
"""
IIPMR Blog Scraper - YouTube Video Posts
Scrapes YouTube video embeds from https://iipmr.com/blog/ and converts them to Hugo posts
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
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


def extract_youtube_id(url):
    """Extract YouTube video ID from URL"""
    if not url:
        return None

    # Handle different YouTube URL formats
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def download_youtube_thumbnail(video_id, slug):
    """Download YouTube video thumbnail"""
    try:
        # YouTube thumbnail URL (max resolution)
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

        # Try to download
        response = requests.get(thumbnail_url, timeout=30)

        # If maxresdefault doesn't exist, fall back to hqdefault
        if response.status_code == 404:
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            response = requests.get(thumbnail_url, timeout=30)

        response.raise_for_status()

        # Save thumbnail
        filename = f"{slug}-thumbnail.jpg"
        filepath = os.path.join(IMAGES_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"  Downloaded thumbnail: {filename}")
        return filename
    except Exception as e:
        print(f"  Failed to download thumbnail: {e}")
        return None


def scrape_video_posts():
    """Scrape YouTube video posts from blog page"""
    print(f"Scraping video posts from {BLOG_URL}...")

    try:
        response = requests.get(BLOG_URL, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        posts = []

        # Find all CTA sections which contain video posts
        cta_sections = soup.find_all('div', class_=lambda x: x and 'pagelayer-cta' in str(x))

        print(f"  Found {len(cta_sections)} video sections")

        for i, cta in enumerate(cta_sections):
            # Extract YouTube link
            link = cta.find('a', href=lambda x: x and ('youtube.com' in x or 'youtu.be' in x))
            if not link:
                continue

            video_url = link.get('href')
            video_id = extract_youtube_id(video_url)

            if not video_id:
                print(f"  Warning: Could not extract video ID from {video_url}")
                continue

            # Extract title - usually the link text or in heading
            title = clean_text(link.get_text())
            if not title or title.lower() == 'click here':
                # Try to find title in surrounding elements
                heading = cta.find(class_=lambda x: x and 'pagelayer-cta-heading' in str(x))
                if heading:
                    title = clean_text(heading.get_text())

                # If still no title, try any h1-h4
                if not title:
                    title_elem = cta.find(['h1', 'h2', 'h3', 'h4'])
                    if title_elem:
                        title = clean_text(title_elem.get_text())

            # If still no title, use video ID
            if not title or title.lower() == 'click here':
                title = f"Video {video_id}"

            # Extract description/subheading
            description = ""
            subheading = cta.find(class_=lambda x: x and 'pagelayer-cta-subheading' in str(x))
            if subheading:
                description = clean_text(subheading.get_text())

            # Extract categories from badges
            categories = []
            badges = cta.find_all(class_=lambda x: x and 'pagelayer-badge' in str(x))
            for badge in badges:
                cat_text = clean_text(badge.get_text())
                if cat_text:
                    categories.append(cat_text)

            # Create slug
            slug = slugify(title)
            if not slug or len(slug) < 3:
                slug = f"video-{video_id}"

            # Download thumbnail
            thumbnail_filename = download_youtube_thumbnail(video_id, slug)

            # Create post data
            post_data = {
                'title': title,
                'slug': slug,
                'date': datetime.now().strftime('%Y-%m-%d'),  # Use current date
                'youtube_id': video_id,
                'youtube_url': video_url,
                'description': description,
                'categories': categories,
                'thumbnail_filename': thumbnail_filename
            }

            posts.append(post_data)

            print(f"  [{i+1}] {title}")
            print(f"      Video ID: {video_id}")
            print(f"      Categories: {', '.join(categories)}")

        # Also check service sections
        service_sections = soup.find_all('div', class_=lambda x: x and 'pagelayer-service' in str(x))

        print(f"\n  Checking {len(service_sections)} service sections...")

        for i, service in enumerate(service_sections):
            link = service.find('a', href=lambda x: x and ('youtube.com' in x or 'youtu.be' in x))
            if not link:
                continue

            video_url = link.get('href')
            video_id = extract_youtube_id(video_url)

            if not video_id:
                continue

            # Check if we already have this video
            if any(p['youtube_id'] == video_id for p in posts):
                continue

            # Extract title
            title = clean_text(link.get_text())
            if not title or title.lower() == 'click here':
                heading = service.find(class_=lambda x: x and 'pagelayer-service-heading' in str(x))
                if heading:
                    title = clean_text(heading.get_text())

            if not title or title.lower() == 'click here':
                title = f"Video {video_id}"

            # Extract description
            description = ""
            details = service.find(class_=lambda x: x and 'pagelayer-service-details' in str(x))
            if details:
                description = clean_text(details.get_text())

            # Extract categories
            categories = []
            badges = service.find_all(class_=lambda x: x and 'pagelayer-badge' in str(x))
            for badge in badges:
                cat_text = clean_text(badge.get_text())
                if cat_text:
                    categories.append(cat_text)

            # Create slug
            slug = slugify(title)
            if not slug or len(slug) < 3:
                slug = f"video-{video_id}"

            # Download thumbnail
            thumbnail_filename = download_youtube_thumbnail(video_id, slug)

            post_data = {
                'title': title,
                'slug': slug,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'youtube_id': video_id,
                'youtube_url': video_url,
                'description': description,
                'categories': categories,
                'thumbnail_filename': thumbnail_filename
            }

            posts.append(post_data)

            print(f"  [Service {i+1}] {title}")
            print(f"      Video ID: {video_id}")

        return posts

    except Exception as e:
        print(f"Error scraping video posts: {e}")
        import traceback
        traceback.print_exc()
        return []


def main():
    print("=" * 80)
    print("IIPMR YouTube Video Posts Scraper")
    print("=" * 80)

    # Scrape video posts
    posts = scrape_video_posts()

    if not posts:
        print("\nNo video posts found. Exiting.")
        return

    # Save all posts to JSON
    with open(POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"Scraping complete!")
    print(f"Scraped {len(posts)} video posts")
    print(f"Data saved to: {POSTS_FILE}")
    print(f"Thumbnails saved to: {IMAGES_DIR}")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
