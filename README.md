# UFlinux website

English and Czech static website for UFlinux. Python 3.10+ builds full HTML documents, and HTMX 4.0.1 loaded from cdnjs progressively enhances internal links with mouseover preloading. Node.js 22+ runs the build-time minifiers.

## Build and preview

```sh
npm ci
python3 scripts/build.py
python3 -m http.server 8000 --directory dist
```

Production builds fetch the latest stable release. GitHub rate limits, server errors and connection failures use the maintained production snapshot in data/releases.json and log a warning. Invalid metadata still fails the build. For reproducible development without GitHub access:

```sh
python3 scripts/build.py --offline
python3 -m unittest discover -s tests -v
```

The offline fixture is for tests/development only. It is never a production fallback.

## Existing Cloudflare Pages project

Set framework preset to None, build command to `python3 scripts/build.py`, output directory to `dist`, and production branch to `main`. Set `PYTHON_VERSION=3.13` and `SITE_ORIGIN=https://uflinux.org` in Pages build environment variables. The existing Git integration builds source changes.

Create a deploy hook for the production branch in Pages → Settings → Builds & deployments → Deploy hooks. Store its URL in this GitHub repository's Actions secret `CLOUDFLARE_PAGES_DEPLOY_HOOK`. The hourly/manual Refresh release downloads workflow compares GitHub metadata against the deployed `/releases.json` and invokes the hook only when it differs. The workflow first refreshes and commits data/releases.json using its built-in GITHUB_TOKEN with contents: write permission, then checks the deployed catalog and triggers the hook. Missing or late-added board assets are detected. Repository branch rules must permit this bot push. No extra personal token is required. Review Actions failures for API or hook issues; scheduled workflows may need re-enabling after prolonged repository inactivity.

The canonical origin defaults to https://uflinux.org. Change it through `SITE_ORIGIN` in Pages and the release workflow together. Set your Cloudflare domain redirect from www to the apex; Pages preview deployments should have Cloudflare's normal noindex behavior.

## Structure and maintenance

- `scripts/build.py`: bilingual page rendering and static wizard graph.
- `scripts/releases.py`: shared release normalization and refresh checker.
- `assets/`: optimized wallpaper, CSS and site JS. HTMX core and its preload/head extensions use pinned cdnjs URLs with subresource integrity and deferred loading.
- `scripts/minify.mjs`: minifies generated HTML and local CSS, JavaScript, and SVG files. The Python generator writes compact release JSON and sitemap XML.
- `tests/`: offline release fixture and route/catalog tests.

The wizard only recommends recognized assets actually present in the latest stable release. Unknown ISO/disk images appear in the list without recommendation. Results are noindex and omitted from the sitemap. Language links use full navigation to update document language reliably. External image downloads never use HTMX or preloading.

Edit bilingual strings together in the generator. Images link directly to GitHub Releases; the guide and navbar link to docs.uflinux.org, with Czech documentation used for Czech pages. Hardware status copy should be reviewed when project support changes.

Artwork sources, adaptations, and licenses are credited on /credits/ and /cs/credits/. To recreate wallpaper assets, run `python3 scripts/prepare-assets.py` with Pillow installed; this is not needed for builds. Preserve the original Ivy JPEG as the source for those derivatives.

The main site hosts `/favicon.svg`, `/favicon.png`, and `/favicon.ico` for all three UFlinux sites. The build derives the SVG from the logo at 32 × 32 pixels. To regenerate the matching raster fallbacks, use ImageMagick.

```sh
magick -background none -density 192 assets/logo.svg -resize 32x32 -strip PNG32:assets/favicon.png
magick assets/favicon.png -strip assets/favicon.ico
```

## Performance verification

Check home, downloads and guide in both languages after deployment at pagespeed.web.dev. Target 95+ for performance, accessibility, best practices and SEO; no deployed score is claimed by the local build. Test no-JS navigation, keyboard focus, browser back/forward, language changes and hover requests before release.

## Cloudflare Fonts

Ubuntu uses a Google Fonts stylesheet link with display=swap, which Cloudflare Fonts rewrites at the edge to serve fonts from your own domain. Enable **Cloudflare Fonts** for uflinux.org under **Speed → Settings** in the Cloudflare dashboard. This zone setting cannot be enabled by a static build. Without it (including localhost and pages.dev previews), the stylesheet loads directly from Google Fonts. Czech characters are included automatically by the font stylesheet.

After deployment, inspect the custom-domain network requests to verify Cloudflare rewrites font delivery to same-origin URLs. Do not infer activation from a local preview. Documentation: https://developers.cloudflare.com/speed/optimization/content/fonts/

Assets keep their original filenames without content hashes or cache-busting parameters. Browsers may cache assets but must revalidate them before reuse. The language selector matches the documentation site: a native English/Čeština menu with translation and caret icons. It keeps the equivalent page or wizard step and provides a link fallback without JavaScript.

The build writes the minified stylesheet to `dist/assets/style.css`. Every document links to this stylesheet in the head, and HTMX keeps the loaded copy during navigation. The Ubuntu stylesheet loads with print media and switches to screen after loading, with display=swap. JavaScript-disabled browsers keep the system-font fallback and all navigation still works. Verify Cloudflare Fonts rewriting on the deployed custom domain.

The release status dot is green only when the build successfully fetches release metadata from GitHub. Snapshot fallback and offline builds use a neutral dot. This reflects the data source at build time, not a live browser connectivity check.

Open Graph metadata is rendered into every HTML document, including per-page title, description and canonical URL, English/Czech locale alternatives, image type/dimensions/alt text, and matching Twitter cards. The local 1200×630 JPEG preview is derived from Dark Ivy and inherits its CC BY-SA 3.0 license (see Credits). Regenerate it with scripts/prepare-assets.py; production builds do not need Pillow.

Interface icons use Font Awesome Free 7.3.1 from cdnjs (core, solid and regular styles only), pinned with SRI. Stylesheets load asynchronously; icon space is reserved and text labels remain usable without icon fonts. UFlinux branding and the native language selector uses language names.

Icon layout regression: with Playwright available to Node and `dist/` served locally, run `node tests/icon-layout.cjs`. It delays Font Awesome CSS and fonts separately, then compares icon and surrounding element positions on English/Czech, mobile/desktop, downloads and wizard pages. Set `SITE_URL` or `TEST_CHROMIUM` to override the server or browser. The icon containers reserve both width and height in inline CSS before any CDN resource arrives.
