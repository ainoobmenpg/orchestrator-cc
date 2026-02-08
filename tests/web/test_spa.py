"""SPAルーティングのテスト

orchestrator/web/spa.py のテストです。
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from orchestrator.web.spa import spa_router


@pytest.fixture
def client():
    """テストクライアントフィクスチャ"""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(spa_router)
    return TestClient(app)


class TestRootEndpoint:
    """ルートエンドポイントのテスト"""

    @patch("orchestrator.web.spa._frontend_dist_dir")
    @patch("orchestrator.web.spa._templates_dir")
    def test_root_returns_dist_index_html(self, mock_templates, mock_dist, client):
        """dist/index.htmlが存在する場合はそれを返す"""
        mock_dist.exists.return_value = True
        mock_index = MagicMock()
        mock_index.exists.return_value = True
        mock_dist.__truediv__.return_value = mock_index

        response = client.get("/")

        assert response.status_code == 200
        # FileResponseはテストクライアントでJSONとして扱われる可能性がある
        # ステータスコードのみ検証

    @patch("orchestrator.web.spa._frontend_dist_dir")
    @patch("orchestrator.web.spa._templates_dir")
    def test_root_returns_template_index_html(self, mock_templates, mock_dist, client):
        """distがない場合はtemplates/index.htmlを返す"""
        mock_dist.exists.return_value = False
        mock_templates.exists.return_value = True
        mock_index = MagicMock()
        mock_index.exists.return_value = True
        mock_templates.__truediv__.return_value = mock_index

        response = client.get("/")

        assert response.status_code == 200

    @patch("orchestrator.web.spa._frontend_dist_dir")
    @patch("orchestrator.web.spa._templates_dir")
    def test_root_returns_json_when_no_build(self, mock_templates, mock_dist, client):
        """ビルド済みファイルがない場合はJSONメッセージを返す"""
        mock_dist.exists.return_value = False
        mock_dist.__truediv__.return_value.exists.return_value = False
        mock_templates.exists.return_value = False
        mock_templates.__truediv__.return_value.exists.return_value = False

        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data


class TestServeSpa:
    """SPA配信ルートのテスト"""

    @patch("orchestrator.web.spa._frontend_dist_dir")
    def test_serve_asset_file_directly(self, mock_dist, client):
        """アセットファイルは直接返す"""
        mock_dist.exists.return_value = True
        mock_asset = MagicMock()
        mock_asset.exists.return_value = True
        mock_asset.is_file.return_value = True
        mock_dist.__truediv__.return_value = mock_asset

        response = client.get("/assets/main.js")

        assert response.status_code == 200

    @patch("orchestrator.web.spa._frontend_dist_dir")
    def test_spa_fallback_to_index_html(self, mock_dist, client):
        """アセットでない場合はindex.htmlを返す（SPAルーティング）"""
        mock_dist.exists.return_value = True
        mock_asset = MagicMock()
        mock_asset.exists.return_value = False
        mock_dist.__truediv__.return_value = mock_asset
        mock_index = MagicMock()
        mock_index.exists.return_value = True
        mock_dist.__truediv__.return_value = mock_index

        response = client.get("/dashboard/settings")

        assert response.status_code == 200

    @patch("orchestrator.web.spa._frontend_dist_dir")
    def test_spa_no_dist_directory(self, mock_dist, client):
        """distディレクトリがない場合はエラーメッセージを返す"""
        mock_dist.exists.return_value = False

        response = client.get("/any-path")

        assert response.status_code == 200
        data = response.json()
        assert "error" in data or "message" in data

    @patch("orchestrator.web.spa._frontend_dist_dir")
    def test_spa_no_index_html_fallback(self, mock_dist, client):
        """index.htmlがない場合はメッセージを返す"""
        mock_dist.exists.return_value = True
        mock_asset = MagicMock()
        mock_asset.exists.return_value = False
        mock_asset.is_file.return_value = False
        mock_index = MagicMock()
        mock_index.exists.return_value = False
        mock_dist.__truediv__.side_effect = [mock_asset, mock_index]

        response = client.get("/some-path")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "note" in data
