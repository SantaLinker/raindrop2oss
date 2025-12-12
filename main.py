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

# === 2. 定义分类映射 ===
# 为了页面整洁，分类逻辑保持不变
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
        # 深度清理标题，只保留品牌名
        for sep in [' | ', ' - ', ' – ', ' : ', '，', ',']: 
            if sep in title:
                title = title.split(sep)[0]
        
        url = item.get('link', '#')
        tags = item.get('tags', [])
        
        cat = "av" 
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
    # === 新版高颜值 UI 模板 ===
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>专业视听品牌大全</title>
<style>
/* 全局重置 */
:root {{ --primary: #2575fc; --bg: #f3f5f9; --text-main: #2d3436; --text-sub: #636e72; --card-bg: #ffffff; }}
* {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: var(--bg); color: var(--text-main); margin: 0; padding: 0; padding-bottom: 60px; }}

/* 头部 Hero 区域 */
header {{ 
    background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); 
    padding: 40px 20px 70px 20px; 
    text-align: center; 
    color: white; 
    border-bottom-left-radius: 30px; 
    border-bottom-right-radius: 30px;
    box-shadow: 0 10px 30px rgba(37, 117, 252, 0.2);
    position: relative;
    z-index: 10;
}}
h1 {{ margin: 0; font-size: 24px; font-weight: 700; letter-spacing: 1px; }}
.subtitle {{ margin-top: 8px; font-size: 13px; opacity: 0.8; font-weight: 300; }}

/* 搜索框 (悬浮玻璃拟态) */
.search-container {{ margin-top: -25px; padding: 0 20px; display: flex; justify-content: center; position: relative; z-index: 20; }}
.search-box {{ 
    width: 100%; max-width: 500px; background: rgba(255, 255, 255, 0.95); 
    backdrop-filter: blur(10px); padding: 5px; border-radius: 50px; 
    box-shadow: 0 10px 25px rgba(0,0,0,0.08); display: flex; align-items: center;
}}
.search-input {{ 
    width: 100%; border: none; background: transparent; padding: 12px 20px; 
    font-size: 16px; outline: none; color: #333; 
}}
.search-icon {{ padding-right: 20px; color: #999; font-size: 18px; }}

/* 导航栏 (Sticky) */
.nav-container {{ 
    position: sticky; top: 0; z-index: 99; background: rgba(243, 245, 249, 0.95); 
    backdrop-filter: blur(5px); padding: 15px 0; margin-bottom: 10px; border-bottom: 1px solid rgba(0,0,0,0.05);
}}
.nav-links {{ 
    display: flex; overflow-x: auto; gap: 10px; padding: 0 20px; 
    scrollbar-width: none; -ms-overflow-style: none; 
}}
.nav-links::-webkit-scrollbar {{ display: none; }}
.nav-item {{ 
    flex-shrink: 0; padding: 8px 16px; border-radius: 20px; font-size: 13px; 
    background: #fff; color: var(--text-sub); border: 1px solid #eee; transition: all 0.3s; cursor: pointer;
}}
.nav-item.active {{ background: var(--text-main); color: #fff; border-color: var(--text-main); box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}

/* 内容区域 */
.container {{ max-width: 1000px; margin: 0 auto; padding: 10px 20px; }}

/* 分类标题 */
.category-section {{ margin-bottom: 40px; scroll-margin-top: 130px; }}
.category-header {{ display: flex; align-items: center; margin-bottom: 15px; }}
.category-title {{ font-size: 18px; font-weight: 700; color: var(--text-main); margin: 0; display: flex; align-items: center; }}
.category-title::before {{ content: ''; display: block; width: 4px; height: 18px; background: var(--primary); margin-right: 10px; border-radius: 2px; }}
.category-count {{ margin-left: 8px; font-size: 12px; background: #e1e5ea; color: #777; padding: 2px 8px; border-radius: 10px; }}

/* 品牌网格 (卡片) */
.brand-grid {{ 
    display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); 
    gap: 15px; 
}}
/* 针对大屏优化 */
@media (min-width: 768px) {{ .brand-grid {{ grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; }} }}

.brand-card {{ 
    background: var(--card-bg); border-radius: 16px; padding: 15px; 
    text-decoration: none; color: inherit; display: flex; flex-direction: column; 
    align-items: center; text-align: center; position: relative; border: 1px solid rgba(0,0,0,0.02);
    box-shadow: 0 4px 6px rgba(0,0,0,0.02); transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}}
.brand-card:hover {{ transform: translateY(-5px); box-shadow: 0 15px 30px rgba(0,0,0,0.08); border-color: transparent; }}

/* Logo 样式 */
.logo-wrapper {{ 
    width: 60px; height: 60px; background: #fff; border-radius: 14px; 
    display: flex; align-items: center; justify-content: center; margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05); overflow: hidden; border: 1px solid #f9f9f9;
}}
.brand-logo {{ width: 40px; height: 40px; object-fit: contain; transition: transform 0.3s; }}
.brand-card:hover .brand-logo {{ transform: scale(1.1); }}

/* 文本信息 */
.brand-name {{ font-size: 14px; font-weight: 600; color: #333; margin-bottom: 8px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 40px; }} /* 固定高度防止错位 */
.tags {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 4px; height: 20px; overflow: hidden; }}
.tag {{ font-size: 10px; color: #666; background: #f0f2f5; padding: 2px 6px; border-radius: 6px; white-space: nowrap; }}

/* 首字母缺省图 */
.initial-fallback {{ width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 24px; }}

/* 底部 */
.footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; }}
</style>
</head>
<body>

<header>
    <h1>品牌视听库</h1>
    <div class="subtitle">实时更新</div>
</header>

<div class="search-container">
    <div class="search-box">
        <input type="text" id="searchInput" class="search-input" placeholder="搜索品牌或标签...">
        <div class="search-icon">🔍</div>
    </div>
</div>

<div class="nav-container">
    <div class="nav-links" id="navLinks"></div>
</div>

<div class="container" id="mainContent"></div>
<div class="footer">Generated via Raindrop API</div>

<script>
const brandsData = {brands_json};
const categories = {{
    "broadcast": "广播商用", "stage": "舞台扩声", "amps": "音频放大",
    "mics": "麦克风/监听", "cables": "线缆连接", "lighting": "灯光控制",
    "personal": "个人/车载", "av": "AV/其他"
}};
const colors = ['#6c5ce7', '#00cec9', '#0984e3', '#fdcb6e', '#e17055', '#d63031', '#e84393'];

function getColor(name) {{ let sum=0; for(let i=0;i<name.length;i++)sum+=name.charCodeAt(i); return colors[sum%colors.length]; }}

function createCard(brand) {{
    let domain = brand.url; try {{ domain = new URL(brand.url).hostname; }} catch(e){{}}
    const iconDDG = `https://icons.duckduckgo.com/ip3/${{domain}}.ico`;
    const iconClearbit = `https://logo.clearbit.com/${{domain}}`;
    const initial = brand.name.charAt(0);
    
    // 只显示前2个标签，保持整洁
    const tagsHtml = brand.tags.slice(0,2).map(t => `<span class="tag">${{t}}</span>`).join('');
    
    return `
    <a href="${{brand.url}}" target="_blank" class="brand-card" data-name="${{brand.name}}" data-tags="${{brand.tags.join(' ')}}">
        <div class="logo-wrapper">
            <img src="${{iconDDG}}" class="brand-logo" loading="lazy"
                 onerror="this.onerror=null; this.src='${{iconClearbit}}'; this.onerror=function(){{this.style.display='none'; this.nextElementSibling.style.display='flex';}}">
            <div class="initial-fallback" style="display:none; background:${{getColor(brand.name)}}">${{initial}}</div>
        </div>
        <div class="brand-name">${{brand.name}}</div>
        <div class="tags">${{tagsHtml}}</div>
    </a>`;
}}

function render() {{
    const nav = document.getElementById('navLinks');
    const main = document.getElementById('mainContent');
    nav.innerHTML = '<div class="nav-item active" onclick="scrollToSec(\\'top\\', this)">全部</div>';
    main.innerHTML = '';
    
    for(const [k,n] of Object.entries(categories)){{
        const items = brandsData.filter(b => b.cat === k);
        if(items.length === 0) continue;
        
        // 导航条
        const btn = document.createElement('div');
        btn.className = 'nav-item';
        btn.innerText = n;
        btn.onclick = function() {{ scrollToSec(k, this); }};
        nav.appendChild(btn);
        
        // 内容区
        main.innerHTML += `
            <div id="cat-${{k}}" class="category-section">
                <div class="category-header">
                    <h2 class="category-title">${{n}}</h2>
                    <span class="category-count">${{items.length}}</span>
                </div>
                <div class="brand-grid">${{items.map(createCard).join('')}}</div>
            </div>`;
    }}
}}

// 搜索
document.getElementById('searchInput').addEventListener('input', (e) => {{
    const term = e.target.value.toLowerCase();
    document.querySelectorAll('.brand-card').forEach(card => {{
        const match = card.getAttribute('data-name').toLowerCase().includes(term) || 
                      card.getAttribute('data-tags').toLowerCase().includes(term);
        card.style.display = match ? 'flex' : 'none';
    }});
}});

// 滚动定位
function scrollToSec(id, btn) {{
    // 切换按钮高亮
    if(btn) {{
        document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }}
    
    if(id==='top') {{
        window.scrollTo({{top:0, behavior:'smooth'}});
    }} else {{
        const el = document.getElementById('cat-'+id);
        const offset = el.getBoundingClientRect().top + window.pageYOffset - 110; // 减去头部高度
        window.scrollTo({{top:offset, behavior:'smooth'}});
    }}
}}

render();
</script>
</body>
</html>"""

def upload_to_oss(html_content):
    print("正在连接阿里云 OSS...")
    auth = oss2.Auth(OSS_ID, OSS_SECRET)
    bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
    
    # === 修改这里：文件名改为 brands.html ===
    filename = 'brands.html'
    result = bucket.put_object(filename, html_content)
    
    if result.status == 200:
        print(f"✅ 成功！文件已上传至: {filename}")
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
