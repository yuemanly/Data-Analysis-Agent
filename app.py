#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Business Analyst Agent — entry point.
Run:  python app.py
Then: http://localhost:5001
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from api import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("AGENT_PORT", 5001))
    print(f"\n  Business Analyst Agent  →  http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=True)
