"""用户文献管理界面 (CLI)

P7-05: 用户文献管理界面
提供简单的文献管理 CLI 命令
"""

import argparse
from pathlib import Path
from typing import Optional

from loguru import logger


def create_parser() -> argparse.ArgumentParser:
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(
        prog="cucumber-rag",
        description="黄瓜灌溉知识库管理工具"
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # upload 命令
    upload_parser = subparsers.add_parser("upload", help="上传文献")
    upload_parser.add_argument("file", help="文件路径")
    upload_parser.add_argument("--title", "-t", help="文献标题")
    upload_parser.add_argument("--author", "-a", help="作者")
    upload_parser.add_argument(
        "--category", "-c",
        choices=["irrigation", "cucumber", "general"],
        default="general",
        help="文献类别"
    )

    # list 命令
    subparsers.add_parser("list", help="列出所有用户文献")

    # info 命令
    info_parser = subparsers.add_parser("info", help="查看文献详情")
    info_parser.add_argument("literature_id", help="文献 ID")

    # delete 命令
    delete_parser = subparsers.add_parser("delete", help="删除文献")
    delete_parser.add_argument("literature_id", help="文献 ID")
    delete_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制删除，不确认"
    )

    # rebuild 命令
    rebuild_parser = subparsers.add_parser("rebuild", help="重建文献索引")
    rebuild_parser.add_argument("literature_id", help="文献 ID")

    # stats 命令
    subparsers.add_parser("stats", help="查看索引统计")

    # search 命令
    search_parser = subparsers.add_parser("search", help="搜索知识库")
    search_parser.add_argument("query", help="查询文本")
    search_parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=5,
        help="返回结果数量"
    )
    search_parser.add_argument(
        "--source",
        choices=["all", "system", "user"],
        default="all",
        help="搜索范围"
    )

    return parser


def cmd_upload(args):
    """上传文献"""
    from .literature_api import LiteratureUploadService
    from .indexer import LiteratureIndexer

    indexer = LiteratureIndexer()
    service = LiteratureUploadService(indexer=indexer)

    try:
        literature_id = service.upload(
            file_path=args.file,
            title=args.title,
            author=args.author,
            category=args.category
        )
        print(f"✓ 上传成功")
        print(f"  文献 ID: {literature_id}")
        print(f"  标题: {args.title or Path(args.file).stem}")

    except FileNotFoundError as e:
        print(f"✗ 错误: {e}")
        return 1

    except ValueError as e:
        print(f"✗ 错误: {e}")
        return 1

    return 0


def cmd_list(args):
    """列出文献"""
    from .literature_api import LiteratureUploadService

    service = LiteratureUploadService()
    literature_list = service.list_user_literature()

    if not literature_list:
        print("暂无用户文献")
        return 0

    print(f"共 {len(literature_list)} 篇用户文献:\n")
    print(f"{'ID':<20} {'标题':<30} {'类别':<12} {'索引':<6}")
    print("-" * 70)

    for lit in literature_list:
        indexed = "✓" if lit.is_indexed else "✗"
        title = lit.title[:28] + ".." if len(lit.title) > 30 else lit.title
        print(f"{lit.literature_id:<20} {title:<30} {lit.category:<12} {indexed:<6}")

    return 0


def cmd_info(args):
    """查看文献详情"""
    from .literature_api import LiteratureUploadService

    service = LiteratureUploadService()
    lit = service.get_literature(args.literature_id)

    if lit is None:
        print(f"✗ 文献不存在: {args.literature_id}")
        return 1

    print(f"文献详情:")
    print(f"  ID: {lit.literature_id}")
    print(f"  标题: {lit.title}")
    print(f"  作者: {lit.author or '未知'}")
    print(f"  类别: {lit.category}")
    print(f"  格式: {lit.file_format}")
    print(f"  大小: {lit.file_size / 1024:.2f} KB")
    print(f"  分块数: {lit.chunk_count}")
    print(f"  已索引: {'是' if lit.is_indexed else '否'}")
    print(f"  上传时间: {lit.upload_time}")

    return 0


def cmd_delete(args):
    """删除文献"""
    from .literature_api import LiteratureUploadService

    service = LiteratureUploadService()

    # 确认删除
    if not args.force:
        lit = service.get_literature(args.literature_id)
        if lit is None:
            print(f"✗ 文献不存在: {args.literature_id}")
            return 1

        confirm = input(f"确认删除 '{lit.title}' (ID: {args.literature_id})? [y/N] ")
        if confirm.lower() != 'y':
            print("取消删除")
            return 0

    success = service.delete(args.literature_id)

    if success:
        print(f"✓ 文献已删除: {args.literature_id}")
        return 0
    else:
        print(f"✗ 删除失败: {args.literature_id}")
        return 1


def cmd_rebuild(args):
    """重建索引"""
    from .literature_api import LiteratureUploadService
    from .indexer import LiteratureIndexer

    service = LiteratureUploadService()
    lit = service.get_literature(args.literature_id)

    if lit is None:
        print(f"✗ 文献不存在: {args.literature_id}")
        return 1

    # 获取文件路径
    file_path = Path(service.config.upload_dir) / f"{args.literature_id}.{lit.file_format}"

    if not file_path.exists():
        print(f"✗ 文件不存在: {file_path}")
        return 1

    indexer = LiteratureIndexer()
    count = indexer.rebuild_index(args.literature_id, str(file_path))

    print(f"✓ 索引重建完成: {count} 个分块")
    return 0


def cmd_stats(args):
    """查看统计"""
    from .indexer import LiteratureIndexer
    from .retriever import MultiSourceRetriever

    indexer = LiteratureIndexer()
    retriever = MultiSourceRetriever()

    print("索引统计:")

    # 索引器统计
    indexer_stats = indexer.get_statistics()
    print(f"\n用户集合 ({indexer_stats['collection']}):")
    print(f"  可用: {'是' if indexer_stats['available'] else '否'}")
    print(f"  分块数: {indexer_stats['entity_count']}")

    # 检索器统计
    retriever_stats = retriever.get_collection_stats()
    print(f"\n系统集合:")
    print(f"  可用: {'是' if retriever_stats['system_available'] else '否'}")
    print(f"  分块数: {retriever_stats['system_count']}")

    return 0


def cmd_search(args):
    """搜索知识库"""
    from .retriever import MultiSourceRetriever

    retriever = MultiSourceRetriever()

    # 确定搜索范围
    if args.source == "all":
        sources = ["system", "user"]
    else:
        sources = [args.source]

    results = retriever.search(
        query=args.query,
        top_k=args.top_k,
        sources=sources
    )

    if not results:
        print("未找到相关结果")
        return 0

    print(f"找到 {len(results)} 条结果:\n")

    for i, result in enumerate(results, 1):
        print(f"[{i}] 分数: {result.score:.4f} | 来源: {result.source_type.value}")
        print(f"    ID: {result.doc_id}")
        content = result.content[:200] + "..." if len(result.content) > 200 else result.content
        print(f"    内容: {content}")
        print()

    return 0


def main():
    """主入口"""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    commands = {
        "upload": cmd_upload,
        "list": cmd_list,
        "info": cmd_info,
        "delete": cmd_delete,
        "rebuild": cmd_rebuild,
        "stats": cmd_stats,
        "search": cmd_search,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    exit(main())
