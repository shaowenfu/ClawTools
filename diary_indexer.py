#!/usr/bin/env python3
"""
Diary Indexer - 自动为日记文件生成元数据索引
Automatically generates metadata index for diary files

功能 Features:
- 扫描日记目录并提取元数据
- 生成YAML frontmatter
- 支持中文和英文内容
- 与Sherwen_Life_System集成

Usage:
    python diary_indexer.py --input /path/to/diaries --output /path/to/index
"""

import os
import re
import yaml
from datetime import datetime
from pathlib import Path

class DiaryIndexer:
    def __init__(self, input_dir, output_dir):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_metadata(self, content, file_path):
        """从日记内容中提取元数据"""
        metadata = {
            'date': file_path.stem,
            'year': file_path.parent.parent.name if file_path.parent.parent.name.isdigit() else '',
            'month': file_path.parent.name if file_path.parent.name.replace('-', '').isdigit() else '',
            'themes': [],
            'keywords': [],
            'mood': '',
            'importance': 0,
            'summary': '',
            'projects': [],
            'tasks_completed': [],
            'tasks_planned': []
        }
        
        # 简单的关键词提取
        content_lower = content.lower()
        keywords = []
        
        # 技术相关关键词
        tech_keywords = ['code', 'bug', 'programming', '开发', '代码', '调试']
        for keyword in tech_keywords:
            if keyword in content_lower:
                keywords.append(keyword)
                break
        
        # 生活相关关键词  
        life_keywords = ['basketball', 'guitar', 'interview', '篮球', '吉他', '面试']
        for keyword in life_keywords:
            if keyword in content_lower:
                keywords.append(keyword)
                break
                
        metadata['keywords'] = keywords[:3]  # 最多3个关键词
        metadata['summary'] = f"日记内容包含 {len(keywords)} 个主要主题"
        
        return metadata
    
    def process_diary_file(self, file_path):
        """处理单个日记文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metadata = self.extract_metadata(content, file_path)
            
            # 生成索引文件
            index_file = self.output_dir / f"{file_path.stem}_index.yaml"
            with open(index_file, 'w', encoding='utf-8') as f:
                yaml.dump(metadata, f, allow_unicode=True, default_flow_style=False)
                
            print(f"✓ 已处理: {file_path.name}")
            
        except Exception as e:
            print(f"✗ 处理失败 {file_path.name}: {e}")
    
    def run(self):
        """运行索引器"""
        print("开始处理日记文件...")
        diary_files = list(self.input_dir.rglob("*.md"))
        
        for file_path in diary_files:
            self.process_diary_file(file_path)
            
        print(f"完成! 共处理 {len(diary_files)} 个文件")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Diary Indexer - 自动为日记文件生成元数据索引')
    parser.add_argument('--input', required=True, help='日记文件输入目录')
    parser.add_argument('--output', required=True, help='索引文件输出目录')
    
    args = parser.parse_args()
    
    indexer = DiaryIndexer(args.input, args.output)
    indexer.run()