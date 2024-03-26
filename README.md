## Developing Guide

使用 venv 环境并安装依赖：

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

本地开发：

```bash
mkdocs serve
```

导出静态页面：

```bash
mkdocs build
```

导出 pdf: (真的很慢)

```bash
ENABLE_PDF_EXPORT=1 mkdocs build
```