#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from pathlib import Path
import pathspec
from tqdm import tqdm

# --- 配置部分 (无变化) ---
DEFAULT_EXCLUDE_PATTERNS = [
    "*.pyc", "__pycache__/", "*.o", "*.a", "*.so", "*.lib", "*.dll", "*.exe",
    ".idea/", ".vscode/", ".project", ".classpath", ".settings/", "node_modules/", "venv/", ".venv/",
    "*.log", "*.tmp", "*.bak", "*.swp",
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.svg", "*.ico",
    "*.mp4", "*.mov", "*.avi", "*.mkv", "*.mp3", "*.wav", "*.flac",
    "*.zip", "*.tar.gz", "*.rar", "*.7z", "*.gz", "*.bz2",
    "*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx", "*.ppt", "*.pptx", "*.db", "*.sqlite3",
    "*.txt", "*.json"
]
DEFAULT_MAX_FILE_SIZE = 200 * 1024
LANGUAGE_MAP = {
    ".py": "python", ".pyw": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".c": "c", ".h": "c", ".cpp": "cpp",
    ".hpp": "cpp", ".cxx": "cpp", ".java": "java", ".go": "go", ".rs": "rust",
    ".rb": "ruby", ".php": "php", ".cs": "csharp", ".swift": "swift", ".kt": "kotlin",
    ".scala": "scala", ".sh": "shell", ".bash": "shell", ".ps1": "powershell",
    ".bat": "batch", ".sql": "sql", ".html": "html", ".htm": "html", ".css": "css",
    ".json": "json", ".xml": "xml", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
    ".md": "markdown", ".markdown": "markdown", ".rst": "rst", ".txt": "text",
    "Dockerfile": "dockerfile", ".env": "ini", ".ini": "ini", ".conf": "ini",
}

# --- 辅助函数 ---
def get_language_identifier(filepath: Path) -> str:
    if filepath.name in LANGUAGE_MAP: return LANGUAGE_MAP[filepath.name]
    return LANGUAGE_MAP.get(filepath.suffix.lower(), "text")

def is_likely_binary(filepath: Path, chunk_size=1024) -> bool:
    try:
        with open(filepath, 'rb') as f: return b'\0' in f.read(chunk_size)
    except IOError: return True

def find_git_root(start_path: Path) -> Path:
    current_path = start_path.resolve()
    while current_path != current_path.parent:
        if (current_path / ".git").is_dir(): return current_path
        current_path = current_path.parent
    return start_path.resolve()

# 【【【BUG已彻底修复的函数】】】
def load_gitignore_rules(git_root: Path) -> pathspec.PathSpec:
    """
    只加载项目根目录的.gitignore文件。这避免了子目录中
    的.gitignore文件（如submodule或依赖包）的规则对整个项目造成污染。
    """
    gitignore_path = git_root / '.gitignore'
    rules = []
    if gitignore_path.is_file():
        try:
            with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
                rules = [line for line in (l.strip() for l in f) if line and not line.startswith('#')]
        except IOError:
            pass # 无法读取则忽略
    return pathspec.PathSpec.from_lines('gitwildmatch', rules)

# --- 主处理函数 (逻辑已验证正确) ---
def process_project(project_root: str, output_file: str, extra_excludes: list, max_size: int,
                    include_exts: set = None, verbose: bool = False):
    root_path = Path(project_root).resolve()
    if not root_path.is_dir():
        print(f"错误: 路径 '{project_root}' 不是一个有效的目录。", file=sys.stderr); sys.exit(1)

    git_root = find_git_root(root_path)
    if verbose:
        print(f"项目根目录: {root_path}", file=sys.stderr)
        print(f"Git根目录: {git_root}", file=sys.stderr)
        print("🔍 正在加载 .gitignore 规则...", file=sys.stderr)
    
    gitignore_spec = load_gitignore_rules(git_root)
    custom_spec = pathspec.PathSpec.from_lines('gitwildmatch', extra_excludes)

    if verbose: print("📂 正在扫描项目文件...", file=sys.stderr)
    
    filtered_files = []
    # 使用os.walk进行遍历，性能和控制力都很好
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True, followlinks=False):
        current_dir_path = Path(dirpath)
        
        # 过滤目录：原地修改dirnames列表，os.walk就不会再进入这些目录
        dirs_to_keep = []
        for d in dirnames:
            dir_path_for_check = current_dir_path.relative_to(root_path) / d
            dir_path_str = dir_path_for_check.as_posix()
            
            # 检查目录时，在末尾添加斜杠'/'
            if gitignore_spec.match_file(dir_path_str + '/') or custom_spec.match_file(dir_path_str + '/'):
                continue
            else:
                dirs_to_keep.append(d)
        dirnames[:] = dirs_to_keep

        # 过滤文件
        for f in filenames:
            file_path = current_dir_path / f
            file_path_for_check = file_path.relative_to(root_path)
            file_path_str = file_path_for_check.as_posix()
            
            if gitignore_spec.match_file(file_path_str) or custom_spec.match_file(file_path_str):
                continue
            else:
                filtered_files.append(file_path)

    # 准备输出
    output_stream = open(output_file, 'w', encoding='utf-8') if output_file else sys.stdout
    try:
        file_iterator = tqdm(filtered_files, desc="🚀 处理文件中", unit="file", disable=not verbose, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]")
        
        for filepath in file_iterator:
            if include_exts and filepath.suffix.lower() not in include_exts: continue
            
            relative_path_str = filepath.relative_to(root_path).as_posix()
            
            try:
                file_size = filepath.stat().st_size
                if file_size > max_size:
                    print(f"File: {relative_path_str}  (Skipped, size > {max_size / 1024:.0f}KB)", file=output_stream); print("\n" + "-"*80 + "\n", file=output_stream)
                    continue
                
                content = ""
                if file_size > 0:
                    if is_likely_binary(filepath): continue
                    content = filepath.read_text(encoding='utf-8')

            except (IOError, OSError, UnicodeDecodeError): continue
            
            language = get_language_identifier(filepath)
            print(f"File: {relative_path_str}", file=output_stream)
            print(f"```{language}", file=output_stream); print(content.strip(), file=output_stream); print("```", file=output_stream)
            print("\n" + "-"*80 + "\n", file=output_stream)
    finally:
        if output_file:
            output_stream.close()
            if verbose: print(f"✅ 处理完成，输出已保存到: {output_file}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="从项目目录中提取可读源代码和文本文件，格式化后输出以供LLM分析。", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("project_root", help="要扫描的项目根目录路径。")
    parser.add_argument("-o", "--output", help="输出文件的路径。如果未指定，则输出到标准输出 (stdout)。")
    parser.add_argument("--exclude", nargs='*', default=DEFAULT_EXCLUDE_PATTERNS, help="要额外排除的文件/目录的 glob 模式列表。")
    parser.add_argument("--include-ext", nargs='*', help="仅包含指定扩展名的文件 (白名单模式)。")
    parser.add_argument("--max-size", type=int, default=DEFAULT_MAX_FILE_SIZE, help=f"文件内容的最大大小（字节）。")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细处理信息和进度条。")
    
    args = parser.parse_args()
    include_exts_set = {ext if ext.startswith('.') else '.' + ext.lower() for ext in args.include_ext} if args.include_ext else None

    process_project(project_root=args.project_root, output_file=args.output, extra_excludes=args.exclude,
                    max_size=args.max_size, include_exts=include_exts_set, verbose=args.verbose)

if __name__ == "__main__":
    main()