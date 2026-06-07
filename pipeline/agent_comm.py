#!/usr/bin/env python3
"""
Agent 消息系统 —— 用于独立 Agent 之间的异步通信
角色通过 JSON 文件在共享目录中收发消息
"""
import json, os, time, uuid
from pathlib import Path

BASE = Path(__file__).parent / "data" / "agent_mailbox"
BASE.mkdir(parents=True, exist_ok=True)

def _normalize_role(role: str) -> str:
    """统一角色名大小写，防止同角色不同大小写导致消息走错目录"""
    if role.lower() == "ceo":
        return "CEO"
    return role.lower()


def send(to_role: str, from_role: str, msg_type: str, payload: dict, ref_id: str = None):
    """发一条消息给指定角色的 inbox"""
    to_role = _normalize_role(to_role)
    from_role = _normalize_role(from_role)
    msg = {
        "id": uuid.uuid4().hex[:12],
        "from": from_role,
        "to": to_role,
        "type": msg_type,       # task / reply / query / notify
        "payload": payload,
        "ref_id": ref_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "sent"
    }
    # 发送方先写一条到 sent 目录
    sent_dir = BASE / from_role / "sent"
    sent_dir.mkdir(parents=True, exist_ok=True)
    (sent_dir / f"{msg['id']}.json").write_text(json.dumps(msg, ensure_ascii=False, indent=2))
    
    # 再复制到接收方的 inbox
    inbox_dir = BASE / to_role / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    (inbox_dir / f"{msg['id']}.json").write_text(json.dumps(msg, ensure_ascii=False, indent=2))
    
    return msg

def check_inbox(role: str):
    """查看指定角色的收件箱"""
    inbox = BASE / role / "inbox"
    if not inbox.exists():
        return []
    msgs = []
    for f in sorted(inbox.iterdir(), key=lambda p: p.stat().st_mtime):
        if f.suffix == ".json":
            msg = json.loads(f.read_text())
            msgs.append(msg)
    return msgs

def mark_done(msg_id: str, role: str, result: dict = None):
    """标记消息为已完成"""
    # 在 sent 目录中找到原消息
    for f in (BASE / role / "sent").iterdir():
        if f.suffix == ".json":
            msg = json.loads(f.read_text())
            if msg["id"] == msg_id:
                msg["status"] = "done"
                msg["result"] = result
                msg["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                f.write_text(json.dumps(msg, ensure_ascii=False, indent=2))
                # 给发送方回复
                send(msg["from"], msg["to"], "reply", {"result": result, "original_msg_id": msg_id}, ref_id=msg_id)
                return True
    return False

def get_message(role: str, msg_id: str):
    """获取特定消息"""
    inbox = BASE / role / "inbox"
    f = inbox / f"{msg_id}.json"
    if f.exists():
        return json.loads(f.read_text())
    return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 agent_comm.py send <to> <from> <type> <json_payload>")
        print("  python3 agent_comm.py inbox <role>")
        print("  python3 agent_comm.py done <role> <msg_id>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "send":
        to, fr, typ = sys.argv[2], sys.argv[3], sys.argv[4]
        payload = json.loads(sys.argv[5]) if len(sys.argv) > 5 else {}
        msg = send(to, fr, typ, payload)
        print(json.dumps(msg, ensure_ascii=False, indent=2))
    elif cmd == "inbox":
        msgs = check_inbox(sys.argv[2])
        print(json.dumps(msgs, ensure_ascii=False, indent=2))
