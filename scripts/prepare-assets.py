"""One-time asset preparation; not needed by production builds."""
from pathlib import Path
from PIL import Image, ImageOps
root=Path(__file__).resolve().parents[1]
for width in (720,1440,1920):
    im=Image.open(root/'assets/ivy.jpg')
    im.thumbnail((width,width))
    im.save(root/f'assets/ivy-{width}.webp',quality=82)

# JPEG preview for social crawlers; prepared once, not during production builds.
preview=ImageOps.fit(Image.open(root/"assets/ivy.jpg").convert("RGB"),(1200,630),method=Image.Resampling.LANCZOS)
preview.save(root/"assets/og-image.jpg",quality=85,optimize=True)
