import sqlite3
import csv
import os

def export_idiom_to_csv(db_path, csv_path):
    """
    将SQLite数据库中的idiom表导出为CSV文件
    
    参数:
        db_path: SQLite数据库文件路径
        csv_path: 输出的CSV文件路径
    """
    # 确保输出目录存在
    output_dir = os.path.dirname(csv_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 连接到SQLite数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取表的所有数据
    cursor.execute("SELECT * FROM idiom")
    rows = cursor.fetchall()
    
    # 获取列名
    cursor.execute("PRAGMA table_info(idiom)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # 写入CSV文件
    with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        
        # 写入表头
        csv_writer.writerow(columns)
        
        # 写入数据行
        csv_writer.writerows(rows)
    
    # 关闭数据库连接
    conn.close()
    
    print(f"成功导出数据到 {csv_path}")
    print(f"共导出 {len(rows)} 条成语记录")

if __name__ == "__main__":
    # 设置数据库文件路径和输出CSV文件路径
    # 请根据实际情况修改这两个路径
    database_path = "chinese-idioms-12976.db"  # 替换为你的SQLite数据库文件路径
    output_csv_path = "chinese-idioms-12976.csv"  # 替换为你想要保存CSV的路径
    
    export_idiom_to_csv(database_path, output_csv_path)