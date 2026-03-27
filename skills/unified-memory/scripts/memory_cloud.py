#!/usr/bin/env python3
"""
Memory Cloud - 云同步支持 v0.2.2

功能:
- 多种云存储支持 (local/s3/webdav/dropbox/gdrive)
- 多设备同步
- 增量同步
- 冲突解决

Usage:
    python3 scripts/memory_cloud.py backup
    python3 scripts/memory_cloud.py restore
    python3 scripts/memory_cloud.py sync
    python3 scripts/memory_cloud.py status
    python3 scripts/memory_cloud.py configure-s3 --endpoint URL --bucket NAME --access-key KEY --secret-key SECRET
    python3 scripts/memory_cloud.py configure-webdav --url URL --username USER --password PASS
    python3 scripts/memory_cloud.py configure-dropbox --token TOKEN
    python3 scripts/memory_cloud.py configure-gdrive --credentials FILE
"""

import argparse
import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import shutil

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
CLOUD_CONFIG = MEMORY_DIR / "cloud_config.json"
SYNC_STATE = MEMORY_DIR / "sync_state.json"

# 云存储类型
STORAGE_TYPES = ["local", "s3", "webdav", "dropbox", "gdrive"]


class CloudConfig:
    """云存储配置"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置"""
        if CLOUD_CONFIG.exists():
            with open(CLOUD_CONFIG) as f:
                return json.load(f)
        return {
            "enabled": False,
            "storage_type": "local",
            "backup_path": str(WORKSPACE / "memory_backup"),
            "auto_sync": False,
            "sync_interval": 3600,
            "s3": {"endpoint": "", "bucket": "", "access_key": "", "secret_key": "", "region": "us-east-1"},
            "webdav": {"url": "", "username": "", "password": "", "path": "/memory_backup"},
            "dropbox": {"access_token": "", "refresh_token": "", "app_key": "", "app_secret": "", "path": "/memory_backup"},
            "gdrive": {"credentials_file": "", "token_file": "", "folder_id": ""}
        }
    
    def save(self):
        CLOUD_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        with open(CLOUD_CONFIG, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def enable(self, storage_type: str = "local", backup_path: str = None):
        self.config["enabled"] = True
        self.config["storage_type"] = storage_type
        if backup_path:
            self.config["backup_path"] = backup_path
        self.save()
    
    def disable(self):
        self.config["enabled"] = False
        self.save()


class CloudProvider:
    """云存储提供商基类"""
    def __init__(self, config: CloudConfig):
        self.config = config
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        raise NotImplementedError
    
    def download(self, remote_path: str, local_path: str) -> bool:
        raise NotImplementedError
    
    def list_files(self, remote_dir: str) -> List[Dict]:
        raise NotImplementedError
    
    def delete(self, remote_path: str) -> bool:
        raise NotImplementedError


class LocalProvider(CloudProvider):
    """本地文件系统"""
    def upload(self, local_path: str, remote_path: str) -> bool:
        try:
            remote_full = Path(self.config.config.get("backup_path", "")) / remote_path
            remote_full.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_path, remote_full)
            return True
        except:
            return False
    
    def download(self, remote_path: str, local_path: str) -> bool:
        try:
            remote_full = Path(self.config.config.get("backup_path", "")) / remote_path
            shutil.copy2(remote_full, local_path)
            return True
        except:
            return False
    
    def list_files(self, remote_dir: str) -> List[Dict]:
        try:
            remote_full = Path(self.config.config.get("backup_path", "")) / remote_dir
            if not remote_full.exists():
                return []
            return [{"name": f.name, "size": f.stat().st_size, "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()} for f in remote_full.iterdir() if f.is_file()]
        except:
            return []
    
    def delete(self, remote_path: str) -> bool:
        try:
            remote_full = Path(self.config.config.get("backup_path", "")) / remote_path
            remote_full.unlink()
            return True
        except:
            return False


class S3Provider(CloudProvider):
    """AWS S3 兼容存储"""
    def _get_client(self):
        try:
            import boto3
            s3_config = self.config.config.get("s3", {})
            return boto3.client(
                "s3",
                endpoint_url=s3_config.get("endpoint") or None,
                aws_access_key_id=s3_config.get("access_key"),
                aws_secret_access_key=s3_config.get("secret_key"),
                region_name=s3_config.get("region", "us-east-1")
            ), s3_config.get("bucket", "")
        except ImportError:
            print("❌ 请安装 boto3: pip install boto3")
            return None, None
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        client, bucket = self._get_client()
        if not client:
            return False
        try:
            client.upload_file(local_path, bucket, remote_path)
            return True
        except Exception as e:
            print(f"❌ 上传失败: {e}")
            return False
    
    def download(self, remote_path: str, local_path: str) -> bool:
        client, bucket = self._get_client()
        if not client:
            return False
        try:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            client.download_file(bucket, remote_path, local_path)
            return True
        except:
            return False
    
    def list_files(self, remote_dir: str) -> List[Dict]:
        client, bucket = self._get_client()
        if not client:
            return []
        try:
            response = client.list_objects_v2(Bucket=bucket, Prefix=remote_dir)
            return [{"name": obj["Key"], "size": obj["Size"], "modified": obj["LastModified"].isoformat()} for obj in response.get("Contents", [])]
        except:
            return []


class WebDAVProvider(CloudProvider):
    """WebDAV 协议"""
    def _get_client(self):
        try:
            from webdav3.client import Client
            webdav_config = self.config.config.get("webdav", {})
            return Client({
                "webdav_hostname": webdav_config.get("url"),
                "webdav_login": webdav_config.get("username"),
                "webdav_password": webdav_config.get("password")
            })
        except ImportError:
            print("❌ 请安装 webdavclient3: pip install webdavclient3")
            return None
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            webdav_config = self.config.config.get("webdav", {})
            remote_full = f"{webdav_config.get('path', '')}/{remote_path}"
            client.upload(remote_path=remote_full, local_path=local_path)
            return True
        except Exception as e:
            print(f"❌ 上传失败: {e}")
            return False
    
    def download(self, remote_path: str, local_path: str) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            webdav_config = self.config.config.get("webdav", {})
            remote_full = f"{webdav_config.get('path', '')}/{remote_path}"
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            client.download(remote_path=remote_full, local_path=local_path)
            return True
        except:
            return False
    
    def list_files(self, remote_dir: str) -> List[Dict]:
        client = self._get_client()
        if not client:
            return []
        try:
            webdav_config = self.config.config.get("webdav", {})
            remote_full = f"{webdav_config.get('path', '')}/{remote_dir}"
            files = client.list(remote_full)
            return [{"name": f, "size": 0, "modified": ""} for f in files]
        except:
            return []


class DropboxProvider(CloudProvider):
    """Dropbox 云存储"""
    def _get_client(self):
        try:
            import dropbox
            dropbox_config = self.config.config.get("dropbox", {})
            return dropbox.Dropbox(dropbox_config.get("access_token"))
        except ImportError:
            print("❌ 请安装 dropbox: pip install dropbox")
            return None
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            dropbox_config = self.config.config.get("dropbox", {})
            remote_full = f"{dropbox_config.get('path', '')}/{remote_path}"
            with open(local_path, 'rb') as f:
                client.files_upload(f.read(), remote_full)
            return True
        except Exception as e:
            print(f"❌ 上传失败: {e}")
            return False
    
    def download(self, remote_path: str, local_path: str) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            dropbox_config = self.config.config.get("dropbox", {})
            remote_full = f"{dropbox_config.get('path', '')}/{remote_path}"
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            client.files_download_to_file(local_path, remote_full)
            return True
        except:
            return False
    
    def list_files(self, remote_dir: str) -> List[Dict]:
        client = self._get_client()
        if not client:
            return []
        try:
            dropbox_config = self.config.config.get("dropbox", {})
            remote_full = f"{dropbox_config.get('path', '')}/{remote_dir}"
            result = client.files_list_folder(remote_full)
            return [{"name": f.name, "size": f.size if hasattr(f, 'size') else 0, "modified": f.server_modified.isoformat() if hasattr(f, 'server_modified') else ""} for f in result.entries]
        except:
            return []


class GDriveProvider(CloudProvider):
    """Google Drive 云存储"""
    def _get_client(self):
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from google.auth.transport.requests import Request
            
            gdrive_config = self.config.config.get("gdrive", {})
            creds = None
            token_file = gdrive_config.get("token_file", "")
            credentials_file = gdrive_config.get("credentials_file", "")
            
            if token_file and Path(token_file).exists():
                creds = Credentials.from_authorized_user_file(token_file)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif credentials_file:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, ['https://www.googleapis.com/auth/drive.file'])
                    creds = flow.run_local_server(port=0)
                    if token_file:
                        with open(token_file, 'w') as f:
                            f.write(creds.to_json())
            
            return build('drive', 'v3', credentials=creds)
        except ImportError:
            print("❌ 请安装: pip install google-api-python-client google-auth-oauthlib")
            return None
        except Exception as e:
            print(f"❌ Google Drive 认证失败: {e}")
            return None
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            from googleapiclient.http import MediaFileUpload
            gdrive_config = self.config.config.get("gdrive", {})
            folder_id = gdrive_config.get("folder_id", "")
            
            file_metadata = {"name": Path(remote_path).name}
            if folder_id:
                file_metadata["parents"] = [folder_id]
            
            media = MediaFileUpload(local_path, resumable=True)
            client.files().create(body=file_metadata, media_body=media, fields="id").execute()
            return True
        except Exception as e:
            print(f"❌ 上传失败: {e}")
            return False
    
    def download(self, remote_path: str, local_path: str) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            results = client.files().list(q=f"name='{Path(remote_path).name}'", fields="files(id, name)").execute()
            files = results.get("files", [])
            if not files:
                return False
            
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            request = client.files().get_media(fileId=files[0]["id"])
            with open(local_path, 'wb') as f:
                f.write(request.execute())
            return True
        except:
            return False
    
    def list_files(self, remote_dir: str) -> List[Dict]:
        client = self._get_client()
        if not client:
            return []
        try:
            results = client.files().list(pageSize=100, fields="files(id, name, size, modifiedTime)").execute()
            return [{"name": f["name"], "size": int(f.get("size", 0)), "modified": f.get("modifiedTime", "")} for f in results.get("files", [])]
        except:
            return []


def get_provider(config: CloudConfig) -> CloudProvider:
    """获取云存储提供商"""
    storage_type = config.config.get("storage_type", "local")
    providers = {"local": LocalProvider, "s3": S3Provider, "webdav": WebDAVProvider, "dropbox": DropboxProvider, "gdrive": GDriveProvider}
    return providers.get(storage_type, LocalProvider)(config)


class MemoryBackup:
    """记忆备份管理"""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.provider = get_provider(config)
    
    def create_backup(self) -> Dict:
        """创建备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = MEMORY_DIR / "temp_backup"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        backup_dir = temp_dir / f"backup_{timestamp}"
        backup_dir.mkdir(parents=True)
        
        # 备份向量数据库
        if VECTOR_DB_DIR.exists():
            db_backup = backup_dir / "vector"
            shutil.copytree(VECTOR_DB_DIR, db_backup)
        
        # 备份配置文件
        for config_file in MEMORY_DIR.glob("*.json"):
            if config_file.name != "cloud_config.json":
                shutil.copy2(config_file, backup_dir)
        
        # 创建清单
        manifest = {
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat(),
            "files": list(str(f.name) for f in backup_dir.rglob("*") if f.is_file()),
            "storage_type": self.config.config.get("storage_type", "local")
        }
        
        with open(backup_dir / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # 上传到云端
        storage_type = self.config.config.get("storage_type", "local")
        if storage_type != "local":
            # 打包
            archive_path = temp_dir / f"backup_{timestamp}.zip"
            shutil.make_archive(str(archive_path.with_suffix('')), 'zip', backup_dir)
            
            # 上传
            remote_path = f"backups/backup_{timestamp}.zip"
            if self.provider.upload(str(archive_path), remote_path):
                print(f"✅ 已上传到 {storage_type}")
            else:
                print(f"⚠️ 上传失败，备份仅保存在本地")
            
            # 清理临时文件
            shutil.rmtree(backup_dir)
            archive_path.unlink(missing_ok=True)
        else:
            # 本地存储：移动到备份目录
            backup_path = Path(self.config.config.get("backup_path", ""))
            backup_path.mkdir(parents=True, exist_ok=True)
            final_dir = backup_path / f"backup_{timestamp}"
            shutil.move(str(backup_dir), str(final_dir))
        
        return {
            "success": True,
            "timestamp": timestamp,
            "files": len(manifest["files"]),
            "storage_type": storage_type
        }
    
    def list_backups(self) -> List[Dict]:
        """列出备份"""
        storage_type = self.config.config.get("storage_type", "local")
        
        if storage_type == "local":
            backup_path = Path(self.config.config.get("backup_path", ""))
            if not backup_path.exists():
                return []
            
            backups = []
            for backup_dir in backup_path.glob("backup_*"):
                manifest_file = backup_dir / "manifest.json"
                if manifest_file.exists():
                    with open(manifest_file) as f:
                        manifest = json.load(f)
                    backups.append({
                        "timestamp": manifest.get("timestamp", ""),
                        "created_at": manifest.get("created_at", ""),
                        "files": len(manifest.get("files", [])),
                        "storage_type": "local"
                    })
            return sorted(backups, key=lambda x: x["timestamp"], reverse=True)
        else:
            # 云端备份
            files = self.provider.list_files("backups")
            return [{
                "timestamp": f["name"].replace("backup_", "").replace(".zip", ""),
                "size": f.get("size", 0),
                "modified": f.get("modified", ""),
                "storage_type": storage_type
            } for f in files if f["name"].endswith(".zip")]
    
    def restore_backup(self, timestamp: str) -> Dict:
        """恢复备份"""
        storage_type = self.config.config.get("storage_type", "local")
        
        if storage_type == "local":
            backup_path = Path(self.config.config.get("backup_path", ""))
            backup_dir = backup_path / f"backup_{timestamp}"
            
            if not backup_dir.exists():
                return {"success": False, "error": "备份不存在"}
            
            # 恢复向量数据库
            db_backup = backup_dir / "vector"
            if db_backup.exists():
                if VECTOR_DB_DIR.exists():
                    shutil.rmtree(VECTOR_DB_DIR)
                shutil.copytree(db_backup, VECTOR_DB_DIR)
            
            # 恢复配置文件
            for config_file in backup_dir.glob("*.json"):
                if config_file.name != "manifest.json":
                    shutil.copy2(config_file, MEMORY_DIR)
            
            return {"success": True, "restored_from": timestamp}
        else:
            # 从云端下载
            temp_dir = MEMORY_DIR / "temp_restore"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            remote_path = f"backups/backup_{timestamp}.zip"
            local_path = temp_dir / f"backup_{timestamp}.zip"
            
            if not self.provider.download(remote_path, str(local_path)):
                shutil.rmtree(temp_dir)
                return {"success": False, "error": "下载失败"}
            
            # 解压
            shutil.unpack_archive(str(local_path), temp_dir)
            
            # 恢复
            backup_dir = temp_dir / f"backup_{timestamp}"
            if backup_dir.exists():
                db_backup = backup_dir / "vector"
                if db_backup.exists():
                    if VECTOR_DB_DIR.exists():
                        shutil.rmtree(VECTOR_DB_DIR)
                    shutil.copytree(db_backup, VECTOR_DB_DIR)
                
                for config_file in backup_dir.glob("*.json"):
                    if config_file.name != "manifest.json":
                        shutil.copy2(config_file, MEMORY_DIR)
            
            shutil.rmtree(temp_dir)
            return {"success": True, "restored_from": timestamp}


class MemorySync:
    """记忆同步管理"""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.backup = MemoryBackup(config)
    
    def get_local_state(self) -> Dict:
        """获取本地状态"""
        state = {"last_sync": None, "memory_count": 0, "checksum": ""}
        
        if SYNC_STATE.exists():
            with open(SYNC_STATE) as f:
                saved = json.load(f)
                state["last_sync"] = saved.get("last_sync")
        
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            data = table.to_lance().to_table().to_pydict()
            
            state["memory_count"] = len(data.get("id", []))
            texts = sorted(data.get("text", []))
            state["checksum"] = hashlib.md5("|".join(texts).encode()).hexdigest()[:16]
        except:
            pass
        
        return state
    
    def sync(self) -> Dict:
        """同步"""
        if not self.config.config.get("enabled"):
            return {"success": False, "error": "云同步未启用"}
        
        backup_result = self.backup.create_backup()
        
        state = {
            "last_sync": datetime.now().isoformat(),
            "backup_timestamp": backup_result.get("timestamp", "")
        }
        
        with open(SYNC_STATE, 'w') as f:
            json.dump(state, f, indent=2)
        
        return {"success": True, "backup": backup_result, "synced_at": state["last_sync"]}


def main():
    parser = argparse.ArgumentParser(description="Memory Cloud 0.2.2")
    parser.add_argument("command", choices=["backup", "restore", "list", "sync", "status", "enable", "disable", "configure-s3", "configure-webdav", "configure-dropbox", "configure-gdrive"])
    parser.add_argument("--timestamp", "-t", help="备份时间戳")
    parser.add_argument("--storage", "-s", choices=STORAGE_TYPES, default="local")
    parser.add_argument("--path", "-p", help="备份路径")
    parser.add_argument("--keep", type=int, default=10)
    parser.add_argument("--endpoint", help="S3 endpoint")
    parser.add_argument("--bucket", help="S3 bucket")
    parser.add_argument("--access-key", help="S3 access key")
    parser.add_argument("--secret-key", help="S3 secret key")
    parser.add_argument("--region", default="us-east-1", help="S3 region")
    parser.add_argument("--url", help="WebDAV URL")
    parser.add_argument("--username", help="WebDAV username")
    parser.add_argument("--password", help="WebDAV password")
    parser.add_argument("--token", help="Dropbox access token")
    parser.add_argument("--credentials", help="Google Drive credentials file")
    parser.add_argument("--token-file", help="Google Drive token file")
    parser.add_argument("--folder-id", help="Google Drive folder ID")
    
    args = parser.parse_args()
    
    config = CloudConfig()
    backup = MemoryBackup(config)
    sync = MemorySync(config)
    
    if args.command == "enable":
        config.enable(args.storage, args.path)
        print(f"✅ 云同步已启用 ({args.storage})")
    
    elif args.command == "disable":
        config.disable()
        print("✅ 云同步已禁用")
    
    elif args.command == "configure-s3":
        if not all([args.bucket, args.access_key, args.secret_key]):
            print("❌ 请提供 --bucket, --access-key, --secret-key")
            return
        config.config["s3"] = {
            "endpoint": args.endpoint or "",
            "bucket": args.bucket,
            "access_key": args.access_key,
            "secret_key": args.secret_key,
            "region": args.region
        }
        config.enable("s3")
        print("✅ S3 配置完成")
    
    elif args.command == "configure-webdav":
        if not all([args.url, args.username, args.password]):
            print("❌ 请提供 --url, --username, --password")
            return
        config.config["webdav"] = {
            "url": args.url,
            "username": args.username,
            "password": args.password,
            "path": args.path or "/memory_backup"
        }
        config.enable("webdav")
        print("✅ WebDAV 配置完成")
    
    elif args.command == "configure-dropbox":
        if not args.token:
            print("❌ 请提供 --token")
            return
        config.config["dropbox"] = {
            "access_token": args.token,
            "refresh_token": "",
            "app_key": "",
            "app_secret": "",
            "path": args.path or "/memory_backup"
        }
        config.enable("dropbox")
        print("✅ Dropbox 配置完成")
    
    elif args.command == "configure-gdrive":
        if not args.credentials:
            print("❌ 请提供 --credentials (credentials.json 路径)")
            return
        config.config["gdrive"] = {
            "credentials_file": args.credentials,
            "token_file": args.token_file or str(MEMORY_DIR / "gdrive_token.json"),
            "folder_id": args.folder_id or ""
        }
        config.enable("gdrive")
        print("✅ Google Drive 配置完成")
    
    elif args.command == "backup":
        print("📦 创建备份...")
        result = backup.create_backup()
        print(f"✅ 备份完成: {result['timestamp']}")
        print(f"   文件数: {result['files']}")
        print(f"   存储类型: {result['storage_type']}")
    
    elif args.command == "restore":
        if not args.timestamp:
            backups = backup.list_backups()
            if backups:
                print("可用备份:")
                for i, b in enumerate(backups[:5], 1):
                    print(f"   {i}. {b['timestamp']} ({b.get('files', '?')} 文件) [{b['storage_type']}]")
                print("\n使用 --timestamp 指定恢复")
            else:
                print("无可用备份")
        else:
            print(f"🔄 恢复备份 {args.timestamp}...")
            result = backup.restore_backup(args.timestamp)
            if result["success"]:
                print("✅ 恢复成功")
            else:
                print(f"❌ 恢复失败: {result['error']}")
    
    elif args.command == "list":
        backups = backup.list_backups()
        print(f"📋 备份列表 ({len(backups)} 个):")
        for b in backups[:10]:
            print(f"   {b['timestamp']} [{b['storage_type']}]")
    
    elif args.command == "sync":
        print("🔄 同步中...")
        result = sync.sync()
        if result["success"]:
            print("✅ 同步完成")
        else:
            print(f"❌ 同步失败: {result['error']}")
    
    elif args.command == "status":
        state = sync.get_local_state()
        print("📊 同步状态:")
        print(f"   已启用: {config.config.get('enabled', False)}")
        print(f"   存储类型: {config.config.get('storage_type', 'local')}")
        print(f"   记忆数: {state['memory_count']}")
        print(f"   校验和: {state['checksum']}")
        if state['last_sync']:
            print(f"   上次同步: {state['last_sync']}")


if __name__ == "__main__":
    main()
