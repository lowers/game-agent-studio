import os
from pathlib import Path

# Load .env file
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ[key.strip()] = value.strip()

# Now run uvicorn (CLI 模式，自动安装信号处理器，支持优雅关闭)
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("UVICORN_PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
        # 优雅关闭：收到 SIGTERM 后等待现有请求完成（默认 10s）
        # CLI 模式下 uvicorn 会自动安装信号处理器处理 SIGTERM/SIGINT
    )
