#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google OAuth API 封装
完全照搬参考项目的实现
"""

import requests
import json
import time
import random
import string
import uuid
from typing import Dict, Optional, Tuple


class GoogleOAuthAPI:
    """Google OAuth API封装类"""
    
    def __init__(self, api_key="AIzaSyCI-zsRP85UVOi0DjtiCwWBwQ1djDy741g"):
        self.api_key = api_key
        self.session = requests.Session()
        self.cookies: Dict[str, str] = {}
        
    def set_cookies(self, cookie_string: str) -> bool:
        """设置Cookie"""
        try:
            if not cookie_string:
                return False
            
            # 解析Cookie字符串
            self.cookies = {}
            for item in cookie_string.split('; '):
                if '=' in item:
                    key, value = item.split('=', 1)
                    self.cookies[key] = value
                    self.session.cookies.set(key, value)
            
            return True
        except Exception as e:
            print(f"设置Cookie失败: {e}")
            return False
    
    def get_cookie_string(self) -> str:
        """获取Cookie字符串"""
        return '; '.join([f"{k}={v}" for k, v in self.cookies.items()])
    
    def generate_auth_header(self) -> str:
        """生成SAPISIDHASH认证头"""
        try:
            import hashlib
            sapisid = self.cookies.get('SAPISID', '')
            if not sapisid:
                return ""
            
            timestamp = str(int(time.time()))
            origin = "https://console.cloud.google.com"
            
            hash_string = f"{timestamp} {sapisid} {origin}"
            sha1_hash = hashlib.sha1(hash_string.encode()).hexdigest()
            
            return f"SAPISIDHASH {timestamp}_{sha1_hash}"
        except Exception as e:
            print(f"生成auth header失败: {e}")
            return ""
    
    def get_server_token(self) -> str:
        """生成x-server-token"""
        try:
            import hashlib
            timestamp = str(int(time.time() * 1000))
            hash_input = f"{timestamp}:AIzaSyCI-zsRP85UVOi0DjtiCwWBwQ1djDy741g"
            token = hashlib.md5(hash_input.encode()).hexdigest()
            return token
        except:
            return ""
    
    def get_first_party_reauth(self) -> str:
        """生成x-goog-first-party-reauth"""
        return str(int(time.time()))
    
    def get_current_user_email(self) -> Optional[str]:
        """获取当前登录用户的邮箱（照搬参考项目）"""
        try:
            # 方法1: 从Cookie中获取
            # Google的LOGIN_INFO cookie包含邮箱信息
            print("尝试从用户信息API获取邮箱...")
            
            url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {
                'Cookie': self.get_cookie_string(),
                'authorization': self.generate_auth_header()
            }
            
            response = self.session.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                email = data.get('email')
                if email:
                    print(f"✅ 获取到用户邮箱: {email}")
                    return email
            
            # 方法2: 从GraphQL获取
            print("尝试从GraphQL API获取邮箱...")
            url = "https://cloudconsole-pa.clients6.google.com/v3/entityServices/ConsoleUserService/userInfo"
            params = {"key": self.api_key}
            headers = {
                'Cookie': self.get_cookie_string(),
                'authorization': self.generate_auth_header()
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                email = data.get('email') or data.get('userEmail')
                if email:
                    print(f"✅ 获取到用户邮箱: {email}")
                    return email
            
            print("❌ 无法获取用户邮箱")
            return None
            
        except Exception as e:
            print(f"获取用户邮箱失败: {e}")
            return None
    
    def check_oauth_brand_exists(self, project_number: str, project_id: str) -> Optional[bool]:
        """检查OAuth Brand是否已存在（照搬参考项目）
        
        Returns:
            True: Brand存在
            False: Brand不存在
            None: 检查失败（可能Brand已存在但查询出错）
        """
        try:
            print("🔍 检查OAuth同意屏幕是否已存在...")
            
            url = "https://cloudconsole-pa.clients6.google.com/v3/entityServices/OauthEntityService/schemas/OAUTH_GRAPHQL:batchGraphql"
            params = {
                "key": self.api_key,
                "prettyPrint": "false"
            }
            
            # GraphQL查询现有Brand（照搬参考项目）
            graphql_data = [
                {
                    "operationName": "ListBrands",
                    "variables": {
                        "parent": f"projects/{project_number}"
                    },
                    "query": """
                        query ListBrands($parent: String!) {
                            listBrands(parent: $parent) {
                                brands {
                                    name
                                    supportEmail
                                    applicationTitle
                                    brandingSettings {
                                        applicationTitle
                                        supportEmail
                                    }
                                }
                            }
                        }
                    """,
                    "querySignature": "2/ukAwn7nyumcqnLfUlkneK4V/rUBKJaa2DeVqmHqcc8U="
                }
            ]
            
            headers = {
                'Content-Type': 'application/json',
                'Cookie': self.get_cookie_string(),
                'authorization': self.generate_auth_header(),
                'x-goog-authuser': '0',
                'referer': 'https://console.cloud.google.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6779.70 Safari/537.36'
            }
            
            response = self.session.post(url, params=params, json=graphql_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if isinstance(result, list) and len(result) > 0:
                    result_data = result[0].get("results", [])
                    if result_data and len(result_data) > 0:
                        brands_data = result_data[0].get("data", {}).get("listBrands", {})
                        brands = brands_data.get("brands", [])
                        
                        if brands and len(brands) > 0:
                            print(f"✅ 发现 {len(brands)} 个已存在的OAuth同意屏幕")
                            for brand in brands:
                                brand_name = brand.get("name", "")
                                support_email = brand.get("supportEmail", "")
                                app_title = brand.get("applicationTitle", "")
                                print(f"   Brand: {brand_name}, 邮箱: {support_email}, 标题: {app_title}")
                            return True
                        else:
                            print("📋 未发现已存在的OAuth同意屏幕")
                            return False
                    else:
                        print("📋 未发现已存在的OAuth同意屏幕")
                        return False
                else:
                    print("📋 未发现已存在的OAuth同意屏幕")
                    return False
            else:
                print(f"⚠️ Brand检查失败 (状态码: {response.status_code}) - 可能已存在")
                return None  # 返回None表示检查失败，但Brand可能已存在
                
        except Exception as e:
            print(f"⚠️ Brand检查异常: {e}")
            return None  # 返回None表示检查失败，但Brand可能已存在
    
    def create_oauth_brand(self, project_number: str, project_id: str, support_email: str, developer_email: str = None) -> Tuple[bool, Optional[str]]:
        """创建OAuth Brand（同意屏幕）- 照搬参考项目
        
        Args:
            project_number: 项目编号
            project_id: 项目ID
            support_email: 支持邮箱（账号邮箱）
            developer_email: 开发者邮箱（辅助邮箱，可选，默认使用support_email）
        """
        try:
            # 如果没有提供开发者邮箱，使用支持邮箱
            if not developer_email:
                developer_email = support_email
            
            url = "https://cloudconsole-pa.clients6.google.com/v3/entityServices/OauthEntityService/schemas/OAUTH_GRAPHQL:batchGraphql"
            params = {
                "key": self.api_key,
                "prettyPrint": "false"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Cookie': self.get_cookie_string(),
                'authorization': self.generate_auth_header(),
                'x-server-token': self.get_server_token(),
                'x-goog-first-party-reauth': self.get_first_party_reauth(),
                'x-client-data': 'CIe2yQEIpLbJAQipncoBCNv+ygEIk6HLAQiFoM0BGI/OzQE=',
                'origin': 'https://console.cloud.google.com',
                'referer': 'https://console.cloud.google.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6779.70 Safari/537.36',
                'x-goog-authuser': '0'
            }
            
            # 生成随机应用名称
            app_names = ["智能助手", "数据分析平台", "云端服务", "移动应用", "管理系统", "API服务", "Web应用"]
            random_app_name = random.choice(app_names)
            
            # 照搬参考项目的payload结构
            payload = {
                "requestContext": {
                    "platformMetadata": {
                        "platformType": "RIF"
                    },
                    "clientVersion": "pantheon.pangular_20250915.01_p0",
                    "pagePath": "/auth/overview/create",
                    "pageViewId": random.randint(1000000000000000, 9999999999999999),
                    "trackingId": f"d{random.randint(1000000000000000, 9999999999999999)}",
                    "forcedExperimentIds": {"add": [], "remove": []},
                    "backendOverrides": {},
                    "clientSessionId": str(uuid.uuid4()).upper(),
                    "projectId": project_id,
                    "selectedPurview": {"projectId": project_id},
                    "jurisdiction": "global",
                    "localizationData": {
                        "locale": "zh_CN",
                        "timezone": "Asia/Hong_Kong"
                    }
                },
                "querySignature": "2/Dw5FvjddGnbXz7Cf+AjErbKQIFNnr3XSYhR1UzkvRFA=",
                "operationName": "CreateBrandInfo",
                "variables": {
                    "request": {
                        "projectNumber": project_number,
                        "displayName": random_app_name,
                        "supportEmail": support_email,
                        "developerEmails": [developer_email],
                        "visibility": "EXTERNAL",
                        "publishState": "TESTING"
                    }
                }
            }
            
            print(f"🔄 创建OAuth Brand: {random_app_name}")
            print(f"   项目编号: {project_number}")
            print(f"   支持邮箱: {support_email}")
            if developer_email != support_email:
                print(f"   开发者邮箱: {developer_email}")
            
            response = self.session.post(url, params=params, json=payload, headers=headers, timeout=30)
            print(f"📊 响应状态: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ 创建失败，状态码: {response.status_code}")
                return False, None
            
            result = response.json()
            
            # 更健壮的响应解析
            if not result or not isinstance(result, list):
                print("❌ 响应格式异常：非列表格式")
                return False, None
            
            if len(result) == 0:
                print("❌ 响应格式异常：空列表")
                return False, None
            
            result_data = result[0].get("results", [])
            if not result_data:
                print("❌ 响应无results数据")
                return False, None
            
            result_data = result_data[0]
            
            # 检查错误
            if "errors" in result_data and result_data["errors"]:
                error = result_data["errors"][0]
                error_message = error.get('message', '未知错误')
                
                # 如果Brand已存在，视为成功（常见情况）
                if "already exists" in error_message.lower() or "duplicate" in error_message.lower():
                    print(f"✅ OAuth同意屏幕已存在（跳过创建）")
                    return True, None
                
                print(f"❌ Brand创建失败: {error_message}")
                return False, None
            
            # 检查操作结果
            brand_data = result_data.get("data", {}).get("createBrandInfo", {})
            if brand_data:
                operation_name = brand_data.get("name")
                is_done = brand_data.get("done", False)
                
                if is_done:
                    print("✅ OAuth同意屏幕创建成功")
                    return True, operation_name
                elif operation_name:
                    print(f"⏳ Brand创建已启动: {operation_name}")
                    return True, operation_name
                else:
                    print("⚠️ Brand创建响应异常")
                    return False, None
            else:
                print("⚠️ Brand创建响应格式异常")
                return False, None
                
        except Exception as e:
            print(f"❌ OAuth Brand创建失败: {e}")
            return False, None
    
    def create_oauth_client(self, project_number: str, project_id: str) -> Tuple[bool, Optional[Dict]]:
        """创建OAuth Client（Web应用）- 使用REST API（照搬参考项目第二版本）"""
        try:
            # 使用抓包的真实REST API端点
            url = "https://clientauthconfig.clients6.google.com/v1/clients"
            params = {
                "key": self.api_key
            }
            
            # 生成随机客户端名称
            client_names = ["Web客户端", "API客户端", "网站应用", "前端客户端", "Web服务"]
            client_name = random.choice(client_names) + f" {random.randint(1, 999)}"
            
            # REST API请求体 - 照搬参考项目
            payload = {
                "type": "WEB",
                "displayName": client_name,
                "postMessageOrigins": [],
                "redirectUris": [],
                "authType": "SHARED_SECRET",
                "brandId": project_number,
                "projectNumber": project_number
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Cookie': self.get_cookie_string(),
                'authorization': self.generate_auth_header(),
                'x-goog-first-party-reauth': self.get_first_party_reauth(),
                'origin': 'https://console.cloud.google.com',
                'referer': 'https://console.cloud.google.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6779.70 Safari/537.36',
                'accept': 'application/json, text/plain, */*',
                'x-goog-authuser': '0',
                'accept-encoding': 'gzip, deflate, br, zstd',
                'accept-language': 'zh-CN,zh;q=0.9'
            }
            
            print(f"🔄 创建OAuth Web客户端（REST API）...")
            print(f"   客户端名称: {client_name}")
            print(f"   项目编号: {project_number}")
            
            response = self.session.post(url, params=params, json=payload, headers=headers, timeout=30)
            print(f"📊 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # REST API响应格式：直接返回客户端信息
                if result and "clientId" in result:
                    client_id = result.get("clientId")
                    client_secret = None
                    
                    # 提取客户端密钥
                    if "clientSecrets" in result and result["clientSecrets"]:
                        client_secret = result["clientSecrets"][0].get("clientSecret")
                    
                    print("✅ OAuth客户端创建成功")
                    print(f"   🔑 客户端ID: {client_id}")
                    if client_secret:
                        print(f"   🔐 客户端密钥: {client_secret[:20]}...")
                    else:
                        print(f"   ⚠️ 未获取到客户端密钥（可能需要在Console查看）")
                    print(f"   📝 显示名称: {result.get('displayName', '')}")
                    
                    return True, {
                        "client_id": client_id,
                        "client_secret": client_secret if client_secret else "",
                        "redirect_uris": result.get("redirectUris", []),
                        "display_name": result.get("displayName", ""),
                        "creation_time": result.get("creationTime", "")
                    }
                else:
                    print("⚠️ 响应中未找到客户端ID")
                    return False, None
            else:
                print(f"❌ 创建失败，状态码: {response.status_code}")
                print(f"   响应内容: {response.text[:500]}")
                return False, None
                
        except Exception as e:
            print(f"❌ OAuth Client创建失败: {e}")
            import traceback
            traceback.print_exc()
            return False, None

