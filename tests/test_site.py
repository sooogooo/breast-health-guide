"""Static site contracts. Run with python -m unittest discover -s tests -v."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
import unittest, re, hashlib
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PAGES = sorted(ROOT.glob('*.html')) + sorted(p for c in ('jichu','jiankang','augmentation','reduction','styling','guide') for p in (ROOT/c).glob('*.html'))

class SiteContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = {p:BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser') for p in PAGES}

    def test_new_policy_pages_exist(self):
        for name in ('privacy.html','open-source.html'):
            self.assertTrue((ROOT/name).is_file(),name)

    def test_footer_is_shared_on_every_page(self):
        variants=set()
        for p,s in self.docs.items():
            foot=s.select_one('footer.site-footer')
            self.assertIsNotNone(foot, p.name)
            variants.add(str(foot))
            text=foot.get_text(' ',strip=True)
            for phrase in ('京ICP备20009050号-2','© 2026 美学实验室 | 美丽派','sooogooo@139.com','@sooogooo'):
                self.assertIn(phrase,text,p.name)
            links={a.get('href') for a in foot.select('a')}
            for href in ('https://beian.miit.gov.cn/','/privacy.html','/open-source.html','https://github.com/sooogooo/breast-health-guide','mailto:sooogooo@139.com'):
                self.assertIn(href,links,p.name)
        self.assertEqual(len(variants),1)

    def test_mobile_menu_has_all_sections_without_javascript(self):
        for p,s in self.docs.items():
            menu=s.select_one('details.mobile-menu')
            self.assertIsNotNone(menu,p.name)
            self.assertIsNotNone(menu.select_one('summary'),p.name)
            hrefs={a.get('href') for a in menu.select('nav a')}
            self.assertTrue({'/index.html','/jichu.html','/jiankang.html','/augmentation.html','/reduction.html','/styling.html','/guide.html'}.issubset(hrefs),p.name)

    def test_all_local_links_assets_and_anchors_exist(self):
        for p,s in self.docs.items():
            ids=[e['id'] for e in s.select('[id]')]
            self.assertEqual(len(ids),len(set(ids)),p.name)
            for e in s.select('a[href],link[href],img[src],script[src],source[srcset]'):
                value=e.get('href') or e.get('src') or e.get('srcset')
                if not value: continue
                for item in value.split(',') if e.name=='source' else [value]:
                    u=urlsplit(item.strip().split(' ')[0])
                    if u.scheme or u.netloc: continue
                    dest=(ROOT/unquote(u.path).lstrip('/')) if u.path.startswith('/') else (p.parent/unquote(u.path)).resolve()
                    if not u.path:dest=p
                    self.assertTrue(dest.exists(),f'{p.name} -> {value}')
                    if u.fragment and dest==p:self.assertIn(u.fragment,ids,p.name)

    def test_brand_and_editorial_constraints(self):
        for p,s in self.docs.items():
            self.assertIsNotNone(s.select_one('link[rel~=icon]'),p.name)
            self.assertIsNotNone(s.select_one('.brand img'),p.name)
            for h in s.select('h1,h2,h3,.at,.ct'):
                self.assertNotRegex(h.get_text(),r'[:：]',p.name)
            self.assertNotIn('三甲',s.get_text(),p.name)

    def test_all_existing_article_entries_keep_images(self):
        counts={'.art-card':0,'.pn a':0,'.cat-card':0}
        for s in self.docs.values():
            for selector in counts:
                for card in s.select(selector):
                    counts[selector]+=1
                    self.assertEqual(len(card.select('img')),1)
        self.assertEqual(counts,{'.art-card':166,'.pn a':68,'.cat-card':6})

    def test_privacy_follows_actual_site_behavior(self):
        p=ROOT/'privacy.html'
        self.assertTrue(p.exists())
        text=BeautifulSoup(p.read_text('utf-8'),'html.parser').get_text()
        for phrase in ('访问日志','IP','Cookie','浏览器','主动联系','GitHub'):
            self.assertIn(phrase,text)
        for s in self.docs.values():self.assertFalse(s.select('form'))

    def test_license_scope_is_explicit(self):
        for file in ('LICENSE','CONTENT-LICENSE.md','README.md'):
            self.assertTrue((ROOT/file).exists(),file)
        self.assertIn('MIT License',(ROOT/'LICENSE').read_text('utf-8'))
        self.assertIn('标志',(ROOT/'CONTENT-LICENSE.md').read_text('utf-8'))

    def test_common_styles_and_share_status(self):
        for p,s in self.docs.items():
            self.assertFalse(s.select('style'),p.name)
            self.assertIsNotNone(s.select_one('link[href*="mobile.css"]'),p.name)
            self.assertIsNotNone(s.select_one('script[src*="site.js"]'),p.name)
            self.assertIsNotNone(s.select_one('[role="status"]'),p.name)
            self.assertFalse(s.select('[onclick]'),p.name)

if __name__=='__main__':unittest.main()
