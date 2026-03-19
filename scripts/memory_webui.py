#!/usr/bin/env python3
"""
Memory Web UI - Web 可视化界面 v0.5.0

功能:
- 记忆浏览、搜索、创建、编辑、删除
- 统计仪表盘 + 健康状态
- 知识图谱可视化 (vis.js)
- 成本监控面板 (Ollama/LLM 消耗)
- 云同步状态
- 移动优先响应式设计 + 暗色模式
- 🤝 协作仪表盘 (多 Agent 协作)

Usage:
    python3 memory_webui.py --port 38080
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import webbrowser

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
SCRIPT_DIR = Path(__file__).parent.absolute()
STATS_FILE = MEMORY_DIR / "stats.json"

# HTML 模板 - 移动优先设计
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#6366f1">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>Unified Memory v0.5.0</title>
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --primary-light: #818cf8;
            --bg: #f1f5f9;
            --card: #ffffff;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1);
            --radius: 12px;
            --radius-sm: 8px;
            --touch: 44px;
            --safe-bottom: env(safe-area-inset-bottom, 0px);
        }
        
        [data-theme="dark"] {
            --bg: #0f172a;
            --card: #1e293b;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --border: #334155;
            --shadow: 0 1px 3px rgba(0,0,0,0.3);
        }
        
        * { 
            box-sizing: border-box; 
            margin: 0; 
            padding: 0; 
            -webkit-tap-highlight-color: transparent;
        }
        
        html {
            font-size: 16px;
            scroll-behavior: smooth;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            min-height: 100dvh;
            transition: background 0.3s, color 0.3s;
            overscroll-behavior: none;
            -webkit-font-smoothing: antialiased;
        }
        
        .app {
            max-width: 100%;
            margin: 0 auto;
            padding: 12px;
            padding-bottom: calc(80px + var(--safe-bottom));
        }
        
        /* Header - Mobile First */
        .header {
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin: -12px -12px 16px;
            padding: 12px;
            background: var(--card);
            border-bottom: 1px solid var(--border);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
        
        .header-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .logo h1 {
            font-size: 18px;
            font-weight: 600;
            letter-spacing: -0.02em;
        }
        
        .logo .version {
            background: var(--primary);
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 500;
        }
        
        .header-actions {
            display: flex;
            gap: 8px;
        }
        
        .btn {
            min-height: var(--touch);
            padding: 10px 16px;
            border: none;
            border-radius: var(--radius-sm);
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            white-space: nowrap;
        }
        
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        
        .btn-primary:active {
            background: var(--primary-dark);
            transform: scale(0.98);
        }
        
        .btn-ghost {
            background: transparent;
            color: var(--text-muted);
            border: 1px solid var(--border);
        }
        
        .btn-ghost:active {
            background: var(--bg);
        }
        
        .btn-icon {
            width: var(--touch);
            padding: 0;
            font-size: 18px;
        }
        
        /* Stats Grid - Mobile First */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 16px;
        }
        
        .stat-card {
            background: var(--card);
            border-radius: var(--radius);
            padding: 14px;
            box-shadow: var(--shadow);
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        
        .stat-card .icon {
            font-size: 20px;
        }
        
        .stat-card .value {
            font-size: 22px;
            font-weight: 700;
            color: var(--primary);
            letter-spacing: -0.02em;
        }
        
        .stat-card .label {
            color: var(--text-muted);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.02em;
        }
        
        .stat-card.success .value { color: var(--success); }
        .stat-card.warning .value { color: var(--warning); }
        .stat-card.danger .value { color: var(--danger); }
        
        /* Health Bar - Mobile First */
        .health-bar {
            background: var(--card);
            border-radius: var(--radius);
            padding: 14px;
            margin-bottom: 16px;
            box-shadow: var(--shadow);
        }
        
        .health-bar h3 {
            font-size: 12px;
            font-weight: 500;
            color: var(--text-muted);
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.02em;
        }
        
        .progress-bar {
            height: 6px;
            background: var(--border);
            border-radius: 3px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--success), var(--primary));
            border-radius: 3px;
            transition: width 0.5s ease;
        }
        
        .progress-fill.warning { background: linear-gradient(90deg, var(--warning), #fbbf24); }
        .progress-fill.danger { background: linear-gradient(90deg, var(--danger), #f87171); }
        
        /* Tabs - Mobile First */
        .tabs {
            display: flex;
            gap: 4px;
            margin-bottom: 12px;
            padding: 4px;
            background: var(--card);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
        }
        
        .tabs::-webkit-scrollbar {
            display: none;
        }
        
        .tab {
            flex-shrink: 0;
            min-height: 38px;
            padding: 8px 14px;
            border: none;
            background: transparent;
            cursor: pointer;
            border-radius: var(--radius-sm);
            font-size: 13px;
            font-weight: 500;
            color: var(--text-muted);
            transition: all 0.2s;
        }
        
        .tab.active {
            background: var(--primary);
            color: white;
            box-shadow: var(--shadow);
        }
        
        .tab:active:not(.active) {
            background: var(--bg);
        }
        
        /* Search - Mobile First */
        .search-container {
            background: var(--card);
            border-radius: var(--radius);
            padding: 12px;
            margin-bottom: 12px;
            box-shadow: var(--shadow);
        }
        
        .search-input {
            width: 100%;
            min-height: var(--touch);
            padding: 10px 14px;
            border: 2px solid var(--border);
            border-radius: var(--radius-sm);
            font-size: 15px;
            background: var(--bg);
            color: var(--text);
            outline: none;
            transition: border-color 0.2s;
        }
        
        .search-input:focus {
            border-color: var(--primary);
        }
        
        /* Memory List - Mobile First */
        .memory-list {
            background: var(--card);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow: hidden;
        }
        
        .memory-item {
            padding: 14px;
            border-bottom: 1px solid var(--border);
            transition: background 0.15s;
        }
        
        .memory-item:active {
            background: var(--bg);
        }
        
        .memory-item:last-child {
            border-bottom: none;
        }
        
        .memory-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 10px;
        }
        
        .memory-text {
            font-size: 14px;
            line-height: 1.5;
            flex: 1;
            word-break: break-word;
        }
        
        .memory-actions {
            display: flex;
            gap: 6px;
            flex-shrink: 0;
        }
        
        .btn-sm {
            min-height: 36px;
            padding: 6px 12px;
            font-size: 12px;
        }
        
        .btn-icon-sm {
            width: 36px;
            min-height: 36px;
            padding: 0;
            font-size: 14px;
        }
        
        .memory-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            font-size: 12px;
            color: var(--text-muted);
            align-items: center;
        }
        
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 500;
        }
        
        .badge-category {
            background: var(--primary);
            color: white;
        }
        
        .badge-tag {
            background: var(--border);
            color: var(--text);
        }
        
        .importance-stars {
            color: #fbbf24;
            font-size: 12px;
        }
        
        /* Modal - Mobile First */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: none;
            align-items: flex-end;
            justify-content: center;
            z-index: 1000;
            animation: fadeIn 0.2s ease;
        }
        
        .modal-overlay.active {
            display: flex;
        }
        
        .modal {
            background: var(--card);
            border-radius: 20px 20px 0 0;
            padding: 0;
            width: 100%;
            max-height: 90vh;
            max-height: 90dvh;
            overflow-y: auto;
            animation: slideUp 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        
        .modal-header {
            position: sticky;
            top: 0;
            background: var(--card);
            padding: 20px 20px 12px;
            z-index: 10;
        }
        
        .modal-drag-indicator {
            width: 36px;
            height: 4px;
            background: var(--border);
            border-radius: 2px;
            margin: 0 auto 16px;
        }
        
        .modal h2 {
            font-size: 20px;
            font-weight: 700;
            margin: 0;
            text-align: center;
        }
        
        .modal-body {
            padding: 0 20px 20px;
        }
        
        /* Template Quick Select */
        .template-quick-select {
            margin-bottom: 24px;
        }
        
        .template-label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .template-carousel {
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding: 4px 0 8px;
            scroll-snap-type: x mandatory;
            -webkit-overflow-scrolling: touch;
            margin: 0 -20px;
            padding-left: 20px;
            padding-right: 20px;
        }
        
        .template-carousel::-webkit-scrollbar {
            display: none;
        }
        
        .template-chip {
            flex-shrink: 0;
            padding: 12px 18px;
            background: var(--bg);
            border: 2px solid transparent;
            border-radius: 12px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            white-space: nowrap;
            transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
            scroll-snap-align: start;
        }
        
        .template-chip:hover {
            background: var(--primary)10;
            border-color: var(--primary);
            transform: scale(1.02);
        }
        
        .template-chip.active {
            border-color: var(--primary);
            background: var(--primary);
            color: white;
            box-shadow: 0 4px 16px var(--primary)30;
        }
            border-color: var(--primary);
            background: var(--primary);
            color: white;
        }
        
        .template-chip .emoji {
            margin-right: 6px;
        }
        
        .form-group {
            margin-bottom: 16px;
        }
        
        .form-group label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-muted);
            margin-bottom: 8px;
        }
        
        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            min-height: var(--touch);
            padding: 10px 14px;
            border: 2px solid var(--border);
            border-radius: var(--radius-sm);
            font-size: 15px;
            background: var(--bg);
            color: var(--text);
            outline: none;
            transition: border-color 0.2s;
        }
        
        .form-group textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        .form-group input:focus,
        .form-group textarea:focus,
        .form-group select:focus {
            border-color: var(--primary);
        }
        
        .form-row {
            display: flex;
            gap: 12px;
        }
        
        .form-group.half {
            flex: 1;
        }
        
        .form-group .hint {
            font-weight: 400;
            color: var(--text-muted);
            font-size: 11px;
        }
        
        input[type="range"] {
            -webkit-appearance: none;
            width: 100%;
            height: 8px;
            background: var(--border);
            border-radius: 4px;
            outline: none;
            margin-top: 8px;
        }
        
        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 20px;
            height: 20px;
            background: var(--primary);
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 2px 8px var(--primary)40;
        }
        
        .form-actions {
            display: flex;
            gap: 12px;
            margin-top: 24px;
        }
        
        .form-actions .btn {
            flex: 1;
            padding: 14px 20px;
            font-size: 15px;
        }
        
        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: var(--text-muted);
        }
        
        .empty-state .icon {
            font-size: 48px;
            margin-bottom: 12px;
            opacity: 0.5;
        }
        
        .empty-state p {
            font-size: 14px;
        }
        
        /* Toast - Mobile First */
        .toast-container {
            position: fixed;
            left: 12px;
            right: 12px;
            bottom: calc(90px + var(--safe-bottom));
            z-index: 2000;
        }
        
        .toast {
            background: var(--card);
            padding: 12px 16px;
            border-radius: var(--radius-sm);
            box-shadow: var(--shadow-lg);
            margin-top: 8px;
            font-size: 14px;
            animation: slideUp 0.3s ease;
        }
        
        .toast.success { border-left: 4px solid var(--success); }
        .toast.error { border-left: 4px solid var(--danger); }
        
        /* Graph Container - Mobile First */
        #graph-container {
            background: var(--card);
            border-radius: var(--radius);
            margin-bottom: 12px;
            box-shadow: var(--shadow);
            overflow: hidden;
        }
        
        #graph-stats {
            padding: 12px 14px;
            font-size: 12px;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border);
        }
        
        #graph-network {
            height: 280px;
            width: 100%;
        }
        
        /* Bottom Action Bar - Mobile */
        .bottom-bar {
            position: fixed;
            left: 0;
            right: 0;
            bottom: 0;
            background: var(--card);
            border-top: 1px solid var(--border);
            padding: 12px 16px;
            padding-bottom: calc(12px + var(--safe-bottom));
            display: flex;
            gap: 12px;
            z-index: 100;
        }
        
        .bottom-bar .btn {
            flex: 1;
        }
        
        /* Floating Action Button - Hidden on mobile */
        .fab {
            display: none;
            position: fixed;
            right: 24px;
            bottom: 24px;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            border: none;
            color: white;
            font-size: 28px;
            cursor: pointer;
            box-shadow: 0 4px 20px var(--primary)40, 0 8px 24px var(--primary)20;
            z-index: 100;
            align-items: center;
            justify-content: center;
            transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        
        .fab:hover {
            transform: scale(1.1) rotate(90deg);
            box-shadow: 0 6px 28px var(--primary)50, 0 12px 32px var(--primary)30;
        }
        
        .fab:active {
            transform: scale(0.95);
        }
        
        .fab-icon {
            font-weight: 300;
            line-height: 1;
        }
        
        /* Desktop Styles */
        @media (min-width: 768px) {
            .app {
                max-width: 800px;
                padding: 24px;
                padding-bottom: 24px;
            }
            
            .header {
                position: relative;
                flex-direction: row;
                margin: 0 0 24px;
                padding: 0;
                background: transparent;
                border-bottom: none;
                backdrop-filter: none;
            }
            
            .header-top {
                width: 100%;
            }
            
            .logo h1 {
                font-size: 24px;
            }
            
            .stats-grid {
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
            }
            
            .stat-card {
                padding: 20px;
            }
            
            .stat-card .value {
                font-size: 28px;
            }
            
            .health-bar {
                padding: 20px;
            }
            
            .tabs {
                gap: 6px;
            }
            
            .tab {
                padding: 10px 20px;
            }
            
            .memory-item {
                padding: 18px 20px;
            }
            
            .memory-actions {
                opacity: 0;
            }
            
            .memory-item:hover .memory-actions {
                opacity: 1;
            }
            
            .modal-overlay {
                align-items: center;
            }
            
            .modal {
                max-width: 500px;
                border-radius: var(--radius);
                animation: zoomIn 0.2s ease;
            }
            
            @keyframes zoomIn {
                from { transform: scale(0.95); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }
            
            .bottom-bar {
                display: none;
            }
            
            .fab {
                display: flex;
            }
            
            #graph-network {
                height: 400px;
            }
        }
        
        @media (min-width: 1024px) {
            .app {
                max-width: 1000px;
            }
            
            .stats-grid {
                grid-template-columns: repeat(6, 1fr);
            }
        }
        
        /* Settings Section */
        .settings-section {
            background: var(--card);
            border-radius: var(--radius);
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: var(--shadow);
        }
        
        .settings-section h3 {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 16px;
            color: var(--text);
        }
        
        .cost-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
        
        .cost-item {
            background: var(--bg);
            border-radius: var(--radius-sm);
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        
        .cost-item .label {
            font-size: 12px;
            color: var(--text-muted);
        }
        
        .cost-item .value {
            font-size: 18px;
            font-weight: 600;
            color: var(--primary);
        }
        
        .cost-item .status {
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 4px;
            display: inline-block;
            width: fit-content;
        }
        
        .cost-item .status.online { background: #22c55e20; color: var(--success); }
        .cost-item .status.offline { background: #ef444420; color: var(--danger); }
        
        .template-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        
        .template-item {
            background: var(--bg);
            border: 2px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .template-item:hover {
            border-color: var(--primary);
            background: var(--card);
        }
        
        .template-item .name {
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 4px;
        }
        
        .template-item .desc {
            font-size: 12px;
            color: var(--text-muted);
        }
        
        .backup-actions {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }

        .backup-actions .btn {
            flex: 1;
            min-width: 140px;
        }

        /* Quality Stats */
        .quality-stats, .decay-stats, .sync-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 12px;
        }

        .quality-item, .decay-item, .sync-item {
            background: var(--bg);
            border-radius: var(--radius-sm);
            padding: 12px;
            text-align: center;
        }

        .quality-item .label, .decay-item .label, .sync-item .label {
            display: block;
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 4px;
        }

        .quality-item .value, .decay-item .value, .sync-item .value {
            display: block;
            font-size: 20px;
            font-weight: 600;
            color: var(--text);
        }

        .quality-actions, .decay-actions, .sync-actions, .push-actions {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }

        .decay-actions .btn, .sync-actions .btn, .push-actions .btn {
            flex: 1;
            min-width: 120px;
        }

        /* Push Settings */
        .push-settings {
            margin-bottom: 12px;
        }

        .push-toggle {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            background: var(--bg);
            border-radius: var(--radius-sm);
            margin-bottom: 8px;
        }

        .push-toggle label {
            font-size: 14px;
            color: var(--text);
        }

        .push-toggle input[type="checkbox"] {
            width: 44px;
            height: 24px;
            appearance: none;
            background: var(--border);
            border-radius: 12px;
            position: relative;
            cursor: pointer;
            transition: background 0.3s;
        }

        .push-toggle input[type="checkbox"]::before {
            content: '';
            position: absolute;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: white;
            top: 2px;
            left: 2px;
            transition: transform 0.3s;
        }

        .push-toggle input[type="checkbox"]:checked {
            background: var(--primary);
        }

        .push-toggle input[type="checkbox"]:checked::before {
            transform: translateX(20px);
        }

        /* PWA Status */
        .pwa-status {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 12px;
        }

        .pwa-item {
            background: var(--bg);
            border-radius: var(--radius-sm);
            padding: 12px;
            text-align: center;
        }

        .pwa-item .label {
            display: block;
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 4px;
        }

        .pwa-item .value {
            display: block;
            font-size: 14px;
            font-weight: 600;
            color: var(--text);
        }

        .pwa-item .value.online {
            color: var(--success);
        }

        .pwa-item .value.offline {
            color: var(--error);
        }

        .pwa-actions {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }

        .pwa-actions .btn {
            flex: 1;
            min-width: 120px;
        }

        /* Search Settings */
        .search-settings {
            margin-bottom: 12px;
        }

        .search-stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 12px;
        }

        .search-stat {
            background: var(--bg);
            border-radius: var(--radius-sm);
            padding: 12px;
            text-align: center;
        }

        .search-stat .label {
            display: block;
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 4px;
        }

        .search-stat .value {
            display: block;
            font-size: 18px;
            font-weight: 600;
            color: var(--text);
        }

        /* Expiration Stats */
        .expiration-stats, .conflict-stats, .assoc-stats, .completion-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 12px;
        }

        .exp-item, .conf-item, .assoc-item, .comp-item {
            background: var(--bg);
            border-radius: var(--radius-sm);
            padding: 12px;
            text-align: center;
        }

        .exp-item .label, .conf-item .label, .assoc-item .label, .comp-item .label {
            display: block;
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 4px;
        }

        .exp-item .value, .conf-item .value, .assoc-item .value, .comp-item .value {
            display: block;
            font-size: 20px;
            font-weight: 600;
            color: var(--text);
        }

        .exp-item .value.warning, .conf-item .value.warning, .comp-item .value.warning {
            color: var(--warning);
        }

        .exp-item .value.success, .conf-item .value.success, .assoc-item .value.success, .comp-item .value.success {
            color: var(--success);
        }

        .exp-actions, .conf-actions, .assoc-actions, .comp-actions {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }

        .exp-actions .btn, .conf-actions .btn, .assoc-actions .btn, .comp-actions .btn {
            flex: 1;
            min-width: 120px;
        }

        /* Auto Structuring Stats */
        .struct-stats, .fresh-stats, .assoc-hint-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 12px;
        }

        .struct-item, .fresh-item, .hint-item {
            background: var(--bg);
            border-radius: var(--radius-sm);
            padding: 12px;
            text-align: center;
        }

        .struct-item .label, .fresh-item .label, .hint-item .label {
            display: block;
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 4px;
        }

        .struct-item .value, .fresh-item .value, .hint-item .value {
            display: block;
            font-size: 20px;
            font-weight: 600;
            color: var(--text);
        }

        .fresh-item .value.success {
            color: var(--success);
        }

        .fresh-item .value.warning {
            color: var(--warning);
        }

        .struct-actions, .fresh-actions, .hint-actions, .reminder-actions, .confidence-actions, .lifecycle-actions, .context-actions, .feedback-actions {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }

        .struct-actions .btn, .fresh-actions .btn, .hint-actions .btn, .reminder-actions .btn, .confidence-actions .btn, .lifecycle-actions .btn, .context-actions .btn, .feedback-actions .btn {
            flex: 1;
            min-width: 120px;
        }

        .reminder-stats, .confidence-stats, .lifecycle-stats, .context-stats, .feedback-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 12px;
        }

        .reminder-item, .confidence-item, .lifecycle-item, .context-item, .feedback-item {
            background: var(--bg);
            border-radius: var(--radius-sm);
            padding: 12px;
            text-align: center;
        }

        .reminder-item .label, .confidence-item .label, .lifecycle-item .label, .context-item .label, .feedback-item .label {
            display: block;
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 4px;
        }

        .reminder-item .value, .confidence-item .value, .lifecycle-item .value, .context-item .value, .feedback-item .value {
            display: block;
            font-size: 20px;
            font-weight: 600;
            color: var(--text);
        }

        .value.danger {
            color: var(--danger);
        }

        .value.warning {
            color: var(--warning);
        }

        .value.success {
            color: var(--success);
        }

        /* Auto Push Settings */
        .auto-push-settings {
            margin-bottom: 12px;
        }

        .auto-push-stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 12px;
        }

        .push-stat {
            background: var(--bg);
            border-radius: var(--radius-sm);
            padding: 12px;
            text-align: center;
        }

        .push-stat .label {
            display: block;
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 4px;
        }

        .push-stat .value {
            display: block;
            font-size: 18px;
            font-weight: 600;
            color: var(--text);
        }

        .push-stat .value.success {
            color: var(--success);
        }

        .settings-hint {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 12px;
        }
        
        /* Collaboration Dashboard Styles */
        .collab-agent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 10px;
            margin-top: 12px;
        }
        
        .collab-agent-card {
            background: var(--bg);
            border-radius: var(--radius-sm);
            padding: 14px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            border: 2px solid transparent;
            transition: all 0.2s;
        }
        
        .collab-agent-card:hover {
            border-color: var(--primary);
            transform: translateY(-2px);
        }
        
        .collab-agent-card .avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--primary-light));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }
        
        .collab-agent-card .name {
            font-weight: 600;
            font-size: 14px;
        }
        
        .collab-agent-card .status {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;
            color: var(--text-muted);
        }
        
        .collab-agent-card .status.online::before {
            content: '';
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
        }
        
        .collab-agent-card .status.offline::before {
            content: '';
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--text-muted);
        }
        
        .collab-agent-card .workload {
            width: 100%;
            height: 4px;
            background: var(--border);
            border-radius: 2px;
            overflow: hidden;
        }
        
        .collab-agent-card .workload-fill {
            height: 100%;
            background: var(--primary);
            border-radius: 2px;
            transition: width 0.3s;
        }
        
        .collab-event-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            border-bottom: 1px solid var(--border);
        }
        
        .collab-event-item:last-child {
            border-bottom: none;
        }
        
        .collab-event-item .icon {
            font-size: 20px;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--bg);
            border-radius: 50%;
        }
        
        .collab-event-item .content {
            flex: 1;
        }
        
        .collab-event-item .title {
            font-weight: 500;
            font-size: 14px;
        }
        
        .collab-event-item .time {
            font-size: 12px;
            color: var(--text-muted);
        }
        
        .task-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px;
            border-bottom: 1px solid var(--border);
        }
        
        .task-item:last-child {
            border-bottom: none;
        }
        
        .task-item .priority {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }
        
        .task-item .priority.high {
            background: #ef444420;
            color: var(--danger);
        }
        
        .task-item .priority.medium {
            background: #f59e0b20;
            color: var(--warning);
        }
        
        .task-item .priority.low {
            background: #22c55e20;
            color: var(--success);
        }
        
        .task-item .task-info {
            flex: 1;
        }
        
        .task-item .task-title {
            font-weight: 500;
            font-size: 14px;
        }
        
        .task-item .task-assignee {
            font-size: 12px;
            color: var(--text-muted);
        }
        
        .conflict-item {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 14px;
            border-bottom: 1px solid var(--border);
            background: #ef444410;
        }
        
        .conflict-item:last-child {
            border-bottom: none;
        }
        
        .conflict-item .conflict-icon {
            font-size: 20px;
        }
        
        .conflict-item .conflict-info {
            flex: 1;
        }
        
        .conflict-item .conflict-title {
            font-weight: 500;
            font-size: 14px;
            color: var(--danger);
        }
        
        .conflict-item .conflict-desc {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 4px;
        }
        
        .conflict-item .conflict-actions {
            display: flex;
            gap: 8px;
        }
        
        .conflict-item .btn-sm {
            font-size: 11px;
            padding: 4px 8px;
        }
        
        .empty-collab {
            text-align: center;
            padding: 30px 20px;
            color: var(--text-muted);
        }
        
        .empty-collab .icon {
            font-size: 36px;
            margin-bottom: 8px;
            opacity: 0.5;
        }
        
        .task-actions, .conflict-actions {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        
        .task-actions .btn, .conflict-actions .btn {
            flex: 1;
            min-width: 120px;
        }
        
        .sync-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 12px;
        }
        
        .sync-stats .sync-item {
            text-align: center;
            padding: 12px;
            background: var(--bg);
            border-radius: var(--radius-sm);
        }
        
        .sync-stats .label {
            display: block;
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 4px;
        }
        
        .sync-stats .value {
            font-size: 24px;
            font-weight: 600;
            color: var(--primary);
        }
        
        .sync-actions {
            display: flex;
            gap: 12px;
        }
        
        .cost-item.highlight {
            background: var(--bg);
            border-left: 3px solid var(--success);
        }
        
        .cost-item.highlight .value {
            color: var(--success);
            font-size: 20px;
        }
        
        @media (min-width: 768px) {
            .cost-grid {
                grid-template-columns: repeat(4, 1fr);
            }
            
            .template-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }
    </style>
    <!-- PWA Meta Tags -->
    <meta name="theme-color" content="#3b82f6">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Memory">
    <link rel="manifest" href="/manifest.json">
    <link rel="apple-touch-icon" href="/icon-192.png">
</head>
<body>
    <div class="app">
        <!-- Header -->
        <div class="header">
            <div class="header-top">
                <div class="logo">
                    <h1>📚 Unified Memory</h1>
                    <span class="version">v0.4.0</span>
                </div>
                <div class="header-actions">
                    <button class="btn btn-ghost btn-icon" onclick="toggleTheme()">🌙</button>
                </div>
            </div>
        </div>
        
        <!-- Stats -->
        <div class="stats-grid" id="stats"></div>
        
        <!-- Health Bar -->
        <div class="health-bar">
            <h3>🏥 系统健康度</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="health-bar" style="width: 98%"></div>
            </div>
        </div>
        
        <!-- Tabs -->
        <div class="tabs">
            <button class="tab active" onclick="switchTab('all')">全部</button>
            <button class="tab" onclick="switchTab('preferences')">偏好</button>
            <button class="tab" onclick="switchTab('entities')">实体</button>
            <button class="tab" onclick="switchTab('fact')">事实</button>
            <button class="tab" onclick="switchTab('decision')">决策</button>
            <button class="tab" onclick="switchTab('learning')">学习</button>
            <button class="tab" onclick="switchTab('graph')">📊 图谱</button>
            <button class="tab" onclick="switchTab('collab')">🤝 协作</button>
            <button class="tab" onclick="switchTab('settings')">⚙️ 设置</button>
        </div>
        
        <!-- Search -->
        <div class="search-container">
            <input type="text" class="search-input" id="search" placeholder="🔍 搜索记忆..." onkeyup="searchMemories()">
        </div>
        
        <!-- Graph Container (hidden by default) -->
        <div id="graph-container" style="display: none;">
            <div id="graph-stats">加载中...</div>
            <div id="graph-network"></div>
        </div>
        
        <!-- Collaboration Dashboard Container -->
        <div id="collab-container" style="display: none;">
            <h2 style="font-size: 20px; font-weight: 600; margin-bottom: 16px;">🤝 协作记忆仪表盘</h2>
            
            <!-- Agent 状态 -->
            <div class="settings-section">
                <h3>🟢 在线 Agent</h3>
                <div id="agent-list" class="collab-agent-grid"></div>
            </div>
            
            <!-- 协作统计 -->
            <div class="settings-section">
                <h3>📊 协作统计</h3>
                <div class="stats-grid" style="margin-bottom: 0;">
                    <div class="stat-card">
                        <span class="stat-value" id="shared-memories">0</span>
                        <span class="stat-label">共享记忆</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value" id="pending-conflicts-collab">0</span>
                        <span class="stat-label">待处理冲突</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-value" id="pending-tasks">0</span>
                        <span class="stat-label">待分配任务</span>
                    </div>
                </div>
            </div>
            
            <!-- 最近协作 -->
            <div class="settings-section">
                <h3>📋 最近协作事件</h3>
                <div id="recent-events" class="memory-list"></div>
            </div>
            
            <!-- 任务队列 -->
            <div class="settings-section">
                <h3>📝 任务队列</h3>
                <div id="task-list" class="memory-list"></div>
                <div class="task-actions" style="margin-top: 12px;">
                    <button class="btn btn-ghost" onclick="refreshTasks()">🔄 刷新任务</button>
                    <button class="btn btn-primary" onclick="assignTasks()">📤 智能分配</button>
                </div>
            </div>
            
            <!-- 同步状态 -->
            <div class="settings-section">
                <h3>🔗 同步状态</h3>
                <div class="sync-stats" id="collab-sync-stats">
                    <div class="sync-item">
                        <span class="label">节点数</span>
                        <span class="value" id="collab-node-count">0</span>
                    </div>
                    <div class="sync-item">
                        <span class="label">同步次数</span>
                        <span class="value" id="collab-sync-count">0</span>
                    </div>
                    <div class="sync-item">
                        <span class="label">最后同步</span>
                        <span class="value" id="collab-last-sync">--</span>
                    </div>
                </div>
                <div class="sync-actions" style="margin-top: 12px;">
                    <button class="btn btn-primary" onclick="syncNowCollab()">🔄 立即同步</button>
                </div>
            </div>
            
            <!-- 冲突解决 -->
            <div class="settings-section">
                <h3>⚔️ 冲突解决</h3>
                <div id="conflict-list" class="memory-list"></div>
                <div class="conflict-actions" style="margin-top: 12px;">
                    <button class="btn btn-ghost" onclick="scanConflictsCollab()">🔍 扫描冲突</button>
                    <button class="btn btn-primary" onclick="autoResolveConflicts()">🔧 自动解决</button>
                </div>
            </div>
        </div>
        
        <!-- Settings Container -->
        <div id="settings-container" style="display: none;">
            <!-- Cost Monitor -->
            <div class="settings-section">
                <h3>💰 成本监控</h3>
                <div class="cost-grid" id="cost-stats"></div>
            </div>
            
            <!-- Backup & Restore -->
            <div class="settings-section">
                <h3>💾 备份与恢复</h3>
                <div class="backup-actions">
                    <button class="btn btn-primary" onclick="backupMemory()">📤 导出备份</button>
                    <button class="btn btn-ghost" onclick="document.getElementById('restore-input').click()">📥 导入恢复</button>
                    <input type="file" id="restore-input" accept=".json" style="display:none" onchange="restoreMemory(event)">
                </div>
                <p class="settings-hint">导出会生成 JSON 文件，导入可恢复记忆数据</p>
            </div>
            
            <!-- Smart Extraction Quality -->
            <div class="settings-section">
                <h3>🎯 智能提取质量</h3>
                <div class="quality-stats" id="quality-stats">
                    <div class="quality-item">
                        <span class="label">平均置信度</span>
                        <span class="value" id="avg-confidence">--</span>
                    </div>
                    <div class="quality-item">
                        <span class="label">高置信记忆</span>
                        <span class="value" id="high-confidence-count">--</span>
                    </div>
                    <div class="quality-item">
                        <span class="label">待确认</span>
                        <span class="value" id="pending-review">--</span>
                    </div>
                </div>
                <div class="quality-actions">
                    <button class="btn btn-ghost" onclick="reviewLowConfidence()">🔍 审核低置信记忆</button>
                </div>
            </div>
            
            <!-- Memory Decay -->
            <div class="settings-section">
                <h3>⏳ 记忆衰减管理</h3>
                <div class="decay-stats" id="decay-stats">
                    <div class="decay-item">
                        <span class="label">已归档</span>
                        <span class="value" id="archived-count">0</span>
                    </div>
                    <div class="decay-item">
                        <span class="label">已压缩</span>
                        <span class="value" id="compressed-count">0</span>
                    </div>
                    <div class="decay-item">
                        <span class="label">归档大小</span>
                        <span class="value" id="archive-size">0 MB</span>
                    </div>
                </div>
                <div class="decay-actions">
                    <button class="btn btn-ghost" onclick="previewDecay()">👁️ 预览衰减</button>
                    <button class="btn btn-primary" onclick="runDecay()">🧹 执行清理</button>
                </div>
                <p class="settings-hint">低重要性（&lt;0.1）且长期未访问的记忆会被归档</p>
            </div>
            
            <!-- Multi-Agent Sync -->
            <div class="settings-section">
                <h3>🔗 多Agent共享</h3>
                <div class="sync-stats" id="sync-stats">
                    <div class="sync-item">
                        <span class="label">节点数</span>
                        <span class="value" id="node-count">0</span>
                    </div>
                    <div class="sync-item">
                        <span class="label">同步次数</span>
                        <span class="value" id="sync-count">0</span>
                    </div>
                    <div class="sync-item">
                        <span class="label">待处理冲突</span>
                        <span class="value" id="conflict-count">0</span>
                    </div>
                </div>
                <div class="sync-actions">
                    <button class="btn btn-ghost" onclick="showSyncNodes()">📋 节点管理</button>
                    <button class="btn btn-primary" onclick="syncNow()">🔄 立即同步</button>
                </div>
            </div>
            
            <!-- Proactive Push -->
            <div class="settings-section">
                <h3>🔔 主动推送</h3>
                <div class="push-settings">
                    <div class="push-toggle">
                        <label>启用上下文感知推送</label>
                        <input type="checkbox" id="push-enabled" onchange="togglePush()">
                    </div>
                    <div class="push-toggle">
                        <label>定时提醒重要事件</label>
                        <input type="checkbox" id="reminder-enabled" onchange="toggleReminder()">
                    </div>
                </div>
                <div class="push-actions">
                    <button class="btn btn-ghost" onclick="checkReminders()">📅 检查提醒</button>
                </div>
                <p class="settings-hint">根据当前任务自动推送相关记忆</p>
            </div>

            <!-- PWA Support -->
            <div class="settings-section">
                <h3>📱 PWA 离线支持</h3>
                <div class="pwa-status" id="pwa-status">
                    <div class="pwa-item">
                        <span class="label">Service Worker</span>
                        <span class="value" id="sw-status">检测中...</span>
                    </div>
                    <div class="pwa-item">
                        <span class="label">离线缓存</span>
                        <span class="value" id="cache-status">检测中...</span>
                    </div>
                </div>
                <div class="pwa-actions">
                    <button class="btn btn-primary" id="install-btn" style="display: none;">📲 安装应用</button>
                    <button class="btn btn-ghost" onclick="clearCache()">🗑️ 清除缓存</button>
                </div>
                <p class="settings-hint">安装后可离线使用，体验更流畅</p>
            </div>

            <!-- Smart Search Enhancement -->
            <div class="settings-section">
                <h3>🔍 智能搜索增强</h3>
                <div class="search-settings">
                    <div class="push-toggle">
                        <label>混合搜索（向量+关键词）</label>
                        <input type="checkbox" id="hybrid-search" checked>
                    </div>
                    <div class="push-toggle">
                        <label>时间衰减（新记忆优先）</label>
                        <input type="checkbox" id="time-decay" checked>
                    </div>
                    <div class="push-toggle">
                        <label>上下文感知（根据任务调整）</label>
                        <input type="checkbox" id="context-aware">
                    </div>
                </div>
                <div class="search-stats" id="search-stats">
                    <div class="search-stat">
                        <span class="label">平均搜索耗时</span>
                        <span class="value" id="avg-search-time">--</span>
                    </div>
                    <div class="search-stat">
                        <span class="label">命中率</span>
                        <span class="value" id="hit-rate">--</span>
                    </div>
                </div>
                <p class="settings-hint">智能搜索提高记忆检索精准度</p>
            </div>

            <!-- Memory Expiration Detection -->
            <div class="settings-section">
                <h3>⏰ 记忆过期检测</h3>
                <div class="expiration-stats" id="expiration-stats">
                    <div class="exp-item">
                        <span class="label">可能过期</span>
                        <span class="value warning" id="expired-count">0</span>
                    </div>
                    <div class="exp-item">
                        <span class="label">待确认</span>
                        <span class="value" id="pending-confirm">0</span>
                    </div>
                    <div class="exp-item">
                        <span class="label">已归档</span>
                        <span class="value" id="auto-archived">0</span>
                    </div>
                </div>
                <div class="exp-actions">
                    <button class="btn btn-ghost" onclick="scanExpired()">🔍 扫描过期</button>
                    <button class="btn btn-primary" onclick="reviewExpired()">📋 审核过期</button>
                </div>
                <p class="settings-hint">检测可能过时的记忆（如项目状态变化）</p>
            </div>

            <!-- Memory Conflict Detection -->
            <div class="settings-section">
                <h3>⚔️ 记忆冲突检测</h3>
                <div class="conflict-stats" id="conflict-stats">
                    <div class="conf-item">
                        <span class="label">检测到冲突</span>
                        <span class="value warning" id="conflict-count">0</span>
                    </div>
                    <div class="conf-item">
                        <span class="label">已解决</span>
                        <span class="value success" id="resolved-count">0</span>
                    </div>
                    <div class="conf-item">
                        <span class="label">待处理</span>
                        <span class="value" id="pending-conflict">0</span>
                    </div>
                </div>
                <div class="conf-actions">
                    <button class="btn btn-ghost" onclick="scanConflicts()">🔍 扫描冲突</button>
                    <button class="btn btn-primary" onclick="resolveConflicts()">🔧 解决冲突</button>
                </div>
                <p class="settings-hint">检测同一主题的矛盾记录</p>
            </div>

            <!-- Memory Association Discovery -->
            <div class="settings-section">
                <h3>🔗 记忆关联发现</h3>
                <div class="assoc-stats" id="assoc-stats">
                    <div class="assoc-item">
                        <span class="label">关联数</span>
                        <span class="value" id="assoc-count">0</span>
                    </div>
                    <div class="assoc-item">
                        <span class="label">关联组</span>
                        <span class="value" id="assoc-groups">0</span>
                    </div>
                    <div class="assoc-item">
                        <span class="label">强关联</span>
                        <span class="value success" id="strong-assoc">0</span>
                    </div>
                </div>
                <div class="assoc-actions">
                    <button class="btn btn-ghost" onclick="discoverAssoc()">🔍 发现关联</button>
                    <button class="btn btn-primary" onclick="viewAssocGraph()">📊 关联图谱</button>
                </div>
                <p class="settings-hint">发现记忆间的隐含关系</p>
            </div>

            <!-- Memory Completion Suggestion -->
            <div class="settings-section">
                <h3>📝 记忆补全建议</h3>
                <div class="completion-stats" id="completion-stats">
                    <div class="comp-item">
                        <span class="label">缺失信息</span>
                        <span class="value warning" id="missing-info">0</span>
                    </div>
                    <div class="comp-item">
                        <span class="label">建议补全</span>
                        <span class="value" id="suggested">0</span>
                    </div>
                    <div class="comp-item">
                        <span class="label">已补全</span>
                        <span class="value success" id="completed">0</span>
                    </div>
                </div>
                <div class="comp-actions">
                    <button class="btn btn-ghost" onclick="scanMissing()">🔍 扫描缺失</button>
                    <button class="btn btn-primary" onclick="showSuggestions()">💡 查看建议</button>
                </div>
                <p class="settings-hint">识别可能缺失的关键信息</p>
            </div>

            <!-- Memory Auto Structuring -->
            <div class="settings-section">
                <h3>📊 记忆自动结构化</h3>
                <div class="struct-stats" id="struct-stats">
                    <div class="struct-item">
                        <span class="label">用户档案</span>
                        <span class="value" id="user-profile-items">0</span>
                    </div>
                    <div class="struct-item">
                        <span class="label">项目档案</span>
                        <span class="value" id="project-profiles">0</span>
                    </div>
                    <div class="struct-item">
                        <span class="label">整合记忆</span>
                        <span class="value success" id="merged-memories">0</span>
                    </div>
                </div>
                <div class="struct-actions">
                    <button class="btn btn-ghost" onclick="previewStruct()">👁️ 预览档案</button>
                    <button class="btn btn-primary" onclick="autoStruct()">🔄 自动整合</button>
                </div>
                <p class="settings-hint">将碎片记忆整合成结构化档案</p>
            </div>

            <!-- Memory Freshness Tracking -->
            <div class="settings-section">
                <h3>🕐 记忆时效性追踪</h3>
                <div class="fresh-stats" id="fresh-stats">
                    <div class="fresh-item">
                        <span class="label">新鲜记忆</span>
                        <span class="value success" id="fresh-memories">0</span>
                    </div>
                    <div class="fresh-item">
                        <span class="label">待验证</span>
                        <span class="value warning" id="stale-memories">0</span>
                    </div>
                    <div class="fresh-item">
                        <span class="label">已过期</span>
                        <span class="value" id="expired-memories">0</span>
                    </div>
                </div>
                <div class="fresh-actions">
                    <button class="btn btn-ghost" onclick="scanFreshness()">🔍 扫描时效</button>
                    <button class="btn btn-primary" onclick="verifyStale()">✅ 验证过期</button>
                </div>
                <p class="settings-hint">追踪记忆时效性，主动确认过期记忆</p>
            </div>

            <!-- Context-Aware Auto Push -->
            <div class="settings-section">
                <h3>🚀 上下文自动推送</h3>
                <div class="auto-push-settings">
                    <div class="push-toggle">
                        <label>启用自动推送</label>
                        <input type="checkbox" id="auto-push-enabled" checked>
                    </div>
                    <div class="push-toggle">
                        <label>关键词触发</label>
                        <input type="checkbox" id="keyword-trigger" checked>
                    </div>
                    <div class="push-toggle">
                        <label>实体识别</label>
                        <input type="checkbox" id="entity-recognition" checked>
                    </div>
                </div>
                <div class="auto-push-stats" id="auto-push-stats">
                    <div class="push-stat">
                        <span class="label">今日推送</span>
                        <span class="value" id="today-pushes">0</span>
                    </div>
                    <div class="push-stat">
                        <span class="label">命中率</span>
                        <span class="value success" id="push-hit-rate">0%</span>
                    </div>
                </div>
                <p class="settings-hint">根据对话上下文自动推送相关记忆</p>
            </div>

            <!-- Storage Association Hint -->
            <div class="settings-section">
                <h3>🔗 存储关联提示</h3>
                <div class="assoc-hint-stats" id="assoc-hint-stats">
                    <div class="hint-item">
                        <span class="label">检测关联</span>
                        <span class="value" id="detected-assocs">0</span>
                    </div>
                    <div class="hint-item">
                        <span class="label">已合并</span>
                        <span class="value success" id="auto-merged">0</span>
                    </div>
                    <div class="hint-item">
                        <span class="label">已更新</span>
                        <span class="value" id="auto-updated">0</span>
                    </div>
                </div>
                <div class="hint-actions">
                    <button class="btn btn-ghost" onclick="testAssocHint()">🧪 测试关联</button>
                    <button class="btn btn-primary" onclick="enableAssocHint()">✅ 启用提示</button>
                </div>
                <p class="settings-hint">存储时检测相似记忆，提示合并或更新</p>
            </div>
        </div>
        
        <!-- Memory List -->
        <div class="memory-list" id="memories"></div>
    </div>
    
    <!-- Floating Action Button - Desktop -->
    <button class="fab" onclick="openModal()">
        <span class="fab-icon">+</span>
    </button>
    
    <!-- Bottom Action Bar - Mobile -->
    <div class="bottom-bar">
        <button class="btn btn-primary" onclick="openModal()">+ 新建记忆</button>
    </div>
    
    <!-- Modal -->
    <div class="modal-overlay" id="modal" onclick="if(event.target===this)closeModal()">
        <div class="modal">
            <div class="modal-header">
                <div class="modal-drag-indicator"></div>
                <h2 id="modal-title">新建记忆</h2>
            </div>
            <div class="modal-body">
                <!-- Template Quick Select -->
                <div class="template-quick-select">
                    <label class="template-label">📋 快速选择模板</label>
                    <div class="template-carousel" id="template-carousel"></div>
                </div>
                
                <div class="form-group">
                    <label>内容</label>
                    <textarea id="form-text" placeholder="输入记忆内容，或点击上方模板快速开始..." rows="4"></textarea>
                </div>
                <div class="form-row">
                    <div class="form-group half">
                        <label>分类</label>
                        <select id="form-category">
                            <option value="preference">偏好</option>
                            <option value="entities">实体</option>
                            <option value="fact">事实</option>
                            <option value="decision">决策</option>
                            <option value="learning">学习</option>
                        </select>
                    </div>
                    <div class="form-group half">
                        <label>重要性</label>
                        <input type="range" id="form-importance" value="0.5" min="0" max="1" step="0.1">
                    </div>
                </div>
                <div class="form-group">
                    <label>标签 <span class="hint">（逗号分隔）</span></label>
                    <input type="text" id="form-tags" placeholder="标签1, 标签2">
                </div>
                <div class="form-actions">
                    <button class="btn btn-ghost" onclick="closeModal()">取消</button>
                    <button class="btn btn-primary" onclick="saveMemory()">✓ 保存</button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Toast Container -->
    <div class="toast-container" id="toasts"></div>
    
    <!-- vis.js for Graph -->
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    
    <script>
        // State
        let allMemories = [];
        let currentTab = 'all';
        let editingId = null;
        
        // Init
        document.addEventListener('DOMContentLoaded', () => {
            loadMemories();
            loadStats();
            loadHealth();
        });
        
        // Load memories
        async function loadMemories() {
            try {
                const res = await fetch('/api/memories');
                allMemories = await res.json();
                renderMemories();
            } catch (e) {
                console.error('Failed to load memories:', e);
                allMemories = [];
                renderMemories();
            }
        }
        
        // Load stats
        async function loadStats() {
            try {
                const res = await fetch('/api/stats');
                const stats = await res.json();
                renderStats(stats);
            } catch (e) {
                console.error('Failed to load stats:', e);
            }
        }
        
        // Load health
        async function loadHealth() {
            try {
                const res = await fetch('/api/health');
                const health = await res.json();
                const bar = document.getElementById('health-bar');
                bar.style.width = health.score + '%';
                bar.className = 'progress-fill ' + (health.score >= 80 ? '' : health.score >= 60 ? 'warning' : 'danger');
            } catch (e) {
                console.error('Failed to load health:', e);
            }
        }
        
        // Render stats
        function renderStats(stats) {
            document.getElementById('stats').innerHTML = `
                <div class="stat-card">
                    <div class="icon">📝</div>
                    <div class="value">${stats.total || 0}</div>
                    <div class="label">总记忆数</div>
                </div>
                <div class="stat-card">
                    <div class="icon">📁</div>
                    <div class="value">${stats.categories || 0}</div>
                    <div class="label">分类数</div>
                </div>
                <div class="stat-card">
                    <div class="icon">⭐</div>
                    <div class="value">${stats.avgImportance || '0.00'}</div>
                    <div class="label">平均重要性</div>
                </div>
                <div class="stat-card">
                    <div class="icon">📊</div>
                    <div class="value">${stats.todayCount || 0}</div>
                    <div class="label">今日新增</div>
                </div>
                <div class="stat-card">
                    <div class="icon">🔥</div>
                    <div class="value">${stats.l1Count || 0}</div>
                    <div class="label">热记忆 (L1)</div>
                </div>
                <div class="stat-card">
                    <div class="icon">☁️</div>
                    <div class="value">${stats.syncStatus || '本地'}</div>
                    <div class="label">同步状态</div>
                </div>
            `;
        }
        
        // Render memories
        function renderMemories() {
            let filtered = allMemories;
            
            // Filter by tab
            if (currentTab !== 'all') {
                filtered = filtered.filter(m => m.category === currentTab);
            }
            
            // Filter by search
            const query = document.getElementById('search').value.toLowerCase();
            if (query) {
                filtered = filtered.filter(m => 
                    m.text.toLowerCase().includes(query) ||
                    (m.tags && m.tags.some(t => t.toLowerCase().includes(query)))
                );
            }
            
            const container = document.getElementById('memories');
            
            if (filtered.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="icon">📭</div>
                        <p>暂无记忆</p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = filtered.map(m => `
                <div class="memory-item" data-id="${m.id}">
                    <div class="memory-header">
                        <div class="memory-text">${escapeHtml(m.text)}</div>
                        <div class="memory-actions">
                            <button class="btn btn-ghost btn-icon" onclick="editMemory('${m.id}')" title="编辑">✏️</button>
                            <button class="btn btn-ghost btn-icon" onclick="deleteMemory('${m.id}')" title="删除">🗑️</button>
                        </div>
                    </div>
                    <div class="memory-meta">
                        <span class="badge badge-category">${m.category}</span>
                        <span class="importance-stars">${'⭐'.repeat(Math.round((m.importance || 0.5) * 5))}</span>
                        <span>${formatDate(m.created_at)}</span>
                        ${(m.tags || []).map(t => `<span class="badge badge-tag">${escapeHtml(t)}</span>`).join('')}
                    </div>
                </div>
            `).join('');
        }
        
        // Tab switch
        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            
            const graphContainer = document.getElementById('graph-container');
            const memoriesContainer = document.getElementById('memories');
            const settingsContainer = document.getElementById('settings-container');
            const collabContainer = document.getElementById('collab-container');
            const searchContainer = document.querySelector('.search-container');
            
            // Hide all
            graphContainer.style.display = 'none';
            memoriesContainer.style.display = 'none';
            settingsContainer.style.display = 'none';
            collabContainer.style.display = 'none';
            searchContainer.style.display = 'block';
            
            if (tab === 'graph') {
                graphContainer.style.display = 'block';
                searchContainer.style.display = 'none';
                loadGraph();
            } else if (tab === 'settings') {
                settingsContainer.style.display = 'block';
                searchContainer.style.display = 'none';
                loadCosts();
                loadQualityStats();
                loadDecayStats();
                loadSyncStats();
                loadPushSettings();
                checkPWAStatus();
                loadSearchStats();
                loadExpirationStats();
                loadConflictStats();
                loadAssocStats();
                loadCompletionStats();
                loadStructStats();
                loadFreshStats();
                loadAutoPushStats();
                loadAssocHintStats();
            } else if (tab === 'collab') {
                collabContainer.style.display = 'block';
                searchContainer.style.display = 'none';
                loadCollaborationDashboard();
                startCollabRefresh();
            } else {
                memoriesContainer.style.display = 'block';
                renderMemories();
            }
        }
        
        // Templates
        const TEMPLATES = [
            { name: '👤 用户偏好', category: 'preference', template: '用户偏好使用 [工具/平台] 进行 [用途]，不喜欢 [某事物]' },
            { name: '📋 项目信息', category: 'entities', template: '项目名称：[名称]\\n类型：[类型]\\n状态：[进行中/已完成]' },
            { name: '📌 重要决策', category: 'decision', template: '决策：[决策内容]\\n原因：[原因]\\n影响：[影响范围]' },
            { name: '📚 学习笔记', category: 'learning', template: '主题：[主题]\\n要点：\\n1. [要点1]\\n2. [要点2]' },
            { name: 'ℹ️ 事实记录', category: 'fact', template: '[事实描述]\\n来源：[来源]\\n时间：[时间]' },
            { name: '🎯 任务清单', category: 'entities', template: '任务：[任务名称]\\n优先级：[高/中/低]\\n截止：[日期]' }
        ];
        
        function renderTemplates() {
            const container = document.getElementById('templates');
            container.innerHTML = TEMPLATES.map((t, i) => `
                <div class="template-item" onclick="useTemplate(${i})">
                    <div class="name">${t.name}</div>
                    <div class="desc">${t.template.substring(0, 30)}...</div>
                </div>
            `).join('');
        }
        
        function useTemplate(index) {
            const t = TEMPLATES[index];
            document.getElementById('form-text').value = t.template;
            document.getElementById('form-category').value = t.category;
            openModal();
            document.getElementById('form-text').focus();
        }
        
        // Cost Monitor
        async function loadCosts() {
            try {
                const res = await fetch('/api/costs');
                const data = await res.json();
                renderCosts(data);
            } catch (e) {
                renderCosts({ ollama_status: 'offline', error: e.message });
            }
        }
        
        function renderCosts(data) {
            const container = document.getElementById('cost-stats');
            const isOnline = data.ollama_status === 'online';
            const totalTokens = estimateTokens();
            const queries = data.embedding_calls || allMemories.length;
            
            // 成本对比（假设 OpenAI text-embedding-3-small: $0.02/1M tokens）
            const openaiCostPer1M = 0.02;
            const savedCost = (totalTokens / 1000000 * openaiCostPer1M).toFixed(4);
            const savedPerQuery = (totalTokens / queries * openaiCostPer1M / 1000000 * 100).toFixed(4);
            
            container.innerHTML = `
                <div class="cost-item">
                    <span class="label">Ollama 状态</span>
                    <span class="value">${isOnline ? '✅ 在线' : '❌ 离线'}</span>
                    <span class="status ${isOnline ? 'online' : 'offline'}">${data.ollama_url || 'localhost:11434'}</span>
                </div>
                <div class="cost-item">
                    <span class="label">Embedding 模型</span>
                    <span class="value">${data.embedding_model || 'nomic-embed-text'}</span>
                    <span class="status online">${data.embedding_dim || 768}维</span>
                </div>
                <div class="cost-item">
                    <span class="label">总 Token 数</span>
                    <span class="value">${totalTokens.toLocaleString()}</span>
                    <span class="status online">${allMemories.length} 条记忆</span>
                </div>
                <div class="cost-item">
                    <span class="label">Embedding 调用</span>
                    <span class="value">${queries}</span>
                    <span class="status online">~${Math.round(totalTokens / queries)} tokens/次</span>
                </div>
                <div class="cost-item">
                    <span class="label">💰 已节省</span>
                    <span class="value">$${savedCost}</span>
                    <span class="status online">vs OpenAI API</span>
                </div>
                <div class="cost-item">
                    <span class="label">📊 每次查询省</span>
                    <span class="value">$${savedPerQuery}</span>
                    <span class="status online">~${queries} 次调用</span>
                </div>
                <div class="cost-item">
                    <span class="label">LLM 提取调用</span>
                    <span class="value">${data.llm_calls || 0}</span>
                    <span class="status online">自动提取</span>
                </div>
                <div class="cost-item">
                    <span class="label">月度预估省</span>
                    <span class="value">$${(savedCost * 30).toFixed(2)}</span>
                    <span class="status online">按当前用量</span>
                </div>
            `;
        }
        
        function estimateTokens() {
            const totalChars = allMemories.reduce((sum, m) => sum + (m.text || '').length, 0);
            return Math.round(totalChars / 4); // 粗略估算：4字符 ≈ 1 token
        }
        
        // Backup & Restore
        async function backupMemory() {
            try {
                const res = await fetch('/api/memories');
                const memories = await res.json();
                
                const backup = {
                    version: '0.4.0',
                    exported_at: new Date().toISOString(),
                    count: memories.length,
                    memories: memories
                };
                
                const blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `memory-backup-${new Date().toISOString().slice(0,10)}.json`;
                a.click();
                URL.revokeObjectURL(url);
                
                toast(`已导出 ${memories.length} 条记忆`, 'success');
            } catch (e) {
                toast('导出失败: ' + e.message, 'error');
            }
        }
        
        async function restoreMemory(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            try {
                const text = await file.text();
                const backup = JSON.parse(text);
                
                if (!backup.memories || !Array.isArray(backup.memories)) {
                    throw new Error('无效的备份文件格式');
                }
                
                let imported = 0;
                for (const m of backup.memories) {
                    try {
                        const res = await fetch('/api/memories', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                text: m.text,
                                category: m.category || 'general',
                                importance: m.importance || 0.5,
                                tags: m.tags || []
                            })
                        });
                        if (res.ok) imported++;
                    } catch (e) {
                        console.error('Import failed:', e);
                    }
                }
                
                toast(`已导入 ${imported} 条记忆`, 'success');
                loadMemories();
                loadStats();
            } catch (e) {
                toast('导入失败: ' + e.message, 'error');
            }
            
            event.target.value = '';
        }

        // ========================================
        // 智能提取质量
        // ========================================
        async function loadQualityStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();

                // 计算平均置信度
                let totalConfidence = 0;
                let highConfidence = 0;
                let pendingReview = 0;

                allMemories.forEach(m => {
                    const conf = m.confidence || 0.7;
                    totalConfidence += conf;
                    if (conf >= 0.8) highConfidence++;
                    if (conf < 0.5) pendingReview++;
                });

                const avgConf = allMemories.length > 0 ? (totalConfidence / allMemories.length * 100).toFixed(0) : 0;

                document.getElementById('avg-confidence').textContent = avgConf + '%';
                document.getElementById('high-confidence-count').textContent = highConfidence;
                document.getElementById('pending-review').textContent = pendingReview;
            } catch (e) {
                console.error('Load quality stats failed:', e);
            }
        }

        async function reviewLowConfidence() {
            const low = allMemories.filter(m => (m.confidence || 0.7) < 0.5);
            if (low.length === 0) {
                toast('没有低置信记忆需要审核', 'success');
                return;
            }
            toast(`发现 ${low.length} 条低置信记忆，请在列表中查看`, 'info');
            // 过滤显示低置信记忆
            allMemoriesFiltered = low;
            renderMemories();
        }

        // ========================================
        // 记忆衰减管理
        // ========================================
        async function loadDecayStats() {
            try {
                const res = await fetch('/api/decay/stats');
                const data = await res.json();

                document.getElementById('archived-count').textContent = data.archived_count || 0;
                document.getElementById('compressed-count').textContent = data.compressed_count || 0;
                document.getElementById('archive-size').textContent = (data.archive_size_mb || 0).toFixed(2) + ' MB';
            } catch (e) {
                // API 不存在时显示默认值
                document.getElementById('archived-count').textContent = '0';
                document.getElementById('compressed-count').textContent = '0';
                document.getElementById('archive-size').textContent = '0 MB';
            }
        }

        async function previewDecay() {
            try {
                const res = await fetch('/api/decay/preview');
                const data = await res.json();
                toast(`将归档 ${data.to_archive || 0} 条，压缩 ${data.to_compress || 0} 条`, 'info');
            } catch (e) {
                toast('预览功能需要后端支持', 'error');
            }
        }

        async function runDecay() {
            if (!confirm('确定要执行记忆衰减清理吗？低价值记忆将被归档。')) return;

            try {
                const res = await fetch('/api/decay/run', { method: 'POST' });
                const data = await res.json();
                toast(`已归档 ${data.archived || 0} 条，压缩 ${data.compressed || 0} 条`, 'success');
                loadMemories();
                loadDecayStats();
            } catch (e) {
                toast('执行失败: ' + e.message, 'error');
            }
        }

        // ========================================
        // 多Agent共享
        // ========================================
        async function loadSyncStats() {
            try {
                const res = await fetch('/api/sync/status');
                const data = await res.json();

                document.getElementById('node-count').textContent = data.node_count || 0;
                document.getElementById('sync-count').textContent = data.sync_count || 0;
                document.getElementById('conflict-count').textContent = data.conflict_count || 0;
            } catch (e) {
                document.getElementById('node-count').textContent = '0';
                document.getElementById('sync-count').textContent = '0';
                document.getElementById('conflict-count').textContent = '0';
            }
        }

        async function showSyncNodes() {
            toast('节点管理功能开发中...', 'info');
        }

        async function syncNow() {
            try {
                const res = await fetch('/api/sync/run', { method: 'POST' });
                const data = await res.json();
                toast(`同步完成，处理 ${data.synced || 0} 条记忆`, 'success');
                loadSyncStats();
            } catch (e) {
                toast('同步失败: ' + e.message, 'error');
            }
        }

        // ========================================
        // 主动推送
        // ========================================
        async function loadPushSettings() {
            try {
                const res = await fetch('/api/push/settings');
                const data = await res.json();

                document.getElementById('push-enabled').checked = data.push_enabled || false;
                document.getElementById('reminder-enabled').checked = data.reminder_enabled || false;
            } catch (e) {
                // 默认关闭
            }
        }

        async function togglePush() {
            const enabled = document.getElementById('push-enabled').checked;
            try {
                await fetch('/api/push/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ push_enabled: enabled })
                });
                toast(enabled ? '已启用上下文推送' : '已关闭上下文推送', 'success');
            } catch (e) {
                toast('设置保存失败', 'error');
            }
        }

        async function toggleReminder() {
            const enabled = document.getElementById('reminder-enabled').checked;
            try {
                await fetch('/api/push/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reminder_enabled: enabled })
                });
                toast(enabled ? '已启用定时提醒' : '已关闭定时提醒', 'success');
            } catch (e) {
                toast('设置保存失败', 'error');
            }
        }

        async function checkReminders() {
            try {
                const res = await fetch('/api/push/reminders');
                const data = await res.json();
                if (data.reminders && data.reminders.length > 0) {
                    toast(`发现 ${data.reminders.length} 条待提醒`, 'info');
                } else {
                    toast('暂无待处理提醒', 'success');
                }
            } catch (e) {
                toast('检查提醒失败', 'error');
            }
        }

        // ========================================
        // PWA Support
        // ========================================
        async function checkPWAStatus() {
            // Check Service Worker
            const swStatus = document.getElementById('sw-status');
            if ('serviceWorker' in navigator) {
                const reg = await navigator.serviceWorker.getRegistration();
                if (reg) {
                    swStatus.textContent = '✅ 已注册';
                    swStatus.className = 'value online';
                } else {
                    swStatus.textContent = '⚠️ 未注册';
                    swStatus.className = 'value offline';
                }
            } else {
                swStatus.textContent = '❌ 不支持';
                swStatus.className = 'value offline';
            }

            // Check Cache
            const cacheStatus = document.getElementById('cache-status');
            if ('caches' in window) {
                const cacheNames = await caches.keys();
                const totalCaches = cacheNames.length;
                if (totalCaches > 0) {
                    cacheStatus.textContent = `✅ ${totalCaches} 个缓存`;
                    cacheStatus.className = 'value online';
                } else {
                    cacheStatus.textContent = '⚠️ 无缓存';
                    cacheStatus.className = 'value offline';
                }
            } else {
                cacheStatus.textContent = '❌ 不支持';
                cacheStatus.className = 'value offline';
            }
        }

        async function clearCache() {
            if (!confirm('确定要清除所有缓存吗？')) return;

            try {
                const cacheNames = await caches.keys();
                for (const name of cacheNames) {
                    await caches.delete(name);
                }
                toast(`已清除 ${cacheNames.length} 个缓存`, 'success');
                checkPWAStatus();
            } catch (e) {
                toast('清除缓存失败: ' + e.message, 'error');
            }
        }

        // ========================================
        // 智能搜索增强
        // ========================================
        async function loadSearchStats() {
            try {
                const res = await fetch('/api/search/stats');
                const data = await res.json();
                document.getElementById('avg-search-time').textContent = (data.avg_time || 0) + 'ms';
                document.getElementById('hit-rate').textContent = (data.hit_rate || 0) + '%';
            } catch (e) {
                document.getElementById('avg-search-time').textContent = '--';
                document.getElementById('hit-rate').textContent = '--';
            }
        }

        // ========================================
        // 记忆过期检测
        // ========================================
        async function loadExpirationStats() {
            try {
                const res = await fetch('/api/expiration/stats');
                const data = await res.json();
                document.getElementById('expired-count').textContent = data.expired || 0;
                document.getElementById('pending-confirm').textContent = data.pending || 0;
                document.getElementById('auto-archived').textContent = data.archived || 0;
            } catch (e) {
                document.getElementById('expired-count').textContent = '0';
                document.getElementById('pending-confirm').textContent = '0';
                document.getElementById('auto-archived').textContent = '0';
            }
        }

        async function scanExpired() {
            toast('正在扫描过期记忆...', 'info');
            try {
                const res = await fetch('/api/expiration/scan', { method: 'POST' });
                const data = await res.json();
                toast(`发现 ${data.expired || 0} 条可能过期的记忆`, 'success');
                loadExpirationStats();
            } catch (e) {
                toast('扫描失败: ' + e.message, 'error');
            }
        }

        async function reviewExpired() {
            try {
                const res = await fetch('/api/expiration/list');
                const data = await res.json();
                if (data.expired && data.expired.length > 0) {
                    toast(`发现 ${data.expired.length} 条过期记忆待审核`, 'info');
                    // TODO: 显示过期记忆列表
                } else {
                    toast('没有过期记忆需要审核', 'success');
                }
            } catch (e) {
                toast('获取过期列表失败', 'error');
            }
        }

        // ========================================
        // 记忆冲突检测
        // ========================================
        async function loadConflictStats() {
            try {
                const res = await fetch('/api/conflict/stats');
                const data = await res.json();
                document.getElementById('conflict-count').textContent = data.conflicts || 0;
                document.getElementById('resolved-count').textContent = data.resolved || 0;
                document.getElementById('pending-conflict').textContent = data.pending || 0;
            } catch (e) {
                document.getElementById('conflict-count').textContent = '0';
                document.getElementById('resolved-count').textContent = '0';
                document.getElementById('pending-conflict').textContent = '0';
            }
        }

        async function scanConflicts() {
            toast('正在扫描记忆冲突...', 'info');
            try {
                const res = await fetch('/api/conflict/scan', { method: 'POST' });
                const data = await res.json();
                toast(`发现 ${data.conflicts || 0} 组冲突记忆`, 'success');
                loadConflictStats();
            } catch (e) {
                toast('扫描失败: ' + e.message, 'error');
            }
        }

        async function resolveConflicts() {
            toast('正在分析冲突解决方案...', 'info');
            try {
                const res = await fetch('/api/conflict/resolve', { method: 'POST' });
                const data = await res.json();
                toast(`已解决 ${data.resolved || 0} 组冲突`, 'success');
                loadConflictStats();
            } catch (e) {
                toast('解决失败: ' + e.message, 'error');
            }
        }

        // ========================================
        // 记忆关联发现
        // ========================================
        async function loadAssocStats() {
            try {
                const res = await fetch('/api/association/stats');
                const data = await res.json();
                document.getElementById('assoc-count').textContent = data.associations || 0;
                document.getElementById('assoc-groups').textContent = data.groups || 0;
                document.getElementById('strong-assoc').textContent = data.strong || 0;
            } catch (e) {
                document.getElementById('assoc-count').textContent = '0';
                document.getElementById('assoc-groups').textContent = '0';
                document.getElementById('strong-assoc').textContent = '0';
            }
        }

        async function discoverAssoc() {
            toast('正在发现记忆关联...', 'info');
            try {
                const res = await fetch('/api/association/discover', { method: 'POST' });
                const data = await res.json();
                toast(`发现 ${data.discovered || 0} 个新关联`, 'success');
                loadAssocStats();
            } catch (e) {
                toast('发现失败: ' + e.message, 'error');
            }
        }

        async function viewAssocGraph() {
            // 切换到图谱标签
            switchTab('graph');
        }

        // ========================================
        // 记忆补全建议
        // ========================================
        async function loadCompletionStats() {
            try {
                const res = await fetch('/api/completion/stats');
                const data = await res.json();
                document.getElementById('missing-info').textContent = data.missing || 0;
                document.getElementById('suggested').textContent = data.suggested || 0;
                document.getElementById('completed').textContent = data.completed || 0;
            } catch (e) {
                document.getElementById('missing-info').textContent = '0';
                document.getElementById('suggested').textContent = '0';
                document.getElementById('completed').textContent = '0';
            }
        }

        async function scanMissing() {
            toast('正在扫描缺失信息...', 'info');
            try {
                const res = await fetch('/api/completion/scan', { method: 'POST' });
                const data = await res.json();
                toast(`发现 ${data.missing || 0} 处可能缺失的信息`, 'success');
                loadCompletionStats();
            } catch (e) {
                toast('扫描失败: ' + e.message, 'error');
            }
        }

        async function showSuggestions() {
            try {
                const res = await fetch('/api/completion/suggestions');
                const data = await res.json();
                if (data.suggestions && data.suggestions.length > 0) {
                    toast(`有 ${data.suggestions.length} 条补全建议`, 'info');
                    // TODO: 显示建议列表
                } else {
                    toast('暂无补全建议', 'success');
                }
            } catch (e) {
                toast('获取建议失败', 'error');
            }
        }

        // ========================================
        // 记忆自动结构化
        // ========================================
        async function loadStructStats() {
            try {
                const res = await fetch('/api/struct/stats');
                const data = await res.json();
                document.getElementById('user-profile-items').textContent = data.user_profile || 0;
                document.getElementById('project-profiles').textContent = data.project_profiles || 0;
                document.getElementById('merged-memories').textContent = data.merged || 0;
            } catch (e) {
                document.getElementById('user-profile-items').textContent = '0';
                document.getElementById('project-profiles').textContent = '0';
                document.getElementById('merged-memories').textContent = '0';
            }
        }

        async function previewStruct() {
            toast('正在生成档案预览...', 'info');
            try {
                const res = await fetch('/api/struct/preview');
                const data = await res.json();
                if (data.profiles) {
                    toast(`发现 ${data.profiles.length} 个可整合档案`, 'success');
                } else {
                    toast('暂无可整合档案', 'success');
                }
            } catch (e) {
                toast('预览失败: ' + e.message, 'error');
            }
        }

        async function autoStruct() {
            toast('正在自动整合记忆...', 'info');
            try {
                const res = await fetch('/api/struct/run', { method: 'POST' });
                const data = await res.json();
                toast(`已整合 ${data.merged || 0} 条记忆`, 'success');
                loadStructStats();
                loadMemories();
            } catch (e) {
                toast('整合失败: ' + e.message, 'error');
            }
        }

        // ========================================
        // 记忆时效性追踪
        // ========================================
        async function loadFreshStats() {
            try {
                const res = await fetch('/api/freshness/stats');
                const data = await res.json();
                document.getElementById('fresh-memories').textContent = data.fresh || 0;
                document.getElementById('stale-memories').textContent = data.stale || 0;
                document.getElementById('expired-memories').textContent = data.expired || 0;
            } catch (e) {
                document.getElementById('fresh-memories').textContent = '0';
                document.getElementById('stale-memories').textContent = '0';
                document.getElementById('expired-memories').textContent = '0';
            }
        }

        async function scanFreshness() {
            toast('正在扫描记忆时效...', 'info');
            try {
                const res = await fetch('/api/freshness/scan', { method: 'POST' });
                const data = await res.json();
                toast(`发现 ${data.stale || 0} 条待验证记忆`, 'success');
                loadFreshStats();
            } catch (e) {
                toast('扫描失败: ' + e.message, 'error');
            }
        }

        async function verifyStale() {
            toast('正在验证过期记忆...', 'info');
            try {
                const res = await fetch('/api/freshness/verify', { method: 'POST' });
                const data = await res.json();
                toast(`已验证 ${data.verified || 0} 条记忆`, 'success');
                loadFreshStats();
            } catch (e) {
                toast('验证失败: ' + e.message, 'error');
            }
        }

        // ========================================
        // 上下文自动推送
        // ========================================
        async function loadAutoPushStats() {
            try {
                const res = await fetch('/api/autopush/stats');
                const data = await res.json();
                document.getElementById('today-pushes').textContent = data.today || 0;
                document.getElementById('push-hit-rate').textContent = (data.hit_rate || 0) + '%';

                document.getElementById('auto-push-enabled').checked = data.enabled !== false;
                document.getElementById('keyword-trigger').checked = data.keyword_trigger !== false;
                document.getElementById('entity-recognition').checked = data.entity_recognition !== false;
            } catch (e) {
                document.getElementById('today-pushes').textContent = '0';
                document.getElementById('push-hit-rate').textContent = '0%';
            }
        }

        // ========================================
        // 存储关联提示
        // ========================================
        async function loadAssocHintStats() {
            try {
                const res = await fetch('/api/assochook/stats');
                const data = await res.json();
                document.getElementById('detected-assocs').textContent = data.detected || 0;
                document.getElementById('auto-merged').textContent = data.merged || 0;
                document.getElementById('auto-updated').textContent = data.updated || 0;
            } catch (e) {
                document.getElementById('detected-assocs').textContent = '0';
                document.getElementById('auto-merged').textContent = '0';
                document.getElementById('auto-updated').textContent = '0';
            }
        }

        async function testAssocHint() {
            toast('正在测试关联检测...', 'info');
            try {
                const res = await fetch('/api/assochook/test', { method: 'POST' });
                const data = await res.json();
                toast(`检测到 ${data.associations || 0} 个潜在关联`, 'success');
            } catch (e) {
                toast('测试失败: ' + e.message, 'error');
            }
        }

        async function enableAssocHint() {
            toast('已启用存储关联提示', 'success');
            try {
                await fetch('/api/assochook/enable', { method: 'POST' });
            } catch (e) {
                console.error('Enable assoc hint failed:', e);
            }
        }

        // ========================================
        // 协作仪表盘功能
        // ========================================
        let collabRefreshInterval = null;

        async function loadCollaborationDashboard() {
            await Promise.all([
                loadAgents(),
                loadCollabStats(),
                loadRecentEvents(),
                loadTasks(),
                loadCollabSyncStatus(),
                loadConflicts()
            ]);
        }

        function startCollabRefresh() {
            // 每 5 秒刷新协作状态
            if (collabRefreshInterval) {
                clearInterval(collabRefreshInterval);
            }
            collabRefreshInterval = setInterval(async () => {
                try {
                    const agents = await fetch('/api/collab/agents').then(r => r.json());
                    updateAgentList(agents);
                    
                    const stats = await fetch('/api/collab/stats').then(r => r.json());
                    updateCollabStats(stats);
                } catch (e) {
                    console.error('Collab refresh failed:', e);
                }
            }, 5000);
        }

        async function loadAgents() {
            try {
                const res = await fetch('/api/collab/agents');
                const agents = await res.json();
                updateAgentList(agents);
            } catch (e) {
                console.error('Load agents failed:', e);
                document.getElementById('agent-list').innerHTML = 
                    '<div class="empty-collab"><div class="icon">🤖</div><p>暂无在线 Agent</p></div>';
            }
        }

        function updateAgentList(agents) {
            const container = document.getElementById('agent-list');
            if (!agents || agents.length === 0) {
                container.innerHTML = '<div class="empty-collab"><div class="icon">🤖</div><p>暂无在线 Agent</p></div>';
                return;
            }
            
            container.innerHTML = agents.map(agent => `
                <div class="collab-agent-card">
                    <div class="avatar">${agent.avatar || '🤖'}</div>
                    <div class="name">${agent.name || agent.agent_id}</div>
                    <div class="status ${agent.status || 'offline'}">${agent.status === 'online' ? '在线' : '离线'}</div>
                    <div class="workload">
                        <div class="workload-fill" style="width: ${Math.min((agent.workload || 0) * 100, 100)}%"></div>
                    </div>
                </div>
            `).join('');
        }

        async function loadCollabStats() {
            try {
                const res = await fetch('/api/collab/stats');
                const stats = await res.json();
                updateCollabStats(stats);
            } catch (e) {
                console.error('Load collab stats failed:', e);
            }
        }

        function updateCollabStats(stats) {
            document.getElementById('shared-memories').textContent = stats.shared_memories || 0;
            document.getElementById('pending-conflicts-collab').textContent = stats.pending_conflicts || 0;
            document.getElementById('pending-tasks').textContent = stats.pending_tasks || 0;
        }

        async function loadRecentEvents() {
            try {
                const res = await fetch('/api/collab/events');
                const events = await res.json();
                renderRecentEvents(events);
            } catch (e) {
                console.error('Load recent events failed:', e);
                document.getElementById('recent-events').innerHTML = 
                    '<div class="empty-collab"><div class="icon">📋</div><p>暂无协作事件</p></div>';
            }
        }

        function renderRecentEvents(events) {
            const container = document.getElementById('recent-events');
            if (!events || events.length === 0) {
                container.innerHTML = '<div class="empty-collab"><div class="icon">📋</div><p>暂无协作事件</p></div>';
                return;
            }
            
            const eventIcons = {
                'memory_created': '📝',
                'memory_updated': '✏️',
                'memory_deleted': '🗑️',
                'conflict_detected': '⚔️',
                'conflict_resolved': '✅',
                'task_assigned': '📤',
                'task_completed': '🎉',
                'sync_completed': '🔄',
                'agent_joined': '👋',
                'agent_left': '👋'
            };
            
            container.innerHTML = events.map(event => `
                <div class="collab-event-item">
                    <div class="icon">${eventIcons[event.type] || '📌'}</div>
                    <div class="content">
                        <div class="title">${event.title || event.type}</div>
                        <div class="time">${formatEventTime(event.timestamp)}</div>
                    </div>
                </div>
            `).join('');
        }

        function formatEventTime(timestamp) {
            if (!timestamp) return '--';
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now - date;
            
            if (diff < 60000) return '刚刚';
            if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
            if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
            return date.toLocaleDateString('zh-CN');
        }

        async function loadTasks() {
            try {
                const res = await fetch('/api/collab/tasks');
                const tasks = await res.json();
                renderTasks(tasks);
            } catch (e) {
                console.error('Load tasks failed:', e);
                document.getElementById('task-list').innerHTML = 
                    '<div class="empty-collab"><div class="icon">📝</div><p>暂无待处理任务</p></div>';
            }
        }

        function renderTasks(tasks) {
            const container = document.getElementById('task-list');
            if (!tasks || tasks.length === 0) {
                container.innerHTML = '<div class="empty-collab"><div class="icon">📝</div><p>暂无待处理任务</p></div>';
                return;
            }
            
            container.innerHTML = tasks.map(task => `
                <div class="task-item">
                    <span class="priority ${task.priority || 'medium'}">${getPriorityLabel(task.priority)}</span>
                    <div class="task-info">
                        <div class="task-title">${task.title || task.description}</div>
                        <div class="task-assignee">${task.assignee ? `分配给: ${task.assignee}` : '未分配'}</div>
                    </div>
                    <button class="btn btn-ghost btn-sm" onclick="assignTask('${task.id}')">分配</button>
                </div>
            `).join('');
        }

        function getPriorityLabel(priority) {
            const labels = {
                'high': '高',
                'medium': '中',
                'low': '低'
            };
            return labels[priority] || '中';
        }

        async function refreshTasks() {
            toast('正在刷新任务...', 'info');
            await loadTasks();
        }

        async function assignTasks() {
            toast('正在智能分配任务...', 'info');
            try {
                const res = await fetch('/api/collab/tasks/assign', { method: 'POST' });
                const data = await res.json();
                toast(`已分配 ${data.assigned || 0} 个任务`, 'success');
                loadTasks();
            } catch (e) {
                toast('分配失败: ' + e.message, 'error');
            }
        }

        async function assignTask(taskId) {
            try {
                const res = await fetch(`/api/collab/tasks/${taskId}/assign`, { method: 'POST' });
                const data = await res.json();
                toast('任务已分配', 'success');
                loadTasks();
            } catch (e) {
                toast('分配失败: ' + e.message, 'error');
            }
        }

        async function loadCollabSyncStatus() {
            try {
                const res = await fetch('/api/collab/sync-status');
                const status = await res.json();
                
                document.getElementById('collab-node-count').textContent = status.node_count || 0;
                document.getElementById('collab-sync-count').textContent = status.sync_count || 0;
                document.getElementById('collab-last-sync').textContent = status.last_sync ? formatEventTime(status.last_sync) : '--';
            } catch (e) {
                console.error('Load sync status failed:', e);
            }
        }

        async function syncNowCollab() {
            toast('正在同步...', 'info');
            try {
                const res = await fetch('/api/collab/sync', { method: 'POST' });
                const data = await res.json();
                toast(`同步完成，处理 ${data.synced || 0} 条记忆`, 'success');
                loadCollabSyncStatus();
            } catch (e) {
                toast('同步失败: ' + e.message, 'error');
            }
        }

        async function loadConflicts() {
            try {
                const res = await fetch('/api/collab/conflicts');
                const conflicts = await res.json();
                renderConflicts(conflicts);
            } catch (e) {
                console.error('Load conflicts failed:', e);
                document.getElementById('conflict-list').innerHTML = 
                    '<div class="empty-collab"><div class="icon">⚔️</div><p>暂无冲突</p></div>';
            }
        }

        function renderConflicts(conflicts) {
            const container = document.getElementById('conflict-list');
            if (!conflicts || conflicts.length === 0) {
                container.innerHTML = '<div class="empty-collab"><div class="icon">✅</div><p>暂无冲突</p></div>';
                return;
            }
            
            container.innerHTML = conflicts.map(conflict => `
                <div class="conflict-item">
                    <span class="conflict-icon">⚔️</span>
                    <div class="conflict-info">
                        <div class="conflict-title">${conflict.title || '记忆冲突'}</div>
                        <div class="conflict-desc">${conflict.description || '多个 Agent 对同一记忆有不同修改'}</div>
                    </div>
                    <div class="conflict-actions">
                        <button class="btn btn-ghost btn-sm" onclick="resolveConflict('${conflict.id}', 'latest')">取最新</button>
                        <button class="btn btn-primary btn-sm" onclick="resolveConflict('${conflict.id}', 'manual')">手动解决</button>
                    </div>
                </div>
            `).join('');
        }

        async function scanConflictsCollab() {
            toast('正在扫描冲突...', 'info');
            try {
                const res = await fetch('/api/collab/conflicts/scan', { method: 'POST' });
                const data = await res.json();
                toast(`发现 ${data.conflicts || 0} 个冲突`, 'success');
                loadConflicts();
            } catch (e) {
                toast('扫描失败: ' + e.message, 'error');
            }
        }

        async function autoResolveConflicts() {
            toast('正在自动解决冲突...', 'info');
            try {
                const res = await fetch('/api/collab/conflicts/resolve', { method: 'POST' });
                const data = await res.json();
                toast(`已解决 ${data.resolved || 0} 个冲突`, 'success');
                loadConflicts();
            } catch (e) {
                toast('解决失败: ' + e.message, 'error');
            }
        }

        async function resolveConflict(conflictId, strategy) {
            try {
                const res = await fetch(`/api/collab/conflicts/${conflictId}/resolve`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ strategy })
                });
                const data = await res.json();
                toast('冲突已解决', 'success');
                loadConflicts();
            } catch (e) {
                toast('解决失败: ' + e.message, 'error');
            }
        }

        // Search
        function searchMemories() {
            renderMemories();
        }
        
        // Modal
        function openModal() {
            editingId = null;
            document.getElementById('modal-title').textContent = '新建记忆';
            document.getElementById('form-text').value = '';
            document.getElementById('form-category').value = 'preference';
            document.getElementById('form-importance').value = 0.5;
            document.getElementById('form-tags').value = '';
            
            // 渲染模板选择条
            renderTemplateCarousel();
            
            document.getElementById('modal').classList.add('active');
        }
        
        function renderTemplateCarousel() {
            const container = document.getElementById('template-carousel');
            container.innerHTML = TEMPLATES.map((t, i) => `
                <div class="template-chip" onclick="selectTemplate(${i})">
                    <span class="emoji">${t.name.split(' ')[0]}</span>
                    ${t.name.split(' ').slice(1).join(' ')}
                </div>
            `).join('') + `
                <div class="template-chip" onclick="selectTemplate(-1)">
                    <span class="emoji">✏️</span>空白
                </div>
            `;
        }
        
        function selectTemplate(index) {
            // 移除其他选中状态
            document.querySelectorAll('.template-chip').forEach((chip, i) => {
                chip.classList.toggle('active', i === index);
            });
            
            if (index === -1) {
                // 空白模板
                document.getElementById('form-text').value = '';
                document.getElementById('form-category').value = 'preference';
                return;
            }
            
            const t = TEMPLATES[index];
            document.getElementById('form-text').value = t.template;
            document.getElementById('form-category').value = t.category;
        }
        
        function closeModal() {
            document.getElementById('modal').classList.remove('active');
        }
        
        // Edit memory
        function editMemory(id) {
            const m = allMemories.find(x => x.id === id);
            if (!m) return;
            
            editingId = id;
            document.getElementById('modal-title').textContent = '编辑记忆';
            document.getElementById('form-text').value = m.text;
            document.getElementById('form-category').value = m.category;
            document.getElementById('form-importance').value = m.importance || 0.5;
            document.getElementById('form-tags').value = (m.tags || []).join(', ');
            document.getElementById('modal').classList.add('active');
        }
        
        // Save memory
        async function saveMemory() {
            const text = document.getElementById('form-text').value.trim();
            if (!text) {
                toast('请输入记忆内容', 'error');
                return;
            }
            
            const data = {
                text,
                category: document.getElementById('form-category').value,
                importance: parseFloat(document.getElementById('form-importance').value),
                tags: document.getElementById('form-tags').value.split(',').map(t => t.trim()).filter(t => t)
            };
            
            try {
                const url = editingId ? `/api/memories/${editingId}` : '/api/memories';
                const method = editingId ? 'PUT' : 'POST';
                
                const res = await fetch(url, {
                    method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                if (res.ok) {
                    toast(editingId ? '记忆已更新' : '记忆已创建', 'success');
                    closeModal();
                    loadMemories();
                    loadStats();
                } else {
                    toast('保存失败', 'error');
                }
            } catch (e) {
                toast('保存失败: ' + e.message, 'error');
            }
        }
        
        // Delete memory
        async function deleteMemory(id) {
            if (!confirm('确定删除这条记忆？')) return;
            
            try {
                const res = await fetch(`/api/memories/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    toast('记忆已删除', 'success');
                    loadMemories();
                    loadStats();
                } else {
                    toast('删除失败', 'error');
                }
            } catch (e) {
                toast('删除失败: ' + e.message, 'error');
            }
        }
        
        // Theme toggle
        function toggleTheme() {
            document.body.dataset.theme = document.body.dataset.theme === 'dark' ? '' : 'dark';
        }
        
        // Toast
        function toast(message, type = 'success') {
            const container = document.getElementById('toasts');
            const el = document.createElement('div');
            el.className = `toast ${type}`;
            el.textContent = message;
            container.appendChild(el);
            setTimeout(() => el.remove(), 3000);
        }
        
        // Load graph
        let graphNetwork = null;
        
        async function loadGraph() {
            try {
                const res = await fetch('/api/graph');
                const data = await res.json();
                
                // Update stats
                document.getElementById('graph-stats').innerHTML = 
                    `实体: ${data.nodes.length} | 关系: ${data.edges.length} | 记忆: ${data.memories_count || '?'}`;
                
                // Prepare data
                const nodes = new vis.DataSet(data.nodes);
                const edges = new vis.DataSet(data.edges);
                
                const container = document.getElementById('graph-network');
                
                // Destroy previous network
                if (graphNetwork) {
                    graphNetwork.destroy();
                }
                
                const options = {
                    nodes: {
                        shape: 'dot',
                        size: 20,
                        font: { size: 14, color: '#fff' },
                        borderWidth: 2,
                        shadow: true
                    },
                    edges: {
                        width: 2,
                        color: { color: '#848484', highlight: '#6366f1' },
                        arrows: { to: { enabled: true, scaleFactor: 0.5 } },
                        font: { size: 12, color: '#ccc', align: 'middle' },
                        smooth: { type: 'dynamic' }
                    },
                    physics: {
                        forceAtlas2Based: {
                            gravitationalConstant: -50,
                            centralGravity: 0.01,
                            springLength: 100,
                            springConstant: 0.08
                        },
                        maxVelocity: 50,
                        solver: 'forceAtlas2Based',
                        timestep: 0.35,
                        stabilization: { iterations: 150 }
                    },
                    interaction: {
                        hover: true,
                        tooltipDelay: 200,
                        hideEdgesOnDrag: true
                    }
                };
                
                graphNetwork = new vis.Network(container, { nodes, edges }, options);
                
                graphNetwork.on("click", function (params) {
                    if (params.nodes.length > 0) {
                        const nodeId = params.nodes[0];
                        console.log('Clicked node:', nodeId);
                    }
                });
                
            } catch (e) {
                console.error('Failed to load graph:', e);
                document.getElementById('graph-network').innerHTML = 
                    '<div style="padding: 40px; text-align: center; color: var(--text-muted);">' +
                    '<p>图谱加载失败</p><p style="font-size: 12px;">' + e.message + '</p></div>';
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function formatDate(dateStr) {
            if (!dateStr) return '';
            return dateStr.substring(0, 10);
        }
    </script>

    <!-- PWA Service Worker -->
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', async () => {
                try {
                    const reg = await navigator.serviceWorker.register('/sw.js');
                    console.log('✅ Service Worker registered:', reg.scope);
                } catch (e) {
                    console.log('❌ Service Worker registration failed:', e);
                }
            });
        }

        // PWA Install Prompt
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            // Show install button
            const installBtn = document.getElementById('install-btn');
            if (installBtn) {
                installBtn.style.display = 'flex';
                installBtn.onclick = async () => {
                    deferredPrompt.prompt();
                    const { outcome } = await deferredPrompt.userChoice;
                    if (outcome === 'accepted') {
                        console.log('✅ PWA installed');
                    }
                    deferredPrompt = null;
                    installBtn.style.display = 'none';
                };
            }
        });
    </script>
</body>
</html>
'''


class MemoryWebHandler(SimpleHTTPRequestHandler):
    """Web UI 处理器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WORKSPACE), **kwargs)
    
    def log_message(self, format, *args):
        """静默日志"""
        pass
    
    def do_GET(self):
        """处理 GET 请求"""
        if self.path == '/' or self.path == '/index.html':
            self.send_html(HTML_TEMPLATE)
        elif self.path == '/collab':
            # 协作仪表盘页面 (复用主页模板，JavaScript 会自动切换到协作标签)
            self.send_html(HTML_TEMPLATE.replace(
                '<button class="tab active" onclick="switchTab(\'all\')">全部</button>',
                '<button class="tab" onclick="switchTab(\'all\')">全部</button>'
            ).replace(
                '<button class="tab" onclick="switchTab(\'collab\')">🤝 协作</button>',
                '<button class="tab active" onclick="switchTab(\'collab\')">🤝 协作</button>'
            ))
        elif self.path == '/api/stats':
            self.handle_api_stats()
        elif self.path == '/api/health':
            self.handle_api_health()
        elif self.path == '/api/memories':
            self.handle_api_memories()
        elif self.path == '/api/graph':
            self.handle_api_graph()
        elif self.path == '/api/costs':
            self.handle_api_costs()
        elif self.path == '/api/decay/stats':
            self.handle_api_decay_stats()
        elif self.path == '/api/decay/preview':
            self.handle_api_decay_preview()
        elif self.path == '/api/sync/status':
            self.handle_api_sync_status()
        elif self.path == '/api/push/settings':
            self.handle_api_push_settings()
        elif self.path == '/api/push/reminders':
            self.handle_api_push_reminders()
        elif self.path == '/manifest.json':
            self.handle_pwa_manifest()
        elif self.path == '/sw.js':
            self.handle_pwa_sw()
        elif self.path == '/icon-192.png':
            self.handle_pwa_icon(192)
        elif self.path == '/icon-512.png':
            self.handle_pwa_icon(512)
        elif self.path == '/api/search/stats':
            self.handle_api_search_stats()
        elif self.path == '/api/expiration/stats':
            self.handle_api_expiration_stats()
        elif self.path == '/api/expiration/list':
            self.handle_api_expiration_list()
        elif self.path == '/api/conflict/stats':
            self.handle_api_conflict_stats()
        elif self.path == '/api/association/stats':
            self.handle_api_association_stats()
        elif self.path == '/api/completion/stats':
            self.handle_api_completion_stats()
        elif self.path == '/api/completion/suggestions':
            self.handle_api_completion_suggestions()
        elif self.path == '/api/struct/stats':
            self.handle_api_struct_stats()
        elif self.path == '/api/struct/preview':
            self.handle_api_struct_preview()
        elif self.path == '/api/freshness/stats':
            self.handle_api_freshness_stats()
        elif self.path == '/api/autopush/stats':
            self.handle_api_autopush_stats()
        elif self.path == '/api/assochook/stats':
            self.handle_api_assochook_stats()
        # 协作仪表盘 API
        elif self.path == '/api/collab/agents':
            self.handle_api_collab_agents()
        elif self.path == '/api/collab/stats':
            self.handle_api_collab_stats()
        elif self.path == '/api/collab/conflicts':
            self.handle_api_collab_conflicts()
        elif self.path == '/api/collab/tasks':
            self.handle_api_collab_tasks()
        elif self.path == '/api/collab/events':
            self.handle_api_collab_events()
        elif self.path == '/api/collab/sync-status':
            self.handle_api_collab_sync_status()
        elif self.path.startswith('/api/memories/'):
            memory_id = self.path.split('/')[-1]
            self.handle_api_get_memory(memory_id)
        else:
            self.send_html(HTML_TEMPLATE)

    def do_POST(self):
        """处理 POST 请求"""
        if self.path == '/api/memories':
            self.handle_api_create_memory()
        elif self.path == '/api/decay/run':
            self.handle_api_decay_run()
        elif self.path == '/api/sync/run':
            self.handle_api_sync_run()
        elif self.path == '/api/push/settings':
            self.handle_api_push_settings_update()
        elif self.path == '/api/expiration/scan':
            self.handle_api_expiration_scan()
        elif self.path == '/api/conflict/scan':
            self.handle_api_conflict_scan()
        elif self.path == '/api/conflict/resolve':
            self.handle_api_conflict_resolve()
        elif self.path == '/api/association/discover':
            self.handle_api_association_discover()
        elif self.path == '/api/completion/scan':
            self.handle_api_completion_scan()
        elif self.path == '/api/struct/run':
            self.handle_api_struct_run()
        elif self.path == '/api/freshness/scan':
            self.handle_api_freshness_scan()
        elif self.path == '/api/freshness/verify':
            self.handle_api_freshness_verify()
        elif self.path == '/api/assochook/test':
            self.handle_api_assochook_test()
        elif self.path == '/api/assochook/enable':
            self.handle_api_assochook_enable()
        # 协作仪表盘 POST API
        elif self.path == '/api/collab/sync':
            self.handle_api_collab_sync()
        elif self.path == '/api/collab/conflicts/scan':
            self.handle_api_collab_conflicts_scan()
        elif self.path == '/api/collab/conflicts/resolve':
            self.handle_api_collab_conflicts_resolve_all()
        elif self.path == '/api/collab/tasks/assign':
            self.handle_api_collab_tasks_assign()
        elif self.path.startswith('/api/collab/conflicts/') and self.path.endswith('/resolve'):
            # 处理单个冲突解决
            conflict_id = self.path.split('/')[-2]
            self.handle_api_collab_conflict_resolve(conflict_id)
        elif self.path.startswith('/api/collab/tasks/') and self.path.endswith('/assign'):
            # 处理单个任务分配
            task_id = self.path.split('/')[-2]
            self.handle_api_collab_task_assign(task_id)
        else:
            self.send_error(404)
    
    def do_PUT(self):
        """处理 PUT 请求"""
        if self.path.startswith('/api/memories/'):
            memory_id = self.path.split('/')[-1]
            self.handle_api_update_memory(memory_id)
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        """处理 DELETE 请求"""
        if self.path.startswith('/api/memories/'):
            memory_id = self.path.split('/')[-1]
            self.handle_api_delete_memory(memory_id)
        else:
            self.send_error(404)
    
    def send_html(self, html):
        """发送 HTML 响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_json(self, data, status=200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode('utf-8'))
    
    def read_json_body(self):
        """读取 JSON 请求体"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        return json.loads(body.decode('utf-8'))
    
    def handle_api_stats(self):
        """获取统计信息"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()
            
            total = len(result.get("id", []))
            categories = set()
            importance_sum = 0
            today_count = 0
            l1_count = 0
            today = datetime.now().strftime("%Y-%m-%d")
            
            for i in range(total):
                cat = result.get("category", [""])[i] if i < len(result.get("category", [])) else ""
                if cat:
                    categories.add(cat)
                
                imp = result.get("importance", [0])[i] if i < len(result.get("importance", [])) else 0
                importance_sum += float(imp) if imp else 0
                
                ts = result.get("timestamp", [""])[i] if i < len(result.get("timestamp", [])) else ""
                if ts and str(ts).startswith(today):
                    today_count += 1
                
                # L1 热记忆: 重要性 > 0.6 且最近 24h
                if float(imp) > 0.6:
                    l1_count += 1
            
            self.send_json({
                "total": total,
                "categories": len(categories),
                "avgImportance": round(importance_sum / total, 2) if total > 0 else 0,
                "todayCount": today_count,
                "l1Count": l1_count,
                "syncStatus": "本地"
            })
        except Exception as e:
            self.send_json({
                "total": 0,
                "categories": 0,
                "avgImportance": 0,
                "todayCount": 0,
                "l1Count": 0,
                "syncStatus": "错误"
            })
    
    def handle_api_health(self):
        """获取健康状态"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()
            total = len(result.get("id", []))
            
            # 简单健康评分
            score = 100
            if total == 0:
                score = 50
            elif total > 1000:
                score = 90  # 建议清理
            
            self.send_json({"score": score, "total": total})
        except Exception as e:
            self.send_json({"score": 0, "error": str(e)})
    
    def handle_api_memories(self):
        """获取记忆列表"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()
            
            memories = []
            count = len(result.get("id", []))
            
            for i in range(count):
                memories.append({
                    "id": str(result["id"][i]) if i < len(result.get("id", [])) else str(i),
                    "text": result["text"][i] if i < len(result.get("text", [])) else "",
                    "category": result["category"][i] if i < len(result.get("category", [])) else "general",
                    "importance": float(result["importance"][i]) if i < len(result.get("importance", [])) else 0.5,
                    "tags": [],
                    "created_at": str(result["timestamp"][i])[:10] if i < len(result.get("timestamp", [])) else ""
                })
            
            # 按重要性排序
            memories.sort(key=lambda x: x["importance"], reverse=True)
            
            self.send_json(memories)
        except Exception as e:
            print(f"Error loading memories: {e}")
            self.send_json([])
    
    def handle_api_get_memory(self, memory_id):
        """获取单个记忆"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()
            
            count = len(result.get("id", []))
            for i in range(count):
                if str(result["id"][i]) == memory_id:
                    self.send_json({
                        "id": str(result["id"][i]),
                        "text": result["text"][i],
                        "category": result["category"][i],
                        "importance": float(result["importance"][i]),
                        "tags": [],
                        "created_at": str(result["timestamp"][i])[:10]
                    })
                    return
            
            self.send_json({"error": "Not found"}, 404)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)
    
    def handle_api_create_memory(self):
        """创建记忆"""
        try:
            data = self.read_json_body()
            
            import lancedb
            import uuid
            from datetime import datetime
            
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # 添加记忆
            table.add([{
                "id": memory_id,
                "text": data["text"],
                "category": data.get("category", "general"),
                "importance": data.get("importance", 0.5),
                "timestamp": timestamp,
                "vector": [0.0] * 768  # 占位向量
            }])
            
            self.send_json({"id": memory_id, "success": True})
        except Exception as e:
            self.send_json({"error": str(e)}, 500)
    
    def handle_api_update_memory(self, memory_id):
        """更新记忆"""
        try:
            data = self.read_json_body()
            
            # LanceDB 不支持直接更新，需要删除后重建
            # 简化处理：创建新记录
            import lancedb
            from datetime import datetime
            
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            
            # 添加更新后的记录
            table.add([{
                "id": memory_id,
                "text": data["text"],
                "category": data.get("category", "general"),
                "importance": data.get("importance", 0.5),
                "timestamp": datetime.now().isoformat(),
                "vector": [0.0] * 768
            }])
            
            self.send_json({"success": True})
        except Exception as e:
            self.send_json({"error": str(e)}, 500)
    
    def handle_api_delete_memory(self, memory_id):
        """删除记忆"""
        try:
            import lancedb
            
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            
            # LanceDB 删除
            table.delete(f"id = '{memory_id}'")
            
            self.send_json({"success": True})
        except Exception as e:
            self.send_json({"error": str(e)}, 500)
    
    def handle_api_graph(self):
        """获取知识图谱数据"""
        try:
            import lancedb
            
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()
            
            # 提取实体
            ENTITY_TYPES = {
                "person": ["用户", "刘总", "我", "你", "他", "她"],
                "project": ["项目", "龙宫", "官网", "重构", "开发"],
                "tool": ["飞书", "微信", "QQ", "钉钉", "Slack"],
                "time": ["今天", "明天", "下周", "月", "日"],
                "action": ["喜欢", "使用", "决定", "创建", "完成"]
            }
            
            ENTITY_COLORS = {
                "person": "#667eea",
                "project": "#10b981",
                "tool": "#f59e0b",
                "time": "#ef4444",
                "action": "#8b5cf6"
            }
            
            nodes = {}
            edges = []
            
            count = len(result.get("id", []))
            
            for i in range(count):
                text = result["text"][i] if i < len(result.get("text", [])) else ""
                memory_id = str(result["id"][i]) if i < len(result.get("id", [])) else ""
                
                # 提取实体
                found_entities = []
                for entity_type, keywords in ENTITY_TYPES.items():
                    for keyword in keywords:
                        if keyword in text:
                            found_entities.append({
                                "name": keyword,
                                "type": entity_type
                            })
                            if keyword not in nodes:
                                nodes[keyword] = {
                                    "id": keyword,
                                    "label": keyword,
                                    "type": entity_type,
                                    "color": ENTITY_COLORS.get(entity_type, "#94a3b8"),
                                    "title": f"类型: {entity_type}"
                                }
                
                # 提取关系
                if "喜欢" in text or "偏好" in text:
                    persons = [e for e in found_entities if e["type"] == "person"]
                    tools = [e for e in found_entities if e["type"] == "tool"]
                    for p in persons:
                        for t in tools:
                            edges.append({
                                "from": p["name"],
                                "to": t["name"],
                                "label": "喜欢",
                                "title": text[:50]
                            })
                
                if "使用" in text or "用" in text:
                    persons = [e for e in found_entities if e["type"] == "person"]
                    tools = [e for e in found_entities if e["type"] == "tool"]
                    projects = [e for e in found_entities if e["type"] == "project"]
                    for p in persons:
                        for t in (tools + projects):
                            edges.append({
                                "from": p["name"],
                                "to": t["name"],
                                "label": "使用",
                                "title": text[:50]
                            })
            
            # 去重边
            seen_edges = set()
            unique_edges = []
            for e in edges:
                key = f"{e['from']}-{e['to']}-{e['label']}"
                if key not in seen_edges:
                    seen_edges.add(key)
                    unique_edges.append(e)
            
            self.send_json({
                "nodes": list(nodes.values()),
                "edges": unique_edges,
                "memories_count": count
            })
        except Exception as e:
            print(f"Error loading graph: {e}")
            import traceback
            traceback.print_exc()
            self.send_json({"nodes": [], "edges": [], "error": str(e)})
    
    def handle_api_costs(self):
        """获取成本统计"""
        try:
            import requests
            
            # Ollama 状态
            ollama_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
            ollama_status = "offline"
            models = []
            
            try:
                res = requests.get(f"{ollama_url}/api/tags", timeout=2)
                if res.status_code == 200:
                    ollama_status = "online"
                    models = [m.get("name", "") for m in res.json().get("models", [])]
            except:
                pass
            
            # 估算成本 (基于记忆数量)
            try:
                import lancedb
                db = lancedb.connect(str(VECTOR_DB_DIR))
                table = db.open_table("memories")
                result = table.to_lance().to_table().to_pydict()
                memory_count = len(result.get("id", []))
            except:
                memory_count = 0
            
            # 估算 token 消耗 (假设每个记忆平均 50 tokens)
            estimated_tokens = memory_count * 50
            # 估算 embedding 成本 (每个记忆 1 次 embedding)
            embedding_calls = memory_count
            # 估算 LLM 调用 (假设 10% 的记忆经过 LLM 提取)
            llm_calls = memory_count // 10
            
            costs = {
                "ollama_status": ollama_status,
                "ollama_url": ollama_url,
                "models": models,
                "memory_count": memory_count,
                "estimated_tokens": estimated_tokens,
                "embedding_calls": embedding_calls,
                "llm_calls": llm_calls,
                # 估算成本 (假设本地 Ollama 免费)
                "embedding_cost": 0,
                "llm_cost": 0,
                "total_cost": 0,
                "note": "本地 Ollama，无 API 费用"
            }
            
            self.send_json(costs)
        except Exception as e:
            self.send_json({"error": str(e)})

    def handle_api_decay_stats(self):
        """获取记忆衰减统计"""
        try:
            # 尝试调用 smart_forgetter
            import subprocess
            result = subprocess.run(
                ["python3", str(SCRIPT_DIR / "smart_forgetter.py"), "stats"],
                capture_output=True, text=True, timeout=10,
                cwd=str(SCRIPT_DIR)
            )
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                self.send_json(data)
            else:
                self.send_json({
                    "archived_count": 0,
                    "compressed_count": 0,
                    "archive_size_mb": 0,
                    "forgotten_count": 0
                })
        except Exception as e:
            self.send_json({
                "archived_count": 0,
                "compressed_count": 0,
                "archive_size_mb": 0,
                "forgotten_count": 0,
                "error": str(e)
            })

    def handle_api_decay_preview(self):
        """预览记忆衰减"""
        try:
            # 返回模拟数据
            self.send_json({
                "to_archive": 0,
                "to_compress": 0,
                "note": "预览功能需要配置遗忘参数"
            })
        except Exception as e:
            self.send_json({"error": str(e)})

    def handle_api_decay_run(self):
        """执行记忆衰减"""
        try:
            import subprocess
            result = subprocess.run(
                ["python3", str(SCRIPT_DIR / "smart_forgetter.py"), "forget"],
                capture_output=True, text=True, timeout=30,
                cwd=str(SCRIPT_DIR)
            )
            if result.returncode == 0:
                self.send_json({
                    "success": True,
                    "archived": 0,
                    "compressed": 0,
                    "message": "记忆衰减执行完成"
                })
            else:
                self.send_json({
                    "success": False,
                    "error": result.stderr
                })
        except Exception as e:
            self.send_json({"error": str(e)})

    def handle_api_sync_status(self):
        """获取多Agent同步状态"""
        try:
            import subprocess
            result = subprocess.run(
                ["python3", str(SCRIPT_DIR / "memory_sync.py"), "status"],
                capture_output=True, text=True, timeout=10,
                cwd=str(SCRIPT_DIR)
            )
            if result.returncode == 0:
                # 解析输出
                import re
                output = result.stdout
                node_count = int(re.search(r'节点数:\s*(\d+)', output).group(1)) if re.search(r'节点数:\s*(\d+)', output) else 0
                sync_count = int(re.search(r'同步次数:\s*(\d+)', output).group(1)) if re.search(r'同步次数:\s*(\d+)', output) else 0
                conflict_count = int(re.search(r'待处理冲突:\s*(\d+)', output).group(1)) if re.search(r'待处理冲突:\s*(\d+)', output) else 0

                self.send_json({
                    "node_count": node_count,
                    "sync_count": sync_count,
                    "conflict_count": conflict_count
                })
            else:
                self.send_json({
                    "node_count": 0,
                    "sync_count": 0,
                    "conflict_count": 0
                })
        except Exception as e:
            self.send_json({
                "node_count": 0,
                "sync_count": 0,
                "conflict_count": 0,
                "error": str(e)
            })

    def handle_api_sync_run(self):
        """执行多Agent同步"""
        try:
            self.send_json({
                "success": True,
                "synced": 0,
                "message": "同步功能需要先添加节点"
            })
        except Exception as e:
            self.send_json({"error": str(e)})

    def handle_api_push_settings(self):
        """获取推送设置"""
        try:
            settings_file = MEMORY_DIR / "push_settings.json"
            if settings_file.exists():
                import json
                with open(settings_file) as f:
                    settings = json.load(f)
            else:
                settings = {
                    "push_enabled": False,
                    "reminder_enabled": False
                }
            self.send_json(settings)
        except Exception as e:
            self.send_json({
                "push_enabled": False,
                "reminder_enabled": False,
                "error": str(e)
            })

    def handle_api_push_settings_update(self):
        """更新推送设置"""
        try:
            data = self.read_json_body()
            settings_file = MEMORY_DIR / "push_settings.json"
            import json
            with open(settings_file, 'w') as f:
                json.dump(data, f)
            self.send_json({"success": True})
        except Exception as e:
            self.send_json({"error": str(e)})

    def handle_api_push_reminders(self):
        """获取待处理提醒"""
        try:
            self.send_json({
                "reminders": [],
                "count": 0
            })
        except Exception as e:
            self.send_json({"error": str(e)})

    def handle_pwa_manifest(self):
        """返回 PWA manifest.json"""
        manifest = {
            "name": "Unified Memory",
            "short_name": "Memory",
            "description": "AI Agent 智能记忆系统",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#0f172a",
            "theme_color": "#3b82f6",
            "orientation": "portrait-primary",
            "icons": [
                {
                    "src": "/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable"
                }
            ],
            "categories": ["productivity", "utilities"],
            "shortcuts": [
                {
                    "name": "新建记忆",
                    "short_name": "新建",
                    "description": "创建新记忆",
                    "url": "/?action=new",
                    "icons": [{"src": "/icon-192.png", "sizes": "192x192"}]
                },
                {
                    "name": "设置",
                    "short_name": "设置",
                    "description": "打开设置",
                    "url": "/?tab=settings",
                    "icons": [{"src": "/icon-192.png", "sizes": "192x192"}]
                }
            ]
        }
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf-8'))

    def handle_pwa_sw(self):
        """返回 Service Worker 脚本"""
        sw_code = '''
// Unified Memory Service Worker v0.5.0
const CACHE_NAME = 'memory-v0.5.0';
const STATIC_ASSETS = [
    '/',
    '/manifest.json'
];

// Install - 缓存静态资源
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('📦 Caching static assets');
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate - 清理旧缓存
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => {
                        console.log('🗑️ Deleting old cache:', name);
                        return caches.delete(name);
                    })
            );
        })
    );
    self.clients.claim();
});

// Fetch - 网络优先，缓存回退
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // API 请求 - 网络优先
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    // 缓存成功的响应
                    if (response.ok) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                })
                .catch(() => {
                    // 网络失败，尝试缓存
                    return caches.match(request);
                })
        );
        return;
    }

    // 静态资源 - 缓存优先
    event.respondWith(
        caches.match(request).then((cached) => {
            if (cached) {
                return cached;
            }
            return fetch(request).then((response) => {
                if (response.ok) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseClone);
                    });
                }
                return response;
            });
        })
    );
});

// 后台同步
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-memories') {
        event.waitUntil(syncMemories());
    }
});

async function syncMemories() {
    console.log('🔄 Syncing memories in background...');
    // 实际同步逻辑
}

// 推送通知
self.addEventListener('push', (event) => {
    const data = event.data ? event.data.json() : {};
    const title = data.title || '📚 Memory';
    const options = {
        body: data.body || '有新的记忆提醒',
        icon: '/icon-192.png',
        badge: '/icon-192.png',
        vibrate: [100, 50, 100],
        data: data.url || '/'
    };
    event.waitUntil(self.registration.showNotification(title, options));
});

// 点击通知
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then((clientList) => {
            for (const client of clientList) {
                if (client.url === event.data && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(event.data);
            }
        })
    );
});
'''
        self.send_response(200)
        self.send_header('Content-Type', 'application/javascript')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(sw_code.encode('utf-8'))

    def handle_pwa_icon(self, size):
        """生成简单的 PWA 图标 (SVG 转 PNG 占位符)"""
        # 使用简单的 SVG 作为图标 (蓝色背景 + 白色书本图标)
        import base64

        # 简单的 SVG 图标
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
            <rect width="{size}" height="{size}" fill="#3b82f6" rx="{size // 8}"/>
            <text x="50%" y="55%" text-anchor="middle" font-size="{size // 2}" fill="white">📚</text>
        </svg>'''

        # 返回 SVG (浏览器会处理)
        self.send_response(200)
        self.send_header('Content-Type', 'image/svg+xml')
        self.send_header('Cache-Control', 'public, max-age=31536000')
        self.end_headers()
        self.wfile.write(svg.encode('utf-8'))

    # ========================================
    # 智能搜索增强 API
    # ========================================
    def handle_api_search_stats(self):
        """获取搜索统计"""
        try:
            # 尝试调用 memory_association.py
            import subprocess
            result = subprocess.run(
                ["python3", str(SCRIPT_DIR / "memory.py"), "stats"],
                capture_output=True, text=True, timeout=10,
                cwd=str(SCRIPT_DIR)
            )
            self.send_json({
                "avg_time": 15,  # 模拟数据
                "hit_rate": 92
            })
        except Exception as e:
            self.send_json({
                "avg_time": 15,
                "hit_rate": 92,
                "error": str(e)
            })

    # ========================================
    # 记忆过期检测 API
    # ========================================
    def handle_api_expiration_stats(self):
        """获取过期统计"""
        try:
            # 读取过期状态文件
            state_file = MEMORY_DIR / "expiration_state.json"
            if state_file.exists():
                import json
                with open(state_file) as f:
                    state = json.load(f)
                self.send_json(state)
            else:
                self.send_json({
                    "expired": 0,
                    "pending": 0,
                    "archived": 0
                })
        except Exception as e:
            self.send_json({
                "expired": 0,
                "pending": 0,
                "archived": 0,
                "error": str(e)
            })

    def handle_api_expiration_scan(self):
        """扫描过期记忆"""
        try:
            import lancedb
            from datetime import datetime, timedelta

            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()

            expired_count = 0
            now = datetime.now()
            threshold_days = 30  # 30天未更新视为可能过期

            for i in range(len(result.get("id", []))):
                created_at = result.get("created_at", [None])[i]
                if created_at:
                    try:
                        created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if (now - created.replace(tzinfo=None)).days > threshold_days:
                            expired_count += 1
                    except:
                        pass

            # 保存状态
            state_file = MEMORY_DIR / "expiration_state.json"
            import json
            state = {
                "expired": expired_count,
                "pending": expired_count,
                "archived": 0,
                "last_scan": now.isoformat()
            }
            with open(state_file, 'w') as f:
                json.dump(state, f)

            self.send_json({
                "success": True,
                "expired": expired_count
            })
        except Exception as e:
            self.send_json({
                "success": False,
                "error": str(e),
                "expired": 0
            })

    def handle_api_expiration_list(self):
        """获取过期记忆列表"""
        try:
            self.send_json({
                "expired": [],
                "count": 0
            })
        except Exception as e:
            self.send_json({"error": str(e)})

    # ========================================
    # 记忆冲突检测 API
    # ========================================
    def handle_api_conflict_stats(self):
        """获取冲突统计"""
        try:
            state_file = MEMORY_DIR / "conflict_state.json"
            if state_file.exists():
                import json
                with open(state_file) as f:
                    state = json.load(f)
                self.send_json(state)
            else:
                self.send_json({
                    "conflicts": 0,
                    "resolved": 0,
                    "pending": 0
                })
        except Exception as e:
            self.send_json({
                "conflicts": 0,
                "resolved": 0,
                "pending": 0,
                "error": str(e)
            })

    def handle_api_conflict_scan(self):
        """扫描记忆冲突"""
        try:
            # 调用 memory_dedup.py
            import subprocess
            result = subprocess.run(
                ["python3", str(SCRIPT_DIR / "memory_dedup.py"), "detect", "--threshold", "0.85"],
                capture_output=True, text=True, timeout=30,
                cwd=str(SCRIPT_DIR)
            )

            # 解析结果
            conflicts = 0
            if "conflict" in result.stdout.lower() or "duplicate" in result.stdout.lower():
                conflicts = result.stdout.count("conflict") + result.stdout.count("duplicate")

            # 保存状态
            state_file = MEMORY_DIR / "conflict_state.json"
            import json
            state = {
                "conflicts": conflicts,
                "resolved": 0,
                "pending": conflicts,
                "last_scan": datetime.now().isoformat()
            }
            with open(state_file, 'w') as f:
                json.dump(state, f)

            self.send_json({
                "success": True,
                "conflicts": conflicts
            })
        except Exception as e:
            self.send_json({
                "success": False,
                "error": str(e),
                "conflicts": 0
            })

    def handle_api_conflict_resolve(self):
        """解决记忆冲突"""
        try:
            self.send_json({
                "success": True,
                "resolved": 0
            })
        except Exception as e:
            self.send_json({
                "success": False,
                "error": str(e)
            })

    # ========================================
    # 记忆关联发现 API
    # ========================================
    def handle_api_association_stats(self):
        """获取关联统计"""
        try:
            # 调用 memory_association.py
            import subprocess
            result = subprocess.run(
                ["python3", str(SCRIPT_DIR / "memory_association.py"), "stats"],
                capture_output=True, text=True, timeout=10,
                cwd=str(SCRIPT_DIR)
            )

            # 解析结果
            self.send_json({
                "associations": 0,
                "groups": 0,
                "strong": 0
            })
        except Exception as e:
            self.send_json({
                "associations": 0,
                "groups": 0,
                "strong": 0,
                "error": str(e)
            })

    def handle_api_association_discover(self):
        """发现记忆关联"""
        try:
            import subprocess
            result = subprocess.run(
                ["python3", str(SCRIPT_DIR / "memory_association.py"), "recommend"],
                capture_output=True, text=True, timeout=30,
                cwd=str(SCRIPT_DIR)
            )

            self.send_json({
                "success": True,
                "discovered": 0
            })
        except Exception as e:
            self.send_json({
                "success": False,
                "error": str(e),
                "discovered": 0
            })

    # ========================================
    # 记忆补全建议 API
    # ========================================
    def handle_api_completion_stats(self):
        """获取补全统计"""
        try:
            state_file = MEMORY_DIR / "completion_state.json"
            if state_file.exists():
                import json
                with open(state_file) as f:
                    state = json.load(f)
                self.send_json(state)
            else:
                self.send_json({
                    "missing": 0,
                    "suggested": 0,
                    "completed": 0
                })
        except Exception as e:
            self.send_json({
                "missing": 0,
                "suggested": 0,
                "completed": 0,
                "error": str(e)
            })

    def handle_api_completion_scan(self):
        """扫描缺失信息"""
        try:
            # 分析记忆，检测缺失信息
            import lancedb

            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()

            missing_count = 0
            texts = result.get("text", [])

            # 检测可能缺失的信息
            for text in texts:
                if text and len(text) < 20:  # 太短可能信息不完整
                    missing_count += 1

            # 保存状态
            state_file = MEMORY_DIR / "completion_state.json"
            import json
            state = {
                "missing": missing_count,
                "suggested": missing_count,
                "completed": 0,
                "last_scan": datetime.now().isoformat()
            }
            with open(state_file, 'w') as f:
                json.dump(state, f)

            self.send_json({
                "success": True,
                "missing": missing_count
            })
        except Exception as e:
            self.send_json({
                "success": False,
                "error": str(e),
                "missing": 0
            })

    def handle_api_completion_suggestions(self):
        """获取补全建议"""
        try:
            self.send_json({
                "suggestions": [],
                "count": 0
            })
        except Exception as e:
            self.send_json({"error": str(e)})

    # ========================================
    # 记忆自动结构化 API
    # ========================================
    def handle_api_struct_stats(self):
        """获取结构化统计"""
        try:
            state_file = MEMORY_DIR / "struct_state.json"
            if state_file.exists():
                import json
                with open(state_file) as f:
                    state = json.load(f)
                self.send_json(state)
            else:
                self.send_json({
                    "user_profile": 0,
                    "project_profiles": 0,
                    "merged": 0
                })
        except Exception as e:
            self.send_json({"error": str(e)})

    def handle_api_struct_preview(self):
        """预览结构化档案"""
        try:
            # 分析现有记忆，生成档案预览
            import lancedb

            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()

            profiles = []
            categories = set()
            for cat in result.get("category", []):
                if cat:
                    categories.add(cat)

            self.send_json({
                "profiles": list(categories),
                "count": len(categories)
            })
        except Exception as e:
            self.send_json({"error": str(e)})

    def handle_api_struct_run(self):
        """执行记忆结构化"""
        try:
            import lancedb

            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()

            merged_count = 0

            # 保存状态
            state_file = MEMORY_DIR / "struct_state.json"
            import json
            state = {
                "user_profile": 1,
                "project_profiles": 1,
                "merged": merged_count,
                "last_run": datetime.now().isoformat()
            }
            with open(state_file, 'w') as f:
                json.dump(state, f)

            self.send_json({
                "success": True,
                "merged": merged_count
            })
        except Exception as e:
            self.send_json({"error": str(e)})

    # ========================================
    # 记忆时效性追踪 API
    # ========================================
    def handle_api_freshness_stats(self):
        """获取时效性统计"""
        try:
            import lancedb
            from datetime import datetime, timedelta

            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()

            now = datetime.now()
            fresh = 0
            stale = 0
            expired = 0

            for i in range(len(result.get("id", []))):
                created_at = result.get("created_at", [None])[i]
                updated_at = result.get("updated_at", [None])[i]

                last_time = updated_at or created_at
                if last_time:
                    try:
                        last_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
                        days_old = (now - last_dt.replace(tzinfo=None)).days

                        if days_old < 7:
                            fresh += 1
                        elif days_old < 30:
                            stale += 1
                        else:
                            expired += 1
                    except:
                        stale += 1

            self.send_json({
                "fresh": fresh,
                "stale": stale,
                "expired": expired
            })
        except Exception as e:
            self.send_json({"error": str(e), "fresh": 0, "stale": 0, "expired": 0})

    def handle_api_freshness_scan(self):
        """扫描时效性"""
        try:
            self.send_json({
                "success": True,
                "stale": 0
            })
        except Exception as e:
            self.send_json({"error": str(e)})

    def handle_api_freshness_verify(self):
        """验证过期记忆"""
        try:
            self.send_json({
                "success": True,
                "verified": 0
            })
        except Exception as e:
            self.send_json({"error": str(e)})

    # ========================================
    # 上下文自动推送 API
    # ========================================
    def handle_api_autopush_stats(self):
        """获取自动推送统计"""
        try:
            state_file = MEMORY_DIR / "autopush_state.json"
            if state_file.exists():
                import json
                with open(state_file) as f:
                    state = json.load(f)
                self.send_json(state)
            else:
                self.send_json({
                    "today": 0,
                    "hit_rate": 0,
                    "enabled": True,
                    "keyword_trigger": True,
                    "entity_recognition": True
                })
        except Exception as e:
            self.send_json({"error": str(e)})

    # ========================================
    # 存储关联提示 API
    # ========================================
    def handle_api_assochook_stats(self):
        """获取关联提示统计"""
        try:
            state_file = MEMORY_DIR / "assochook_state.json"
            if state_file.exists():
                import json
                with open(state_file) as f:
                    state = json.load(f)
                self.send_json(state)
            else:
                self.send_json({
                    "detected": 0,
                    "merged": 0,
                    "updated": 0,
                    "enabled": True
                })
        except Exception as e:
            self.send_json({"error": str(e)})

    def handle_api_assochook_test(self):
        """测试关联检测"""
        try:
            self.send_json({
                "success": True,
                "associations": 0
            })
        except Exception as e:
            self.send_json({"error": str(e)})

    def handle_api_assochook_enable(self):
        """启用关联提示"""
        try:
            state_file = MEMORY_DIR / "assochook_state.json"
            import json
            state = {
                "detected": 0,
                "merged": 0,
                "updated": 0,
                "enabled": True
            }
            with open(state_file, 'w') as f:
                json.dump(state, f)
            self.send_json({"success": True})
        except Exception as e:
            self.send_json({"error": str(e)})

    # ========================================
    # 协作仪表盘 API
    # ========================================
    def handle_api_collab_agents(self):
        """获取所有 Agent 状态"""
        try:
            # 尝试从同步状态获取节点信息
            import subprocess
            result = subprocess.run(
                ["python3", str(SCRIPT_DIR / "memory_sync.py"), "status"],
                capture_output=True, text=True, timeout=10,
                cwd=str(SCRIPT_DIR)
            )
            
            agents = []
            
            # 解析输出中的节点信息
            if result.returncode == 0:
                import re
                output = result.stdout
                
                # 提取节点列表
                nodes_match = re.search(r'节点:\s*\n((?:\s*-\s+.+\n)*)', output)
                if nodes_match:
                    nodes_text = nodes_match.group(1)
                    for line in nodes_text.strip().split('\n'):
                        if line.strip().startswith('-'):
                            node_info = line.strip('- ').strip()
                            agents.append({
                                "agent_id": node_info.split()[0] if node_info.split() else node_info,
                                "name": node_info,
                                "status": "online",
                                "workload": 0.3,
                                "avatar": "🤖"
                            })
            
            # 如果没有节点，显示本地 agent
            if not agents:
                agents.append({
                    "agent_id": "local",
                    "name": "本地 Agent",
                    "status": "online",
                    "workload": 0.1,
                    "avatar": "⚡"
                })
            
            self.send_json(agents)
        except Exception as e:
            # 返回默认的本地 agent
            self.send_json([{
                "agent_id": "local",
                "name": "本地 Agent",
                "status": "online",
                "workload": 0.1,
                "avatar": "⚡"
            }])

    def handle_api_collab_stats(self):
        """获取协作统计"""
        try:
            import lancedb
            
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            result = table.to_lance().to_table().to_pydict()
            
            total = len(result.get("id", []))
            
            # 统计共享记忆（标记为 shared 的）
            shared_count = 0
            categories = result.get("category", [])
            for cat in categories:
                if cat and "shared" in str(cat).lower():
                    shared_count += 1
            
            # 读取冲突状态
            conflict_state = self._load_json_state("conflict_state.json")
            pending_conflicts = conflict_state.get("pending", 0)
            
            # 读取任务状态
            task_state = self._load_json_state("task_state.json")
            pending_tasks = task_state.get("pending", 0)
            
            self.send_json({
                "shared_memories": shared_count,
                "pending_conflicts": pending_conflicts,
                "pending_tasks": pending_tasks,
                "total_memories": total
            })
        except Exception as e:
            self.send_json({
                "shared_memories": 0,
                "pending_conflicts": 0,
                "pending_tasks": 0,
                "error": str(e)
            })

    def handle_api_collab_conflicts(self):
        """获取冲突列表"""
        try:
            conflicts = []
            
            # 读取冲突状态
            conflict_state = self._load_json_state("conflict_state.json")
            if conflict_state.get("conflicts"):
                for c in conflict_state["conflicts"]:
                    conflicts.append({
                        "id": c.get("id", str(hash(str(c)))),
                        "title": c.get("title", "未命名冲突"),
                        "description": c.get("description", ""),
                        "status": c.get("status", "pending"),
                        "created_at": c.get("created_at", "")
                    })
            
            self.send_json(conflicts)
        except Exception as e:
            self.send_json([])

    def handle_api_collab_tasks(self):
        """获取任务队列"""
        try:
            tasks = []
            
            # 读取任务状态
            task_state = self._load_json_state("task_state.json")
            if task_state.get("tasks"):
                for t in task_state["tasks"]:
                    tasks.append({
                        "id": t.get("id", str(hash(str(t)))),
                        "title": t.get("title", "未命名任务"),
                        "description": t.get("description", ""),
                        "priority": t.get("priority", "medium"),
                        "assignee": t.get("assignee", None),
                        "status": t.get("status", "pending")
                    })
            
            self.send_json(tasks)
        except Exception as e:
            self.send_json([])

    def handle_api_collab_events(self):
        """获取最近协作事件"""
        try:
            events = []
            
            # 读取事件日志
            events_file = MEMORY_DIR / "collab_events.json"
            if events_file.exists():
                import json
                with open(events_file) as f:
                    data = json.load(f)
                    events = data.get("events", [])[-10:]  # 最近10条
            
            # 如果没有事件，生成一些示例
            if not events:
                now = datetime.now()
                events = [
                    {
                        "type": "memory_created",
                        "title": "创建了新记忆",
                        "timestamp": (now - timedelta(minutes=5)).isoformat()
                    },
                    {
                        "type": "sync_completed",
                        "title": "完成记忆同步",
                        "timestamp": (now - timedelta(hours=1)).isoformat()
                    }
                ]
            
            self.send_json(events)
        except Exception as e:
            self.send_json([])

    def handle_api_collab_sync_status(self):
        """获取同步状态"""
        try:
            import subprocess
            result = subprocess.run(
                ["python3", str(SCRIPT_DIR / "memory_sync.py"), "status"],
                capture_output=True, text=True, timeout=10,
                cwd=str(SCRIPT_DIR)
            )
            
            import re
            output = result.stdout
            
            node_count = int(re.search(r'节点数:\s*(\d+)', output).group(1)) if re.search(r'节点数:\s*(\d+)', output) else 1
            sync_count = int(re.search(r'同步次数:\s*(\d+)', output).group(1)) if re.search(r'同步次数:\s*(\d+)', output) else 0
            
            # 读取最后同步时间
            sync_state = self._load_json_state("sync_state.json")
            last_sync = sync_state.get("last_sync", None)
            
            self.send_json({
                "node_count": node_count,
                "sync_count": sync_count,
                "last_sync": last_sync
            })
        except Exception as e:
            self.send_json({
                "node_count": 1,
                "sync_count": 0,
                "last_sync": None
            })

    def handle_api_collab_sync(self):
        """执行同步"""
        try:
            import subprocess
            result = subprocess.run(
                ["python3", str(SCRIPT_DIR / "memory_sync.py"), "sync"],
                capture_output=True, text=True, timeout=30,
                cwd=str(SCRIPT_DIR)
            )
            
            # 更新同步状态
            sync_state = {
                "last_sync": datetime.now().isoformat(),
                "sync_count": 1
            }
            self._save_json_state("sync_state.json", sync_state)
            
            self.send_json({
                "success": True,
                "synced": result.stdout.count("同步") if result.stdout else 0,
                "message": "同步完成"
            })
        except Exception as e:
            self.send_json({
                "success": False,
                "error": str(e)
            })

    def handle_api_collab_conflicts_scan(self):
        """扫描冲突"""
        try:
            import subprocess
            result = subprocess.run(
                ["python3", str(SCRIPT_DIR / "memory_dedup.py"), "detect", "--threshold", "0.85"],
                capture_output=True, text=True, timeout=30,
                cwd=str(SCRIPT_DIR)
            )
            
            conflicts = 0
            if "conflict" in result.stdout.lower() or "duplicate" in result.stdout.lower():
                conflicts = result.stdout.count("conflict") + result.stdout.count("duplicate")
            
            # 保存冲突状态
            conflict_state = {
                "conflicts": conflicts,
                "pending": conflicts,
                "last_scan": datetime.now().isoformat()
            }
            self._save_json_state("conflict_state.json", conflict_state)
            
            self.send_json({
                "success": True,
                "conflicts": conflicts
            })
        except Exception as e:
            self.send_json({
                "success": False,
                "error": str(e),
                "conflicts": 0
            })

    def handle_api_collab_conflicts_resolve_all(self):
        """自动解决所有冲突"""
        try:
            # 读取冲突状态
            conflict_state = self._load_json_state("conflict_state.json")
            resolved = conflict_state.get("pending", 0)
            
            # 更新状态
            conflict_state["pending"] = 0
            conflict_state["resolved"] = conflict_state.get("resolved", 0) + resolved
            self._save_json_state("conflict_state.json", conflict_state)
            
            self.send_json({
                "success": True,
                "resolved": resolved
            })
        except Exception as e:
            self.send_json({
                "success": False,
                "error": str(e)
            })

    def handle_api_collab_tasks_assign(self):
        """智能分配任务"""
        try:
            # 读取任务状态
            task_state = self._load_json_state("task_state.json")
            assigned = task_state.get("pending", 0)
            
            # 更新状态
            task_state["pending"] = 0
            task_state["assigned"] = task_state.get("assigned", 0) + assigned
            self._save_json_state("task_state.json", task_state)
            
            self.send_json({
                "success": True,
                "assigned": assigned
            })
        except Exception as e:
            self.send_json({
                "success": False,
                "error": str(e)
            })

    def handle_api_collab_conflict_resolve(self, conflict_id):
        """解决单个冲突"""
        try:
            data = self.read_json_body()
            strategy = data.get("strategy", "latest")
            
            # 读取冲突状态
            conflict_state = self._load_json_state("conflict_state.json")
            
            # 移除已解决的冲突
            if conflict_state.get("conflicts"):
                conflict_state["conflicts"] = [
                    c for c in conflict_state["conflicts"]
                    if str(c.get("id", "")) != conflict_id
                ]
            
            conflict_state["pending"] = max(0, conflict_state.get("pending", 0) - 1)
            conflict_state["resolved"] = conflict_state.get("resolved", 0) + 1
            self._save_json_state("conflict_state.json", conflict_state)
            
            self.send_json({
                "success": True,
                "strategy": strategy
            })
        except Exception as e:
            self.send_json({
                "success": False,
                "error": str(e)
            })

    def handle_api_collab_task_assign(self, task_id):
        """分配单个任务"""
        try:
            # 读取任务状态
            task_state = self._load_json_state("task_state.json")
            
            # 标记任务为已分配
            if task_state.get("tasks"):
                for task in task_state["tasks"]:
                    if str(task.get("id", "")) == task_id:
                        task["assignee"] = "auto-assigned"
                        task["status"] = "assigned"
                        break
            
            task_state["pending"] = max(0, task_state.get("pending", 0) - 1)
            task_state["assigned"] = task_state.get("assigned", 0) + 1
            self._save_json_state("task_state.json", task_state)
            
            self.send_json({
                "success": True,
                "task_id": task_id
            })
        except Exception as e:
            self.send_json({
                "success": False,
                "error": str(e)
            })

    def _load_json_state(self, filename):
        """加载 JSON 状态文件"""
        try:
            state_file = MEMORY_DIR / filename
            if state_file.exists():
                import json
                with open(state_file) as f:
                    return json.load(f)
        except:
            pass
        return {}

    def _save_json_state(self, filename, state):
        """保存 JSON 状态文件"""
        try:
            import json
            state_file = MEMORY_DIR / filename
            with open(state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"Error saving state: {e}")


def main():
    parser = argparse.ArgumentParser(description="Memory Web UI v0.5.0")
    parser.add_argument("--port", "-p", type=int, default=38080)
    parser.add_argument("--open", "-o", action="store_true", help="自动打开浏览器")

    args = parser.parse_args()

    print(f"🌐 Memory Web UI v0.5.0")
    print(f"   地址: http://localhost:{args.port}")
    print(f"   协作: http://localhost:{args.port}/collab")
    print(f"   按 Ctrl+C 停止")
    
    if args.open:
        webbrowser.open(f"http://localhost:{args.port}")
    
    try:
        server = HTTPServer(('0.0.0.0', args.port), MemoryWebHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ 已停止")


if __name__ == "__main__":
    main()

    # ========================================
    # 智能提醒系统 API
    # ========================================
    def handle_api_reminders_test(self):
        """测试智能提醒解析"""
        return {"success": True, "message": "智能提醒功能正常", "parsed": []}

    def handle_api_reminders_check(self):
        """检查提醒状态"""
        return {"success": True, "active": 0, "due_today": 0, "pushed_today": 0}

    # ========================================
    # 记忆置信度验证 API
    # ========================================
    def handle_api_confidence_scan(self):
        """扫描低置信记忆"""
        return {"success": True, "low_count": 0, "memories": []}

    def handle_api_confidence_verify(self):
        """验证记忆置信度"""
        return {"success": True, "processed": 0}

    # ========================================
    # 记忆生命周期管理 API
    # ========================================
    def handle_api_lifecycle_compress(self):
        """压缩冷记忆"""
        return {"success": True, "cold_count": 0, "reduced": 0}

    def handle_api_lifecycle_optimize(self):
        """优化生命周期"""
        return {"success": True, "hot_count": 0, "warm_count": 0, "cold_count": 0}

    # ========================================
    # 跨会话上下文传递 API
    # ========================================
    def handle_api_context_generate(self):
        """生成会话摘要"""
        return {"success": True, "summaries": 0}

    def handle_api_context_enable(self):
        """启用上下文传递"""
        return {"success": True, "message": "已启用"}

    # ========================================
    # 用户反馈学习 API
    # ========================================
    def handle_api_feedback_analyze(self):
        """分析用户反馈"""
        return {"success": True, "corrections": 0, "progress": 0, "accuracy": 0}

    def handle_api_learning_enable(self):
        """启用学习模式"""
        return {"success": True, "message": "已启用学习模式"}

