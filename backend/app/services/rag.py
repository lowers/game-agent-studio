"""RAG 知识库服务 — 使用 ChromaDB 检索相似经验。"""
from pathlib import Path

_wiki_root = Path(__file__).resolve().parents[3] / "llm_wiki"


def get_wiki_root() -> Path:
    return _wiki_root


def list_wiki_docs() -> list[dict]:
    """列出 llm_wiki 下的所有文档。"""
    docs = []
    for p in _wiki_root.rglob("*.md"):
        rel = p.relative_to(_wiki_root)
        docs.append({"path": str(rel), "name": p.stem})
    for p in _wiki_root.rglob("*.yaml"):
        rel = p.relative_to(_wiki_root)
        docs.append({"path": str(rel), "name": p.stem})
    return docs


def read_wiki_doc(relative_path: str) -> str:
    """读取指定文档内容。

    安全措施：验证解析后的路径仍在 _wiki_root 目录内，防止路径遍历攻击。
    """
    full = (_wiki_root / relative_path).resolve()

    # 防止路径遍历：确保解析后的路径仍在允许的根目录下
    if not full.is_relative_to(_wiki_root.resolve()):
        raise ValueError(f"非法路径：{relative_path} 超出知识库根目录")

    if not full.exists():
        return ""
    return full.read_text(encoding="utf-8")
