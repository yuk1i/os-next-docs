# OS Next Docs

Shall be used in future semester.

> Perhaps

## Quick Start

Use `venv` and install dependencies：

```bash
# Create your own vrtuial environment
python3 -m venv venv
source venv/bin/activate

# Install dependenices
pip3 install -r requirements.txt
```

###### Previewing:

```bash
mkdocs serve
```

###### Build site：

```bash
mkdocs build
```

export pdf: ("really slow" says yuki)

> 修改了 mkdocs-with-pdf 以导出不同的章节，具体配置见 `mkdocs.yml` 中 `with-pdf: jobs` 节
```bash
ENABLE_PDF_EXPORT=1 mkdocs build
```

## TODO List

###### Message Board

Refered to:
1. https://squidfunk.github.io/mkdocs-material/setup/adding-a-comment-system/
> I'm not sure if it's because I'm not the owner of this repository, so I can't find where to turn on the repository Discussion feature.

## Bug List

###### Navigation on Different Language

The existing version of the website has some bugs in the navigation bar. Simply put, when switching languages, only the page changes, and the navigation bar does not change to a different language.
The simplest solution to this problem can be found at:
1. https://squidfunk.github.io/mkdocs-material/plugins/projects/ 
2. https://squidfunk.github.io/mkdocs-material/setup/building-an-optimized-site/#built-in-projects-plugin

But we do not have the required "insider" identity, so we will not consider this for now.

For a less elegant solution, we can refer to this discussion and this case:
1. https://github.com/squidfunk/mkdocs-material/discussions/2346
2. https://github.com/berkantsahn/mkdocs-sample/tree/main

But we cannot use two languages ​​at the same time in `mkdocs serve`, which is a great discovinent while developing this site.

This bug will be left for later reconfiguration.
