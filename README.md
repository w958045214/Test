# 表格文件合并工具（支持 Mac 交互页面）

现在提供两种使用方式：

1. **Web 交互页面（推荐，Mac 友好）**
2. 命令行（CLI）

## 1) Web 交互页面（Mac 推荐）

### 启动方式

```bash
python run_web_ui.py
```

启动后会自动打开浏览器，你也可以手动访问：

- <http://127.0.0.1:8000>

### 页面能力

- 上传多个 `CSV / XLSX / XLSM` 文件（至少 2 个）
- 选择输出格式（`CSV` 或 `XLSX`）
- 点击按钮后自动下载合并结果
- 自动校验表头一致性，不一致会在页面提示错误

## 2) 命令行方式（CLI）

```bash
python merge_tables.py -i 文件1.csv 文件2.xlsx 文件3.csv -o merged.xlsx
```

参数：

- `-i, --input`：输入文件列表（至少 2 个）
- `-o, --output`：输出文件路径（仅支持 `.csv` 或 `.xlsx`）

## 说明

- 输入支持：`.csv`、`.xlsx`、`.xlsm`
- 输出支持：`.csv`、`.xlsx`
- 如果处理 `xlsx/xlsm`，需要安装 `openpyxl`
