import json, subprocess, sys, unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from releases import normalize, ARCHES, TARGETS

class Document(HTMLParser):
    def __init__(self,text):
        super().__init__(); self.links=[]; self.ids=set(); self.lang=None; self.feed(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs: self.ids.add(attrs['id'])
        if tag=='html': self.lang=attrs.get('lang')
        for key in ('href','src'):
            if attrs.get(key,'').startswith('/'): self.links.append(attrs[key])

class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable,'scripts/build.py','--offline'],cwd=ROOT,check=True)
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
        raw={'tag_name':'v1.2.3','published_at':'2026-01-01','html_url':'https://github.com/UFlinux-project/uflinux3/releases/tag/v1.2.3','assets':[]}
        for name in ('uflinux-1.2.3-x86_64.iso','uflinux-1.2.3-rpi-aarch64.img.zst','custom.iso'):
            raw['assets'].append({'name':name,'size':123,'browser_download_url':'https://github.com/UFlinux-project/uflinux3/releases/download/v1.2.3/'+name})
        data=normalize(raw)
        self.assertEqual({a['key'] for a in data['assets']},{'x86_64','rpi',None})
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

    def test_sitemap_and_locales(self):
        import xml.etree.ElementTree as ET
        root=ET.parse(ROOT/'dist/sitemap.xml').getroot()
        locations=[x.text for x in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        self.assertEqual(len(locations),8)
        self.assertFalse(any('/image/' in x or '/choose/' in x for x in locations))
        for route in ('','downloads/','guide/','credits/'):
            en=(ROOT/f'dist/{route}index.html').read_text()
            cs=(ROOT/f'dist/cs/{route}index.html').read_text()
            self.assertIn('hreflang="cs"',en)
            self.assertIn('lang="cs"',cs)
if __name__=='__main__': unittest.main()
