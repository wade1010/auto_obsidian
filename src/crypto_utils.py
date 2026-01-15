"""
加密工具模块
用于敏感数据的加密和解密
"""
import base64
import hashlib
import platform
import logging
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)


class CryptoManager:
    """加密管理器"""

    def __init__(self):
        """初始化加密管理器"""
        self._fernet = None
        self._init_encryption()

    def _init_encryption(self):
        """初始化加密器"""
        if not CRYPTO_AVAILABLE:
            logger.warning("cryptography 库未安装，将使用简单编码代替加密")
            return

        try:
            # 基于机器特征生成密钥
            # 这样同一台机器可以解密，但配置文件泄露到其他机器也无法解密
            machine_id = self._get_machine_id()

            # 使用 PBKDF2 生成密钥
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'auto_obsidian_salt',  # 固定 salt，确保同一台机器生成的密钥一致
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
            self._fernet = Fernet(key)
            logger.info("加密器初始化成功")
        except Exception as e:
            logger.error(f"加密器初始化失败: {e}")
            self._fernet = None

    def _get_machine_id(self) -> str:
        """获取机器唯一标识"""
        try:
            # 组合多个机器特征
            identifiers = [
                platform.node(),  # 计算机名
                platform.system(),  # 操作系统
                platform.machine(),  # 机器类型
                platform.processor(),  # 处理器信息
            ]

            # 尝试获取 MAC 地址
            try:
                import uuid
                mac = uuid.getnode()
                identifiers.append(str(mac))
            except:
                pass

            # 组合并哈希
            combined = ":".join(identifiers)
            return hashlib.sha256(combined.encode()).hexdigest()
        except Exception as e:
            logger.error(f"获取机器标识失败: {e}")
            return "default_machine_id"

    def encrypt(self, plaintext: str) -> str:
        """加密文本

        Args:
            plaintext: 明文

        Returns:
            加密后的文本（Base64编码）
        """
        if not plaintext:
            return ""

        # 如果 cryptography 不可用，使用简单的 Base64 编码
        if not CRYPTO_AVAILABLE or self._fernet is None:
            logger.warning("使用 Base64 编码代替加密")
            encoded = base64.b64encode(plaintext.encode()).decode()
            return f"encoded:{encoded}"

        try:
            encrypted = self._fernet.encrypt(plaintext.encode())
            return f"encrypted:{base64.urlsafe_b64encode(encrypted).decode()}"
        except Exception as e:
            logger.error(f"加密失败: {e}")
            return ""

    def decrypt(self, ciphertext: str) -> str:
        """解密文本

        Args:
            ciphertext: 密文（可能带有 encrypted: 或 encoded: 前缀）

        Returns:
            解密后的明文
        """
        if not ciphertext:
            return ""

        # 如果没有前缀，直接返回（向后兼容旧版本）
        if not ciphertext.startswith(("encrypted:", "encoded:")):
            logger.debug("未加密的 API key，直接返回")
            return ciphertext

        # 提取前缀后的内容
        prefix, content = ciphertext.split(":", 1)

        # 如果是 Base64 编码的（降级方案）
        if prefix == "encoded":
            try:
                decoded = base64.b64decode(content).decode()
                return decoded
            except Exception as e:
                logger.error(f"解码失败: {e}")
                return ""

        # 如果是加密的
        if prefix == "encrypted":
            if not CRYPTO_AVAILABLE or self._fernet is None:
                logger.error("无法解密：cryptography 不可用")
                return ""

            try:
                encrypted_data = base64.urlsafe_b64decode(content)
                decrypted = self._fernet.decrypt(encrypted_data)
                return decrypted.decode()
            except Exception as e:
                logger.error(f"解密失败: {e}")
                return ""

        return ""

    def is_available(self) -> bool:
        """检查是否可以使用加密"""
        return CRYPTO_AVAILABLE and self._fernet is not None


# 全局单例
_crypto_manager = None


def get_crypto_manager() -> CryptoManager:
    """获取加密管理器单例"""
    global _crypto_manager
    if _crypto_manager is None:
        _crypto_manager = CryptoManager()
    return _crypto_manager
