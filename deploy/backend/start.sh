#!/bin/bash
# 智慧农业物联网平台启动脚本

cd "$(dirname "$0")"

# 检查授权文件
if [ ! -f ".policy" ]; then
    echo "错误: 未找到授权文件 (.policy)"
    echo "请联系发行方获取授权"
    exit 1
fi

if [ ! -f ".auth" ]; then
    echo "错误: 未找到公钥文件 (.auth)"
    exit 1
fi

# 启动后端
echo "正在启动智慧农业物联网平台..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
