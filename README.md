# UFlinux website

English and Czech static website for UFlinux. Python 3.10+ builds full HTML documents; HTMX 4.0.1 progressively enhances internal links with mouseover preloading. No runtime backend, browser API calls, analytics, or npm dependencies.

## Build and preview

```sh
python3 scripts/build.py
python3 -m http.server 8000 --directory dist
```

Production builds fetch the latest published stable GitHub Release and fail on network or metadata errors, leaving the previous Cloudflare deployment intact. For reproducible development without GitHub access:

```sh
python3 scripts/build.py --offline
python3 -m unittest discover -s tests -v
```

The offline fixture is for tests/development only. It is never a production fallback.

## Existing Cloudflare Pages project

Set framework preset to None, build command to `python3 scripts/build.py`, output directory to `dist`, and production branch to `main`. Set `PYTHON_VERSION=3.13` and `SITE_ORIGIN=https://uflinux.org` in Pages build environment variables. The existing Git integration builds source changes.

Create a deploy hook for the production branch in Pages → Settings → Builds & deployments → Deploy hooks. Store its URL in this GitHub repository's Actions secret `CLOUDFLARE_PAGES_DEPLOY_HOOK`. The hourly/manual Refresh release downloads workflow compares GitHub metadata against the deployed `/releases.json` and invokes the hook only when it differs. Missing or late-added board assets are detected. No repository write token is required. Review Actions failures for API or hook issues; scheduled workflows may need re-enabling after prolonged repository inactivity.

The canonical origin defaults to https://uflinux.org. Change it through `SITE_ORIGIN` in Pages and the release workflow together. Set your Cloudflare domain redirect from www to the apex; Pages preview deployments should have Cloudflare's normal noindex behavior.

## Structure and maintenance

- `scripts/build.py`: bilingual page rendering and static wizard graph.
- `scripts/releases.py`: shared release normalization and refresh checker.
- `assets/`: optimized wallpaper, CSS, JS and pinned HTMX.
- `tests/`: offline release fixture and route/catalog tests.

The wizard only recommends recognized assets actually present in the latest stable release. Unknown ISO/disk images appear in the list without recommendation. Results are noindex and omitted from the sitemap. Language links use full navigation to update document language reliably. External image downloads never use HTMX or preloading.

Edit bilingual strings together in the generator. Images link directly to GitHub Releases; the guide links to documentation at the release tag. Hardware status copy should be reviewed when project support changes.

Artwork sources, adaptations, and licenses are credited on /credits/ and /cs/credits/. To recreate wallpaper assets, run `python3 scripts/prepare-assets.py` with Pillow installed; this is not needed for builds. Preserve the original Ivy JPEG as the source for those derivatives.

## Performance verification

Check home, downloads and guide in both languages after deployment at pagespeed.web.dev. Target 95+ for performance, accessibility, best practices and SEO; no deployed score is claimed by the local build. Test no-JS navigation, keyboard focus, browser back/forward, language changes and hover requests before release.

## Cloudflare Fonts

Ubuntu uses a Google Fonts stylesheet link with display=swap, which Cloudflare Fonts rewrites at the edge to serve fonts from your own domain. Enable **Cloudflare Fonts** for uflinux.org under **Speed → Settings** in the Cloudflare dashboard. This zone setting cannot be enabled by a static build. Without it (including localhost and pages.dev previews), the stylesheet loads directly from Google Fonts. Czech characters are included automatically by the font stylesheet.

After deployment, inspect the custom-domain network requests to verify Cloudflare rewrites font delivery to same-origin URLs. Do not infer activation from a local preview. Documentation: https://developers.cloudflare.com/speed/optimization/content/fonts/
