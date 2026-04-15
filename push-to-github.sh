#!/bin/bash

echo "🚀 Unified Memory v5.2.0 GitHub 推送脚本"
echo "========================================"

# 检查当前目录
if [ ! -f "package.json" ]; then
    echo "❌ 错误: 请在 Unified Memory 项目目录中运行"
    exit 1
fi

echo "📊 当前状态:"
echo "  仓库: $(git remote -v | grep origin | head -1)"
echo "  分支: $(git branch --show-current)"
echo "  待推送: $(git log origin/master..HEAD --oneline | wc -l) 个提交"

echo ""
echo "🔐 请选择认证方式:"
echo "  1. 使用 GitHub Token (推荐)"
echo "  2. 使用 SSH 密钥"
echo "  3. 查看推送指南"
read -p "选择 (1/2/3): " auth_choice

case $auth_choice in
    1)
        # 使用 GitHub Token
        read -p "请输入 GitHub Personal Access Token: " github_token
        if [ -z "$github_token" ]; then
            echo "❌ Token 不能为空"
            exit 1
        fi
        
        echo "🔑 设置 token 认证..."
        git remote set-url origin https://x-access-token:${github_token}@github.com/mouxangithub/unified-memory.git
        ;;
    2)
        # 使用 SSH
        echo "🔑 使用 SSH 认证..."
        git remote set-url origin git@github.com:mouxangithub/unified-memory.git
        
        # 测试 SSH 连接
        echo "测试 SSH 连接..."
        ssh -T git@github.com 2>&1 | grep -i "successfully authenticated" || {
            echo "⚠️  SSH 认证可能有问题"
            echo "请确保:"
            echo "  1. SSH 密钥已生成: ssh-keygen -t ed25519 -C 'your_email@example.com'"
            echo "  2. 公钥已添加到 GitHub: cat ~/.ssh/id_ed25519.pub"
            echo "  3. SSH 代理运行: eval \$(ssh-agent -s) && ssh-add ~/.ssh/id_ed25519"
            read -p "继续尝试推送? (y/n): " continue_choice
            if [ "$continue_choice" != "y" ]; then
                exit 1
            fi
        }
        ;;
    3)
        echo "📖 推送指南:"
        cat PUSH-TO-GITHUB.md | head -50
        echo ""
        echo "完整指南请查看: cat PUSH-TO-GITHUB.md"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "📤 开始推送代码..."
echo "提交详情:"
git log origin/master..HEAD --oneline

echo ""
read -p "确认推送以上提交到 GitHub? (y/n): " confirm_push
if [ "$confirm_push" != "y" ]; then
    echo "❌ 推送取消"
    exit 0
fi

# 推送代码
echo "🔄 推送中..."
git push origin master

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 推送成功！"
    echo ""
    echo "📊 推送统计:"
    echo "  仓库: https://github.com/mouxangithub/unified-memory"
    echo "  分支: master"
    echo "  最新提交: $(git log --oneline -1)"
    
    # 恢复原始 URL (如果是 token 方式)
    if [ "$auth_choice" = "1" ]; then
        echo "🔄 恢复原始 URL..."
        git remote set-url origin git@github.com:mouxangithub/unified-memory.git
    fi
    
    echo ""
    echo "✅ Unified Memory v5.2.0 已成功发布到 GitHub！"
    echo ""
    echo "🚀 下一步建议:"
    echo "  1. 访问 https://github.com/mouxangithub/unified-memory 验证"
    echo "  2. 创建 v5.2.0 Release"
    echo "  3. 更新生产环境: ./deploy-atomic-fixes.sh"
    echo "  4. 监控服务运行"
    
else
    echo "❌ 推送失败"
    echo ""
    echo "🔧 故障排除:"
    echo "  1. 检查网络连接"
    echo "  2. 验证认证信息"
    echo "  3. 检查仓库权限"
    echo "  4. 尝试: git pull origin master --rebase"
    exit 1
fi

echo ""
echo "📋 最终验证:"
echo "  远程提交: $(git log --oneline -3)"
echo "  状态: $(git status --short | head -5)"

echo ""
echo "🏁 脚本执行完成！"