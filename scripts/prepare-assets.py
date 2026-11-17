"""One-time asset preparation; not needed by production builds."""
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[1]
for width in (720,1440,1920):
    im=Image.open(root/'assets/ivy.jpg')
    im.thumbnail((width,width))
    im.save(root/f'assets/ivy-{width}.webp',quality=82)
