# PDFOCR PaddleV3 GitHub 发布资料设计

## 目标

将 `PDFOCR-25-1标点宽度调整.py` 作为唯一正式程序，整理成一个可理解、可复现且不会误导使用者的 GitHub 源代码项目。当前阶段发布源代码、说明和截图，不打包模型或 Windows 可执行文件。

## 发布定位

- 项目名称：PDFOCR PaddleV3
- 主要受众：需要为扫描版 PDF 添加可搜索、可复制文字层的中文用户
- 文档语言：中文为主，README 开头提供简短英文说明
- 发布形态：源代码项目
- 主要运行环境：Windows、Python 3.9 及以上、NVIDIA GPU、匹配的 CUDA/PaddlePaddle GPU 环境
- 许可证：GPL-3.0，并保留代码中已有的 Cao Yang（2025）与 Yang Qi（2026）署名

## 真实性边界

README 只描述 25-1 已实现并能从代码中确认的能力：

- Tkinter 图形界面与命令行双入口
- 单文件、多文件和文件夹递归选择
- PaddleOCR 文本识别与 PP-StructureV3 版面分析
- 扫描 PDF 添加隐藏文字层
- 页眉、页脚和页码区域的智能过滤
- 原生文字 PDF 检测和分流处理
- 指定物理页码处理、输出目录和多档 DPI
- 中文标点宽度压缩，改善文字层对齐
- 纯文本、原地覆写、置信度显影、擦除旧文字层、光栅化及关闭页边过滤等高级模式
- 多语种模型选择、批量输出防重名和模型/显存清理

以下内容必须明确列为限制，不能包装成已完成能力：

- 竖排文字写入尚未解决，竖排或复杂旋转文本可能错位
- 代码将推理设备写死为 `gpu:0`，当前没有 CPU 自动回退
- 首次运行需要下载 PaddleOCR/PP-StructureV3 模型
- 模型、CUDA 和 PaddlePaddle GPU 环境不随 GitHub 仓库分发
- 原地覆写模式存在数据风险，必须先备份源 PDF
- 不承诺所有特殊字体、损坏 PDF、加密 PDF 或复杂版式均能正确处理

## 目录结构

```text
PDFOCR_PaddleV3/
├── PDFOCR_PaddleV3.py
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
└── docs/
    ├── images/
    │   ├── main-interface.png
    │   ├── advanced-options.png
    │   └── recognition-preview.png
    └── superpowers/
        └── specs/
            └── 2026-08-02-github-release-docs-design.md
```

原有 `images.docx` 仅作为截图来源，不进入最终 GitHub 发布目录。三张嵌入图片将以有意义的英文文件名提取到 `docs/images/`。

## README 结构

1. 项目名称、简短中英文定位和状态提示
2. 主界面截图
3. 项目简介与适用场景
4. 功能列表
5. 当前限制与风险警告
6. 系统要求
7. 环境安装
   - 创建 Python 虚拟环境
   - 按官方页面选择并安装匹配硬件/CUDA 的 PaddlePaddle 推理引擎
   - 安装 `paddleocr[doc-parser]` 和其余 Python 依赖
   - 说明模型首次运行自动下载
8. 图形界面使用方法
9. 命令行使用方法与参数示例
10. 高级选项说明
11. 输出文件和防覆盖规则
12. 常见问题
13. 项目结构
14. 许可证、作者署名和第三方项目致谢

安装部分不写死未经验证的 CUDA/PaddlePaddle GPU 安装命令，而是链接 PaddlePaddle 官方安装选择器；`requirements.txt` 记录通用 Python 依赖，PaddlePaddle 推理引擎单独安装。

## 配置文件

### requirements.txt

包含代码直接使用的通用依赖：PaddleOCR 的 `doc-parser` 可选依赖组、PyMuPDF、OpenCV、Pillow、NumPy 和 tqdm。PaddlePaddle GPU 不直接写入该文件，避免为不同显卡/CUDA 环境安装错误轮子。

### .gitignore

排除 Python 缓存、虚拟环境、构建目录、IDE 配置、Paddle 模型缓存、常见模型文件、用户 PDF、OCR 输出和临时文件。保留 `docs/images/*.png`。

### LICENSE

采用完整 GNU General Public License version 3 正文，与程序现有版权提示保持一致。

## 文件迁移

实施时先验证源文件和目标文件的大小、时间与 SHA-256。随后用 25-1 源文件替换当前误放的 25-2 版本，并保留统一发布文件名 `PDFOCR_PaddleV3.py`。替换后再次比较 SHA-256，确保目标内容与 25-1 完全一致。

## 验证标准

- `PDFOCR_PaddleV3.py` 与 25-1 源文件 SHA-256 完全一致
- Python AST 语法解析通过
- README 不出现“支持竖排文字”等错误表述
- README 的三张图片均能从相对路径打开
- README 中的 CLI 参数与代码实际参数一致
- 目录中不存在模型、私人 PDF、OCR 输出、缓存或密钥
- `.gitignore` 不会忽略项目截图和必要源码
- `requirements.txt` 中不出现错误的 `fitz` 包名
- Git 状态仅包含本次发布资料的预期文件

## 非目标

本次不修改 OCR 算法，不重新解决竖排文字，不增加 CPU 模式，不封装 EXE，不上传模型，不创建远程 GitHub 仓库，也不推送任何内容。远程发布将在本地资料审核通过后单独进行。
