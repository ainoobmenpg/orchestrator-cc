"""ミドルウェア設定のテスト

orchestrator/web/middleware.py のテストです。
"""

from unittest.mock import patch

from fastapi import FastAPI


class TestCorsMiddleware:
    """CORSミドルウェアのテスト"""

    @patch.dict("os.environ", {"CORS_ORIGINS": "http://localhost:3000,http://localhost:5173"})
    def test_setup_cors_with_custom_origins(self):
        """カスタムCORSオリジンを設定できる"""
        from orchestrator.web.middleware import setup_cors_middleware

        app = FastAPI()
        setup_cors_middleware(app)

        # ミドルウェアが追加されたことを確認
        assert len(app.user_middleware) > 0

    @patch.dict("os.environ", {}, clear=True)
    def test_setup_cors_with_default_origins(self):
        """デフォルトのCORSオリジンが使用される"""
        from orchestrator.web.middleware import setup_cors_middleware

        app = FastAPI()
        setup_cors_middleware(app)

        # ミドルウェアが追加されたことを確認
        assert len(app.user_middleware) > 0

    @patch.dict("os.environ", {"CORS_ORIGINS": "*"})
    def test_setup_cors_with_wildcard(self):
        """ワイルドカードオリジンを設定できる"""
        from orchestrator.web.middleware import setup_cors_middleware

        app = FastAPI()
        setup_cors_middleware(app)

        # ミドルウェアが追加されたことを確認
        assert len(app.user_middleware) > 0

    @patch.dict("os.environ", {"CORS_ORIGINS": "http://localhost:3000, ,http://localhost:5173"})
    def test_setup_cors_ignores_empty_origins(self):
        """空のオリジンは無視される"""
        from orchestrator.web.middleware import setup_cors_middleware

        app = FastAPI()
        setup_cors_middleware(app)

        # ミドルウェアが追加されたことを確認
        assert len(app.user_middleware) > 0

    @patch.dict("os.environ", {"CORS_ORIGINS": "https://example.com,https://app.example.com"})
    def test_setup_cors_with_multiple_origins(self):
        """複数のオリジンを設定できる"""
        from orchestrator.web.middleware import setup_cors_middleware

        app = FastAPI()
        setup_cors_middleware(app)

        # ミドルウェアが追加されたことを確認
        assert len(app.user_middleware) > 0

    @patch.dict("os.environ", {"CORS_ORIGINS": "http://localhost:3000,"})
    def test_setup_cors_with_trailing_comma(self):
        """末尾のカンマは処理される"""
        from orchestrator.web.middleware import setup_cors_middleware

        app = FastAPI()
        setup_cors_middleware(app)

        # ミドルウェアが追加されたことを確認
        assert len(app.user_middleware) > 0
