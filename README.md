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

修改了 mkdocs-with-pdf 以导出不同的章节，具体配置见 `mkdocs.yml` 中 `with-pdf: jobs` 节

```bash
ENABLE_PDF_EXPORT=1 mkdocs build
```


## Bug List

###### Navigation on Different Language

The existing version of the website has some bugs in the navigation bar. Simply put, when switching languages, only the page changes, and the navigation bar does not change to a different language.
The simplest solution to this problem can be found at:
1. https://squidfunk.github.io/mkdocs-material/plugins/projects/ 
2. https://squidfunk.github.io/mkdocs-material/setup/building-an-optimized-site/#built-in-projects-plugin
But we do not have the required "insider" identity, so we will not consider it for now.

For a less elegant solution, you can refer to this discussion and case:
1. https://github.com/squidfunk/mkdocs-material/discussions/2346
2. https://github.com/berkantsahn/mkdocs-sample/tree/main
But we cannot use two languages ​​at the same time in `mkdocs serve`, which is a great discovinent while developing this site, we need to deploy and test in the actual scenario.

This bug will be left for later reconfiguration.