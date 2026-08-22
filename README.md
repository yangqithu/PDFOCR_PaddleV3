# PDFOCR PaddleV3

基于 PaddleOCR 3 的 PDF OCR 桌面工具，为扫描版 PDF 添加可搜索、可复制的隐藏文字层，并通过版面分析减少页眉、页脚和页码对正文识别的干扰。v32 在 v31 的速度与显存优化基础上，加入倾斜校正、竖排文字模式和低分辨率文档强化检测。

*A Windows-oriented GUI and CLI tool that adds a searchable OCR text layer to scanned PDFs, with layout-aware filtering, skew correction, and opt-in vertical-text support.*

> [!IMPORTANT]
> 当前发布的是 **v32 源代码版本**。横排文字继续使用稳定默认流程；竖排文档需要手动启用 `-V` / `--vertical`。程序会自动选择 `gpu:0` 或 CPU，但 CPU 模式可能慢一个数量级，因此仍强烈推荐 NVIDIA GPU 及匹配的 PaddlePaddle GPU 环境。模型、CUDA 和 EXE 不包含在仓库中。

详细版本变化见 [CHANGELOG.md](CHANGELOG.md)。

![PDFOCR PaddleV3 主界面](docs/images/main-interface.png)

## 项目特点

- **图形界面与命令行双模式**：不带参数启动时打开 Tkinter 桌面界面，带文件参数时进入 CLI 批处理。
- **扫描件文字层写入**：在保留原 PDF 视觉内容的基础上写入隐藏文字，使扫描件可以搜索和复制。
- **更快的版面分析**：默认使用独立版面检测模型分析正文边界，减少重复 OCR；必要时可切回 PP-StructureV3。
- **原生 PDF 检测**：抽样判断文档是否已有矢量文字层，并选择清理页边元素或跳过不必要的 OCR。
- **奇偶页分别拟合**：分别估计左右页的边界，适应书籍装订线和不对称页边距。
- **中文标点宽度调整**：压缩常见全角标点的文字层占位宽度，改善横排文字层与原图的贴合程度。
- **批量处理**：支持多文件、文件夹递归选择、指定输出目录以及同名文件自动编号。
- **局部处理**：图形界面支持指定单页或连续物理页码范围，如 `5` 或 `5-10`。
- **双联页拆分**：可自动寻找书籍跨页中缝，也可按固定比例切分；支持跳过指定页面和从右向左排列。
- **显存与内存优化**：限制超大图像尺寸，版面分析完成后及时释放模型，并按间隔回收资源。
- **性能诊断**：可输出各阶段耗时、GPU 状态和显存信息，便于排查速度或设备问题。
- **倾斜文字层校正**：默认根据 OCR 四点框校正文字层角度；异常时可关闭或调整角度上限。
- **竖排文字模式**：支持自上而下、自右向左的中日韩竖排文字层，必须由用户手动开启。
- **强化检测**：提供 150、220、300 DPI 与“300 DPI 强化检测”档，并支持低分辨率文档的多尺度扫描和检测阈值调整。
- **多语种识别**：界面内置中英文、繁体中文、日文、韩文、法文、德文等常用模型代码，也支持手动输入 PaddleOCR 语言代码。
- **改进图形界面**：高级选项区域可滚动，参数块对齐并提供悬停说明；顶部控件不会再因长提示文字被压缩。
- **设备与打包自检**：自动探测 GPU/CPU，提供 `--selftest` 检查模型、依赖和推理引擎，并为后续 Windows 打包准备模型路径与 CUDA 获取逻辑。
- **资源清理**：处理过程中定期释放缓存，处理完成后主动释放模型引用、图像缓存、内存和 GPU 缓存。

## 适用范围

本项目主要用于：

- 只有扫描图像、无法搜索文字的书籍或论文 PDF；
- 页眉、页脚和页码容易混入 OCR 正文的文档；
- 需要批量生成 `原文件名-OCR.pdf` 的本地工作流；
- 需要检查文字识别置信度或生成纯文本辅助 PDF 的实验场景。

它不是 PDF 编辑器，也不保证恢复原文档的字体、段落结构、书签、表格语义或阅读顺序。

## 已知限制

- **竖排模式需要手动开启**：程序不会自动判断整份文档是否应按竖排处理。使用 `-V` 后会跳过横排版面边界分析，并按自右向左的列序写入。
- **低分辨率密排小字仍有明显漏识别**：测试中，大字正文可达到较高覆盖率，但双行小注召回率约为 32%，不适合要求文字层完整的场合。
- **特殊竖排页面仍可能漏识别**：超大字号扉页、连点目录、横竖混排和自身带页面旋转的 PDF，文字层仍可能缺漏或错位。
- **CPU 仅作为回退**：没有可用 NVIDIA GPU 时程序可以继续使用 CPU，但可能慢一个数量级，并使电脑长时间高负载。
- **首次运行依赖网络**：未提供本地模型目录时，PaddleOCR 会尝试下载所需模型。
- **复杂版式存在误判可能**：大幅插图、跨栏排版、边注、异形页面或损坏 PDF 可能导致正文边缘被错误过滤。
- **高 DPI 占用更多资源**：300 DPI 会明显增加显存、内存和处理时间。程序会对超大图像自动缩放，但大型 PDF 仍可能需要较多资源。
- **双联页会改变页数**：启用拆分后，普通跨页通常会变成两个输出页面；页码范围和跳过页码按拆分前的物理页计算。
- **双联页默认采用有损压缩**：拆分出的半页默认以 JPEG 质量 88 暂存，以降低内存占用；需要无损时请使用 `--split-lossless`。
- **原地覆写具有风险**：使用 `-I` 或界面的“原地覆写模式”前必须备份源文件。
- 当前发布源代码与使用说明，不提供 EXE、CUDA、PaddlePaddle 安装包或预下载模型。

## 系统要求

推荐环境：

- Windows 10/11 64 位；
- Python 3.10；
- 推荐支持 CUDA 的 NVIDIA GPU；无 GPU 时可回退 CPU，但速度很慢；
- 与显卡驱动和 CUDA 环境匹配的 `paddlepaddle-gpu`；
- 首次下载模型时可访问 PaddleOCR 模型源；
- 处理大型 PDF 时具备足够的显存、内存和磁盘空间。

本项目开发环境中已验证的主要版本如下：

| 组件 | 版本 |
| --- | --- |
| Python | 3.10.11 |
| paddlepaddle-gpu | 3.3.0 |
| paddleocr | 3.4.0 |
| PyMuPDF | 1.27.2.2 |
| opencv-contrib-python（由 PaddleOCR/PaddleX 安装） | 4.10.0.84 |
| Pillow | 12.1.1 |
| NumPy | 1.24.4 |
| tqdm | 4.67.3 |

其他版本可能可用，但尚未在本项目中验证。

## 安装

### 1. 获取源代码

可以在 GitHub 项目页选择 **Code → Download ZIP** 并解压，也可以使用 Git 克隆仓库。进入包含 `PDFOCR_PaddleV3.py` 的项目目录后继续下面的步骤。

### 2. 创建虚拟环境

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

如果 PowerShell 禁止运行激活脚本，也可以不激活环境，后续直接使用 `.\.venv\Scripts\python.exe`。

### 3. 安装 PaddlePaddle GPU

PaddlePaddle GPU 的安装命令取决于操作系统、显卡驱动和 CUDA 版本。请通过 [PaddlePaddle 官方安装页面](https://www.paddlepaddle.org.cn/install/quick) 选择与你的环境匹配的命令，不要盲目复制其他电脑的 GPU 安装命令。

本项目已验证过 `paddlepaddle-gpu==3.3.0`，但你仍需以官方安装选择器给出的索引地址和 CUDA 版本为准。

如果只能安装 CPU 版 PaddlePaddle，v32 会自动回退到 CPU 并给出提醒，但这只是兼容路径，不适合大型 PDF 或高精度批处理。

安装后检查 Paddle 是否识别 CUDA：

```powershell
python -c "import paddle; print(paddle.__version__); print(paddle.device.is_compiled_with_cuda())"
```

最后一项应输出 `True`。

### 4. 安装项目依赖

```powershell
python -m pip install -r requirements.txt
python -m pip check
```

版面检测和 PP-StructureV3 兼容路径属于 PaddleOCR 的文档解析能力，因此依赖文件使用了 `paddleocr[doc-parser]`。可参考 [PaddleOCR 官方安装文档](https://www.paddleocr.ai/latest/version3.x/installation.html)。

PaddleOCR/PaddleX 会安装提供 cv2 的 opencv-contrib-python。不要再同时安装 opencv-python，以免两个包争用同一模块。

> [!NOTE]
> 代码导入的是 PyMuPDF 提供的 `fitz` 模块。请安装 `PyMuPDF`，不要安装 PyPI 上另一个无关的 `fitz` 包。

## 图形界面使用

启动程序：

```powershell
python PDFOCR_PaddleV3.py
```

如果 Windows 已正确关联 `.py` 文件，也可以双击脚本启动。

1. 点击“选择文件”载入一个或多个 PDF，或点击“选择文件夹”递归载入其中的 PDF。
2. 可选：设置统一输出目录；未设置时输出到原文件所在目录。
3. 选择识别语种和扫描清晰度。一般文档建议先使用默认的 220 DPI；低分辨率密排小字可尝试“300 DPI 强化检测”，但显存占用约为 2.8 GB。
4. 可选：勾选指定处理页码并输入单页 `5` 或连续范围 `5-10`。
5. 如果原 PDF 每页包含左右两个书页，可勾选“双联页拆分 `-D`”。
6. 如果文档为自上而下、自右向左的竖排文本，可勾选“竖排文本 `-V`”。它会自动跳过横排版面过滤。
7. 检查高级选项；第一次使用建议保持默认。倾斜校正默认开启，高级选项区域可用鼠标滚轮查看，并可将鼠标停在选项上阅读完整说明。
8. 点击“启动识别序列”，等待处理完成。
9. 默认会自动打开处理完成的文档。

![完整界面与高级选项](docs/images/advanced-options.png)

> [!NOTE]
> 截图用于展示整体布局。v32 的高级选项区域可滚动并带悬停说明，新增竖排文本、关闭倾斜校正和多尺度深度扫描等选项；截图中的局部文字可能与最新版略有不同。

## 命令行使用

处理单个文件：

```powershell
python PDFOCR_PaddleV3.py "D:\PDF\input.pdf"
```

批量处理多个文件：

```powershell
python PDFOCR_PaddleV3.py "D:\PDF\book-a.pdf" "D:\PDF\book-b.pdf"
```

指定统一输出目录：

```powershell
python PDFOCR_PaddleV3.py "D:\PDF\book-a.pdf" "D:\PDF\book-b.pdf" -o "D:\PDF\OCR-results"
```

选择语言并生成置信度显影结果：

```powershell
python PDFOCR_PaddleV3.py "D:\PDF\input.pdf" -l en -g
```

拆分双联页并输出分段耗时：

```powershell
python PDFOCR_PaddleV3.py "D:\PDF\book.pdf" -D --timing
```

处理竖排文档并启用五尺度深度扫描：

```powershell
python PDFOCR_PaddleV3.py "D:\PDF\vertical-book.pdf" -V --multi-scale 5
```

按 300 DPI 渲染，并提高文字检测输入上限：

```powershell
python PDFOCR_PaddleV3.py "D:\PDF\faint-scan.pdf" --dpi 300 --max-pixels 3800 --det-limit 2800
```

命令行参数：

| 参数 | 作用 |
| --- | --- |
| `input_files` | 一个或多个输入 PDF 文件，必填 |
| `-o`, `--outdir` | 指定统一输出目录 |
| `-p`, `--pure` | 额外生成纯白背景的文字版辅助 PDF |
| `-c`, `--cv` | 显示 OpenCV 处理窗口 |
| `-n`, `--no-ocr` | 跳过 OCR，用于清理已有文字层等场景 |
| `-l`, `--lang` | 设置 PaddleOCR 语言代码，默认 `ch` |
| `-I`, `--inplace` | 直接向源 PDF 写入文字层，使用前必须备份 |
| `-P`, `--pixmap` | 强制使用页面光栅化结果进行分析 |
| `-g`, `--debug` | 将文字层按识别置信度着色显示 |
| `-S`, `--skip-layout` | 关闭智能页边过滤，对完整页面执行 OCR |
| `-D`, `--split-double-page` | 将每个物理页拆分为左右两个页面 |
| `--split-ratio` | 中缝自动检测失败时使用的固定切分比例 |
| `--split-fixed` | 不自动寻找中缝，始终按固定比例切分 |
| `--split-window` | 自动寻找中缝时，相对页面中心的搜索范围 |
| `--split-gap` | 切分时从中缝两侧各去掉的像素数 |
| `--split-skip` | 不拆分的物理页，如 `1,4-6` |
| `--split-quality` | 拆分半页的 JPEG 暂存质量，默认 `88` |
| `--split-lossless` | 拆分半页使用无损暂存，内存和文件体积会增加 |
| `--split-rtl` | 拆分后先输出右半页，适合从右向左翻阅的书籍 |
| `--split-dpi` | 双联页拆分时的渲染 DPI |
| `--skip-cuda-fetch` | 轻量打包版中跳过首次 CUDA 运算库获取；源码运行时通常无需使用 |
| `--det-limit` | 文字检测图像的最大边长，默认 `1600`；`0` 表示不限制 |
| `--layout-engine` | 选择版面分析引擎；可切换到兼容的 `v3` 路径 |
| `--timing` | 输出各处理阶段耗时和设备诊断信息 |
| `--legacy-text` | 使用旧版逐字符文字层写入方式 |
| `--gc-interval` | 每处理多少页执行一次资源回收，默认 `10` |
| `--dpi` | 设置主识别渲染 DPI，默认 `220` |
| `--max-pixels` | 设置渲染图像长边上限，程序硬上限为 `4000` |
| `--det-thresh` | 设置 DB 二值化阈值；降低后可保留更淡的笔画 |
| `--det-box-thresh` | 设置 DB 检测框保留阈值；降低后可保留较弱的文字框 |
| `--multi-scale` | 使用 1、3、5 或 7 个邻近尺度重复检测并合并；裸参数等于 `5`，耗时约按尺度数增加 |
| `-V`, `--vertical` | 按自上而下、自右向左的竖排模式处理，并自动等效于 `-S` |
| `--no-skew` | 关闭默认启用的文字层倾斜校正 |
| `--skew-max` | 设置可接受的倾斜角度上限，默认 `30` 度 |
| `--selftest` | 执行打包环境自检，检查模型缓存、依赖、设备和三个推理引擎 |

指定 OCR 页码范围目前仍是图形界面功能，没有对应的命令行参数。主识别 DPI、最大像素、双联页跳过页码与拆分 DPI 均可通过命令行设置。

## 高级选项

- **原地覆写模式 `-I`**：直接修改源 PDF。请先复制备份；一般不建议首次使用时开启。
- **纯净文本模式 `-p`**：额外生成一份白色背景、只显示识别文字的辅助 PDF。
- **色彩置信度显影 `-g`**：以可见颜色写入文字，便于检查置信度和对齐情况，不适合作为最终隐藏文字层版本。
- **关闭页边滤除 `-S`**：跳过版面边界分析，扫描整页；适用于页边过滤误删正文的文档。
- **擦除矢量层 `-n`**：跳过 OCR，用于清理旧的识别文字层等实验用途。
- **光栅化页面渲染 `-P`**：将页面按像素渲染后再识别，适合图层损坏或难以提取原始图片的 PDF，但资源消耗更高。
- **双联页拆分 `-D`**：适合一张 PDF 页面同时包含左右两个书页的扫描件。默认自动寻找中缝；识别不稳定时可使用固定比例。
- **分段计时 `--timing`**：报告拆分、版面分析、文字检测、文字写入等阶段耗时，并显示可用的 GPU/显存信息。
- **文字检测边长 `--det-limit`**：默认将检测输入的最大边长限制为 1600 像素，通常更快、更省显存；小字很多时可以适当提高。
- **兼容版面引擎 `--layout-engine v3`**：默认快速版面引擎异常时，可切回 PP-StructureV3 路径进行对照。
- **旧版文字写入 `--legacy-text`**：默认写入方式更快；若个别文档的文字层表现异常，可以用此参数对比旧方法。
- **竖排文本 `-V`**：按列写入文字层，并把列序改为自右向左。此模式必须手动开启，同时会跳过横排版面过滤。
- **关闭倾斜校正 `--no-skew`**：倾斜校正默认启用；若某份文档的文字层角度异常，可关闭后与旧水平写入方式对比。
- **多尺度深度扫描 `--multi-scale`**：针对低分辨率、淡字或密排小字重复检测。它只能改善部分漏检，不能突破识别模型对模糊小字的能力上限。
- **检测阈值 `--det-thresh` / `--det-box-thresh`**：降低阈值可保留更多淡笔画和弱框，也可能增加噪声；建议只在普通设置明显漏字时调整。

## 输出规则

- 默认输出文件名为 `原文件名-OCR.pdf`。
- 如果目标名称已经存在，程序会自动生成 `原文件名-OCR(1).pdf`、`原文件名-OCR(2).pdf`，避免覆盖旧结果。
- 指定输出目录不存在时，程序会自动创建。
- 原生文字 PDF 会先经过抽样检测；具体行为取决于是否启用了页边过滤。
- 原地覆写模式的保存位置与普通输出模式不同，请在处理后查看界面或终端报告。

## 识别效果检查

下图展示了置信度显影模式，用于观察文字层位置、字号和识别可靠度。它是调试视图，不代表最终隐藏文字层的颜色。

![置信度显影示例](docs/images/recognition-preview.png)

建议完成后检查：

- 搜索正文中的多个关键词；
- 复制一段文字并确认顺序；
- 放大查看页眉、页脚、脚注和页码附近；
- 检查中英文混排及全角标点；
- 检查奇偶页正文边界是否一致。
- 竖排文档检查列序是否自右向左、复制顺序是否正确；
- 倾斜扫描件放大检查隐藏文字层是否跟随原图角度。

## 常见问题

### `ModuleNotFoundError: No module named 'fitz'`

安装的是 `PyMuPDF`：

```powershell
python -m pip uninstall fitz
python -m pip install --force-reinstall PyMuPDF
```

### Paddle 报告未编译 CUDA，或程序无法使用 `gpu:0`

v32 会自动回退到 CPU 并显示提醒，但速度可能慢一个数量级。需要正常 GPU 速度时，请根据 [PaddlePaddle 官方安装页面](https://www.paddlepaddle.org.cn/install/quick) 重新安装与显卡驱动和 CUDA 匹配的 GPU 版本。

### 首次运行提示无法访问模型源

确认网络可以访问 PaddleOCR 支持的模型源。模型下载完成后会保存在本机缓存中；本仓库不会提交这些模型文件。

### 显存不足或处理速度过慢

先在图形界面降低为 150 或 220 DPI，并缩小指定页码范围。保持默认文字检测边长限制；命令行可用 `--det-limit 1280` 进一步降低占用。关闭不必要的调试窗口，避免同时运行其他 GPU 程序。使用 `--timing` 可以查看各阶段耗时和设备状态。

### 双联页中缝检测不准确

先尝试 `--split-fixed`，让程序按 `--split-ratio` 指定的固定比例切分。装订线偏离中心时可调整比例；不应拆分的封面、目录折页等页面可用 `--split-skip 1,4-6` 跳过。

### 页边过滤误删正文

尝试开启“关闭页边滤除 `-S`”，让程序扫描完整页面，然后人工检查页眉、页脚和页码是否被混入文字层。

### 竖排文字错位

确认已启用 `-V` / `--vertical`。该模式会按自上而下、自右向左写入，并自动跳过横排版面过滤。自身带 PDF 页面旋转、复杂横竖混排、超大字号扉页和连点目录仍可能异常。`--split-rtl` 只改变双联页左右两半的输出顺序，不能代替 `-V`。

### 低分辨率密排小字仍然大量漏识别

可以尝试“300 DPI 强化检测”或命令行 `--dpi 300 --max-pixels 3800 --det-limit 2800 --multi-scale 5`。这些选项会明显增加显存和处理时间，而且不能恢复源图中已经粘连或模糊的笔画。内部测试中双行小注召回率约为 32%，因此不应把强化模式理解为完整识别保证。

### 如何检查打包环境或模型是否完整

运行：

```powershell
python PDFOCR_PaddleV3.py --selftest
```

它会依次报告模型缓存路径、依赖元数据、Paddle 设备状态，并尝试实例化版面模型和 OCR 模型。该检查可能加载较大模型；首次缺少模型时仍可能需要网络。

## 隐私与数据

程序在本地读取和写入 PDF。模型首次下载需要网络，但项目代码没有上传用户 PDF 的功能。仍建议不要把私人 PDF、OCR 输出、模型缓存或日志提交到公开仓库；本项目的 `.gitignore` 已排除常见相关文件。

## 项目结构

```text
PDFOCR_PaddleV3/
├── PDFOCR_PaddleV3.py
├── README.md
├── CHANGELOG.md
├── requirements.txt
├── .gitignore
├── LICENSE
└── docs/
    ├── images/
    └── superpowers/
```

## 许可证与致谢

本项目代码按照 [GNU General Public License version 3](LICENSE) 发布。代码中保留的版权信息为：

- Copyright © 2025 Cao Yang
- Copyright © 2026 Yang Qi

本项目依赖 [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)、[PaddlePaddle](https://github.com/PaddlePaddle/Paddle)、[PyMuPDF](https://github.com/pymupdf/PyMuPDF)、[OpenCV](https://github.com/opencv/opencv) 等开源项目。各第三方组件继续适用其各自许可证。

## 发布状态

当前仓库提供可审阅和自行运行的 **v32 源代码版本**，不包含 EXE、CUDA、PaddlePaddle GPU 安装包或模型文件。源码已经加入模型路径、中文安装路径、GPU/CPU 探测、轻量打包版 CUDA 获取和 `--selftest` 等打包准备逻辑，但这些功能不等于已经提供可下载的 Windows 安装包。
