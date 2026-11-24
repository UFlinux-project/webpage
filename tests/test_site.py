import json, re, subprocess, sys, unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from releases import normalize, ARCHES, TARGETS

class Document(HTMLParser):
    def __init__(self,text):
        super().__init__(); self.links=[]; self.ids=set(); self.lang=None; self.metadata={}; self.canonical=None; self.alternates={}; self.icons=[]; self.feed(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs: self.ids.add(attrs['id'])
        if tag=='html': self.lang=attrs.get('lang')
        if tag=='meta': self.metadata[attrs.get('property',attrs.get('name'))]=attrs.get('content')
        if tag=='link' and attrs.get('rel')=='canonical': self.canonical=attrs.get('href')
        if tag=='link' and attrs.get('rel')=='alternate': self.alternates[attrs.get('hreflang')]=attrs.get('href')
        if tag=='link' and 'icon' in attrs.get('rel','').split():
            self.icons.append((attrs.get('href'),attrs.get('type'),attrs.get('sizes')))
        for key in ('href','src'):
            if attrs.get(key,'').startswith('/'): self.links.append(attrs[key])

class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable,'scripts/build.py','--offline'],cwd=ROOT,check=True)
    def test_build_minifies_local_assets(self):
        out=ROOT/'dist'
        for name in ('assets/style.css','assets/site.js','assets/logo.svg'):
            with self.subTest(asset=name):
                self.assertLess((out/name).stat().st_size,(ROOT/name).stat().st_size)
        catalog=(out/'releases.json').read_text()
        self.assertEqual(catalog,json.dumps(json.loads(catalog),ensure_ascii=False,separators=(',',':')))
        self.assertNotIn('\n',(out/'index.html').read_text())

    def test_pages_link_to_one_stylesheet(self):
        out=ROOT/'dist'
        for file in out.rglob('*.html'):
            text=file.read_text()
            self.assertEqual(Document(text).links.count('/assets/style.css'),1,str(file))
            self.assertNotIn('<style',text,str(file))

    def test_favicon_preference_on_every_page(self):
        expected=[
            ('/favicon.ico','image/vnd.microsoft.icon','32x32'),
            ('/favicon.png','image/png','32x32'),
            ('/favicon.svg','image/svg+xml','any'),
        ]
        for file in (ROOT/'dist').rglob('*.html'):
            self.assertEqual(Document(file.read_text()).icons,expected,str(file))

    def test_local_links_and_anchors(self):
        out=ROOT/'dist'
        for file in out.rglob('*.html'):
            doc=Document(file.read_text())
            self.assertIn(doc.lang,('en','cs'))
            for link in doc.links:
                parsed=urlsplit(link); target=out/unquote(parsed.path).lstrip('/')
                if parsed.path.endswith('/'): target=target/'index.html'
                self.assertTrue(target.is_file(),f'{file}: {link}')
                if parsed.fragment and target.suffix=='.html':
                    self.assertIn(parsed.fragment,Document(target.read_text()).ids)
    def test_x86_64_iso_is_the_first_download(self):
        data=json.loads((ROOT/'tests/release-fixture.json').read_text())
        iso=next(item['name'] for item in data['assets'] if item['key']=='x86_64')
        for lang in ('','cs/'):
            text=(ROOT/f'dist/{lang}downloads/index.html').read_text()
            first_download=text.split('<article class=download-row>',1)[1].split('</article>',1)[0]
            self.assertIn(iso,first_download)

    def test_every_image_has_one_recommendation(self):
        data=json.loads((ROOT/'tests/release-fixture.json').read_text())
        keys=[x['key'] for x in data['assets'] if x['key']]
        self.assertEqual(set(keys),set(ARCHES)|set(TARGETS))
        self.assertEqual(len(keys),len(set(keys)))
        for lang in ('','cs/'):
            for key in keys:
                text=(ROOT/f'dist/{lang}downloads/image/{key}/index.html').read_text()
                item=next(a for a in data['assets'] if a['key']==key)
                self.assertIn(item['url'],text)
                self.assertIn('noindex,follow',text)
    def test_normalization_and_unknown_variants(self):
        raw={'tag_name':'v1.2.3','published_at':'2026-01-01','html_url':'https://github.com/UFlinux-project/uflinux/releases/tag/v1.2.3','assets':[]}
        for name in ('uflinux-1.2.3-x86_64.iso','uflinux-1.2.3-rpi-aarch64.img.zst','custom.iso',
                     'uflinux-1.2.3-x86.iso','uflinux-1.2.3-armv7.iso',
                     'uflinux-1.2.3-pc-xfs-x86.img.zst','uflinux-1.2.3-pc-xfs-x86.img.zst.sha256'):
            raw['assets'].append({'name':name,'size':123,'browser_download_url':'https://github.com/UFlinux-project/uflinux/releases/download/v1.2.3/'+name})
        data=normalize(raw)
        self.assertEqual({a['key'] for a in data['assets']},{'x86_64','rpi',None})
        self.assertEqual({a['name'] for a in data['assets']},
                         {'uflinux-1.2.3-x86_64.iso','uflinux-1.2.3-rpi-aarch64.img.zst','custom.iso'})
        raw['prerelease']=True
        with self.assertRaises(ValueError): normalize(raw)
    def test_catalog_deterministic_and_rejects_foreign_urls(self):
        raw={'tag_name':'v1','published_at':'date','html_url':'url','assets':[{'name':'file','size':1,'browser_download_url':'https://evil.example/file'}]}
        with self.assertRaises(ValueError): normalize(raw)
    def test_missing_image_and_late_asset(self):
        from unittest.mock import patch
        import runpy
        fixture=ROOT/'tests/release-fixture.json'
        original_read=Path.read_text
        catalog=json.loads(fixture.read_text())
        late=next(a for a in catalog['assets'] if a['key']=='rpi')
        catalog['assets'].remove(late)
        def read(path,*args,**kwargs):
            return json.dumps(catalog) if path==fixture else original_read(path,*args,**kwargs)
        with patch.object(Path,'read_text',read), patch.object(sys,'argv',['build.py','--offline']):
            runpy.run_path(str(ROOT/'scripts/build.py'),run_name='__main__')
        result=ROOT/'dist/downloads/image/rpi/index.html'
        self.assertIn('Unavailable in this release',result.read_text())
        self.assertNotIn(late['url'],result.read_text())
        subprocess.run([sys.executable,'scripts/build.py','--offline'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        self.assertIn(late['url'],result.read_text())

    def test_failed_fetch_preserves_existing_output(self):
        from unittest.mock import patch
        import runpy
        before=(ROOT/'dist/index.html').read_bytes()
        with patch('releases.fetch',side_effect=ValueError('Invalid release metadata')), patch.object(sys,'argv',['build.py']):
            with self.assertRaises(ValueError):
                runpy.run_path(str(ROOT/'scripts/build.py'),run_name='__main__')
        self.assertEqual(before,(ROOT/'dist/index.html').read_bytes())

    def test_rate_limit_uses_production_snapshot(self):
        from unittest.mock import patch
        from urllib.error import HTTPError
        from releases import latest, load_snapshot
        snapshot=ROOT/'data/releases.json'
        for code in (403,429,503):
            with patch('releases.fetch',side_effect=HTTPError('https://api.github.com/',code,'unavailable',{},None)):
                self.assertEqual(latest(snapshot),(load_snapshot(snapshot),'snapshot'))
        with patch('releases.fetch',side_effect=TimeoutError()):
            self.assertEqual(latest(snapshot),(load_snapshot(snapshot),'snapshot'))
        with patch('releases.fetch',side_effect=HTTPError('https://api.github.com/',401,'unauthorized',{},None)):
            with self.assertRaises(HTTPError): latest(snapshot)

    def test_release_status_matches_build_source(self):
        from unittest.mock import patch
        import runpy
        saved=json.loads((ROOT/'data/releases.json').read_text())
        raw={'tag_name':saved['tag'],'published_at':saved['published'],'html_url':saved['url'],
             'assets':[dict(a,browser_download_url=a['url'],updated_at=a.get('updated')) for a in saved['assets']]}
        try:
            for failed in (False,True):
                mock={'side_effect':TimeoutError()} if failed else {'return_value':raw}
                with patch('releases.fetch',**mock), patch.object(sys,'argv',['build.py']):
                    runpy.run_path(str(ROOT/'scripts/build.py'),run_name='__main__')
                for prefix in ('','cs/'):
                    text=(ROOT/f'dist/{prefix}index.html').read_text()
                    self.assertEqual('class="status-dot status-dot-github"' in text,not failed)
                    self.assertIn('Saved release information' if failed else 'Release information from GitHub',
                                  (ROOT/'dist/index.html').read_text())
        finally:
            subprocess.run([sys.executable,'scripts/build.py','--offline'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        self.assertNotIn('class="status-dot status-dot-github"',(ROOT/'dist/index.html').read_text())

    def test_open_graph_metadata(self):
        from urllib.parse import urlsplit
        for file in (ROOT/'dist').rglob('*.html'):
            doc=Document(file.read_text())
            meta=doc.metadata
            for key in ('og:title','og:description','og:type','og:url','og:image',
                        'og:site_name','og:locale','og:locale:alternate','og:image:alt'):
                self.assertTrue(meta.get(key),f'{file}: missing {key}')
            self.assertEqual(meta['og:url'],doc.canonical)
            self.assertEqual(meta['og:locale'],'cs_CZ' if doc.lang=='cs' else 'en_GB')
            self.assertEqual(meta['og:locale:alternate'],'en_GB' if doc.lang=='cs' else 'cs_CZ')
            self.assertEqual(meta['og:image:type'],'image/jpeg')
            self.assertEqual((meta['og:image:width'],meta['og:image:height']),('1200','630'))
            self.assertEqual(meta['og:image'],meta['twitter:image'])
            self.assertEqual(meta['og:title'],meta['twitter:title'])
            self.assertEqual(meta['og:description'],meta['description'])
            image=ROOT/'dist'/urlsplit(meta['og:image']).path.lstrip('/')
            self.assertEqual(image.read_bytes()[:2],b'\xff\xd8')

    def test_sitemap_and_locales(self):
        import xml.etree.ElementTree as ET
        root=ET.parse(ROOT/'dist/sitemap.xml').getroot()
        locations=[x.text for x in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        self.assertEqual(len(locations),8)
        self.assertFalse(any('/image/' in x or '/choose/' in x for x in locations))
        for route in ('','downloads/','guide/','credits/'):
            en=Document((ROOT/f'dist/{route}index.html').read_text())
            cs=Document((ROOT/f'dist/cs/{route}index.html').read_text())
            self.assertEqual(en.alternates['cs'],cs.canonical)
            self.assertEqual(cs.lang,'cs')

    def test_structured_data_matches_indexable_pages(self):
        out=ROOT/'dist'
        version=json.loads((out/'releases.json').read_text())['tag']
        for file in out.rglob('*.html'):
            with self.subTest(page=file.relative_to(out)):
                text=file.read_text()
                doc=Document(text)
                scripts=re.findall(r'<script type="?application/ld\+json"?>(.*?)</script>',text,re.S)
                if 'noindex' in doc.metadata.get('robots',''):
                    self.assertEqual(scripts,[])
                    continue
                self.assertEqual(len(scripts),1)
                data=json.loads(scripts[0])
                self.assertEqual(data['@context'],'https://schema.org')
                graph={node['@type']:node for node in data['@graph']}
                prefix='cs/' if doc.lang=='cs' else ''
                home=file == out/f'{prefix}index.html'
                downloads=file == out/f'{prefix}downloads/index.html'
                page=graph['CollectionPage' if downloads else 'WebPage']
                self.assertEqual(page['url'],doc.canonical)
                self.assertEqual(page['description'],doc.metadata['description'])
                self.assertEqual(page['inLanguage'],doc.lang)
                self.assertEqual('WebSite' in graph,home)
                self.assertEqual('SoftwareApplication' in graph,home or downloads)
                if home:
                    self.assertEqual(page['isPartOf']['@id'],graph['WebSite']['@id'])
                if home or downloads:
                    software=graph['SoftwareApplication']
                    self.assertEqual(page['mainEntity']['@id'],software['@id'])
                    self.assertEqual(software['softwareVersion'],version)
                    self.assertEqual(urlsplit(software['downloadUrl']).path,f'/{prefix}downloads/')

if __name__=='__main__': unittest.main()
