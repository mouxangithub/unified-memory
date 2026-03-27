#!/usr/bin/env python3
"""
Collaboration Bus - Real-time agent collaboration communication

Usage:
    python3 scripts/collab_bus.py start
    python3 scripts/collab_bus.py status
    python3 scripts/collab_bus.py subscribe <agent_id> --topics <topics>
    python3 scripts/collab_bus.py pending <agent_id>
    python3 scripts/collab_bus.py broadcast --type <event_type> --source <agent> --payload <json>
"""

import os
import sys
import json
import uuid
import argparse
import threading
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Callable, Any
from enum import Enum
from queue import Queue, Empty
from pathlib import Path
import time


# Storage paths
WORKSPACE = Path.home() / ".openclaw" / "workspace"
COLLAB_DIR = WORKSPACE / "memory" / "collab"
EVENTS_FILE = COLLAB_DIR / "events.jsonl"
STATUS_FILE = COLLAB_DIR / "status.json"


class EventType(Enum):
    """Event types for collaboration communication"""
    MEMORY_CREATED = "memory_created"
    MEMORY_UPDATED = "memory_updated"
    MEMORY_DELETED = "memory_deleted"
    CONFLICT_DETECTED = "conflict_detected"
    CONFLICT_RESOLVED = "conflict_resolved"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    TASK_HANDOFF = "task_handoff"
    AGENT_ONLINE = "agent_online"
    AGENT_OFFLINE = "agent_offline"
    SYNC_REQUEST = "sync_request"


@dataclass
class CollaborationEvent:
    """Event for agent collaboration"""
    event_id: str
    event_type: EventType
    source_agent: str
    target_agents: List[str]  # empty = broadcast
    timestamp: str  # ISO format
    payload: Dict[str, Any]
    priority: str = "normal"  # low, normal, high, urgent
    acknowledged_by: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source_agent": self.source_agent,
            "target_agents": self.target_agents,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "priority": self.priority,
            "acknowledged_by": self.acknowledged_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CollaborationEvent':
        """Create from dictionary"""
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            source_agent=data["source_agent"],
            target_agents=data.get("target_agents", []),
            timestamp=data["timestamp"],
            payload=data.get("payload", {}),
            priority=data.get("priority", "normal"),
            acknowledged_by=data.get("acknowledged_by", [])
        )
    
    @classmethod
    def create(cls, event_type: EventType, source_agent: str, 
               payload: Dict, target_agents: List[str] = None,
               priority: str = "normal") -> 'CollaborationEvent':
        """Create a new event"""
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            source_agent=source_agent,
            target_agents=target_agents or [],
            timestamp=datetime.now().isoformat(),
            payload=payload,
            priority=priority
        )


@dataclass
class Subscription:
    """Agent subscription to event topics"""
    agent_id: str
    topics: List[EventType]
    callback: Optional[Callable] = None
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "topics": [t.value for t in self.topics],
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Subscription':
        return cls(
            agent_id=data["agent_id"],
            topics=[EventType(t) for t in data.get("topics", [])],
            created_at=data.get("created_at", "")
        )


class CollaborationBus:
    """
    Real-time collaboration bus for agent communication.
    
    Features:
    - Event publish/subscribe
    - Offline queue support
    - Event persistence
    - Broadcast and targeted messaging
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path) if storage_path else COLLAB_DIR
        self.subscriptions: Dict[str, List[Subscription]] = {}
        self.event_queue: Queue = Queue()
        self.event_history: List[CollaborationEvent] = []
        self.running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing state
        self._load_state()
        self._load_event_history()
    
    def _load_state(self):
        """Load subscriptions and status from file"""
        status_file = self.storage_path / "status.json"
        if status_file.exists():
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for agent_id, subs in data.get("subscriptions", {}).items():
                        self.subscriptions[agent_id] = [
                            Subscription.from_dict(s) for s in subs
                        ]
            except Exception as e:
                print(f"Warning: Failed to load state: {e}")
    
    def _save_state(self):
        """Save subscriptions and status to file"""
        status_file = self.storage_path / "status.json"
        try:
            data = {
                "subscriptions": {
                    agent_id: [s.to_dict() for s in subs]
                    for agent_id, subs in self.subscriptions.items()
                },
                "last_updated": datetime.now().isoformat()
            }
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save state: {e}")
    
    def _load_event_history(self):
        """Load event history from JSONL file"""
        events_file = self.storage_path / "events.jsonl"
        if events_file.exists():
            try:
                with open(events_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            event = CollaborationEvent.from_dict(json.loads(line))
                            self.event_history.append(event)
            except Exception as e:
                print(f"Warning: Failed to load event history: {e}")
    
    def _append_event(self, event: CollaborationEvent):
        """Append event to JSONL file"""
        events_file = self.storage_path / "events.jsonl"
        try:
            with open(events_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Warning: Failed to append event: {e}")
    
    def start(self):
        """Start the collaboration bus"""
        if self.running:
            print("Bus already running")
            return
        
        self.running = True
        self._worker_thread = threading.Thread(target=self._process_events, daemon=True)
        self._worker_thread.start()
        print("Collaboration bus started")
    
    def stop(self):
        """Stop the collaboration bus"""
        self.running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=2)
        self._save_state()
        print("Collaboration bus stopped")
    
    def _process_events(self):
        """Background worker to process events"""
        while self.running:
            try:
                event = self.event_queue.get(timeout=1)
                self._dispatch_event(event)
            except Empty:
                continue
            except Exception as e:
                print(f"Error processing event: {e}")
    
    def _dispatch_event(self, event: CollaborationEvent):
        """Dispatch event to subscribers"""
        with self._lock:
            for agent_id, subs in self.subscriptions.items():
                # Skip if source is same as target
                if agent_id == event.source_agent:
                    continue
                
                # Check if targeted or broadcast
                is_targeted = not event.target_agents or agent_id in event.target_agents
                if not is_targeted:
                    continue
                
                # Check subscription topics
                for sub in subs:
                    if event.event_type in sub.topics:
                        # Invoke callback if available
                        if sub.callback:
                            try:
                                sub.callback(event)
                            except Exception as e:
                                print(f"Callback error for {agent_id}: {e}")
            
            # Store in history
            self.event_history.append(event)
            self._append_event(event)
    
    def publish(self, event: CollaborationEvent, immediate: bool = False):
        """Publish an event to the bus.
        
        Args:
            event: The event to publish
            immediate: If True, dispatch immediately instead of queuing (for CLI mode)
        """
        if immediate or not self.running:
            # For CLI mode or when not running, dispatch immediately
            self._dispatch_event(event)
        else:
            self.event_queue.put(event)
        return event.event_id
    
    def subscribe(self, agent_id: str, topics: List[EventType], 
                  callback: Optional[Callable] = None):
        """Subscribe an agent to event topics"""
        with self._lock:
            subscription = Subscription(
                agent_id=agent_id,
                topics=topics,
                callback=callback
            )
            
            if agent_id not in self.subscriptions:
                self.subscriptions[agent_id] = []
            
            # Remove existing subscription for same topics
            self.subscriptions[agent_id] = [
                s for s in self.subscriptions[agent_id] 
                if set(s.topics) != set(topics)
            ]
            
            self.subscriptions[agent_id].append(subscription)
            self._save_state()
        
        return subscription
    
    def unsubscribe(self, agent_id: str):
        """Unsubscribe an agent from all topics"""
        with self._lock:
            if agent_id in self.subscriptions:
                del self.subscriptions[agent_id]
                self._save_state()
    
    def broadcast_change(self, memory_id: str, change_type: str, 
                         source_agent: str, payload: Dict = None):
        """Broadcast a memory change event"""
        event_type_map = {
            "created": EventType.MEMORY_CREATED,
            "updated": EventType.MEMORY_UPDATED,
            "deleted": EventType.MEMORY_DELETED
        }
        
        event_type = event_type_map.get(change_type, EventType.MEMORY_UPDATED)
        event = CollaborationEvent.create(
            event_type=event_type,
            source_agent=source_agent,
            payload={"memory_id": memory_id, **(payload or {})}
        )
        
        return self.publish(event)
    
    def get_pending_events(self, agent_id: str) -> List[CollaborationEvent]:
        """Get unacknowledged events for an agent"""
        pending = []
        
        with self._lock:
            # Get agent's subscribed topics
            subscribed_topics = set()
            if agent_id in self.subscriptions:
                for sub in self.subscriptions[agent_id]:
                    subscribed_topics.update(sub.topics)
            
            # Find unacknowledged events matching subscriptions
            for event in self.event_history[-100:]:  # Last 100 events
                # Skip if already acknowledged
                if agent_id in event.acknowledged_by:
                    continue
                
                # Skip if source is same agent
                if event.source_agent == agent_id:
                    continue
                
                # Check if targeted or broadcast
                is_targeted = not event.target_agents or agent_id in event.target_agents
                if not is_targeted:
                    continue
                
                # Check if event type is subscribed
                if event.event_type in subscribed_topics:
                    pending.append(event)
        
        return pending
    
    def acknowledge(self, event_id: str, agent_id: str):
        """Acknowledge an event has been processed"""
        with self._lock:
            for event in self.event_history:
                if event.event_id == event_id:
                    if agent_id not in event.acknowledged_by:
                        event.acknowledged_by.append(agent_id)
                    break
        
        # Update the events file
        self._rewrite_events_file()
    
    def _rewrite_events_file(self):
        """Rewrite the entire events file"""
        events_file = self.storage_path / "events.jsonl"
        try:
            with open(events_file, 'w', encoding='utf-8') as f:
                for event in self.event_history:
                    f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Warning: Failed to rewrite events file: {e}")
    
    def get_sync_state(self) -> Dict:
        """Get overall sync state"""
        with self._lock:
            agents = list(self.subscriptions.keys())
            pending_counts = {
                agent_id: len(self.get_pending_events(agent_id))
                for agent_id in agents
            }
            
            return {
                "running": self.running,
                "total_subscriptions": sum(len(subs) for subs in self.subscriptions.values()),
                "agents": agents,
                "event_history_size": len(self.event_history),
                "pending_events": pending_counts,
                "storage_path": str(self.storage_path)
            }
    
    def request_sync(self, from_agent: str, to_agent: str):
        """Request sync from one agent to another"""
        event = CollaborationEvent.create(
            event_type=EventType.SYNC_REQUEST,
            source_agent=from_agent,
            target_agents=[to_agent],
            payload={"request_time": datetime.now().isoformat()}
        )
        return self.publish(event)


class SyncManager:
    """
    Manages synchronization between agents.
    Handles conflict detection and resolution.
    """
    
    def __init__(self, bus: CollaborationBus):
        self.bus = bus
        self.sync_states: Dict[str, Dict] = {}
    
    def check_sync_status(self, agent_id: str) -> Dict:
        """Check sync status for an agent"""
        pending = self.bus.get_pending_events(agent_id)
        
        return {
            "agent_id": agent_id,
            "pending_events": len(pending),
            "last_sync": self.sync_states.get(agent_id, {}).get("last_sync"),
            "sync_required": len(pending) > 0,
            "pending_types": list(set(e.event_type.value for e in pending))
        }
    
    def resolve_conflict(self, conflict_data: Dict) -> Dict:
        """Resolve a sync conflict"""
        strategy = conflict_data.get("strategy", "latest_wins")
        memories = conflict_data.get("memories", [])
        
        if not memories:
            return {"resolved": False, "reason": "No memories to resolve"}
        
        if strategy == "latest_wins":
            # Sort by timestamp and take latest
            sorted_memories = sorted(
                memories,
                key=lambda m: m.get("timestamp", ""),
                reverse=True
            )
            winner = sorted_memories[0] if sorted_memories else None
            
            return {
                "resolved": True,
                "strategy": strategy,
                "winner": winner,
                "conflict_id": str(uuid.uuid4())
            }
        
        elif strategy == "merge":
            # Attempt to merge all memories
            merged_content = "\n".join(
                m.get("content", "") for m in memories if m.get("content")
            )
            
            return {
                "resolved": True,
                "strategy": strategy,
                "merged_content": merged_content,
                "conflict_id": str(uuid.uuid4())
            }
        
        else:
            return {
                "resolved": False,
                "reason": f"Unknown strategy: {strategy}"
            }
    
    def perform_sync(self, agent_id: str) -> Dict:
        """Perform full sync for an agent"""
        pending = self.bus.get_pending_events(agent_id)
        results = []
        
        for event in pending:
            # Process each event
            result = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "processed": True
            }
            
            # Acknowledge the event
            self.bus.acknowledge(event.event_id, agent_id)
            results.append(result)
        
        # Update sync state
        self.sync_states[agent_id] = {
            "last_sync": datetime.now().isoformat(),
            "events_processed": len(results)
        }
        
        return {
            "agent_id": agent_id,
            "synced": True,
            "events_processed": len(results),
            "results": results
        }


# CLI Interface
def main():
    parser = argparse.ArgumentParser(description="Collaboration Bus CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # start command
    subparsers.add_parser("start", help="Start the collaboration bus")
    
    # stop command
    subparsers.add_parser("stop", help="Stop the collaboration bus")
    
    # status command
    subparsers.add_parser("status", help="Get bus status")
    
    # subscribe command
    sub_subscribe = subparsers.add_parser("subscribe", help="Subscribe to events")
    sub_subscribe.add_argument("agent_id", help="Agent ID")
    sub_subscribe.add_argument("--topics", required=True, 
                               help="Comma-separated topics (e.g., memory_created,conflict_detected)")
    
    # unsubscribe command
    sub_unsubscribe = subparsers.add_parser("unsubscribe", help="Unsubscribe from events")
    sub_unsubscribe.add_argument("agent_id", help="Agent ID")
    
    # pending command
    sub_pending = subparsers.add_parser("pending", help="Get pending events")
    sub_pending.add_argument("agent_id", help="Agent ID")
    
    # broadcast command
    sub_broadcast = subparsers.add_parser("broadcast", help="Broadcast an event")
    sub_broadcast.add_argument("--type", required=True, dest="event_type",
                               help="Event type (e.g., memory_created)")
    sub_broadcast.add_argument("--source", required=True, help="Source agent ID")
    sub_broadcast.add_argument("--payload", default="{}", help="JSON payload")
    sub_broadcast.add_argument("--targets", default="", help="Comma-separated target agents")
    sub_broadcast.add_argument("--priority", default="normal", 
                               choices=["low", "normal", "high", "urgent"])
    
    # ack command
    sub_ack = subparsers.add_parser("ack", help="Acknowledge an event")
    sub_ack.add_argument("event_id", help="Event ID")
    sub_ack.add_argument("agent_id", help="Agent ID")
    
    # sync command
    sub_sync = subparsers.add_parser("sync", help="Perform sync")
    sub_sync.add_argument("agent_id", help="Agent ID")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    bus = CollaborationBus()
    
    if args.command == "start":
        bus.start()
        print("Bus started. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            bus.stop()
    
    elif args.command == "stop":
        bus.stop()
    
    elif args.command == "status":
        status = bus.get_sync_state()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    elif args.command == "subscribe":
        topics = [EventType(t.strip()) for t in args.topics.split(",")]
        sub = bus.subscribe(args.agent_id, topics)
        print(f"Subscribed {args.agent_id} to: {[t.value for t in topics]}")
    
    elif args.command == "unsubscribe":
        bus.unsubscribe(args.agent_id)
        print(f"Unsubscribed {args.agent_id}")
    
    elif args.command == "pending":
        events = bus.get_pending_events(args.agent_id)
        result = {
            "agent_id": args.agent_id,
            "count": len(events),
            "events": [e.to_dict() for e in events]
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "broadcast":
        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON payload")
            return
        
        try:
            event_type = EventType(args.event_type)
        except ValueError:
            print(f"Error: Unknown event type: {args.event_type}")
            print(f"Valid types: {[e.value for e in EventType]}")
            return
        
        targets = [t.strip() for t in args.targets.split(",")] if args.targets else []
        
        event = CollaborationEvent.create(
            event_type=event_type,
            source_agent=args.source,
            payload=payload,
            target_agents=targets,
            priority=args.priority
        )
        
        event_id = bus.publish(event, immediate=True)
        print(f"Event published: {event_id}")
    
    elif args.command == "ack":
        bus.acknowledge(args.event_id, args.agent_id)
        print(f"Event {args.event_id} acknowledged by {args.agent_id}")
    
    elif args.command == "sync":
        sync_manager = SyncManager(bus)
        result = sync_manager.perform_sync(args.agent_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
