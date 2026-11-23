"""Shared, deterministic GitHub release normalization."""
import json, os, re, sys, urllib.request, urllib.error
from pathlib import Path
API = 'https://api.github.com/repos/UFlinux-project/uflinux/releases/latest'
REPO = 'https://github.com/UFlinux-project/uflinux'
ARCHES = ('x86_64','x86','aarch64','armv7','ppc64le','riscv64')
TARGETS = {'rpi':('Raspberry Pi 3 / 4 / 5','aarch64'), 'qcs6490':('Dragon Q6A / QCS6490','aarch64'), 'spacemit-k1':('SpacemiT K1 / Orange Pi RV2','riscv64'), 'vm-x86_64':('VM · Intel / AMD','x86_64'), 'vm-aarch64':('VM · ARM64','aarch64')}
def fetch(url):
    headers={'User-Agent':'UFlinux-website','Accept':'application/vnd.github+json'}
    if os.getenv('GITHUB_TOKEN') and url.startswith('https://api.github.com/'):
        headers['Authorization']='Bearer '+os.environ['GITHUB_TOKEN']
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as r:
        return json.load(r)
def normalize(raw):
    if raw.get('draft') or raw.get('prerelease') or not raw.get('tag_name'):
        raise ValueError('Expected a published stable release')
    assets=[]
    for a in raw['assets']:
        name=a['name']; url=a['browser_download_url']
        if not url.startswith(REPO+'/releases/download/'):
            raise ValueError('Unexpected release asset origin')
        key=None
        version=re.escape(raw['tag_name'].removeprefix('v'))
        for arch in ARCHES:
            if re.fullmatch(r'uflinux-'+version+'-'+arch+r'\.iso',name): key=arch
        for target,(_,arch) in TARGETS.items():
            device='vm' if target.startswith('vm-') else target
            if re.fullmatch(r'uflinux-'+version+'-'+device+'-'+arch+r'\.img\.zst',name): key=target
        assets.append({'name':name,'url':url,'size':a['size'],'key':key,'updated':a.get('updated_at'),'digest':a.get('digest')})
    return {'tag':raw['tag_name'],'published':raw['published_at'],'url':raw['html_url'],'assets':sorted(assets,key=lambda a:a['name'])}
def load_snapshot(path):
    saved=json.loads(Path(path).read_text())
    return normalize({'tag_name':saved['tag'],'published_at':saved['published'],
        'html_url':saved['url'],'assets':[dict(a, browser_download_url=a['url'],
        updated_at=a.get('updated')) for a in saved['assets']]})

def latest(snapshot):
    """Return the catalog and its build-time source without changing catalog JSON."""
    try:
        return normalize(fetch(API)), 'github'
    except urllib.error.HTTPError as error:
        if error.code not in (403,429) and error.code < 500: raise
        reason=f'GitHub HTTP {error.code}'
    except (urllib.error.URLError, TimeoutError) as error:
        reason=type(error).__name__
    saved=load_snapshot(snapshot)
    print(f'Warning: {reason}; using production release snapshot {saved["tag"]}.',file=sys.stderr)
    return saved, 'snapshot'

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--check',action='store_true'); p.add_argument('--snapshot',type=Path); args=p.parse_args()
    current=normalize(fetch(API))
    if args.snapshot:
        temporary=args.snapshot.with_suffix('.tmp')
        temporary.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n')
        temporary.replace(args.snapshot)
        print('Updated release snapshot:',current['tag'])
        sys.exit(0)
    if args.check:
        deployed=fetch(os.getenv('SITE_ORIGIN','https://uflinux.org').rstrip('/')+'/releases.json')
        if current!=deployed:
            hook=os.environ['CLOUDFLARE_PAGES_DEPLOY_HOOK']
            with urllib.request.urlopen(urllib.request.Request(hook,data=b'',method='POST'),timeout=30) as response:
                print('Triggered Cloudflare rebuild:',response.status)
        else: print('Release catalog unchanged')
    else: print(json.dumps(current,ensure_ascii=False,indent=2))
