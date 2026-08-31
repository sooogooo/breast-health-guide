"""Synchronize static shared UI and information pages without rewriting article content."""
from pathlib import Path
from html import escape
import re, json, hashlib
from bs4 import BeautifulSoup
from share_metadata import sync_share_metadata

ROOT=Path(__file__).resolve().parents[1]
VERSION='20260831-mobile1'
SECTIONS=[('index','首页'),('jichu','基础与美学'),('jiankang','健康护理'),('augmentation','隆胸科普'),('reduction','巨乳缩小'),('styling','日常美化穿搭'),('guide','就医指南')]
footer=(ROOT/'templates/footer.html').read_text('utf-8').strip()
home=(ROOT/'index.html').read_text('utf-8')
base_style=re.search(r'<style>(.*?)</style>',home,re.S)
if base_style:
    (ROOT/'assets/base.css').write_text(base_style[1]+'\n','utf-8',newline='\n')

def header(current):
    def navlinks(mobile=False):
        return ''.join(f'<a href="/{slug}.html"'+(' aria-current="page" class="cur"' if current==slug else '')+f'>{label}</a>' for slug,label in SECTIONS)
    return '<header class="header"><div class="header__in"><a class="brand" href="/index.html"><img src="/assets/logo.png?v=amc-20260830" width="34" height="34" alt="AMC"><span><span class="b1">重庆西区医院医学美容中心</span><span class="b2">认识胸部 · 科普系列</span></span></a><nav class="nav" aria-label="主要导航">'+navlinks()+'<button class="share-btn" type="button" data-share>分享</button></nav><details class="mobile-menu"><summary><span class="menu-glyph" aria-hidden="true">☰</span>专栏</summary><div class="mobile-menu-panel"><nav aria-label="手机专栏导航">'+navlinks(True)+'</nav><div class="menu-utilities"><a href="/privacy.html">隐私声明</a><button class="share-btn" type="button" data-share>分享此页</button></div></div></details></div></header>'

def shared_head():
    return f'<link rel="stylesheet" href="/assets/base.css?v={VERSION}"><link rel="stylesheet" href="/assets/visual.css?v={VERSION}"><link rel="stylesheet" href="/assets/mobile.css?v={VERSION}"><script defer src="/assets/visual.js?v={VERSION}"></script><script defer src="/assets/site.js?v={VERSION}"></script>'

icons=''.join(str(x) for x in BeautifulSoup(home,'html.parser').select('link[rel~=icon],link[rel="apple-touch-icon"]'))
def info_page(name,title,description,content):
    og=''
    return '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#faf8f4"><meta name="referrer" content="strict-origin-when-cross-origin"><title>'+escape(title)+' · 认识胸部</title><meta name="description" content="'+escape(description)+'">'+icons+og+shared_head()+'</head><body id="top"><a class="skip-link" href="#main-content">跳到主要内容</a>'+header(None)+content+footer+'<div class="share-status" role="status" aria-live="polite"></div></body></html>\n'

for name,title,description in [('privacy','隐私声明','本站的个人资料、页面功能、访问日志、外部链接与隐私联系说明。'),('open-source','开源说明','网站源码、MIT 代码许可、文章与素材边界，以及复用网站时需要注意的事项。')]:
    content=(ROOT/f'templates/{name}-content.html').read_text('utf-8')
    (ROOT/f'{name}.html').write_text(info_page(f'{name}.html',title,description,content),'utf-8',newline='\n')

error='<main class="container error-page" id="main-content"><p class="error-mark" aria-hidden="true">404</p><h1>这一页暂时找不到了</h1><p>链接可能已变更。你可以回到首页，或从专栏继续阅读。</p><div class="hero-actions"><a href="/index.html">返回首页</a><a href="/guide.html">查看就医指南</a></div></main>'
(ROOT/'404.html').write_text(info_page('404.html','页面未找到','返回认识胸部科普网站首页或选择其他专栏。',error),'utf-8',newline='\n')

paths=sorted(ROOT.glob('*.html'))+sorted(p for c,_ in SECTIONS[1:] for p in (ROOT/c).glob('*.html'))
for path in paths:
    if path.name in ('privacy.html','open-source.html','404.html'):continue
    text=path.read_text('utf-8')
    original=BeautifulSoup(text,'html.parser')
    text=re.sub(r'<style>.*?</style>','',text,flags=re.S)
    text=re.sub(r'<link[^>]*href="(?:\.\./)?/?assets/(?:base|visual|mobile)\.css[^>]*>','',text)
    text=re.sub(r'<script[^>]*src="(?:\.\./)?/?assets/(?:visual|site)\.js[^>]*>\s*</script>','',text)
    text=text.replace('</head>',shared_head()+'</head>')
    slug=path.parent.name if path.parent!=ROOT else path.stem
    text=re.sub(r'<header class="header">.*?</header>',lambda _:header(slug),text,count=1,flags=re.S)
    text=re.sub(r'<footer class="(?:foot|site-footer)">.*?</footer>',lambda _:footer,text,count=1,flags=re.S)
    text=re.sub(r'<script>function share\(\).*?</script>','',text,flags=re.S)
    text=re.sub(r'<div class="share-status".*?</div>','',text,flags=re.S)
    text=text.replace('</body>','<div class="share-status" role="status" aria-live="polite"></div></body>')
    updated=BeautifulSoup(text,'html.parser')
    assert updated.h1.get_text()==original.h1.get_text(),path
    assert updated.title.get_text()==original.title.get_text(),path
    if original.select_one('.prose'):
        assert str(updated.select_one('.prose'))==str(original.select_one('.prose')),path
    for selector in ('.art-card','.cat-card','.pn'):
        assert [str(x) for x in updated.select(selector)]==[str(x) for x in original.select(selector)],(path,selector)
    path.write_text(text,'utf-8',newline='\n')

for path in paths:
    text=path.read_text('utf-8')
    path.write_text(sync_share_metadata(text,path,ROOT),'utf-8',newline='\n')

sitemap=ROOT/'sitemap.xml'
xml=sitemap.read_text('utf-8')
for page in ('privacy.html','open-source.html'):
    if f'/{page}</loc>' not in xml:xml=xml.replace('</urlset>',f'  <url><loc>https://breast.meilipai.vip/{page}</loc></url>\n</urlset>')
sitemap.write_text(xml,'utf-8',newline='\n')
print(f'Synchronized {len(paths)} pages. Article text, card links and images preserved.')
