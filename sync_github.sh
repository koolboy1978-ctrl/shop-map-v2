#!/bin/bash
# 自动同步到 GitHub

echo "正在同步到 GitHub..."

cd /Users/apple/WorkBuddy/20260405094656/图片提取

# 检查是否有更改
if [ -z "$(git status --porcelain)" ]; then
    echo "没有文件需要同步"
    exit 0
fi

# 显示更改的文件数量
count=$(git status --porcelain | wc -l)
echo "发现 $count 个文件更改"

# 推送到两个仓库（可选，如果需要同步到旧仓库）
echo "推送到 shop-map-v2..."
git push origin2 main

# 如果也需要推送到旧仓库（可选）
# git push origin main

echo "同步完成！"