# Whale Knowledge Base Documentation

This directory contains the complete documentation for Whale Knowledge Base, ready to be published via GitHub Pages.

## Documentation Structure

- [**index.md**](index.md) - Main landing page with overview
- [**getting-started.md**](getting-started.md) - Quick start guide and installation
- [**api-reference.md**](api-reference.md) - Complete API documentation
- [**mcp-integration.md**](mcp-integration.md) - MCP server integration guide
- [**architecture.md**](architecture.md) - System architecture and design
- [**deployment.md**](deployment.md) - Production deployment guide
- [**configuration.md**](configuration.md) - Configuration reference

## Publishing to GitHub Pages

### Option 1: Using GitHub Settings (Recommended)

1. **Push to GitHub:**
   ```bash
   git add docs/
   git commit -m "Add comprehensive documentation"
   git push origin main
   ```

2. **Enable GitHub Pages:**
   - Go to your repository on GitHub
   - Navigate to Settings → Pages
   - Under "Source", select:
     - Branch: `main`
     - Folder: `/docs`
   - Click "Save"

3. **Wait for deployment:**
   - GitHub will build and deploy your site
   - Access it at: `https://your-username.github.io/whale-knowledge/`

### Option 2: Using GitHub Actions

Create `.github/workflows/deploy-docs.yml`:

```yaml
name: Deploy Documentation

on:
  push:
    branches:
      - main
    paths:
      - 'docs/**'

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Pages
        uses: actions/configure-pages@v3

      - name: Build with Jekyll
        uses: actions/jekyll-build-pages@v1
        with:
          source: ./docs
          destination: ./_site

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v2

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v2
```

### Option 3: Custom Domain

If you have a custom domain:

1. Add a `CNAME` file in the `docs/` directory:
   ```bash
   echo "docs.yourdomain.com" > docs/CNAME
   ```

2. Configure your DNS:
   ```
   CNAME docs.yourdomain.com → your-username.github.io
   ```

3. Update GitHub Pages settings to use custom domain

## Theme Customization

The documentation uses the Cayman theme. To customize:

### Change Theme

Edit `docs/_config.yml`:

```yaml
theme: jekyll-theme-minimal  # or other themes
# Options: cayman, minimal, slate, architect, etc.
```

### Custom Styling

Create `docs/assets/css/style.scss`:

```scss
---
---

@import "{{ site.theme }}";

/* Custom styles */
.main-content {
  max-width: 1200px;
}

code {
  background-color: #f6f8fa;
  padding: 0.2em 0.4em;
  border-radius: 3px;
}
```

### Navigation Menu

Create `docs/_layouts/default.html`:

```html
<!DOCTYPE html>
<html lang="{{ site.lang | default: "en-US" }}">
  <head>
    <meta charset="UTF-8">
    <title>{{ page.title | default: site.title }}</title>
  </head>
  <body>
    <header>
      <nav>
        <a href="index.html">Home</a>
        <a href="getting-started.html">Getting Started</a>
        <a href="api-reference.html">API</a>
        <a href="mcp-integration.html">MCP</a>
        <a href="architecture.html">Architecture</a>
        <a href="deployment.html">Deployment</a>
        <a href="configuration.html">Configuration</a>
      </nav>
    </header>
    <main>
      {{ content }}
    </main>
  </body>
</html>
```

## Local Preview

### Using Jekyll Locally

```bash
# Install Jekyll
gem install bundler jekyll

# Create Gemfile in docs/
cd docs
cat > Gemfile <<EOF
source "https://rubygems.org"
gem "github-pages", group: :jekyll_plugins
gem "jekyll-theme-cayman"
EOF

# Install dependencies
bundle install

# Serve locally
bundle exec jekyll serve

# Open http://localhost:4000
```

### Using Python HTTP Server

```bash
# Serve static files (limited functionality)
cd docs
python -m http.server 8000

# Open http://localhost:8000
```

### Using Docker

```bash
# Run Jekyll in Docker
docker run --rm \
  --volume="$PWD/docs:/srv/jekyll" \
  --publish 4000:4000 \
  jekyll/jekyll \
  jekyll serve
```

## Documentation Maintenance

### Adding New Pages

1. Create new markdown file in `docs/`:
   ```bash
   touch docs/new-page.md
   ```

2. Add front matter:
   ```markdown
   ---
   title: New Page Title
   description: Page description
   ---

   # Content here
   ```

3. Link from other pages:
   ```markdown
   [New Page](new-page.md)
   ```

### Updating Existing Pages

1. Edit the markdown file
2. Commit and push changes
3. GitHub Pages will automatically rebuild

### Adding Images

1. Create assets directory:
   ```bash
   mkdir -p docs/assets/images
   ```

2. Add images:
   ```bash
   cp screenshot.png docs/assets/images/
   ```

3. Reference in markdown:
   ```markdown
   ![Screenshot](assets/images/screenshot.png)
   ```

## SEO Optimization

Add to `_config.yml`:

```yaml
title: Whale Knowledge Base
description: Production-ready RAG system with MCP integration
author: Your Name
url: https://your-username.github.io
baseurl: /whale-knowledge

# SEO
lang: en-US
twitter:
  username: your_twitter
  card: summary_large_image
social:
  name: Your Name
  links:
    - https://twitter.com/your_twitter
    - https://github.com/your-username

# Analytics (optional)
google_analytics: UA-XXXXXXXXX-X
```

## Troubleshooting

### Build Failures

**Check build status:**
- Go to Actions tab on GitHub
- Look for failed builds
- Check error messages

**Common issues:**
- Invalid YAML in `_config.yml`
- Missing front matter in markdown files
- Broken links

### Page Not Found

**Verify:**
1. GitHub Pages is enabled
2. Correct branch and folder selected
3. Index file exists (`index.md` or `index.html`)
4. Wait 1-2 minutes for deployment

### Styling Issues

**Clear cache:**
```bash
# Add cache-busting parameter
?v=20240115
```

**Check theme:**
```bash
# Verify theme is installed
bundle list | grep jekyll-theme
```

## Resources

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Jekyll Documentation](https://jekyllrb.com/docs/)
- [Markdown Guide](https://www.markdownguide.org/)
- [GitHub Pages Themes](https://pages.github.com/themes/)

## Support

For documentation issues:
- [Open an Issue](https://github.com/your-org/whale-knowledge/issues)
- [Submit a PR](https://github.com/your-org/whale-knowledge/pulls)
