"""
测试加密解密功能
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from src.crypto_utils import get_crypto_manager
except Exception as e:
    print(f"导入加密模块失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


def test_crypto():
    """测试加密解密功能"""
    print("=" * 60)
    print("测试加密解密功能")
    print("=" * 60)

    # 获取加密管理器
    try:
        crypto_manager = get_crypto_manager()
    except Exception as e:
        print(f"获取加密管理器失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 测试数据
    test_api_key = "sk-abc123def456ghi789jkl012mno345pq"

    print(f"\n原始 API Key: {test_api_key}")
    print(f"加密器可用: {crypto_manager.is_available()}")

    # 加密测试
    print("\n--- 加密测试 ---")
    encrypted = crypto_manager.encrypt(test_api_key)
    print(f"加密后: {encrypted}")

    # 解密测试
    print("\n--- 解密测试 ---")
    decrypted = crypto_manager.decrypt(encrypted)
    print(f"解密后: {decrypted}")

    # 验证结果
    print("\n--- 验证结果 ---")
    if decrypted == test_api_key:
        print("[OK] 加密解密测试成功!")
    else:
        print("[FAIL] 加密解密测试失败!")
        print(f"期望: {test_api_key}")
        print(f"实际: {decrypted}")

    # 测试向后兼容（未加密的数据）
    print("\n--- 向后兼容测试 ---")
    plain_key = "plain_api_key_12345"
    decrypted_plain = crypto_manager.decrypt(plain_key)
    print(f"未加密的 key: {plain_key}")
    print(f"解密结果: {decrypted_plain}")
    if decrypted_plain == plain_key:
        print("[OK] 向后兼容测试成功!")
    else:
        print("[FAIL] 向后兼容测试失败!")

    # 测试空值
    print("\n--- 空值测试 ---")
    empty_encrypted = crypto_manager.encrypt("")
    empty_decrypted = crypto_manager.decrypt("")
    print(f"空字符串加密: '{empty_encrypted}'")
    print(f"空字符串解密: '{empty_decrypted}'")
    if empty_encrypted == "" and empty_decrypted == "":
        print("[OK] 空值测试成功!")
    else:
        print("[FAIL] 空值测试失败!")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_crypto()
