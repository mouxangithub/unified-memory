# 主动感知模块 (proactive_care.py)

> 检测刘总状态变化并主动关心

## 功能概览

| 检测项 | 触发条件 | 冷却时间 | 消息示例 |
|--------|----------|----------|----------|
| 日程密度 | > 5个会议/天 | 2小时 | "刘总，今天会议挺密集的(6个)，记得适当休息，喝口水活动一下~" |
| 连续工作 | > 4小时 | 1小时 | "刘总，连续工作4小时了，休息一下喝口水吧！" |
| 负面关键词 | 检测到"累"、"烦"等 | 3小时 | "刘总，看你今天挺累的，注意身体啊！需要我帮忙处理什么吗？" |
| 任务截止 | < 24小时 | 6小时 | "刘总，有3个任务截止时间快到了(< 24小时)，注意优先级安排~" |

## 使用方法

### 命令行

```bash
# 执行检查（集成到 HEARTBEAT.md）
python3 ~/.openclaw/workspace/skills/unified-memory/scripts/proactive_care.py check

# 显示配置
python3 ~/.openclaw/workspace/skills/unified-memory/scripts/proactive_care.py config

# 启用/禁用模块
python3 ~/.openclaw/workspace/skills/unified-memory/scripts/proactive_care.py config --enable
python3 ~/.openclaw/workspace/skills/unified-memory/scripts/proactive_care.py config --disable

# 测试关键词检测
python3 ~/.openclaw/workspace/skills/unified-memory/scripts/proactive_care.py test --text "今天好累"
```

### 集成到 Heartbeat

已在 `HEARTBEAT.md` 中添加检查命令，每次心跳时自动执行。

## 配置文件

位置：`~/.openclaw/workspace/memory/proactive_care_config.json`

```json
{
  "enabled": true,
  "check_interval_minutes": 30,
  "rules": {
    "meeting_density": {
      "enabled": true,
      "threshold": 5,
      "cooldown_hours": 2,
      "message": "刘总，今天会议挺密集的({count}个)，记得适当休息，喝口水活动一下~"
    },
    "continuous_work": {
      "enabled": true,
      "threshold_hours": 4,
      "cooldown_hours": 1,
      "message": "刘总，连续工作{hours}小时了，休息一下喝口水吧！"
    },
    "negative_keywords": {
      "enabled": true,
      "keywords": ["累", "烦", "忙", "烦死了", "好累", "太忙", "崩溃", "压力大", "头疼", "无语"],
      "cooldown_hours": 3,
      "message": "刘总，看你今天挺累的，注意身体啊！需要我帮忙处理什么吗？"
    },
    "deadline_pressure": {
      "enabled": true,
      "threshold_hours": 24,
      "cooldown_hours": 6,
      "message": "刘总，有{count}个任务截止时间快到了(< {hours}小时)，注意优先级安排~"
    }
  },
  "user": {
    "open_id": "ou_dcdc467a4de8cd4667474ccb99522e80",
    "name": "刘总"
  }
}
```

### 配置说明

- `enabled`: 是否启用该检测项
- `threshold`: 触发阈值（会议数量、小时数等）
- `cooldown_hours`: 触发后冷却时间，避免频繁提醒
- `message`: 提醒消息模板（支持变量替换）

## 状态文件

位置：`~/.openclaw/workspace/memory/proactive_care_state.json`

记录：
- `last_check`: 最后检查时间
- `work_start_time`: 工作开始时间（用于计算连续工作时长）
- `last_trigger`: 各项检测的最后触发时间

## 实现原理

1. **日程密度检测**：调用飞书日历 API 获取今日日程，统计会议数量
2. **连续工作检测**：通过消息频率推断工作状态，计算连续工作时长
3. **负面关键词检测**：搜索最近消息，匹配预设关键词
4. **任务截止检测**：获取任务列表，计算截止时间剩余

所有检测都通过 subprocess 调用飞书工具，避免模块导入问题。

## 注意事项

- 只在工作时间（9:00-18:00）检测连续工作
- 冷却时间内不会重复触发同一检测项
- 消息通过飞书私聊发送给刘总

## 扩展建议

1. **添加更多检测项**：如邮件压力、群聊活跃度等
2. **智能推送时机**：根据用户习惯选择最佳推送时间
3. **个性化消息**：根据历史反馈调整消息内容
4. **群聊@提醒**：在特定群聊中@提醒（可选功能）

---

*最后更新：2026-03-21*
