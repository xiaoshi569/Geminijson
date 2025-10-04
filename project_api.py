#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Cloud Project API 封装
用于创建和管理Google Cloud项目
"""

import hashlib
import time
import random
import string
import json
import requests
from typing import Dict, Optional, Tuple


class GoogleCloudProjectAPI:
    """Google Cloud Project API封装类"""
    
    def __init__(self):
        self.api_key = "AIzaSyCI-zsRP85UVOi0DjtiCwWBwQ1djDy741g"
        self.session = requests.Session()
        self.cookies = {}
        
    def set_cookies(self, cookie_string: str):
        """设置Cookie"""
        try:
            self.cookies = {}
            for cookie in cookie_string.split(';'):
                if '=' in cookie:
                    name, value = cookie.strip().split('=', 1)
                    self.cookies[name] = value
                    self.session.cookies.set(name, value)
            return len(self.cookies) > 0
        except Exception as e:
            print(f"设置Cookie失败: {e}")
            return False
    
    def generate_project_id(self, prefix="project") -> str:
        """生成随机项目ID"""
        # 4-15个字符的随机长度
        length = random.randint(4, 10)
        chars = string.ascii_lowercase + string.digits
        random_str = ''.join(random.choice(chars) for _ in range(length))
        suffix = random.randint(100000, 999999)
        return f"{prefix}{random_str}-{suffix}"
    
    def generate_auth_header(self) -> str:
        """生成认证头"""
        try:
            if 'SAPISID' not in self.cookies:
                raise Exception("缺少SAPISID Cookie")
            
            sapisid = self.cookies['SAPISID']
            timestamp = str(int(time.time()))
            origin = "https://console.cloud.google.com"
            hash_string = f"{timestamp} {sapisid} {origin}"
            hash_value = hashlib.sha1(hash_string.encode()).hexdigest()
            
            # 生成复合认证头
            sapisidhash = f"SAPISIDHASH {timestamp}_{hash_value}"
            sapisid1phash = f"SAPISID1PHASH {timestamp}_{hash_value}"
            sapisid3phash = f"SAPISID3PHASH {timestamp}_{hash_value}"
            
            return f"{sapisidhash} {sapisid1phash} {sapisid3phash}"
        except Exception as e:
            print(f"生成认证头失败: {e}")
            return ""
    
    def get_cookie_string(self) -> str:
        """获取Cookie字符串"""
        return '; '.join([f"{name}={value}" for name, value in self.cookies.items()])
    
    def get_server_token(self) -> str:
        """获取服务器令牌"""
        # 简化处理，返回固定值或从Cookie中提取
        return str(random.randint(1000000000, 9999999999))
    
    def get_first_party_reauth(self) -> str:
        """获取第一方重新认证令牌"""
        return ""  # 可选参数
    
    def validate_project_id(self, project_id: str) -> bool:
        """验证项目ID是否可用"""
        try:
            url = "https://cloudconsole-pa.clients6.google.com/v3/entityServices/CrmEntityService/schemas/CRM_GRAPHQL:batchGraphql"
            params = {
                "key": self.api_key,
                "prettyPrint": "false"
            }
            
            payload = {
                "requests": [{
                    "@type": "type.googleapis.com/google.internal.cloud.console.clientapi.crm.CrmGraphqlBatchRequest",
                    "graphqlQueries": [{
                        "query": f'query {{ projectIdValidator(projectId: "{project_id}") {{ error }} }}'
                    }]
                }]
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Cookie': self.get_cookie_string(),
                'authorization': self.generate_auth_header(),
                'x-goog-authuser': '0',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.session.post(url, params=params, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                # 检查是否有错误
                if 'responses' in result and len(result['responses']) > 0:
                    graphql_result = result['responses'][0].get('graphqlResponses', [{}])[0]
                    data = graphql_result.get('data', {})
                    validator = data.get('projectIdValidator', {})
                    error = validator.get('error')
                    
                    if not error:
                        return True  # 无错误，ID可用
                    
            return False
            
        except Exception as e:
            print(f"验证项目ID失败: {e}")
            return False
    
    def create_project(self, project_name: str, project_id: str) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """
        创建项目（手动指定项目ID）
        返回: (成功与否, 消息, 项目ID, 项目编号)
        """
        try:
            url = "https://cloudconsole-pa.clients6.google.com/v3/entityServices/CrmEntityService/entities/CRM_PROJECT/async/CREATE"
            params = {
                "key": self.api_key,
                "alt": "json",
                "prettyPrint": "false"
            }
            
            # 手动指定项目ID（参考项目的方式）
            payload = {
                "request": {
                    "@type": "type.googleapis.com/google.internal.cloud.console.clientapi.crm.CreateProjectRequest",
                    "enableCloudApisInServiceManager": True,
                    "assignedIdForDisplay": project_id,  # 指定项目ID
                    "generateProjectId": False,  # 不自动生成
                    "name": project_name,
                    "isAe4B": False,
                    "billingAccountId": None,
                    "inheritsBillingAccount": False,
                    "tags": {},
                    "noCloudProject": False,
                    "phantomData": {
                        "phantomRows": [{
                            "displayName": project_name,
                            "type": "PROJECT",
                            "lifecycleState": "ACTIVE",
                            "id": project_id,
                            "organizationId": None,
                            "name": f"projects/{project_id}"
                        }]
                    },
                    "description": {
                        "descriptionKey": "panCreateProject",
                        "descriptionArgs": {
                            "name": project_name,
                            "assignedIdForDisplay": project_id,
                            "isAe4B": "false",
                            "organizationId": None
                        }
                    }
                }
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Cookie': self.get_cookie_string(),
                'authorization': self.generate_auth_header(),
                'x-goog-authuser': '0',
                'x-requested-with': 'XMLHttpRequest',
                'referer': 'https://console.cloud.google.com/',
                'origin': 'https://console.cloud.google.com',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'x-server-token': self.get_server_token(),
                'x-goog-first-party-reauth': self.get_first_party_reauth()
            }
            
            response = self.session.post(url, params=params, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # 完全照搬参考项目的响应解析逻辑
                if "name" in result and "operations/" in result["name"]:
                    operation_id = result["name"]
                    
                    # 从phantomData中提取项目信息
                    phantom_data = result.get("metadata", {}).get("phantomData", {})
                    phantom_rows = phantom_data.get("phantomRows", [])
                    
                    if phantom_rows and len(phantom_rows) > 0:
                        project_info = phantom_rows[0]
                        
                        # 照搬参考项目的提取逻辑
                        project_display_name = project_info.get("displayName", "未知")
                        project_id_from_response = project_info.get("id", project_info.get("name", "").replace("projects/", ""))
                        
                        print(f"✅ 项目创建成功: {project_display_name} ({project_id_from_response})")
                        
                        # 项目编号通常需要后续查询
                        return True, "项目创建成功", project_id_from_response, None
                    else:
                        # 如果没有phantomRows，返回我们传入的project_id
                        return True, "项目创建成功", project_id, None
                
                elif "error" in result:
                    error_msg = result.get("error", {}).get("message", "未知错误")
                    print(f"❌ API错误: {error_msg}")
                    return False, error_msg, None, None
                else:
                    return True, "项目创建成功", project_id, None
            else:
                return False, f"API返回错误: {response.status_code}", None, None
                
        except Exception as e:
            return False, f"创建项目失败: {str(e)}", None, None
    
    def get_project_number(self, project_id: str, max_retries=5, initial_delay=10) -> Optional[str]:
        """
        使用GraphQL API获取项目编号（基于参考项目的完整实现）
        会重试多次，因为项目创建后需要时间才能查询到
        """
        try:
            print(f"⏳ 查询项目编号: {project_id}")
            
            # 先等待项目创建完成（参考项目的做法）
            print(f"   等待 {initial_delay} 秒让项目初始化...")
            time.sleep(initial_delay)
            
            # 严格按照抓包数据使用正确的URL
            url = "https://cloudconsole-pa.clients6.google.com/v3/entityServices/CrmEntityService/schemas/CRM_GRAPHQL:batchGraphql"
            
            # 重试多次查询
            for attempt in range(max_retries):
                if attempt > 0:
                    wait_time = 5 * attempt  # 递增等待时间：5s, 10s, 15s...
                    print(f"   重试中 ({attempt}/{max_retries})，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                
                # 动态生成参数
                import uuid
                
                # 根据抓包数据构建GraphQL请求
                graphql_data = {
                "requestContext": {
                    "clientVersion": "pantheon.pangular_20250924.10_p0",
                    "pagePath": "/welcome",
                    "pageViewId": random.randint(1000000000000000, 9999999999999999),
                    "trackingId": f"d{random.randint(1000000000000000, 9999999999999999)}",
                    "forcedExperimentIds": {
                        "add": [],
                        "remove": []
                    },
                    "backendOverrides": {},
                    "clientSessionId": str(uuid.uuid4()).upper(),
                    "projectId": project_id,
                    "selectedPurview": {
                        "projectId": project_id
                    },
                    "jurisdiction": "global",
                    "experimentFlagsBinary": "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",
                    "localizationData": {
                        "locale": "zh_CN",
                        "timezone": "Asia/Hong_Kong"
                    }
                },
                "querySignature": "2/ukAwn7nyumcqnLfUlkneK4V/rUBKJaa2DeVqmHqcc8U=",
                "operationName": "GetProject",
                "variables": {
                    "projectId": project_id
                }
                }
                
                # 添加认证头
                headers = {
                    'Content-Type': 'application/json',
                    'Cookie': self.get_cookie_string(),
                    'authorization': self.generate_auth_header(),
                    'x-goog-authuser': '0',
                    'referer': 'https://console.cloud.google.com/',
                    'user-agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6779.70 Safari/537.36',
                    'origin': 'https://console.cloud.google.com',
                    'x-requested-with': 'XMLHttpRequest'
                }
                
                # 查询参数
                params = {
                    "key": self.api_key,
                    "prettyPrint": "false"
                }
                
                response = self.session.post(url, params=params, json=graphql_data, headers=headers, timeout=10)
                
                if response.status_code == 400:
                    try:
                        array_data = [graphql_data]
                        alt_response = self.session.post(url, json=array_data, headers=headers, timeout=10)
                        if alt_response.status_code == 200:
                            response = alt_response
                    except:
                        pass
                    
                    if response.status_code == 400:
                        continue
                elif response.status_code != 200:
                    continue
                
                if response.status_code == 200:
                    response_json = response.json()
                    
                    # 解析GetProject响应（严格按照抓包数据格式）
                    if isinstance(response_json, list) and len(response_json) > 0:
                        results = response_json[0].get('results', [])
                        if results and len(results) > 0:
                            data = results[0].get('data', {})
                            
                            # 从project中获取项目信息
                            project_info = data.get('project', {})
                            if project_info:
                                # 获取项目编号
                                project_number = project_info.get('projectNumber') or project_info.get('numericProjectId')
                                
                                if project_number:
                                    print(f"✅ 成功获取项目编号: {project_number}")
                                    return str(project_number)
            
            # 所有重试都失败了
            print(f"❌ 经过 {max_retries} 次尝试后仍无法获取项目编号")
            return None
                
        except Exception as e:
            print(f"GraphQL API查询异常: {e}")
            return None
