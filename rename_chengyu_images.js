const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

// 定义目录和文件路径
const imageDir = './chengyu_images';
const mappingFile = './chengyu_uuid_mapping.json';

// 主函数
async function renameImages() {
  try {
    console.log('开始处理图片文件...');
    
    // 读取目录中的所有文件
    const files = fs.readdirSync(imageDir);
    
    // 过滤出图片文件 (jpg, png等)
    const imageFiles = files.filter(file => {
      const ext = path.extname(file).toLowerCase();
      return ['.jpg', '.png', '.jpeg', '.gif'].includes(ext);
    });
    
    console.log(`找到 ${imageFiles.length} 个图片文件`);
    
    // 用于存储映射关系
    const mapping = {};
    
    // 处理每个图片文件
    for (const file of imageFiles) {
      // 提取成语名称（文件名去除扩展名）
      const chengyu = path.basename(file, path.extname(file));
      
      // 生成UUID
      const uuid = uuidv4();
      
      // 获取文件扩展名
      const ext = path.extname(file);
      
      // 新文件名
      const newFilename = `${uuid}${ext}`;
      
      // 重命名文件
      fs.renameSync(
        path.join(imageDir, file),
        path.join(imageDir, newFilename)
      );
      
      // 记录映射关系
      mapping[uuid] = chengyu;
      
      console.log(`已重命名: ${file} -> ${newFilename}`);
    }
    
    // 将映射关系写入JSON文件
    fs.writeFileSync(mappingFile, JSON.stringify(mapping, null, 2), 'utf8');
    
    console.log(`处理完成，共重命名 ${Object.keys(mapping).length} 个文件`);
    console.log(`映射关系已保存至: ${mappingFile}`);
    
  } catch (error) {
    console.error('处理过程中出错:', error);
  }
}

// 运行主函数
renameImages(); 