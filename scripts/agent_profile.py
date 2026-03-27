#!/usr/bin/env python3
"""
Agent Profile Manager - Agent 能力画像管理

管理多个 Agent 的能力信息、工作负载、信任分数等。

Usage:
    python3 scripts/agent_profile.py register --id xiao-zhi --name "小智"
    python3 scripts/agent_profile.py skills xiao-zhi --add "coding:0.9,design:0.7"
    python3 scripts/agent_profile.py status xiao-zhi --set online
    python3 scripts/agent_profile.py match --skills "coding,python"
    python3 scripts/agent_profile.py list
    python3 scripts/agent_profile.py stats
"""

import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import sys


# Storage path
STORAGE_PATH = Path.home() / ".openclaw" / "workspace" / "memory" / "agents"


@dataclass
class SkillScore:
    """技能评分"""
    skill_name: str
    score: float  # 0.0 - 1.0
    last_used: Optional[str] = None  # ISO format
    usage_count: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SkillScore':
        return cls(**data)


@dataclass
class AgentProfile:
    """Agent 能力画像"""
    agent_id: str
    name: str
    skills: List[dict] = field(default_factory=list)  # List of SkillScore dicts
    preferences: Dict = field(default_factory=dict)
    workload: float = 0.0  # 0.0 - 1.0
    expertise: List[str] = field(default_factory=list)
    collaboration_style: str = "collaborative"  # proactive, reactive, collaborative
    trust_scores: Dict[str, float] = field(default_factory=dict)  # agent_id -> score
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "offline"  # online, offline, busy
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AgentProfile':
        return cls(**data)
    
    def get_skill_score(self, skill_name: str) -> Optional[float]:
        """获取指定技能的分数"""
        for skill in self.skills:
            if skill['skill_name'].lower() == skill_name.lower():
                return skill['score']
        return None
    
    def update_skill_usage(self, skill_name: str):
        """更新技能使用记录"""
        for skill in self.skills:
            if skill['skill_name'].lower() == skill_name.lower():
                skill['last_used'] = datetime.now().isoformat()
                skill['usage_count'] += 1
                return
        # If skill doesn't exist, add it
        self.skills.append({
            'skill_name': skill_name,
            'score': 0.5,
            'last_used': datetime.now().isoformat(),
            'usage_count': 1
        })


class AgentProfileManager:
    """Agent 能力画像管理器"""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path) if storage_path else STORAGE_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, AgentProfile] = {}
        self._load_all()
    
    def _load_all(self):
        """加载所有 Agent 画像"""
        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    profile = AgentProfile.from_dict(data)
                    self.profiles[profile.agent_id] = profile
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")
    
    def _save(self, profile: AgentProfile):
        """保存 Agent 画像到文件"""
        file_path = self.storage_path / f"{profile.agent_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)
    
    def register(self, profile: AgentProfile) -> bool:
        """注册新 Agent"""
        if profile.agent_id in self.profiles:
            print(f"Agent {profile.agent_id} already exists")
            return False
        self.profiles[profile.agent_id] = profile
        self._save(profile)
        print(f"✓ Registered agent: {profile.name} ({profile.agent_id})")
        return True
    
    def update_skills(self, agent_id: str, skills: List[SkillScore]) -> bool:
        """更新技能评分"""
        profile = self.profiles.get(agent_id)
        if not profile:
            print(f"Agent {agent_id} not found")
            return False
        
        # Merge or update skills
        for new_skill in skills:
            found = False
            for i, existing in enumerate(profile.skills):
                if existing['skill_name'].lower() == new_skill.skill_name.lower():
                    profile.skills[i] = new_skill.to_dict()
                    found = True
                    break
            if not found:
                profile.skills.append(new_skill.to_dict())
        
        profile.last_active = datetime.now().isoformat()
        self._save(profile)
        print(f"✓ Updated skills for {agent_id}")
        return True
    
    def update_workload(self, agent_id: str, workload: float) -> bool:
        """更新工作负载"""
        profile = self.profiles.get(agent_id)
        if not profile:
            print(f"Agent {agent_id} not found")
            return False
        
        profile.workload = max(0.0, min(1.0, workload))
        profile.last_active = datetime.now().isoformat()
        self._save(profile)
        print(f"✓ Updated workload for {agent_id}: {profile.workload:.1%}")
        return True
    
    def set_status(self, agent_id: str, status: str) -> bool:
        """设置在线状态"""
        profile = self.profiles.get(agent_id)
        if not profile:
            print(f"Agent {agent_id} not found")
            return False
        
        valid_statuses = ['online', 'offline', 'busy']
        if status not in valid_statuses:
            print(f"Invalid status: {status}. Must be one of {valid_statuses}")
            return False
        
        profile.status = status
        profile.last_active = datetime.now().isoformat()
        self._save(profile)
        print(f"✓ Set status for {agent_id}: {status}")
        return True
    
    def get_best_agent_for_task(self, task_skills: List[str]) -> Optional[str]:
        """根据技能匹配找最佳 Agent"""
        available = self.get_available_agents()
        if not available:
            return None
        
        best_agent = None
        best_score = -1
        
        for profile in available:
            # Calculate matching score
            match_score = 0.0
            for skill in task_skills:
                skill_score = profile.get_skill_score(skill)
                if skill_score:
                    match_score += skill_score
            
            # Normalize by number of skills
            if task_skills:
                match_score /= len(task_skills)
            
            # Penalize high workload
            match_score *= (1.0 - profile.workload * 0.5)
            
            if match_score > best_score:
                best_score = match_score
                best_agent = profile.agent_id
        
        return best_agent
    
    def get_available_agents(self) -> List[AgentProfile]:
        """获取可用 Agent（online 且 workload < 0.8）"""
        return [
            p for p in self.profiles.values()
            if p.status == 'online' and p.workload < 0.8
        ]
    
    def update_trust(self, from_agent: str, to_agent: str, score: float) -> bool:
        """更新信任分数"""
        profile = self.profiles.get(from_agent)
        if not profile:
            print(f"Agent {from_agent} not found")
            return False
        
        if to_agent not in self.profiles:
            print(f"Agent {to_agent} not found")
            return False
        
        profile.trust_scores[to_agent] = max(0.0, min(1.0, score))
        profile.last_active = datetime.now().isoformat()
        self._save(profile)
        print(f"✓ Updated trust: {from_agent} -> {to_agent}: {score:.2f}")
        return True
    
    def get_agent_stats(self) -> Dict:
        """获取 Agent 统计"""
        total = len(self.profiles)
        online = sum(1 for p in self.profiles.values() if p.status == 'online')
        busy = sum(1 for p in self.profiles.values() if p.status == 'busy')
        offline = sum(1 for p in self.profiles.values() if p.status == 'offline')
        
        avg_workload = sum(p.workload for p in self.profiles.values()) / total if total > 0 else 0
        
        all_skills = set()
        for p in self.profiles.values():
            for skill in p.skills:
                all_skills.add(skill['skill_name'])
        
        return {
            'total_agents': total,
            'online': online,
            'busy': busy,
            'offline': offline,
            'avg_workload': avg_workload,
            'total_skills': len(all_skills),
            'skills': sorted(list(all_skills))
        }
    
    def list_agents(self) -> List[Dict]:
        """列出所有 Agent 的摘要信息"""
        result = []
        for profile in sorted(self.profiles.values(), key=lambda p: p.agent_id):
            status_emoji = {'online': '🟢', 'offline': '⚫', 'busy': '🔴'}.get(profile.status, '❓')
            result.append({
                'agent_id': profile.agent_id,
                'name': profile.name,
                'status': f"{status_emoji} {profile.status}",
                'workload': f"{profile.workload:.0%}",
                'skills_count': len(profile.skills),
                'expertise': profile.expertise
            })
        return result


def init_default_agents(manager: AgentProfileManager):
    """初始化默认 Agent"""
    # xiao-zhi: 开发、记忆系统、EvoMap
    if 'xiao-zhi' not in manager.profiles:
        xiao_zhi = AgentProfile(
            agent_id='xiao-zhi',
            name='小智',
            skills=[
                SkillScore('coding', 0.95, usage_count=100).to_dict(),
                SkillScore('python', 0.9, usage_count=80).to_dict(),
                SkillScore('memory_system', 0.95, usage_count=50).to_dict(),
                SkillScore('evomap', 0.9, usage_count=30).to_dict(),
                SkillScore('development', 0.95, usage_count=90).to_dict(),
                SkillScore('api_design', 0.85, usage_count=40).to_dict(),
            ],
            expertise=['开发', '记忆系统', 'EvoMap', 'API设计'],
            collaboration_style='proactive',
            status='offline'
        )
        manager.register(xiao_zhi)
    
    # xiao-liu: 产品、飞书、协作
    if 'xiao-liu' not in manager.profiles:
        xiao_liu = AgentProfile(
            agent_id='xiao-liu',
            name='小刘',
            skills=[
                SkillScore('product', 0.9, usage_count=60).to_dict(),
                SkillScore('feishu', 0.95, usage_count=70).to_dict(),
                SkillScore('collaboration', 0.9, usage_count=50).to_dict(),
                SkillScore('documentation', 0.85, usage_count=40).to_dict(),
                SkillScore('user_research', 0.8, usage_count=30).to_dict(),
            ],
            expertise=['产品', '飞书', '协作', '文档'],
            collaboration_style='collaborative',
            status='offline'
        )
        manager.register(xiao_liu)


def parse_skills_string(skills_str: str) -> List[SkillScore]:
    """解析技能字符串 'coding:0.9,design:0.7' -> List[SkillScore]"""
    skills = []
    for item in skills_str.split(','):
        item = item.strip()
        if ':' in item:
            name, score = item.split(':', 1)
            try:
                score = float(score)
            except ValueError:
                score = 0.5
        else:
            name = item
            score = 0.5
        skills.append(SkillScore(name.strip(), score))
    return skills


def main():
    parser = argparse.ArgumentParser(
        description='Agent Profile Manager - 管理多个 Agent 的能力信息',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/agent_profile.py register --id xiao-zhi --name "小智"
  python3 scripts/agent_profile.py skills xiao-zhi --add "coding:0.9,design:0.7"
  python3 scripts/agent_profile.py status xiao-zhi --set online
  python3 scripts/agent_profile.py match --skills "coding,python"
  python3 scripts/agent_profile.py list
  python3 scripts/agent_profile.py stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # register command
    register_parser = subparsers.add_parser('register', help='注册新 Agent')
    register_parser.add_argument('--id', required=True, help='Agent ID')
    register_parser.add_argument('--name', required=True, help='Agent 名称')
    register_parser.add_argument('--expertise', help='专业领域 (逗号分隔)')
    register_parser.add_argument('--style', default='collaborative', 
                                  choices=['proactive', 'reactive', 'collaborative'],
                                  help='协作风格')
    
    # skills command
    skills_parser = subparsers.add_parser('skills', help='管理 Agent 技能')
    skills_parser.add_argument('agent_id', help='Agent ID')
    skills_parser.add_argument('--add', help='添加技能 (格式: skill:score,skill:score)')
    skills_parser.add_argument('--remove', help='移除技能 (逗号分隔)')
    
    # status command
    status_parser = subparsers.add_parser('status', help='设置 Agent 状态')
    status_parser.add_argument('agent_id', help='Agent ID')
    status_parser.add_argument('--set', dest='status', required=True,
                                choices=['online', 'offline', 'busy'],
                                help='状态值')
    
    # workload command
    workload_parser = subparsers.add_parser('workload', help='更新工作负载')
    workload_parser.add_argument('agent_id', help='Agent ID')
    workload_parser.add_argument('--set', dest='workload', type=float, required=True,
                                  help='工作负载 (0.0-1.0)')
    
    # match command
    match_parser = subparsers.add_parser('match', help='匹配最佳 Agent')
    match_parser.add_argument('--skills', required=True, help='所需技能 (逗号分隔)')
    
    # list command
    subparsers.add_parser('list', help='列出所有 Agent')
    
    # stats command
    subparsers.add_parser('stats', help='显示统计信息')
    
    # trust command
    trust_parser = subparsers.add_parser('trust', help='更新信任分数')
    trust_parser.add_argument('from_agent', help='来源 Agent ID')
    trust_parser.add_argument('to_agent', help='目标 Agent ID')
    trust_parser.add_argument('--score', type=float, required=True, help='信任分数 (0.0-1.0)')
    
    # init command
    subparsers.add_parser('init', help='初始化默认 Agent')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = AgentProfileManager()
    
    if args.command == 'register':
        expertise = args.expertise.split(',') if args.expertise else []
        profile = AgentProfile(
            agent_id=args.id,
            name=args.name,
            expertise=expertise,
            collaboration_style=args.style
        )
        manager.register(profile)
    
    elif args.command == 'skills':
        if args.add:
            skills = parse_skills_string(args.add)
            manager.update_skills(args.agent_id, skills)
        elif args.remove:
            profile = manager.profiles.get(args.agent_id)
            if profile:
                remove_names = [s.strip().lower() for s in args.remove.split(',')]
                profile.skills = [s for s in profile.skills 
                                 if s['skill_name'].lower() not in remove_names]
                manager._save(profile)
                print(f"✓ Removed skills from {args.agent_id}")
            else:
                print(f"Agent {args.agent_id} not found")
        else:
            # Show skills
            profile = manager.profiles.get(args.agent_id)
            if profile:
                print(f"\n{profile.name} ({profile.agent_id}) Skills:")
                for skill in profile.skills:
                    print(f"  • {skill['skill_name']}: {skill['score']:.0%} "
                          f"(used {skill['usage_count']} times)")
            else:
                print(f"Agent {args.agent_id} not found")
    
    elif args.command == 'status':
        manager.set_status(args.agent_id, args.status)
    
    elif args.command == 'workload':
        manager.update_workload(args.agent_id, args.workload)
    
    elif args.command == 'match':
        skills = [s.strip() for s in args.skills.split(',')]
        best_agent = manager.get_best_agent_for_task(skills)
        if best_agent:
            profile = manager.profiles[best_agent]
            print(f"\n🎯 Best agent for {skills}:")
            print(f"  {profile.name} ({profile.agent_id})")
            print(f"  Status: {profile.status}")
            print(f"  Workload: {profile.workload:.0%}")
            print(f"  Matching skills:")
            for skill in skills:
                score = profile.get_skill_score(skill)
                if score:
                    print(f"    • {skill}: {score:.0%}")
        else:
            print(f"No available agent found for skills: {skills}")
    
    elif args.command == 'list':
        agents = manager.list_agents()
        if agents:
            print("\n📋 Registered Agents:")
            print("-" * 60)
            for agent in agents:
                print(f"  {agent['status']} {agent['name']} ({agent['agent_id']})")
                print(f"      Workload: {agent['workload']} | Skills: {agent['skills_count']}")
                if agent['expertise']:
                    print(f"      Expertise: {', '.join(agent['expertise'])}")
        else:
            print("No agents registered. Run 'python3 scripts/agent_profile.py init' to add default agents.")
    
    elif args.command == 'stats':
        stats = manager.get_agent_stats()
        print("\n📊 Agent Statistics:")
        print("-" * 40)
        print(f"  Total Agents: {stats['total_agents']}")
        print(f"  Online: {stats['online']} | Busy: {stats['busy']} | Offline: {stats['offline']}")
        print(f"  Average Workload: {stats['avg_workload']:.0%}")
        print(f"  Total Skills: {stats['total_skills']}")
        if stats['skills']:
            print(f"  Skills: {', '.join(stats['skills'])}")
    
    elif args.command == 'trust':
        manager.update_trust(args.from_agent, args.to_agent, args.score)
    
    elif args.command == 'init':
        print("Initializing default agents...")
        init_default_agents(manager)
        print("\n✓ Default agents initialized")


if __name__ == '__main__':
    main()
