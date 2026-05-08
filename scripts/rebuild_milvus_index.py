"""重建 Milvus 向量索引

从 MongoDB 的 literature_chunks 集合读取文档，
使用 BGE-M3 生成向量，存入 Milvus Lite。

Run:
    # 1. 确保 MongoDB 已启动:
    scripts/start_mongodb.bat

    # 2. 运行重建:
    cd cucumber-irrigation
    uv run --extra rag python scripts/rebuild_milvus_index.py
"""

import sys
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("Milvus 向量索引重建")
print("=" * 60)

# ===== 检查依赖 =====
try:
    from pymilvus import (
        connections, utility, Collection,
        CollectionSchema, FieldSchema, DataType
    )
    from pymilvus.model.hybrid import BGEM3EmbeddingFunction
    from pymongo import MongoClient
except ImportError as e:
    print(f"✗ 缺少依赖: {e}")
    print("运行: uv pip install pymilvus FlagEmbedding pymongo")
    sys.exit(1)

# ===== 配置 =====
MILVUS_PATH = Path(__file__).parent.parent / "data" / "index" / "milvus.db"
BGE_M3_PATH = Path("G:/Wyatt/Greenhouse_RAG/models/BAAI/bge-m3")
MONGO_URI = "mongodb://localhost:27017/"
COLLECTION_NAME = "greenhouse_bge_m3"
BATCH_SIZE = 50
MAX_TEXT_LENGTH = 512

# ===== 连接 MongoDB =====
print("\n[1] 连接 MongoDB...")
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command('ping')
    db = mongo_client["greenhouse_db"]
    chunks = db["literature_chunks"]
    total_docs = chunks.count_documents({})
    print(f"    ✓ MongoDB 已连接")
    print(f"    ✓ literature_chunks: {total_docs} 条记录")
except Exception as e:
    print(f"    ✗ MongoDB 连接失败: {e}")
    print("\n    请先启动 MongoDB:")
    print("    > scripts\\start_mongodb.bat")
    sys.exit(1)

# ===== 加载 BGE-M3 模型 =====
print("\n[2] 加载 BGE-M3 嵌入模型...")
if not BGE_M3_PATH.exists():
    print(f"    ✗ 模型路径不存在: {BGE_M3_PATH}")
    sys.exit(1)

try:
    print(f"    模型路径: {BGE_M3_PATH}")
    print("    ⏳ 加载模型 (首次可能需要几分钟)...")
    embedding_fn = BGEM3EmbeddingFunction(model_name=str(BGE_M3_PATH))
    print(f"    ✓ 模型加载成功")
    print(f"    ✓ 向量维度: {embedding_fn.dim}")
except Exception as e:
    print(f"    ✗ 模型加载失败: {e}")
    sys.exit(1)

# ===== 初始化 Milvus =====
print("\n[3] 初始化 Milvus Lite...")
MILVUS_PATH.parent.mkdir(parents=True, exist_ok=True)

try:
    connections.connect(uri=str(MILVUS_PATH))
    print(f"    ✓ Milvus Lite 连接: {MILVUS_PATH}")

    # 删除旧集合
    if utility.has_collection(COLLECTION_NAME):
        Collection(COLLECTION_NAME).drop()
        print(f"    ✓ 删除旧集合: {COLLECTION_NAME}")

    # 创建新集合
    fields = [
        FieldSchema(name="unique_id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=MAX_TEXT_LENGTH),
        FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
        FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=embedding_fn.dim["dense"]),
    ]
    schema = CollectionSchema(fields)
    collection = Collection(COLLECTION_NAME, schema, consistency_level="Strong")
    print(f"    ✓ 创建集合: {COLLECTION_NAME}")

    # 创建索引
    collection.create_index("sparse_vector", {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "IP"})
    collection.create_index("dense_vector", {"index_type": "AUTOINDEX", "metric_type": "IP"})
    print(f"    ✓ 创建索引完成")

except Exception as e:
    print(f"    ✗ Milvus 初始化失败: {e}")
    sys.exit(1)

# ===== 批量索引文档 =====
print("\n[4] 索引文档...")
print(f"    批次大小: {BATCH_SIZE}")

batch_texts = []
batch_ids = []
indexed_count = 0
skipped_count = 0

cursor = chunks.find({})
for doc in cursor:
    unique_id = doc.get("unique_id", "")
    content = doc.get("page_content", "")

    if not unique_id or not content:
        skipped_count += 1
        continue

    # 截断文本
    text = content[:MAX_TEXT_LENGTH]

    batch_texts.append(text)
    batch_ids.append(unique_id[:100])  # 截断 ID

    # 批量处理
    if len(batch_texts) >= BATCH_SIZE:
        try:
            embeddings = embedding_fn(batch_texts)
            entities = [
                batch_ids,
                batch_texts,
                embeddings["sparse"],
                embeddings["dense"],
            ]
            collection.insert(entities)
            indexed_count += len(batch_texts)
            print(f"    已索引: {indexed_count}/{total_docs} ({100*indexed_count/total_docs:.1f}%)")
        except Exception as e:
            print(f"    ⚠ 批次索引失败: {e}")
            skipped_count += len(batch_texts)

        batch_texts = []
        batch_ids = []

# 处理剩余批次
if batch_texts:
    try:
        embeddings = embedding_fn(batch_texts)
        entities = [
            batch_ids,
            batch_texts,
            embeddings["sparse"],
            embeddings["dense"],
        ]
        collection.insert(entities)
        indexed_count += len(batch_texts)
    except Exception as e:
        print(f"    ⚠ 最后批次索引失败: {e}")
        skipped_count += len(batch_texts)

# ===== 完成 =====
collection.load()
print(f"\n{'='*60}")
print(f"索引完成!")
print(f"{'='*60}")
print(f"  成功索引: {indexed_count} 条")
print(f"  跳过: {skipped_count} 条")
print(f"  集合实体数: {collection.num_entities}")
print(f"  Milvus 文件: {MILVUS_PATH}")

# 测试检索
print("\n[5] 测试检索...")
try:
    from pymilvus import AnnSearchRequest, RRFRanker

    test_query = "黄瓜灌溉 作物系数 Kc"
    query_embeddings = embedding_fn.encode_queries([test_query])

    results = collection.hybrid_search(
        [
            AnnSearchRequest(
                [query_embeddings["sparse"][[0]]],
                "sparse_vector",
                {"metric_type": "IP"},
                limit=3,
            ),
            AnnSearchRequest(
                [query_embeddings["dense"][0]],
                "dense_vector",
                {"metric_type": "IP"},
                limit=3,
            ),
        ],
        rerank=RRFRanker(),
        limit=3,
        output_fields=["unique_id", "text"],
    )[0]

    print(f"    查询: {test_query}")
    print(f"    结果数: {len(results)}")
    for i, r in enumerate(results, 1):
        print(f"    [{i}] {r.get('text', '')[:80]}...")

except Exception as e:
    print(f"    ✗ 测试检索失败: {e}")

print("\n✓ 索引重建完成! 现在可以运行:")
print("  uv run --extra rag python scripts/run_weekly_real.py")
