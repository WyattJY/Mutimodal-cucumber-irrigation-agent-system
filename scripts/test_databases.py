"""测试 MongoDB 和 Milvus 连接

Run:
    # 1. 先在另一个终端启动 MongoDB:
    scripts/start_mongodb.bat

    # 2. 运行此脚本测试:
    cd cucumber-irrigation
    uv run --extra rag python scripts/test_databases.py
"""

import sys
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

print("=" * 60)
print("数据库连接测试")
print("=" * 60)

# ===== 测试 MongoDB =====
print("\n[1] 测试 MongoDB...")
try:
    from pymongo import MongoClient

    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    client.admin.command('ping')

    db = client["greenhouse_db"]
    chunks = db["literature_chunks"]
    count = chunks.count_documents({})

    print(f"    ✓ MongoDB 已连接")
    print(f"    ✓ literature_chunks 集合: {count} 条记录")

    # 显示示例
    sample = chunks.find_one()
    if sample:
        print(f"    ✓ 示例文档 ID: {sample.get('unique_id', 'N/A')[:50]}...")
        meta = sample.get('metadata', {})
        print(f"    ✓ 来源: {meta.get('source', 'unknown')}")

    mongo_ok = True
except Exception as e:
    print(f"    ✗ MongoDB 连接失败: {e}")
    print("\n    请先启动 MongoDB:")
    print("    > scripts\\start_mongodb.bat")
    mongo_ok = False

# ===== 测试 Milvus =====
print("\n[2] 测试 Milvus Lite...")
try:
    from pymilvus import connections, utility, Collection

    milvus_path = Path(__file__).parent.parent / "data" / "index" / "milvus.db"

    if not milvus_path.exists():
        print(f"    ✗ Milvus 数据库不存在: {milvus_path}")
        milvus_ok = False
    else:
        connections.connect(uri=str(milvus_path))

        collections = utility.list_collections()
        print(f"    ✓ Milvus Lite 已连接")
        print(f"    ✓ 可用集合: {collections}")

        if "greenhouse_bge_m3" in collections:
            col = Collection("greenhouse_bge_m3")
            col.load()
            print(f"    ✓ greenhouse_bge_m3 集合已加载")
            print(f"    ✓ 实体数量: {col.num_entities}")
        else:
            print("    ⚠ greenhouse_bge_m3 集合不存在，需要重建索引")

        milvus_ok = True
except ImportError:
    print("    ✗ pymilvus 未安装")
    print("    运行: uv pip install pymilvus")
    milvus_ok = False
except Exception as e:
    print(f"    ✗ Milvus 连接失败: {e}")
    milvus_ok = False

# ===== 测试 BGE-M3 模型 =====
print("\n[3] 测试 BGE-M3 嵌入模型...")
try:
    model_path = Path("G:/Wyatt/Greenhouse_RAG/models/BAAI/bge-m3")

    if not model_path.exists():
        print(f"    ✗ 模型路径不存在: {model_path}")
        model_ok = False
    else:
        print(f"    ✓ 模型路径存在: {model_path}")

        # 尝试加载模型
        try:
            from pymilvus.model.hybrid import BGEM3EmbeddingFunction

            print("    ⏳ 加载 BGE-M3 模型 (首次可能需要几分钟)...")
            embedding_fn = BGEM3EmbeddingFunction(model_name=str(model_path))

            # 测试编码
            test_query = "黄瓜灌溉水分管理"
            embeddings = embedding_fn.encode_queries([test_query])

            print(f"    ✓ 模型加载成功")
            print(f"    ✓ 稀疏向量维度: {embeddings['sparse'].shape}")
            print(f"    ✓ 稠密向量维度: {len(embeddings['dense'][0])}")
            model_ok = True
        except ImportError:
            print("    ⚠ FlagEmbedding 未安装，跳过模型测试")
            print("    运行: uv pip install FlagEmbedding")
            model_ok = False
        except Exception as e:
            print(f"    ✗ 模型加载失败: {e}")
            model_ok = False
except Exception as e:
    print(f"    ✗ 模型检查失败: {e}")
    model_ok = False

# ===== 总结 =====
print("\n" + "=" * 60)
print("测试结果总结")
print("=" * 60)
print(f"  MongoDB:  {'✓ OK' if mongo_ok else '✗ 失败'}")
print(f"  Milvus:   {'✓ OK' if milvus_ok else '✗ 失败'}")
print(f"  BGE-M3:   {'✓ OK' if model_ok else '⚠ 未测试/失败'}")

if mongo_ok and milvus_ok:
    print("\n✓ 数据库就绪！可以运行完整 RAG 演示:")
    print("  uv run --extra rag python scripts/run_weekly_real.py")
else:
    print("\n请解决上述问题后重试。")
