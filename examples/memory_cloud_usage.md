# Memory Cloud 使用指南

本文档演示 unified-memory 云同步功能的完整使用流程。

## 📋 目录

1. [快速开始](#快速开始)
2. [本地备份](#1-本地备份)
3. [AWS S3](#2-aws-s3--兼容存储)
4. [WebDAV](#3-webdav)
5. [Dropbox](#4-dropbox)
6. [Google Drive](#5-google-drive)
7. [高级用法](#高级用法)
8. [故障排除](#故障排除)

---

## 快速开始

```bash
# 查看当前状态
python3 scripts/memory_cloud.py status

# 快速本地备份
python3 scripts/memory_cloud.py enable --storage local
python3 scripts/memory_cloud.py backup
```

---

## 1. 本地备份

最简单的备份方式，无需额外配置。

### 启用

```bash
# 使用默认路径 (~/.openclaw/workspace/memory_backup)
python3 scripts/memory_cloud.py enable --storage local

# 或指定自定义路径
python3 scripts/memory_cloud.py enable --storage local --path /path/to/backup
```

### 创建备份

```bash
$ python3 scripts/memory_cloud.py backup
📦 创建备份...
✅ 备份完成: 20260318_121530
   文件数: 3
   存储类型: local
```

### 查看备份列表

```bash
$ python3 scripts/memory_cloud.py list
📋 备份列表 (3 个):
   20260318_121530 [local]
   20260317_090000 [local]
   20260316_180000 [local]
```

### 恢复备份

```bash
# 先列出可用备份
python3 scripts/memory_cloud.py list

# 恢复指定备份
$ python3 scripts/memory_cloud.py restore --timestamp 20260318_121530
🔄 恢复备份 20260318_121530...
✅ 恢复成功
```

---

## 2. AWS S3 / 兼容存储

支持所有 S3 兼容的存储服务：
- AWS S3
- MinIO
- 阿里云 OSS
- 腾讯云 COS
- 华为云 OBS

### 安装依赖

```bash
pip install boto3
```

### 配置

#### AWS S3

```bash
python3 scripts/memory_cloud.py configure-s3 \
  --bucket my-memory-backup \
  --access-key AKIAIOSFODNN7EXAMPLE \
  --secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
  --region us-east-1
```

#### MinIO

```bash
python3 scripts/memory_cloud.py configure-s3 \
  --endpoint http://localhost:9000 \
  --bucket memory-backup \
  --access-key minioadmin \
  --secret-key minioadmin
```

#### 阿里云 OSS

```bash
python3 scripts/memory_cloud.py configure-s3 \
  --endpoint https://oss-cn-beijing.aliyuncs.com \
  --bucket my-memory-bucket \
  --access-key LTAI4xxx \
  --secret-key xxx
```

#### 腾讯云 COS

```bash
python3 scripts/memory_cloud.py configure-s3 \
  --endpoint https://cos.ap-guangzhou.myqcloud.com \
  --bucket my-memory-1234567890 \
  --access-key AKIDxxx \
  --secret-key xxx
```

### 使用

```bash
# 创建备份并上传
$ python3 scripts/memory_cloud.py backup
📦 创建备份...
✅ 已上传到 s3
✅ 备份完成: 20260318_122000
   文件数: 3
   存储类型: s3

# 查看云端备份
$ python3 scripts/memory_cloud.py list
📋 备份列表 (5 个):
   20260318_122000 [s3] (1024 bytes, modified: 2026-03-18T12:20:00)
   20260317_090000 [s3] (980 bytes, modified: 2026-03-17T09:00:00)

# 从云端恢复
$ python3 scripts/memory_cloud.py restore --timestamp 20260318_122000
🔄 恢复备份 20260318_122000...
✅ 恢复成功
```

---

## 3. WebDAV

支持所有 WebDAV 协议服务：
- 坚果云
- Nextcloud
- ownCloud
- Synology NAS

### 安装依赖

```bash
pip install webdavclient3
```

### 配置

#### 坚果云

1. 登录坚果云 → 账户信息 → 安全选项
2. 添加应用密码 → 生成第三方应用密码

```bash
python3 scripts/memory_cloud.py configure-webdav \
  --url https://dav.jianguoyun.com/dav/ \
  --username your@email.com \
  --password your-app-password \
  --path /memory_backup
```

#### Nextcloud

```bash
python3 scripts/memory_cloud.py configure-webdav \
  --url https://cloud.example.com/remote.php/dav/files/username/ \
  --username username \
  --password your-password \
  --path /memory_backup
```

#### Synology NAS

```bash
python3 scripts/memory_cloud.py configure-webdav \
  --url https://nas.local:5006/ \
  --username admin \
  --password your-password \
  --path /memory_backup
```

### 使用

```bash
# 创建备份并上传
$ python3 scripts/memory_cloud.py backup
📦 创建备份...
✅ 已上传到 webdav
✅ 备份完成: 20260318_122500

# 查看备份
$ python3 scripts/memory_cloud.py list
📋 备份列表 (3 个):
   20260318_122500 [webdav]
   ...
```

---

## 4. Dropbox

### 安装依赖

```bash
pip install dropbox
```

### 获取 Access Token

1. 访问 https://www.dropbox.com/developers/apps
2. 点击 "Create app"
3. 选择 "Dropbox API" → "Full Dropbox"
4. 在 Settings 中点击 "Generate access token"

### 配置

```bash
python3 scripts/memory_cloud.py configure-dropbox \
  --token sl.Bxxx \
  --path /memory_backup
```

### 使用

```bash
# 创建备份
$ python3 scripts/memory_cloud.py backup
📦 创建备份...
✅ 已上传到 dropbox
✅ 备份完成: 20260318_123000

# 查看 Dropbox 中的备份
$ python3 scripts/memory_cloud.py list
📋 备份列表 (4 个):
   20260318_123000 [dropbox] (2048 bytes)
   ...
```

---

## 5. Google Drive

### 安装依赖

```bash
pip install google-api-python-client google-auth-oauthlib
```

### 获取凭证

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建项目或选择现有项目
3. 启用 Google Drive API
4. 创建 OAuth 2.0 凭证
   - 应用类型：桌面应用
   - 下载 credentials.json

### 配置

```bash
python3 scripts/memory_cloud.py configure-gdrive \
  --credentials /path/to/credentials.json \
  --token-file ~/.openclaw/workspace/memory/gdrive_token.json
```

**首次使用会自动打开浏览器进行授权。**

### 使用

```bash
# 创建备份
$ python3 scripts/memory_cloud.py backup
📦 创建备份...
✅ 已上传到 gdrive
✅ 备份完成: 20260318_123500

# 查看 Google Drive 中的备份
$ python3 scripts/memory_cloud.py list
📋 备份列表 (5 个):
   20260318_123500 [gdrive] (3072 bytes)
   ...
```

---

## 高级用法

### 定时自动备份

添加到 crontab：

```bash
# 每天凌晨 2 点自动备份
0 2 * * * cd ~/.openclaw/workspace/skills/unified-memory && python3 scripts/memory_cloud.py backup >> ~/memory_backup.log 2>&1
```

### 在 Agent 工作流中使用

```python
# 在 AGENTS.md 中添加
# 会话结束时自动备份
python3 scripts/memory_cloud.py backup
```

### 多设备同步

```bash
# 设备 A：创建备份
python3 scripts/memory_cloud.py backup

# 设备 B：查看备份
python3 scripts/memory_cloud.py list

# 设备 B：恢复备份
python3 scripts/memory_cloud.py restore --timestamp 20260318_120000
```

### 清理旧备份

```bash
# 只保留最近 10 个备份
python3 scripts/memory_cloud.py backup --keep 10
```

---

## 故障排除

### S3 上传失败

```
❌ 上传失败: InvalidAccessKeyId
```

**解决方案**：检查 access-key 和 secret-key 是否正确。

### WebDAV 连接超时

```
❌ 上传失败: Connection refused
```

**解决方案**：
1. 检查 URL 是否正确
2. 确认 WebDAV 服务已启动
3. 检查防火墙设置

### Dropbox Token 过期

```
❌ 上传失败: expired_access_token
```

**解决方案**：重新生成 access token 或使用 refresh token。

### Google Drive 认证失败

```
❌ Google Drive 认证失败: invalid_grant
```

**解决方案**：
1. 删除 token 文件
2. 重新运行配置命令
3. 重新授权

### 依赖缺失

```
❌ 请安装 boto3: pip install boto3
```

**解决方案**：

```bash
pip install boto3              # S3
pip install webdavclient3      # WebDAV
pip install dropbox            # Dropbox
pip install google-api-python-client google-auth-oauthlib  # GDrive
```

---

## 📊 功能对比

| 功能 | local | s3 | webdav | dropbox | gdrive |
|------|-------|----|----|---------|--------|
| 备份创建 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 备份恢复 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 备份列表 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 自动同步 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 多设备 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 增量备份 | ❌ | ✅ | ❌ | ❌ | ❌ |
| 免费额度 | 无限 | 5GB | 取决于服务 | 2GB | 15GB |

---

## 🔐 安全建议

1. **不要将凭证提交到版本控制**
   ```bash
   # 添加到 .gitignore
   echo "cloud_config.json" >> .gitignore
   echo "gdrive_token.json" >> .gitignore
   ```

2. **使用应用专用密码** (坚果云等)

3. **定期轮换密钥**

4. **限制权限** (最小权限原则)
   - S3: 只授予特定 bucket 的读写权限
   - Dropbox: 使用 Full Dropbox 或 App folder
   - Google Drive: 只请求必要的 scope

---

## 📚 相关文档

- [English Documentation](../README.md)
- [中文文档](../README_CN.md)
- [Version History](../VERSION.md)
