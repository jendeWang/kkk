"""
授权与运行状态管理模块
采用非对称签名 + 本地加密状态记录的组合方案
"""

import os
import json
import base64
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# 常量与路径（分散定义，避免敏感字符串集中出现）
# ---------------------------------------------------------------------------
_BASE = Path(__file__).resolve().parent.parent.parent  # backend/
_SIG_FILE = _BASE / ".auth"               # 公钥文件
_POLICY_FILE = _BASE / ".policy"          # 授权策略文件（License）
_STATE_FILE = _BASE / ".state"            # 加密运行状态记录

# 用于本地状态加密的派生盐（非密钥本身，每次运行时动态派生）
_SALT_SEED = b"\x4a\x91\xb3\x7e\x2f\xd8\x6c\x15"


# ---------------------------------------------------------------------------
# 内部辅助
# ---------------------------------------------------------------------------
def _derive_key(ts: int) -> bytes:
    """基于时间戳动态派生 AES-256 密钥，增加静态分析难度"""
    raw = hashlib.sha256(_SALT_SEED + str(ts).encode()).digest()
    return raw[:32]


def _obfuscate(data: bytes, key: bytes) -> bytes:
    """AES-256-CBC 加密，IV 随机"""
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    pad_len = 16 - (len(data) % 16)
    padded = data + bytes([pad_len]) * pad_len
    return iv + encryptor.update(padded) + encryptor.finalize()


def _deobfuscate(token: bytes, key: bytes) -> bytes:
    """AES-256-CBC 解密"""
    if len(token) < 16:
        raise ValueError("invalid token length")
    iv, payload = token[:16], token[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(payload) + decryptor.finalize()
    pad_len = padded[-1]
    return padded[:-pad_len]


def _load_verify_key() -> Optional[Any]:
    """加载 RSA 公钥（验签用）"""
    if not _SIG_FILE.exists():
        return None
    try:
        pem = _SIG_FILE.read_bytes()
        return serialization.load_pem_public_key(pem, backend=default_backend())
    except Exception:
        return None


def _load_policy() -> Optional[Dict[str, Any]]:
    """加载并初步解析授权策略文件"""
    if not _POLICY_FILE.exists():
        return None
    try:
        raw = _POLICY_FILE.read_text(encoding="utf-8")
        payload = json.loads(raw)
        return payload
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 核心校验逻辑
# ---------------------------------------------------------------------------
def _verify_integrity(payload: Dict[str, Any], pubkey: Any) -> bool:
    """RSA 签名验证"""
    try:
        content = payload.get("c")
        signature_b64 = payload.get("s")
        if not content or not signature_b64:
            return False
        signature = base64.b64decode(signature_b64)
        pubkey.verify(
            signature,
            content.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False


def _decode_content(content_b64: str) -> Optional[Dict[str, Any]]:
    """解码授权内容"""
    try:
        raw = base64.b64decode(content_b64)
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def _check_clock_rollback(issued_at: int) -> Tuple[bool, int]:
    """
    检查系统时间是否被回拨
    返回: (是否通过检查, 当前时间戳)
    """
    now = int(datetime.utcnow().timestamp())
    if not _STATE_FILE.exists():
        # 首次运行判断：授权签发 7 天内允许创建状态文件；
        # 超过 7 天仍无状态文件，视为被恶意删除
        if now - issued_at <= 7 * 86400:
            _persist_state(now)
            return True, now
        else:
            logger.warning("State file missing after grace period — possible tampering")
            return False, now

    try:
        token = _STATE_FILE.read_bytes()
        # 尝试用当前时间附近的时间戳派生密钥解密（允许 ±365 天正常停机）
        for delta in range(-365, 366):
            key = _derive_key(now + delta * 86400)
            try:
                plain = _deobfuscate(token, key)
                record = json.loads(plain.decode("utf-8"))
                last = record.get("t", 0)
                if now < last - 300:  # 允许 5 分钟时钟漂移
                    logger.warning("System clock rollback detected")
                    return False, now
                break
            except Exception:
                continue
        else:
            # 状态文件存在但无法解密 = 被篡改
            logger.warning("State file corrupted — possible tampering")
            return False, now
    except Exception:
        return False, now

    # 更新时间记录
    _persist_state(now)
    return True, now


def _persist_state(ts: int):
    """持久化加密运行状态"""
    key = _derive_key(ts)
    record = json.dumps({"t": ts}).encode("utf-8")
    _STATE_FILE.write_bytes(_obfuscate(record, key))


def _evaluate(content: Dict[str, Any], now_ts: int) -> Tuple[str, Dict[str, Any]]:
    """
    评估授权状态
    返回: (状态码, 信息字典)
    状态码: "active" | "readonly" | "expired" | "corrupted"
    """
    try:
        until = content.get("u")
        if not until:
            return "corrupted", {}
        expire_ts = int(until)
        if now_ts > expire_ts:
            grace = expire_ts + 7 * 86400  # 7 天宽限期（只读）
            if now_ts > grace:
                return "expired", content
            return "readonly", content
        return "active", content
    except Exception:
        return "corrupted", {}


# ---------------------------------------------------------------------------
# 对外接口
# ---------------------------------------------------------------------------
class AuthResult:
    """授权检查结果"""
    def __init__(self, status: str, info: Dict[str, Any]):
        self.status = status      # active / readonly / expired / corrupted / missing
        self.info = info
        self.school = info.get("n", "")
        self.max_devices = info.get("d", 0)
        self.expire_at = info.get("u", 0)

    @property
    def is_valid(self) -> bool:
        return self.status in ("active", "readonly")

    @property
    def can_write(self) -> bool:
        return self.status == "active"

    def readable_status(self) -> str:
        mapping = {
            "active": "授权有效",
            "readonly": "授权过期（只读模式）",
            "expired": "授权已失效",
            "corrupted": "授权文件损坏",
            "missing": "未找到授权文件",
        }
        return mapping.get(self.status, "未知状态")


def verify_system() -> AuthResult:
    """
    主入口：完整校验流程
    1. 加载公钥与策略
    2. 验签
    3. 防时间回拨
    4. 评估有效期
    """
    pubkey = _load_verify_key()
    if pubkey is None:
        logger.error("Verify key not found")
        return AuthResult("missing", {})

    payload = _load_policy()
    if payload is None:
        logger.error("Policy file not found")
        return AuthResult("missing", {})

    if not _verify_integrity(payload, pubkey):
        logger.error("Integrity check failed")
        return AuthResult("corrupted", {})

    content = _decode_content(payload.get("c", ""))
    if content is None:
        return AuthResult("corrupted", {})

    now_ts = int(datetime.utcnow().timestamp())
    issued_at = content.get("i", now_ts)
    ok, now_ts = _check_clock_rollback(issued_at)
    if not ok:
        return AuthResult("expired", content)

    status, info = _evaluate(content, now_ts)
    return AuthResult(status, info)


# FastAPI 依赖注入用
async def require_write_access():
    """需要写权限的 API 装饰器依赖"""
    from fastapi import HTTPException, status
    result = verify_system()
    if not result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"系统未授权或授权已失效: {result.readable_status()}",
        )
    if not result.can_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="授权已过期，当前仅支持只读访问，请联系管理员续期",
        )
