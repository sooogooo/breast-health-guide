"""Build static sharing metadata from the page's own lead image, never navigation."""
from html import escape
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit
import json
import re
from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError

ORIGIN = 'https://breast.meilipai.vip'
FALLBACK = 'assets/logo-192.png'


def sync_share_metadata(text: str, path: Path, root: Path) -> str:
    """Update only the head; reject missing, tiny, external or opted-out leads."""
    root, path = root.resolve(), path.resolve()
    page_url = ORIGIN + '/' + quote(path.relative_to(root).as_posix())
    doc = BeautifulSoup(text, 'html.parser')
    title = doc.title.get_text(strip=True)
    description_tag = doc.select_one('meta[name="description"]')
    description = description_tag.get('content', '') if description_tag else ''
    lead = (doc.select_one('.lead-fig img') or doc.select_one('.category-hero img')
            or doc.select_one('.hero figure img'))
    image_path = root / FALLBACK
    image_url = ORIGIN + '/' + FALLBACK
    alt = 'AMC 标志 · 重庆西区医院医学美容中心'
    if lead and lead.get('src') and lead.get('data-share-image') != 'skip':
        candidate_url = urljoin(page_url, lead['src'])
        parsed = urlsplit(candidate_url)
        candidate = (root / unquote(parsed.path).lstrip('/')).resolve()
        if parsed.scheme == 'https' and parsed.netloc == urlsplit(ORIGIN).netloc and candidate.is_relative_to(root):
            try:
                with Image.open(candidate) as image:
                    suitable = image.format in ('JPEG', 'PNG') and image.width >= 300 and image.height >= 200
                    image.verify()
                if suitable:
                    image_path, image_url = candidate, candidate_url
                    alt = lead.get('alt') or title
            except (OSError, ValueError, UnidentifiedImageError):
                pass
    with Image.open(image_path) as image:
        width, height, mime = image.width, image.height, Image.MIME[image.format]
    og = {
        'og:type': 'article' if doc.select_one('article.page') else 'website',
        'og:site_name': '重庆西区医院医学美容中心',
        'og:locale': 'zh_CN',
        'og:title': title,
        'og:description': description,
        'og:url': page_url,
        'og:image': image_url,
        'og:image:secure_url': image_url,
        'og:image:type': mime,
        'og:image:width': str(width),
        'og:image:height': str(height),
        'og:image:alt': alt,
    }
    twitter = {
        'twitter:card': 'summary' if image_path == root / FALLBACK else 'summary_large_image',
        'twitter:title': title,
        'twitter:description': description,
        'twitter:image': image_url,
        'twitter:image:alt': alt,
    }
    metadata = ''.join(f'<meta property="{key}" content="{escape(value, quote=True)}">' for key, value in og.items())
    metadata += ''.join(f'<meta name="{key}" content="{escape(value, quote=True)}">' for key, value in twitter.items())
    metadata += f'<link rel="image_src" href="{escape(image_url, quote=True)}">'

    def update_head(match):
        head = match.group(0)
        head = re.sub(r'<meta\b[^>]*(?:property|name)=["\'](?:og:|twitter:)[^>]*>', '', head, flags=re.I)
        head = re.sub(r'<link\b[^>]*rel=["\']image_src["\'][^>]*>', '', head, flags=re.I)

        def update_schema(script):
            data = json.loads(script.group(2))
            if isinstance(data, dict) and data.get('@type') in ('Article', 'CollectionPage'):
                data['image'] = image_url
                payload = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
                return script.group(1) + payload + script.group(3)
            return script.group(0)

        head = re.sub(r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)', update_schema, head, flags=re.S | re.I)
        return re.sub(r'</head>', lambda _: metadata + '</head>', head, count=1, flags=re.I)

    return re.sub(r'<head\b[^>]*>.*?</head>', update_head, text, count=1, flags=re.S | re.I)
