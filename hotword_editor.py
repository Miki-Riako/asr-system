# File: hotword_editor.py (Final Corrected & Standalone Version 5.0)
# To run: python hotword_editor.py
# Then open your browser to http://127.0.0.1:8765

import os
import uvicorn
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any

# --- Configuration ---
HOST = "127.0.0.1"
PORT = 8765
HOTWORDS_FILENAME = "hotwords.txt"

# --- FastAPI App Initialization ---
app = FastAPI(title="Standalone Hotword Editor")

# --- HTML, CSS, JS Frontend (All in one file) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hotword Editor</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #1e1e1e; color: #d4d4d4; margin: 0; padding: 2rem; }
        .container { max-width: 800px; margin: auto; background-color: #252526; border: 1px solid #373737; border-radius: 8px; padding: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.4); }
        h1 { color: #4e94f7; border-bottom: 1px solid #373737; padding-bottom: 0.5rem; }
        .toolbar { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; background-color: #333; padding: 1rem; border-radius: 6px; margin-bottom: 1.5rem; gap: 1rem; }
        .actions button { margin-right: 1rem; }
        .stats { font-size: 0.9rem; color: #a0a0a0; }
        table { width: 100%; border-collapse: collapse; table-layout: fixed; }
        th, td { padding: 0.8rem 1rem; text-align: left; border-bottom: 1px solid #373737; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        th { background-color: #333; }
        td:first-of-type, th:first-of-type { width: 5%; }
        td:nth-of-type(2), th:nth-of-type(2) { width: 60%; white-space: normal; word-break: break-all; }
        tr:hover { background-color: #3c3c3c; }
        button { background-color: #4e94f7; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 5px; cursor: pointer; font-size: 0.9rem; transition: background-color 0.2s; }
        button:hover { background-color: #68a5f8; }
        button.danger { background-color: #f44336; }
        button.danger:hover { background-color: #f66a60; }
        button.success { background-color: #4CAF50; }
        button.success:hover { background-color: #66bb6a; }
        button:disabled { background-color: #555; cursor: not-allowed; }
        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; z-index: 1000; visibility: hidden; opacity: 0; transition: visibility 0s 0.3s, opacity 0.3s; }
        .modal-overlay.visible { visibility: visible; opacity: 1; transition: visibility 0s, opacity 0.3s; }
        .modal-content { background: #252526; padding: 2rem; border-radius: 8px; width: 90%; max-width: 500px; box-shadow: 0 5px 15px rgba(0,0,0,0.5); }
        .modal-title { font-size: 1.5rem; margin-bottom: 1.5rem; }
        .form-group { margin-bottom: 1.5rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; color: #a0a0a0; }
        input[type="text"], input[type="number"] { width: calc(100% - 20px); padding: 10px; background: #333; border: 1px solid #555; color: #d4d4d4; border-radius: 4px; }
        .modal-actions { text-align: right; }
        .slider-container { display: flex; align-items: center; gap: 1rem; }
        input[type="range"] { flex-grow: 1; }
    </style>
</head>
<body>
    <div class="container">
        <h1>热词编辑器 (hotwords.txt)</h1>
        <div class="toolbar">
            <div class="actions">
                <button id="add-btn">＋ 添加热词</button>
                <button id="import-btn" class="success">批量导入</button>
                <button id="batch-delete-btn" class="danger" disabled>批量删除 (0)</button>
                <input type="file" id="import-file-input" accept=".txt" style="display: none;">
            </div>
            <div id="stats" class="stats">共 0 个热词</div>
        </div>
        <table>
            <thead>
                <tr>
                    <th><input type="checkbox" id="select-all"></th>
                    <th>热词</th>
                    <th>权重</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody id="hotword-table-body"></tbody>
        </table>
    </div>

    <!-- Add/Edit Modal -->
    <div id="modal" class="modal-overlay">
        <div class="modal-content">
            <h2 class="modal-title">添加热词</h2>
            <div class="form-group">
                <label for="hotword-input">热词</label>
                <input type="text" id="hotword-input" placeholder="请输入热词">
            </div>
            <div class="form-group">
                <label for="weight-slider">权重</label>
                <div class="slider-container">
                    <input type="range" id="weight-slider" min="1" max="20" value="10">
                    <input type="number" id="weight-input" min="1" max="20" value="10" style="width: 60px;">
                </div>
            </div>
            <div class="modal-actions">
                <button id="cancel-btn" style="background-color: #555; margin-right: 1rem;">取消</button>
                <button id="save-btn">添加</button>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            let hotwords = [];

            const tableBody = document.getElementById('hotword-table-body');
            const stats = document.getElementById('stats');
            const modal = document.getElementById('modal');
            const hotwordInput = document.getElementById('hotword-input');
            const weightSlider = document.getElementById('weight-slider');
            const weightInput = document.getElementById('weight-input');
            const batchDeleteBtn = document.getElementById('batch-delete-btn');
            const selectAllCheckbox = document.getElementById('select-all');
            const fileInput = document.getElementById('import-file-input');

            const api = {
                getHotwords: async () => (await fetch('/api/hotwords')).json(),
                saveHotwords: async (data) => fetch('/api/hotwords', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                })
            };

            const render = () => {
                tableBody.innerHTML = '';
                hotwords.forEach(item => {
                    const row = tableBody.insertRow();
                    row.innerHTML = `
                        <td><input type="checkbox" class="row-checkbox" data-word="${item.word}"></td>
                        <td>${item.word}</td>
                        <td>${item.weight}</td>
                        <td><button class="danger delete-btn" data-word="${item.word}">删除</button></td>
                    `;
                });
                stats.textContent = `共 ${hotwords.length} 个热词`;
                updateBatchDeleteButton();
                selectAllCheckbox.checked = false;
            };

            const performUpdate = async (updateAction) => {
                try {
                    updateAction();  // 执行更新操作
                    const response = await api.saveHotwords(hotwords);
                    if (!response.ok) throw new Error('保存失败');
                    const result = await response.json();  // 获取返回的数据
                    hotwords = await api.getHotwords();  // 重新加载热词列表
                    render();  // 重新渲染界面
                } catch (error) {
                    alert(`操作失败: ${error.message}`);
                    await loadAndRender();  // 出错时重新加载
                }
            };

            const loadAndRender = async () => {
                try {
                    hotwords = await api.getHotwords();
                    render();
                } catch (error) {
                    alert('加载热词失败，请确保后端脚本正在运行。');
                }
            };

            const openModal = () => {
                hotwordInput.value = '';
                weightSlider.value = 10;
                weightInput.value = 10;
                modal.classList.add('visible');
                hotwordInput.focus();
            };
            
            const handleSave = () => {
                const word = hotwordInput.value.trim();
                const weight = parseInt(weightInput.value, 10);
                if (!word) return alert('热词不能为空');
                if (hotwords.some(h => h.word === word)) return alert('该热词已存在');
                
                performUpdate(() => {
                    hotwords.push({ word, weight });
                    hotwords.sort((a, b) => a.word.localeCompare(b.word, 'zh-CN'));
                });
                modal.classList.remove('visible');
            };

            const handleDelete = (word) => {
                performUpdate(() => {
                    hotwords = hotwords.filter(h => h.word !== word);
                });
            };

            const handleBatchDelete = () => {
                const selectedWords = new Set([...document.querySelectorAll('.row-checkbox:checked')].map(cb => cb.dataset.word));
                if (selectedWords.size > 0) {
                     performUpdate(() => {
                        hotwords = hotwords.filter(h => !selectedWords.has(h.word));
                    });
                }
            };

            const handleFileImport = (event) => {
                const file = event.target.files[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = (e) => {
                    const content = e.target.result;
                    const lines = content.split(/\\r?\\n/).filter(line => line.trim() !== '');
                    
                    performUpdate(() => {
                        const existingWords = new Set(hotwords.map(h => h.word));
                        lines.forEach(line => {
                            const parts = line.trim().split(/\\s+/);
                            if (parts.length >= 2) {
                                const weight = parseInt(parts[parts.length - 1], 10);
                                const word = parts.slice(0, -1).join(' ');
                                if (word && !isNaN(weight) && !existingWords.has(word)) {
                                    hotwords.push({ word, weight });
                                    existingWords.add(word);
                                }
                            }
                        });
                        hotwords.sort((a, b) => a.word.localeCompare(b.word, 'zh-CN'));
                    });
                };
                reader.readAsText(file);
                event.target.value = '';
            };
            
            const updateBatchDeleteButton = () => {
                const selectedCount = document.querySelectorAll('.row-checkbox:checked').length;
                batchDeleteBtn.textContent = `批量删除 (${selectedCount})`;
                batchDeleteBtn.disabled = selectedCount === 0;
            };

            // --- Attach Event Listeners ---
            document.getElementById('add-btn').addEventListener('click', openModal);
            document.getElementById('cancel-btn').addEventListener('click', () => modal.classList.remove('visible'));
            document.getElementById('save-btn').addEventListener('click', handleSave);
            document.getElementById('import-btn').addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', handleFileImport);
            
            weightSlider.addEventListener('input', () => weightInput.value = weightSlider.value);
            weightInput.addEventListener('input', () => weightSlider.value = weightInput.value);

            tableBody.addEventListener('click', e => {
                if (e.target.classList.contains('delete-btn')) handleDelete(e.target.dataset.word);
                if (e.target.classList.contains('row-checkbox')) updateBatchDeleteButton();
            });
            
            batchDeleteBtn.addEventListener('click', handleBatchDelete);

            selectAllCheckbox.addEventListener('change', e => {
                document.querySelectorAll('.row-checkbox').forEach(cb => cb.checked = e.target.checked);
                updateBatchDeleteButton();
            });

            loadAndRender();
        });
    </script>
</body>
</html>
"""

# --- API Endpoints (Backend Logic) ---
@app.get("/", response_class=HTMLResponse)
async def get_root():
    """Serves the main HTML page."""
    return HTMLResponse(content=HTML_TEMPLATE)

@app.get("/api/hotwords", response_model=List[Dict[str, Any]])
def get_hotwords():
    """Reads and returns all hotwords from the file."""
    if not os.path.exists(HOTWORDS_FILENAME):
        return []
    try:
        hotwords_list = []
        with open(HOTWORDS_FILENAME, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                parts = line.rsplit(' ', 1)
                if len(parts) == 2:
                    word, weight_str = parts
                    if word and weight_str.isdigit():
                        hotwords_list.append({"word": word.strip(), "weight": int(weight_str)})
        return hotwords_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")

@app.post("/api/hotwords")
def save_hotwords(hotwords: List[Dict[str, Any]] = Body(...)):
    """保存热词到文件"""
    try:
        with open(HOTWORDS_FILENAME, "w", encoding="utf-8") as f:
            for item in hotwords:
                word = str(item.get("word", "")).strip()
                weight = int(item.get("weight", 10))
                if word:  # 只有热词不为空时才写入
                    f.write(f"{word} {weight}\n")  # 关键修改：每个热词单独一行
                    
        return {"message": "热词保存成功", "count": len(hotwords)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文件出错: {e}")

# --- Main Entry Point ---
if __name__ == "__main__":
    print("--- Standalone Hotword Editor ---")
    print(f"Starting server on http://{HOST}:{PORT}")
    print(f"Editing file: {os.path.abspath(HOTWORDS_FILENAME)}")
    print("Press CTRL+C to stop.")
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")