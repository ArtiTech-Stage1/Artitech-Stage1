#!/usr/bin/env python3
"""
批量修复认证导入的脚本
"""

import re

def fix_routes_file():
    """修复routes.py文件中的认证导入"""
    
    file_path = "user_management/routes.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换所有的get_current_user为get_current_user_simple
        content = re.sub(
            r'Depends\(get_current_user\)',
            'Depends(get_current_user_simple)',
            content
        )
        
        # 保存修改后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已修复 {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ 修复 {file_path} 失败: {e}")
        return False

if __name__ == "__main__":
    print("🔧 修复认证导入...")
    success = fix_routes_file()
    
    if success:
        print("🎉 修复完成！")
    else:
        print("❌ 修复失败！")
