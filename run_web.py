#!/usr/bin/env python3
"""
Run the LEGO Architect web application.

Usage:
    python run_web.py [--host HOST] [--port PORT] [--reload]
"""

import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Run LEGO Architect web app")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    print(f"\n{'='*50}")
    print("  LEGO Architect Web Application")
    print(f"{'='*50}")
    print(f"\n  Open in browser: http://{args.host}:{args.port}")
    print(f"  API docs: http://{args.host}:{args.port}/docs")
    print(f"\n{'='*50}\n")

    uvicorn.run(
        "lego_architect.web.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
