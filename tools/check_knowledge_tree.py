#!/usr/bin/env python3
"""检查 framework/ 和 repos/ 的目录、索引与 Markdown 链接。"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_ROOTS = (ROOT / "framework", ROOT / "repos")
INDEX_NAME = "_index.md"
SPECIAL_PAGES = {INDEX_NAME, "rules.md", "architecture.md"}
GROUP_DIRS = {"guides", "history", "incidents", "references", "results", "rfcs"}
INCIDENT_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*\.md$")
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
INCIDENT_FIELDS = ("- 编号：", "- 归属：", "- 状态：", "- 搜索词：", "- 影响范围：")
INCIDENT_STATES = ("待归类", "处理中", "已验证", "已提炼", "仅历史")
PRIVATE_IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
WINDOWS_USER_PATH = re.compile(r"[A-Za-z]:\\Users\\[^\\\s`]+", re.IGNORECASE)
REMOTE_USER_PATH = re.compile(
    r"/(?:home/(?!models(?:/|\b)|<)|data/(?!models?(?:/|\b)|<))"
    r"[A-Za-z0-9_-]+"
)


errors: list[str] = []
warnings: list[str] = []
incident_ids: dict[str, Path] = {}


def display(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def markdown_links(path: Path) -> list[str]:
    """提取代码块之外的 Markdown 链接目标。"""
    links: list[str] = []
    in_fence = False
    fence_marker = ""
    for line in read_text(path).splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            continue
        if in_fence:
            continue
        links.extend(match.group(1).strip() for match in MARKDOWN_LINK.finditer(line))
    return links


def local_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    elif " " in target:
        target = target.split(" ", 1)[0]
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return None
    return unquote(target.split("#", 1)[0])


def check_links(path: Path) -> None:
    for raw_target in markdown_links(path):
        target = local_target(raw_target)
        if not target:
            continue
        if target.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[\\/]", target):
            errors.append(f"绝对路径链接：{display(path)} -> {target}")
            continue
        resolved = (path.parent / target).resolve()
        if not resolved.exists():
            errors.append(f"链接不存在：{display(path)} -> {target}")


def has_markdown(path: Path) -> bool:
    return any(path.rglob("*.md"))


def check_file_size(path: Path, index_text: str) -> None:
    text = read_text(path)
    non_empty_lines = sum(1 for line in text.splitlines() if line.strip())
    byte_size = path.stat().st_size
    if non_empty_lines >= 500 or byte_size >= 32 * 1024:
        has_exception = path.name in index_text and "暂不拆分" in index_text
        if not has_exception:
            errors.append(
                f"文件必须拆分：{display(path)} "
                f"({non_empty_lines} 个非空行，{byte_size} bytes)"
            )
    elif non_empty_lines >= 300 or byte_size >= 16 * 1024:
        warnings.append(
            f"文件接近拆分线：{display(path)} "
            f"({non_empty_lines} 个非空行，{byte_size} bytes)"
        )


def check_sensitive_text(path: Path) -> None:
    text = read_text(path)
    for match in PRIVATE_IPV4.finditer(text):
        if not match.group(0).startswith("127."):
            errors.append(f"页面包含真实 IPv4，请改成 <REMOTE_HOST>：{display(path)}")
            break
    if WINDOWS_USER_PATH.search(text):
        errors.append(f"页面包含用户目录，请改成 <USER_HOME>：{display(path)}")
    if REMOTE_USER_PATH.search(text):
        errors.append(
            f"页面包含远端用户目录，请改成 <REMOTE_WORK_ROOT>：{display(path)}"
        )
    if "-----BEGIN PRIVATE KEY-----" in text:
        errors.append(f"页面包含私钥内容：{display(path)}")


def check_incident(path: Path) -> None:
    if not INCIDENT_NAME.match(path.name):
        errors.append(f"错题文件名不符合 YYYY-MM-DD-short-name.md：{display(path)}")
    text = read_text(path)
    for field in INCIDENT_FIELDS:
        if field not in text:
            errors.append(f"错题缺少字段 {field}：{display(path)}")
    status_line = next(
        (line for line in text.splitlines() if line.startswith("- 状态：")), ""
    )
    if status_line and not any(state in status_line for state in INCIDENT_STATES):
        errors.append(f"错题状态不合法：{display(path)}")
    id_match = re.search(r"^- 编号：`([^`]+)`", text, re.MULTILINE)
    if id_match:
        incident_id = id_match.group(1)
        previous = incident_ids.get(incident_id)
        if previous is not None:
            errors.append(
                f"错题编号重复：{incident_id} 同时出现在 "
                f"{display(previous)} 和 {display(path)}"
            )
        else:
            incident_ids[incident_id] = path


def check_directory(directory: Path) -> None:
    direct_pages = sorted(directory.glob("*.md"))
    child_dirs = sorted(
        child for child in directory.iterdir() if child.is_dir() and has_markdown(child)
    )
    if not direct_pages and not child_dirs:
        return

    index = directory / INDEX_NAME
    if not index.is_file():
        errors.append(f"目录缺少 {INDEX_NAME}：{display(directory)}")
        index_text = ""
    else:
        index_text = read_text(index)

    for page in direct_pages:
        check_links(page)
        check_file_size(page, index_text)
        check_sensitive_text(page)
        if page.name != INDEX_NAME and page.name not in index_text:
            errors.append(f"页面没有登记到当前目录索引：{display(page)}")
        if directory.name == "incidents" and page.name != INDEX_NAME:
            check_incident(page)

    for child in child_dirs:
        expected = f"{child.name}/{INDEX_NAME}"
        if expected not in index_text.replace("\\", "/"):
            errors.append(
                f"子目录没有登记到上一层索引：{display(child)} "
                f"(应在 {display(index)} 链接 {expected})"
            )

    ordinary_pages = [page for page in direct_pages if page.name not in SPECIAL_PAGES]
    is_group = directory.name in GROUP_DIRS or any(
        parent.name in GROUP_DIRS for parent in directory.parents
    )
    if len(ordinary_pages) > 7 and not is_group:
        warnings.append(
            f"目录有 {len(ordinary_pages)} 个普通页面，应该考虑分类：{display(directory)}"
        )
    if is_group and len(ordinary_pages) > 20:
        errors.append(
            f"分类目录有 {len(ordinary_pages)} 个页面，必须继续按主题整理：{display(directory)}"
        )


def check_local_is_untracked() -> None:
    result = subprocess.run(
        ["git", "ls-files", "--", "local"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        errors.append(f"无法检查 local/ 的 Git 状态：{result.stderr.strip()}")
        return
    tracked = [line for line in result.stdout.splitlines() if line.strip()]
    for path in tracked:
        errors.append(f"local/ 中存在被 Git 跟踪的文件：{path}")


def main() -> int:
    for root in KNOWLEDGE_ROOTS:
        if not root.is_dir():
            errors.append(f"缺少知识根目录：{display(root)}")
            continue
        for directory in sorted(path for path in root.rglob("*") if path.is_dir()):
            check_directory(directory)
        check_directory(root)

    excluded_parts = {
        ".git",
        "artifacts",
        "framework",
        "local",
        "outputs",
        "repos",
        "templates",
        "遗言",
    }
    for path in ROOT.rglob("*.md"):
        relative_parts = set(path.relative_to(ROOT).parts)
        if relative_parts & excluded_parts:
            continue
        check_links(path)
        check_sensitive_text(path)

    check_local_is_untracked()

    for message in warnings:
        print(f"提醒：{message}")
    for message in errors:
        print(f"错误：{message}")

    if errors:
        print(f"检查失败：{len(errors)} 个错误，{len(warnings)} 个提醒")
        return 1
    print(f"知识目录检查通过：0 个错误，{len(warnings)} 个提醒")
    return 0


if __name__ == "__main__":
    sys.exit(main())
