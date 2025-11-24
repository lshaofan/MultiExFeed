#!/bin/bash
# exdatahub startup script

# 1. Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo ">> uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add to path for current session if needed (best effort)
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# 2. Ensure python version is pinned and dependencies are synced
if [ ! -d ".venv" ]; then
    echo ">> Initializing environment..."
    uv python install 3.12
    uv python pin 3.12
    uv sync
fi

# 3. Run the CLI
# Pass all arguments to the python script
uv run python -m exdatahub.cli.main "$@"
