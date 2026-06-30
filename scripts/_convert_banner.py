from PIL import Image
import os

base = 'c:/Users/alucardzhou/WorkBuddy/20260527101502/horror-intel-dashboard/docs/images/'

# Convert screenshot1 PNG to JPEG for banner
img = Image.open(base + 'czr-screenshot1.png')
# Resize to 1280 width for web optimization
w, h = img.size
new_w = 1280
new_h = int(h * new_w / w)
img_resized = img.resize((new_w, new_h), Image.LANCZOS)
img_resized.convert('RGB').save(base + 'czr-banner-new.jpg', 'JPEG', quality=80)
size = os.path.getsize(base + 'czr-banner-new.jpg')
print(f'czr-banner-new.jpg: {new_w}x{new_h}, {size} bytes ({size/1024:.0f}KB)')

# Also convert icon to smaller size
icon = Image.open(base + 'czr-icon.png')
icon_resized = icon.resize((128, 128), Image.LANCZOS)
icon_resized.save(base + 'czr-icon-sm.png', 'PNG', optimize=True)
size2 = os.path.getsize(base + 'czr-icon-sm.png')
print(f'czr-icon-sm.png: 128x128, {size2} bytes ({size2/1024:.0f}KB)')
