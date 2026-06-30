import urllib.request, re

url = 'https://www.taptap.cn/app/714123'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')

# Find __NUXT_DATA__
m = re.search(r'__NUXT_DATA__\s*=\s*(.*?)</script>', html, re.DOTALL)
if m:
    nuxt = m.group(1)
    imgs = re.findall(r'https?://[^\s"\\\]]+\.(?:jpg|png|webp|jpeg)', nuxt)
    for img in imgs[:30]:
        print(img)
else:
    print('No __NUXT_DATA__ found')
    imgs = re.findall(r'https?://img[^"\s]+\.(?:jpg|png|webp)', html)
    for img in imgs[:20]:
        print(img)
