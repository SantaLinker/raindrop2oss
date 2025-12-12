import os
import json
import requests
import oss2

# === 1. 配置获取 (从 GitHub Secrets 读取) ===
RAINDROP_TOKEN = os.environ.get('RAINDROP_TOKEN')
COLLECTION_ID = os.environ.get('RAINDROP_COLLECTION_ID')
OSS_ID = os.environ.get('OSS_ACCESS_KEY_ID')
OSS_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET')
OSS_BUCKET_NAME = os.environ.get('OSS_BUCKET')
OSS_ENDPOINT = os.environ.get('OSS_ENDPOINT')

# === 2. 定义分类映射 (和之前一样) ===
CATEGORY_MAP = {
    "广播商用音响": "broadcast", "舞台扩声": "stage", "音频放大": "amps",
    "麦克风": "mics", "混音直播及监听": "mics",
    "线缆": "cables", "连接件": "cables", "电源管理": "cables",
    "环境灯具": "lighting", "舞台效果灯具": "lighting", "灯具控制及传输": "lighting",
    "个人娱乐及车载": "personal",
    "音频处理及传输": "av", "IT多媒体及云计算": "av", "自动化控制": "av", "投影仪": "av",
    "音视频元件": "av", "通信对讲": "av", "会议讨论": "av", "音视频存储及播放": "av", "调音台": "av"
}

def fetch_raindrops():
    print("正在从 Raindrop 拉取数据...")
    items = []
    page = 0
    while True:
        # Raindrop API 限制每页最大 50 条，所以要循环拉取
        url = f"https://api.raindrop.io/rest/v1/raindrops/{COLLECTION_ID}?perpage=50&page={page}"
        headers = {"Authorization": f"Bearer {RAINDROP_TOKEN}"}
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Error: {resp.text}")
            break
        
        data = resp.json()
        current_items = data.get('items', [])
        if not current_items:
            break
        
        items.extend(current_items)
        print(f"  已获取第 {page+1} 页，共 {len(current_items)} 条...")
        page += 1
        
    print(f"✅ 拉取完成，共 {len(items)} 个书签。")
    return items

def process_data(items):
    brands_data = []
    for item in items:
        title = item.get('title', 'Unknown')
        # 清理标题 (去除 | 后面的内容)
        for sep in [' | ', ' - ', ' – ', ' : ']:
            if sep in title:
                title = title.split(sep)[0]
        
        url = item.get('link', '#')
        # 处理标签
        tags = item.get('tags', [])
        
        # 确定分类
        cat = "av" # 默认
        for t in tags:
            if t in CATEGORY_MAP:
                cat = CATEGORY_MAP[t]
                break
        
        brands_data.append({
            "name": title.strip(),
            "url": url,
            "cat": cat,
            "tags": tags
        })
    return brands_data

def generate_html(brands_json):
    # 这里嵌入之前的 HTML 模板
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>专业视听品牌大全</title>
<style>
:root {{ --primary: #007bff; --bg: #f4f6f9; --card-bg: #fff; --text: #2c3e50; }}
body {{ font-family: "Segoe UI", "Microsoft YaHei", sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 0; }}
header {{ background: #fff; padding: 40px 20px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.03); }}
.search-box {{ margin-top: 20px; max-width: 400px; margin-left: auto; margin-right: auto; }}
.search-input {{ width: 100%; padding: 12px 20px; border: 2px solid #eee; border-radius: 30px; outline: none; box-sizing: border-box; }}
.search-input:focus {{ border-color: var(--primary); }}
.nav-container {{ position: sticky; top: 0; background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); z-index: 100; border-bottom: 1px solid #eee; padding: 10px 0; }}
.nav-links {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; max-width: 1200px; margin: 0 auto; }}
.nav-item {{ cursor: pointer; color: #555; padding: 6px 14px; border-radius: 20px; background: #f8f9fa; transition: 0.2s; font-size: 13px; }}
.nav-item:hover, .nav-item.active {{ background: var(--primary); color: #fff; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 20px; padding-bottom: 80px; }}
.category-section {{ margin-bottom: 50px; scroll-margin-top: 140px; }}
.category-header {{ display: flex; align-items: center; border-bottom: 2px solid #eee; margin-bottom: 20px; padding-bottom: 10px; }}
.category-title {{ font-size: 1.4em; margin: 0; color: var(--text); }}
.category-count {{ margin-left: 10px; background: #e9ecef; color: #666; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; }}
.brand-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }}
.brand-card {{ background: var(--card-bg); border-radius: 12px; padding: 15px; display: flex; align-items: center; gap: 15px; border: 1px solid #f0f0f0; text-decoration: none; color: inherit; transition: 0.2s; }}
.brand-card:hover {{ transform: translateY(-4px); box-shadow: 0 10px 20px rgba(0,0,0,0.08); border-color: #cce5ff; }}
.logo-box {{ width: 50px; height: 50px; flex-shrink: 0; background: #fff; border-radius: 8px; border: 1px solid #f1f1f1; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
.brand-logo {{ width: 36px; height: 36px; object-fit: contain; }}
.info-box {{ flex-grow: 1; overflow: hidden; }}
.name {{ font-weight: 700; font-size: 1.05em; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.tags {{ height: 22px; overflow: hidden; display: flex; gap: 4px; }}
.tag {{ font-size: 0.7em; color: var(--primary); background: #e7f1ff; padding: 2px 6px; border-radius: 4px; white-space: nowrap; }}
.link-icon {{ color: #ddd; margin-left: auto; }}
.brand-card:hover .link-icon {{ color: var(--primary); }}
</style>
</head>
<body>
<header><h1>专业视听品牌大全</h1><div style="color:#666; margin-top:5px">数据实时同步自 Raindrop</div><div class="search-box"><input type="text" id="searchInput" class="search-input" placeholder="搜索品牌..."></div></header>
<div class="nav-container"><div class="nav-links" id="navLinks"></div></div>
<div class="container" id="mainContent"></div>
<script>
const brandsData = {brands_json};
const categories = {{
    "broadcast": "广播商用音响", "stage": "舞台扩声", "amps": "音频放大",
    "mics": "麦克风 & 直播", "cables": "线缆 & 连接", "lighting": "灯光 & 控制",
    "personal": "个人娱乐及车载", "av": "AV传输 & 其他"
}};
const colors = ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6', '#e67e22', '#1abc9c'];
function getColor(name) {{ let sum=0; for(let i=0;i<name.length;i++)sum+=name.charCodeAt(i); return colors[sum%colors.length]; }}
function createCard(brand) {{
    let domain = brand.url; try {{ domain = new URL(brand.url).hostname; }} catch(e){{}}
    const iconDDG = `https://icons.duckduckgo.com/ip3/${{domain}}.ico`;
    const iconClearbit = `https://logo.clearbit.com/${{domain}}`;
    const initial = brand.name.charAt(0);
    return `<a href="${{brand.url}}" target="_blank" class="brand-card" data-name="${{brand.name}}" data-tags="${{brand.tags.join(' ')}}">
        <div class="logo-box"><img src="${{iconDDG}}" class="brand-logo" onerror="this.onerror=null; this.src='${{iconClearbit}}'; this.onerror=function(){{this.style.display='none'; this.nextElementSibling.style.display='flex';}}"><div style="display:none; width:100%; height:100%; align-items:center; justify-content:center; color:#fff; font-weight:bold; background:${{getColor(brand.name)}}">${{initial}}</div></div>
        <div class="info-box"><div class="name">${{brand.name}}</div><div class="tags">${{brand.tags.slice(0,3).map(t=>`<span class="tag">#${{t}}</span>`).join('')}}</div></div><div class="link-icon">➜</div></a>`;
}}
function render() {{
    const navLinks=document.getElementById('navLinks'); const mainContent=document.getElementById('mainContent');
    navLinks.innerHTML='<div class="nav-item active" onclick="scrollToSec(\\'top\\')">全部</div>'; mainContent.innerHTML='';
    for(const [k,n] of Object.entries(categories)){{
        const items=brandsData.filter(b=>b.cat===k); if(items.length===0)continue;
        const nav=document.createElement('div'); nav.className='nav-item'; nav.innerText=n; nav.onclick=()=>scrollToSec(k); navLinks.appendChild(nav);
        mainContent.innerHTML+=`<div id="cat-${{k}}" class="category-section"><div class="category-header"><h2 class="category-title">${{n}}</h2><span class="category-count">${{items.length}}</span></div><div class="brand-grid">${{items.map(createCard).join('')}}</div></div>`;
    }}
}}
document.getElementById('searchInput').addEventListener('input',(e)=>{{ const term=e.target.value.toLowerCase(); document.querySelectorAll('.brand-card').forEach(c=>{{ const match=c.getAttribute('data-name').toLowerCase().includes(term)||c.getAttribute('data-tags').toLowerCase().includes(term); c.style.display=match?'flex':'none'; }}); }});
function scrollToSec(id){{ if(id==='top')window.scrollTo({{top:0,behavior:'smooth'}}); else {{ const el=document.getElementById('cat-'+id); const offset=el.getBoundingClientRect().top+window.pageYOffset-120; window.scrollTo({{top:offset,behavior:'smooth'}}); }} }}
render();
</script></body></html>"""

def upload_to_oss(html_content):
    print("正在连接阿里云 OSS...")
    auth = oss2.Auth(OSS_ID, OSS_SECRET)
    bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
    
    # 上传 index.html
    result = bucket.put_object('index.html', html_content)
    if result.status == 200:
        print("✅ 成功上传 index.html 到 OSS！")
    else:
        print(f"❌ 上传失败，状态码: {result.status}")

if __name__ == "__main__":
    if not RAINDROP_TOKEN:
        print("❌ 错误：未配置环境变量 RAINDROP_TOKEN")
    else:
        items = fetch_raindrops()
        if items:
            clean_data = process_data(items)
            brands_json = json.dumps(clean_data, ensure_ascii=False)
            final_html = generate_html(brands_json)
            upload_to_oss(final_html)
