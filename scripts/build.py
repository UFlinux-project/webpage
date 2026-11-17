"""Build complete static documents. Builds use live release metadata or a maintained production snapshot."""
import html, json, os, shutil, sys
from pathlib import Path
from releases import ARCHES, REPO, TARGETS, latest
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'
origin=os.getenv('SITE_ORIGIN','https://uflinux.org').rstrip('/')
if '--offline' in sys.argv:
    catalog=json.loads((ROOT/'tests/release-fixture.json').read_text())
    catalog_source='snapshot'
else:
    catalog,catalog_source=latest(ROOT/'data/releases.json')
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()
shutil.copytree(ROOT/'assets',OUT/'assets',ignore=shutil.ignore_patterns('ivy.jpg'))
# Keep original asset filenames and stable URLs across builds.
asset={'/'+file.relative_to(OUT).as_posix(): file for file in (OUT/'assets').rglob('*') if file.is_file()}
def a(path):
    url='/assets/'+path
    if url not in asset: raise FileNotFoundError(path)
    return url
def esc(s): return html.escape(str(s),quote=True)
def icon(name,style='solid'):
    return f'<i class="fa-{style} fa-{name}" aria-hidden="true"></i>'
sitemap=[]
def render(lang,route,title,description,body,index=True):
    cs=lang=='cs'
    def tr(en,cz): return cz if cs else en
    prefix='/cs' if cs else ''
    url=prefix+route
    alt=route if cs else '/cs'+route
    nav=[('/',tr('Overview','Přehled')),('/downloads/',tr('Downloads','Ke stažení')),('/guide/',tr('Get started','Začínáme'))]
    docs_origin='https://docs.uflinux.org'+('/cs/' if cs else '/')
    navhtml=''.join(f'<a href="{prefix+p}"'+(' aria-current="page"' if route==p else '')+f'>{label}</a>' for p,label in nav)+f'<a href="{docs_origin}" hx-boost="false">{tr("Documentation","Dokumentace")} ↗</a>'
    document=f"""<!doctype html>
<html lang="{lang}" prefix="og: https://ogp.me/ns#"><head hx-head="merge">
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · UFlinux</title><meta name="description" content="{esc(description)}">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebSite","name":"UFlinux","url":"{origin}/","inLanguage":["en","cs"]}}</script>
<meta name="theme-color" content="#191919"><meta name="color-scheme" content="dark">
<link rel="canonical" href="{origin}{url}">
<link rel="alternate" hreflang="en" href="{origin}{route}"><link rel="alternate" hreflang="cs" href="{origin}/cs{route}">
<link rel="alternate" hreflang="x-default" href="{origin}{route}">
<meta property="og:title" content="{esc(title)} · UFlinux"><meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website"><meta property="og:url" content="{origin}{url}">
<meta property="og:site_name" content="UFlinux">
<meta property="og:locale" content="{'cs_CZ' if cs else 'en_GB'}"><meta property="og:locale:alternate" content="{'en_GB' if cs else 'cs_CZ'}">
<meta property="og:image" content="{origin}{a('og-image.jpg')}">
<meta property="og:image:type" content="image/jpeg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{tr('Dark Ivy wallpaper: dark leaves with water droplets','Tapeta Dark Ivy: tmavé listy s kapkami vody')}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)} · UFlinux">
<meta name="twitter:description" content="{esc(description)}"><meta name="twitter:image" content="{origin}{a('og-image.jpg')}">
<meta name="twitter:image:alt" content="{tr('Dark Ivy wallpaper: dark leaves with water droplets','Tapeta Dark Ivy: tmavé listy s kapkami vody')}">
<link rel="icon" href="{a('logo.svg')}" type="image/svg+xml">
<style>{(ROOT/'assets/site.css').read_text()}</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Ubuntu:wght@400;500;700&amp;display=swap" media="print" onload="&quot;use strict&quot;; this.onload=null; this.media='all';" hx-preserve="true" id="ubuntu-fonts">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/7.3.1/css/fontawesome.min.css" integrity="sha384-m8DKa0MtZAZlyNgF18TSkQRYTPDY0sEELpwK2YijfYnVFH8kxiaO6hvopM168nue" crossorigin="anonymous" media="print" onload="&quot;use strict&quot;; this.onload=null; this.media='all';" hx-preserve="true" id="fa-fontawesome">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/7.3.1/css/solid.min.css" integrity="sha384-p/nJzgOJxEnSeUkMQ0nk5oPsUT5x8eOWi6pxU2ls9qcO9B78dCvZk0JSAOXWXUQN" crossorigin="anonymous" media="print" onload="&quot;use strict&quot;; this.onload=null; this.media='all';" hx-preserve="true" id="fa-solid">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/7.3.1/css/regular.min.css" integrity="sha384-2RNNQHI9yrjVDjr8zReHCzBa25B4jlokRSel4Cnp9s+PCUDvwxBq8ZbIODO51CZL" crossorigin="anonymous" media="print" onload="&quot;use strict&quot;; this.onload=null; this.media='all';" hx-preserve="true" id="fa-regular">
<meta name="htmx-config" content='{{"allowEval":false,"allowScriptTags":false,"preload":{{"autoBoost":false}}}}'>
{'' if index else '<meta name="robots" content="noindex,follow">'}
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/htmx/4.0.1/htmx.min.js" integrity="sha384-Qp9rdC8H7EqOoX+nR0P3RPG2Noji+qdwJlGpfzwQJsfOpp3sGwIdSP9xO3+UlEhn" crossorigin="anonymous"></script><script defer src="https://cdnjs.cloudflare.com/ajax/libs/htmx/4.0.1/ext/hx-preload.min.js" integrity="sha384-7gaXKgQyxJfh9ekNnYPYQ27fsBHx1Qgya7sMCEFLlsW57R8l6rEnCWO8ucRcmYrP" crossorigin="anonymous"></script>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/htmx/4.0.1/ext/hx-head.min.js" integrity="sha384-mvnUtszG0CziW1z/k9JYg2OpRWyy4FOsdzv9SINg91JArmMOAfzy0+xvC0wnFEBy" crossorigin="anonymous"></script><script defer src="{a('site.js')}"></script>
</head><body>
<a class="skip" href="#main">{tr('Skip to content','Přejít k obsahu')}</a>
<div id="page" data-language="{lang}" hx-history-elt hx-boost:inherited="true" hx-target:inherited="#page" hx-select:inherited="#page" hx-swap:inherited="outerHTML" hx-preload:inherited="mouseover">
<header class="header"><a class="brand" href="{prefix}/"><img src="{a('logo.svg')}" width="35" height="35" alt=""><span class="wordmark">UFlinux.</span></a>
<nav aria-label="{tr('Main navigation','Hlavní navigace')}">{navhtml}</nav>
<a class="language" href="{alt}" hreflang="{'en' if cs else 'cs'}" lang="{'en' if cs else 'cs'}" hx-boost="false" aria-label="{tr('Switch language to Czech','Přepnout jazyk na angličtinu')}"><span class="language-flag" aria-hidden="true">{'🇬🇧' if cs else '🇨🇿'}</span>{'EN' if cs else 'CZ'} ↗</a></header>
<main id="main" tabindex="-1">{body}</main>
<footer><div><a class="brand" href="{prefix}/"><span class="wordmark">UFlinux.</span></a><p>{tr('A small system. Room for your ideas.','Malý systém. Prostor pro vaše nápady.')}</p></div>
<div class="footer-links"><a href="{REPO}" hx-boost="false">GitHub ↗</a><a href="{REPO}/issues" hx-boost="false">{tr('Report an issue','Nahlásit chybu')} ↗</a>
<a href="{prefix}/credits/">{tr('Artwork & licenses','Autoři a licence')}</a></div><small>© {tr('UFlinux contributors','Přispěvatelé UFlinux')} · {tr('Built in the open.','Vyvíjeno otevřeně.')}</small></footer>
</div></body></html>"""
    # Keep source translations readable; replace decorative symbols at render time.
    document=document.replace(' ↓</a>',' '+icon('download')+'</a>')
    for symbol,name in (('↗','arrow-up-right-from-square'),('↓','arrow-down'),('←','arrow-left'),('◐','circle-half-stroke')):
        document=document.replace(symbol,icon(name))
    destination=OUT/url.lstrip('/')/'index.html'
    destination.parent.mkdir(parents=True,exist_ok=True); destination.write_text(document.replace('hx-boost="false"', 'hx-boost="false" hx-preload=""'))
    if index: sitemap.append(url)

def build_language(lang):
    cs=lang=='cs'; pre='/cs' if cs else ''
    def t(en,cz): return cz if cs else en
    def link(route,label,cls='button'):
        return f'<a class="{cls}" href="{pre}{route}">{label}</a>'
    def intro(kicker,title,text):
        return f'<section class="intro"><p class="eyebrow">{kicker}</p><h1>{title}</h1><p class="lead">{text}</p></section>'
    def page(route,title,text,body,index=True): render(lang,route,title,text,body,index)
    def options(items):
        return '<div class="options">'+''.join(link(route,f'<span>{label}<small>{hint}</small></span><span aria-hidden="true">↗</span>','option') for route,label,hint in items)+'</div>'
    def step(route,title,items,back='/downloads/choose/'):
        text=t('Choose the hardware you will run UFlinux on.','Vyberte hardware, na kterém bude UFlinux běžet.')
        body=intro(t('IMAGE SELECTOR','VÝBĚR OBRAZU'),title,text)+options(items)
        body+=f'<div class="step-footer">{link(back,t("← Back","← Zpět"),"text-link")}{link("/downloads/choose/",t("Start again","Začít znovu"),"text-link")}{link("/downloads/#images",t("Browse all images","Všechny obrazy"),"text-link")}</div>'
        page(route,title,text,body,False)
    release=esc(catalog['tag'])
    home=f"""<section class="hero">
<picture><source srcset="{a('ivy-720.webp')} 720w, {a('ivy-1440.webp')} 1440w, {a('ivy-1920.webp')} 1920w" sizes="100vw" type="image/webp"><img class="hero-image" src="{a('ivy-1440.webp')}" alt="" width="1920" height="1200" fetchpriority="high"></picture>
<div class="hero-content"><a class="release-pill" href="{pre}/downloads/"><span class="status-dot{' status-dot-github' if catalog_source=='github' else ''}" role="img" aria-label="{t('Release information from GitHub','Informace o vydání z GitHubu') if catalog_source=='github' else t('Saved release information','Uložené informace o vydání')}" title="{t('Release information from GitHub','Informace o vydání z GitHubu') if catalog_source=='github' else t('Saved release information','Uložené informace o vydání')}"></span>{release} <span> / </span>{t('Available now','Právě k dispozici')} ↗</a>
<h1>{t('Less noise.<br>More Linux.','Méně rozptylování.<br>Více Linuxu.')}</h1>
<p>{t('A minimal Alpine Linux desktop. Familiar on the surface. Refreshingly simple underneath.','Minimalistický desktop založený na Alpine Linuxu. Známé prostředí. Osvěžující jednoduchost uvnitř.')}</p>
<div class="actions">{link('/downloads/choose/',t('Find your image','Najít vhodný obraz')+' <span aria-hidden="true">↗</span>')}{link('/downloads/#images',t('Browse downloads','Vše ke stažení'),'button secondary')}</div>
</div><div class="hero-bottom"><span>ALPINE LINUX / LABWC / WAYLAND</span><span>{t('Made to feel at home.','Abyste se cítili jako doma.')} ↓</span></div></section>
<section class="section"><div class="section-heading"><p class="eyebrow">{t('THE DESKTOP, RECONSIDERED','DESKTOP JINAK')}</p><h2>{t('Everything in its place.','Všechno na svém místě.')}</h2><p>{t('A focused desktop with the tools you reach for every day.','Přehledný desktop s nástroji, které potřebujete každý den.')}</p></div>
<div class="features"><article><span class="feature-number">01 /</span><h3>{t('A familiar rhythm','Známý rytmus')}</h3><p>{t('A taskbar, an application menu, and window controls that get out of your way. Powered by the labwc Wayland compositor.','Hlavní panel, nabídka aplikací a ovládání oken, které nepřekáží. Základem je Wayland kompozitor labwc.')}</p></article>
<article><span class="feature-number">02 /</span><h3>{t('Small at the core','Malý v základu')}</h3><p>{t('Built on Alpine Linux with OpenRC and APK package management. A straightforward foundation you can make your own.','Postaveno na Alpine Linuxu s OpenRC a správou balíčků APK. Jednoduchý základ, který si přizpůsobíte.')}</p></article>
<article><span class="feature-number">03 /</span><h3>{t('Ready for the everyday','Pro každý den')}</h3><p>{t('Firefox, a file manager, media tools, and system settings. A consistent dark theme ties it all together.','Firefox, správce souborů, multimediální nástroje a nastavení systému. Vše spojuje jednotný tmavý vzhled.')}</p></article></div></section>
<section class="callout"><div><p class="eyebrow">{t('YOUR NEXT BOOT','VAŠE PŘÍŠTÍ SPUŠTĚNÍ')}</p><h2>{t('Different hardware.<br>Same quiet confidence.','Různý hardware.<br>Stejný klid.')}</h2><p>{t('PCs, virtual machines, and selected single-board computers. Let us help you choose the right starting point.','PC, virtuální stroje i vybrané jednodeskové počítače. Pomůžeme vám vybrat správný začátek.')}</p>{link('/downloads/choose/',t('Choose your image','Vybrat obraz')+' ↗')}</div>
<div class="system-card"><div class="window-bar"><span aria-hidden="true"></span><b>UFlinux</b><div class="window-controls" aria-hidden="true"><span class="window-control">{icon('minus')}</span><span class="window-control">{icon('square','regular')}</span><span class="window-control close">{icon('xmark')}</span></div></div><div class="system-body"><img src="{a('logo.svg')}" width="76" height="76" alt="" loading="lazy"><h3>{t('Simple by design.','Jednoduchost záměrem.')}</h3><p>Alpine Linux + labwc</p><div class="system-row"><span>{t('Appearance','Vzhled')}</span><span>{t('Dark','Tmavý')} ◐</span></div><div class="system-row"><span>{t('Your system','Váš systém')}</span><span>{t('Your choice','Vaše volba')} ↗</span></div></div></div></section>"""
    page('/',t('A minimal Alpine Linux desktop','Minimalistický desktop s Alpine Linuxem'),t('Discover UFlinux, a minimal Alpine Linux desktop with labwc. Download images for PCs, virtual machines and selected boards.','Objevte UFlinux, minimalistický desktop s Alpine Linuxem a labwc. Stáhněte obrazy pro PC, virtuální stroje a vybrané desky.'),home)
    def asset_card(item):
        name=esc(item['name']); size=f"{item['size']/1024**3:.2f} GiB"
        key=item['key']; label=TARGETS[key][0] if key in TARGETS else (key or name)
        experimental=key in ('qcs6490','spacemit-k1')
        checksum=next((x for x in catalog['assets'] if x['name']==item['name']+'.sha256'),None)
        if name.endswith('.iso'): checksum=next((x for x in catalog['assets'] if x['name']=='SHA256SUMS'),None)
        return f'<article class="download-row"><div><h3>{esc(label)}</h3><p class="filename">{name}</p><small>{size} · {"ISO" if name.endswith(".iso") else "IMG · Zstandard"}{(" · "+t("Experimental","Experimentální")) if experimental else ""}</small></div><div class="download-actions"><a class="button compact" href="{esc(item["url"])}" hx-boost="false">{t("Download","Stáhnout")} ↓</a>'+ (f'<a href="{esc(checksum["url"])}" hx-boost="false">SHA-256 ↗</a>' if checksum else '')+'</div></article>'
    images=[x for x in catalog['assets'] if x['name'].endswith(('.iso','.img.zst'))]
    download=intro(t('DOWNLOAD UFLINUX','STÁHNOUT UFLINUX'),t('Your hardware. Your Linux.','Váš hardware. Váš Linux.'),t('Find the right image, or go straight to the complete list.','Najděte správný obraz, nebo přejděte rovnou na úplný seznam.'))
    download+=f'<div class="wizard-banner"><div><p class="eyebrow">{t("A LITTLE GUIDANCE","MALÁ NÁPOVĚDA")}</p><h2>{t("Not sure where to start?","Nevíte, kde začít?")}</h2><p>{t("A few hardware questions. One matching image.","Několik otázek o hardwaru. Jeden vhodný obraz.")}</p></div>{link("/downloads/choose/",t("Find my image","Najít můj obraz")+" ↗")}</div>'
    download+=f'<section class="section" id="images"><div class="list-heading"><h2>{t("All images","Všechny obrazy")}</h2><a href="{esc(catalog["url"])}" hx-boost="false">{release} · {t("Release notes","Poznámky k vydání")} ↗</a></div>'
    for suffix,title in [('.iso',t('Live / installer ISOs','Živé / instalační ISO')),('.img.zst',t('Installed board & VM images','Předinstalované obrazy pro desky a VM'))]:
        download+=f'<h3 class="group-title">{title}</h3>'+''.join(asset_card(x) for x in images if x['name'].endswith(suffix))
    download+=f'<p class="note">{t("Only the x86_64 ISO has configured BIOS and UEFI VM boot tests. Other architectures and board images have different validation coverage. CPU architecture alone does not guarantee device compatibility.","Pouze ISO x86_64 má nastavené testy spuštění v BIOS a UEFI VM. Ostatní architektury a obrazy desek mají jiné pokrytí testy. Samotná architektura procesoru nezaručuje kompatibilitu zařízení.")}</p><div class="actions">{link("/guide/",t("Verification & installation guide","Ověření a instalace"),"text-link")}<a href="{REPO}/releases" hx-boost="false">{t("Older releases","Starší vydání")} ↗</a></div></section>'
    page('/downloads/',t('Downloads','Ke stažení'),t('Download UFlinux ISO and disk images. Choose by architecture and device, with checksum links and an image selection wizard.','Stáhněte ISO a diskové obrazy UFlinuxu podle architektury a zařízení. Kontrolní součty a průvodce výběrem obrazu.'),download)
    step('/downloads/choose/',t('Where will you run it?','Kde ho budete používat?'),[
        ('/downloads/choose/pc/',t('PC or laptop','PC nebo notebook'),'Intel / AMD'),
        ('/downloads/choose/vm/',t('Virtual machine','Virtuální stroj'),'QEMU / KVM / UEFI'),
        ('/downloads/choose/board/',t('Single-board computer','Jednodeskový počítač'),'Raspberry Pi / QCS6490 / SpacemiT'),
        ('/downloads/choose/other/',t('Other hardware / I’m not sure','Jiný hardware / Nevím'),t('Architecture help','Nápověda k architektuře'))],'/downloads/')
    result=lambda key:'/downloads/image/'+key+'/'
    step('/downloads/choose/pc/',t('Which processor does it use?','Jaký procesor používá?'),[(result('x86_64'),'Intel / AMD · 64-bit',t('Most modern PCs and laptops','Většina moderních PC a notebooků')),(result('x86'),'Intel / AMD · 32-bit',t('Older x86 computers','Starší počítače x86')),('/downloads/choose/other/',t('I’m not sure','Nevím'),t('How to check your architecture','Jak zjistit architekturu'))])
    step('/downloads/choose/vm/',t('Which guest architecture?','Jaká je architektura virtuálního stroje?'),[('/downloads/choose/vm/'+arch+'/',label,t('Match the guest configuration, not the browser','Podle nastavení VM, nikoli prohlížeče')) for arch,label in [('x86_64','Intel / AMD · x86_64'),('aarch64','ARM64 · aarch64')]])
    for arch in ('x86_64','aarch64'):
        step('/downloads/choose/vm/'+arch+'/',t('How would you like to start?','Jak chcete začít?'),[(result(arch),t('Live desktop / installer','Živý desktop / instalátor'),'ISO'),(result('vm-'+arch),t('Installed virtual disk','Předinstalovaný virtuální disk'),'IMG · Zstandard · UEFI')],'/downloads/choose/vm/')
    step('/downloads/choose/board/',t('Which board do you have?','Jakou desku máte?'),[(result(key),label,t('Experimental','Experimentální') if key!='rpi' else 'ARM64') for key,(label,_) in TARGETS.items() if not key.startswith('vm-')]+[('/downloads/choose/other/',t('Another board / I’m not sure','Jiná deska / Nevím'),t('Check firmware requirements first','Nejprve ověřte požadavky firmwaru'))])
    step('/downloads/choose/other/',t('Check the target architecture.','Ověřte cílovou architekturu.'),[(result(arch),arch,t('Generic ISO · compatible firmware required','Obecné ISO · vyžaduje kompatibilní firmware')) for arch in ARCHES])
    # Add concrete help to the architecture selection document.
    helpfile=OUT/(pre+'/downloads/choose/other/').lstrip('/')/'index.html'
    helptext=t('On Linux, run uname -m. On Windows, open Settings → System → About → System type. ARM and RISC-V boards need compatible firmware; a matching CPU is not enough. If uncertain, check the project hardware guide before downloading.','V Linuxu spusťte uname -m. Ve Windows otevřete Nastavení → Systém → O systému → Typ systému. Desky ARM a RISC-V potřebují kompatibilní firmware; shodný procesor nestačí. Pokud si nejste jisti, ověřte zařízení v dokumentaci projektu.')
    helpfile.write_text(helpfile.read_text().replace('<div class="options">',f'<p class="note">{helptext}</p><div class="options">',1))
    for key in (*ARCHES,*TARGETS):
        item=next((x for x in images if x['key']==key),None)
        label=TARGETS[key][0] if key in TARGETS else key
        text=t('This image matches your selected device and architecture.','Tento obraz odpovídá vybranému zařízení a architektuře.')
        body=intro(t('YOUR MATCH','VÁŠ VÝBĚR'),esc(label),text)
        body+='<div class="result-panel">'+(asset_card(item) if item else f'<h2>{t("Unavailable in this release","V tomto vydání není k dispozici")}</h2>')+'</div>'
        body+=f'<p class="note">{t("Board images contain device-specific boot files. Generic ISOs require compatible firmware. Review the release documentation and verify the checksum before use.","Obrazy desek obsahují specifické spouštěcí soubory. Obecné ISO vyžaduje kompatibilní firmware. Před použitím si přečtěte dokumentaci vydání a ověřte kontrolní součet.")}</p>'
        if key in ('qcs6490','spacemit-k1'):
            body+=f'<p class="note">{t("Experimental technology preview. Physical hardware and display support are limited; SpacemiT K1 may require a serial console.","Experimentální technologická ukázka. Podpora fyzického hardwaru a obrazu je omezená; SpacemiT K1 může vyžadovat sériovou konzoli.")}</p>'
        body+=f'<div class="actions">{link("/guide/",t("Read the setup guide","Přečíst průvodce instalací"))}{link("/downloads/choose/",t("Start again","Začít znovu"),"text-link")}{link("/downloads/#images",t("All images","Všechny obrazy"),"text-link")}</div>'
        page(result(key),t('Recommended image','Doporučený obraz')+' · '+label,text,body,False)
    docs='https://docs.uflinux.org'+('/cs/' if cs else '/')
    guide=intro(t('GET STARTED','ZAČÍNÁME'),t('A good first boot.','První spuštění bez tápání.'),t('Choose carefully. Verify your download. Follow the documentation for your device.','Vybírejte pečlivě. Ověřte stažený soubor. Postupujte podle dokumentace svého zařízení.'))
    for number,title,text,url in [
        ('01',t('Choose the right image','Vyberte správný obraz'),t('Use a live ISO for a compatible computer or an installer VM. Use the dedicated installed disk image for a listed board or a UEFI VM.','Pro kompatibilní počítač nebo instalační VM použijte živé ISO. Pro uvedené desky nebo UEFI VM použijte příslušný předinstalovaný diskový obraz.'),docs+'reference/architectures/'),
        ('02',t('Verify before writing','Před zápisem ověřte soubor'),t('Download SHA256SUMS for ISOs, or the .sha256 sidecar for disk images, from the same release. Run sha256sum -c with the checksum file in the download directory. Review GitHub artifact attestations as well.','Stáhněte SHA256SUMS pro ISO nebo soubor .sha256 pro diskový obraz ze stejného vydání. Ve složce se staženým obrazem spusťte sha256sum -c se souborem kontrolních součtů. Ověřte také atestace artefaktů GitHubu.'),catalog['url']),
        ('03',t('Prepare your media','Připravte médium'),t('Back up the target drive. Writing an image replaces its contents. Disk images must be decompressed from Zstandard first. Confirm the exact device and follow the release guide; Secure Boot signatures are not supplied.','Zálohujte cílový disk. Zápis obrazu nahradí jeho obsah. Diskové obrazy nejprve rozbalte ze Zstandardu. Ověřte přesné cílové zařízení a postupujte podle dokumentace vydání; podpisy pro Secure Boot nejsou dodávány.'),docs+'devices/'),
        ('04',t('Install and make it yours','Nainstalujte a přizpůsobte'),t('ISO installation and board-image first boot follow different procedures. Read the documentation for partition requirements, login details, account setup and updates.','Instalace z ISO a první spuštění obrazu desky mají odlišný postup. Požadavky na oddíly, přihlašovací údaje, nastavení účtu a aktualizace najdete v dokumentaci svého zařízení.'),docs+'installing/')]:
        guide+=f'<article class="guide-step"><span class="feature-number">{number} /</span><div><h2>{title}</h2><p>{text}</p><a href="{esc(url)}" hx-boost="false">{t("Read documentation","Dokumentace")} ↗</a></div></article>'
    page('/guide/',t('Getting started','Začínáme'),t('Verify your UFlinux download and follow the installation instructions for your device and release.','Ověřte stažený UFlinux a postupujte podle instalačních pokynů pro své zařízení a vydání.'),guide)
    credits=intro(t('CREDITS','AUTOŘI'),t('Built on shared work.','Postaveno na společné práci.'),t('Thank you to the people behind the project and its artwork.','Děkujeme lidem, kteří tvoří projekt a jeho vzhled.'))
    credits+=f'<div class="prose"><p>Dark Ivy — Garrett LeSage / GNOME, <a href="https://creativecommons.org/licenses/by-sa/3.0/" hx-boost="false">CC BY-SA 3.0</a>. {t("Resized and converted to WebP for this site; derivatives retain the same license.","Pro tento web zmenšeno a převedeno do WebP; odvozené obrazy zachovávají stejnou licenci.")} <a href="https://github.com/GNOME/gnome-backgrounds/tree/3.38.0" hx-boost="false">{t("Original source","Původní zdroj")} ↗</a></p><p>UFlinux logo — UFlinux project, GPL-3.0-only. {t("Leaf and stem merged into one continuous vector silhouette; original circular badge retained.","List a stonek sloučeny do jedné souvislé vektorové siluety; původní kruhový znak zachován.")} <a href="{a("LOGO-LICENSE.txt")}" hx-boost="false">GPL-3.0</a> · <a href="https://docs.uflinux.org{'/cs' if cs else ''}/developer/artwork-and-licenses/" hx-boost="false">{t("Source and attribution","Zdroj a autorství")}</a></p><p>Ubuntu — Canonical Ltd., <a href="/assets/fonts/LICENSE.txt" hx-boost="false">Ubuntu Font Licence</a>.</p><p>Font Awesome Free 7.3.1 — <a href="https://fontawesome.com/license/free" hx-boost="false">SIL OFL 1.1 / MIT / CC BY 4.0</a>.</p><p>HTMX 4.0.1 — <a href="{a("vendor/LICENSE.txt")}" hx-boost="false">Zero-Clause BSD</a>.</p></div>'
    page('/credits/',t('Artwork and licenses','Autoři a licence'),t('Artwork attribution and licenses for the UFlinux website.','Autoři grafiky a licence webu UFlinux.'),credits)
for lang in ('en','cs'): build_language(lang)
(OUT/'releases.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2))
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+origin+p+'</loc></url>' for p in sitemap)+'</urlset>')
(OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+origin+'/sitemap.xml\n')
(OUT/'_headers').write_text('/assets/*\n  Cache-Control: public, max-age=0, must-revalidate\n/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n/releases.json\n  Cache-Control: public, max-age=0, must-revalidate\n')
render('en','/404/','Page not found','This page could not be found.','<section class="intro"><p class="eyebrow">404</p><h1>A path less travelled.</h1><p>Page not found. Stránka nebyla nalezena.</p><a class="button" href="/">Home</a> <a href="/cs/">Česky</a></section>',False)
errorfile=OUT/'404/index.html'
errorfile.write_text(errorfile.read_text().replace('/cs/404/','/cs/').replace('/404/','/'))
shutil.move(errorfile,OUT/'404.html'); (OUT/'404').rmdir()
print(f'Built {len(list(OUT.rglob("*.html")))} pages in {OUT}')
