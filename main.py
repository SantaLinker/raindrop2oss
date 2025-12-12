import os
import json
import requests
import oss2

# === 1. 配置获取 ===
RAINDROP_TOKEN = os.environ.get('RAINDROP_TOKEN')
COLLECTION_ID = os.environ.get('RAINDROP_COLLECTION_ID')
OSS_ID = os.environ.get('OSS_ACCESS_KEY_ID')
OSS_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET')
OSS_BUCKET_NAME = os.environ.get('OSS_BUCKET')
OSS_ENDPOINT = os.environ.get('OSS_ENDPOINT')

# === 2. 数据获取 ===
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
        # 深度清理标题
        for sep in [' | ', ' - ', ' – ', ' : ', '，', ',']: 
            if sep in title:
                title = title.split(sep)[0]
        
        url = item.get('link', '#')
        # 获取所有标签，不进行人为归类映射，保持原样
        tags = item.get('tags', [])
        
        # 如果没有标签，给一个默认的
        if not tags:
            tags = ["未分类"]

        brands_data.append({
            "name": title.strip(),
            "url": url,
            "tags": tags # 列表保留
        })
    return brands_data

def generate_html(brands_json):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>专业视听品牌库</title>
<style>
:root {{ --primary: #2575fc; --bg: #f8f9fa; --text-main: #2d3436; --card-bg: #ffffff; }}
* {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; background-color: var(--bg); color: var(--text-main); margin: 0; padding: 0; padding-bottom: 60px; }}

/* 头部设计 */
header {{ 
    background: linear-gradient(120deg, #2980b9, #2575fc); /* 调整为更稳重的科技蓝 */
    padding: 30px 20px 80px 20px; 
    text-align: center; color: white; 
    border-bottom-left-radius: 24px; border-bottom-right-radius: 24px;
    position: relative; z-index: 10;
}}
h1 {{ margin: 0; font-size: 26px; font-weight: 800; letter-spacing: 1px; }}
.subtitle {{ margin-top: 8px; font-size: 13px; opacity: 0.9; font-weight: 400; }}

/* 搜索框 */
.search-container {{ margin-top: -30px; padding: 0 20px; display: flex; justify-content: center; position: relative; z-index: 20; }}
.search-box {{ 
    width: 100%; max-width: 600px; background: rgba(255, 255, 255, 0.98); 
    padding: 6px; border-radius: 16px; 
    box-shadow: 0 8px 30px rgba(0,0,0,0.08); display: flex; align-items: center; border: 1px solid rgba(0,0,0,0.05);
}}
.search-input {{ 
    width: 100%; border: none; background: transparent; padding: 14px 15px; 
    font-size: 15px; outline: none; color: #333; 
}}
.search-icon {{ padding: 0 15px; color: #bbb; font-size: 18px; }}

/* 分类导航 (标签筛选) */
.nav-wrap {{ position: sticky; top: 0; z-index: 99; background: rgba(248, 249, 250, 0.96); backdrop-filter: blur(8px); border-bottom: 1px solid rgba(0,0,0,0.05); }}
.nav-links {{ 
    display: flex; overflow-x: auto; gap: 8px; padding: 12px 15px; 
    scrollbar-width: none; -ms-overflow-style: none; max-width: 1200px; margin: 0 auto;
}}
.nav-links::-webkit-scrollbar {{ display: none; }}
.nav-item {{ 
    flex-shrink: 0; padding: 6px 14px; border-radius: 50px; font-size: 13px; font-weight: 500;
    background: #fff; color: #666; border: 1px solid #e0e0e0; transition: all 0.2s; cursor: pointer;
}}
.nav-item.active {{ background: var(--primary); color: #fff; border-color: var(--primary); box-shadow: 0 4px 12px rgba(37, 117, 252, 0.3); }}

/* 统计条 */
.status-bar {{ text-align: center; font-size: 12px; color: #888; margin: 15px 0 5px 0; }}

/* 品牌网格 */
.container {{ max-width: 1200px; margin: 0 auto; padding: 10px 20px; }}
.brand-grid {{ 
    display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); 
    gap: 16px; 
}}
@media (min-width: 768px) {{ .brand-grid {{ grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; }} }}

/* 卡片样式 */
.brand-card {{ 
    background: var(--card-bg); border-radius: 12px; padding: 20px 15px; 
    text-decoration: none; color: inherit; display: flex; flex-direction: column; 
    align-items: center; text-align: center; border: 1px solid #f0f0f0;
    transition: transform 0.2s, box-shadow 0.2s;
}}
.brand-card:hover {{ transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.06); border-color: transparent; }}

/* Logo */
.logo-wrapper {{ 
    width: 64px; height: 64px; background: #fff; border-radius: 16px; 
    display: flex; align-items: center; justify-content: center; margin-bottom: 15px;
    border: 1px solid #f5f5f5; padding: 5px;
}}
.brand-logo {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
.initial-fallback {{ width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 28px; border-radius: 12px; }}

/* 文字内容 */
.brand-name {{ font-size: 15px; font-weight: 700; color: #2c3e50; margin-bottom: 10px; line-height: 1.3; }}
.tags {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; }}
.tag {{ 
    font-size: 11px; color: #555; background: #f1f3f5; 
    padding: 3px 8px; border-radius: 6px; 
    max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.footer {{ text-align: center; color: #aaa; font-size: 12px; margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; }}
</style>
</head>
<body>

<header>
    <h1>品牌视听库</h1>
    <div class="subtitle">实时更新 · 收录全球专业品牌</div>
</header>

<div class="search-container">
    <div class="search-box">
        <input type="text" id="searchInput" class="search-input" placeholder="搜索品牌、标签或域名...">
        <div class="search-icon">🔍</div>
    </div>
</div>

<div class="nav-wrap">
    <div class="nav-links" id="navLinks"></div>
</div>

<div class="container">
    <div class="status-bar" id="statusText">加载中...</div>
    <div class="brand-grid" id="brandGrid"></div>
</div>
<div class="footer">Generated via Raindrop API</div>

<script>
// 数据注入
const brandsData = {brands_json};

// 颜色生成器
const colors = ['#4e54c8', '#11998e', '#eb3b5a', '#f7b731', '#20bf6b', '#fa8231', '#a55eea'];
function getColor(str) {{ let hash=0; for(let i=0;i<str.length;i++)hash=str.charCodeAt(i)+((hash<<5)-hash); return colors[Math.abs(hash)%colors.length]; }}

// 1. 提取并排序所有标签
let allTags = new Set();
brandsData.forEach(item => {{
    item.tags.forEach(t => allTags.add(t));
}});
// 排序：为了美观，可以把短标签排前面，或者按首字母
const sortedTags = Array.from(allTags).sort();

// 全局状态
let currentFilter = 'all';

// DOM 元素
const navContainer = document.getElementById('navLinks');
const gridContainer = document.getElementById('brandGrid');
const statusText = document.getElementById('statusText');
const searchInput = document.getElementById('searchInput');

// 2. 初始化导航栏
function initNav() {{
    let html = `<div class="nav-item active" onclick="applyFilter('all', this)">全部 (${{brandsData.length}})</div>`;
    sortedTags.forEach(tag => {{
        // 计算该标签下的数量
        const count = brandsData.filter(b => b.tags.includes(tag)).length;
        html += `<div class="nav-item" onclick="applyFilter('${{tag}}', this)">${{tag}} (${{count}})</div>`;
    }});
    navContainer.innerHTML = html;
}}

// 3. 渲染卡片 (核心逻辑：筛选 + 渲染)
function renderCards(data) {{
    if (data.length === 0) {{
        gridContainer.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:40px; color:#999;">未找到匹配的品牌</div>';
        statusText.innerText = '0 个结果';
        return;
    }}
    
    statusText.innerText = `显示 ${{data.length}} 个品牌`;
    
    const html = data.map(brand => {{
        let domain = brand.url; 
        try {{ domain = new URL(brand.url).hostname; }} catch(e){{}}
        const iconDDG = `https://icons.duckduckgo.com/ip3/${{domain}}.ico`;
        const iconClearbit = `https://logo.clearbit.com/${{domain}}`;
        const initial = brand.name.charAt(0).toUpperCase();
        
        // 渲染所有标签
        const tagsHtml = brand.tags.map(t => `<span class="tag">${{t}}</span>`).join('');
        
        return `
        <a href="${{brand.url}}" target="_blank" class="brand-card">
            <div class="logo-wrapper">
                <img src="${{iconDDG}}" class="brand-logo" loading="lazy"
                     onerror="this.onerror=null; this.src='${{iconClearbit}}'; this.onerror=function(){{this.style.display='none'; this.nextElementSibling.style.display='flex';}}">
                <div class="initial-fallback" style="display:none; background:${{getColor(brand.name)}}">${{initial}}</div>
            </div>
            <div class="brand-name">${{brand.name}}</div>
            <div class="tags">${{tagsHtml}}</div>
        </a>`;
    }}).join('');
    
    gridContainer.innerHTML = html;
}}

// 4. 筛选功能
function applyFilter(tag, btnElement) {{
    currentFilter = tag;
    
    // 更新按钮高亮
    if(btnElement) {{
        document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
        btnElement.classList.add('active');
        // 按钮自动滚动到可视区域
        btnElement.scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'center' }});
    }}
    
    // 执行筛选
    if (tag === 'all') {{
        renderCards(brandsData);
    }} else {{
        const filtered = brandsData.filter(b => b.tags.includes(tag));
        renderCards(filtered);
    }}
    
    // 清空搜索框，避免逻辑冲突
    searchInput.value = '';
}}

// 5. 搜索功能 (支持 品牌名 + 标签 + 域名)
searchInput.addEventListener('input', (e) => {{
    const term = e.target.value.toLowerCase().trim();
    
    // 搜索时移除导航栏高亮，因为搜索是全局的
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    
    if (!term) {{
        // 搜索清空时，恢复到“全部”
        applyFilter('all', document.querySelector('.nav-item')); 
        return;
    }}

    const filtered = brandsData.filter(b => {{
        const inName = b.name.toLowerCase().includes(term);
        const inTags = b.tags.some(t => t.toLowerCase().includes(term));
        const inUrl = b.url.toLowerCase().includes(term); // 关键：支持搜索域名
        return inName || inTags || inUrl;
    }});
    
    renderCards(filtered);
}});

// 启动
initNav();
renderCards(brandsData);

</script>
</body>
</html>"""

def upload_to_oss(html_content):
    print("正在连接阿里云 OSS...")
    auth = oss2.Auth(OSS_ID, OSS_SECRET)
    bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
    
    # 保持文件名
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
