# IIPMR Blog - Hugo Site

This is the Hugo-based blog for the International Institute for Procurement and Market Research (IIPMR), migrated from WordPress.

## Overview

The site features educational video content on supply chain management, logistics, procurement, and market research. All content consists of YouTube video embeds with descriptions and categorization.

## Features

- **19 Video Posts** covering topics like:
  - Supply Chain Management
  - Logistics Optimization
  - AI and Automation
  - Sustainability
  - Warehouse Productivity
- **BlogRa Theme** - clean, modern Hugo theme optimized for technical blogging
- **YouTube Integration** - all videos embedded using Hugo shortcodes
- **Responsive Design** - mobile-friendly layout
- **Tag-based Organization** - content organized by topics
- **GitHub Pages Deployment** - automated CI/CD via GitHub Actions

## Local Development

### Prerequisites

- Hugo Extended (v0.102.3 or higher)
- Git

### Running Locally

```bash
# Start the development server
hugo server -D

# Build the site
hugo

# The site will be available at http://localhost:1313/blog/
```

## Deployment

The site is configured for automatic deployment to GitHub Pages using GitHub Actions.

### Setup GitHub Pages

1. Push this repository to GitHub
2. Go to repository Settings → Pages
3. Set Source to "GitHub Actions"
4. The site will automatically deploy on every push to main

### Update Base URL

After deploying, update the `baseURL` in `config.toml` with your actual GitHub Pages URL:

```toml
baseURL = "https://YOUR_GITHUB_USERNAME.github.io/blog/"
```

## Directory Structure

```
.
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions deployment workflow
├── content/
│   ├── posts/                  # Blog posts (YouTube videos)
│   ├── about/                  # About page
│   └── contact/                # Contact page
├── themes/
│   └── BlogRa/                 # Hugo theme
├── static/
│   └── images/                 # Static images
├── scripts/
│   ├── scrape-youtube-posts.py    # Web scraper for WordPress videos
│   └── transform-to-hugo.py       # Conversion script to Hugo format
├── config.toml                 # Hugo configuration
└── README.md                   # This file
```

## Migration Details

The migration was performed by:

1. **Scraping** the WordPress blog at https://iipmr.com/blog/
2. **Extracting** YouTube video information (titles, categories, descriptions)
3. **Downloading** video thumbnails from YouTube
4. **Converting** to Hugo markdown format with proper front matter
5. **Embedding** videos using Hugo's YouTube shortcode

### Technologies Used

- **Hugo** - Static site generator
- **BlogRa Theme** - Modern Hugo blogging theme
- **Python** - Scraping and transformation scripts
- **BeautifulSoup** - HTML parsing
- **GitHub Actions** - CI/CD automation

## Content Management

### Adding New Videos

To add a new video post:

1. Create a new folder in `content/posts/` with a descriptive slug
2. Add `index.md` with front matter:

```markdown
---
title: "Your Video Title"
date: 2025-01-15
tags: ["supply-chain", "logistics", "video"]
image: "thumbnail.jpg"
description: "Brief description of the video"
---

Video description or introduction text.

{{< youtube VIDEO_ID >}}
```

3. Add the video thumbnail image to the same folder

### Customization

- **Theme Settings**: Edit `config.toml` to customize site title, description, social media links, etc.
- **Menu**: Update the `[menu]` section in `config.toml`
- **Colors/Styling**: Customize BlogRa theme in `themes/BlogRa/assets/`

## License

The content is property of IIPMR. The Hugo framework and BlogRa theme have their own respective licenses.

## Contact

For questions about this site or IIPMR programs:
- Email: contact@iipmr.com
- Website: https://iipmr.com

