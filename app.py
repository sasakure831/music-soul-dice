from flask import Flask, render_template_string, jsonify, request, send_file
import requests
import json
import os
import urllib.parse

app = Flask(__name__)
MEMORY_FILE = "music_dice_memory.json"
DEFAULT_DATA = {str(i): {"label": f"面 0{i}", "song": "", "artist": "", "pic": ""} for i in range(1, 7)}

# ======= 【绝对路径锁死保护】 =======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MADONNA_IMAGE_NAME = "3e58a6b112d65bcf7028b95751c5b654.png" 
MADONNA_ABS_PATH = os.path.join(BASE_DIR, MADONNA_IMAGE_NAME)
# ==================================

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return DEFAULT_DATA
    return DEFAULT_DATA

def save_memory(data):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)

INDEX_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Music Soul Dice</title>
    <style>
        body { margin: 0; padding: 0; background-color: #fcf9f5; font-family: 'Georgia', serif; display: flex; flex-direction: column; align-items: center; justify-content: flex-start; min-height: 100vh; color: #2c2a29; }
        h1 { font-size: 24px; font-weight: 300; letter-spacing: 4px; margin-top: 50px; margin-bottom: 5px; color: #1a1a1a; }
        .subtitle { color: #8a827c; font-size: 12px; font-style: italic; margin-bottom: 30px; letter-spacing: 1px; }
        .dice-stage { width: 220px; height: 220px; position: relative; margin: 50px 0; perspective: 1200px; }
        .cube { width: 100%; height: 100%; position: absolute; transform-style: preserve-3d; transition: transform 0.8s cubic-bezier(0.2, 0.8, 0.2, 1); }
        .face { position: absolute; width: 220px; height: 220px; background-color: rgba(255, 252, 247, 0.95); background-size: cover; background-position: center; border: 4px solid rgba(255, 255, 255, 0.8); outline: 1px solid #e0d7cd; border-radius: 32px; box-shadow: inset 0 0 20px rgba(255,255,255,1), 0 15px 35px rgba(26,24,23,0.05); display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; box-sizing: border-box; padding: 25px; }
        .front { transform: translateZ(110px); } .back { transform: rotateY(180deg) translateZ(110px); } .left { transform: rotateY(-90deg) translateZ(110px); } .right { transform: rotateY(90deg) translateZ(110px); } .top { transform: rotateX(90deg) translateZ(110px); } .bottom { transform: rotateX(-90deg) translateZ(110px); }
        .dice-number { font-size: 80px; font-weight: bold; font-family: 'Trebuchet MS', sans-serif; color: rgba(235, 226, 213, 0.6); }
        .face.has-song .dice-number { display: none; }
        .face.has-song::before { content: ""; position: absolute; top:0; left:0; right:0; bottom:0; background: rgba(255, 252, 247, 0.35); border-radius: 28px; z-index: 1; }
        .face:not(.has-song) { background-image: radial-gradient(circle at 25% 18%, #ff4d4d 9px, transparent 10px), radial-gradient(circle at 78% 28%, #2ecc71 8px, transparent 9px), radial-gradient(circle at 18% 78%, #e84393 10px, transparent 11px), radial-gradient(circle at 82% 72%, #ff4d4d 8px, transparent 9px), radial-gradient(circle at 38% 42%, #fdcb6e 11px, transparent 12px), radial-gradient(circle at 62% 85%, #0984e3 7px, transparent 8px); }
        .g-clef { display: none; font-size: 65px; color: #1a1a1a; z-index: 2; } .face.has-song .g-clef { display: block; }
        .side-tag { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #a19790; margin-bottom: 3px; z-index: 2; }
        .song-name { font-size: 13px; font-weight: 600; color: #2c2a29; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; z-index: 2; text-align: center; }
        .artist-name { font-size: 11px; font-style: italic; color: #7a7571; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; z-index: 2; margin-top: 2px; display: none; }
        .face.has-song .artist-name { display: block; }
        .control-panel { background: #ffffff; border: 1px solid #eee8df; border-radius: 20px; padding: 25px 30px; width: 360px; box-shadow: 0 10px 30px rgba(163,149,131,0.05); margin-top: 20px; }
        .panel-header { font-size: 14px; font-weight: bold; letter-spacing: 1px; border-bottom: 1px solid #fcf9f5; padding-bottom: 12px; margin-bottom: 18px; display: flex; justify-content: space-between; }
        .input-box { width: 100%; padding: 12px 15px; border: 1px solid #e8e2d8; border-radius: 10px; background: #fdfcfb; font-size: 13px; box-sizing: border-box; outline: none; }
        .search-container { position: relative; margin-top: 12px; }
        .search-dropdown { position: absolute; top: 100%; left: 0; right: 0; background: #fff; border: 1px solid #e8e2d8; border-radius: 12px; max-height: 250px; overflow-y: auto; z-index: 100; display: none; margin-top: 5px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); }
        .search-row { display: flex; align-items: center; padding: 12px; cursor: pointer; border-bottom: 1px solid #fdfcfb; }
        .play-btn { width: 28px; height: 28px; border: 1px solid #ddd; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #666; margin-left: auto; }
        .search-row img { width: 42px; height: 42px; border-radius: 8px; margin-right: 15px; }
        .toggle-btn { width: 100%; padding: 10px; margin-bottom: 15px; background: #2c2a29; color: #fff; border: none; border-radius: 10px; cursor: pointer; font-size: 13px; }
    </style>
</head>
<body>
    <h1>Music Soul Dice</h1>
    <div class="subtitle">关于音乐，你...的一面</div>
    <div class="dice-stage" id="stage">
        <div class="cube" id="cube">
            {% for i in ['1', '2', '3', '4', '5', '6'] %}
            {% set face_name = ['front', 'back', 'left', 'right', 'top', 'bottom'][loop.index0] %}
            <div class="face {{ face_name }} {% if dice[i].song %}has-song{% endif %}" onclick="selectSide({{ i }})" style="{% if dice[i].pic %}background-image: url('{{ dice[i].pic }}');{% endif %}">
                <div class="dice-number">{{ i }}</div><div class="g-clef">𝄞</div>
                <div class="side-tag" id="label-{{ i }}">{{ dice[i].label }}</div>
                <div class="song-name" id="song-{{ i }}">{{ dice[i].song }}</div>
                <div class="artist-name" id="artist-{{ i }}">{{ dice[i].artist }}</div>
            </div>
            {% endfor %}
        </div>
    </div>
    <div class="control-panel">
        <button class="toggle-btn" onclick="toggleView()">切换视角 (135 ⇋ 246)</button>
        <button class="toggle-btn" style="background:#8a827c;" onclick="generateCrossNet()">下载十字展开图</button>
        <div class="panel-header"><span id="panel-title">SCULPTING: SIDE 01</span></div>
        <input type="hidden" id="current-side" value="1">
        <input type="text" id="node-label" class="input-box" placeholder="关于你...的一面" oninput="syncLabel(this.value)">
        <div class="search-container">
            <input type="text" id="music-search" class="input-box" placeholder="输入搜索音乐..." oninput="instantSearch(this.value)">
            <div class="search-dropdown" id="dropdown-box"></div>
        </div>
    </div>
    <audio id="audio-player"></audio>
    <script>
        const cube = document.getElementById('cube');
        let mouseX = 0, mouseY = 0;
        let viewMode = 0; 
        document.addEventListener('mousemove', (e) => {
            mouseX = (e.clientX - window.innerWidth / 2) / 20;
            mouseY = (e.clientY - window.innerHeight / 2) / 20;
            render();
        });
        function toggleView() { viewMode = (viewMode === 0) ? 1 : 0; render(); }
        function render() {
            const rotX = viewMode === 0 ? -22 : 66;
            const rotY = viewMode === 0 ? 25 : 222;
            cube.style.transform = `rotateX(${-mouseY + rotX}deg) rotateY(${mouseX + rotY}deg)`;
        }

        async function generateCrossNet() {
            const canvas = document.createElement('canvas');
            canvas.width = 1100; canvas.height = 950;
            const ctx = canvas.getContext('2d');
            const data = {{ dice | tojson }};
            
            // 绘制干净底色
            ctx.fillStyle = "#f7f0e7"; ctx.fillRect(0, 0, 1100, 950);

            // 1. 依次6行严格拼接输出文字格式
            ctx.textAlign = "left";
            ctx.fillStyle = "#8a827c"; 
            ctx.font = "bold 24px Georgia";
            ctx.fillText("My Music Soul Dice", 50, 100);
            
            ctx.fillStyle = "#959292";
            ctx.font = "16px Georgia";
            for(let i=1; i<=6; i++) {
                let yPos = 700 + (i-1) * 35;
                let sideLabel = data[i].label || "未填写";
                let songName = data[i].song || "无歌曲";
                ctx.fillText(`0${i}  ${sideLabel} : ${songName}`, 37, yPos);
            }

            // 2. 十字架布局部分
            const offsetX = 450; 
            const offsetY = 50; 
            const pos = { 
                '1': [offsetX + 200, offsetY + 50],  
                '2': [offsetX + 200, offsetY + 650], 
                '3': [offsetX + 0,   offsetY + 250], 
                '4': [offsetX + 400, offsetY + 250], 
                '5': [offsetX + 200, offsetY + 250], 
                '6': [offsetX + 200, offsetY + 450]  
            };
            
            // 完美的圆角矩形，四个角绝对圆润饱满
            function drawRoundedRect(x,y,w,h,r) {
                ctx.beginPath();
                ctx.moveTo(x+r,y); 
                ctx.lineTo(x+w-r,y); 
                ctx.quadraticCurveTo(x+w,y,x+w,y+r);
                ctx.lineTo(x+w,y+h-r); 
                ctx.quadraticCurveTo(x+w,y+h,x+w-r,y+h);
                ctx.lineTo(x+r,y+h); 
                ctx.quadraticCurveTo(x,y+h,x,y+h-r);
                ctx.lineTo(x,y+r); 
                ctx.quadraticCurveTo(x,y,x+r,y);
                ctx.closePath();
            }

            for(let i=1; i<=6; i++) {
                let [x, y] = pos[i];
                ctx.save();
                drawRoundedRect(x, y, 200, 200, 32);
                ctx.clip();
                if(data[i].pic) {
                    const img = new Image(); img.crossOrigin = "anonymous";
                    img.src = data[i].pic;
                    try {
                        await new Promise(r => img.onload = r);
                        ctx.drawImage(img, x, y, 200, 200);
                        ctx.fillStyle = "rgba(255, 252, 247, 0.35)"; ctx.fillRect(x, y, 200, 200);
                    } catch(e) {
                        ctx.fillStyle = "rgba(255, 252, 247, 0.6)"; ctx.fillRect(x, y, 200, 200);
                    }
                } else {
                    ctx.fillStyle = "rgba(255, 252, 247, 0.6)"; ctx.fill();
                    ctx.fillStyle = "#1a1a1a"; ctx.font = "65px Georgia"; ctx.textAlign = "center";
                    ctx.fillText("𝄞", x+100, y+120);
                }
                ctx.restore();
                ctx.strokeStyle = "#e0d7cd"; ctx.lineWidth=2; ctx.stroke();
                
                ctx.textAlign = "center";
                ctx.fillStyle = "#a19790"; ctx.font = "11px Georgia";
                ctx.fillText(data[i].label.toUpperCase(), x+100, y+70);
                // === 👇 智能换行核心算法 👇 ===
                ctx.fillStyle = "#2c2a29"; ctx.font = "600 13px Georgia";
                let songText = data[i].song || "";
                let lines = [];
                let currentLine = "";

                // 逐字计算宽度，超过 170px（留出边距）就切到下一行
                for (let j = 0; j < songText.length; j++) {
                    let testLine = currentLine + songText[j];
                    if (ctx.measureText(testLine).width > 170 && j > 0) {
                        lines.push(currentLine);
                        currentLine = songText[j];
                    } else {
                        currentLine = testLine;
                    }
                }
                lines.push(currentLine);

                // 根据最终行数，动态调整 Y 轴坐标避免重叠
                if (lines.length > 1) {
                    // 【双行模式】第一行往上移到 y+94
                    ctx.fillText(lines[0], x+100, y+94);
                    
                    // 第二行如果还超长，尾部自动掐掉加省略号
                    let secondLine = lines[1];
                    if (lines.length > 2 || ctx.measureText(secondLine).width > 170) {
                        while(ctx.measureText(secondLine + "...").width > 170 && secondLine.length > 0) {
                            secondLine = secondLine.slice(0, -1);
                        }
                        secondLine += "...";
                    }
                    ctx.fillText(secondLine, x+100, y+112); // 第二行在 y+112
                    
                    // 歌手名字自动顺延顺挪到 y+132
                    ctx.fillStyle = "#7a7571"; ctx.font = "italic 11px Georgia";
                    ctx.fillText(data[i].artist, x+100, y+132);
                } else {
                    // 【单行模式】保持你原本完美的居中位置不动
                    ctx.fillText(lines[0] || "无歌曲", x+100, y+100);
                    
                    ctx.fillStyle = "#7a7571"; ctx.font = "italic 11px Georgia";
                    ctx.fillText(data[i].artist, x+100, y+120);
                }
                // === 👆 智能换行核心算法结束 👆 ===
            }
            
            // 🌟【完美比例顶层淡淡水印】在方块全部画完后压轴登场，绝不拉伸
            try {
                const madonnaImg = new Image();
                madonnaImg.src = '/madonna_bg.png?t=' + new Date().getTime(); 
                await new Promise((resolve, reject) => {
                    madonnaImg.onload = resolve;
                    madonnaImg.onerror = reject;
                });
                ctx.save();
                ctx.globalCompositeOperation = 'multiply'; // 开启正片叠底模式完美融合
                ctx.globalAlpha = 0.28; // 👈 降低透明度，呈现极具高级感的隐隐约约效果
                
                // 💡 核心修复：保持原图 650x950 的完美比例不拉伸！
                // 将起始点挪到 X=450，刚好完美覆盖右侧整个十字架区域（450 + 650 = 1100 画布总宽）
                ctx.drawImage(madonnaImg, -10, 0, 650, 950); 
                
                ctx.restore(); 
            } catch(e) {
                console.warn("前端Canvas未能从后端成功获取到圣母像：", e);
            }
            
            const link = document.createElement('a');
            link.download = 'my-music-dice.png';
            link.href = canvas.toDataURL();
            link.click();
        }

        function selectSide(i) {
            document.getElementById('current-side').value = i;
            document.getElementById('panel-title').innerText = 'SCULPTING: SIDE 0' + i;
            fetch('/get_side/' + i).then(r=>r.json()).then(d=> document.getElementById('node-label').value = d.label);
        }
        function syncLabel(val) {
            const i = document.getElementById('current-side').value;
            document.getElementById('label-' + i).innerText = val;
            fetch('/save_side', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({side:i, label:val})});
        }
        function toggleAudio(btn, url) {
            const player = document.getElementById('audio-player');
            if (player.src !== url) { player.src = url; player.play(); document.querySelectorAll('.play-btn').forEach(b => b.innerText = '▶'); btn.innerText = '⏸'; }
            else if (player.paused) { player.play(); btn.innerText = '⏸'; }
            else { player.pause(); btn.innerText = '▶'; }
        }
        function instantSearch(val) {
            const box = document.getElementById('dropdown-box');
            if(!val.trim()) { box.style.display = 'none'; return; }
            box.style.display = 'block';
            fetch('/api_search?w='+encodeURIComponent(val)).then(r=>r.json()).then(res => {
                box.innerHTML = '';
                res.forEach(item => {
                    const row = document.createElement('div'); row.className = 'search-row';
                    row.innerHTML = `<img src="${item.pic}"><div style="flex:1">${item.name}</div><div class="play-btn" onclick="event.stopPropagation(); toggleAudio(this, '${item.preview}');">▶</div>`;
                    row.onclick = () => {
                        const i = document.getElementById('current-side').value;
                        fetch('/save_side', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({side:i, song:item.name, artist:item.artist, pic:item.pic})}).then(() => location.reload());
                    };
                    box.appendChild(row);
                });
            });
        }
    </script>
</body>
</html>
"""

@app.route('/madonna_bg.png')
def get_madonna():
    print(f"========== 后端正在尝试通过绝对路径读取圣母像: {MADONNA_ABS_PATH} ==========")
    if os.path.exists(MADONNA_ABS_PATH):
        return send_file(MADONNA_ABS_PATH)
    print("❌ 警告：在上述绝对路径下依然找不到该图片！请检查文件名是否100%匹配。")
    return "Image not found", 404

@app.route('/')
def index(): return render_template_string(INDEX_HTML, dice=load_memory())

@app.route('/get_side/<int:side_num>')
def get_side(side_num): return jsonify(load_memory().get(str(side_num), {}))

@app.route('/save_side', methods=['POST'])
def save_side():
    d = request.json
    m = load_memory()
    side = str(d.get('side'))
    if side in m: m[side].update(d); save_memory(m)
    return jsonify({"status": "success"})

@app.route('/api_search')
def api_search():
    w = request.args.get('w', '')
    url = f"https://itunes.apple.com/search?term={urllib.parse.quote(w)}&entity=song&limit=6"
    data = requests.get(url).json()
    return jsonify([{"name": s['trackName'], "artist": s['artistName'], "pic": s['artworkUrl100'], "preview": s['previewUrl']} for s in data['results']])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)