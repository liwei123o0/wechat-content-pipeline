#!/usr/bin/env python3
"""
微信公众号账号配置管理模块
支持多账号隔离，通过 --account 参数或环境变量切换

用法:
    from account_config import get_account, get_access_token, list_accounts

    # 获取指定账号配置
    cfg = get_account('guangyinpiano')
    token = get_access_token('guangyinpiano')

    # 命令行参数解析
    import argparse
    parser = argparse.ArgumentParser()
    add_account_arg(parser)
    args = parser.parse_args()
    cfg = get_account(args.account)
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

# 账号配置目录（使用实际用户 HOME，而非 Hermes 虚拟 HOME）
_USER_HOME = Path("/home/lw")
ACCOUNTS_DIR = _USER_HOME / ".wechat_accounts"
# 默认账号（当不指定时使用）
DEFAULT_ACCOUNT = "old"


def _list_config_files():
    """列出所有账号配置文件"""
    if not ACCOUNTS_DIR.exists():
        return []
    return sorted(ACCOUNTS_DIR.glob("*.json"))


def list_accounts():
    """列出所有可用公众号账号"""
    accounts = []
    for f in _list_config_files():
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
            accounts.append({
                "key": f.stem,
                "name": data.get("name", f.stem),
                "app_id": data.get("app_id", ""),
                "author": data.get("author", ""),
            })
        except Exception:
            accounts.append({"key": f.stem, "name": f.stem, "app_id": "?", "author": "?"})
    return accounts


def get_account(account_name=None):
    """
    获取指定账号的配置字典
    
    优先级：参数 > 环境变量 WECHAT_ACCOUNT > 默认 'old'
    
    返回:
        {
            "name": "光音谷piano",
            "app_id": "wx...",
            "app_secret": "...",
            "author": "光音谷",
            "key": "guangyinpiano"
        }
    """
    if account_name is None:
        account_name = os.environ.get("WECHAT_ACCOUNT", DEFAULT_ACCOUNT)

    account_name = account_name.strip().lower()
    
    config_path = ACCOUNTS_DIR / f"{account_name}.json"
    if not config_path.exists():
        available = [f.stem for f in _list_config_files()]
        print(f"❌ 账号 '{account_name}' 未找到配置")
        print(f"   可用账号: {', '.join(available)}")
        print(f"   提示: 创建 ~/.wechat_accounts/{account_name}.json 或使用已有账号")
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)

    data["key"] = account_name
    return data


def get_access_token(account_name=None, force_refresh=False):
    """
    获取微信 access_token
    
    支持缓存（token.json 按账号名隔离）
    返回 access_token 字符串，失败返回 None
    """
    cfg = get_account(account_name)
    account_key = cfg["key"]
    
    # token 缓存路径（按账号隔离）
    _user_home = Path("/home/lw")
    token_cache_dir = _user_home / ".wechat_accounts" / "tokens"
    token_cache_dir.mkdir(parents=True, exist_ok=True)
    token_cache_path = token_cache_dir / f"{account_key}.json"

    # 检查缓存是否有效
    if not force_refresh and token_cache_path.exists():
        try:
            with open(token_cache_path, encoding="utf-8") as f:
                cached = json.load(f)
            if cached.get("expire_at", 0) > time.time() + 60:  # 保留1分钟buffer
                return cached["access_token"]
        except Exception:
            pass

    # 刷新 token
    params = urllib.parse.urlencode({
        "grant_type": "client_credential",
        "appid": cfg["app_id"],
        "secret": cfg["app_secret"],
    })
    url = f"https://api.weixin.qq.com/cgi-bin/token?{params}"

    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ❌ token 请求失败: {e}")
        return None

    if "access_token" in result:
        token = result["access_token"]
        # 缓存
        with open(token_cache_path, "w", encoding="utf-8") as f:
            json.dump({
                "access_token": token,
                "expire_at": time.time() + result.get("expires_in", 7200),
                "account_key": account_key,
            }, f)
        print(f"  ✅ [{cfg['name']}] token 获取成功")
        return token
    else:
        print(f"  ❌ [{cfg['name']}] token 获取失败: {result}")
        if result.get("errcode") == 40164:
            print(f"  ⚠️  出口 IP 不在白名单，请登录公众号后台添加白名单")
        return None


def add_account_arg(parser):
    """为 argparse 添加 --account 参数"""
    accounts = list_accounts()
    choices = [a["key"] for a in accounts]
    default = os.environ.get("WECHAT_ACCOUNT", DEFAULT_ACCOUNT)
    
    parser.add_argument(
        "--account", "-a",
        default=default,
        choices=choices,
        help=f"公众号账号 (默认: {default}, 可用: {', '.join(choices)})"
    )


def http_request(url, data=None, method="GET", headers=None):
    """通用 HTTP 请求"""
    if data and isinstance(data, dict):
        data = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"errcode": e.code, "errmsg": body[:200]}
    except Exception as e:
        return {"errcode": -1, "errmsg": str(e)}


def verify_account(account_name=None):
    """验证账号配置是否正确（token 能否获取成功）"""
    cfg = get_account(account_name)
    print(f"📋 账号: {cfg['name']} (key: {cfg['key']})")
    print(f"   AppID: {cfg['app_id'][:10]}...{cfg['app_id'][-4:]}")
    print(f"   作者: {cfg.get('author', '未设置')}")
    
    token = get_access_token(cfg["key"], force_refresh=True)
    if token:
        print(f"   ✅ access_token: {token[:15]}...")
        
        # 额外验证：查询草稿箱数量
        url = f"https://api.weixin.qq.com/cgi-bin/draft/count?access_token={token}"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                draft_info = json.loads(resp.read().decode())
            count = draft_info.get("total_count", "?")
            print(f"   📝 草稿箱: {count} 篇")
        except Exception:
            pass
        
        return True
    return False


# ===== 便捷脚本入口 =====
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="微信公众号账号管理工具")
    parser.add_argument("action", nargs="?", default="list",
                        choices=["list", "verify", "token"],
                        help="操作: list=列出账号, verify=验证配置, token=获取token")
    add_account_arg(parser)
    args = parser.parse_args()

    if args.action == "list":
        print("📱 已配置的公众号账号:")
        print(f"{'KEY':<20} {'名称':<16} {'AppID':<22} {'作者':<12}")
        print("-" * 70)
        for a in list_accounts():
            print(f"{a['key']:<20} {a['name']:<16} {a['app_id']:<22} {a['author']:<12}")

    elif args.action == "verify":
        success = verify_account(args.account)
        sys.exit(0 if success else 1)

    elif args.action == "token":
        token = get_access_token(args.account, force_refresh=True)
        if token:
            print(token)
        else:
            sys.exit(1)
