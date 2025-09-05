#!/usr/bin/env python3
"""
艺术品CSV数据导入脚本
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.config import init_database, close_database
from artwork_retrieval.data_importer import ArtworkDataImporter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('artwork_import.log')
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    try:
        print("🎨 艺术品数据导入工具")
        print("=" * 50)
        
        # 检查CSV文件
        csv_file_path = "../../painting_info_with_descriptions.csv"
        
        if not os.path.exists(csv_file_path):
            print(f"❌ CSV文件不存在: {csv_file_path}")
            print("请确保CSV文件在正确的位置")
            return
        
        print(f"📁 CSV文件路径: {csv_file_path}")
        
        # 初始化数据库
        print("🔗 初始化数据库连接...")
        await init_database()
        
        # 创建导入器
        print("🚀 创建数据导入器...")
        importer = ArtworkDataImporter()
        await importer.initialize()
        
        # 执行导入
        print("📥 开始导入数据...")
        print("这可能需要几分钟时间，请耐心等待...")
        
        batch_size = 50  # 较小的批次大小以避免内存问题
        status = await importer.import_from_csv(csv_file_path, batch_size)
        
        # 显示结果
        print("\n" + "=" * 50)
        print("📊 导入结果:")
        print(f"状态: {status.status}")
        print(f"总记录数: {status.total_items}")
        print(f"已处理: {status.processed_items}")
        print(f"进度: {status.progress:.1%}")
        
        if status.error_message:
            print(f"错误信息: {status.error_message}")
        
        # 获取导入统计
        print("\n📈 导入统计:")
        stats = await importer.get_import_stats()
        
        if stats:
            print(f"总艺术品数: {stats.get('total_artworks', 0)}")
            print(f"总艺术家数: {stats.get('total_artists', 0)}")
            print(f"总文化数: {stats.get('total_cultures', 0)}")
            print(f"总部门数: {stats.get('total_departments', 0)}")
            print(f"平均流行度: {stats.get('avg_popularity', 0):.2f}")
            print(f"平均质量: {stats.get('avg_quality', 0):.2f}")
        
        if status.status == "completed":
            print("\n🎉 数据导入完成！")
        else:
            print(f"\n❌ 数据导入失败: {status.status}")
        
    except Exception as e:
        logger.error(f"导入过程发生错误: {e}")
        print(f"\n❌ 导入失败: {e}")
    
    finally:
        # 关闭数据库连接
        await close_database()
        print("\n🔚 数据库连接已关闭")


async def test_import_small_batch():
    """测试导入小批量数据"""
    try:
        print("🧪 测试模式：导入前100条记录")
        print("=" * 50)
        
        # 检查CSV文件
        csv_file_path = "../../painting_info_with_descriptions.csv"
        
        if not os.path.exists(csv_file_path):
            print(f"❌ CSV文件不存在: {csv_file_path}")
            return
        
        # 初始化数据库
        await init_database()
        
        # 创建导入器
        importer = ArtworkDataImporter()
        await importer.initialize()
        
        # 读取前100行进行测试
        import pandas as pd
        df = pd.read_csv(csv_file_path, nrows=100)
        
        # 保存为临时文件
        temp_csv = "temp_test_data.csv"
        df.to_csv(temp_csv, index=False)
        
        try:
            # 执行测试导入
            status = await importer.import_from_csv(temp_csv, batch_size=20)
            
            print(f"测试导入状态: {status.status}")
            print(f"处理记录数: {status.processed_items}")
            
            # 获取统计
            stats = await importer.get_import_stats()
            print(f"数据库中的艺术品总数: {stats.get('total_artworks', 0)}")
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_csv):
                os.remove(temp_csv)
        
    except Exception as e:
        logger.error(f"测试导入失败: {e}")
        print(f"❌ 测试失败: {e}")
    
    finally:
        await close_database()


async def check_database_status():
    """检查数据库状态"""
    try:
        print("🔍 检查数据库状态")
        print("=" * 50)
        
        await init_database()
        
        importer = ArtworkDataImporter()
        await importer.initialize()
        
        stats = await importer.get_import_stats()
        
        if stats:
            print("📊 当前数据库状态:")
            print(f"艺术品总数: {stats.get('total_artworks', 0)}")
            print(f"艺术家总数: {stats.get('total_artists', 0)}")
            print(f"文化总数: {stats.get('total_cultures', 0)}")
            print(f"部门总数: {stats.get('total_departments', 0)}")
        else:
            print("📊 数据库为空或查询失败")
        
    except Exception as e:
        logger.error(f"检查数据库状态失败: {e}")
        print(f"❌ 检查失败: {e}")
    
    finally:
        await close_database()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            asyncio.run(test_import_small_batch())
        elif command == "status":
            asyncio.run(check_database_status())
        elif command == "full":
            asyncio.run(main())
        else:
            print("使用方法:")
            print("  python import_csv_data.py test    # 测试导入前100条记录")
            print("  python import_csv_data.py status  # 检查数据库状态")
            print("  python import_csv_data.py full    # 完整导入所有数据")
    else:
        print("🎨 艺术品数据导入工具")
        print("=" * 50)
        print("使用方法:")
        print("  python import_csv_data.py test    # 测试导入前100条记录")
        print("  python import_csv_data.py status  # 检查数据库状态")
        print("  python import_csv_data.py full    # 完整导入所有数据")
        print("\n建议先运行 'test' 命令测试导入功能")
