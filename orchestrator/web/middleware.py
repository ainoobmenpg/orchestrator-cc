"""ミドルウェア設定

このモジュールでは、FastAPIアプリケーションのミドルウェア設定を提供します。
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors_middleware(app: FastAPI) -> None:
    """CORSミドルウェアを設定します。

    環境変数からCORSオリジンを取得（デフォルト: localhost:8000 と localhost:5173）。

    Args:
        app: FastAPIアプリケーションインスタンス
    """
    cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://localhost:5173")
    cors_origins: list[str] = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

    # 開発環境向けのワイルドカードが指定されている場合は全許可
    if "*" in cors_origins:
        cors_origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
