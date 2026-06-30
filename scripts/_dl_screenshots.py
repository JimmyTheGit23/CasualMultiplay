import urllib.request

# 下载截图（不带_tap后缀的是原图）
screenshots = [
    ('https://img-tc.tapimg.com/market/images/11ac8d3f9adf2341ff78f995459fb381.png', 'czr-screenshot1.png'),
    ('https://img-tc.tapimg.com/market/images/717d2880d8b75b33056f1cb5a2dc537c.png', 'czr-screenshot2.png'),
    ('https://img-tc.tapimg.com/market/images/f27344f6eadd79417c3da54b9598fe2e.png', 'czr-screenshot3.png'),
]

for url, fname in screenshots:
    try:
        out = f'c:/Users/alucardzhou/WorkBuddy/20260527101502/horror-intel-dashboard/docs/images/{fname}'
        urllib.request.urlretrieve(url, out)
        import os
        size = os.path.getsize(out)
        print(f'{fname}: {size} bytes')
    except Exception as e:
        print(f'{fname}: FAILED - {e}')
