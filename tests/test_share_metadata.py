"""Per-page sharing contracts, including missing/unsuitable lead images."""
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
from importlib import import_module, util
import json
import unittest
from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://breast.meilipai.vip'
FALLBACK = ORIGIN + '/assets/logo-192.png'
PAGES = sorted(p for p in ROOT.rglob('*.html') if 'templates' not in p.parts)


class SharingContracts(unittest.TestCase):
    def test_concurrent_google_verification_is_preserved_in_head(self):
        doc = BeautifulSoup((ROOT/'index.html').read_text('utf-8'), 'html.parser')
        self.assertIsNotNone(doc.head.select_one('meta[name="google-site-verification"]'))

    def test_every_page_shares_its_lead_or_new_amc_logo(self):
        article_images = []
        for path in PAGES:
            with self.subTest(page=path.relative_to(ROOT).as_posix()):
                doc = BeautifulSoup(path.read_text('utf-8'), 'html.parser')
                lead = doc.select_one('.lead-fig img, .category-hero img, .hero figure img')
                expected = urljoin(ORIGIN + '/' + path.relative_to(ROOT).as_posix(), lead['src']) if lead else FALLBACK
                self.assertEqual(doc.select_one('meta[property="og:image"]')['content'], expected)
                self.assertEqual(doc.select_one('meta[name="twitter:image"]')['content'], expected)
                if doc.select_one('.lead-fig img'):
                    article_images.append(expected)
        self.assertEqual(len(article_images), 40)
        self.assertEqual(len(set(article_images)), 40)

    def test_metadata_is_consistent_with_real_image_files(self):
        for path in PAGES:
            with self.subTest(page=path.name):
                doc = BeautifulSoup(path.read_text('utf-8'), 'html.parser')
                for name in ('og:image', 'og:image:secure_url', 'og:image:type', 'og:image:width', 'og:image:height', 'og:image:alt', 'og:type', 'og:title', 'og:description', 'og:url'):
                    self.assertEqual(len(doc.select(f'meta[property="{name}"]')), 1, name)
                image_url = doc.select_one('meta[property="og:image"]')['content']
                self.assertTrue(image_url.startswith(ORIGIN + '/assets/'))
                self.assertNotIn('share-card', image_url)
                with Image.open(ROOT / unquote(urlsplit(image_url).path).lstrip('/')) as image:
                    self.assertEqual(doc.select_one('meta[property="og:image:width"]')['content'], str(image.width))
                    self.assertEqual(doc.select_one('meta[property="og:image:height"]')['content'], str(image.height))
                    self.assertEqual(doc.select_one('meta[property="og:image:type"]')['content'], Image.MIME[image.format])
                self.assertEqual(doc.select_one('meta[property="og:image:secure_url"]')['content'], image_url)
                self.assertEqual(doc.select_one('link[rel="image_src"]')['href'], image_url)
                self.assertEqual(doc.select_one('meta[name="twitter:image:alt"]')['content'], doc.select_one('meta[property="og:image:alt"]')['content'])
                for script in doc.select('script[type="application/ld+json"]'):
                    data = json.loads(script.string)
                    if data.get('@type') in ('Article', 'CollectionPage'):
                        self.assertEqual(data['image'], image_url)
                expected_card = 'summary' if image_url == FALLBACK else 'summary_large_image'
                self.assertEqual(doc.select_one('meta[name="twitter:card"]')['content'], expected_card)

    def generator(self):
        self.assertIsNotNone(util.find_spec('scripts.share_metadata'), 'A reusable sharing metadata generator is required')
        return import_module('scripts.share_metadata')

    def test_invalid_or_absent_lead_uses_logo_not_navigation_image(self):
        module = self.generator()
        variants = [
            '',
            '<figure class="lead-fig"><img src="/assets/missing.jpg"></figure>',
            '<figure class="lead-fig"><img src="/assets/favicon-16.png"></figure>',
            '<figure class="lead-fig"><img src="https://example.org/photo.jpg"></figure>',
            '<figure class="lead-fig"><img src="../../outside.jpg"></figure>',
            '<figure class="lead-fig"><img src="/assets/img/hero.jpg" data-share-image="skip"></figure>',
        ]
        for lead in variants:
            with self.subTest(lead=lead):
                html = '<html><head><title>Example</title><meta name="description" content="Example summary"></head><body><header><img src="/assets/logo.png"></header>' + lead + '<a class="art-card"><img src="/assets/img/hero.jpg"></a></body></html>'
                result = module.sync_share_metadata(html, ROOT/'index.html', ROOT)
                doc = BeautifulSoup(result, 'html.parser')
                self.assertEqual(doc.select_one('meta[property="og:image"]')['content'], FALLBACK)
                self.assertEqual(result.split('<body>')[1], html.split('<body>')[1])
                self.assertEqual(module.sync_share_metadata(result, ROOT/'index.html', ROOT), result)

    def test_relative_lead_is_resolved_and_stale_metadata_removed(self):
        module = self.generator()
        html = '<html><head><title>A &amp; B</title><meta name="description" content="A &quot;quote&quot;"><meta property="og:image" content="old"><meta name="twitter:image" content="old"></head><body><figure class="lead-fig"><img src="../assets/img/hero.jpg" width="1" height="1" alt="A &amp; B"></figure></body></html>'
        result = module.sync_share_metadata(html, ROOT/'guide/example.html', ROOT)
        doc = BeautifulSoup(result, 'html.parser')
        self.assertEqual(doc.select_one('meta[property="og:image"]')['content'], ORIGIN + '/assets/img/hero.jpg')
        self.assertEqual(len(doc.select('meta[property="og:image"]')), 1)
        self.assertEqual(doc.select_one('meta[property="og:image:width"]')['content'], '1672')
        self.assertEqual(doc.select_one('meta[property="og:title"]')['content'], 'A & B')
        self.assertEqual(doc.select_one('meta[property="og:description"]')['content'], 'A "quote"')
        self.assertNotIn('content="old"', result)
        self.assertEqual(module.sync_share_metadata(result, ROOT/'guide/example.html', ROOT), result)


if __name__ == '__main__':
    unittest.main()
