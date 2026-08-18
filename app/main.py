"""PratikAI backend entry point.

Run with: venv\\Scripts\\python.exe -m app.main
(or via scripts/start.ps1, which also handles the frontend and Ollama).
"""

from __future__ import annotations

import uvicorn

from app.core.config import get_settings
from app.core.logging import configure_logging


def main() -> None:
    configure_logging()
    settings = get_settings()
    uvicorn.run(
        "app.api.server:app",
        host=settings.backend.host,
        port=settings.backend.port,
        reload=False,
        # Keep uvicorn's default logging (not log_config=None) so unhandled
        # exception tracebacks still reach stderr — app.core.logging adds
        # our own "pratikai.*" file logging alongside it, not instead of it.
    )


if __name__ == "__main__":
    main()
