from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """加载指定名称的 prompt 模板内容。

    Args:
        name: prompt 文件名（不含 .txt 后缀），如 "planner"、"architect"。

    Returns:
        prompt 文件的完整文本内容。

    Raises:
        FileNotFoundError: 指定的 prompt 文件不存在。
    """
    path = _PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")
