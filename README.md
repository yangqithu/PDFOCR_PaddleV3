# PDFOCR PaddleV3

PDFOCR 是一款面向 Windows 的本地 PDF OCR 工具。它可以给扫描版 PDF 写入可搜索、可复制的隐藏文字层，同时尽量保持原页面的图像、版式和字符位置不变。

当前稳定版：**v281**。推荐使用 NVIDIA 显卡的 Windows 10/11 用户下载已经打包好的 ZIP，无需安装 Python。

![PDFOCR 主界面](docs/images/main-interface.png)

## 为什么选择 PDFOCR

1. **大模型识别，准确率极高**
   使用 PP-OCRv5 server 级文字检测和识别模型。在清晰的印刷扫描件上通常可以获得很高的识别准确率；实际效果仍会受到扫描清晰度、字体和版式影响。

2. **多语种识别**
   支持简体中文、繁体中文、英文、日文、韩文、法文、德文等常用语种，也可以手动填写 PaddleOCR 支持的语言代码。

3. **页脚页眉滤除，方便跨页复制**
   程序会分析正文区域，尽量排除页眉、页脚和页码。连续复制多页内容时，能够减少页码和重复标题混入正文。

4. **排版严格对应原文字符位置**
   隐藏文字层依据识别框写入，并结合倾斜校正、中文标点宽度调整和 PDF CropBox 补偿，尽量让可选中的文字贴合原图字符位置。

5. **印刷体古籍及日语竖排文本识别**
   可在主页面开启“竖排文本识别”，按自上而下、自右向左的顺序处理竖排文字，适合印刷体古籍和日语竖排文本。该模式需要手动开启。

6. **完全免费，本地化大模型识别**
   使用百度提供开源Paddle大模型，本地化加载识别，安装完成后不需要任何联网或付费操作。

此外，PDFOCR 还支持批量处理、文件夹递归选择、指定页码范围、双联页拆分、低分辨率强化检测、处理耗时统计和离线运行。

## 一分钟开始使用（NVIDIA Windows 用户）

### 1. 下载 ZIP

点击下载：**[PDFOCR-v281-Windows-x64.zip](https://github.com/yangqithu/PDFOCR_PaddleV3/releases/latest/download/PDFOCR-v281-Windows-x64.zip)**

下载完成后，右键 ZIP，选择“全部解压”。请不要直接在压缩包预览窗口中运行程序，也不要只把 `PDFOCR.exe` 单独拖出来。

### 2. 启动软件

打开解压后的 `PDFOCR` 文件夹，双击 `PDFOCR.exe`。

程序每次启动都需要初始化 AI 引擎，可能会等待一段时间。窗口出现前请耐心等待，不要重复双击或强行关闭。

本软件目前没有代码签名。Windows SmartScreen 如果显示“Windows 已保护你的电脑”，请先确认文件来自本仓库的 Release 页面，再点击“更多信息”→“仍要运行”。也可以按照本文后面的校验方法核对 SHA256。

### 3. 一键下载 NVIDIA 运算库

发布包已经包含程序和四个基础模型，但为了控制下载体积，**没有内嵌 NVIDIA CUDA 运算库**。

第一次检测到运算库缺失时，程序会弹出说明窗口。确认下载后，程序才会联网获取约 2.2 GB 的固定版本组件，解压后约占 3.1 GB。默认会依次尝试清华大学镜像、北京外国语大学镜像和 PyPI，并在下载后校验文件大小和 SHA256。

请保持网络连接和足够磁盘空间。下载完成后按提示重新启动软件。你不需要另外安装完整的 CUDA Toolkit。

如果暂时不想下载，可以取消；程序不会在没有确认的情况下自动下载。

### 4. 可正常使用：完成一次识别

1. 点击“选择 PDF 文件”添加一个或多个扫描版 PDF；也可以选择文件夹批量导入。
2. 选择输出目录。未指定时，结果通常保存到原文件旁边，并命名为 `原文件名-OCR.pdf`。
3. 选择识别语言。中文资料一般使用简体中文；日语竖排资料应选择日语。
4. 选择清晰度。普通清晰扫描件建议先用 **220 DPI**；小字或模糊页面再尝试 300 DPI 或“300 DPI 强化检测”。
5. 如只处理部分页面，在“页码范围”中填写 `5` 或 `5-10`。这里使用 PDF 的物理页码，从封面页起作为第1页计数。
6. 如果是印刷体古籍或日语竖排文本，开启“竖排文本识别”；普通横排文档不要开启。
7. 根据需要勾选“完成时自动打开”，然后点击“开始处理”。

处理完成后，用任意 PDF 阅读器打开输出文件，即可搜索或选择复制文字。

## 下载文件

| 文件 | 用途 |
| --- | --- |
| [PDFOCR-v281-Windows-x64.zip](https://github.com/yangqithu/PDFOCR_PaddleV3/releases/latest/download/PDFOCR-v281-Windows-x64.zip) | **推荐下载**。完整解压后运行，便于保留程序目录结构 |
| [PDFOCR-v281-Windows-x64.exe](https://github.com/yangqithu/PDFOCR_PaddleV3/releases/latest/download/PDFOCR-v281-Windows-x64.exe) | 自解压安装包，与 ZIP 内容相同；运行后选择解压位置 |
| [PDFOCR-v281-source.py](https://github.com/yangqithu/PDFOCR_PaddleV3/releases/latest/download/PDFOCR-v281-source.py) | v281 单文件统一源码 |
| [SHA256SUMS.txt](https://github.com/yangqithu/PDFOCR_PaddleV3/releases/latest/download/SHA256SUMS.txt) | 发布文件的 SHA256 校验值 |

> ZIP 和自解压 EXE 二选一即可，不需要同时下载。仓库中的 `PDFOCR_PaddleV3.py` 与 Release 中的源码内容相同。

## 系统要求

- Windows 10/11 64 位；
- 推荐 NVIDIA 显卡，并安装较新的官方显卡驱动；
- 推荐至少 16 GB 内存、6 GB 显存；
- 首次准备 NVIDIA 运算库时，建议预留至少 6 GB 磁盘空间；
- 程序包本身已经包含四个基础 OCR 模型，不需要另行下载模型；
- 没有可用 NVIDIA GPU 时可以尝试 CPU 回退，但速度可能慢一个数量级，不适合大量文档。

## 主页面常用功能

### 添加文件与选择输出位置

- “选择 PDF 文件”可一次添加多个文件。
- “选择文件夹”可递归查找文件夹中的 PDF，适合批量处理。
- 输出目录留空时，结果写到源文件旁；指定目录后，所有结果集中保存。
- 同名输出文件已经存在时，程序会自动编号，避免直接覆盖。

### 识别语言

语言应与文档正文一致。中英混排通常可先选择简体中文模型；日文资料选择日语。选择错误的语言会显著降低识别质量。

### 清晰度档位

| 档位 | 建议用途 | 资源占用 |
| --- | --- | --- |
| 150 DPI | 快速预览、清晰大字 | 低 |
| 220 DPI | 大多数普通扫描件，推荐起点 | 中等 |
| 300 DPI | 小字、较模糊页面 | 较高 |
| 300 DPI 强化检测 | 低分辨率、淡字、密排小字测试 | 很高 |

清晰度越高并不一定越准确，也会明显增加显存、内存和处理时间。建议先抽取几页试跑，再决定是否整本处理。

### 页码范围

- 留空：处理全部页面；
- `5`：只处理第 5 个物理页面；
- `5-10`：处理第 5 至第 10 个物理页面。

### 竖排文本识别

该开关面向**印刷体古籍及日语竖排文本识别**。开启后，程序会使用适合竖排文字的检测、排序和文字层写入方式，并跳过仅适合横排正文的页边界分析。程序不会自动判断整本文档是否为竖排。

### 完成时自动打开

启用后，任务成功结束会自动打开生成的 PDF。批量处理或长时间无人值守时可以关闭。

## 高级功能

展开主界面的“高级选项”可使用以下功能：

- **双联页拆分**：把一张跨页扫描拆成左右两个单页输出页面；支持自动寻找中缝、固定比例、跳过指定页和从右向左输出。
- **多尺度深度扫描**：用多个邻近尺度重复检测并合并结果，可能改善淡字和小字检测，但耗时与显存占用会明显增加。
- **检测阈值**：降低阈值可能保留更多淡笔画，也可能带来噪点和误识别。
- **最大检测边长**：限制送入文字检测模型的图像尺寸；增大有助于小字，但需要更多显存。
- **倾斜校正**：默认读取 OCR 四点框角度，让文字层贴合倾斜扫描。异常文档可以关闭或调整角度上限。
- **原地覆写**：直接替换源 PDF。使用前必须自行备份，普通用户不建议开启。
- **仅生成文本辅助 PDF**：适合检查识别结果和文字层，不保留原扫描图像。
- **跳过版面分析**：排查页眉页脚过滤是否误删正文时使用。
- **分段计时**：显示拆分、版面分析、OCR 和文字写入等阶段耗时。

## 命令行和源码使用

### 打包版命令行示例

在 `PDFOCR.exe` 所在目录打开 PowerShell：

```powershell
.\PDFOCR.exe "D:\资料\扫描书.pdf"
.\PDFOCR.exe "D:\资料\扫描书.pdf" -o "D:\OCR结果" -l ch --dpi 220
.\PDFOCR.exe "D:\资料\古籍.pdf" -V -l ch --dpi 300
.\PDFOCR.exe "D:\资料\日文.pdf" -V -l japan --timing
```

### 源码运行示例

源码版需要自行准备 Python、PaddlePaddle GPU、PaddleOCR、PyMuPDF、OpenCV、Pillow 等依赖：

```powershell
python .\PDFOCR_PaddleV3.py "D:\资料\扫描书.pdf"
python .\PDFOCR_PaddleV3.py "D:\资料\古籍.pdf" -V -l ch --dpi 300
```

不带 PDF 参数运行时打开图形界面：

```powershell
python .\PDFOCR_PaddleV3.py
```

### 常用参数

| 参数 | 作用 |
| --- | --- |
| `-o DIR`, `--outdir DIR` | 指定输出目录 |
| `-p`, `--pure` | 在正常输出之外，额外生成白底纯文字辅助 PDF |
| `-c`, `--cv` | 打开 OpenCV 调试窗口，查看程序实际读取的页面图像 |
| `-n`, `--no-ocr` | 只剥离原有矢量文字层，不运行 OCR |
| `-l CODE`, `--lang CODE` | 指定识别语言代码 |
| `-I`, `--inplace` | 原地覆写源文件，使用前必须备份 |
| `-P`, `--pixmap` | 强制把 PDF 页面栅格化后再做 OCR，不是页码范围参数 |
| `-g`, `--debug` | 把文字层按识别置信度着色并显示在输出页面上 |
| `-S`, `--skip-layout` | 跳过正文边界分析 |
| `-V`, `--vertical` | 开启竖排文本识别 |
| `--dpi N` | 设置 OCR 渲染 DPI |
| `--max-pixels N` | 限制页面渲染后的最大像素数 |
| `--det-limit N` | 设置文字检测最大边长；`0` 表示不限制 |
| `--det-thresh N` | 调整文本像素检测阈值 |
| `--det-box-thresh N` | 调整候选文字框阈值 |
| `--multi-scale N` | 多尺度检测，常用 `3`、`5` 或 `7` |
| `--no-skew` | 关闭文字层倾斜校正 |
| `--skew-max N` | 设置允许的最大倾斜角度 |
| `--legacy-text` | 使用旧版文字层写入方式作对照 |
| `--gc-interval N` | 调整资源回收的页数间隔 |
| `--timing` | 输出各处理阶段耗时 |
| `--skip-cuda-fetch` | 禁止本次运行准备 CUDA 组件 |

### 双联页拆分参数

| 参数 | 作用 |
| --- | --- |
| `-D`, `--split-double-page` | 开启双联页拆分 |
| `--split-ratio N` | 固定切分比例 |
| `--split-fixed` | 关闭自动寻找中缝，始终按 `--split-ratio` 切分 |
| `--split-window N` | 自动寻找中缝的中心搜索范围 |
| `--split-gap N` | 中缝留白宽度 |
| `--split-skip PAGES` | 不拆分的物理页码 |
| `--split-quality N` | 拆分页的 JPEG 暂存质量 |
| `--split-lossless` | 使用无损暂存，消耗更多内存和磁盘 |
| `--split-rtl` | 先输出右半页，适合从右向左翻阅 |
| `--split-dpi N` | 设置拆分页渲染 DPI |

运行下面的命令可以查看当前版本全部参数和默认值：

```powershell
.\PDFOCR.exe --help
```

## CUDA 安装、调试与测试命令

### 主动准备 CUDA 组件

```powershell
.\PDFOCR.exe --install-cuda
.\PDFOCR.exe --install-cuda --cuda-source auto
.\PDFOCR.exe --install-cuda --cuda-source tuna
.\PDFOCR.exe --install-cuda --cuda-source bfsu
.\PDFOCR.exe --install-cuda --cuda-source pypi
```

`auto` 会按国内镜像和 PyPI 的预设顺序尝试；另外三个值用于锁定下载源。只有明确执行该命令或在图形界面确认后，程序才会联网下载。

CUDA 下载日志保存在程序目录下的 `PDFOCR\_internal\CUDA下载日志.txt`，排查下载失败时请先查看该文件。

### 环境自检

```powershell
.\PDFOCR.exe --selftest
```

自检会检查模型目录、关键依赖、Paddle 设备以及推理引擎能否正常初始化。提交问题时，建议同时附上自检输出、显卡型号、显卡驱动版本和 Windows 版本。

### 定位识别问题

```powershell
.\PDFOCR.exe "D:\资料\样本.pdf" --timing -g
.\PDFOCR.exe "D:\资料\少量样本页.pdf" -c -P
.\PDFOCR.exe "D:\资料\少量样本页.pdf" -S
.\PDFOCR.exe "D:\资料\少量样本页.pdf" --legacy-text
```

- `--timing`：判断时间主要花在拆分、版面分析、OCR 还是文字写入；
- `-g`：让文字层可见并按识别置信度着色，检查识别质量和落点；
- `-c`：显示 OpenCV 调试图，检查程序实际读取的页面图像；
- `-P`：强制把 PDF 页面栅格化后识别，用于对照页面图像提取路径；
- `-S`：临时关闭页眉页脚过滤，用于判断正文是否被版面分析误删；
- `--legacy-text`：与旧版文字层写入方式对照；
- 调试前可先用界面的“页码范围”导出少量样本页，或准备一个只含问题页面的小 PDF，避免每次运行整本书。

## 输出、隐私与联网说明

- PDF 内容在本机处理，程序没有把 PDF 上传到服务器的功能。
- 正常识别不依赖云端 OCR 服务。
- 仅在用户确认准备 CUDA 组件或显式运行 `--install-cuda` 时联网下载运算库。
- 下载项采用固定版本、固定文件大小和 SHA256 校验，并在隔离目录中安全解压。
- 输出 PDF 保留原扫描图像并加入隐藏文字层；本工具不负责恢复原字体、段落语义、书签或表格结构。

## 校验下载文件

PowerShell 示例：

```powershell
Get-FileHash .\PDFOCR-v281-Windows-x64.zip -Algorithm SHA256
Get-FileHash .\PDFOCR-v281-Windows-x64.exe -Algorithm SHA256
Get-FileHash .\PDFOCR-v281-source.py -Algorithm SHA256
```

把结果与 Release 页面中的 `SHA256SUMS.txt` 对照。v281 的校验值为：

```text
f610440531d23ae122121bf6035115f564711b4f07fb937d2f230a320c2a5223  PDFOCR-v281-Windows-x64.zip
ffe0857ec1814d071a7cbd3480e458044bd712d9fa933bd3061321febf7f7a7f  PDFOCR-v281-Windows-x64.exe
7e045db839c2eceee527a5d38c1ac0da936d1a235c96782babe2c86af18d3ca8  PDFOCR-v281-source.py
```

## 已知限制

- 竖排模式必须手动开启，程序不会自动判断整本文档的排版方向。
- 超大字号扉页、连点目录、复杂横竖混排、自带页面旋转的 PDF 仍可能漏识别或错位。
- 低分辨率密排小字，尤其双行小注，仍可能大量漏检；强化检测不能恢复源图中已经模糊或粘连的笔画。
- 大幅插图、跨栏、边注、异形页面或损坏 PDF 可能使正文边界判断失误。可用 `-S` 对照排查。
- 300 DPI、多尺度检测和低阈值会显著增加显存、内存和处理时间。
- 双联页拆分会改变输出页数，页码范围和跳过页码仍按拆分前的物理页计算。
- 原地覆写具有风险，使用 `-I` 前务必备份源文件。
- 当前 Windows EXE 未进行代码签名，可能触发 SmartScreen 提示。

## 源码目录

```text
PDFOCR_PaddleV3.py   v281 统一源码
requirements.txt    源码运行所需的主要 Python 依赖
README.md           使用说明
CHANGELOG.md        版本工作日志
SHA256SUMS.txt       v281 Release 文件校验值
docs/images/        README 截图
```

## 许可证

本项目使用 [GNU General Public License v3.0](LICENSE)。使用、修改和再发布时请遵守许可证要求。PaddleOCR、PaddlePaddle、PyMuPDF、OpenCV、Pillow 等第三方组件分别遵循其各自许可证。
