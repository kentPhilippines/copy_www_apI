import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.services.nginx_service import NginxService

def test_get_nginx_status(client):
    """测试获取Nginx状态"""
    response = client.get("/api/v1/nginx/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_running" in data

def test_create_site(client):
    """测试创建站点"""
    site_data = {
        "domain": "test.com",
        "root_path": "/var/www/test.com",
        "php_enabled": False
    }
    
    with patch.object(NginxService, 'create_site') as mock_create:
        mock_create.return_value = {"success": True, "message": "Site created"}
        response = client.post("/api/v1/nginx/sites", json=site_data)
        assert response.status_code == 200
        assert response.json()["success"] is True

def test_delete_site(client):
    """测试删除站点"""
    with patch.object(NginxService, 'delete_site') as mock_delete:
        mock_delete.return_value = {"success": True, "message": "Site deleted"}
        response = client.delete("/api/v1/nginx/sites/test.com")
        assert response.status_code == 200
        assert response.json()["success"] is True

def test_list_sites(client):
    """测试获取站点列表"""
    with patch.object(NginxService, 'list_sites') as mock_list:
        mock_list.return_value = [
            {
                "domain": "test.com",
                "root_path": "/var/www/test.com",
                "php_enabled": False
            }
        ]
        response = client.get("/api/v1/nginx/sites")
        assert response.status_code == 200
        assert len(response.json()) > 0

@pytest.mark.parametrize("domain,expected_status", [
    ("valid.com", 200),
    ("invalid", 422),
    ("", 422),
])
def test_validate_domain(client, domain, expected_status):
    """测试域名验证"""
    site_data = {
        "domain": domain,
        "root_path": f"/var/www/{domain}",
        "php_enabled": False
    }
    
    response = client.post("/api/v1/nginx/sites", json=site_data)
    assert response.status_code == expected_status

def test_nginx_config_generation():
    """测试Nginx配置生成"""
    from app.utils.nginx import generate_nginx_config
    from app.schemas.nginx import NginxSite
    
    site = NginxSite(
        domain="test.com",
        root_path="/var/www/test.com",
        php_enabled=True
    )
    
    config = generate_nginx_config(site)
    assert "server_name test.com" in config
    assert "root /var/www/test.com" in config
    assert "fastcgi_pass" in config

def test_nginx_service_error_handling(client):
    """测试错误处理"""
    with patch.object(NginxService, 'create_site') as mock_create:
        mock_create.side_effect = Exception("Test error")
        response = client.post("/api/v1/nginx/sites", json={
            "domain": "test.com",
            "root_path": "/var/www/test.com"
        })
        assert response.status_code == 400
        assert "error" in response.json()

def test_nginx_reload(client):
    """测试Nginx重载配置"""
    with patch.object(NginxService, 'reload') as mock_reload:
        mock_reload.return_value = {"success": True, "message": "Reloaded"}
        response = client.post("/api/v1/nginx/reload")
        assert response.status_code == 200
        assert response.json()["success"] is True 