import colorsys, os
from PIL import Image
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ---------- accent from photo ----------
def lum(rgb):
    def f(c):
        c/=255; return c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4
    r,g,b=rgb; return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b)
def contrast(a,b):
    la,lb=lum(a),lum(b); return (max(la,lb)+0.05)/(min(la,lb)+0.05)
PAPER=(247,242,226); DPAPER=(30,34,41)
def hexc(rgb): return '#%02x%02x%02x'%tuple(int(round(x)) for x in rgb)
def candidates(fn):
    im=Image.open(os.path.join(ROOT,'assets',fn)).convert('RGB'); w,h=im.size
    im=im.crop((0,int(h*0.35),w,h)); im.thumbnail((160,160))
    q=im.quantize(8,method=Image.Quantize.MEDIANCUT); pal=q.getpalette()[:24]; cnt=sorted(q.getcolors(),reverse=True)
    scored=[]
    for n,i in cnt:
        r,g,b=pal[i*3:i*3+3]; h,l,s=colorsys.rgb_to_hls(r/255,g/255,b/255)
        score=s*(n/cnt[0][0])**0.35*(1-abs(l-0.5))*(0.55 if 0.52<h<0.70 else 1)
        scored.append((score,h,s))
    scored.sort(reverse=True)
    return scored[:5]
def hue_dist(a,b):
    d=abs(a-b)%1.0; return min(d,1-d)
def solve(h,s,bg,start,step):
    l=start
    while 0.08<l<0.92:
        rgb=[c*255 for c in colorsys.hls_to_rgb(h,l,s)]
        if contrast(rgb,bg)>=4.6: return rgb
        l+=step
    return [c*255 for c in colorsys.hls_to_rgb(h,l,s)]
IMG={'cover':'AI/kamakura-enoshima.png','naka':'AI/江之島弁財天仲見世通.png','hetsu':'AI/江島神社 邊津宮.png','candle':'AI/江之島海蠟燭.png','aqua':'AI/新江之島水族館.png','iwaya':'AI/江之島岩屋.png','koko':'AI/鎌倉高校前電列車.png','uomi':'AI/江之島魚亭.png','tobi':'AI/とびっちょ 本店.png','madu':'AI/CafeMadu ENOSHIMA.png'}
# 先各自取候選重點色，再依信心高低依序挑選，避免多頁撞成同一色系
CAND={k:candidates(v) for k,v in IMG.items()}
_order=sorted(CAND,key=lambda k:-CAND[k][0][0])
_used=[]; HS={}
for k in _order:
    pick=None
    for score,h,s in CAND[k]:
        if all(hue_dist(h,uh)>=0.07 for uh in _used):
            pick=(h,s); break
    if pick is None: pick=(CAND[k][0][1],CAND[k][0][2])
    _used.append(pick[0]); HS[k]=pick
# 仍落在同一色系（同一 0.05 色相桶）的，依序微調色相與飽和度拉開差異
from collections import defaultdict
_buckets=defaultdict(list)
for k,(h,s) in HS.items(): _buckets[round(h,2)].append(k)
for keys in _buckets.values():
    if len(keys)>1:
        keys.sort(); n=len(keys)
        for idx,k in enumerate(keys):
            h0,s0=HS[k]
            HS[k]=((h0+(idx-(n-1)/2)*0.035)%1.0, min(0.85,s0+0.04*idx))
AC={k:(hexc(solve(h,max(0.45,min(0.75,s+0.15)),PAPER,0.46,-0.02)),hexc(solve(h,max(0.45,min(0.75,s+0.15)),DPAPER,0.6,0.02))) for k,(h,s) in HS.items()}
def img(k,cls='',alt='',style=''):
    return f'<img class="{cls}" src="../assets/{IMG[k]}" alt="{alt}"'+(f' style="{style}"' if style else '')+'>'

TAGS={'off':'官方已核對','site':'專門網站查證','map':'地圖實測','multi':'多來源一致','one':'單一來源','none':'行前自行確認','mine':'我的整理'}
def t(k,extra=''): return f'<span class="tag {k}">{TAGS[k]}{extra}</span>'
def rows(items,cls=''):
    return f'<table class="info {cls}">'+''.join(f'<tr><th>{a}</th><td>{b}<span class="tgs">{c}</span></td></tr>' for a,b,c in items)+'</table>'
S=[]
def slide(src,body,ac='cover',cls=''):
    if '</header>' in body:
        h,rest=body.split('</header>',1)
        body=h+'</header>'+f'<div class="bodywrap">{rest}</div>'
    S.append(f'<section class="slide ac-{ac}{" "+cls if cls else ""}" data-src="{src}"><i class="deco d1"></i><i class="deco d2"></i><i class="deco d3"></i>{body}</section>')
def head(title,sub='',ok=False):
    b='<span class="badge ok">時間・地點已確認</span>' if ok else ''
    return f'<header><span class="dot"></span><h2>{title}</h2><p class="sub">{sub}</p>{b}</header>'
def foot(source,where=''):
    w=f'<span class="where"><b>查證去處：</b>{where}</span>' if where else ''
    return f'<div class="src"><span><b>來源：</b>{source}</span>{w}</div>'
def note(x): return f'<p class="note">{x}</p>'
def card(title,lis): return f'<div class="card"><h3>{title}</h3><ul>'+''.join(f'<li>{x}</li>' for x in lis)+'</ul></div>'
PIC='圖片：使用者提供（AI 生成風格插畫，非實景照片）。'

# 1 cover
slide('index,江之島是什麼',img('cover','bg','步道遠望江之島（AI 插畫）')+'<div class="scrim"></div><div class="cover-text"><p class="kicker">新手導覽 ・ 神奈川縣藤澤市</p><h1>第一次去江之島</h1><p class="lead">景點、餐飲、交通與住宿地區，每個資訊都標出它的來源。</p></div><div class="src"><span><b>圖片：</b>使用者提供（AI 生成風格插畫，非實景照片）。內容整理自 LLM Wiki。</span></div>','cover','cover')
# 2
slide('meta',head('怎麼讀這份導覽','每個欄位旁都有一個來源標籤')+'<div class="legend">'+''.join(f'<div class="lg">{t(k)}<p>{d}</p></div>' for k,d in [
 ('off','店家或設施官網，由使用者剪藏提供'),('site','旅遊專門網站標示官方確認或有監製單位；是網站的標示，無法獨立驗證'),
 ('map','路線時間與座標，用 Google 地圖實際查詢（只看路線，不查班次）'),('multi','沒有官方資料，但兩個以上來源說法一致'),
 ('one','只有一個二手來源，沒有佐證'),('none','沒有官方資料或沒查到；出發前請自行確認，並列在最後的「行前確認清單」')])+'</div>'+
 note('標有<b>時間・地點已確認</b>的頁面：營業時間、公休與交通時間都有官方、專門網站或 Google 地圖的依據。其他欄位（費用、座位、預約等）若標<b>行前自行確認</b>，請照最後兩頁的清單再確認。每張下方的「來源」列寫出資料是誰提供的。'),'hetsu')
# 3
ISLAND='<svg class="illus" viewBox="0 0 420 200" role="img" aria-label="小島與橋的示意圖"><path d="M0 150H420" class="ln"/><path d="M230 150C240 96 286 70 322 78C362 86 392 118 400 150Z" class="fillac"/><path d="M318 78V40M310 46H326M312 40H324" class="ln"/><path d="M20 150V132H232V150M60 132V150M100 132V150M140 132V150M180 132V150" class="ln"/><path d="M0 170q15-10 30 0t30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0 30 0" class="ln thin"/></svg>'
slide('江之島是什麼',head('認識江之島','一座與陸地相連的小島')+'<div class="cols"><div class="col"><ul class="big"><li>神奈川縣藤澤市的小島：江島神社、洞窟、展望燈塔，和一條熱鬧的參道商店街。</li><li>退潮時可以徒步走過去；今天遊客主要走 1949 年建成的江の島弁天橋。</li><li>信仰是弁財天：1182 年源賴朝造了八臂弁財天，江戶時代成為藝能、音樂、智慧之神。</li></ul></div><div class="col side">'+ISLAND+card('江島神社三宮',['奥津宮、中津宮、辺津宮'])+card('島上的自然',['岩屋是海蝕洞，因土地隆起現在位在海面之上','西南端稚児ヶ淵的波蝕台，關東大地震時隆起約 1 公尺'])+'</div></div>'+foot('神奈川縣觀光協會「江島神社」、藤澤市「このまちアーカイブス」（Claude 查證用的工具摘要，不是原文全文；屬單一來源等級）。示意圖為自繪。'),'cover')
# 4
def route(frm,stops,time):
    return f'<div class="route"><b class="from">{frm}</b>'+''.join(f'<span class="seg">{lab}</span><span class="stn">{st}</span>' for lab,st in stops)+f'<em>{time}</em></div>'
slide('怎麼去江之島',head('怎麼去 ①','目的地記住一個站名：片瀬江ノ島')+'<div class="routes">'+
 route('新宿',[('小田急浪漫特快（江之島）直達，不用轉車','片瀬江ノ島')],'約 1 小時 7 分')+
 route('東京',[('JR 東海道本線','藤澤'),('小田急江之島線','片瀬江ノ島')],'約 1 小時')+
 route('橫濱',[('JR 東海道本線','藤澤'),('小田急江之島線','片瀬江ノ島')],'約 31 分')+'</div>'+
 '<p class="row2">'+t('map')+'所需時間是查詢當下的班次，不是時刻表。票價與是否另付特急券：'+t('none')+'</p>'+
 note('搭 JR 或小田急到藤澤後，也可以改搭江之電到「江ノ島」站，較慢、風景較好；所需時間 wiki 沒有。')+
 foot('Google 地圖路線查詢，2026-11-13（Claude 查證）。路線圖為自繪示意。','小田急電鐵官網（票價、特急券）；時刻不在查證範圍。'),'koko')
# 5
slide('怎麼去江之島',head('怎麼去 ②','三個車站，與周遊券')+'<div class="cols"><div class="col r">'+rows([
 ('三個車站','小田急「片瀬江ノ島」、江ノ島電鐵「江ノ島」、湘南モノレール「湘南江の島」；到江島神社都步行約 15–23 分',t('one')),
 ('實測','片瀬江ノ島站 → 弁財天仲見世通：步行 13 分、約 900 公尺，路線經過江の島弁天橋',t('map')),
 ('周遊券','小田急「江の島・鎌倉フリーパス」，新宿出發 1,640 日圓（2025 年 8 月的資料）',t('one')+t('none','：2026 現況')),
 ('往鎌倉','從鎌倉站搭江ノ電約 20 分到鎌倉高校前站',t('site'))])+'</div><div class="col l"><figure class="photo">'+img('cover','','第一次去江之島 主視覺插畫')+'</figure><p class="cap">示意插畫</p></div></div>'+
 foot('神奈川縣觀光協會（三個車站）、Google 地圖 2026-11-10（步行實測）、fun-japan（周遊券，二手資料）、gltjp（往鎌倉高校前）；皆為 Claude 查證。'+PIC,'小田急電鐵、江ノ島電鐵官網（周遊券現價與適用範圍）。'),'cover')
# 6
slide('住宿地區',head('住在哪','住宿地區：先看你要待幾天')+
 '<div class="areas"><span>新宿、東京</span><span>藤澤站</span><span class="on">江之島</span><span>由比之濱、長谷</span><span>鎌倉站</span></div>'+
 '<table class="grid"><tr><th>地區</th><th>優點</th><th>缺點</th></tr>'+
 f'<tr><td>新宿、東京</td><td>{t("mine")}交通與購物選擇多</td><td>{t("mine")}去江之島要一段車程，早出晚歸</td></tr>'+
 f'<tr><td>藤澤站附近</td><td>{t("mine")}離江之島近，早上不用趕車</td><td>{t("mine")}夜間可逛的地方較少</td></tr>'+
 f'<tr><td>鎌倉站周邊</td><td>{t("one")}市中心，餐廳商店多，到東京約一小時</td><td>{t("mine")}要再搭車到江之島</td></tr>'+
 f'<tr><td>由比之濱、長谷</td><td>{t("one")}靠海灘，江之電沿線</td><td>來源沒寫缺點</td></tr>'+
 f'<tr><td>江之島附近</td><td>{t("one")}景點集中，適合看夕陽與夜景</td><td>{t("mine")}選擇較少</td></tr></table>'+
 note('只去江之島一天，從東京或新宿當天來回即可；想看夕陽或夜間點燈住藤澤或江之島附近；江之島加鎌倉兩天，住鎌倉站周邊（我的整理）。住宿價格與評價沒有來源，不寫。')+
 foot('LIVE JAPAN「鎌倉住宿」（旅遊媒體，可靠度低；Claude 查證）；標「我的整理」者沒有來源。地區示意為自繪，不代表實際距離。','藤澤市觀光網站「住宿」頁、鎌倉市觀光協會住宿頁。'),'madu')
# 7
def circ(k,name,time,far=''):
    return f'<div class="circ"><figure class="photo sm">{img(k,"",name)}</figure><b>{name}</b><span>{time}</span>{far}{t("map")}</div>'
slide('江之島弁財天仲見世通,江島神社邊津宮,江之島海蠟燭展望燈塔,新江之島水族館,江之島岩屋,鎌倉高校前平交道',head('景點總覽','從弁財天仲見世通出發，各景點多遠',True)+'<div class="circs">'+
 circ('hetsu','江島神社邊津宮','步行 5 分')+circ('candle','海蠟燭展望燈塔','步行 12 分')+circ('aqua','新江之島水族館','步行 15 分、大眾運輸 10 分')+circ('iwaya','江之島岩屋','步行 16 分')+circ('koko','鎌倉高校前平交道','大眾運輸 18 分（步行 31 分）','<span class="far">距離較遠</span>')+'</div>'+
 note('2026-11-10 約 18:00 以「立即出發」查詢；時間會隨班次與路況變動。')+
 foot('Google 地圖，2026-11-10（Claude 查證）。'+PIC,'出發當天用 Google 地圖重查。'),'naka')

def place(src_id,ac,kind,title,sub,caption,hi,items,source,where):
    left=f'<figure class="photo">{img(ac,"",title)}</figure><p class="cap">{caption}</p><ul class="hi">'+''.join(f'<li>{x}</li>' for x in hi)+'</ul>'
    slide(src_id,head(title,kind+' ・ '+sub,True)+'<div class="cols"><div class="col l">'+left+'</div><div class="col r">'+rows(items,'sm')+'</div></div>'+foot(source+PIC,where),ac)
G10='Google 地圖 2026-11-10（Claude 查證）。'; G13='Google 地圖 2026-11-13（Claude 查證）。'
place('江之島弁財天仲見世通','naka','景點','弁財天仲見世通','參道商店街','圖中可見「女夫饅頭」老店招牌',
 ['章魚仙貝、女夫饅頭、吻仔魚軟冰淇淋','街底有石階通往江島神社'],
 [('開放','街道全天開放、無休（指街道本身）',t('site')),('各店時間','約 9:00–18:00；公休例：あさひ本店週四、紀の国屋本店週三',t('one','（資料頁，可接受）')+t('none','：當日')),('費用','逛街免費；女夫饅頭 1 個 150 日圓',t('one')),('交通','片瀬江ノ島駅步行 13 分',t('map'))],
 'gltjp（旅遊專門網站，標示官方確認；使用者提供）、るるぶ（資料頁；Claude 查證）、'+G10,'整條街沒有單一官網，各店時間看店家官網或當天現場。')
place('江島神社邊津宮','hetsu','景點','江島神社 邊津宮','江之島最下方的神社，又稱下之宮','邊津宮社殿',
 ['1206 年創建，供奉水與航海之神','錢洗白龍王（龍之錢洗）、茅之輪、結緣之樹','奉安殿供奉妙音弁財天、八臂弁財天'],
 [('參拜時間','8:30–17:00、無休；有御朱印',t('site')),('奉安殿拝觀','8:30–16:30；大人 200 日圓',t('one','（機構頁，可接受）')),('參拜費用','沒有資料',t('none')),('交通','從仲見世通步行 5 分',t('map'))],
 'gltjp（標示官方確認，監製：江島神社；使用者提供）、神奈川縣觀光協會（奉安殿）、'+G10,'江島神社官網辺津宮頁（參拜時間與費用）。')
place('江之島海蠟燭展望燈塔','candle','景點','江之島海蠟燭 展望燈塔','展望室、夕陽與冬季燈飾','展望燈塔外觀',
 ['展望室與夕陽；展望室下有木製平台','冬季「湘南の宝石」燈飾主會場：去年度 2025-11-22 至 2026-02-28，今年度日期行前自行確認'],
 [('營業','9:00–20:00（最後入場 19:30）',t('off')),('費用','海蠟燭 大人 800、兒童 400 日圓；17:00 後入苑 大人 500、兒童 250 日圓',t('off','；有矛盾')),('休業日','通常無休；遇惡劣天候會中止營業，出發當天確認',t('off')),('交通','從仲見世通步行 12 分',t('map'))],
 '海蠟燭官網「營業時間」「價格／門票」（官方，機翻頁；使用者提供）、江之電官方頁（休業日；使用者提供）、神奈川縣觀光協會（燈飾）、'+G10,'海蠟燭官網日文原頁；今年度燈飾日期看官網公告。')
place('新江之島水族館','aqua','景點','新江之島水族館','室內景點，片瀬江ノ島站步行 3 分','海豚表演池，遠方是江之島',
 ['大型行李不能帶入觀覽區，請用付費置物櫃','部分展示區禁用閃光燈、全館禁菸','憑票當日可再次入館；可免費租輪椅（數量有限）'],
 [('營業','3–11 月 9:00–17:00，12–2 月 10:00–17:00；最晚入場在閉館前 1 小時',t('off')),('費用','大人 2,800、高中生 1,800、中小學生 1,300、幼兒 900 日圓',t('off')),('公休','全年無休，設施檢查可能臨時休館',t('off')),('交通','從仲見世通步行 15 分、大眾運輸 10 分',t('map'))],
 '新江之島水族館官網繁中版（官方；使用者提供）、'+G10,'水族館官網（出發前看當日公告）。')
place('江之島岩屋','iwaya','景點','江之島岩屋','海蝕洞窟','岩屋洞口外觀',
 ['第一岩屋約 152 公尺，可免費租蠟燭進洞','洞內濕滑，建議穿好走的鞋；洞內沒有洗手間、投幣式寄物櫃'],
 [('入窟費','一般 500、小學生 200 日圓；20 人以上 8 折',t('off')),('開放與公休','9:00–17:00（依季節而異）；無休',t('off')+t('site')),('參觀時間','約 30 分（15–40 分）',t('multi')),('悪天候','是否封閉沒有資料；天候不佳先確認',t('none')),('交通','從仲見世通步行 16 分',t('map'))],
 '藤澤市觀光公式網站（官方；使用者提供）、gltjp（標示官方確認；使用者提供）、boo2k 部落格與 banzokubiology（參觀時間）、'+G10,'藤澤市觀光網站首頁公告；岩屋 Facebook 專頁。')
place('鎌倉高校前平交道','koko','景點','鎌倉高校前平交道','電車與海景同框','江之電沿海行駛，遠方是江之島',
 ['望見七里濱、江之島與三浦半島','是一般道路與平交道，不進軌道','不長時間佔用公共空間拍照、垃圾自行帶走'],
 [('開放','公共道路，沒有營業時間',t('site')),('拍照規定','2025-10 鎌倉市增派警衛，請到附近公園拍攝區',t('multi','；現況待查證')),('交通','江ノ電鎌倉高校前駅步行約 1 分；從仲見世通大眾運輸 18 分',t('map')+t('one')),('官網','尚未找到官網',t('none'))],
 'gltjp（標示官方確認；使用者提供）、神奈川新聞（拍照規定；Claude 查證）、'+G10,'鎌倉市官方公告（現況的警衛與拍照規定）。')
place('江之島魚見亭','uomi','餐廳','江之島 魚見亭','島西側高處的海鮮餐廳','店門口',
 ['官網說有 150 年以上歷史（部落格寫 140 年，有矛盾）','天氣好可坐露台','顧客提到江之島丼定食、吻仔魚丼；菜單價格待查證'],
 [('營業','10:00–17:00（最後點餐）；颱風、暴雨警報等不定期休息',t('off')),('費用','平均消費 1,500 日圓起',t('off')),('座位與預約','140 個座位；不接受預約，用餐時間要抽號碼牌排隊',t('off')+t('one')),('交通','從仲見世通步行 12 分；到 Cafe Madu 步行 3 分',t('map'))],
 '魚見亭官網「店鋪概覽」（官方；使用者提供）、boo2k 部落格（排隊方式；使用者提供）、'+G13,'魚見亭官網（當日是否營業）。')
place('江之島とびっちょ本店','tobi','餐廳','海鮮丼 とびっちょ 本店','生白魚乾丼專門店','店面與招牌',
 ['生しらす丼只用當天在地水揚的生白魚乾','とびっちょ丼是赤醋飯搭 8 種以上依進貨而變的海鮮','生しらす丼在禁漁期（1 月至 3 月中旬）與不漁時不提供'],
 [('營業','11:00–21:00；最後點餐 平日 20:00、週六日假日 20:30；無休，荒天可能休息',t('off')),('費用','生しらす丼 1,380、とびっちょ丼 2,530 日圓（稅込）',t('off')),('座位與預約','官網沒寫',t('none')),('交通','從魚見亭步行 15 分',t('map'))],
 'とびっちょ官網「江の島本店」店舖頁（官方；使用者提供）、'+G13,'店家 X 公告（當日是否營業）；官網補座位與預約。')
place('江之島CafeMadu','madu','咖啡廳','Cafe Madu 江の島店','高台上的自助式咖啡廳','露台座位',
 ['可一覽相模灣的一軒屋咖啡廳，有露台','咖哩、白魚乾可麗餅、聖代','自助式；擁擠時段可能要等位'],
 [('營業','平日 11:00–18:00（最後點餐 17:00）；週六日假日 10:00–19:00（最後點餐 18:00）',t('off','；有矛盾')),('座位','店內 42 席、露台 48 席',t('off','；有矛盾')),('預算','午餐、晚餐各約 1,800 日圓',t('one')),('交通','從魚見亭步行 3 分（180 公尺）',t('map'))],
 'HAKKA GROUP 店舖頁（營運公司官網；使用者提供）、ぐるなび（預算；Claude 查證）、'+G13,'營運公司 X 公告（休業日）；官網補菜單價格。')
# notes
IC={'clock':'<svg viewBox="0 0 40 40" class="ic"><circle cx="20" cy="20" r="15" class="ln"/><path d="M20 11V20L27 24" class="ln"/></svg>','stairs':'<svg viewBox="0 0 40 40" class="ic"><path d="M5 33H13V25H21V17H29V9H36" class="ln"/></svg>','coin':'<svg viewBox="0 0 40 40" class="ic"><circle cx="20" cy="20" r="15" class="ln"/><path d="M14 12L20 21L26 12M20 21V30M14 21H26M14 25H26" class="ln"/></svg>'}
def icard(ic,title,lis): return f'<div class="card ic-card">{IC[ic]}<div><h3>{title}</h3><ul>'+''.join(f'<li>{x}</li>' for x in lis)+'</ul></div></div>'
slide('逛江之島的注意事項',head('逛江之島的注意事項','出發前先知道這幾件事')+'<div class="cols"><div class="col">'+
 icard('clock','時間與人潮',['參道各店時間與公休不同，出發前再確認','あさひ本店前總是有長長的隊伍','魚見亭不接受預約，用餐時間可能排隊'])+
 icard('stairs','路況',['參道是緩上坡，盡頭有石階，高度行前自行確認','岩屋洞內濕滑，建議穿好走的鞋','島入口有廁所與免費 Wi-Fi'])+'</div><div class="col">'+
 icard('coin','費用一覽（日圓）',['女夫饅頭 150；奉安殿 大人 200','海蠟燭 大人 800；水族館 大人 2,800','岩屋 大人 500；生しらす丼 1,380','魚見亭 平均 1,500 起'])+
 note('冬季燈飾「湘南の宝石」去年度是 2025-11-22 至 2026-02-28，今年度日期行前自行確認。')+'</div></div>'+
 foot('同前面各景點與餐廳頁的來源列；るるぶ（あさひ本店排隊）、gltjp（廁所與 Wi-Fi）、神奈川縣觀光協會（燈飾）為 Claude 查證。圖示為自繪。'),'hetsu')
def checks(title,sub,first,rws,ac):
    slide(('待查證清單,'+first),head(title,sub)+'<table class="grid check"><tr><th></th><th>'+rws[0][0]+'</th><th>要確認什麼</th><th>去哪裡查</th></tr>'+''.join(f'<tr><td><i class="box"></i></td><td>{a}</td><td>{b}</td><td>{c}</td></tr>' for a,b,c in rws[1:])+'</table>'+foot('wiki 的待查證清單（由各頁「查證狀態」表自動彙整）。這些是非核心欄位，不影響時間・地點已確認。'),ac)
checks('行前確認清單 ①','景點：出發前要再確認的事','江島神社邊津宮,江之島海蠟燭展望燈塔,江之島岩屋,江之島弁財天仲見世通',[('景點',),
 ('江島神社邊津宮','參拜費用；奉安殿費用與時間','江島神社官網辺津宮頁'),
 ('海蠟燭','費用（江之電頁 500／250 與官網 800／400 不一致）；今年度燈飾日期','海蠟燭官網日文頁'),
 ('江之島岩屋','悪天候是否封閉；每日實際開放時間','藤澤市觀光網站、岩屋 Facebook'),
 ('弁財天仲見世通','各店營業時間與公休；Google 當日顯示至 20:00，與 9:00–18:00 不同','各店官網、現場'),
 ('鎌倉高校前平交道','警衛與拍照規定的現況','鎌倉市官方公告')],'iwaya')
checks('行前確認清單 ②','交通與餐飲：出發前要再確認的事','怎麼去江之島,江之島魚見亭,江之島とびっちょ本店,江之島CafeMadu',[('項目',),
 ('交通','特急券與票價；周遊券 2026 現況與適用範圍','小田急電鐵、江ノ島電鐵官網'),
 ('魚見亭','當日是否營業','店家官網'),
 ('とびっちょ 本店','座位數與預約；當日是否營業','店家官網、店家 X 公告'),
 ('Cafe Madu','休業日；菜單與價格','營運公司官網與 X 公告'),
 ('活動','冬季燈飾今年度日期；wiki 尚未收錄其他活動','藤澤市觀光網站、海蠟燭官網')],'tobi')

CSS=open(''+os.path.join(ROOT,'scripts','slides.css')+'').read()+'\n'+'\n'.join(f'.ac-{k}{{--ac-l:{l};--ac-dk:{d}}}' for k,(l,d) in AC.items())
tail=open(''+os.path.join(ROOT,'scripts','slides_tail.html')+'',encoding='utf-8').read()
html=f'''<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>江之島新手導覽</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@700;900&display=swap">
<style>
{CSS}
</style>
</head>
<body>
<div id="bar"></div>
<div id="stage">
'''+'\n'.join(S)+'\n</div>\n'+tail
open(ROOT+'/slides/src.html','w',encoding='utf-8').write(html)
print(len(S),AC)
