import struct
base = 'c:/Users/alucardzhou/WorkBuddy/20260527101502/horror-intel-dashboard/docs/images/'
for n in ['czr-screenshot1.png', 'czr-screenshot2.png', 'czr-screenshot3.png', 'czr-banner.jpg', 'czr-icon.png']:
    path = base + n
    with open(path, 'rb') as f:
        data = f.read(24)
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            w, h = struct.unpack('>II', data[16:24])
            print(f'{n}: {w}x{h}')
        elif data[:2] == b'\xff\xd8':
            print(f'{n}: JPEG (need Pillow for dimensions)')
        else:
            print(f'{n}: unknown format')
