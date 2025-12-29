#!/usr/bin/env python3
"""
Transform scraped YouTube video posts to Hugo format
Converts the scraped JSON data into Hugo markdown posts
"""

import json
import os
import shutil
import re
from pathlib import Path

SCRAPED_DATA = "wordpress-scraped/posts.json"
SCRAPED_IMAGES = "wordpress-scraped/images"
HUGO_CONTENT = "content/posts"

# Category mapping to tags
CATEGORY_MAPPING = {
    "Supply Chain": "supply-chain",
    "Logistics": "logistics",
    "Artificial Intelligence": "artificial-intelligence",
    "AI": "artificial-intelligence",
    "Market Research": "market-research",
    "Warehousing": "warehousing",
    "Gaming": "gaming",
    "News": "news",
    "Industry Updates": "industry-updates",
    "Sustainability": "sustainability",
    "Automation": "automation",
    "Digital Transformation": "digital-transformation",
}


def slugify(text):
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')


def map_categories_to_tags(categories):
    """Map WordPress categories to Hugo tags"""
    tags = []
    for cat in categories:
        # Try exact match first
        if cat in CATEGORY_MAPPING:
            tags.append(CATEGORY_MAPPING[cat])
        else:
            # Try case-insensitive match
            for key, value in CATEGORY_MAPPING.items():
                if key.lower() == cat.lower():
                    tags.append(value)
                    break
            else:
                # If no mapping found, slugify the category
                tags.append(slugify(cat))

    # Remove duplicates and add a default tag
    tags = list(set(tags))
    if not tags:
        tags = ["video"]

    # Always add 'video' tag
    if "video" not in tags:
        tags.append("video")

    return tags


def transform_post(post_data):
    """Transform a single post to Hugo format"""
    title = post_data['title']
    slug = post_data['slug']
    date = post_data['date']
    youtube_id = post_data['youtube_id']
    description = post_data.get('description', '')
    categories = post_data.get('categories', [])
    thumbnail_filename = post_data.get('thumbnail_filename', '')

    print(f"Transforming: {title}")

    # Create post directory
    post_dir = os.path.join(HUGO_CONTENT, slug)
    os.makedirs(post_dir, exist_ok=True)

    # Map categories to tags
    tags = map_categories_to_tags(categories)

    # Create front matter
    front_matter = {
        'title': title,
        'date': date,
        'tags': tags,
    }

    # Add thumbnail as featured image if available
    if thumbnail_filename:
        front_matter['image'] = thumbnail_filename

        # Copy thumbnail to post directory
        src_image = os.path.join(SCRAPED_IMAGES, thumbnail_filename)
        if os.path.exists(src_image):
            dest_image = os.path.join(post_dir, thumbnail_filename)
            shutil.copy2(src_image, dest_image)
            print(f"  Copied thumbnail: {thumbnail_filename}")

    # Add description if available
    if description:
        front_matter['description'] = description

    # Create markdown content
    content_lines = []

    # Add description as content if available
    if description:
        content_lines.append(description)
        content_lines.append("")
        content_lines.append("---")
        content_lines.append("")

    # Add YouTube embed
    content_lines.append(f"{{{{< youtube {youtube_id} >}}}}")

    content = "\n".join(content_lines)

    # Write Hugo post
    post_file = os.path.join(post_dir, 'index.md')
    with open(post_file, 'w', encoding='utf-8') as f:
        # Write front matter
        f.write('---\n')
        for key, value in front_matter.items():
            if isinstance(value, list):
                # Format tags as YAML array
                tags_str = ", ".join(f'"{v}"' for v in value)
                f.write(f'{key}: [{tags_str}]\n')
            else:
                # Escape quotes in strings
                value_str = str(value).replace('"', '\\"')
                f.write(f'{key}: "{value_str}"\n')
        f.write('---\n\n')

        # Write content
        f.write(content)

    print(f"  Created: {post_file}")
    print(f"  Tags: {', '.join(tags)}")


def main():
    print("=" * 80)
    print("Transform Scraped Posts to Hugo Format")
    print("=" * 80)

    # Load scraped data
    if not os.path.exists(SCRAPED_DATA):
        print(f"Error: Scraped data not found at {SCRAPED_DATA}")
        print("Please run the scraper first: python3 scripts/scrape-youtube-posts.py")
        return

    with open(SCRAPED_DATA, 'r', encoding='utf-8') as f:
        posts = json.load(f)

    print(f"\nLoaded {len(posts)} posts from {SCRAPED_DATA}\n")

    # Create content directory if it doesn't exist
    os.makedirs(HUGO_CONTENT, exist_ok=True)

    # Transform each post
    for i, post in enumerate(posts, 1):
        print(f"\n[{i}/{len(posts)}]", end=" ")
        transform_post(post)

    print(f"\n{'='*80}")
    print(f"Transformation complete!")
    print(f"Created {len(posts)} Hugo posts in {HUGO_CONTENT}/")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
