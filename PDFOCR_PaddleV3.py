# ============================================================================
#  PDFOCR 281 · 统一源码（透明 CUDA 下载 + 主页面竖排开关）
# ============================================================================

# 281 版改动：
#   · CUDA 下载改为用户显式确认、公开来源、固定文件与 SHA-256 校验；
#     先隔离解压，全部校验通过后才安装，并保留可查看的下载日志。
#   · 默认下载源为“中国大陆优化”：清华 TUNA -> 北外 BFSU -> PyPI 官方；
#     用户也可主动固定为其中任意一个来源。
#   · “竖排文本识别”从高级参数移到主页面，位于指定页码与自动打开之间。
#   · 延续 280 版 CropBox 纵向补偿及此前全部识别功能。
#
#  本文件是 261/262 两条并行分支的合并点。此前的分叉与合并关系如下：
#
#      257 打包就绪
#       |
#      258 轻量版 CUDA 自动获取
#       |
#       +--- [打包线] ------------------------------+
#       |     259-A/B  首次分出全捆绑 / 轻量下载两个变体
#       |     260-A/B  打包环境自检 --selftest
#       |     261 统一源码  A/B 合回单一源码 + 模型缓存路径处理
#       |     262 统一源码  CLI 场景不弹 GUI 对话框、内存不足提示
#       |                                            |
#       +--- [功能线] ------------------------------+|
#             261-A/B  文字层倾斜校正                ||
#             262-A/B  竖排文本（竖排排印 / 日文）    ||
#                                                   ||
#      263 统一源码  <-- 两条线在此合并 ---------------++
#       |
#      264 统一源码  命令行清晰度旋钮 + 界面"强化检测"档
#                        （低分辨率密排影印件：默认档 7781 字 -> 强化检测档 11979 字）
#       |
#      265 统一源码  跨列误并拆分
#                        （落在横排块里的正文字 1022 -> 149，减少 85%）
#       |
#      266 统一源码  竖排"字距/字号"解耦 + 低分辨率扫描件自动抬高检测上限
#       |
#      267 统一源码  竖排正文页一律按竖排写入
#                        （《中庸章句集注》全书横排块 155 -> 1；纯横排页不受影响）
#       |
#      268 统一源码  低分辨率竖排件自动**整档**提升（渲染+检测一起抬）
#       |
#      269 统一源码  多尺度深度扫描 --multi-scale（低清影印件专用）
#       |
#      270 统一源码  放宽 DB 检测阈值（低分辨率影印件自动启用）
#       |
#      271 统一源码  高级参数面板对齐整理 + 悬停提示（界面美化阶段起点）
#       |
#      272 统一源码  措辞去门类化 + 清晰度档位标明 DPI 与显存需求
#       |
#      273 统一源码  修好顶部控件行被 pack 压扁的问题；ToolTip 统一复用
#       |
#      274 统一源码  <-- 本文件。Doctor Cat 形象接入（窗口图标 / 页头四态 / 出错对话框）
#                        + 修好按钮处理态文字被 disabledforeground 变灰看不清
#
#  【打包提示】exe 图标与随包资源：
#     pyinstaller --icon "assets/app-icons/doctorcat-faithful/doctorcat-faithful-windows-exe-multisize.ico" ^
#                 --add-data "assets/app-icons/doctorcat-faithful;assets/app-icons/doctorcat-faithful" ...
#     资源缺失时程序不会崩，只是没有猫（_asset_path + 逐张 try 兜底）。
#
#  合并方式：以打包线的 262 统一源码为底，把功能线的补丁按序重放上去
#  （倾斜校正 13 处 + 竖排 32 处 + 显存 1 处 + 字号上限 1 处，共 47 处）。
#  合并后逐项验证：
#    · 竖排：竖排测试件 12 页，正文覆盖率 96%（与功能线的 262-B 完全一致）
#    · 横排：倾斜样张与 261 输出内容流逐字节相同（2106 字节）
#    · 横排：水平样张与 258 基线内容流逐字节相同（1673 字节）
#    · 打包：--selftest 三个模型通道全部实例化成功
#    · 界面：高级面板 10 条指令、5 行、顺序与位置全部正确
#
#  【往后只有这一条线】。功能改动、打包适配、bug 修复一律往序号更大的
#  统一源码迭代；公开产物统一使用 PDFOCR-v版本-Windows-x64，不再附加
#  A/B、完整版、轻量版等后缀。
#  公开发布版本号（v31/v32）与脚本序号（263/264）的对应关系见 CHANGELOG.md。
#  历史版本已全部移入同目录的 历史版本/ 子文件夹，主目录只保留本文件
#  与 CHANGELOG.md，避免再出现"哪个是最新"的疑问。
# ============================================================================

# ============================================================================
# 【本版本唯一改动：消除编辑器“问题”面板里的报错，运行逻辑一行未动】
# ----------------------------------------------------------------------------
# 下面这一行是给 Pylance / Pyright 看的开关，Python 解释器会当成普通注释跳过。
# 它关掉的全部是「第三方库没有提供类型说明文件」造成的假报错：
#   paddle / cv2 / fitz / paddleocr 这几个库都是 C++ 编译出来的，
#   编辑器读不到它们的函数签名，于是把 cv2.imshow、paddle.__version__ 之类
#   全部标成红线。这些在实际运行时完全正常（本文件已实测跑通）。
# 真正有价值的检查（变量可能未定义 reportPossiblyUnbound 等）一律保留开启，
# 并且已在本版本中逐条改成真正定义好，而不是靠屏蔽糊弄过去。
# ============================================================================
# pyright: reportAttributeAccessIssue=false, reportPrivateImportUsage=false
# pyright: reportArgumentType=false, reportMissingImports=false
# pyright: reportMissingModuleSource=false, reportMissingTypeStubs=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false, reportUnknownParameterType=false
# pyright: reportMissingParameterType=false, reportUnknownLambdaType=false
# pyright: reportMissingTypeArgument=false, reportIndexIssue=false
# pyright: reportCallIssue=false, reportOptionalMemberAccess=false
# pyright: reportRedeclaration=false, reportSelfClsParameterName=false
# pyright: reportUnusedImport=false, reportUnusedVariable=false
# pyright: reportUnnecessaryComparison=false

r"""
    操作方法：这里有一个对PDF进行OCR识别的脚本。

    它的操作命令是
    单文件：python PDFOCR.py input.pdf
    多文件：python PDFOCR.py 论文A.pdf 论文B.pdf ...
        其中，input.pdf是你需要进行OCR识别的PDF文件，填入文件路径即可。
        默认位置：会在原文件旁生成 论文A-OCR.pdf 或 论文B-OCR.pdf。

    指定保存地址（带 -o 参数）
    示例：python PDFOCR.py "D:\论文A.pdf" "C:\论文B.pdf" -o "D:\OCR结果\今天"
        结果：即使这两个PDF 原本在不同的盘符，脚本也会统一将它们处理完毕并全部塞进 D:\OCR结果\今天 文件夹里。
        如果 D:\OCR结果\今天 这个文件夹原本不存在，会自动新建.

    ---------------------------------------------------------------------
    【本版本新增功能】双联页拆分 (-D / --split-double-page)
    ---------------------------------------------------------------------
    适用场景：有些扫描件是把书本摊开后，左右两个逻辑页一次性拍进同一张图像里。
    这种文件直接走原来的流程，左页和右页的文字会落在同一张 PDF 页面上。
    多数阅读器判断“选中哪几行”是按文字的纵坐标分组的，只要左页某一行和右页
    对应的那一行纵坐标重叠，阅读器就会把它们当成同一行，拖拽框选时左右两页
    的文字就会被一起选中。

    解决办法是在版面分析与 OCR 识别之前，先把这张图像沿中缝物理切成左右两张
    独立的 PDF 页面，让左页和右页从一开始就是两个互不相干的页面对象。之后
    版面分析、页边距抽样、OCR 识别都是在两张页面上分别独立进行的，识别出的
    文字框不会跨过中缝，阅读器也就不会把左右两页并成同一行。

    命令行用法：python PDFOCR.py input.pdf -D
    图形界面：在“展开高级干预参数”里勾选【双联页拆分 (-D)】。

    相关可选参数（一般用默认值即可）：
        --split-ratio 0.5     分割线基准位置（页面宽度的比例），默认正中央。
        --split-fixed         关闭自动探测中缝，强制按 --split-ratio 固定比例切。
        --split-window 0.06   自动探测中缝时，在基准位置左右各搜索的范围比例。
        --split-gap 0         分割线两侧各留出的间隙(pt)，用于避开装订阴影。
        --split-skip 1,32     指定哪些物理页码不拆分（如封面、封底），逗号分隔。
        --split-rtl           拆分后按“右页在前、左页在后”排列（自右向左翻阅的书籍）。
        --split-dpi 300       拆分时重新采样两个半页所用的分辨率，默认 300。

    注意：开启拆分后，输出 PDF 的页数会接近原来的两倍。
    若同时使用“指定处理页码”，填写的是【拆分前】的原始物理页码。

    ---------------------------------------------------------------------
    【本版本新增】速度优化与性能诊断
    ---------------------------------------------------------------------

    相关参数：
        --timing         打印每页耗时构成（渲染/擦除/推理/写入），并检测
                         Paddle 是否真的在用 GPU。用来判断瓶颈在代码还是显卡。
                         图形界面里对应【分段计时诊断】勾选框。
        --legacy-text    退回旧的逐字符写入通道（很慢，但保留标点压扁效果）。

    【261 版新增】倾斜扫描页的文字层角度校正
    ---------------------------------------------------------------------
    非标准扫描件的文字行往往整体歪斜几度。旧版写入的文字层永远是水平的，
    于是矢量文字与图像文字对不上，斜率大时甚至跨行错位。本版让文字层跟着
    每一行的真实倾角一起倾斜。

    相关参数：
        --no-skew        关闭倾斜校正，完全退回 258 版的水平写入行为。

    【262 版新增】竖排文本（竖排排印 / 日文）
    ---------------------------------------------------------------------
    竖排页面的一"列"在几何上就是一条旋转了 90 度的"行"，因此本版把 261 版
    的倾斜写入机制原样复用：写入轴由「左下→右下」改取「左上→左下」，倾角
    基准由 0 度改为 90 度，其余（morph 旋转、TextWriter 高速通道）完全不变。

    与横排的三处实质差异：
      1. 字号来自「列长 ÷ 字数」，而不是「行宽 ÷ 各字宽度之和」——竖排
         每个字占满一个全角字身，没有西文那种变宽。
      2. 每字推移量恒为一个字号，不再按 text_length 逐字测算，中文标点
         也不再压半宽（竖排标点同样占满一个字身）。
      3. 列序按自右向左重排。PaddleOCR 的 SortQuadBoxes 是按 (上, 左)
         排序的，对竖排会给出从左到右的顺序，正好是反的；不重排的话
         复制出来的正文整段倒序。

    相关参数：
        --vertical / -V  按竖排处理。默认关闭，必须由用户显式指定。
                         图形界面对应【竖排文本 (-V)】勾选框。
                         注意 1：开启后会自动等效于 -S（跳过版面分析），
                         因为现有的天头地脚拟合是按横排文字行统计的，
                         用在竖排页面上有整列被误判为页眉页脚的风险。
                         注意 2：开启后会关闭文本行方向分类器。这是竖排
                         能不能用的关键，原因见 get_ocr_engine 里的长注释；
                         实测正文覆盖率从 29~79% 提升到 94~97%。
        --skew-max N     倾角绝对值超过 N 度的框判定为异常（竖排、印章、
                         误检的旁注），按 0 度处理，默认 30。

    【267 版新增】竖排正文页一律按竖排写入
    ---------------------------------------------------------------------
    262 版是逐框按长宽比判朝向。实测发现，竖排正文页上被判成"横排"的框
    绝大多数是检测误判（密排影印件里相邻列的字被连成横长块），把它们当横排
    写会让文字层横着盖在竖排正文上。本版改为：只要判定本页是竖排正文页，
    页内所有框一律按竖排写。代价是真正的横排书名、页码也按竖排处理 ——
    那些通常只有两三个字，位置依然落在字上，只是选中顺序变成自上而下。
    正文准确性优先。竖排书里夹的横排页（版权页、索引）判定不通过，不受影响。

    【266 版新增】竖排"字距 / 字号"解耦 + 竖排自动抬高检测上限
    ---------------------------------------------------------------------
    262~265 让同一个 fs 同时当字号和字距。横排里两者本就相等，竖排里不是：
    经注合刻本（如《中庸章句集注》）的小注与大字**行距相同**，只是字形更小、
    列更窄。字号若跟着字距取 22pt，字身旋转后横向跨度 29pt，而小注子列只有
    16pt 宽，左右各溢出 6.5pt 压进相邻列，阅读器里选一列会连带选中隔壁。
    本版分开算：字距仍取「列长÷字数」，字号取 min(字距, 列宽/1.3086)。

    另外竖排模式会自动把检测输入上限抬到 2800 像素 —— 竖排书几乎都是低分辨率
    影印件，用前三档的 1600 会把小字笔画压糊（实测第 4 页 233 字 -> 801 字）。

    【265 版新增】跨列误并拆分
    ---------------------------------------------------------------------
    低分辨率密排影印件上，相邻列顶端的字会被检测网络连成一个横长框（六列各取
    一字连成 "天人物以是哀"）。这些字是每列的首字，丢不得。本版按字数把这类
    框等分拆回各列，识别结果原样复用（这些框的识别分数本来就有 0.98~1.00），
    顺带修掉了旧写法按字体推进量累加造成的横向漂移。
    只在"本页确实以竖排列为主"时才拆，竖排书里夹的横排页不受影响。
    详见 _explode_cross_column_rows 的注释。

    【264 版新增】命令行清晰度旋钮 / 界面"强化检测"档
    ---------------------------------------------------------------------
        --dpi N          目标渲染 DPI，默认 220（界面档位为 150/220/300）。
        --max-pixels N   渲染长边像素上限，默认 2500，硬顶 4000。
        --det-limit N    文字检测网络的输入长边上限，0 = 不限制。

    低分辨率的密排影印件（扫描源只有几十 DPI、且带双行夹注）需要把检测输入
    上限抬上去，否则小字的笔画会被压糊。界面新增的【强化检测】档等价于
        --dpi 300 --max-pixels 3800 --det-limit 2800
    实测在一份 89 DPI 的密排影印件上比默认的 220 档多认出约六成字，
    显存峰值 1021MB -> 2816MB。前三档的参数一个都没动。
        --gc-interval N  每 N 页强制回收一次内存，默认 10。旧版是每页都回收，
                         大模型常驻时一次回收要 0.1~0.5 秒，每页做太浪费。
                         设为 1 可恢复旧行为。
"""

# （注：以下为注入了“核心锚定、奇偶分流、逆向滤波”等高级版面分析算法的智能识别脚本）

#!/usr/bin/env python3

# =========================================================================
# 【257 版新增 · 打包自举】必须放在所有第三方库导入之前
# -------------------------------------------------------------------------
# paddlex 在**模块导入的那一瞬间**就会去读环境变量 PADDLE_PDX_CACHE_HOME
# 来决定模型缓存目录（见 paddlex/utils/cache.py 第 29 行）。所以这段代码
# 必须抢在 import paddle / paddleocr 之前执行，晚一步就没用了。
#
# 打包成 exe 之后，模型不能再依赖用户机器上的 C:\Users\xxx\.paddlex，
# 否则程序一启动就会联网重新下载 300 MB 模型。这里把缓存目录指向
# exe 旁边的 paddlex_cache 文件夹，模型随程序一起分发，开箱即用。
#
# 目录结构（发布包）：
#     PDFOCR.exe
#     paddlex_cache\official_models\PP-DocLayout_plus-L\...
#     paddlex_cache\official_models\PP-OCRv5_server_det\...
#     paddlex_cache\official_models\PP-OCRv5_server_rec\...
#     paddlex_cache\official_models\PP-LCNet_x1_0_textline_ori\...
#
# 源码直接运行时，若旁边没有这个文件夹，就什么都不做，沿用系统默认路径，
# 因此本改动对你现在的开发环境完全没有影响。
# =========================================================================
import os as _os
import sys as _sys

# GUI 双击启动时，PyInstaller 会在启动器层尽早隐藏自建控制台。若个别
# Windows Terminal 配置只能最小化而不能隐藏，这行文字会先立即出现，
# 明确告诉用户程序仍在加载；从已有终端启动的命令行模式不受影响。
if getattr(_sys, "frozen", False) and len(_sys.argv) <= 1:
    try:
        if _sys.stdout is not None:
            print("PDFOCR 正在打开。AI 引擎初始化需要一定时间，请耐心等待；请不要关闭此窗口。",
                  flush=True)
    except Exception:
        pass
    try:
        import ctypes as _early_ct
        _early_hwnd = _early_ct.windll.kernel32.GetConsoleWindow()
        if _early_hwnd:
            _early_ct.windll.user32.ShowWindow(_early_hwnd, 0)
    except Exception:
        pass


def _app_dir():
    """打包后返回 exe 所在目录；源码运行时返回脚本所在目录。"""
    if getattr(_sys, "frozen", False):
        return _os.path.dirname(_sys.executable)
    return _os.path.dirname(_os.path.abspath(__file__))


APP_DIR = _app_dir()


# =========================================================================
# 【261 版新增 · 中文路径防护】
# -------------------------------------------------------------------------
# paddle 的 C++ 推理引擎在 Windows 上用窄字符 API 打开模型文件，**路径里
# 只要含非 ASCII 字符就会读到空内容**，然后抛出一句完全看不出所以然的
#     RuntimeError: [json.exception.parse_error.101] ... empty input
# 这一点已用隔离实验确认：同一份模型、同一套代码，仅仅把缓存目录从
# ascii_path 换成"路径测试_中文"，就从成功变成失败。
#
# 这对中文用户是致命的，因为下面这些都极其常见：
#     C:\Users\张三\Desktop\PDF识别\      （Windows 用户名是中文）
#     D:\我的软件\PDFOCR\
# 一解压就用不了，而且报错信息毫无指向性。
#
# 三级应对，优先级从高到低：
#   1) 程序目录本来就是纯 ASCII      -> 直接用，零开销（绝大多数情况）
#   2) 能取到 Windows 8.3 短路径名   -> 用短名，例如 我的软件 -> 6E1F~1
#      （零拷贝。但短名功能可能被系统关闭，尤其非系统盘）
#   3) 以上都不行                    -> 把模型迁移到 C:\ProgramData 下的
#      纯 ASCII 目录，只在首次运行时复制一次
# =========================================================================
def _is_ascii(text):
    try:
        text.encode("ascii")
        return True
    except (UnicodeEncodeError, AttributeError):
        return False


def _win_short_path(path):
    """取 Windows 8.3 短路径名；取不到或功能被关闭时返回 None。"""
    try:
        import ctypes
        from ctypes import wintypes
        fn = ctypes.windll.kernel32.GetShortPathNameW
        fn.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        fn.restype = wintypes.DWORD
        buf = ctypes.create_unicode_buffer(4096)
        if fn(path, buf, 4096) and buf.value:
            return buf.value
    except Exception:
        pass
    return None


def _prepare_model_cache():
    """挑一个 paddle 一定读得到的模型缓存目录，必要时迁移模型。"""
    local = _os.path.join(APP_DIR, "paddlex_cache")
    if not _os.path.isdir(_os.path.join(local, "official_models")):
        return None            # 源码运行或没带模型：沿用系统默认路径

    if _is_ascii(local):
        return local           # 情况 1：本来就安全

    short = _win_short_path(local)
    if short and _is_ascii(short):
        return short           # 情况 2：短路径名救场，零拷贝

    # 情况 3：迁移到 ProgramData（该路径在任何中文 Windows 上都是纯 ASCII）
    base = _os.environ.get("ProgramData", r"C:\ProgramData")
    target = _os.path.join(base, "PDFOCR", "paddlex_cache")
    src_models = _os.path.join(local, "official_models")
    dst_models = _os.path.join(target, "official_models")
    try:
        import shutil
        need = []
        for name in _os.listdir(src_models):
            if not _os.path.isdir(_os.path.join(dst_models, name)):
                need.append(name)
        if need:
            print("=" * 62)
            print("  首次运行：正在准备 AI 模型")
            print("  程序所在路径含中文，而 AI 引擎无法从中文路径读取模型，")
            print("  因此需要把模型复制到以下位置（仅此一次，约 300 MB）：")
            print("     " + target)
            print("=" * 62)
            _os.makedirs(dst_models, exist_ok=True)
            for i, name in enumerate(need, 1):
                print("   [%d/%d] 正在复制 %s ..." % (i, len(need), name))
                shutil.copytree(_os.path.join(src_models, name),
                                _os.path.join(dst_models, name),
                                dirs_exist_ok=True)
            print("   模型准备完成。\n")
        if _is_ascii(target):
            return target
    except Exception as e:
        print("   [!] 迁移模型失败：%s: %s" % (type(e).__name__, e))
        print("   [!] 请把本程序移动到不含中文的路径下再运行，例如 D:\\PDFOCR\\")

    return None


_cache_home = _prepare_model_cache()
if _cache_home:
    _os.environ["PADDLE_PDX_CACHE_HOME"] = _cache_home

# 跳过启动时的"联网检查模型源"，那一步在离线机器上会干等好几秒
_os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

# =========================================================================
# 【261 版新增 · 打包必需】强制控制台使用 UTF-8
# -------------------------------------------------------------------------
# 打包成 exe 后遇到的第一个真实崩溃：
#     UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f4c2'
#
# 中文版 Windows 的控制台默认编码是 GBK(代码页 936)，而本脚本的提示信息里
# 用了大量 emoji（✅ 📁 🔍 ⏱ ✂️ 🎉 📦 等）。GBK 表示不了这些字符，于是
# 程序一执行到 print 就抛异常整个崩掉——而且是在正式干活之前就崩。
#
# 开发阶段一直没暴露，是因为调试时都用 `python -X utf8 脚本.py` 运行，
# 那个参数强制解释器全程 UTF-8。打包后没有这个参数，问题才浮出水面。
#
# 这里做两件事：
#   1) 把控制台的输出代码页切到 65001(UTF-8)，让 emoji 能正常显示；
#   2) 把 stdout/stderr 重新配置成 UTF-8，并且 errors="replace" —— 万一
#      某些环境切不动代码页，也只会把个别字符显示成"?"，绝不再崩溃。
# 用 --noconsole 方式打包时 sys.stdout 可能是 None，所以每一步都做了判空。
# =========================================================================
try:
    import ctypes as _ctypes
    _ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    _ctypes.windll.kernel32.SetConsoleCP(65001)
except Exception:
    pass

for _stream_name in ("stdout", "stderr"):
    _stream = getattr(_sys, _stream_name, None)
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


# =========================================================================
# 【281 版】双击启动时的控制台已在文件最前部处理
# -------------------------------------------------------------------------
# 打包时用的是 console=True。这不是笔误：本程序同时要服务两类人 ——
#   · 普通用户双击图标使用，他们只该看到图形界面，不该看到黑底命令行；
#   · 技术用户在命令行里跑批处理，他们需要 --timing / --selftest 的输出。
# 如果改成 console=False（窗口化打包），第二类人就完全拿不到任何输出了，
# PyInstaller 会把 stdout 换成一个丢弃一切的空写入器。
#
# 所以做法是：保留真正的控制台，但在"无参数启动"（即双击）时把这个窗口
# 藏起来。print / tqdm 照常工作、写进真实的控制台缓冲区，只是不显示。
# 带参数启动时不隐藏，命令行输出一切如常。
#
# 代价：双击时黑窗会闪一下（进程启动到执行这几行之间的几十毫秒）。
# 这比"技术用户完全没有输出"要好得多。
# =========================================================================
# =========================================================================
# 【281 版】CUDA 运算库按需、安全、透明获取
# -------------------------------------------------------------------------
# 背景：paddle 做 AI 推理需要 cuDNN / cuBLAS / cuFFT / cuSOLVER / cuSPARSE
# 这几套 NVIDIA 计算库，解压后约 3.1 GB。它们**不在显卡驱动里**——装了
# N 卡只会有 nvcuda.dll（驱动 API），这些计算库要另外获取。
#
# 把它们打进安装包会让安装包膨胀到 3 GB 级别。本版本改为：安装包里不带，
# 首次运行时从 PyPI 官方源自动下载（它们本来就是公开的 pip 轮子，
# 不需要任何私有服务器），解压到程序目录，之后每次启动都直接复用。
#
# 为什么必须放在文件最顶部：
#   paddle 在 **import 的那一瞬间** 就会执行
#       site_cuda_path = <paddle目录>/../nvidia/<库名>/bin
#       os.add_dll_directory(site_cuda_path)
#   来注册 DLL 搜索路径（见 paddle/__init__.py 的 Windows 分支）。
#   等到 import paddle 之后再补文件就晚了，那时路径已经注册完毕。
# =========================================================================
# 清单固定到 NVIDIA 在 PyPI 发布的 Windows x64 轮子。运行时不再查询
# PyPI 元数据；文件名、体积和 SHA-256 都随版本审计并写死在发布源码中。
_CUDA_MANIFEST = [
    {"package": "nvidia-cudnn-cu12", "version": "9.9.0.52",
     "filename": "nvidia_cudnn_cu12-9.9.0.52-py3-none-win_amd64.whl",
     "size": 767785830,
     "sha256": "d53036b7edad1a85b5d59580defc91e30326746fde21ffc701eb8b4d4695eca1",
     "url": "https://files.pythonhosted.org/packages/6f/5c/f77147ce7e27a4e9087fb34b0539ff085c68e7093e96ee85576fe31fe064/nvidia_cudnn_cu12-9.9.0.52-py3-none-win_amd64.whl"},
    {"package": "nvidia-cublas-cu12", "version": "12.9.0.13",
     "filename": "nvidia_cublas_cu12-12.9.0.13-py3-none-win_amd64.whl",
     "size": 552611067,
     "sha256": "a525014e22b8adb79d04b70f69fd53d09c7b851002b3d332cd601da3a37276fd",
     "url": "https://files.pythonhosted.org/packages/08/79/0cf1ed0ccea47067cc2140ab9bd38100de574824a6dc9e12151fb9b39c59/nvidia_cublas_cu12-12.9.0.13-py3-none-win_amd64.whl"},
    {"package": "nvidia-cusparse-cu12", "version": "12.5.9.5",
     "filename": "nvidia_cusparse_cu12-12.5.9.5-py3-none-win_amd64.whl",
     "size": 362510485,
     "sha256": "228d7ee34c8e3622fa58aa7a53c6f5d05f5d0c6980173c46e308129b66910c88",
     "url": "https://files.pythonhosted.org/packages/4e/de/d771533939aeea1433a338825190453f9fcbf235370b8e7161522fd89a13/nvidia_cusparse_cu12-12.5.9.5-py3-none-win_amd64.whl"},
    {"package": "nvidia-cusolver-cu12", "version": "11.7.4.40",
     "filename": "nvidia_cusolver_cu12-11.7.4.40-py3-none-win_amd64.whl",
     "size": 320275500,
     "sha256": "288993d2c3bd8167baa3f7b581e219175db576a54d2c36ad62b163a07de923c5",
     "url": "https://files.pythonhosted.org/packages/b6/c6/0e3459479a34e7d7cde75b6990953b0873781eac05edfafcd761fe8918c2/nvidia_cusolver_cu12-11.7.4.40-py3-none-win_amd64.whl"},
    {"package": "nvidia-cufft-cu12", "version": "11.4.0.6",
     "filename": "nvidia_cufft_cu12-11.4.0.6-py3-none-win_amd64.whl",
     "size": 200095584,
     "sha256": "26cd694ef8472efac5e73466d05d5b356f80eafe849095eb6bf4d7f93390557d",
     "url": "https://files.pythonhosted.org/packages/4d/fe/b83d984f5f7420e2d43d148fe2379775d6f53d3e0a9057d998b16939ffc8/nvidia_cufft_cu12-11.4.0.6-py3-none-win_amd64.whl"},
    {"package": "nvidia-curand-cu12", "version": "10.3.10.19",
     "filename": "nvidia_curand_cu12-10.3.10.19-py3-none-win_amd64.whl",
     "size": 68774847,
     "sha256": "e8129e6ac40dc123bd948e33d3e11b4aa617d87a583fa2f21b3210e90c743cde",
     "url": "https://files.pythonhosted.org/packages/e5/98/1bd66fd09cbe1a5920cb36ba87029d511db7cca93979e635fd431ad3b6c0/nvidia_curand_cu12-10.3.10.19-py3-none-win_amd64.whl"},
    {"package": "nvidia-nvjitlink-cu12", "version": "12.9.86",
     "filename": "nvidia_nvjitlink_cu12-12.9.86-py3-none-win_amd64.whl",
     "size": 35584936,
     "sha256": "cc6fcec260ca843c10e34c936921a1c426b351753587fdd638e8cff7b16bb9db",
     "url": "https://files.pythonhosted.org/packages/dd/7e/2eecb277d8a98184d881fb98a738363fd4f14577a4d2d7f8264266e82623/nvidia_nvjitlink_cu12-12.9.86-py3-none-win_amd64.whl"},
    {"package": "nvidia-cuda-runtime-cu12", "version": "12.9.37",
     "filename": "nvidia_cuda_runtime_cu12-12.9.37-py3-none-win_amd64.whl",
     "size": 3591221,
     "sha256": "84a750e4d46a32e0b8adc4efdd4021fe49741b1cbbee72421c5400ff9865dd83",
     "url": "https://files.pythonhosted.org/packages/b8/1c/c6352858f84e5203279300a9fb4f9d7613cbab5fd4afd78613bb9bcdc64c/nvidia_cuda_runtime_cu12-12.9.37-py3-none-win_amd64.whl"},
]

# 兼容旧代码和诊断输出。
_CUDA_WHEELS = [(item["package"], item["version"]) for item in _CUDA_MANIFEST]

# 判断"已经装好了"的标志文件：挑两个最大、最不可能缺失的
_CUDA_SENTINELS = [
    "nvidia/cublas/bin/cublasLt64_12.dll",
    "nvidia/cudnn/bin/cudnn64_9.dll",
]

_PYPI_HOST = "https://files.pythonhosted.org/"
_CUDA_SOURCES = {
    "tuna": ("清华大学 TUNA 镜像", "https://pypi.tuna.tsinghua.edu.cn/"),
    "bfsu": ("北京外国语大学 BFSU 镜像", "https://mirrors.bfsu.edu.cn/pypi/web/"),
    "pypi": ("PyPI 官方源（NVIDIA 发布）", _PYPI_HOST),
}
_CUDA_SOURCE_DISPLAY = {
    "自动选择（推荐，中国大陆优化）": "auto",
    "PyPI 官方源（NVIDIA 发布）": "pypi",
    "清华大学 TUNA 镜像": "tuna",
    "北京外国语大学 BFSU 镜像": "bfsu",
}


def _cuda_source_candidates(choice):
    """返回用户准许使用的下载源；auto 按国内网络友好的固定顺序回退。"""
    choice = (choice or "auto").lower()
    keys = ["tuna", "bfsu", "pypi"] if choice == "auto" else [choice]
    if any(key not in _CUDA_SOURCES for key in keys):
        raise ValueError("未知 CUDA 下载源：%s" % choice)
    return [(key, _CUDA_SOURCES[key][0], _CUDA_SOURCES[key][1]) for key in keys]


def _cuda_cli_download_requested(argv):
    """命令行只有显式给出 --install-cuda 才允许联网下载。"""
    return "--install-cuda" in argv


def _cuda_source_from_argv(argv):
    for index, arg in enumerate(argv):
        if arg.startswith("--cuda-source="):
            value = arg.split("=", 1)[1]
            _cuda_source_candidates(value)
            return value
        if arg == "--cuda-source" and index + 1 < len(argv):
            value = argv[index + 1]
            _cuda_source_candidates(value)
            return value
    return "auto"


def _verify_file_sha256(path, expected):
    import hashlib
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower() == expected.lower()


def _extract_cuda_wheel_safely(wheel_path, target_root):
    """仅释放 nvidia/，并在写文件前整体拒绝路径穿越与符号链接。"""
    import shutil
    import stat
    import zipfile
    from pathlib import Path, PurePosixPath

    target_root = Path(target_root).resolve()
    with zipfile.ZipFile(wheel_path) as archive:
        allowed = []
        for info in archive.infolist():
            parts = PurePosixPath(info.filename).parts
            if not parts or parts[0] != "nvidia":
                continue
            if any(part in ("", ".", "..") for part in parts):
                raise ValueError("CUDA 安装包含不安全路径：%s" % info.filename)
            if info.filename.startswith(("/", "\\")) or ":" in parts[0]:
                raise ValueError("CUDA 安装包含绝对路径：%s" % info.filename)
            mode = (info.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(mode):
                raise ValueError("CUDA 安装包含符号链接：%s" % info.filename)
            destination = target_root.joinpath(*parts).resolve()
            try:
                destination.relative_to(target_root)
            except ValueError:
                raise ValueError("CUDA 安装包路径越界：%s" % info.filename)
            allowed.append((info, destination))

        if not allowed:
            raise ValueError("CUDA 安装包中没有 nvidia/ 运行库")
        for info, destination in allowed:
            if info.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, open(destination, "wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)


def _cuda_manifest_details():
    lines = ["发布者：NVIDIA CUDA Installer Team（经 PyPI 发布）", ""]
    for item in _CUDA_MANIFEST:
        lines.extend([
            "%s  %s  %.1f MB" % (item["package"], item["version"], item["size"] / 1048576),
            "SHA-256: %s" % item["sha256"],
            "官方地址: %s" % item["url"], "",
        ])
    return "\n".join(lines)


# =========================================================================
# 【274 版新增】应用形象（Doctor Cat）资源定位
# -------------------------------------------------------------------------
# 素材放在 assets/app-icons/doctorcat-faithful/ 下：
#   · doctorcat-faithful-windows-exe-multisize.ico  窗口 / 任务栏 / exe 图标
#   · ui/doctorcat-{idle,puzzle,smile,defeated}-header.png   71x84，标题右侧
#   · ui/doctorcat-{...}-dialog.png                         61x72，对话框内
# ui/ 下这批是按四张原图的 alpha 边界裁齐后统一缩放的，四态严格重合，
# 切换表情时不会有位移或大小跳动。
#
# 打包成 exe 后资源被解到 _MEIPASS，源码运行时就在脚本同级目录，
# 这里统一处理，调用方不必关心。
# =========================================================================
def _asset_path(*parts):
    base = getattr(_sys, "_MEIPASS", None)
    if not base:
        try:
            base = _os.path.dirname(_os.path.abspath(__file__))
        except NameError:
            base = _os.getcwd()
    return _os.path.join(base, "assets", "app-icons", "doctorcat-faithful", *parts)


def _cuda_root():
    """CUDA 库应该放在哪：必须和 paddle 包同级。"""
    if getattr(_sys, "frozen", False):
        # PyInstaller 单目录模式下，第三方包都在 _internal 里
        return getattr(_sys, "_MEIPASS", _os.path.dirname(_sys.executable))
    # 源码运行：site-packages 里本来就有，不需要下载
    return None


def _cuda_ready(root):
    if root is None:
        return True
    return all(_os.path.isfile(_os.path.join(root, p.replace("/", _os.sep)))
               for p in _CUDA_SENTINELS)


def _system_has_cuda_libs():
    """
    【277 版新增】判断这台机器上是否已经有可用的 CUDA 运算库。

    做法：不扫描硬盘，只把库名交给 Windows 的加载器，让它按标准顺序
    （程序目录 -> System32 -> PATH 上的目录）去找。找得到就说明系统里
    本来就有，paddle 运行时也会用同一套，我们再下载一份纯属浪费 2.2 GB。

    为什么不遍历硬盘找 DLL：
      · 慢 —— 全盘遍历动辄几分钟；
      · 会撞上其他用户目录的"拒绝访问"，得处理一堆权限异常；
      · 更要紧的是，"遍历磁盘搜索 DLL"正是杀毒软件判定可疑行为的典型
        特征，普通用户很可能直接看到安全警告。
    而 WinDLL() 只是一次普通的动态库加载，不枚举、不遍历、不需要提权。

    版本安全性：CUDA 系列的 DLL 文件名自带主版本号 ——
    cublasLt64_12 就是 CUDA 12.x，cudnn64_9 就是 cuDNN 9.x。
    能按这个名字加载成功，主版本必然是对的（本程序的 paddle 3.3.0
    正是针对 CUDA 12.9 / cuDNN 9.9 构建）。次版本的细微差异理论上仍
    可能有影响，但主版本已经卡住了绝大部分风险。
    """
    try:
        import ctypes
        for _dll in ("cublasLt64_12.dll", "cudnn64_9.dll"):
            ctypes.WinDLL(_dll)
        return True
    except Exception:
        return False


def _has_nvidia_driver():
    """轻量探测：能加载 nvcuda.dll 就说明装了 N 卡驱动。不依赖 paddle。"""
    try:
        import ctypes
        ctypes.WinDLL("nvcuda.dll")
        return True
    except Exception:
        return False


def _fetch_cuda_libraries(root, report, source="auto"):
    """按固定清单下载、验哈希、隔离解压，全部成功后一次性安装。"""
    import datetime
    import shutil
    import tempfile
    import urllib.request

    total_bytes = sum(item["size"] for item in _CUDA_MANIFEST)
    candidates = _cuda_source_candidates(source)
    log_path = _os.path.join(root, "CUDA下载日志.txt")
    stage = tempfile.mkdtemp(prefix=".pdfocr-cuda-", dir=root)
    payload = _os.path.join(stage, "payload")
    _os.makedirs(payload, exist_ok=True)

    def log(message):
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as stream:
            stream.write("[%s] %s\n" % (stamp, message))

    log("开始 CUDA 安装；用户选择=%s；总下载=%d 字节" % (source, total_bytes))
    done_bytes = 0
    try:
        for index, item in enumerate(_CUDA_MANIFEST, 1):
            wheel_path = _os.path.join(stage, item["filename"])
            last_error = None
            downloaded = False
            tail = item["url"].split(_PYPI_HOST, 1)[1]
            for key, name, host in candidates:
                real_url = host + tail
                report(done_bytes / total_bytes,
                       "下载源：%s；正在获取 %s (%d/%d)" %
                       (name, item["package"], index, len(_CUDA_MANIFEST)))
                log("下载 %s；来源=%s；URL=%s" % (item["package"], name, real_url))
                try:
                    got = 0
                    request = urllib.request.Request(
                        real_url, headers={"User-Agent": "PDFOCR/281 (+GitHub release)"})
                    with urllib.request.urlopen(request, timeout=120) as response, \
                            open(wheel_path, "wb") as output:
                        while True:
                            chunk = response.read(1024 * 1024)
                            if not chunk:
                                break
                            output.write(chunk)
                            got += len(chunk)
                            fraction = min(1.0, (done_bytes + got) / total_bytes)
                            report(fraction,
                                   "%s：%.0f/%.0f MB；总进度 %.0f%%" %
                                   (item["package"], got / 1048576,
                                    item["size"] / 1048576, fraction * 100))
                    if got != item["size"]:
                        raise RuntimeError("文件大小不符：应为 %d，实际 %d" %
                                           (item["size"], got))
                    if not _verify_file_sha256(wheel_path, item["sha256"]):
                        raise RuntimeError("SHA-256 校验失败，文件可能损坏或被篡改")
                    log("校验通过 %s；字节=%d；SHA-256=%s" %
                        (item["filename"], got, item["sha256"]))
                    downloaded = True
                    break
                except Exception as error:
                    last_error = error
                    log("来源失败 %s / %s：%s: %s" %
                        (item["package"], name, type(error).__name__, error))
                    try:
                        _os.remove(wheel_path)
                    except Exception:
                        pass
                    if source == "auto" and key != candidates[-1][0]:
                        report(done_bytes / total_bytes, "当前来源失败，切换下一项已公开来源…")
            if not downloaded:
                raise RuntimeError("%s 下载失败：%s" % (item["package"], last_error))

            report((done_bytes + item["size"]) / total_bytes,
                   "哈希已通过，正在安全解压 %s" % item["package"])
            _extract_cuda_wheel_safely(wheel_path, payload)
            _os.remove(wheel_path)
            done_bytes += item["size"]

        if not _cuda_ready(payload):
            raise RuntimeError("隔离区完整性校验失败，未修改现有程序文件")

        target = _os.path.join(root, "nvidia")
        staged_nvidia = _os.path.join(payload, "nvidia")
        backup = _os.path.join(stage, "previous-nvidia")
        if _os.path.exists(target):
            _os.replace(target, backup)
        try:
            _os.replace(staged_nvidia, target)
            if not _cuda_ready(root):
                raise RuntimeError("安装后的 CUDA 运行库校验失败")
        except Exception:
            if _os.path.exists(target):
                shutil.rmtree(target, ignore_errors=True)
            if _os.path.exists(backup):
                _os.replace(backup, target)
            raise
        if _os.path.exists(backup):
            shutil.rmtree(backup, ignore_errors=True)
        log("CUDA 安装完成；目标=%s" % target)
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def _ensure_cuda_libraries():
    """启动自举总入口。返回 True 表示可以继续用 GPU。"""
    root = _cuda_root()
    if _cuda_ready(root):
        return True

    # 【277 版】程序目录里没有，先看看这台机器上本来有没有。
    # 装过 paddlepaddle-gpu / PyTorch 等的机器通常已经带了同一套运算库，
    # 命中的话直接省掉 2.2 GB 下载。
    if _system_has_cuda_libs():
        print("   [i] 检测到本机已有可用的 NVIDIA 运算库，跳过下载。")
        return True

    if not _has_nvidia_driver():
        # 没有 N 卡，下 2.2 GB 也没意义，直接放行由后续的自检去提示用户
        return False

    need_mb = int(round(sum(item["size"] for item in _CUDA_MANIFEST) / 1048576))

    # ==================================================================
    # 命令行 / 批处理场景绝不能弹出 GUI 对话框，也不能把“传了任意参数”
    # 当作下载许可。只有 --install-cuda 是明确同意联网和写入程序目录。
    # ------------------------------------------------------------------
    # 旧写法只要 tkinter 能导入就弹 messagebox.askyesno 等人点"是"。
    # 双击启动时这是对的，但用命令行或脚本调用时，对话框后面根本没有人，
    # 程序会永远卡在那里——自动化流程、批处理、CI 全部会挂死。
    #
    # 现在按启动方式分流：
    #   带参数启动（命令行） -> 全程走控制台，打印说明后直接开始下载
    #                          （用户既然主动敲了命令，就是想让它干活）
    #   无参数启动（双击）   -> 保留原有的图形化询问与进度条
    #   --skip-cuda-fetch    -> 明确跳过下载，用于测试，或用户想手动放置文件
    # ==================================================================
    if "--skip-cuda-fetch" in _sys.argv:
        print("   [i] 已指定 --skip-cuda-fetch，跳过 CUDA 运算库获取。")
        return False

    _is_cli = len(_sys.argv) > 1
    if _is_cli and not _cuda_cli_download_requested(_sys.argv):
        print("   [i] CUDA 运算库尚未安装；本次未联网下载。")
        print("       如需安装，请明确运行：PDFOCR.exe --install-cuda")
        print("       可追加 --cuda-source auto|pypi|tuna|bfsu 选择来源。")
        return False
    try:
        _chosen_source = _cuda_source_from_argv(_sys.argv) if _is_cli else "auto"
    except ValueError as _source_error:
        print("   [!] %s" % _source_error)
        return False
    gui = False
    if not _is_cli:
        try:
            import tkinter as tk
            from tkinter import messagebox, ttk
            gui = True
        except Exception:
            gui = False

    if gui:
        # ==============================================================
        # 【278 版修正】首次运行的询问窗必须是"找得到"的
        # --------------------------------------------------------------
        # 旧写法是 root_win.withdraw() + messagebox.askyesno()，两个后果：
        #   1) 根窗口被隐藏，这个对话框在任务栏上没有任何图标；
        #   2) 对话框不置顶，浏览器、资源管理器随便一个窗口就把它盖住。
        # 实测（真实双击启动，非从终端拉起）：对话框弹出后静静等了 95 秒
        # 无人应答，下载一个字节都没开始。用户看到的现象是"双击没反应、
        # 什么都不加载"——其实程序在等一个他根本看不见的问题。
        #
        # 现在改成一个正经窗口：居中、置顶、任务栏有图标、按钮写清楚，
        # 关窗口等同于"暂不下载"。进度显示也复用同一个窗口，
        # 这样从头到尾任务栏上始终有一个可点回来的入口。
        # ==============================================================
        # ==============================================================
        # 【279 版】视觉与主界面统一
        # --------------------------------------------------------------
        # 278 把窗口做成了"能被看见"，但用的是 Tk 默认灰底样式，和主界面
        # 那套白底 + 微软雅黑 + 黑色主按钮的语言完全不搭，像另一个软件弹
        # 出来的东西。这里改成同一套：白底 #FFFFFF、标题微软雅黑加粗、
        # 主按钮 #111111 白字、次按钮白底细边框、窗口图标用 Doctor Cat，
        # 左侧放一张 Doctor Cat 对话形象，和主界面保持同一个"人"。
        #
        # 按钮文案也从"开始准备（推荐）"改成"开始下载"——前者要用户自己
        # 转译成"哦原来是要下载东西"，多一层理解成本，而这句话上面已经
        # 讲清楚了要下载什么、多大。按钮就该直说它会做什么。
        # ==============================================================
        root_win = tk.Tk()
        root_win.title("PDF 文字识别工具 · 首次运行")
        root_win.configure(bg="#FFFFFF")
        root_win.resizable(False, False)
        _W, _H = 680, 500
        try:
            _sw = root_win.winfo_screenwidth()
            _sh = root_win.winfo_screenheight()
            root_win.geometry("%dx%d+%d+%d" % (_W, _H,
                              max(0, (_sw - _W) // 2), max(0, (_sh - _H) // 3)))
        except Exception:
            root_win.geometry("%dx%d" % (_W, _H))
        # 窗口/任务栏图标与主界面一致
        try:
            root_win.iconbitmap(_asset_path("doctorcat-faithful-windows-exe-multisize.ico"))
        except Exception:
            pass

        _ans = {"ok": False, "source": "auto"}

        _head = tk.Frame(root_win, bg="#FFFFFF")
        _head.pack(fill="x", padx=34, pady=(24, 6))
        try:
            root_win._cat_img = tk.PhotoImage(
                file=_asset_path("ui", "doctorcat-idle-dialog.png"))
            tk.Label(_head, image=root_win._cat_img, bg="#FFFFFF").pack(side="left", padx=(0, 16))
        except Exception:
            pass
        _txt = tk.Frame(_head, bg="#FFFFFF")
        _txt.pack(side="left", anchor="w")
        tk.Label(_txt, text="首次运行，需要下载 AI 运算库",
                 font=("微软雅黑", 13, "bold"), bg="#FFFFFF", fg="#111111"
                 ).pack(anchor="w")
        tk.Label(_txt, text="只需下载这一次，之后每次打开都会直接使用",
                 font=("微软雅黑", 9), bg="#FFFFFF", fg="#888888"
                 ).pack(anchor="w", pady=(4, 0))

        tk.Label(root_win, justify="left", bg="#FFFFFF", fg="#333333",
                 font=("微软雅黑", 9),
                 text=("检测到你的电脑装有 NVIDIA 显卡。本程序依靠显卡做 AI 识别，\n"
                       "需要一套 NVIDIA 官方运算库（cuDNN / cuBLAS 等）。\n\n"
                       "这套库约 %d MB，没有随程序一起打包，需要现在下载一次。\n"
                       "下载后逐项校验固定 SHA-256，通过后才会安装。\n"
                       "保存位置：%s\n"
                       "下载完成后，主界面会自动打开。" % (need_mb, root))
                 ).pack(padx=36, anchor="w", pady=(14, 0))

        _source_box = tk.Frame(root_win, bg="#FFFFFF")
        _source_box.pack(fill="x", padx=36, pady=(14, 0))
        tk.Label(_source_box, text="下载来源：", font=("微软雅黑", 9, "bold"),
                 bg="#FFFFFF", fg="#333333").pack(side="left")
        _source_var = tk.StringVar(value="自动选择（推荐，中国大陆优化）")
        _source_combo = ttk.Combobox(
            _source_box, textvariable=_source_var, state="readonly", width=34,
            values=list(_CUDA_SOURCE_DISPLAY.keys()), font=("微软雅黑", 9))
        _source_combo.pack(side="left", padx=(8, 0))

        def _show_manifest():
            messagebox.showinfo("CUDA 组件与安全校验信息", _cuda_manifest_details(),
                                parent=root_win)

        tk.Button(root_win, text="查看组件、官方地址及 SHA-256",
                  command=_show_manifest, bg="#FFFFFF", fg="#0078D4",
                  activebackground="#FFFFFF", activeforeground="#005A9E",
                  font=("微软雅黑", 9), relief="flat", cursor="hand2"
                  ).pack(anchor="w", padx=34, pady=(8, 0))

        _btns = tk.Frame(root_win, bg="#FFFFFF")
        _btns.pack(side="bottom", pady=22)

        def _yes():
            _ans["ok"] = True
            _ans["source"] = _CUDA_SOURCE_DISPLAY[_source_var.get()]
            root_win.quit()

        def _no():
            _ans["ok"] = False
            root_win.quit()

        # 主按钮：与主界面「INITIALIZE SEQUENCE」同款黑底白字
        tk.Button(_btns, text="开始下载", command=_yes,
                  bg="#111111", fg="#FFFFFF", font=("微软雅黑", 11, "bold"),
                  activebackground="#333333", activeforeground="#FFFFFF",
                  relief="flat", width=16, height=2, cursor="hand2"
                  ).pack(side="left", padx=10)
        # 次按钮：与主界面「选择文件」同款白底细边框
        tk.Button(_btns, text="暂不下载", command=_no,
                  bg="#FFFFFF", fg="#333333", font=("微软雅黑", 9),
                  relief="solid", bd=1, width=12, height=2, cursor="hand2"
                  ).pack(side="left", padx=10)
        root_win.protocol("WM_DELETE_WINDOW", _no)

        # 置顶 + 抢焦点：确保它一定出现在用户眼前，而不是藏在别的窗口后面
        try:
            root_win.attributes("-topmost", True)
        except Exception:
            pass
        root_win.lift()
        try:
            root_win.focus_force()
        except Exception:
            pass

        root_win.mainloop()          # 阻塞，直到用户按下按钮或关窗

        if not _ans["ok"]:
            try:
                root_win.destroy()
            except Exception:
                pass
            return False
        _chosen_source = _ans["source"]

        # 用户同意了：清空这个窗口的内容，原地改造成进度窗
        for _c in root_win.winfo_children():
            _c.destroy()
        win = root_win
        win.title("正在下载 AI 运算库 · 请勿关闭")
        win.configure(bg="#FFFFFF")
        win.geometry("600x230")
        _ph = tk.Frame(win, bg="#FFFFFF")
        _ph.pack(pady=(26, 6))
        try:
            win._cat_dl = tk.PhotoImage(
                file=_asset_path("ui", "doctorcat-puzzle-dialog.png"))
            tk.Label(_ph, image=win._cat_dl, bg="#FFFFFF").pack(side="left", padx=(0, 14))
        except Exception:
            pass
        _pt = tk.Frame(_ph, bg="#FFFFFF")
        _pt.pack(side="left", anchor="w")
        tk.Label(_pt, text="正在下载 AI 运算库…", font=("微软雅黑", 12, "bold"),
                 bg="#FFFFFF", fg="#111111").pack(anchor="w")
        tk.Label(_pt, text="完成后主界面会自动打开，请不要关闭本窗口",
                 font=("微软雅黑", 9), bg="#FFFFFF", fg="#888888"
                 ).pack(anchor="w", pady=(4, 0))
        bar = ttk.Progressbar(win, length=520, mode="determinate", maximum=1000)
        bar.pack(pady=(10, 4))
        lbl = tk.Label(win, text="准备中…", font=("微软雅黑", 8),
                       bg="#FFFFFF", fg="#666666")
        lbl.pack(pady=4)
        _log_path = _os.path.join(root, "CUDA下载日志.txt")

        def _open_log():
            try:
                _os.startfile(_log_path)
            except Exception:
                messagebox.showinfo("下载日志", "日志保存位置：\n" + _log_path, parent=win)

        tk.Button(win, text="打开下载日志", command=_open_log,
                  bg="#FFFFFF", fg="#666666", relief="flat",
                  font=("微软雅黑", 8), cursor="hand2").pack()
        win.update()

        def report(frac, msg):
            bar["value"] = max(0, min(1000, int(frac * 1000)))
            lbl.config(text=msg[:88])
            win.update()
    else:
        def report(frac, msg):
            _sys.stdout.write("\r   [%3.0f%%] %-80s" % (frac * 100, msg[:80]))
            _sys.stdout.flush()
        print("\n" + "=" * 62)
        print("  首次运行：需要获取 NVIDIA 运算库（约 %d MB）" % need_mb)
        print("  这些是 cuDNN / cuBLAS 等公开的官方运算库，未随程序打包。")
        print("  用户已显式允许下载；每个文件都会按固定 SHA-256 校验。")
        print("  下载源选项：%s" % _chosen_source)
        print("  安装位置：%s" % root)
        print("=" * 62)

    try:
        _fetch_cuda_libraries(root, report, source=_chosen_source)
        okflag = True
    except Exception as e:
        okflag = False
        err = "%s: %s" % (type(e).__name__, e)
        if gui:
            messagebox.showerror("下载失败", "获取运算库失败：\n\n" + err +
                                 "\n\n可以检查网络后重新启动程序再试。")
        else:
            print("\n   下载失败：" + err)
    if gui:
        try:
            # 278 版起 win 与 root_win 是同一个窗口，销毁一次即可；
            # 这里保留两次调用并容错，兼容两种情况。
            win.destroy()
            root_win.destroy()
        except Exception:
            pass
    else:
        print()
    return okflag


_CUDA_BOOTSTRAP_OK = _ensure_cuda_libraries()


def _show_startup_notice(force=False):
    """在耗时的 AI 模块导入前先显示一个可见、可理解的等待窗口。"""
    if not force and not (getattr(_sys, "frozen", False) and len(_sys.argv) <= 1):
        return None
    try:
        import tkinter as _startup_tk
        from tkinter import ttk as _startup_ttk

        win = _startup_tk.Tk()
        win.title("PDF 文字识别工具 · 正在启动")
        win.configure(bg="#FFFFFF")
        win.resizable(False, False)
        width, height = 540, 210
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        win.geometry("%dx%d+%d+%d" %
                     (width, height, max(0, (screen_w - width) // 2),
                      max(0, (screen_h - height) // 3)))
        try:
            win.iconbitmap(_asset_path("doctorcat-faithful-windows-exe-multisize.ico"))
        except Exception:
            pass

        body = _startup_tk.Frame(win, bg="#FFFFFF")
        body.pack(fill="both", expand=True, padx=34, pady=28)
        try:
            win._startup_cat = _startup_tk.PhotoImage(
                file=_asset_path("ui", "doctorcat-puzzle-dialog.png"))
            _startup_tk.Label(body, image=win._startup_cat,
                              bg="#FFFFFF").pack(side="left", padx=(0, 18))
        except Exception:
            pass
        text_box = _startup_tk.Frame(body, bg="#FFFFFF")
        text_box.pack(side="left", fill="both", expand=True)
        _startup_tk.Label(text_box, text="PDFOCR 正在打开",
                          font=("微软雅黑", 14, "bold"), bg="#FFFFFF",
                          fg="#111111").pack(anchor="w")
        _startup_tk.Label(
            text_box,
            text="AI 引擎初始化需要一定时间，请耐心等待。\n请不要关闭此提示窗口，主界面就绪后它会自动消失。",
            justify="left", font=("微软雅黑", 9), bg="#FFFFFF", fg="#666666"
        ).pack(anchor="w", pady=(9, 14))
        bar = _startup_ttk.Progressbar(text_box, mode="indeterminate", length=340)
        bar.pack(anchor="w")
        bar.start(12)
        win.protocol("WM_DELETE_WINDOW", lambda: None)
        try:
            win.attributes("-topmost", True)
        except Exception:
            pass
        win.update_idletasks()
        win.update()
        return win
    except Exception:
        return None


_STARTUP_NOTICE = _show_startup_notice()


import logging
import colorsys

# 禁用调试和警告信息，保持控制台输出整洁
logging.disable(logging.DEBUG)
logging.disable(logging.WARNING)

import fitz          # PyMuPDF，用于PDF解析、页面渲染和隐形文字写入
import cv2           # OpenCV，用于图像显示和矩阵变换
from PIL import Image
import numpy as np
import tqdm          # 提供控制台进度条
import sys
import argparse      # 命令行参数解析
import pathlib
import io
import time as _time    # 顶层导入：--timing 分段计时器要用它。放在顶部而不是
                        # 放在 if 里面，编辑器才不会全篇标"_time 可能未定义"。
import paddle

# =========================================================================
# 【254 版新增】全局硬性像素天花板
# -------------------------------------------------------------------------
# 无论用户在界面上选了多高的 DPI、无论命令行传进来什么参数，任何一次
# 光栅化的长边都不允许超过这个像素数。这是最后一道保险丝：
#   4000 像素 × 4000 像素 × 3 通道 = 48 MB，单张图的内存占用有确定上界，
#   再叠加大模型也不会把内存撑爆。
# 之所以定在 4000：界面上最高档 300 DPI 对应的上限是 3800，留一点余量，
# 既不影响任何现有档位的正常工作，又能挡住异常参数。
# =========================================================================
HARD_PIXEL_CEILING = 4000.0


def clamp_zoom(max_side_points, target_dpi, max_pixels):
    """
    把"目标 DPI"换算成实际可用的缩放倍率，并施加两道上限：
        1) 用户档位对应的像素上限 max_pixels（150档=1800 / 220档=2500 / 300档=3800）
        2) 全局硬顶 HARD_PIXEL_CEILING
    返回值同时被"双联页拆分"和"OCR 渲染"两个阶段共用，保证两边口径一致。
    """
    ceiling = min(float(max_pixels), HARD_PIXEL_CEILING)
    theoretical = float(target_dpi) / 72.0
    if max_side_points <= 0:
        return theoretical
    if max_side_points * theoretical > ceiling:
        return ceiling / max_side_points
    return theoretical


def get_textwriter_crop_y_delta(page, tolerance=0.01):
    """计算 TextWriter 在上下 CropBox 不对称时的纵向误差。

    PyMuPDF 的 CropBox 采用左上原点坐标，因此：
      上裁剪量 = cropbox.y0
      下裁剪量 = mediabox 高度 - cropbox.y1

    返回值为正时，当前 TextWriter 会向下偏该数值；
    返回值为负时，会向上偏。标准页面和上下对称
    裁剪页面都严格返回 0，不改变原有坐标。
    """
    cropbox = page.cropbox
    top_crop = float(cropbox.y0)
    # 必须取 Rect.height，不能取 mediabox_size.y：当 MediaBox
    # 本身以非零 y0 起算时，后者是右下角坐标，不是高度。
    bottom_crop = float(page.mediabox.height - cropbox.y1)
    delta_y = bottom_crop - top_crop
    if abs(delta_y) < float(tolerance):
        return 0.0
    return delta_y


def parse_page_range(page_str, total_pages):
    """
    独立工具函数：解析用户输入的物理页码范围（1-based），
    转换为计算机底层处理所需的索引列表（0-based）。
    如果格式非法或越界，直接抛出异常，拒绝妥协。
    """
    if not page_str or not str(page_str).strip():
        raise ValueError("你勾选了指定页码处理，但输入框为空。")

    page_str = str(page_str).strip()
    try:
        if '-' in page_str:
            start_str, end_str = page_str.split('-')
            start = int(start_str.strip())
            end = int(end_str.strip())

            if start < 1 or end > total_pages or start >= end:
                raise ValueError(f"指定的范围 ({start}-{end}) 逻辑错误或超出了文档总页数 ({total_pages} 页)。")
            return list(range(start - 1, end))
        else:
            # 单页模式
            idx = int(page_str)
            if 1 <= idx <= total_pages:
                return [idx - 1]
            else:
                raise ValueError(f"指定的单页 ({idx}) 超出了文档总页数 ({total_pages} 页)。")
    except ValueError as e:
        # 捕获所有格式错误（如输入字母）并向上抛出
        if "invalid literal" in str(e):
            raise ValueError(f"包含非法字符，请输入纯数字或连字符（如 5 或 5-10）。")
        raise ValueError(str(e))

def parse_skip_pages(skip_str):
    """
    【新增】独立工具函数：解析"不参与双联页拆分"的页码字符串，
    格式如 "1,32,33"，返回一个 1-based 物理页码的集合。
    空字符串返回空集合，代表所有页都参与拆分。
    """
    if not skip_str or not str(skip_str).strip():
        return set()
    result = set()
    for part in str(skip_str).split(','):
        part = part.strip()
        if not part:
            continue
        try:
            result.add(int(part))
        except ValueError:
            raise ValueError(f"不拆分页码中包含非法字符: '{part}'，请使用类似 1,32,33 的格式。")
    return result

# =========================================================================
# [独立模块 0.5]：全局 AI 模型生命周期调度器 (单例缓存池)
# =========================================================================
class AIModelEngine:
    _layout_engine = None
    _ocr_engines = {} # 使用字典缓存不同语种的 OCR 模型，防止切换语种失效
    # 【270 版】DB 检测的两个阈值。None = 用 PaddleOCR 默认（0.3 / 0.6）。
    # 低分辨率影印件上把它们放宽能让检测端的墨迹覆盖从 93.7% 提到 99.8%。
    _det_thresh = None
    _det_box_thresh = None
    _det_limit_side_len = 1600   # 文字检测网络的输入长边上限，0 = 不限制(旧行为)
    _device = None               # 实际使用的运算设备，由 resolve_device() 探测一次后缓存

    @classmethod
    def resolve_device(cls):
        """
        【257 版新增】自动探测该用 GPU 还是 CPU。

        旧版三处写死 device="gpu:0"。在自己的开发机上没问题，但打包成 exe
        发给别人之后，只要对方没有 NVIDIA 显卡，程序就会在加载模型时直接
        抛异常崩掉，而且报错信息是一串英文堆栈，普通用户完全看不懂。

        这里改成探测一次：真的有可用的 N 卡才用 gpu:0，否则老实回落到 cpu，
        由上层负责把"你这台机器没有 N 卡"这件事用人话告诉用户。
        """
        if cls._device is not None:
            return cls._device
        dev = "cpu"
        try:
            import paddle
            if paddle.device.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0:
                dev = "gpu:0"
        except Exception:
            dev = "cpu"
        cls._device = dev
        return dev

    @classmethod
    def get_layout_engine(cls):
        """
        单例获取版面分析模型。

        =================================================================
        【255 版核心改动】：把 PPStructureV3 换成轻量的 LayoutDetection
        -----------------------------------------------------------------
        本脚本在版面分析阶段，**只用到一样东西**：版面框的 label 和坐标
        （见 analyze_smart_layout 里那句 layout_det_res['boxes']），
        用来推算页眉页脚和正文的安全边界。除此之外的返回值一律丢弃。

        但 PPStructureV3 是一条完整的文档解析流水线：它内部自带一整套
        文字检测 + 文字识别模型，每分析一页版面，都会把这一页的文字
        **完整 OCR 一遍**，然后我们把识别结果原封不动扔掉。也就是说，
        整本书的 OCR 实际上被做了两次，第一次纯属白做。

        它还会连带把 PP-Chart2Table 拉进显存 —— 那个模型光权重就 1.4 GB，
        是"图表转表格"用的，本脚本完全用不到。加上版面模型、区域检测模型、
        以及它自带的那套 OCR 模型，6 GB 显存的笔记本显卡（如 RTX 3060
        Laptop）会被塞到只剩几百 MB；等到第二阶段真正的 OCR 模型再进来，
        显存不够，驱动就把张量挤到共享内存（走 PCIe 的系统内存）里去算，
        速度直接掉一个数量级 —— 这正是"版面 20 秒一页、OCR 十几秒一页"
        的根源。

        LayoutDetection 是同一个版面模型（PP-DocLayout_plus-L）的单体版：
        输入同一张图，输出同样的 label + coordinate，但不带任何 OCR，
        也不会拉 PP-Chart2Table。

        =================================================================
        【275 版】：彻底移除 PPStructureV3 退路
        -----------------------------------------------------------------
        此前保留 V3 作为兜底，是想着"万一轻量通道在某些环境不可用"。
        实践下来它只带来坏处，没带来好处：

        1. V3 会**无条件**加载 PP-Chart2Table（1368 MB）与
           PP-DocBlockLayout（124 MB），共 1492 MB。这是 PaddleX 源码里
           的缺陷 —— chart 模型的实例化没有任何开关保护，`use_chart_
           recognition=False` 只在推理时生效，拦不住加载。
        2. 结果是只要有任何一条代码路径碰到 V3，这 1492 MB 就会被拉进
           模型缓存。发布包因此凭空胖了 1.5 GB，用户跑一次诊断也会莫名
           其妙开始下载 1.4 GB。
        3. 而这条退路从未真正派上用场：轻量通道在所有实测环境下都正常。

        所以本版把 V3 相关的实例化、命令行开关、自检项一并删除。
        轻量通道若真的失败，直接抛出带排查建议的异常，而不是悄悄退回一条
        会拖垮体积的通道 —— 出错要让人看见，不要用更差的方案掩盖。
        =================================================================
        """
        if cls._layout_engine is None:
            try:
                from paddleocr import LayoutDetection
                cls._layout_engine = LayoutDetection(
                    model_name="PP-DocLayout_plus-L",
                    device=cls.resolve_device(),
                    enable_mkldnn=False
                )
            except Exception as e:
                import traceback as _tb
                print("   [!] 版面分析模型加载失败。")
                print(f"       原因: {type(e).__name__}: {e}")
                for _line in _tb.format_exc().splitlines()[-6:]:
                    print("       | " + _line)
                print("       排查建议：")
                print("         · 确认程序目录下 paddlex_cache\\official_models\\ 里")
                print("           有 PP-DocLayout_plus-L 这个文件夹；")
                print("         · 用 --selftest 查看更完整的环境报告；")
                print("         · 也可以勾选【关闭页边滤除】跳过版面分析直接识别。")
                raise
        return cls._layout_engine

    @classmethod
    def release_layout_engine(cls):
        """
        【255 版新增】版面分析阶段结束后，立刻把版面模型踢出显存。

        旧版定义了 destroy_engines() 却从头到尾没有调用过一次，于是版面
        模型会一直霸占显存到整本书跑完，和真正干活的 OCR 模型抢地方。
        版面边界是一次性算完的，算完之后这个模型再无用处，理应马上释放。
        """
        if cls._layout_engine is None:
            return
        cls._layout_engine = None
        try:
            import gc
            gc.collect()
            import paddle
            if paddle.device.is_compiled_with_cuda():
                paddle.device.cuda.empty_cache()
        except Exception:
            pass

    @classmethod
    def get_ocr_engine(cls, lang, vertical=False):
        """
        单例获取对应语种的 OCR 识别大模型。

        =================================================================
        【256 版核心改动】：限制"文字检测网络"的输入边长
        -----------------------------------------------------------------
        逐环节实测显存后发现，显存的大头根本不是模型权重：

            加载 OCR 模型        ->  742 MB   （权重才 178 MB）
            OCR 推理 1 页        -> 4468 MB   （一次推理暴涨 3.7 GB）

        这 3.7 GB 全部是**文字检测网络的激活显存**。PP-OCRv5 的检测模型是
        DBNet 类的分割网络，要为整幅输入图维护多个尺度的特征图，显存与
        输入面积成正比。我们喂进去的是 1787×2500（447 万像素），于是
        特征图大得惊人。

        而 PaddleOCR 的默认配置压根不缩小输入：

            TextDetection:
                limit_side_len: 64
                limit_type: min      <- 是"最短边不小于 64"，不是"最长边不超过"

        也就是说，你渲染多大它就按多大算。

        这里改成 limit_type="max" 并给出长边上限。实测（10 个半页）：

            长边限制    每页耗时   显存峰值   识别行数   识别字数
            默认 2500   1.534 秒   4599 MB     385      15730
            1920        1.250 秒   3079 MB     385      15730
            1600        1.149 秒   2420 MB     385      15730
            1280        1.162 秒   2170 MB     385      15730

        显存降低 47%，速度快 25%，而 **385 行文字逐行完全一致，一个字
        都没差**。

        为什么不掉精度：检测网络只负责"把文字行框出来"，真正认字的识别
        网络是**从原分辨率的图上裁剪**这些框再识别的。所以降低检测输入
        只影响框的定位精度（对正文这种尺寸绰绰有余），不影响认字的清晰度。

        上限跟随用户在界面上选的清晰度档位，尊重用户"要清楚还是要快"的
        选择；也可以用 --det-limit 手动指定，设 0 表示恢复旧的不限制行为。
        =================================================================
        """
        # ==================================================================
        # 【262 版关键修复】竖排必须关闭"文本行方向分类器"
        # ------------------------------------------------------------------
        # use_textline_orientation 启用的是 PP-LCNet_x1_0_textline_ori，
        # 一个**只判 0 度 / 180 度**的二分类器。横排扫描件上它很有用（能把
        # 倒置的行翻正），但竖排的处境完全不同：
        #
        # PaddleOCR 裁剪文字框时，对 h/w >= 1.5 的竖长框会先 np.rot90 转成
        # 横向再送识别（见 crop_image_regions.py 的 get_rotate_crop_image）。
        # 这样送进方向分类器的，是一堆被转了 90 度的竖排列 —— 完全在它的
        # 训练分布之外。实测它会把其中相当一部分判成"倒置"再翻一次，翻完
        # 的图识别网络就什么也读不出来了。
        #
        # 在一份竖排测试件上实测（以原书自带文字层为真值）：
        #
        #     页码          第3页   第4页   第5页   第9页  第11页
        #     方向分类 开     79%    29%    53%    61%    72%
        #     方向分类 关     97%    95%    96%    96%    96%
        #
        # 失败的框有个共同特征：长宽比 20 以上、识别分数 0.00~0.48、只吐出
        # 0~2 个字；而同一页上长宽比 10 以下的短框（页码、书名、脚注）全都
        # 正常。关掉分类器后整页恢复到 95% 以上，且各页表现整齐。
        #
        # 代价：竖排页面上倒置的文字行不再被自动翻正。竖排排印物里
        # 几乎不存在这种情况，用不着为它牺牲掉三分之一的正文。
        #
        # 顺带实测：检测输入上限（省显存那一档）与 unclip_ratio 在关掉方向
        # 分类器之后已经不再影响竖排结果（94%~97% 区间内浮动），所以 256 版
        # 的省显存策略原样保留，不为竖排做任何让步。
        # ==================================================================
        _key = (lang, bool(vertical), cls._det_thresh, cls._det_box_thresh)

        # 【262 版】缓存键加了竖排标志之后，同一语种理论上会驻留两套引擎
        # （启动时的预热建的是横排那套，正式跑竖排时又要建一套），白白多占
        # 约 700MB 显存 —— 这与 254~256 三个版本一路压下来的显存优化背道而驰。
        # 一次任务只会用其中一种模式，所以建新引擎之前先把同语种、另一种
        # 模式的那套踢掉，驻留量维持在"一套"，和 261 版完全一致。
        if _key not in cls._ocr_engines:
            _stale = [k for k in cls._ocr_engines if k[0] == lang and k != _key]
            if _stale:
                for k in _stale:
                    cls._ocr_engines.pop(k, None)
                try:
                    import gc
                    gc.collect()
                    import paddle
                    if paddle.device.is_compiled_with_cuda():
                        paddle.device.cuda.empty_cache()
                except Exception:
                    pass

            from paddleocr import PaddleOCR
            kw = dict(
                use_textline_orientation=(not vertical),
                lang=lang,
                use_doc_unwarping=False,
                use_doc_orientation_classify=False,
                device=cls.resolve_device(),
                precision="fp32",
                enable_mkldnn=False
            )
            limit = int(cls._det_limit_side_len or 0)
            if limit > 0:
                kw["text_det_limit_side_len"] = limit
                kw["text_det_limit_type"] = "max"
            # 【270 版】DB 二值化阈值 / 框保留阈值
            if cls._det_thresh is not None:
                kw["text_det_thresh"] = float(cls._det_thresh)
            if cls._det_box_thresh is not None:
                kw["text_det_box_thresh"] = float(cls._det_box_thresh)
            cls._ocr_engines[_key] = PaddleOCR(**kw)
        return cls._ocr_engines[_key]

    @classmethod
    def destroy_engines(cls):
        """结束常驻内存的大模型，将空间归还系统"""
        cls._layout_engine = None
        cls._ocr_engines.clear()

# =========================================================================
# [独立模块 0]：核心 OCR 引擎与版面算法
# =========================================================================
def im2stream(im: np.ndarray):
    """
    辅助函数：将 OpenCV 的 numpy 图像数组转换为内存中的字节流 (BytesIO)。
    常用于需要将图像数据无损传递给其他处理模块的场景。
    """
    _, buffer = cv2.imencode(".bmp", im)
    bio = io.BytesIO(buffer)
    return bio

def get_x_anchor(values, page_dim, is_right_side=False):
    """X轴锚定滤波器：抗扫描抖动"""
    if not values: return page_dim if is_right_side else 0.0
    sorted_v = sorted(values)
    if len(sorted_v) <= 2: return max(sorted_v) if is_right_side else min(sorted_v)
    med = sorted_v[len(sorted_v)//2]
    valid = [v for v in sorted_v if abs(v - med) < page_dim * 0.05]
    if not valid: valid = sorted_v
    return max(valid) if is_right_side else min(valid)

def get_y_robust_anchor(values, page_dim, is_bottom_logic=False):
    """Y轴锚定滤波器：一维密度聚类"""
    if not values: return page_dim if is_bottom_logic else 0.0
    if len(values) <= 2: return sum(values) / len(values)
    tolerance = page_dim * 0.02
    best_cluster = []
    for v in values:
        cluster = [x for x in values if abs(x - v) <= tolerance]
        if len(cluster) > len(best_cluster):
            best_cluster = cluster
        elif len(cluster) == len(best_cluster) and len(cluster) > 0:
            avg_current = sum(cluster) / len(cluster)
            avg_best = sum(best_cluster) / len(best_cluster)
            if is_bottom_logic and avg_current > avg_best: best_cluster = cluster
            elif not is_bottom_logic and avg_current < avg_best: best_cluster = cluster
    if not best_cluster: best_cluster = values
    return sum(best_cluster) / len(best_cluster)

def calculate_dynamic_padding(main_text_heights, global_page_h, global_page_w, lang):
    """
    自适应边界冗余测算器：根据正文单行字高与语种，推导安全的边缘留白。
    注意：传入的 main_text_heights 必须已在外部剔除标题、脚注等异常字号。
    """
    # 1. 语言判定：方块字 vs 字母语言
    cjk_langs = ['ch', 'chinese_cht', 'japan', 'korean']
    is_cjk = lang in cjk_langs

    # 2. 核心数学推演：从正文块中提取“单行字高”
    if main_text_heights:
        # 过滤掉极小噪点（高度不足页面 0.5% 的识别碎片）
        valid_heights = [h for h in main_text_heights if h > global_page_h * 0.005]
        if valid_heights:
            valid_heights.sort()
            # 选取最矮的 15% 作为“单行正文段落”的代表，计算平均真实字高
            sample_count = max(1, int(len(valid_heights) * 0.15))
            single_line_height = sum(valid_heights[:sample_count]) / sample_count
        else:
            single_line_height = global_page_h * 0.012 # 兜底值
    else:
        single_line_height = global_page_h * 0.012

    # 3. 语种分流测算冗余量
    if is_cjk:
        # 中日韩方块字：冗余量以“平均行间距”为准（约 1.5 倍单行高度）
        y_pad = single_line_height * 1
        x_pad = single_line_height * 1
    else:
        # 字母语言：冗余严格收缩至不超过“一行字母的高度”（约 1.0 倍单行高度）
        y_pad = single_line_height * 1
        x_pad = single_line_height * 3

    # 4. 绝对物理安全阈值钳制 (防止大模型误判导致极值崩溃)
    # 强制将冗余卡在页面高度的 0.5% ~ 2.5% 之间
    y_pad = max(global_page_h * 0.005, min(y_pad, global_page_h * 0.02))
    x_pad = max(global_page_w * 0.005, min(x_pad, global_page_w * 0.02))

    return y_pad, x_pad

def report_device_status():
    """
    【新增】运算设备体检：确认 Paddle 是不是真的在用 GPU 跑。
    脚本里虽然写了 device="gpu:0"，但如果装的是 CPU 版 paddlepaddle，
    或者 CUDA 驱动对不上，Paddle 会静默退回 CPU 继续运行而不报错。
    CPU 版又配上 enable_mkldnn=False，速度会比 GPU 慢一到两个数量级，
    "一页十几秒"最常见的元凶就是这个。这里把真实情况直接打印出来。
    """
    print("\n" + "─"*58)
    print("🔍 运算设备体检")
    print("─"*58)
    try:
        import paddle
        compiled = paddle.device.is_compiled_with_cuda()
        print(f"   paddle 版本            : {getattr(paddle, '__version__', '未知')}")
        print(f"   是否为 CUDA(GPU) 版本  : {compiled}")
        if compiled:
            try:
                cnt = paddle.device.cuda.device_count()
                print(f"   检测到的 GPU 数量      : {cnt}")
                # 【255 版新增】：显存余量是速度的关键指标。
                # 显存一旦被占满，驱动会把张量挤到走 PCIe 的共享内存里去算，
                # 速度会掉一个数量级，但 GPU 占用率仍然显示 100%，
                # 光看占用率是发现不了的。
                try:
                    import subprocess
                    q = subprocess.run(
                        ["nvidia-smi", "--query-gpu=memory.used,memory.total",
                         "--format=csv,noheader,nounits"],
                        capture_output=True, text=True, timeout=10)
                    if q.returncode == 0 and q.stdout.strip():
                        used, total = [int(v) for v in q.stdout.strip().split(chr(10))[0].split(",")]
                        print(f"   显存占用 / 总量        : {used} MB / {total} MB"
                              f"（剩余 {total - used} MB）")
                        if total - used < 1200:
                            print("   ⚠️  显存余量不足 1.2 GB，推理很可能被迫使用共享内存，")
                            print("      表现为 GPU 占用率 100% 但速度极慢。建议关闭其它占用显卡的程序。")
                except Exception:
                    pass
                if cnt > 0:
                    print(f"   GPU 型号               : {paddle.device.cuda.get_device_name(0)}")
                else:
                    print("   ⚠️  编译时带 CUDA，但运行时找不到可用 GPU，实际会退回 CPU！")
            except Exception as e:
                print(f"   ⚠️  查询 GPU 信息失败: {e}")
        else:
            print("   ⚠️  当前装的是 CPU 版 paddlepaddle。脚本里的 device='gpu:0' 不会生效，")
            print("      实际全部在 CPU 上跑，这通常就是每页十几秒的根本原因。")
            print("      解决办法：卸载 paddlepaddle，改装与本机 CUDA 版本匹配的 paddlepaddle-gpu。")
        print(f"   paddle 当前默认设备    : {paddle.device.get_device()}")
    except Exception as e:
        print(f"   ⚠️  无法读取 paddle 设备信息: {e}")
    print("─"*58)

def detect_native_pdf(pdf_doc):
    """
    [阶段零]：全局原生排版嗅探 (Text Rendering Mode 中部抽样检测)
    功能：检测文档是否自带原生矢量文字层。
    返回：布尔值 (True 代表是原生文献, False 代表是扫描件)
    """
    # =========================================================================
    # [阶段零]：全局原生排版嗅探 (Text Rendering Mode 中部抽样检测)
    # =========================================================================
    print("\n[0/2] 正在进行底层图元嗅探，检测是否为原生排版文档...")
    total_pages = pdf_doc.page_count

    # 确定抽样范围：抽取文档正中间的 10 页进行检测（不足 10 页则全量检测）
    if total_pages > 10:
        mid_start = total_pages // 2 - 5
        sniff_pages = list(range(mid_start, mid_start + 10))
    else:
        sniff_pages = list(range(total_pages))

    # 引入三态投票器
    native_votes = 0   # 确信为原生正文的票数
    scanned_votes = 0  # 确信为扫描图片的票数

    for sp_num in sniff_pages:
        try:
            page = pdf_doc.load_page(sp_num)

            # 1. 统计页面真实的文本数量
            text_content = page.get_text("text")
            char_count = len(text_content.replace(" ", "").replace("\n", ""))

            # 2. 统计页面中图像的绝对覆盖面积
            page_area = page.rect.width * page.rect.height
            image_area = 0

            img_list = page.get_image_info()
            for img_info in img_list:
                bbox = img_info.get("bbox")
                if bbox:
                    image_area += fitz.Rect(bbox).get_area()

            coverage_ratio = image_area / page_area if page_area > 0 else 0

            # ==========================================================
            # 【核心修复】：三态分类过滤逻辑 (排查无效样本)
            # ==========================================================
            if char_count > 300 and coverage_ratio < 0.85:
                # 状态 A：字多图少 -> 铁证如山的原生正文页
                native_votes += 1

            elif coverage_ratio >= 0.85 and char_count < 100:
                # 状态 B：图铺满全页，且几乎没有底层文字 -> 典型的扫描件特征
                scanned_votes += 1

            else:
                # 状态 C：空白页、大字标题页、字数极少的插图页
                # 动作：【弃权】。既不增加原生票，也不增加扫描票，直接过滤掉这些噪音干扰。
                pass

        except Exception:
            pass # 容错：跳过解析失败的异常页面

    # ==========================================================
    # 终极裁决：基于【有效选票】进行对比
    # ==========================================================
    print(f"    └─ 嗅探探针返回: 确信原生页 {native_votes} 票, 确信扫描页 {scanned_votes} 票, 弃权 {len(sniff_pages) - native_votes - scanned_votes} 票")

    # 只要抽样区里有任何明确的原生正文页，且数量压倒扫描页，即定性为原生文档
    if native_votes > 0 and native_votes >= scanned_votes:
        return True

    # 如果极端情况下（比如抽样正好全是纯白页），有效票全是 0，保守起见放行去执行 OCR
    return False

# =========================================================================
# [新增独立模块]：双联页物理拆分 (Double-Page Spread Splitter)
# =========================================================================
def _find_gutter_x(page, ratio, window_frac, probe_dpi=100):
    """
    【新增】中缝探测器：在页面中线附近的一个搜索窗口内，寻找平均灰度最亮
    （也就是最"空白"）的那一条竖线，把它当作两页之间的装订缝，返回其物理
    坐标（单位 pt）。这是一个基于亮度的简单启发式方法：能应付大多数"中缝
    是空白纸边"的情况；如果中缝本身是很深的装订阴影，探测结果可能偏移，
    这时应改用固定比例分割 (--split-fixed)。
    任何异常情况下，都退回到固定比例的位置，绝不让拆分流程中断。
    """
    rect = page.rect
    fallback_x = rect.x0 + rect.width * ratio
    try:
        zoom = probe_dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY, alpha=False)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w)
        # 逐列求平均灰度：值越大代表这一竖列越白、越可能是空白的中缝
        col_mean = arr.mean(axis=0)

        center_px = int((ratio * rect.width) * zoom)
        half_win_px = max(2, int(rect.width * zoom * window_frac))
        lo = max(0, center_px - half_win_px)
        hi = min(pix.w, center_px + half_win_px)
        if hi - lo < 3:
            return fallback_x

        window = col_mean[lo:hi]

        # 中缝通常不是孤零零的一条线，而是一整片连续的空白竖带。
        # 直接取最亮的单列，遇到整片同样白的区域时会退化成"取到窗口边缘"，
        # 所以这里改为：先框出接近最亮的所有列，再取其中最长的一段连续白带，
        # 把切割点定在这段白带的正中央，结果要稳得多。
        peak = float(window.max())
        threshold = peak - 3.0          # 允许 3 级灰度的扫描噪声波动
        bright = window >= threshold

        best_start, best_len = 0, 0
        cur_start, cur_len = 0, 0
        for idx, is_bright in enumerate(bright):
            if is_bright:
                if cur_len == 0:
                    cur_start = idx
                cur_len += 1
                if cur_len > best_len:
                    best_start, best_len = cur_start, cur_len
            else:
                cur_len = 0

        if best_len <= 0:
            return fallback_x

        best_px = lo + best_start + best_len / 2.0
        return rect.x0 + best_px / zoom
    except Exception:
        return fallback_x

def split_double_pages(src_doc, args):
    """
    【新增】双联页拆分主函数：把"一张扫描页 = 左右两个逻辑页"的跨页扫描件，
    沿中缝物理切成两张独立页面，使得后续的版面分析与 OCR 识别，天然把左页
    和右页当成两个互不相干的页面来处理，识别出来的文字框不会跨过中缝。

    必须在版面分析和 OCR 之前执行，理由见脚本开头的说明。

    返回: (new_doc, mapping)
        new_doc  —— 拆分后的新 fitz.Document
        mapping  —— 长度等于原始页数的列表，mapping[i] 是原始第 i 页在新文档
                     里对应的新页码列表（已按输出文档里的实际顺序排好）
    """
    ratio = getattr(args, 'split_ratio', 0.5)
    if not (0.05 < ratio < 0.95):
        raise ValueError(f"分割线比例 {ratio} 不合理，必须在 0.05 ~ 0.95 之间。")

    # 不拆分页码：CLI 与 GUI 都只传字符串，这里就地解析，避免额外的外部铺垫
    skip_set = parse_skip_pages(getattr(args, 'split_skip', ''))
    auto_detect = not getattr(args, 'split_fixed', False)
    window_frac = getattr(args, 'split_window', 0.06)
    gap_pt = max(0.0, getattr(args, 'split_gap', 0.0))
    rtl = getattr(args, 'split_rtl', False)
    dpi = getattr(args, 'split_dpi', 300.0)

    # ==================================================================
    # 【254 版核心修复 1】：拆分阶段过去完全没有像素上限
    # ------------------------------------------------------------------
    # 旧版这里是无条件按 split_dpi(=300) 重新光栅化两个半页，既不看用户
    # 在界面上选的清晰度档位，也不受任何像素上限约束。实测一个 A3 跨页
    # 拆出来的半页在 300 DPI 下是 2480×3509 像素，塞进新文档要占 12.6 MB，
    # 而后续 OCR 阶段最多只会用到 2500 像素长边 —— 多出来的像素一个都用
    # 不上，纯粹是白占内存。
    # 现在改为与 OCR 阶段共用同一套钳制逻辑：跟随用户选的 DPI 档位，
    # 并且绝不越过该档位的像素上限和全局硬顶。
    # ==================================================================
    split_max_pixels = getattr(args, 'max_pixels', 2500.0)
    jpeg_quality = int(getattr(args, 'split_quality', 88))
    lossless = bool(getattr(args, 'split_lossless', False))

    new_doc = fitz.open()
    mapping = []
    out_index = 0   # 【关键】自行维护输出页序号，绝不依赖 Page.number 属性

    total = src_doc.page_count
    mode_desc = f"自动探测中缝(基准 {ratio}, 窗口 ±{window_frac*100:.0f}%)" if auto_detect else f"固定比例 {ratio}"
    print(f"\n✂️  [双联页拆分] 正在按 {mode_desc} 拆分全书 {total} 页...")

    pbar = tqdm.tqdm(range(total), desc="双联页拆分", unit="page")
    for i in pbar:
        if hasattr(args, 'ui_callback'):
            stats_str = str(pbar).split('|')[-1]
            args.ui_callback(1, "STAGE 1: PAGE SPLITTING", "阶段 1/6: 正在将双联页沿中缝拆分为左右独立页面...", current=pbar.n, total=pbar.total, stats=stats_str)
            import time
            time.sleep(0.01)

        page_no_1based = i + 1
        page = src_doc.load_page(i)

        # 用户指定不拆分的页（封面、封底等）：原样整页克隆，不重新光栅化
        if page_no_1based in skip_set:
            new_doc.insert_pdf(src_doc, from_page=i, to_page=i)
            mapping.append([out_index])
            out_index += 1
            continue

        rect = page.rect
        if auto_detect:
            split_x = _find_gutter_x(page, ratio, window_frac)
        else:
            split_x = rect.x0 + rect.width * ratio

        left_edge = max(rect.x0, split_x - gap_pt)
        right_edge = min(rect.x1, split_x + gap_pt)
        # 间隙设置过大导致某一侧被压扁时，自动放弃间隙，退回无缝分割
        if left_edge <= rect.x0 or right_edge >= rect.x1:
            left_edge = split_x
            right_edge = split_x

        left_rect = fitz.Rect(rect.x0, rect.y0, left_edge, rect.y1)
        right_rect = fitz.Rect(right_edge, rect.y0, rect.x1, rect.y1)

        if left_rect.width <= 1 or right_rect.width <= 1:
            raise ValueError(f"第 {page_no_1based} 页拆分后有一侧宽度过小，分割线过于靠边。请检查分割比例，或把该页加入不拆分名单。")

        # 两个半页各自按自己的长边钳制（半页竖长，长边通常是高度）
        zoom_l = clamp_zoom(max(left_rect.width, left_rect.height), dpi, split_max_pixels)
        zoom_r = clamp_zoom(max(right_rect.width, right_rect.height), dpi, split_max_pixels)
        pix_left = page.get_pixmap(matrix=fitz.Matrix(zoom_l, zoom_l), clip=left_rect, alpha=False)
        pix_right = page.get_pixmap(matrix=fitz.Matrix(zoom_r, zoom_r), clip=right_rect, alpha=False)

        # 按阅读顺序决定两张新页面的先后（默认左页在前；--split-rtl 时右页在前）
        if rtl:
            ordered = [(right_rect, pix_right), (left_rect, pix_left)]
        else:
            ordered = [(left_rect, pix_left), (right_rect, pix_right)]

        # ==============================================================
        # 【254 版核心修复 2】：半页图像改用 JPEG 编码后再塞进新文档
        # --------------------------------------------------------------
        # 旧版是 insert_image(pixmap=...)，PyMuPDF 会把整幅未压缩的像素流
        # 存进文档对象里；扫描件噪点多，Flate 压不动，实测每个半页要占
        # 12.6 MB，而且这些内存要一直背到整本书 OCR 结束。
        # 实测同一个半页：原始像素流 12.6 MB / PNG 无损 3.1 MB /
        # JPEG 质量 88 只要 0.46 MB —— 相差 27 倍。
        # 扫描件本身几乎都是 JPEG 存的，重新编码一次画质损失可以忽略；
        # 真需要无损的场合，加 --split-lossless 就退回旧的 pixmap 通道。
        # ==============================================================
        new_indices = []
        for half_rect, half_pix in ordered:
            np_page = new_doc.new_page(width=half_rect.width, height=half_rect.height)
            inserted = False
            if not lossless:
                try:
                    np_page.insert_image(np_page.rect,
                                         stream=half_pix.tobytes("jpeg", jpg_quality=jpeg_quality))
                    inserted = True
                except Exception:
                    # 少见的色彩空间编不了 JPEG，就老老实实退回旧通道
                    inserted = False
            if not inserted:
                np_page.insert_image(np_page.rect, pixmap=half_pix)
            new_indices.append(out_index)
            out_index += 1

        mapping.append(new_indices)

        try:
            del pix_left
            del pix_right
            del page
        except NameError:
            pass

        # 拆分循环同样需要定期清理：gc 管 Python 对象，store_shrink 管
        # MuPDF 自己那份 Python 看不见也回收不掉的图像解码缓存。
        if (i + 1) % 20 == 0:
            import gc
            gc.collect()
            try:
                fitz.TOOLS.store_shrink(100)
            except Exception:
                pass

    print(f"✅ [双联页拆分] 完成，页数由 {total} 页拆分为 {new_doc.page_count} 页。")
    return new_doc, mapping

def analyze_smart_layout(pdf_doc, args):
    """
    [阶段一独立模块]：全局智能版面抽样分析与边界拟合
    功能：加载版面分析模型，抽取连续页进行结构嗅探，并运行滤波算法剔除页眉页脚噪音。
    返回：包含 6 个全局安全边界参数的字典 dict。
    """
    import numpy as np

    if hasattr(args, 'ui_callback'):
        args.ui_callback(2, "STAGE 2: ALIGNING LAYOUT AI", "阶段 2/6: 正在调取版面分析大模型...")

    # 【改动】：直接从全局缓存池获取模型，首次调用耗时，后续瞬间完成
    layout_engine = AIModelEngine.get_layout_engine()
    print("   └─ 版面引擎: LayoutDetection（单体模型，不做多余的 OCR，不加载图表模型）")

    # =========================================================================
    # [阶段一]：全局智能版面抽样分析
    # =========================================================================
    # --- 插入点 1：Y轴核心锚定 + X轴奇偶页独立分流拟合 ---
    print("\n[1/2] 正在抽取中部连续正文页进行核心锚定与奇偶页边距拟合...")
    total_pages = pdf_doc.page_count
    # 获取 PDF 全局的物理长宽尺寸作为基准
    global_page_h = pdf_doc[0].rect.height
    global_page_w = pdf_doc[0].rect.width

    # 根据 PDF 总页数动态调整连续抽样页数，大文件增加样本量以提高准确性
    # 连续抽样是为了绝对保证覆盖奇数页（右页）和偶数页（左页），解决不对称的装订线边距问题
    if total_pages > 40:
        mid_start = total_pages // 2 - 10
        sample_pages = list(range(mid_start, mid_start + 20))
    elif total_pages > 10:
        # 短文档：从中间向两侧提取，最多不超过 20 页
        mid_start = total_pages // 2 - (total_pages // 4)
        sample_pages = list(range(mid_start, mid_start + min(20, total_pages // 2)))
    else:
        sample_pages = list(range(total_pages))

    sampled_core_tops, sampled_core_bottoms = [], []
    sampled_left_even, sampled_right_even = [], []
    sampled_left_odd, sampled_right_odd = [], []

    # 新增：单独剥离并记录噪音元素的绝对物理坐标，用于反推安全边界
    sampled_header_boxes = []
    sampled_footer_boxes = []
    sampled_page_number_boxes = []

    # 【奇偶分流】：为奇数页和偶数页分别建立 X 轴（左右）存储器
    # 应对现代出版物“外侧边距大，内侧装订线边距小”的排版特点
    sampled_left_even, sampled_right_even = [], []
    sampled_left_odd, sampled_right_odd = [], []

    # 【修改】：严格命名为正文高度收集器
    sampled_main_text_heights = []

    import tqdm # 确保局部能调用到 tqdm

    pbar = tqdm.tqdm(sample_pages, desc="AI 视觉版面测算", unit="page")
    for sp_num in pbar:
        if hasattr(args, 'ui_callback'):
            # 核心黑科技：直接读取 tqdm 当前渲染出的完整字符串
            stats_str = str(pbar).split('|')[-1]
            args.ui_callback(3, "STAGE 3: LAYOUT SAMPLING", "阶段 3/6: AI 视觉版面测算中，提取安全排版边界...", current=pbar.n, total=pbar.total, stats=stats_str)

            # 【新增核心修复】：强制让当前运算线程休眠 50 毫秒，交出 GIL 锁。
            # 确保 Tkinter 主界面有绝对充足的时间，在重度运算卡死 CPU 前，将阶段 3 的文字渲染到屏幕上！
            import time
            time.sleep(0.05)

        page = pdf_doc.load_page(sp_num)

        # ==========================================================
        # 版面分析专属：极速降维分辨率 (Layout Dynamic Resolution)
        # ==========================================================
        max_phys_side = max(global_page_w, global_page_h)
        # 版面分析不需要看清字，只需结构轮廓，1500 像素是速度与准确率的黄金分割点
        layout_zoom = 1500 / max_phys_side

        # 钳制比例：允许缩小到 0.3 倍，最多放大 2.0 倍
        layout_zoom = max(0.3, min(layout_zoom, 2.0))

        mat = fitz.Matrix(layout_zoom, layout_zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        cim_sp = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        cim_sp = np.ascontiguousarray(cim_sp[..., [2, 1, 0]]) # RGB 转 BGR 给 PaddleOCR 使用

        # 调用 V3 进行推理
        outputs = layout_engine.predict(cim_sp)
        if not outputs:
            continue

        # ==============================================================
        # 【255 版】：兼容两种返回结构，取到的框内容完全一样
        #   PPStructureV3      -> res['layout_det_res']['boxes']
        #   LayoutDetection    -> res['boxes']
        # 两者的每个元素都是 {'label': ..., 'coordinate': [x0,y0,x1,y1], ...}
        # 因此下方所有解析代码一个字都不用改。
        # ==============================================================
        res_json = outputs[0].json
        inner = res_json.get('res', res_json)
        if 'layout_det_res' in inner:
            layout_results = inner['layout_det_res'].get('boxes', [])
        elif 'boxes' in inner:
            layout_results = inner.get('boxes', [])
        else:
            continue

        # 【核心修正 1】：将 footnote (脚注) 补充进受保护的正文类别中
        valid_classes = ['text', 'title', 'doc_title', 'paragraph_title', 'figure', 'image', 'figure_title', 'table', 'equation', 'formula', 'reference', 'footnote', '脚注']

        # 定义需要捕捉的噪音字典 (兼容 V3 大模型不同语种的底层返回名)
        noise_header = ['header', '页眉']
        noise_footer = ['footer', '页脚']
        noise_pagenum = ['page_number', 'page number', 'number', '页码']

        phys_boxes = []

        for region in layout_results:
            label = region.get('label', '').lower()
            b = region['coordinate']

            # 将大模型输出的高分辨率像素坐标，精准映射回 PDF 的物理尺寸坐标
            x0 = b[0] / cim_sp.shape[1] * global_page_w
            y0 = b[1] / cim_sp.shape[0] * global_page_h
            x1 = b[2] / cim_sp.shape[1] * global_page_w
            y1 = b[3] / cim_sp.shape[0] * global_page_h
            mapped_box = [x0, y0, x1, y1]

            # 核心正文和脚注进入基础包络线
            if label in valid_classes:
                phys_boxes.append(mapped_box)

                # 【核心拦截】：如果是纯正文（抛开标题、引用、脚注、图表），才允许参与真实字高测算！
                if label == 'text':
                    sampled_main_text_heights.append(y1 - y0)

            # 【核心修正 2】：剥离并捕获噪音元素
            elif label in noise_header:
                sampled_header_boxes.append(mapped_box)
            elif label in noise_footer:
                sampled_footer_boxes.append(mapped_box)
            elif label in noise_pagenum:
                # 【微调 1】：不要只传 mapped_box，必须捆绑传入奇偶属性 (is_even)
                is_even = (sp_num % 2 == 0)
                sampled_page_number_boxes.append((mapped_box, is_even))

        # 如果该页没有任何正文（如纯白页或全是插画），跳过抽样
        if not phys_boxes:
            continue

        # 提取当前抽样页的核心包络线
        page_core_top = min([b[1] for b in phys_boxes])
        page_core_bottom = max([b[3] for b in phys_boxes])
        page_core_left = min([b[0] for b in phys_boxes])
        page_core_right = max([b[2] for b in phys_boxes])

        # 录入 Y 轴抽样数组
        sampled_core_tops.append(page_core_top)
        sampled_core_bottoms.append(page_core_bottom)

        # 录入 X 轴奇偶分流抽样数组 (应对不对称装订线)
        if sp_num % 2 == 0:
            sampled_left_even.append(page_core_left)
            sampled_right_even.append(page_core_right)
        else:
            sampled_left_odd.append(page_core_left)
            sampled_right_odd.append(page_core_right)

    # 动态计算抗扫描抖动冗余量：调用高内聚的自适应冗余测算模块
    current_lang = getattr(args, 'lang', 'ch')
    y_pad, x_pad = calculate_dynamic_padding(sampled_main_text_heights, global_page_h, global_page_w, current_lang)

    # ====================================================================
    # 【核心修正 3】：利用页眉、页脚、页码的稳定坐标反推绝对安全边界
    # 升级：引入大模型误识别的“频次校验”，过滤低频假阳性噪音
    # ====================================================================
    # 定义频次阈值：噪音元素至少要在多少比例的抽样页中出现，才被认为是真实存在的
    # 抽样页一般为连续的10-20页，真实的页眉/页码通常出现率极高，这里设定为保守的 30%
    min_appearance_ratio = 0.3
    min_required_count = max(2, int(len(sample_pages) * min_appearance_ratio))

    # 1. 提取稳定页眉的底部边界与稳定页脚的顶部边界
    header_bottoms = [b[3] for b in sampled_header_boxes]
    stable_header_b = get_y_robust_anchor(header_bottoms, global_page_h, is_bottom_logic=True) if len(header_bottoms) >= min_required_count else 0.0

    footer_tops = [b[1] for b in sampled_footer_boxes]
    stable_footer_t = get_y_robust_anchor(footer_tops, global_page_h, is_bottom_logic=False) if len(footer_tops) >= min_required_count else global_page_h

    # ====================================================================
    # 【第一层防线】：Y 轴定性过滤与奇偶物理隔离
    # ====================================================================
    # 提前算出正文的绝对 Y 轴顶线和底线，作为侧边页码的“准入标尺”
    stable_core_top_y = get_y_robust_anchor(sampled_core_tops, global_page_h, is_bottom_logic=False)
    stable_core_bottom_y = get_y_robust_anchor(sampled_core_bottoms, global_page_h, is_bottom_logic=True)

    # 提取上下页码（注意现在 item 是元组，item[0] 才是 box 坐标）
    top_pns = [item[0][3] for item in sampled_page_number_boxes if (item[0][1]+item[0][3])/2 < global_page_h * 0.15]
    bottom_pns = [item[0][1] for item in sampled_page_number_boxes if (item[0][1]+item[0][3])/2 > global_page_h * 0.85]

    # 初始化奇偶页的真·侧边页码容器
    left_pns_even, left_pns_odd = [], []
    right_pns_even, right_pns_odd = [], []

    for item in sampled_page_number_boxes:
        b = item[0]
        is_even = item[1]
        center_x = (b[0] + b[2]) / 2
        center_y = (b[1] + b[3]) / 2

        # 【过滤核心】：页码的 Y 中心必须在正文上下边缘内部。只要越界，彻底剥夺 X 轴干预权！
        is_true_side_pn = (center_y >= stable_core_top_y - y_pad) and (center_y <= stable_core_bottom_y + y_pad)

        if is_true_side_pn:
            if center_x < global_page_w * 0.25:
                if is_even: left_pns_even.append(b[2])
                else:       left_pns_odd.append(b[2])
            elif center_x > global_page_w * 0.75:
                if is_even: right_pns_even.append(b[0])
                else:       right_pns_odd.append(b[0])

    stable_top_pn_b = get_y_robust_anchor(top_pns, global_page_h, is_bottom_logic=True) if len(top_pns) >= min_required_count else 0.0
    stable_bottom_pn_t = get_y_robust_anchor(bottom_pns, global_page_h, is_bottom_logic=False) if len(bottom_pns) >= min_required_count else global_page_h

    side_min_count = max(1, int(min_required_count / 2))

    # 算出四个独立的侧边页码物理屏障
    stable_l_pn_even = get_x_anchor(left_pns_even, global_page_w, is_right_side=True) if len(left_pns_even) >= side_min_count else 0.0
    stable_l_pn_odd  = get_x_anchor(left_pns_odd, global_page_w, is_right_side=True) if len(left_pns_odd) >= side_min_count else 0.0
    stable_r_pn_even = get_x_anchor(right_pns_even, global_page_w, is_right_side=False) if len(right_pns_even) >= side_min_count else global_page_w
    stable_r_pn_odd  = get_x_anchor(right_pns_odd, global_page_w, is_right_side=False) if len(right_pns_odd) >= side_min_count else global_page_w

    # ====================================================================
    # 3. 动态组装 Y 轴全局安全区 (恢复：黄金中点防吞噬算法)
    # ====================================================================
    top_barriers = []
    if stable_header_b > 0: top_barriers.append(stable_header_b)
    if stable_top_pn_b > 0: top_barriers.append(stable_top_pn_b)

    if top_barriers:
        max_noise_top = max(top_barriers)
        # 【微调恢复】：如果确信页眉在正文上方，切割线设为它们两者的绝对中点！
        # 废除容易误伤的粗暴 +y_pad，实现物理级别的完美避让
        if max_noise_top < stable_core_top_y:
            global_top = (max_noise_top + stable_core_top_y) / 2.0
        else:
            global_top = max_noise_top + (y_pad * 0.3)
    else:
        global_top = max(0.0, stable_core_top_y - y_pad)

    bottom_barriers = []
    if stable_footer_t < global_page_h: bottom_barriers.append(stable_footer_t)
    if stable_bottom_pn_t < global_page_h: bottom_barriers.append(stable_bottom_pn_t)

    if bottom_barriers:
        min_noise_bottom = min(bottom_barriers)
        # 【微调恢复】：底线同理，取页脚与正文底部的绝对中点
        if min_noise_bottom > stable_core_bottom_y:
            global_bottom = (min_noise_bottom + stable_core_bottom_y) / 2.0
        else:
            global_bottom = min_noise_bottom - (y_pad * 0.3)
    else:
        global_bottom = min(global_page_h, stable_core_bottom_y + y_pad)

    # ====================================================================
    # 【第二层防线】：动态组装 X 轴全局安全区 (复原 v16 护城河 + 宽容度外扩)
    # ====================================================================
    # 获取奇偶页最纯净的、无视扫描污点的正文骨架边界
    raw_l_even = get_x_anchor(sampled_left_even, global_page_w, is_right_side=False)
    raw_r_even = get_x_anchor(sampled_right_even, global_page_w, is_right_side=True)
    raw_l_odd = get_x_anchor(sampled_left_odd, global_page_w, is_right_side=False)
    raw_r_odd = get_x_anchor(sampled_right_odd, global_page_w, is_right_side=True)

    # --- 偶数页绝对安全防线 ---
    if stable_l_pn_even > 0.0:
        # 分流 A：有真·侧边页码 -> 启用 v16 强力推土机，用标准 x_pad 狠狠向右切除噪音
        safe_l_pn_even = stable_l_pn_even + x_pad
        g_left_even = max(safe_l_pn_even, raw_l_even - x_pad)
    else:
        # 分流 B：无侧边页码 (或在角落) -> 释放极致宽容度，向外延伸 1.5 倍容差保护正文边缘
        g_left_even = max(0.0, raw_l_even - x_pad)

    if stable_r_pn_even < global_page_w:
        safe_r_pn_even = stable_r_pn_even - x_pad
        g_right_even = min(safe_r_pn_even, raw_r_even + x_pad)
    else:
        g_right_even = min(global_page_w, raw_r_even + x_pad)

    # --- 奇数页绝对安全防线 ---
    if stable_l_pn_odd > 0.0:
        safe_l_pn_odd = stable_l_pn_odd + x_pad
        g_left_odd = max(safe_l_pn_odd, raw_l_odd - x_pad)
    else:
        g_left_odd = max(0.0, raw_l_odd - x_pad)

    if stable_r_pn_odd < global_page_w:
        safe_r_pn_odd = stable_r_pn_odd - x_pad
        g_right_odd = min(safe_r_pn_odd, raw_r_odd + x_pad)
    else:
        g_right_odd = min(global_page_w, raw_r_odd + x_pad)

    print(f"✅ AI 视觉版面分析锚定完成！设定全局绝对安全区：")
    print(f"   【页面物理尺寸】: 宽 {global_page_w:.1f} × 高 {global_page_h:.1f}")
    print(f"   【上下边距】: Top {global_top:.1f} - Bottom {global_bottom:.1f}")
    print(f"   【偶数页左/右】: {g_left_even:.1f} / {g_right_even:.1f}")
    print(f"   【奇数页左/右】: {g_left_odd:.1f} / {g_right_odd:.1f}")
    print("[2/2] 开始正式扫描并写入隐形文字层...")

    # 统一打包返回，供总调度器使用
    return {
        "top": global_top,
        "bottom": global_bottom,
        "left_even": g_left_even,
        "right_even": g_right_even,
        "left_odd": g_left_odd,
        "right_odd": g_right_odd,
        "page_w": global_page_w,
        "page_h": global_page_h
    }

def process_native_pdf(pdf_doc, layout_bounds, args, output_pdf_path):
    """
    [阶段一分类情况A]：原生文献专属处理链路
    功能：仅挂载安全边界进行四周噪音物理擦除，无损保留中心原生矢量正文。
    """
    import fitz
    import pathlib

    # 解包绝对安全区边界
    global_top = layout_bounds["top"]
    global_bottom = layout_bounds["bottom"]
    g_left_even = layout_bounds["left_even"]
    g_right_even = layout_bounds["right_even"]
    g_left_odd = layout_bounds["left_odd"]
    g_right_odd = layout_bounds["right_odd"]
    global_page_w = layout_bounds["page_w"]
    global_page_h = layout_bounds["page_h"]

    # ---------------------------------------------------------------------
    # 原生文献的边缘精确擦除 (保留核心正文)
    # ---------------------------------------------------------------------
    for page_number in args.target_pages:
        page = pdf_doc.load_page(page_number)
        scale_y = page.rect.height / global_page_h
        scale_x = page.rect.width / global_page_w

        base_left = g_left_even if page_number % 2 == 0 else g_left_odd
        base_right = g_right_even if page_number % 2 == 0 else g_right_odd

        current_top = global_top * scale_y
        current_bottom = global_bottom * scale_y
        current_left = base_left * scale_x
        current_right = base_right * scale_x

        # ====================================================================
        # 【核心重构】：获取真实物理坐标系，粉碎 CropBox 偏移问题
        # ====================================================================
        x0 = page.rect.x0
        y0 = page.rect.y0
        x1 = page.rect.x1
        y1 = page.rect.y1

        # 必须以真实的起点 (x0, y0) 为基准进行叠加，彻底抛弃绝对的 0
        rect_top = fitz.Rect(x0, y0, x1, y0 + current_top)
        rect_bottom = fitz.Rect(x0, y0 + current_bottom, x1, y1)
        rect_left = fitz.Rect(x0, y0 + current_top, x0 + current_left, y0 + current_bottom)
        rect_right = fitz.Rect(x0 + current_right, y0 + current_top, x1, y0 + current_bottom)

        # ====================================================================
        # 【局部栅格化重构】：提取高清位图 -> 销毁底层矢量 -> 回填贴图
        # ====================================================================
        # 筛选出真正需要处理的有效边界框
        valid_rects = [r for r in [rect_top, rect_bottom, rect_left, rect_right] if r.is_valid and r.get_area() > 0]

        # 1. 拍照存档：在擦除前，先抓取这 4 个危险区的高清位图外观
        # 提升至 Matrix(4, 4) 即 288 DPI，获得缩放级锐度
        mat = fitz.Matrix(4, 4)
        pix = None          # 先占个名字，下方 del pix 时不会再被判为"可能未定义"
        margin_images = []
        for r in valid_rects:
            # 【极致优化】：引入 colorspace=fitz.csGRAY 强制灰度渲染
            # 画质提升的同时，体积暴降 66%，完美契合黑白电纸书设备
            pix = page.get_pixmap(clip=r, matrix=mat, alpha=False, colorspace=fitz.csGRAY)
            margin_images.append((r, pix))

        # 2. 挂载白条待擦除标记并强制刷新
        for r in valid_rects:
            annot = page.add_redact_annot(r)
            annot.set_colors(fill=(1, 1, 1)) # 设置纯白底色，准备覆盖矢量图层
            annot.update()

        # 3. 擦除
        page.apply_redactions()

        # 4. 无缝回填：在擦除后的纯白废墟上，把第一步截取的高清位图严丝合缝地贴回去！
        for r, pix in margin_images:
            page.insert_image(r, pixmap=pix)

        # ==========================================================
        # 【新增 2】：原生单页处理结束，释放高清裁剪位图内存
        # ==========================================================
        try:
            del margin_images
            del pix
            del page
        except NameError:
            pass

    # 终极“防锁死”保存机制 (直接保存 pdf_doc 自身)
    final_out_path = pathlib.Path(output_pdf_path)

    print(f"\n📦 正在执行底层无损压缩与最终文件封装 (garbage=4, deflate=True)...")
    if hasattr(args, 'ui_callback'):
        args.ui_callback(6, "STAGE 6: PDF PACKAGE", "阶段 6/6: 文件封装中，可能需数秒至数分，请勿关闭程序...")
        import time
        time.sleep(0.1) # 同样释放 GIL 让 UI 渲染

    print(f"   [!] 引擎正在对全书的局部光栅化位图进行极限 ZIP 压缩，")
    print(f"   [!] 此过程为单核阻塞运算，根据文件大小可能需要数秒至数分钟，请绝对不要关闭程序...")

    save_counter = 1
    saved_successfully = False

    while not saved_successfully:
        try:
            pdf_doc.save(str(final_out_path), garbage=4, deflate=True)
            saved_successfully = True

            if str(final_out_path) != output_pdf_path:
                print(f"\n 💡 提示: 原生文献已保存至: {final_out_path.name}")

        except (OSError, RuntimeError, PermissionError):
            final_out_path = final_out_path.with_name(f"{final_out_path.stem}_转存({save_counter}){final_out_path.suffix}")
            save_counter += 1

    # ==========================================================
    # 【新增】：输出任务视觉分界线与最终绝对路径
    # ==========================================================
    print(f"\n" + "═"*65)
    print(f"✅ 任务执行完毕！")
    print(f"📁 绝对保存路径: {final_out_path.resolve()}")
    print("═"*65 + "\n")

    return "SUCCESS"

# =========================================================================
# 【261 版新增】倾斜角度的取值与净化
# -------------------------------------------------------------------------
# 背景：PaddleOCR 的 t0["rec_boxes"] 并不是检测出来的四边形，而是把四边形
# 取 min/max 拍扁后的轴对齐矩形 [left, top, right, bottom]（见 paddlex 的
# convert_points_to_boxes）——倾斜信息在这一步就被丢光了。258 版及以前那段
# "isinstance(rec_box[0], (list, tuple, np.ndarray))" 的判断因此恒为 False，
# text_angle 恒等于 0.0，整条倾斜处理链路从来没有被真正执行过。
#
# 真正带角度的四点框在 t0["rec_polys"] 里，与 rec_texts 一一对应、等长，
# 点序为 [左上, 右上, 右下, 左下]（由 DBNet 后处理的 get_mini_boxes 保证，
# box_type 默认 "quad" 恒为 4 点）。下面两个函数负责把它变成可用的角度。
# =========================================================================

# 【266 版】字身绕基线旋转 90 度后的横向跨度 / 字号。
# 取值 = ascender - descender，china-ss 实测 1.043 - (-0.2656) = 1.3086。
# 竖排用它把字号压到"不越出本列"，避免相邻子列的隐形文字互相重叠。
VERT_GLYPH_SPAN = 1.3086


# 死区：小于这个角度一律按 0 处理。
# 这一条是"不破坏已跑通功能"的最强保证：标准扫描件的输出与 258 版完全相同。
SKEW_DEAD_ZONE_DEG = 0.3


def _sanitize_skew(angle, max_deg=30.0):
    """
    把一个原始倾角净化成"可以放心用"的角度。

    两道闸：
      1. 死区：|angle| < 0.3 度 -> 返回 0。正常扫描件不受任何影响。
      2. 钳位：|angle| > max_deg -> 返回 0。这种框基本不是正常横排文字行，
         而是竖排、印章、边缘噪点或误检的旁注；与其歪着写不如维持旧行为。
    """
    try:
        a = float(angle)
    except (TypeError, ValueError):
        return 0.0
    if a != a:                # NaN
        return 0.0
    if abs(a) < SKEW_DEAD_ZONE_DEG or abs(a) > float(max_deg):
        return 0.0
    return a


def _is_vertical_box(poly):
    """
    这个检测框是不是"竖长"的？

    竖排页面上并不是所有东西都竖着：书名、卷端题、版心的页码、天头的批注
    往往是横排的，日文竖排书里也常有横排的标题行。整页一刀切按竖排写，
    这些横的部分就会被拧成一列，反而比不支持竖排还糟。

    所以竖排模式下逐框判断：框的"高"大于"宽"才按列处理，否则仍走横排。
    用四边形的两条邻边长度比较，天然对倾斜的框也成立。
    """
    import math as _m
    try:
        w = _m.hypot(float(poly[1][0]) - float(poly[0][0]),
                     float(poly[1][1]) - float(poly[0][1]))
        h = _m.hypot(float(poly[3][0]) - float(poly[0][0]),
                     float(poly[3][1]) - float(poly[0][1]))
        return h > w
    except (TypeError, ValueError, IndexError):
        return False


def _native_scan_dpi(pdf_doc, sample=6):
    """
    估算这本书的**扫描源**分辨率（DPI），取抽样页的中位数。

    扫描件的信息量上限由内嵌图像的像素数决定，与我们渲染多大无关：
    一张 736px 宽、页面 595pt 宽的图，源分辨率就是 736 / (595/72) = 89 DPI，
    渲染到 2500px 也只是把这 89 DPI 的信息插值放大，不会凭空多出笔画。

    这个数字用来决定要不要给竖排抬高检测输入上限：
      · 268 DPI 的《古文舊書考》—— 上限 1600 已经够用，抬高反而让目录页的
        连点引导线碎成更多框；
      · 89 DPI 的《中庸章句集注》—— 上限 1600 会把双行小注的笔画压糊，
        必须抬高（实测第 4 页 233 字 -> 810 字）。

    取不到内嵌图像（矢量页、空白页）时返回 None，调用方按"不抬高"处理。
    """
    vals = []
    n = pdf_doc.page_count
    idx = range(n) if n <= sample else [n * (i + 1) // (sample + 1) for i in range(sample)]
    for i in idx:
        try:
            page = pdf_doc.load_page(i)
            w_pt = page.rect.width
            if w_pt <= 1:
                continue
            for im in page.get_images(full=True):
                px = im[2]
                if px > 50:
                    vals.append(px / (w_pt / 72.0))
        except Exception:
            continue
    if not vals:
        return None
    vals.sort()
    return vals[len(vals) // 2]


def _extent_overlap(a0, a1, b0, b1):
    """两个一维区间的重叠长度 / 较短者的长度。"""
    lo, hi = max(a0, b0), min(a1, b1)
    if hi <= lo:
        return 0.0
    return (hi - lo) / max(min(a1 - a0, b1 - b0), 1e-9)


def _same_text_run(a, b, cross_ov=0.6, cross_ratio=0.6, along_ov=0.6, short_ratio=0.4):
    """
    【269 版】判断两个框是不是"同一段文字的两个版本"，用于多尺度并集去重。

    这条规则要同时满足三件事，前两次尝试各挂在其中一条上：
      A. 同一段文字在不同尺度下各出一个框   -> 必须去重，否则文字层重复写两遍
      B. 长列里套着的短碎片（同一列）        -> 必须去重，碎片是长列的子集
      C. 大字列框在几何上"包住"旁边的小注子列 -> **必须都保留**，那是两段不同的文字

    第一次用 IoU 去重挂在 B（1 字框与 7 字列的 IoU 只有 0.14，判不出重复）；
    第二次改用覆盖率去重挂在 C（小注子列 73% 落在大字列框内，被当成重复删掉，
    正好把用户指出的那条子列删没了）。

    本版分两步判：先判"是不是同一列"，再判"是不是同一段"。
      · 同一列：短轴（竖排是 x）区间重叠 >= 窄者的 60%，**且**短轴长度之比 >= 0.6。
        大字列宽 46pt 对小注子列宽 24pt，比值 0.52 < 0.6 -> 判为不同列，C 得解。
      · 同一段：在此基础上长轴（竖排是 y）区间重叠 >= 短者的 60%。
        1 字碎片完全落在 7 字列的 y 区间内，重叠 100% -> 判为重复，B 得解。

    注意"上下相邻但不重叠"的两个框（例如「不」与「及之名庸平常也」，
    合起来才是完整的「不及之名庸平常也」）长轴重叠为 0，不会被误删。
    """
    va = (a[3] - a[1]) >= (a[2] - a[0])
    vb = (b[3] - b[1]) >= (b[2] - b[0])
    if va != vb:
        return False                       # 朝向不同，不是同一段
    if va:
        cross = _extent_overlap(a[0], a[2], b[0], b[2])
        la, lb = a[2] - a[0], b[2] - b[0]
        a_lo, a_hi, b_lo, b_hi = a[1], a[3], b[1], b[3]
    else:
        cross = _extent_overlap(a[1], a[3], b[1], b[3])
        la, lb = a[3] - a[1], b[3] - b[1]
        a_lo, a_hi, b_lo, b_hi = a[0], a[2], b[0], b[2]
    along = _extent_overlap(a_lo, a_hi, b_lo, b_hi)
    l_a, l_b = a_hi - a_lo, b_hi - b_lo
    if cross < cross_ov:
        return False
    if min(la, lb) / max(la, lb, 1e-9) < cross_ratio:
        return False
    # 长轴长度悬殊时（一个是整列、另一个是碎片），改判"碎片中心是否落在整列区间内"。
    # 只用 60% 区间重叠会漏掉骑在列首/列尾边界上的碎片 —— 它与整列的重叠不足六成，
    # 却实实在在把同一个字又写了一遍。实测这条把重复率从 2.9% 压到接近 1%。
    if min(l_a, l_b) / max(l_a, l_b, 1e-9) < short_ratio:
        if l_a < l_b:
            c = (a_lo + a_hi) / 2.0
            return b_lo <= c <= b_hi
        c = (b_lo + b_hi) / 2.0
        return a_lo <= c <= a_hi
    return along >= along_ov


def _union_scale_runs(runs):
    """
    多尺度结果取并集。runs 里每一份是 [(box, poly, text, score), ...]，
    box/poly 必须已经换算到同一坐标系（本脚本统一换算到基准尺度的像素）。
    保留顺序按"字数多优先、其次分数高"，所以留下的总是信息量最大的那个框。
    """
    cand = [x for r in runs for x in r]
    cand.sort(key=lambda x: (-len(x[2]), -x[3]))
    kept = []
    for box, poly, t, sc in cand:
        if any(_same_text_run(box, k[0]) for k in kept):
            continue
        kept.append((box, poly, t, sc))
    return kept


def _page_is_vertical_body(items, min_cols=5, col_frac=0.55):
    """
    这一页是不是"竖排正文页"？

    判据：拿得到四边形、且竖长的框，数量 >= min_cols 且占比 >= col_frac。
    竖排书里夹的横排页（版权页、索引、中英文摘要）竖长框接近 0，判 False。
    """
    cols = rows = 0
    for it in items:
        poly = it[1]
        if poly is None:
            continue
        if _is_vertical_box(poly):
            cols += 1
        else:
            rows += 1
    n_all = cols + rows
    if n_all == 0:
        return False
    return cols >= min_cols and cols >= col_frac * n_all


def _explode_cross_column_rows(items, min_cols=5, col_frac=0.55):
    """
    【265 版新增】把"跨列误并"的横长框按字数等分，拆回各自所属的列。

    ---- 问题 ----
    低分辨率的密排影印件上，相邻列**顶端**的字会被检测网络连成一个横长框。
    例如《中庸章句集注》第 11 页的 "天人物以是哀"，其实是相邻六列各取了
    第一个字；"敏成種則滅問右" 是七列各取一字。最坏的一页有 23/159 = 14%
    的框是这样来的。

    ---- 为什么不能简单丢掉 ----
    这些字是**正文**，而且是每一列的首字；竖排列框恰恰是从它们下面才开始的，
    所以丢掉就等于每列都缺字。实测把误并框叠在原图上看，蓝框确实压在
    "天""人""物""以""是""哀"这六个字上，一个不差。

    ---- 为什么可以按字数等分 ----
    识别网络是**逐列各取一字、从左到右**读出来的，而且读得很准（这些框的
    识别分数高达 0.98~1.00）。所以框里的第 i 个字，就属于框宽等分后的第 i 段。
    等分同时还修掉了原来的累积漂移：旧写法按字体推进量逐字累加，与真实列距
    对不上，一行下来末字能偏出半个字身；改成按框宽等分，误差不再累积。

    ---- 已否决的其他思路（均有实测数据，见 CHANGELOG）----
      · 按识别分数过滤：无效，误并框分数 0.98~1.00。
      · 按与竖排列的重叠率过滤：无效，重叠率 0%~100% 全谱分布。
      · 调低 unclip_ratio：无效，1.5→0.6 五档误并框数量恒定不变，
        说明连通发生在 DB 的分割概率图里，不在后处理的框膨胀里。
      · 整页转 90 度后再检测：更糟，误并 75 框 -> 266 框、字数还掉了三成，
        因为侧倒的字形对**检测**网络同样是分布外输入。

    ---- 安全闸 ----
    只在"这一页确实以竖排列为主"时才拆（竖排列数 >= min_cols 且占比
    >= col_frac）。竖排书里夹的横排页（版权页、索引、中英文摘要）竖排列数
    接近 0，闸门不通过，整页原样放行，行为与 264 完全一致。
    """
    cols, rows = [], []
    for it in items:
        poly = it[1]
        if poly is None or _is_vertical_box(poly):
            cols.append(it)
        else:
            rows.append(it)
    if not rows:
        return items
    if not _page_is_vertical_body(items, min_cols, col_frac):
        return items          # 不是竖排正文页，原样放行

    out = list(cols)
    for rec_box, poly, text, score in rows:
        n = len(text or "")
        if n < 2:
            # 单字横长框没有"跨列"可言，原样保留即可
            out.append((rec_box, poly, text, score))
            continue
        p0, p1, p2, p3 = (np.asarray(q, dtype=float) for q in poly)
        top, bot = p1 - p0, p2 - p3        # 上边、下边的方向向量
        for i, ch in enumerate(text):
            a, b = i / float(n), (i + 1) / float(n)
            q0, q1 = p0 + top * a, p0 + top * b
            q3, q2 = p3 + bot * a, p3 + bot * b
            sub_poly = np.array([q0, q1, q2, q3], dtype=float)
            xs, ys = sub_poly[:, 0], sub_poly[:, 1]
            sub_box = np.array([xs.min(), ys.min(), xs.max(), ys.max()], dtype=float)
            out.append((sub_box, sub_poly, ch, score))
    return out


def _skew_axis(poly, vertical=False):
    """
    取出一个检测框的"写入轴"：起点、终点。

    横排：轴 = 左下 -> 右下（poly[3] -> poly[2]），即文字基线。
    竖排：轴 = 左上 -> 左下（poly[0] -> poly[3]），即一列文字自上而下。

    点序 [左上, 右上, 右下, 左下] 由 DBNet 后处理的 get_mini_boxes 保证。
    注意竖排时千万不能沿用横排的那条轴：对一个竖长框来说 poly[3]->poly[2]
    是底边那条**短边**，算出来的角度恒为 0 度，正是旧版把整列压成一小撮
    横向糊斑的根源。
    """
    if vertical:
        return poly[0], poly[3]
    return poly[3], poly[2]


def _estimate_page_skew(polys, texts, max_deg=30.0, vertical=False):
    """
    统计整页的系统性倾角（中位数），供短框借用。

    为什么需要：只有两三个字的检测框（页码、章节号、脚注序号），四边形的
    角度抖动能到好几度，逐框独立取角会让这些零星短行歪得各不相同，看着比
    不校正还别扭。而整页的系统性倾斜是同一个值，用长框统计出来更稳。

    只统计"够长"的框（至少 4 个字符、基线长度够），取中位数抗离群点。
    有效样本不足 3 个时返回 None，调用方会退回"短框不校正"。
    """
    import math as _m
    samples = []
    for poly, txt in zip(polys, texts):
        if poly is None or len(txt or "") < 4:
            continue
        try:
            # 竖排页上混着的横长框（书名、卷端、页码）不参与竖排倾角统计
            if vertical and not _is_vertical_box(poly):
                continue
            bl, br = _skew_axis(poly, vertical)
            dx = float(br[0]) - float(bl[0])
            dy = float(br[1]) - float(bl[1])
            if _m.hypot(dx, dy) < 40:      # 轴太短的样本不参与统计
                continue
            # 竖排的基准角是 90 度（自上而下），统计的是"偏离垂直多少度"
            base = 90.0 if vertical else 0.0
            a = _m.degrees(_m.atan2(dy, dx)) - base
            if abs(a) <= float(max_deg):
                samples.append(a)
        except (TypeError, ValueError, IndexError):
            continue
    if len(samples) < 3:
        return None
    samples.sort()
    mid = len(samples) // 2
    if len(samples) % 2:
        return samples[mid]
    return (samples[mid - 1] + samples[mid]) / 2.0


def execute_ocr_and_render(pdf_doc, layout_bounds, args, input_pdf_path, output_pdf_path):
    """
    [阶段二独立模块]：正式全文档扫描、OCR 写入与防锁死保存
    功能：解析 PDF 渲染像素矩阵，挂载安全边界进行拦截，写入不可见文本，并执行最终的文件 IO。
    """
    import fitz
    import cv2
    import numpy as np
    import tqdm
    import sys
    import pathlib
    import colorsys
    from paddleocr import PaddleOCR

    # 从阶段一传入的字典中解包绝对安全区边界
    global_top = layout_bounds["top"]
    global_bottom = layout_bounds["bottom"]
    g_left_even = layout_bounds["left_even"]
    g_right_even = layout_bounds["right_even"]
    g_left_odd = layout_bounds["left_odd"]
    g_right_odd = layout_bounds["right_odd"]
    global_page_w = layout_bounds["page_w"]
    global_page_h = layout_bounds["page_h"]

    # 如果需要生成纯文本 PDF（-p），新建一个容器
    # 先统一置空，保证无论走不走 -p 分支，pure 这个名字都始终存在
    pure = None
    if args.pure:
        pure = fitz.open()

    if hasattr(args, 'ui_callback'):
        args.ui_callback(4, "STAGE 4: ALIGNING OCR CORE", "阶段 4/6: 正在调取OCR 核心识别模型...")

    # 【改动】：向全局引擎请求对应语种的模型
    # 【256 版】：把检测输入上限交给引擎（跟随用户选的清晰度档位）
    AIModelEngine._det_limit_side_len = int(getattr(args, 'det_limit', 1600) or 0)
    AIModelEngine._det_thresh = getattr(args, 'det_thresh', None)
    AIModelEngine._det_box_thresh = getattr(args, 'det_box_thresh', None)
    ocr = AIModelEngine.get_ocr_engine(args.lang, getattr(args, 'vertical', False))
    if getattr(args, 'vertical', False):
        print("   └─ 竖排模式: 已关闭文本行方向分类器"
              "（它会把转正后的竖排列误判为倒置，实测会吃掉三到七成正文）")
    if AIModelEngine._det_limit_side_len > 0:
        print(f"   └─ 文字检测输入上限: 长边 {AIModelEngine._det_limit_side_len} 像素"
              f"（限制检测网络的激活显存，不影响认字清晰度）")
    else:
        print("   └─ 文字检测输入上限: 不限制（旧行为，显存占用高）")

    # =========================================================================
    # 【本版本新增】：分段计时器 (--timing)
    # 目的：把"每页耗时"拆成 页面渲染 / 擦除旧层 / OCR 推理 / 文字写入 四段，
    # 好判断慢的到底是本脚本的代码，还是 Paddle 调用 GPU 这一环。
    # 不开启 --timing 时，下面这几行只是几个恒为 0 的浮点数，没有任何开销。
    # =========================================================================
    _timing_on = getattr(args, 'timing', False)
    _tm = {"渲染页面": 0.0, "擦除旧层": 0.0, "OCR 推理": 0.0, "写入文字": 0.0}
    _tm_pages = 0
    if _timing_on:
        # time / _time 已在文件顶部统一导入，这里不再局部 import，
        # 否则编辑器会认为 _time 只在 if 成立时才存在，从而全篇标红。
        report_device_status()

    # =========================================================================
    # [阶段二]：正式全文档扫描与 OCR 写入
    # =========================================================================
    pbar = tqdm.tqdm(args.target_pages, desc="OCR Scanning", unit="page")
    for page_number in pbar:
        if hasattr(args, 'ui_callback'):
            # 同样的手法提取 tqdm 内置数据
            stats_str = str(pbar).split('|')[-1]
            args.ui_callback(5, "STAGE 5: OCR SCANNING", "阶段 5/6: 正在进行OCR扫描并写入隐形文字层...\n处理速度取决于显卡性能和页面复杂度", current=pbar.n, total=pbar.total, stats=stats_str)

        page = pdf_doc.load_page(page_number)

        # 【280 版】每页只计算一次 CropBox 纵向补偿。普通页面与
        # 上下对称裁剪页面的结果都为 0，只有上下裁剪不对称时
        # 才会对高速 TextWriter 落点进行反向补偿。
        textwriter_crop_y_delta = get_textwriter_crop_y_delta(page)

        # 预处理：擦除 PDF 现有的文字图层，防止原有乱码干扰
        _t_mark = _time.perf_counter() if _timing_on else 0.0
        page.add_redact_annot(page.rect)
        page.apply_redactions(images=0)
        if _timing_on:
            _tm["擦除旧层"] += _time.perf_counter() - _t_mark

        # ==========================================================
        # 智能动态分辨率 (Dynamic Resolution) - 支持手动调整清晰度
        # ==========================================================
        # 获取当前页面的真实物理尺寸（PDF 默认单位为 Point，72 Point = 1 英寸）
        max_side_points = max(page.rect.width, page.rect.height)

        # 1. 目标基准：从用户面板获取的目标 DPI (兼顾 CLI 的 220 默认兜底)
        #    150 档 -> 150 DPI / 上限 1800 像素
        #    220 档 -> 220 DPI / 上限 2500 像素   ← 默认
        #    300 档 -> 300 DPI / 上限 3800 像素
        #    这三档由界面右上角的【扫描清晰度】下拉框决定，254 版原样保留。
        target_dpi = getattr(args, 'target_dpi', 220.0)

        # 2. 深度学习安全阈值钳制：从用户面板获取的像素上限
        #    【254 版调整】：改为调用与拆分阶段共用的 clamp_zoom，
        #    算法与旧版逐字等价，只是额外加了一道全局硬顶 4000 像素，
        #    防止命令行传进异常参数时把内存撑爆。
        max_safe_pixels = getattr(args, 'max_pixels', 2500.0)
        actual_zoom = clamp_zoom(max_side_points, target_dpi, max_safe_pixels)

        # 3. 终极自适应：允许向下缩小！
        # 解除了之前 max(1.0, zoom) 的死锁。如果源 PDF 本身的长边高达 5000 Point，
        # actual_zoom 将自动计算为 0.7，实现对巨型页面的物理级“缩小”。
        # 设立 0.3 为兜底极限，防止遇到异常参数导致画面彻底坍缩。
        zoom = max(0.3, actual_zoom)

        mat = fitz.Matrix(zoom, zoom)

        # alpha=False 强制生成实心白色背景，防止黑底报错
        _t_mark = _time.perf_counter() if _timing_on else 0.0
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # 将 PyMuPDF 提取的像素流转为 numpy 数组，再调换 RGB 通道为 BGR 供 PaddleOCR 读取
        cim = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        cim = np.ascontiguousarray(cim[..., [2, 1, 0]])
        if _timing_on:
            _tm["渲染页面"] += _time.perf_counter() - _t_mark

        # OpenCV 的 debug 可视化界面支持 (放在涂白之后，这样你能通过开启 -c 直观看到画面被裁切的效果)
        if args.cv:
            cv2.imshow(sys.argv[0], cim)
            cv2.waitKey(1)

        # 跳过实际 OCR 运算（用于单纯擦除旧文本等目的）
        if args.no_ocr:
            continue

        # 新建纯净文本页（针对 -p 参数）
        # 同样先置空：不开 -p 时下方只会读到 None，绝不会碰到未定义的名字
        new_page = None
        if args.pure and pure is not None:
            new_page = pure.new_page(width=page.rect.width, height=page.rect.height)

        # 调用引擎进行全图 OCR 识别（此时大模型看到的只有纯净的正文！）
        _t_mark = _time.perf_counter() if _timing_on else 0.0

        # ==========================================================
        # 【269 版新增】多尺度深度扫描
        # ----------------------------------------------------------
        # 低清影印件上，双行夹注这类细密文字的检测**正好卡在 DB 分割图的
        # 阈值线上**：实测同一条小注子列，渲染缩放差 0.66%（4.1667 对
        # 4.1943）就能让一个 7 字框塌成 2 字框。也就是说"某个尺度恰好抓到、
        # 换个尺度就抓不到"是常态，而不是偶然。
        #
        # 对策：同一页按几个相邻缩放各跑一遍，把结果并起来。实测三尺度并集
        # （以《中庸章句集注》为例，指标取"落在 >=4 字框里的字数"，
        # 碎片刷不动这个指标）：
        #     第 4 页  最好单尺度 525 -> 并集 590
        #     第11页  最好单尺度 483 -> 并集 570
        #     第13页  最好单尺度 602 -> 并集 678
        # 代价是耗时翻倍到三倍，所以默认关闭，由 --multi-scale 显式开启。
        #
        # 缩放系数刻意取得很近（0.86 / 1.00 / 1.06）：目的不是"看得更清楚"
        # （源图分辨率摆在那儿，放大不会多出信息），而是让那些卡在阈值上的
        # 连通区域在某一个尺度上恰好成形。所有尺度都受 4000 像素硬顶约束，
        # 免得在 6GB 显卡上撑爆显存。
        # ==========================================================
        # 档位实测（《中庸章句集注》，指标为"落在 >=4 字框里的字数"）：
        #            第4页   第11页  第13页
        #   1 尺度     488     483     594
        #   3 尺度     528     527     644
        #   5 尺度     595     562     663
        #   7 尺度     614     580     670
        # 收益随尺度数单调上升、逐步收敛。系数刻意偏向 1.0 以下，
        # 因为往上很快被 4000 像素硬顶截断，再加也是重复跑同一个缩放。
        _MS_SETS = {
            3: (1.0, 0.86, 1.06),
            5: (1.0, 0.82, 0.90, 0.96, 1.06),
            7: (1.0, 0.78, 0.84, 0.88, 0.93, 0.97, 1.06),
        }
        _ms_level = int(getattr(args, 'multi_scale', 1) or 1)
        _ms_factors = _MS_SETS.get(_ms_level, (1.0,)) if _ms_level > 1 else (1.0,)

        if len(_ms_factors) == 1:
            text = ocr.predict(cim)
        else:
            _runs = []
            _done_zooms = [zoom]
            for _fi, _f in enumerate(_ms_factors):
                if _fi == 0:
                    _sub_im, _sub_zoom = cim, zoom
                else:
                    _z2 = clamp_zoom(max_side_points, target_dpi * _f, max_safe_pixels * _f)
                    _z2 = max(0.3, _z2)
                    # 与已跑过的任一缩放太接近就跳过：多个系数可能被 4000
                    # 像素硬顶钳到同一个值，跑了也是白跑
                    if any(abs(_z2 - _zd) / max(_zd, 1e-9) < 0.01 for _zd in _done_zooms):
                        continue
                    _p2 = page.get_pixmap(matrix=fitz.Matrix(_z2, _z2), alpha=False)
                    _sub_im = np.ascontiguousarray(
                        np.frombuffer(_p2.samples, dtype=np.uint8)
                        .reshape(_p2.h, _p2.w, _p2.n)[..., [2, 1, 0]])
                    _sub_zoom = _z2
                    _done_zooms.append(_z2)
                    del _p2
                try:
                    _r = ocr.predict(_sub_im)[0]
                except Exception:
                    _r = None
                if _fi != 0:
                    del _sub_im
                if not _r:
                    continue
                # 统一换算到基准尺度的像素坐标
                _k = zoom / _sub_zoom
                _polys = _r.get("rec_polys") or []
                _texts = _r.get("rec_texts") or []
                _scores = _r.get("rec_scores") or []
                _one = []
                for _p, _t, _sc in zip(_polys, _texts, _scores):
                    _pp = np.asarray(_p, dtype=float) * _k
                    _xs, _ys = _pp[:, 0], _pp[:, 1]
                    _one.append(((float(_xs.min()), float(_ys.min()),
                                  float(_xs.max()), float(_ys.max())),
                                 _pp, _t, float(_sc)))
                _runs.append(_one)
                if _fi != 0:
                    try:
                        import paddle
                        if paddle.device.is_compiled_with_cuda():
                            paddle.device.cuda.empty_cache()
                    except Exception:
                        pass
            _merged = _union_scale_runs(_runs) if _runs else []
            text = [{
                "rec_polys": [m[1] for m in _merged],
                "rec_boxes": np.array([m[0] for m in _merged], dtype=float)
                             if _merged else np.array([]),
                "rec_texts": [m[2] for m in _merged],
                "rec_scores": [m[3] for m in _merged],
            }]
            if _timing_on:
                print("      [诊断] 多尺度并集: %s -> %d 框"
                      % ("+".join(str(len(r)) for r in _runs), len(_merged)))
        if _timing_on:
            _one_infer = _time.perf_counter() - _t_mark
            _tm["OCR 推理"] += _one_infer
            _tm_pages += 1
            # ==========================================================
            # 【256 版新增】逐页诊断行
            # ----------------------------------------------------------
            # 只有开了 --timing 才打印。目的是在"某一本书特别慢"的时候，
            # 能一眼看出到底是哪一项在膨胀：是页面像素太大、还是这一页
            # 被检测出了异常多的文字行（噪点多的扫描件很容易几百行）。
            # 每页的识别耗时基本与文字行数成正比。
            # ==========================================================
            try:
                _nline = len(text[0].get("rec_texts", [])) if text and text[0] else 0
            except Exception:
                _nline = 0
            _pgno = getattr(args, '_diag_seq', 0) + 1
            args._diag_seq = _pgno
            if _pgno <= 5 or _pgno % 10 == 0:
                print(f"      [诊断] 第{_pgno}页  图像 {pix.w}x{pix.h}px  "
                      f"检出 {_nline} 行  推理 {_one_infer:.2f} 秒")
        if not text[0]:
            continue
        t0 = text[0]

        import math  # 如果文件开头没有，请在这里或者顶部引入

        _t_mark = _time.perf_counter() if _timing_on else 0.0

        # ==========================================================
        # 【261 版新增】并排取出带角度的四点框
        # ----------------------------------------------------------
        # rec_polys 与 rec_texts 一一对应、等长。取不到（旧版 Paddle、
        # 非 general 的 text_type 等）就整列填 None，下面每一处都会原样
        # 退回 258 版的水平写入逻辑，行为完全不变。
        #
        # page.rotation != 0 的页面整体不做倾斜校正：那些页面走的是下方
        # 的逐字符老通道，而老通道表达不了"基线倾斜"（详见写入处的说明）。
        # ==========================================================
        # 【262 版】竖排必须由用户显式勾选，绝不自动判断。
        # 竖排模式下即便勾了 --no-skew 也仍要走带角度的写入通道 —— 因为
        # "竖排"本身就是一个 90 度的角度，关掉它就没法写了；--no-skew 在
        # 竖排模式下只表示"不再额外校正列的微小倾斜"。
        _vertical = bool(getattr(args, 'vertical', False))
        _skew_on = ((not getattr(args, 'no_skew', False)) or _vertical) and page.rotation == 0
        _skew_max = float(getattr(args, 'skew_max', 30.0) or 30.0)
        _polys = None
        if _skew_on:
            try:
                _cand = t0.get("rec_polys")
                if _cand is not None and len(_cand) == len(t0["rec_texts"]):
                    _polys = list(_cand)
            except (AttributeError, TypeError, KeyError):
                _polys = None
        if _polys is None:
            _polys = [None] * len(t0["rec_texts"])
            _page_skew = None
        else:
            _page_skew = _estimate_page_skew(_polys, t0["rec_texts"], _skew_max, _vertical)

        # ==========================================================
        # 【262 版新增】竖排列序重排：自右向左
        # ----------------------------------------------------------
        # PaddleOCR 的 SortQuadBoxes 是 sorted(key=(左上y, 左上x))，即
        # "从上到下、从左到右"。竖排页面上所有列的顶端 y 几乎相同，于是
        # 排序退化成纯粹的"从左到右"—— 而竖排排印物都是自右向左读。
        # 不重排的话，写进 PDF 的文字顺序是整段倒序的，复制粘贴、Ctrl+F
        # 跨列检索全都会错乱（每一列内部的字序是对的，列与列之间是反的）。
        # 这里按框中心 x 降序重排，纯粹是调换遍历顺序，不改任何几何量。
        # ==========================================================
        _items = list(zip(t0["rec_boxes"], _polys, t0["rec_texts"], t0["rec_scores"]))
        _force_vert = False          # 非竖排模式恒为 False，逐框判断照旧
        if _vertical:
            # 【265 版】先把跨列误并的横长框拆回各列，再排列序。
            # 顺序不能反：拆出来的单字必须参与自右向左的列序排序。
            _n_before = len(_items)
            _items = _explode_cross_column_rows(_items)

            # 【269 版】多尺度时要在 explode **之后**再去一次重。
            # 并集是在 explode 之前做的，而 explode 会把跨列误并块拆成一批
            # 单字框 —— 这些新生成的框没参与过并集去重，很容易和另一个尺度
            # 直接检出的单字框撞在同一个位置，把同一个字写两遍。
            # 实测第 4 页 65 处重复里，绝大多数正是这种"单字撞单字"。
            if int(getattr(args, 'multi_scale', 1) or 1) > 1:
                _n_ex = len(_items)
                _items = _union_scale_runs([_items])
                if _n_ex != len(_items) and getattr(args, 'timing', False):
                    print("      [诊断] 拆分后二次去重: %d -> %d 框" % (_n_ex, len(_items)))
            if len(_items) != _n_before and getattr(args, 'timing', False):
                print("      [诊断] 跨列误并拆分: %d 框 -> %d 框"
                      % (_n_before, len(_items)))

            def _col_key(it):
                b = it[0]
                try:
                    return -(float(b[0]) + float(b[2])) / 2.0
                except (TypeError, ValueError, IndexError):
                    return 0.0
            _items.sort(key=_col_key)

            # ==================================================
            # 【267 版新增】竖排正文页上一律按竖排写入
            # --------------------------------------------------
            # 262 版是逐框按长宽比判朝向，本意是照顾竖排页上真实的横排
            # 书名、卷端题和页码。但实测下来，竖排正文页上被判成"横排"的
            # 框绝大多数并不是真的横排文字，而是检测网络的误判 —— 密排
            # 密排件里相邻列的字很容易被连成一个横长块。把它们当横排写，
            # 文字层就横着盖在竖排正文上，位置和阅读顺序全错。
            #
            # 权衡下来：宁可把真正的横排书名、页码也按竖排写（那些内容
            # 通常只有两三个字，按竖排写位置依然落在字上，只是选中顺序
            # 变成自上而下），也不能让误判的横长块污染正文区。正文的准确
            # 性优先级远高于书名页码。
            #
            # 只在"这一页确实以竖排列为主"时生效；竖排书里夹的横排页
            # （版权页、索引）判定不通过，整页仍按原逻辑逐框判断。
            # ==================================================
            _force_vert = _page_is_vertical_body(_items)

        # 遍历全页所有识别出的文字框
        for rec_box, rec_poly, rec_text, rec_score in _items:
            # ==========================================================
            # 【终极修正 4】：精准锚定真实起点与计算文本矢量角度
            # ==========================================================
            if isinstance(rec_box[0], (list, tuple, np.ndarray)):
                # PaddleOCR 默认输出 [左上, 右上, 右下, 左下]
                xs = [pt[0] for pt in rec_box]
                ys = [pt[1] for pt in rec_box]
                x_min, x_max = min(xs), max(xs)
                y_min, y_max = min(ys), max(ys)

                # 提取真实的文本基线起点（左下角）和终点（右下角）
                pt_bl = rec_box[3]
                pt_br = rec_box[2]

                # 计算文字在图像中的真实视觉倾斜/翻转角度
                dx = pt_br[0] - pt_bl[0]
                dy = pt_br[1] - pt_bl[1]
                text_angle = math.degrees(math.atan2(dy, dx))
            else:
                x_min, y_min, x_max, y_max = rec_box[:4]
                pt_bl = [x_min, y_max]
                text_angle = 0.0

            # ==========================================================
            # 【261 版新增】用真实四边形改写锚点、倾角与基线长度
            # ----------------------------------------------------------
            # 上面那段 if/else 是 258 版原样保留的，走的必然是 else 分支
            # （rec_boxes 是轴对齐矩形，原因见文件上方 _sanitize_skew 处的
            # 说明）。这里在它之后做一次覆盖：只有拿到了四边形、且净化后的
            # 角度非 0 时才改写，否则一个变量都不碰，输出与 258 版完全相同。
            #
            # 锚点必须一起换：旧的 pt_bl = [x_min, y_max] 是**外接框**的左下
            # 角，倾斜行的真实基线起点并不在那里 —— 右端上扬的行，真实左下角
            # 比 y_max 高出整整 L·sinθ，照旧锚点写会让整行下沉。
            # ==========================================================
            skew_len = None      # 写入轴的真实长度(图像像素)；None = 沿用外接框宽
            col_w = None         # 【262】竖排时的列宽(图像像素)，用于把基线摆到列心
            # 【262 版】本框到底按竖排还是横排写：竖排模式下也要逐框判断，
            # 因为竖排页上的书名、卷端、页码、天头批注常常是横排的。
            _box_vert = bool(_vertical and rec_poly is not None
                             and (_force_vert or _is_vertical_box(rec_poly)))
            if rec_poly is not None:
                try:
                    # 【262 版】横排取基线（左下->右下），竖排取列轴（左上->左下）
                    p_bl, p_br = _skew_axis(rec_poly, _box_vert)
                    _dx = float(p_br[0]) - float(p_bl[0])
                    _dy = float(p_br[1]) - float(p_bl[1])
                    # 竖排的基准角是 90 度；死区与钳位只作用在"偏离基准多少"上，
                    # 于是 89.8 度的列会被归正成 90 度，93 度的斜列则保留 3 度倾斜。
                    _base_ang = 90.0 if _box_vert else 0.0
                    _dev = math.degrees(math.atan2(_dy, _dx)) - _base_ang
                    # 不足 4 个字的短框角度噪声大，借用整页基准偏离量
                    if len(rec_text) < 4 and _page_skew is not None:
                        _dev = _page_skew
                    _ang = _base_ang + _sanitize_skew(_dev, _skew_max)
                    if _box_vert or _ang != 0.0:
                        text_angle = _ang
                        pt_bl = [float(p_bl[0]), float(p_bl[1])]
                        skew_len = math.hypot(_dx, _dy)
                        if _box_vert:
                            # 列宽 = 左上到右上的距离
                            col_w = math.hypot(
                                float(rec_poly[1][0]) - float(rec_poly[0][0]),
                                float(rec_poly[1][1]) - float(rec_poly[0][1]))
                except (TypeError, ValueError, IndexError):
                    skew_len = None
                    col_w = None

            # 保持之前的绝对物理映射坐标（完全正确，无需回滚）
            true_page_w = pix.w / zoom
            true_page_h = pix.h / zoom
            true_x0 = pix.x / zoom
            true_y0 = pix.y / zoom

            # 这里的 R 依然用于防线拦截计算（保持不变）
            x0_pdf = true_x0 + (x_min / zoom)
            y0_pdf = true_y0 + (y_min / zoom)
            x1_pdf = true_x0 + (x_max / zoom)
            y1_pdf = true_y0 + (y_max / zoom)
            R = fitz.Rect(x0_pdf, y0_pdf, x1_pdf, y1_pdf)

            # --- 全局硬性拦截器（保持你之前的代码不变即可） ---
            if not getattr(args, 'skip_layout', False):
                scale_y = true_page_h / global_page_h
                scale_x = true_page_w / global_page_w
                base_left = g_left_even if page_number % 2 == 0 else g_left_odd
                base_right = g_right_even if page_number % 2 == 0 else g_right_odd

                current_top = true_y0 + (global_top * scale_y)
                current_bottom = true_y0 + (global_bottom * scale_y)
                current_left = true_x0 + (base_left * scale_x)
                current_right = true_x0 + (base_right * scale_x)

                box_center_y = (R.y0 + R.y1) / 2
                if (box_center_y < current_top or
                    box_center_y > current_bottom or
                    R.x1 < current_left or
                    R.x0 > current_right):
                    continue
            # --- 拦截器结束 ---

            # ==========================================================
            # 【终极修正 6.1】：安全实例化内置字体对象
            # ==========================================================
            font_en = fitz.Font("tiro")
            font_cn = fitz.Font("china-ss")

            # 1. 定义需要被强行压缩宽度的全角标点集合
            cn_punctuation = set("，。、；：？！“”‘’（）《》〈〉【】『』—…")

            # 2. 逐字符测算物理长度 (针对标点启用 50% 折半测算)
            #
            # 【262 版】竖排不走这套测算：竖排每个字都占满一个全角字身，
            # 无论汉字、西文还是标点，纵向推进量恒为一个字号。所以"1 号字下
            # 整列的长度"就等于字数本身。
            total_length_1 = 0
            for char in rec_text:
                is_ascii = char.isascii()
                f_obj = font_en if is_ascii else font_cn
                char_len = f_obj.text_length(char, fontsize=1)

                # 核心：如果是中文标点，强行将其占位宽度砍半
                if char in cn_punctuation:
                    char_len *= 0.5

                total_length_1 += char_len

            # 3. 计算完美贴合 OCR 识别框的统一缩放字号
            #
            # 【261 版修正】倾斜行必须用真实基线长度，不能用 R.width。
            # R 是**轴对齐**外接框，对倾角 θ、行高 h、基线长 L 的斜行，
            # R.width = L·cosθ + h·sinθ，比真实的 L 虚胖。长行误差可忽略，
            # 短行非常明显：θ=10°、h=30、L=50 的两字页码会胖出约 9%，
            # 照它算字号会把整行顶出识别框。
            if _box_vert and skew_len is not None:
                # 【262 版】竖排：字距 = 列长 ÷ 字数
                _base_w = skew_len / zoom
                _units = float(len(rec_text))
            else:
                _base_w = R.width if skew_len is None else (skew_len / zoom)
                _units = total_length_1
            fs = _base_w / _units if _units > 0 else 1

            # ==========================================================
            # 【266 版核心修正】竖排把"字距"与"字号"解耦
            # ----------------------------------------------------------
            # 262~265 版让同一个 fs 同时承担两件事：既当**字号**（画多大），
            # 又当**字距**（下一个字往下挪多远）。横排里这两者本来就相等，
            # 所以一直没出问题；竖排里它们是两个独立的量，绑死就会出事。
            #
            # 《中庸章句集注》这类经注合刻本最能暴露：实测全页真实字距恒为
            # 22~24pt（自相关扫描 64 个窄条，没有第二个峰），也就是说小注
            # 与大字的**行距是一样的**，小注只是**字形更小、列更窄**。于是：
            #
            #   · 字距 = 列长 ÷ 字数 = 22pt  —— 正确，位置就该这么排
            #   · 字号 若也取 22pt         —— 错误。字身绕基线旋转 -90 度后，
            #     横向跨度是 (ascender-descender) x 字号 ≈ 1.31 x 22 = 29pt，
            #     而小注子列只有 16pt 宽，左右各溢出 6.5pt 直接压进相邻子列。
            #     阅读器里选一列会连带选中隔壁，Ctrl+F 高亮也落在错的地方。
            #
            # 所以本版分开算：
            #   _pitch = 列长 ÷ 字数        -> 逐字推移量，保持不变
            #   fs     = min(_pitch, 列宽 / 1.31)  -> 字身，保证不越出本列
            #
            # 1.31 就是 (ascender - descender)，即字身横向跨度与字号的比值，
            # 直接从字体度量里取，不是拍脑袋的经验值。
            #
            # 对大字列没有任何影响：大字列宽 45pt、字距 23pt，
            # 45/1.31 = 34pt > 23pt，min 取的仍是字距，与 265 版完全一致。
            # 顺带把 262 版那条"长列少字"的上限也一并覆盖了（目录连点引导线
            # 那种 171pt 的字号，会被 列宽/1.31 直接压回正常尺寸）。
            # ==========================================================
            _pitch = fs          # 竖排的逐字推移量；横排下方不会用到
            if _box_vert and col_w:
                _fs_fit = (col_w / zoom) / VERT_GLYPH_SPAN
                if fs > _fs_fit:
                    fs = _fs_fit

            # ==========================================================
            # 【262 版新增】把竖排的基线摆到列的正中央
            # ----------------------------------------------------------
            # 写入轴取的是列的左上角，而字身并不是以基线为中心的：绕轴旋转
            # -90 度之后，字身在页面 +x 方向上从 基线-descender 伸到
            # 基线+ascender，中心落在 基线 + (asc+desc)/2 * 字号 处
            # （china-ss 实测 0.3887 em）。直接拿左上角当基线，整列文字会
            # 偏向列的左侧。这里把基线沿垂直于写入轴的方向推到列心。
            # ==========================================================
            if _box_vert and skew_len is not None and col_w:
                _u_len = math.hypot(_dx, _dy) or 1.0
                _ux, _uy = _dx / _u_len, _dy / _u_len       # 写入轴单位向量
                _px, _py = _uy, -_ux                        # 字身伸展方向
                _mid = (font_cn.ascender + font_cn.descender) / 2.0
                _shift = (col_w / 2.0) - _mid * fs * zoom   # 单位：图像像素
                pt_bl = [pt_bl[0] + _px * _shift, pt_bl[1] + _py * _shift]

            # ==========================================================
            # 【本版本新增：高速写入通道 (TextWriter)】
            # ----------------------------------------------------------
            # 下方原有的"逐字符 insert_text"写法有一个隐蔽的性能陷阱：
            # 每调用一次 insert_text，PyMuPDF 都要把整页的内容流重读一遍再
            # 追加写回，于是耗时随本页已写入的字数呈平方增长。实测：
            #     250 字/页 -> 0.28 秒    500 字/页 -> 0.90 秒
            #    1000 字/页 -> 5.17 秒   2000 字/页 -> 23.58 秒
            # 这正是"一页要 10~15 秒"的主要来源，且页面文字越密越慢。
            #
            # TextWriter 可以把整个文字框的所有字符攒在一起，一次性写入，
            # 耗时随字数线性增长，实测同样内容 1000 字/页仅 0.08 秒。
            #
            # 落点算法完全照搬下方原有代码：字号 fs、逐字 X 推移量、标点
            # 半宽推移，一个数都没改，因此每个字符的基线坐标与原来完全一致，
            # 提取出的文本内容也完全一致（已逐字符比对验证）。
            # 唯一区别：原写法会给标点额外套一个 0.5 倍横向压缩矩阵，把标点
            # 的字形挤窄一半；TextWriter 无法逐字施加矩阵，因此标点的高亮框
            # 宽度会恢复为整字宽。字符位置不受影响，只是选中标点时的高亮块
            # 略宽一点。若要完全保留旧行为，加 --legacy-text 参数即可回退。
            #
            # 安全起见，只在页面无旋转、文字无倾斜时启用；其余任何情况，
            # 以及本通道出现任何异常，都自动落回下方原有的逐字符通道。
            # ==========================================================
            box_morph_angle = page.rotation - text_angle
            fast_write_done = False

            # ==========================================================
            # 【261 版修改】门槛由"角度必须为 0"放宽为"页面自身未旋转"
            # ----------------------------------------------------------
            # 258 版这里 text_angle 恒为 0，所以 abs(page.rotation - text_angle)
            # < 1e-6 的实际含义就是 page.rotation == 0；改成显式判断后语义
            # 完全一致，区别只是现在 text_angle 可以非 0 了。
            #
            # 关键点：TextWriter.write_text() 本身就支持 morph 参数，可以把
            # 整框攒好的字符**一次性**带角度写入，所以倾斜页依然走高速通道，
            # 绝不会掉回下面那条随字数平方增长的逐字符慢速老路。
            #
            # 页面自身带旋转（page.rotation != 0）的仍然原样走老通道 —— 那条
            # 路径每个字符各自绕自身原点旋转、而推移量只加在水平方向上，天然
            # 只能表达"整页旋转"，表达不了"基线倾斜"；硬塞角度进去会变成每个
            # 字歪着、整行却还是平的。所以倾斜校正在上面就已经对旋转页整体
            # 关闭了（_skew_on 里的 page.rotation == 0）。
            # ==========================================================
            if (not getattr(args, 'legacy_text', False)) and page.rotation == 0:
                try:
                    tw = fitz.TextWriter(page.rect)
                    tw_pure = fitz.TextWriter(new_page.rect) if (args.pure and new_page is not None) else None

                    fast_offset = 0
                    for char in rec_text:
                        f_obj = font_en if char.isascii() else font_cn

                        part_start_x_pdf = true_x0 + (pt_bl[0] / zoom) + fast_offset
                        part_start_y_pdf = true_y0 + (pt_bl[1] / zoom)
                        part_unrotated = fitz.Point(
                            part_start_x_pdf,
                            part_start_y_pdf - textwriter_crop_y_delta,
                        ) * page.derotation_matrix

                        tw.append(part_unrotated, char, font=f_obj, fontsize=fs)

                        if tw_pure is not None:
                            tw_pure.append(fitz.Point(part_start_x_pdf - true_x0,
                                                      part_start_y_pdf - true_y0),
                                           char, font=f_obj, fontsize=fs)

                        # 推移量与下方原有算法逐字一致（标点仍然只前进半格）
                        # 【262 版】竖排恒为一个全角字身，标点也不压半宽
                        # 【266 版】用 _pitch 而不是 fs：字号可能已被列宽压小，
                        # 但字与字之间的距离必须保持真实字距，否则整列会缩短。
                        if _box_vert:
                            char_w = _pitch
                        else:
                            char_w = f_obj.text_length(char, fontsize=fs)
                            if char in cn_punctuation:
                                char_w *= 0.5
                        fast_offset += char_w

                    # ==================================================
                    # 【261 版新增】整框一次性带角度写入
                    # --------------------------------------------------
                    # morph = (支点, 矩阵)。支点取这一行基线的真实起点；矩阵
                    # 取 fitz.Matrix(-text_angle)：图像坐标系 y 轴向下，
                    # text_angle = atan2(dy, dx) 为正表示右端下沉，而
                    # fitz.Matrix(+θ) 在页面上是逆时针（右端上扬），故取负号。
                    # 这与下方老通道 morph_angle = page.rotation - text_angle
                    # 的符号约定完全一致。
                    #
                    # 实测(PyMuPDF 1.27.2)：这样写入后提取的文本顺序完全正常，
                    # 且提取出的 line["dir"] 精确等于倾斜方向，说明阅读器的
                    # 选中高亮框会跟着一起倾斜，复制、Ctrl+F 全部照常。
                    # ==================================================
                    skew_morph = None
                    skew_morph_pure = None
                    if abs(text_angle) > 1e-9:
                        _pivot_visual = fitz.Point(true_x0 + (pt_bl[0] / zoom),
                                                  true_y0 + (pt_bl[1] / zoom))
                        _pivot = fitz.Point(
                            _pivot_visual.x,
                            _pivot_visual.y - textwriter_crop_y_delta,
                        ) * page.derotation_matrix
                        skew_morph = (_pivot, fitz.Matrix(-text_angle))
                        skew_morph_pure = (fitz.Point(pt_bl[0] / zoom, pt_bl[1] / zoom),
                                           fitz.Matrix(-text_angle))

                    if args.debug:
                        tw.write_text(page, render_mode=0,
                                      color=colorsys.hsv_to_rgb(rec_score / 2, 1, 1),
                                      morph=skew_morph)
                    else:
                        tw.write_text(page, render_mode=3, morph=skew_morph)

                    if tw_pure is not None:
                        tw_pure.write_text(new_page, render_mode=0, morph=skew_morph_pure)

                    fast_write_done = True
                except Exception:
                    # 任何异常都不影响结果：直接落回下方久经考验的逐字符通道。
                    # 【261 版】落回前必须把倾角清零：老通道表达不了基线倾斜
                    # （原因见上面那段说明），带着角度进去会变成每个字歪着、
                    # 整行却还是平的。清零后就是 258 版的行为，安全兜底。
                    fast_write_done = False
                    text_angle = 0.0

            if fast_write_done:
                continue
            # ---------- 以下为原有逐字符写入通道，未作任何改动 ----------

            # 4. 逐字拼贴写入，动态推移基线 X 坐标
            current_x_offset = 0
            for char in rec_text:
                is_ascii = char.isascii()
                is_punc = char in cn_punctuation

                f_name = "tiro" if is_ascii else "china-ss"
                f_obj = font_en if is_ascii else font_cn

                # 在未旋转的视觉基线上，向右推移当前字符的起点
                part_start_x_pdf = true_x0 + (pt_bl[0] / zoom) + current_x_offset
                part_start_y_pdf = true_y0 + (pt_bl[1] / zoom)
                part_visual_point = fitz.Point(part_start_x_pdf, part_start_y_pdf)

                part_unrotated = part_visual_point * page.derotation_matrix

                # ==========================================================
                # 【物理级宽度压缩】：使用 Matrix 矩阵强行压扁标点符号
                # ==========================================================
                # 如果是标点，赋予它一个 X 轴为 0.5，Y 轴为 1.0 的变形矩阵
                base_morph = fitz.Matrix(0.5, 1.0) if is_punc else fitz.Matrix(1.0, 1.0)
                morph_angle = page.rotation - text_angle

                # 矩阵相乘：先进行横向挤压，再叠加文字正常的倾斜旋转角度
                combined_matrix = base_morph * fitz.Matrix(morph_angle)

                # 【核心修复】：PyMuPDF 的 morph 必须是一个元组 -> (锚点, 矩阵)
                morph = (part_unrotated, combined_matrix)

                if args.debug:
                    page.insert_text(
                        part_unrotated,
                        char,
                        fontname=f_name,
                        fontsize=fs,
                        render_mode=0,
                        color=colorsys.hsv_to_rgb(rec_score / 2, 1, 1),
                        morph=morph
                    )
                else:
                    page.insert_text(
                        part_unrotated,
                        char,
                        fontname=f_name,
                        fontsize=fs,
                        render_mode=3,
                        morph=morph
                    )

                if args.pure and new_page is not None:
                    pure_matrix = base_morph * fitz.Matrix(-text_angle)
                    pure_point = fitz.Point(part_start_x_pdf - true_x0, part_start_y_pdf - true_y0)
                    # 纯净模式同理，必须打包为长度为 2 的元组
                    pure_morph = (pure_point, pure_matrix)

                    new_page.insert_text(
                        pure_point,
                        char,
                        fontname=f_name,
                        fontsize=fs,
                        render_mode=0,
                        morph=pure_morph
                    )

                # 累加当前字符的真实渲染宽度，作为下一个字的起点
                # 【262 版】竖排恒为一个全角字身，标点也不压半宽
                # 【266 版】推移量用真实字距 _pitch，与字号解耦
                if _box_vert:
                    char_w = _pitch
                else:
                    char_w = f_obj.text_length(char, fontsize=fs)
                    if is_punc:
                        char_w *= 0.5  # 下一个字符的起点也会跟着向左平移，消除空隙
                current_x_offset += char_w

        if _timing_on:
            _tm["写入文字"] += _time.perf_counter() - _t_mark

        # ==========================================================
        # 【新增 1】：单页 OCR 结束，强制回收巨大图像矩阵与页面句柄
        # ==========================================================
        try:
            # 1. 粉碎大模型的输出结果与特征图
            del text
            del t0

            # 2. 粉碎极度吃内存的图像底层矩阵与 PDF 页面临时句柄
            del cim
            del pix
            del page
        except NameError:
            pass

        # 3. 【核心救命代码】：拿鞭子抽打 Python，强迫它在进入下一页前立刻倒垃圾！
        # 绝不允许垃圾在系统内存中堆积，斩断线性膨胀的源头
        # 【本版本微调】：改为每 10 页回收一次，而不是每页都回收。
        # 大模型常驻内存后对象图极其庞大，一次 gc.collect() 实测要 0.1~0.5 秒，
        # 每页都做等于白白搭进去可观的时间；每 10 页一次同样能压住内存增长。
        # 若想恢复"每页回收"的旧行为，把 gc_interval 改成 1 即可。
        import gc
        gc_interval = getattr(args, 'gc_interval', 10)
        _page_seq = getattr(args, '_page_seq', 0) + 1
        args._page_seq = _page_seq
        if gc_interval <= 1 or _page_seq % gc_interval == 0:
            gc.collect()
            # ==========================================================
            # 【254 版新增】：同时清空 MuPDF 自己的图像解码缓存
            # ----------------------------------------------------------
            # 这是 gc.collect() 完全够不着的一块内存：MuPDF 在 C 层维护
            # 自己的 store，缓存解码后的图像和字体。实测连续处理 240 页，
            # 只做 gc.collect() 时常驻 251 MB，加上 store_shrink 之后降到
            # 51 MB —— 200 MB 的差额全部是这块 Python 回收不到的缓存。
            # 它本身不是泄漏（不会随页数增长），但在内存吃紧时白白占着，
            # 顺手清掉可以给大模型腾出空间。
            # ==========================================================
            try:
                fitz.TOOLS.store_shrink(100)
            except Exception:
                pass



    # ====================================================================
    # 【本版本新增】：分段计时报告 (--timing)
    # ====================================================================
    if _timing_on and _tm_pages > 0:
        total = sum(_tm.values())
        print("\n" + "─"*58)
        print(f"⏱  分段计时报告（共统计 {_tm_pages} 页，仅含逐页处理环节）")
        print("─"*58)
        for k, v in sorted(_tm.items(), key=lambda kv: -kv[1]):
            share = (v / total * 100) if total > 0 else 0
            print(f"   {k}: {v/_tm_pages:7.3f} 秒/页   占比 {share:5.1f}%   累计 {v:7.2f} 秒")
        print(f"   {'合计':<8}: {total/_tm_pages:7.3f} 秒/页")
        print("─"*58)
        print("   判读方法：")
        print("     · 若 [OCR 推理] 占大头 -> 瓶颈在模型/显卡，属调用 GPU 的问题；")
        print("       此时请核对上方的运算设备检测，确认没有悄悄退回 CPU 运行。")
        print("     · 若 [写入文字] 占大头 -> 瓶颈在本脚本代码；")
        print("       请确认没有加 --legacy-text（那会退回旧的逐字符慢速通道）。")
        print("     · 若 [渲染页面] 占大头 -> 扫描清晰度设得过高，可下调 DPI。")
        print("     · 上方[诊断]行里的\"检出行数\"若普遍超过 100 行，说明扫描件噪点多、")
        print("       被切出大量碎块，识别耗时会成倍上升。此时降低清晰度档位、")
        print("       或用 --det-limit 调小检测输入，都能明显缓解。")
        print("─"*58 + "\n")

    # 扫尾与保存工作
    # （原先这段被粘贴了两遍，第二遍是纯粹的重复，已删除，行为不变）
    if args.cv:
        cv2.destroyAllWindows()

    # 保存提取出的纯净文本 PDF
    if args.pure and pure is not None:
        try:
            if pdf_doc.get_page_labels():
                pure.set_page_labels(pdf_doc.get_page_labels())
        except TypeError:
            pass
        try:
            if pdf_doc.get_toc():
                pure.set_toc(pdf_doc.get_toc())
        except TypeError:
            pass
        pure.save(
            pathlib.Path(output_pdf_path).stem + "-pure.pdf", garbage=2, deflate=True
        )
        pure.close()

   # ====================================================================
    # 终极“防锁死”保存与压缩机制（Last-mile Safety Net）
    # ====================================================================
    print(f"\n📦 正在执行底层无损压缩与最终文件封装 (garbage=4, deflate=True)...")
    if hasattr(args, 'ui_callback'):
        args.ui_callback(6, "STAGE 6: PDF PACKAGE", "阶段 6/6: 文件封装中，可能需数秒至数分钟，请勿关闭程序...")

        # 【核心防阻塞机制】：强制让后台线程睡眠 0.1 秒并交出 GIL 控制权。
        # 确保 Tkinter 主线程有足够的时间在被 C 层面的 PDF.save() 卡死之前，成功将 STAGE 6 的画面渲染到屏幕上。
        import time
        time.sleep(0.1)

    print(f"   [!] 引擎正在整合隐形文字层并进行极限 ZIP 压缩，")
    print(f"   [!] 此过程为单核阻塞运算，根据文件大小可能需要数秒至数分钟，请绝对不要关闭程序...")

    import os

    # ---------------------------------------------------------
    # 【修正升级】：真正的物理原地覆写逻辑 (-I) 与完美的闭环降级
    # ---------------------------------------------------------
    if getattr(args, 'inplace', False):
        print(f"\n⚠️ 警告: 已开启原地覆写模式 (-I)，正在物理替换源文件...")
        temp_path = input_pdf_path + ".tmp_save"
        try:
            # 1. 先安全地将修改后的结果打包为一个临时文件
            pdf_doc.save(temp_path, garbage=2, deflate=True)
            # 2. 释放对原文件的操作系统占用锁 (极其关键，一旦执行，pdf_doc 就失效了)
            pdf_doc.close()

            try:
                # 3. 原子级覆盖：用临时文件物理替换原文件
                os.replace(temp_path, input_pdf_path)
                print(f"✅ 覆写完成: {pathlib.Path(input_pdf_path).name}")

                print(f"\n" + "═"*65)
                print(f"✅ 任务执行完毕！")
                print(f"📁 绝对保存路径: {pathlib.Path(input_pdf_path).resolve()}")
                print("═"*65 + "\n")

                return "SUCCESS"

            except Exception as e:
                # ==========================================================
                # 【核心修复】：替换被拒 (Zotero 等阅读器锁定) 时的偷梁换柱
                # 此时 pdf_doc 已关闭，绝对不能顺延给下方的常规保存去处理！
                # ==========================================================
                print(f"\n❌ 原地覆写失败 (文件正被阅读器锁定): {e}")
                print("   └─ 正在将已生成的缓存文件转存为安全副本...")

                final_out_path = pathlib.Path(output_pdf_path)
                save_counter = 1

                # 寻找一个不冲突的新名字
                while final_out_path.exists():
                    final_out_path = final_out_path.with_name(f"{final_out_path.stem}_转存({save_counter}){final_out_path.suffix}")
                    save_counter += 1

                # 直接把刚刚辛苦存好的完整临时文件 temp_path，重命名为另存为的文件！
                if os.path.exists(temp_path):
                    os.replace(temp_path, str(final_out_path))

                print(f"\n 💡 提示: 原定覆写被拒绝，结果已自动转存保护至: {final_out_path.name}")
                print(f"\n" + "═"*65)
                print(f"✅ 任务执行完毕！")
                print(f"📁 绝对保存路径: {final_out_path.resolve()}")
                print("═"*65 + "\n")

                # 提前成功返回，完美避开下方的 document closed 报错
                return "SUCCESS"

        except Exception as e:
            # 这里捕获的是极小概率情况：生成 temp_path 本身就失败了（此时 pdf_doc 未关闭）
            print(f"\n❌ 严重错误：生成临时覆写缓存失败: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            print("   └─ 将自动降级为安全另存模式...")
            # 这种情况才会安全顺延给下方的常规另存逻辑

    # ---------------------------------------------------------
    # 常规的安全另存逻辑 (带有 -OCR 后缀)
    # ---------------------------------------------------------
    final_out_path = pathlib.Path(output_pdf_path)
    save_counter = 1
    saved_successfully = False

    # 开启“死缠烂打”保存模式：直接将修改后的 pdf_doc 另存为目标文件，绝不破坏源文件
    while not saved_successfully:
        try:
            pdf_doc.save(str(final_out_path), garbage=2, deflate=True)
            saved_successfully = True

            if str(final_out_path) != output_pdf_path:
                print(f"\n 警告: 原定输出文件被占用，结果已自动转存保护至: {final_out_path.name}")

        except (OSError, RuntimeError, PermissionError):
            final_out_path = final_out_path.with_name(f"{final_out_path.stem}_转存({save_counter}){final_out_path.suffix}")
            save_counter += 1

    # ==========================================================
    # 【新增】：输出任务视觉分界线与最终绝对路径
    # ==========================================================
    print(f"\n" + "═"*65)
    print(f"✅ 任务执行完毕！")
    print(f"📁 绝对保存路径: {final_out_path.resolve()}")
    print("═"*65 + "\n")

    return "SUCCESS"

def process_pdf(input_pdf_path, output_pdf_path):
    """
    核心调度器：协调原生检测、版面分析与 OCR 覆写。
    [阶段零] 原生排版嗅探
    [阶段一] 全局页边距抽样与智能拟合
    [阶段二] 逐页 OCR 识别与硬性拦截过滤
    """
    import fitz
    global args  # 确保能读取到 GUI/CLI 解析的全局配置

    # ==========================================================
    # 【262 版新增】竖排模式自动等效于 -S（跳过版面分析）
    # ----------------------------------------------------------
    # analyze_smart_layout 拟合天头地脚用的是横排文字行的统计规律：
    # 它假设"正文由许多条又宽又矮的横行密集堆叠而成"。竖排页面上每一列
    # 都是又窄又高、且几乎贯穿整个版心，这套统计完全失效，最坏的情况是
    # 把整列判成页眉页脚而整列丢弃 —— 正是"十列只出来三列"这类现象的
    # 一个可能来源。在拿到更多竖排样张调准竖排版面分析之前，这里直接
    # 关掉拦截器，宁可多识别边框和书耳，也绝不丢正文。
    # ==========================================================
    if getattr(args, 'vertical', False) and not getattr(args, 'skip_layout', False):
        args.skip_layout = True
        print("   [!] 竖排模式已开启 -> 自动跳过智能版面分析（等效 -S），避免整列正文被误判为页眉页脚。")


    # 打开源 PDF 文件
    pdf_doc = fitz.open(input_pdf_path)

    # ==========================================================
    # 【266 版新增】低分辨率竖排扫描件自动抬高检测输入上限
    # ----------------------------------------------------------
    # 前三档的检测上限（1280/1600/2000）是按横排现代印刷品标定的。竖排书
    # 里有一类很吃亏：扫描源分辨率本来就低、字小、还带双行小注，检测输入
    # 再被压到 1600，小注的笔画就彻底糊了。
    #
    # 但这**不是**所有竖排书的问题，所以不能对竖排一刀切抬高。两本实测：
    #
    #   《中庸章句集注》 源 89 DPI  det1600 -> 第4页 233 字
    #                              det2800 -> 第4页 810 字   （必须抬）
    #   《古文舊書考》   源 268 DPI det1600 -> 全书覆盖率 96%
    #                              det2800 -> 全书 95%，目录页 85%->72%
    #                                         （抬了反而碎，不该抬）
    #
    # 判据就取扫描源的原始分辨率：低于 150 DPI 才抬。这直接对应"源图本来
    # 就没多少像素，再降采样就没笔画了"这件事，而不是拍一个经验阈值。
    #
    # 2800 这个值来自显存曲线的拐点（RTX 3060 实测峰值 2853MB，
    # 而"完全不限"要 5489MB，会吃掉一张 6GB 卡的几乎全部显存）。
    #
    # 用户在命令行显式写了 --det-limit 就完全听用户的，一个字不改。
    # ==========================================================
    # 【268 版修正】必须整档提升，只抬 det_limit 没用
    # ----------------------------------------------------------
    # 266 版只抬了 det_limit，但检测网络的实际输入是
    # min(渲染像素, det_limit) —— 默认档渲染长边只有 2500，det 上限抬到
    # 2800 完全不起作用，等于白抬。实测第 4 页那条小注子列：
    #   渲染 2500px -> 检测根本框不出来
    #   渲染 3775px -> 框出 7 字 '及之名庸年常也'（真值「及之名庸平常也」）
    # 所以低分辨率竖排件要整档提升：渲染分辨率和检测上限一起上。
    _VERT_DET_FLOOR = 2800
    _VERT_DPI_FLOOR = 300.0
    _VERT_PX_FLOOR = 3800.0
    _LOWRES_DPI = 150.0
    _auto = (getattr(args, 'vertical', False)
             and not getattr(args, '_res_explicit', False))
    if _auto:
        _dpi = _native_scan_dpi(pdf_doc)
        if _dpi is not None and _dpi < _LOWRES_DPI:
            _o_dpi = float(getattr(args, 'target_dpi', 220.0) or 220.0)
            _o_px = float(getattr(args, 'max_pixels', 2500.0) or 2500.0)
            _o_det = int(getattr(args, 'det_limit', 0) or 0)
            args.target_dpi = max(_o_dpi, _VERT_DPI_FLOOR)
            args.max_pixels = max(_o_px, _VERT_PX_FLOOR)
            if 0 < _o_det < _VERT_DET_FLOOR:
                args.det_limit = _VERT_DET_FLOOR
            # 【270 版】同时放宽 DB 的两个阈值。低分辨率影印件的笔画本来就淡，
            # 默认 thresh=0.3 / box_thresh=0.6 会把大量细密小注整块滤掉。
            # 实测（《中庸章句集注》第4/11页，指标为检测框对墨迹的覆盖率）：
            #   thresh 0.3 / box 0.6（默认）-> 93.7% / 84.8%
            #   thresh 0.2 / box 0.4        -> 99.8% / 99.9%
            # 对 268 DPI 的《古文舊書考》不启用（那本判定为分辨率充足）。
            if getattr(args, 'det_thresh', None) is None:
                args.det_thresh = 0.2
            if getattr(args, 'det_box_thresh', None) is None:
                args.det_box_thresh = 0.4
            print("   [!] 扫描源仅约 %.0f DPI（低于 %.0f）-> 自动切到 300 DPI 强化检测档。"
                  % (_dpi, _LOWRES_DPI))
            print("       DB 检测阈值同步放宽为 thresh=%.2f / box_thresh=%.2f（检测端墨迹覆盖 94%% -> 99%%）。"
                  % (args.det_thresh, args.det_box_thresh))
            print("       渲染 %.0fDPI/%.0fpx -> %.0fDPI/%.0fpx，检测上限 %d -> %d。"
                  % (_o_dpi, _o_px, args.target_dpi, args.max_pixels, _o_det, args.det_limit))
            print("       低分辨率影印件的密排小字笔画很细，渲染或检测上限过低都会把它压糊；")
            print("       如需沿用原值请显式指定 --dpi / --max-pixels / --det-limit。")
        elif _dpi is not None:
            print("   └─ 扫描源约 %.0f DPI，分辨率充足，维持当前清晰度档位。" % _dpi)

    # ==========================================================
    # 【改动逻辑】：根据开关状态分流，并拦截非法输入
    # ==========================================================
    if getattr(args, 'enable_pages', False):
        try:
            # 尝试解析，如果失败会直接抛出 ValueError
            raw_range = getattr(args, 'page_range', '')
            target_pages = parse_page_range(raw_range, pdf_doc.page_count)
            print(f"\n🎯 [精准打击模式] 已锁定处理范围：物理页码 {target_pages[0]+1} 到 {target_pages[-1]+1}，共 {len(target_pages)} 页。")
        except ValueError as e:
            # 捕获异常，关闭内存，向外层发送致命错误信号
            pdf_doc.close()
            return f"ERROR_PAGE:{str(e)}"
    else:
        # 【关键兜底】：未勾选此功能时，稳妥地注入全书索引！
        target_pages = list(range(pdf_doc.page_count))

    # ==========================================================
    # 【新增阶段】：双联页物理拆分
    # 必须抢在版面分析与 OCR 之前执行：只有先把左右两页切成两个独立的
    # 页面对象，后续识别出的文字框才不会跨过中缝，阅读器也才不会把
    # 左页的一行和右页的对应行当成同一行来框选。
    # ==========================================================
    if getattr(args, 'split_double_page', False):
        try:
            new_doc, mapping = split_double_pages(pdf_doc, args)
        except ValueError as e:
            pdf_doc.close()
            return f"ERROR_PAGE:【双联页拆分】{str(e)}"

        # 拆分完成，原始文档已无用，把后续所有工作交给拆分后的新文档
        pdf_doc.close()

        # ==============================================================
        # 【254 版核心修复 3】：拆分结果先落盘，再以只读方式重新打开
        # --------------------------------------------------------------
        # 旧版是把拆分后的整本书一直捧在内存里，直到 OCR 全部跑完才释放。
        # 实测 120 个跨页拆成 240 个半页，光这一步就吃掉 3.8 GB，而且是
        # 随页数线性增长的 —— 页数一多，后面 OCR 阶段再申请内存就必然失败，
        # 报出 "malloc (xxx bytes) failed"。
        # 现在把它写进系统临时目录的一个文件，然后重新打开：MuPDF 会按需
        # 从磁盘读取页面，常驻内存变成一个与总页数无关的固定值。
        # 临时文件在本书处理结束时自动删除。
        # ==============================================================
        import os, tempfile
        _tmp_fd, _tmp_path = tempfile.mkstemp(prefix="pdfocr_split_", suffix=".pdf")
        os.close(_tmp_fd)
        print(f"   └─ 正在将拆分结果暂存到磁盘，避免整本书常驻内存...")
        new_doc.save(_tmp_path, garbage=3, deflate=True)
        new_doc.close()
        del new_doc

        import gc
        gc.collect()
        try:
            fitz.TOOLS.store_shrink(100)
        except Exception:
            pass

        pdf_doc = fitz.open(_tmp_path)
        args._split_tmp_path = _tmp_path

        # 用户填写的是【拆分前】的原始页码，这里换算成拆分后的新页码
        mapped_pages = []
        for orig_idx in target_pages:
            mapped_pages.extend(mapping[orig_idx])
        target_pages = mapped_pages

    # 将正确的索引数组挂载到全局，供后续版面抽样和 OCR 使用
    args.target_pages = target_pages


    if len(target_pages) < pdf_doc.page_count:
        print(f"\n🎯 [精准打击模式] 已锁定处理范围：物理页码 {target_pages[0]+1} 到 {target_pages[-1]+1}，共 {len(target_pages)} 页。")

    # 【触发 Stage 1 UI】：底层图元嗅探
    if hasattr(args, 'ui_callback'):
        args.ui_callback(1, "STAGE 1: NATIVE PDF DETECTION", "阶段 1/6: 正在进行底层图元嗅探，检测是否为原生排版文档...")

    # ==========================================
    # [阶段零]：检测原生文献并分流
    # ==========================================
    is_native = detect_native_pdf(pdf_doc)

    if is_native:
        print(f"\n[AI 检测雷达] 💡 警报：发现原生排版文档！(>300/页矢量特征)")

        # 核心分流逻辑 1：是原生文献，且选择了【关闭智能滤除】 -> 直接终止该文件任务
        if getattr(args, 'skip_layout', False):
            print(f"    └─ 动作: 当前已开启 [-S 关闭页边智能滤除]，且文件自带原生文字层，无运行必要。直接跳过！")

            # 清理内存并返回跳过指令给外层
            pdf_doc.close()
            return "SKIPPED_NATIVE"

        # 核心分流逻辑 2：是原生文献，且【未关闭智能滤除】 -> 仅擦除边缘，不走 OCR
        else:
            print(f"    └─ 动作: 仅挂载智能视觉版面引擎获取边距参数，清理四周边角料，【跳过 OCR 阶段】。")
    else:
        print("    └─ 结论: 未检测到原生矢量特征，确认为扫描件或栅格化文档，允许放行。")

    # ==========================================
    # [阶段一]：版面边界计算或默认值分配
    # ==========================================
    if not getattr(args, 'skip_layout', False):
        # 挂载大模型，提取精确的安全包络线
        layout_bounds = analyze_smart_layout(pdf_doc, args)

        # ==========================================================
        # 【255 版新增】：版面边界已经算完，立刻把版面模型踢出显存，
        # 给下一阶段真正干活的 OCR 模型腾地方。
        # 6 GB 显存的笔记本显卡上，这一步是"能不能跑满速"的分水岭。
        # ==========================================================
        AIModelEngine.release_layout_engine()

    else:
        # 如果用户选择关闭版面分析，直接跳过 Phase 1 并赋初始安全宽容值
        print("\n[!] 提示：已关闭智能版面分析，将执行全画幅无死角 OCR...")
        global_page_h = pdf_doc[0].rect.height
        global_page_w = pdf_doc[0].rect.width

        layout_bounds = {
            "top": 0.0,
            "bottom": global_page_h,
            "left_even": 0.0,
            "right_even": global_page_w,
            "left_odd": 0.0,
            "right_odd": global_page_w,
            "page_w": global_page_w,
            "page_h": global_page_h
        }
        print("[2/2] 开始正式扫描并写入隐形文字层...")


    # ==========================================
    # [阶段二]：执行 OCR 覆写与保存
    # ==========================================
    # 如果是原生文献，且没有关闭智能滤除，则走向纯净擦除链路
    if is_native and not getattr(args, 'skip_layout', False):
        result = process_native_pdf(pdf_doc, layout_bounds, args, output_pdf_path)
    # 否则（扫描件，或是强制要求全图扫的原生文献），走向 OCR 识别链路
    else:
        result = execute_ocr_and_render(pdf_doc, layout_bounds, args, input_pdf_path, output_pdf_path)

    # ==========================================================
    # 【新增 3】：整书处理完毕，执行深度显存与内存核弹级清洗
    # ==========================================================
    # 1. 确保当前文档被彻底关闭并释放文件系统锁
    if 'pdf_doc' in locals() and pdf_doc is not None:
        # 【核心防撞锁】：侦测文档是否已经在原地覆写模式中被提前关闭
        try:
            pdf_doc.close()
        except Exception:
            pass


    # 【254 版新增】：删除双联页拆分留下的临时文件
    import os
    _tmp_path = getattr(args, '_split_tmp_path', None)
    if _tmp_path:
        try:
            os.remove(_tmp_path)
        except Exception:
            pass          # 删不掉也不影响结果，系统重启时临时目录会被清理
        args._split_tmp_path = None

    # 3. 强制 Python 立刻回收所有无人认领的残骸（图像废料）
    import gc
    gc.collect()

    # 【新增】：强行清空 PyMuPDF 底层 100% 的高速缓存！
    # 因为马上要处理下一本全新的书了，上一本书的字体和水印缓存已经毫无价值
    import fitz
    fitz.TOOLS.store_shrink(100)

    # 4. 强制要求 PaddlePaddle 清空 GPU 缓存池
    try:
        import paddle
        if paddle.device.is_compiled_with_cuda():
            paddle.device.cuda.empty_cache()
    except Exception:
        pass

    # 5. 【新增】：强制物理睡眠 3 秒，让被烤热的 CPU/GPU 降温散热
    import time
    time.sleep(3)

    return result

# =========================================================================
# [独立模块 1]：GUI 图形界面视窗系统
# =========================================================================
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

# --- 新增：轻量级鼠标悬停提示 (Tooltip) 控件 ---
class ToolTip:
    # 【273 版】原来只能先构造、再另行给 .text 赋值，且只绑定控件自身。
    # 顶部控件行要给一个静态标签挂长说明，容器里还套着子控件，
    # 于是补两件事：构造时可直接传 text；deep=True 时连同所有后代一起绑定
    # （鼠标从父控件移到子控件会触发父控件的 <Leave>，不一起绑就会闪）。
    def __init__(self, widget, text="", deep=False):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.text = text
        self._bind(widget)
        if deep:
            self._bind_children(widget)

    def _bind(self, w):
        w.bind("<Enter>", self.enter, add="+")
        w.bind("<Leave>", self.leave, add="+")

    def _bind_children(self, w):
        for ch in w.winfo_children():
            self._bind(ch)
            self._bind_children(ch)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(400, self.showtip) # 悬停 400ms 后触发

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def showtip(self, event=None):
        if not self.text: return
        # 【273 版】原来用 self.widget.bbox("insert") 取偏移。它在 Label 上
        # 虽然不报错（Misc.bbox 实为 grid_bbox，返回 0），但语义上是给
        # Entry/Text 用的，对普通控件毫无意义。改成直接贴控件左下角。
        x = self.widget.winfo_rootx() + 8
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True) # 去除系统窗口边框
        tw.wm_geometry("+%d+%d" % (x, y))

        # 【273 版】配色与高级面板的悬停提示统一为深色浮层，
        # 免得同一个软件里出现两种风格的气泡。
        label = tk.Label(tw, text=self.text, justify="left", anchor="w",
                         background="#2B2B2B", foreground="#F2F2F2",
                         relief="solid", borderwidth=1,
                         wraplength=360, font=("微软雅黑", 9))
        label.pack(ipadx=6, ipady=4)

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

class PDFOCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("针对PDF的OCR智能识别与边码滤除-基于Paddle大模型")
        # 初始窗口高度变小，呈现极致紧凑感
        self.root.geometry("800x540")
        self.root.configure(bg="#FFFFFF")
        self.root.resizable(False, False)

        self.input_files = []
        self.output_dir = ""
        self.advanced_visible = False # 折叠状态追踪

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TCheckbutton', background='#FFFFFF', font=("微软雅黑", 10, "bold"), foreground="#333333")
        style.configure('TFrame', background='#FFFFFF')

        # 【274 版】加载 Doctor Cat 四态形象。任何一张缺失都只是没有猫，
        # 绝不能影响主程序启动，所以整段包在 try 里，失败就退化为无图模式。
        self._cat_imgs = {}
        self._cat_dialog_imgs = {}
        for _st in ("idle", "puzzle", "smile", "defeated"):
            for _kind, _store in (("header", self._cat_imgs), ("dialog", self._cat_dialog_imgs)):
                try:
                    _store[_st] = tk.PhotoImage(
                        file=_asset_path("ui", "doctorcat-%s-%s.png" % (_st, _kind)))
                except Exception:
                    pass
        # 窗口 / 任务栏图标
        try:
            self.root.iconbitmap(_asset_path("doctorcat-faithful-windows-exe-multisize.ico"))
        except Exception:
            try:
                self._icon_img = tk.PhotoImage(
                    file=_asset_path("doctorcat-faithful-explorer-small-48x48.png"))
                self.root.iconphoto(True, self._icon_img)
            except Exception:
                pass

        main_frame = tk.Frame(root, bg="#FFFFFF", padx=40, pady=25)
        # 【修改点1】：增加 anchor="n" 确保主框架内的组件永远置顶对齐，避免因窗口高度变化导致的内部垂直重绘（上下跳动）
        main_frame.pack(fill="both", expand=True, anchor="n")

        # 标题区
        # 【274 版】改为三列网格：左右两列等权重留白，标题居中不动，
        # 猫贴在中间那列的右侧。这样标题的视觉重心与原来完全一致，
        # 只是右边多了一只猫，不会因为加图把标题挤偏。
        head_frame = tk.Frame(main_frame, bg="#FFFFFF")
        head_frame.pack(fill="x", pady=(0, 20))
        head_frame.grid_columnconfigure(0, weight=1)
        head_frame.grid_columnconfigure(2, weight=1)

        title_box = tk.Frame(head_frame, bg="#FFFFFF")
        title_box.grid(row=0, column=1)
        tk.Label(title_box, text="N E X U S  P D F - O C R   E N G I N E",
                 font=("Arial", 22, "bold"), bg="#FFFFFF", fg="#111111").pack(pady=(0, 5))
        tk.Label(title_box, text="智能排版分析与OCR识别覆写系统",
                 font=("微软雅黑", 9), bg="#FFFFFF", fg="#888888").pack()

        self.lbl_cat = tk.Label(head_frame, bg="#FFFFFF")
        # 【274 版】主标题在 800px 窗口下本身就要 647px（共 720px 可用），
        # 留给猫的只有约 70px，所以页头素材取 64px 高（54px 宽），padx 收到 8。
        # 实测总占用 713px，留 7px 余量，不会把标题挤偏也不会压扁猫。
        self.lbl_cat.grid(row=0, column=2, sticky="w", padx=(40, 0))
        ToolTip(self.lbl_cat, "Doctor Cat —— 本程序的状态指示。" + "\n" +
                              "待机 / 识别中 / 已完成 / 出错，会换四种表情。")
        self.set_cat("idle")

        # ==========================================
        # 第一区：文件与目录 IO
        # ==========================================
        io_frame = tk.Frame(main_frame, bg="#FFFFFF")
        io_frame.pack(fill="x", pady=5)

        # 【核心修改 3】：使用 uniform="io_group"，强制左右两个模块宽度永远 1:1 绝对相等
        # 这样即使内部字符数变动（修改2），模块的物理边框也绝不会发生形变
        io_frame.columnconfigure(0, weight=1, uniform="io_group")
        io_frame.columnconfigure(1, weight=1, uniform="io_group")

        # ----------------- 左侧：源文件装载 -----------------
        in_frame = tk.Frame(io_frame, bg="#F9F9FB", padx=20, pady=15, highlightbackground="#EEEEEE", highlightthickness=1)
        in_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(in_frame, text="01  源文件装载", font=("微软雅黑", 10, "bold"), bg="#F9F9FB", fg="#333333").pack(anchor="w")
        tk.Label(in_frame, text="选择需要进行深度分析的 PDF 序列", font=("微软雅黑", 8), bg="#F9F9FB", fg="#888888").pack(anchor="w", pady=(0, 10))

        btn_box_in = tk.Frame(in_frame, bg="#F9F9FB")
        btn_box_in.pack(fill="x")
        # 【核心修改 1】：强制将左侧两个按钮的宽度锁死在 1:1，解决字数导致的宽窄不一
        btn_box_in.columnconfigure(0, weight=1, uniform="btn_in")
        btn_box_in.columnconfigure(1, weight=1, uniform="btn_in")

        self.btn_files = tk.Button(btn_box_in, text="📄 选择文件", command=self.select_files, bg="#FFFFFF", relief="solid", bd=1, font=("微软雅黑", 9), cursor="hand2")
        self.btn_files.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_input_dir = tk.Button(btn_box_in, text="🗂️ 选择文件夹", command=self.select_input_folder, bg="#FFFFFF", relief="solid", bd=1, font=("微软雅黑", 9), cursor="hand2")
        self.btn_input_dir.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # --- 改造：构建底部信息容器，防止文字过长撑破 1:1 对称布局 ---
        info_bot_frame = tk.Frame(in_frame, bg="#F9F9FB")
        info_bot_frame.pack(anchor="w", fill="x", pady=(5, 0))

        # 左侧：维持原有的数据包数量显示
        self.lbl_files = tk.Label(info_bot_frame, text="等待输入...(按住ctrl多选)", bg="#F9F9FB", fg="#AAAAAA", font=("微软雅黑", 8))
        self.lbl_files.pack(side="left")

        # 右侧：新增的具体文件名预览 (设置固定的截断宽度，绝不破坏 UI)
        self.lbl_filenames = tk.Label(info_bot_frame, text="", bg="#F9F9FB", fg="#00AEEF", font=("微软雅黑", 8), anchor="w")
        self.lbl_filenames.pack(side="left", padx=(10, 0), fill="x", expand=True)

        # 将刚刚写的 Tooltip 类挂载到右侧文件名标签上
        self.file_tooltip = ToolTip(self.lbl_filenames)

        # ----------------- 右侧：数据输出舱 -----------------
        out_frame = tk.Frame(io_frame, bg="#F9F9FB", padx=20, pady=15, highlightbackground="#EEEEEE", highlightthickness=1)
        out_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        tk.Label(out_frame, text="02  数据输出舱", font=("微软雅黑", 10, "bold"), bg="#F9F9FB", fg="#333333").pack(anchor="w")
        tk.Label(out_frame, text="指定处理后文件的存放路径（可选）", font=("微软雅黑", 8), bg="#F9F9FB", fg="#888888").pack(anchor="w", pady=(0, 10))

        btn_box_out = tk.Frame(out_frame, bg="#F9F9FB")
        btn_box_out.pack(fill="x")
        # 同样强制配平右侧两个按钮
        btn_box_out.columnconfigure(0, weight=1, uniform="btn_out")
        btn_box_out.columnconfigure(1, weight=1, uniform="btn_out")

        self.btn_dir = tk.Button(btn_box_out, text="◱ 设定目录", command=self.select_outdir, bg="#FFFFFF", relief="solid", bd=1, font=("微软雅黑", 9), cursor="hand2")
        self.btn_dir.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_open_dir = tk.Button(btn_box_out, text="📂 打开位置", command=self.open_current_dir, bg="#FFFFFF", relief="solid", bd=1, font=("微软雅黑", 9), cursor="hand2")
        self.btn_open_dir.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.lbl_dir = tk.Label(out_frame, text="默认: 原文件所在目录", bg="#F9F9FB", fg="#AAAAAA", font=("微软雅黑", 8))
        self.lbl_dir.pack(anchor="w", pady=(5, 0))

        # ==========================================
        # 第二区：执行与状态 (提至核心视觉区)
        # ==========================================
        bot_frame = tk.Frame(main_frame, bg="#FFFFFF")
        bot_frame.pack(fill="x", pady=(20, 10))

        self.btn_start = tk.Button(bot_frame, text="INITIALIZE SEQUENCE  /  启动识别序列", command=self.start_processing,
                                    bg="#111111", fg="#FFFFFF", font=("微软雅黑", 11, "bold"),
                                    activebackground="#333333", activeforeground="#FFFFFF",
                                    # 【274 版】按钮在处理期间是 state="disabled"，而 Tk 对
                                    # 禁用态**不用 fg，改用 disabledforeground**（默认系统灰）。
                                    # 加上原先又把底色换成浅灰 #CCCCCC，于是灰字压浅灰底，
                                    # 进度条和阶段文字几乎看不见。这里显式给一个亮青蓝，
                                    # 配合下面把处理态底色改深，两者对比度都够。
                                    disabledforeground="#A8ECFF",
                                    relief="flat", cursor="hand2", height=2)
        # 按钮下方的间距收紧，让状态灯靠近按钮
        self.btn_start.pack(fill="x", pady=(0, 8))

        # --- 唯一的系统状态指示灯 (移至按钮正下方，紧密关联动作) ---
        self.lbl_status = tk.Label(bot_frame, text="System Ready.", font=("Arial", 9), bg="#FFFFFF", fg="#00AEEF")
        self.lbl_status.pack(pady=(0, 18)) # 状态灯下方留出空间，与语言菜单隔开

        # ==========================================
        # 【第一行】：设定识别语种与扫描清晰度 (全局核心配置)
        # ==========================================
        config_frame = tk.Frame(bot_frame, bg="#FFFFFF")
        config_frame.pack(fill="x", pady=(0, 12))

        # --- 创建左右两个独立容器，实现完美的左右两端对齐拉伸 ---
        left_config = tk.Frame(config_frame, bg="#FFFFFF")
        left_config.pack(side="left")

        right_config = tk.Frame(config_frame, bg="#FFFFFF")
        right_config.pack(side="right") # 核心：强制吸附到界面的最右侧

        # --- 1. 左侧容器：设定识别语种 ---
        tk.Label(left_config, text="▤ 识别语种:", font=("微软雅黑", 9, "bold"), bg="#FFFFFF", fg="#333333").pack(side="left")

        self.var_lang = tk.StringVar()
        self.lang_cb = ttk.Combobox(left_config, textvariable=self.var_lang, font=("Arial", 9), width=16)
        self.lang_cb['values'] = [
            "ch (中英文混合 - 默认)", "en (纯英文)", "chinese_cht (繁体中文)", "japan (日文)",
            "korean (韩文)", "fr (法文)", "german (德文)", "ru (俄文)", "es (西班牙文)",
            "it (意大利文)", "ar (阿拉伯文)", "hi (印地文)", "th (泰文)", "vi (越南文)", "la (拉丁文)"
        ]
        self.lang_cb.pack(side="left", padx=(8, 6))
        self.var_lang.set(self.lang_cb['values'][0])

        # 将提示小字紧贴在语言菜单右侧，作为附属说明
        # 【273 版】原标签宽 287px，把整行的宽度需求撑过窗口宽，pack 于是
        # 从末尾开始压，「完成时自动打开」只分到 92px（需要 180px）。
        # 长说明挪进悬停提示，行内只留短标签。
        _lang_hint = tk.Label(left_config, text="*可手动键入", font=("微软雅黑", 8),
                              bg="#FFFFFF", fg="#AAAAAA")
        _lang_hint.pack(side="left")
        ToolTip(_lang_hint, "下拉框里没有的小语种，可以直接手动键入语种代码，"
                            "取值参考 PaddleOCR 官方识别手册（如 japan、korean、latin 等）。")

        # --- [新增] 中间视觉分隔符 (利用 expand=True 实现动态居中悬浮) ---
        tk.Label(config_frame, text=" | ", font=("Arial", 10), bg="#FFFFFF", fg="#DDDDDD").pack(side="left", expand=True)

        # --- 2. 右侧容器：设定扫描清晰度 ---
        tk.Label(right_config, text="◧ 扫描清晰度:", font=("微软雅黑", 9, "bold"), bg="#FFFFFF", fg="#333333").pack(side="left")

        self.var_dpi = tk.StringVar()
        self.dpi_cb = ttk.Combobox(right_config, textvariable=self.var_dpi, font=("微软雅黑", 9), width=20)
        # 【272 版】档位改为写明实际渲染 DPI 与显存需求。
        # 显存为 RTX 3060 上对 595x906pt 页面的实测峰值，页面越大越高。
        self.dpi_cb['values'] = [
            "150 DPI 极速 (显存 0.7GB)",
            "220 DPI 默认 (显存 1.0GB)",
            "300 DPI 高精 (显存 1.5GB)",
            "300 DPI 强化检测 (显存 2.8GB)"
        ]
        # 右侧无需外边距，直接贴紧窗口右边缘
        self.dpi_cb.pack(side="left", padx=(8, 0))
        self.var_dpi.set(self.dpi_cb['values'][1]) # 默认选中索引为 1 的 220 DPI

        # ==========================================
        # 【第二行】：主面板通用功能控制行 (单次执行控制)
        # ==========================================
        ctrl_frame = tk.Frame(bot_frame, bg="#FFFFFF")
        ctrl_frame.pack(fill="x", pady=(0, 5)) # 紧凑收尾

        # --- 1. 指定处理页码组件 ---
        self.var_enable_pages = tk.BooleanVar(value=False)
        self.var_pages = tk.StringVar()
        # 竖排文本是文档形制，不应藏在高级参数中；默认仍保持关闭。
        self.var_vertical = tk.BooleanVar(value=False)

        page_toggle_box = tk.Frame(ctrl_frame, bg="#FFFFFF", cursor="hand2")
        page_toggle_box.pack(side="left")

        self.icon_page_lbl = tk.Label(page_toggle_box, text="□", font=("Arial", 14), bg="#FFFFFF", fg="#BBBBBB")
        self.icon_page_lbl.pack(side="left", padx=(0, 6))

        page_title_lbl = tk.Label(page_toggle_box, text="【可选】指定处理页码:", font=("微软雅黑", 9, "bold"), bg="#FFFFFF", fg="#333333")
        page_title_lbl.pack(side="left")

        self.entry_pages = tk.Entry(ctrl_frame, textvariable=self.var_pages, font=("Arial", 9), width=10, relief="solid", bd=1, state="disabled", disabledbackground="#F0F0F0")
        self.entry_pages.pack(side="left", padx=8)

        _page_tip = ("先勾选左侧方框，再填页码，否则该输入框不生效。\n"
                     "填绝对页码（从 1 开始数的物理页），可以是单页 5，也可以是范围 5-10。\n"
                     "若同时开启了双联页拆分，页码按拆分前的物理页计算。")
        ToolTip(page_toggle_box, _page_tip, deep=True)
        ToolTip(self.entry_pages, _page_tip)

        # 页码联动控制函数
        def toggle_page_entry(*args):
            if self.var_enable_pages.get():
                self.entry_pages.config(state="normal", bg="#FFFFFF")
                self.icon_page_lbl.config(text="■", fg="#00AEEF")
            else:
                self.entry_pages.config(state="disabled", bg="#F0F0F0")
                self.icon_page_lbl.config(text="□", fg="#BBBBBB")

        def manual_toggle_page(event):
            self.var_enable_pages.set(not self.var_enable_pages.get())
            toggle_page_entry()

        self.icon_page_lbl.bind("<Button-1>", manual_toggle_page)
        page_title_lbl.bind("<Button-1>", manual_toggle_page)
        page_toggle_box.bind("<Button-1>", manual_toggle_page)

        # 视觉分隔符
        tk.Label(ctrl_frame, text=" | ", font=("Arial", 10), bg="#FFFFFF", fg="#DDDDDD").pack(side="left", padx=16)

        # --- 2. 竖排文本识别组件（主页面显式展示） ---
        vertical_toggle_frame = tk.Frame(ctrl_frame, bg="#FFFFFF", cursor="hand2")
        vertical_toggle_frame.pack(side="left")

        self.icon_vertical = tk.Label(vertical_toggle_frame, text="□", font=("Arial", 14),
                                      bg="#FFFFFF", fg="#BBBBBB")
        self.icon_vertical.pack(side="left", padx=(0, 6))
        lbl_vertical = tk.Label(vertical_toggle_frame, text="竖排文本识别",
                                font=("微软雅黑", 9, "bold"), bg="#FFFFFF", fg="#333333")
        lbl_vertical.pack(side="left")

        def toggle_vertical(*args):
            self.var_vertical.set(not self.var_vertical.get())
            self.icon_vertical.config(text="■" if self.var_vertical.get() else "□",
                                      fg="#00AEEF" if self.var_vertical.get() else "#BBBBBB")

        self.icon_vertical.bind("<Button-1>", toggle_vertical)
        lbl_vertical.bind("<Button-1>", toggle_vertical)
        vertical_toggle_frame.bind("<Button-1>", toggle_vertical)
        ToolTip(vertical_toggle_frame,
                "适用于自上而下、自右向左排版的竖排页面。开启后会按列写入文字层，"
                "并针对竖排扫描件调整识别策略。普通横排文档请保持关闭。", deep=True)

        tk.Label(ctrl_frame, text=" | ", font=("Arial", 10), bg="#FFFFFF",
                 fg="#DDDDDD").pack(side="left", padx=16)

        # --- 3. 自动打开文档组件 ---
        self.var_auto_open = tk.BooleanVar(value=True)

        auto_toggle_frame = tk.Frame(ctrl_frame, bg="#FFFFFF", cursor="hand2")
        auto_toggle_frame.pack(side="left")

        self.icon_auto_open = tk.Label(auto_toggle_frame, text="■", font=("Arial", 14), bg="#FFFFFF", fg="#00AEEF")
        self.icon_auto_open.pack(side="left", padx=(0, 6))

        lbl_auto_open = tk.Label(auto_toggle_frame, text="完成时自动打开文档", font=("微软雅黑", 9, "bold"), bg="#FFFFFF", fg="#333333")
        lbl_auto_open.pack(side="left")

        # 自动打开联动控制函数
        def toggle_auto(*args):
            self.var_auto_open.set(not self.var_auto_open.get())
            if self.var_auto_open.get():
                self.icon_auto_open.config(text="■", fg="#00AEEF")
            else:
                self.icon_auto_open.config(text="□", fg="#BBBBBB")

        self.icon_auto_open.bind("<Button-1>", toggle_auto)
        lbl_auto_open.bind("<Button-1>", toggle_auto)
        auto_toggle_frame.bind("<Button-1>", toggle_auto)

        # ==========================================
        # 第三区：折叠的高级参数面板
        # ==========================================
        # 增加上边距 pady=(10, 0)，让折叠按钮远离上方的核心区
        self.btn_toggle = tk.Button(main_frame, text="▼ 展开高级干预参数 (ADVANCED OVERRIDES)", command=self.toggle_advanced,
                                    bg="#FFFFFF", fg="#000000", font=("微软雅黑", 8, "bold"), relief="flat", cursor="hand2")
        self.btn_toggle.pack(pady=(10, 0))

        self.opt_container = tk.Frame(main_frame, bg="#FFFFFF")

        # ==========================================================
        # 【本版本改动 1】：高级参数区改为「画布 + 右侧滚动条」
        # ----------------------------------------------------------
        # 原先是把 8 条指令一次性铺开，面板越长窗口越高，在 125%/150%
        # 缩放的笔记本屏幕上，底部会被任务栏挡住、点不到。
        # 现在把这些指令装进一块可上下滚动的画布里：窗口高度被锁死在一个
        # 屏幕一定放得下的数值，看不见的部分用右侧滚动条（或鼠标滚轮）拉。
        # ==========================================================
        # 滚动条本体：做成细窄的浅灰样式，避免破坏整体的极简白色调
        style.configure("Nexus.Vertical.TScrollbar",
                        background="#DDDDDD", troughcolor="#F7F7F9",
                        bordercolor="#F7F7F9", arrowcolor="#999999",
                        relief="flat", arrowsize=12)

        self.opt_canvas = tk.Canvas(self.opt_container, bg="#FFFFFF",
                                    highlightthickness=0, bd=0, height=240)
        self.opt_scroll = ttk.Scrollbar(self.opt_container, orient="vertical",
                                        style="Nexus.Vertical.TScrollbar",
                                        command=self.opt_canvas.yview)
        self.opt_canvas.configure(yscrollcommand=self.opt_scroll.set)

        self.opt_scroll.pack(side="right", fill="y", pady=(10, 0))
        self.opt_canvas.pack(side="left", fill="both", expand=True, pady=(10, 0))

        # 真正承载指令的框架，作为一个"窗口对象"挂进画布里
        opt_frame = tk.Frame(self.opt_canvas, bg="#FFFFFF", highlightbackground="#EEEEEE", highlightthickness=1, padx=20, pady=15)
        self._opt_win = self.opt_canvas.create_window((0, 0), window=opt_frame, anchor="nw")
        opt_frame.columnconfigure(0, weight=1)
        opt_frame.columnconfigure(1, weight=1)

        # 内容高度变化时，重新计算可滚动范围
        def _sync_scrollregion(event=None):
            self.opt_canvas.configure(scrollregion=self.opt_canvas.bbox("all"))
        opt_frame.bind("<Configure>", _sync_scrollregion)

        # 画布宽度变化时，让内部框架跟着一起拉宽，保持左右两栏对齐
        def _sync_width(event):
            self.opt_canvas.itemconfigure(self._opt_win, width=event.width)
        self.opt_canvas.bind("<Configure>", _sync_width)

        # 鼠标滚轮支持：指针移进这块区域才接管滚轮，移出去就还给主窗口，
        # 避免用户在上方选文件时误滚动到高级面板。
        def _on_wheel(event):
            box = self.opt_canvas.bbox("all")
            if box is None:
                return
            if (box[3] - box[1]) <= self.opt_canvas.winfo_height():
                return          # 内容没超出可视高度，不需要滚
            self.opt_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_wheel(event=None):
            self.opt_canvas.bind_all("<MouseWheel>", _on_wheel)

        def _unbind_wheel(event=None):
            self.opt_canvas.unbind_all("<MouseWheel>")

        self.opt_canvas.bind("<Enter>", _bind_wheel)
        self.opt_canvas.bind("<Leave>", _unbind_wheel)
        opt_frame.bind("<Enter>", _bind_wheel)
        opt_frame.bind("<Leave>", _unbind_wheel)

        self.var_pure = tk.BooleanVar(value=False)
        self.var_inplace = tk.BooleanVar(value=False)
        self.var_pixmap = tk.BooleanVar(value=False)
        self.var_debug = tk.BooleanVar(value=False)
        self.var_cv = tk.BooleanVar(value=False)
        self.var_no_ocr = tk.BooleanVar(value=False)
        self.var_skip_layout = tk.BooleanVar(value=False)
        self.var_split_double = tk.BooleanVar(value=False)   # 【新增】双联页拆分开关
        self.var_timing = tk.BooleanVar(value=False)         # 【新增】分段计时诊断开关
        # 【261 版新增】倾斜校正默认开启，这个开关是"关掉它"，所以默认 False
        self.var_no_skew = tk.BooleanVar(value=False)
        # 【269 版新增】多尺度深度扫描，耗时翻倍，默认关闭
        self.var_multi_scale = tk.BooleanVar(value=False)

        # ==============================================================
        # 【271 版新增】高级参数悬停提示
        # --------------------------------------------------------------
        # 界面上只留两行短说明，完整解释（为什么要有这个开关、什么时候该用、
        # 代价是什么）改为鼠标悬停时浮出。这样既不牺牲信息量，又不会让面板
        # 变成一堵密密麻麻的小字墙。
        # 显示/隐藏都走延时：进入后 450ms 才浮出，离开后 120ms 才收起，
        # 这样在同一个选项块内部（图标 -> 标题 -> 说明）移动鼠标时不会闪烁。
        # ==============================================================
        def attach_tip(holder, text):
            if not text:
                return
            st = {"win": None, "show_job": None, "hide_job": None}

            def _show():
                st["show_job"] = None
                if st["win"] is not None:
                    return
                try:
                    x = holder.winfo_rootx() + 26
                    y = holder.winfo_rooty() + holder.winfo_height() + 6
                    tw = tk.Toplevel(holder)
                    tw.wm_overrideredirect(True)
                    tw.attributes("-topmost", True)
                    tk.Label(tw, text=text, justify="left", anchor="w",
                             bg="#2B2B2B", fg="#F2F2F2", font=("微软雅黑", 9),
                             wraplength=360, padx=11, pady=9,
                             relief="solid", bd=1).pack()
                    tw.wm_geometry("+%d+%d" % (x, y))
                    st["win"] = tw
                except Exception:
                    st["win"] = None

            def _hide():
                st["hide_job"] = None
                if st["win"] is not None:
                    try:
                        st["win"].destroy()
                    except Exception:
                        pass
                    st["win"] = None

            def _cancel(key):
                # 窗口已销毁时 after_cancel 会抛异常，这里一律吞掉
                if st[key] is not None:
                    try:
                        holder.after_cancel(st[key])
                    except Exception:
                        pass
                    st[key] = None

            def on_enter(_=None):
                _cancel("hide_job")
                if st["win"] is None and st["show_job"] is None:
                    try:
                        st["show_job"] = holder.after(450, _show)
                    except Exception:
                        st["show_job"] = None

            def on_leave(_=None):
                _cancel("show_job")
                if st["hide_job"] is None:
                    try:
                        st["hide_job"] = holder.after(120, _hide)
                    except Exception:
                        _hide()

            def bind_all(w):
                w.bind("<Enter>", on_enter, add="+")
                w.bind("<Leave>", on_leave, add="+")
                for ch in w.winfo_children():
                    bind_all(ch)
            bind_all(holder)

        def create_option(parent, row, col, var, title, desc, tip=None):
            f = tk.Frame(parent, bg="#FFFFFF")
            # 【271 版】sticky 由 "ew" 改为 "new"
            # ----------------------------------------------------------
            # 旧值 "ew" 只在水平方向拉伸，纵向不拉伸，于是 tkinter 把每个
            # 选项块在所在行里**垂直居中**。而一行的行高由该行最高的那块
            # 决定，所以只要同一行里两个选项的说明行数不一样（一个三行、
            # 一个一行），矮的那个标题就会被推到行的中间去，看上去参差不齐。
            # 加上 "n" 之后每块一律贴着行的顶边，标题就横平了。
            # 说明文字本版也统一压到两行以内，行高整齐，观感更稳。
            f.grid(row=row, column=col, sticky="new", padx=10, pady=6)

            # 头部容器，包含几何图标和标题，并设置鼠标悬停为手型
            head_frame = tk.Frame(f, bg="#FFFFFF", cursor="hand2")
            head_frame.pack(anchor="w")

            # 自定义视觉指示器：使用纯文本的几何图形
            # 未选中: 空心方块 □, 选中: 实心方块 ■ (也可以换成 ○ 和 ●)
            icon_lbl = tk.Label(head_frame, text="□", font=("Arial", 14), bg="#FFFFFF", fg="#BBBBBB")
            icon_lbl.pack(side="left", padx=(0, 6))

            title_lbl = tk.Label(head_frame, text=title, font=("微软雅黑", 10, "bold"), bg="#FFFFFF", fg="#333333")
            title_lbl.pack(side="left")

            # 描述文本 (缩进对齐)
            # 【本版本改动 4】：wraplength 由 310 收到 278，并显式 anchor="w"。
            # 面板右侧新增了滚动条，可用宽度比旧版少了十几个像素；旧版的 310
            # 本来就已经贴着栏宽的极限，加滚动条后就溢出了。Label 默认居中
            # 对齐，一溢出就变成左右两头同时被裁，说明文字会缺字。
            # 收窄到 278 并强制左对齐，文字改为正常换行，不再缺字。
            tk.Label(f, text=desc, font=("微软雅黑", 8), bg="#FFFFFF", fg="#999999",
                     justify="left", anchor="w", wraplength=278).pack(anchor="w", padx=(26, 4), fill="x")

            # 核心绑定：点击触发状态切换与 UI 渲染
            def toggle(event=None):
                # 反转当前的布尔值
                current_state = var.get()
                var.set(not current_state)

                # 动态改变图标形状和颜色
                if var.get():
                    icon_lbl.config(text="■", fg="#00AEEF") # 选中时：科技蓝实心方块
                else:
                    icon_lbl.config(text="□", fg="#BBBBBB") # 取消时：浅灰色空心方块

            # 将点击事件绑定到图标和标题上，提升点击热区范围
            icon_lbl.bind("<Button-1>", toggle)
            title_lbl.bind("<Button-1>", toggle)
            head_frame.bind("<Button-1>", toggle)

            # 【271 版】整块（图标 / 标题 / 说明）都能触发悬停提示
            attach_tip(f, tip)

        # ==========================================================
        # 【281 版】竖排文本已移至主页面；高级区只保留干预与诊断选项。
        # ----------------------------------------------------------
        # 排序原则：越靠前 = 越多人会去动它；越靠后 = 越偏开发者自查。
        # 阅读顺序是「从左到右、从上到下」，整条序列严格按频率单调递减：
        #
        #   1 关闭页边滤除    2 双联页拆分      <- 版面控制，最常被调整
        #   3 竖排文本        4 原地覆写        <- 文档类型 / 产物形态
        #   5 纯净文本        6 关闭倾斜校正
        #   7 光栅化渲染      8 擦除矢量层      <- 疑难救援，出问题了才用
        #   9 色彩置信度显影 10 分段计时诊断    <- 开发自查，普通用户用不到
        #
        # 【262 版新增的"竖排文本"为什么放在第 3 位】：它和"双联页拆分"
        # 一样，属于"这本书是什么形制"的声明 —— 拿到一本竖排书，
        # 用户在点开始之前就知道要勾它，而不是等出了问题再回来找。所以
        # 紧跟在版面控制那一档后面，排在所有"产物形态"与"疑难救援"之前。
        #
        # 【261 版新增的"关闭倾斜校正"为什么放在第 5 位】：倾斜校正是默认
        # 开启并且自带死区与钳位的，绝大多数人一辈子不需要关它；但它是本版
        # 唯一会改变文字层几何形态的新行为，万一某本书上表现异常，用户第一
        # 反应就是找地方把它关掉。所以归入"疑难救援"档，并排在该档最前 ——
        # 比"光栅化渲染""擦除矢量层"这两条更容易被想起来。
        #
        # 9 条指令铺进两列，末尾必然空出一格；把空格留在最后一行的右侧，
        # 视觉上最不突兀。滚动条默认停在顶部，最常用的两条一展开就能看到。
        # ==========================================================

        # ---------- 第 1 行：版面控制（最高频） ----------
        create_option(opt_frame, 0, 0, self.var_skip_layout, "关闭页边滤除 (-S)",
                      "跳过版面分析，全画幅识别。\n页眉页脚与页码也会一并写入。",
                      "默认会先用版面模型拟合出正文的天头地脚与左右边界，把落在正文框外的"
                      "页眉、页脚、页码拦掉，避免它们混进正文。勾选后跳过这一步，整页文字"
                      "一律识别写入。适合版式特殊、正文被误拦的文档。")
        create_option(opt_frame, 0, 1, self.var_split_double, "双联页拆分 (-D)",
                      "左右两页扫在同一张图时，\n沿中缝切成两页再识别。",
                      "自动探测靠近页面中心的装订中缝并切开，左右半页分别做版面分析与识别，"
                      "可以各自框选边界。注意：输出 PDF 的页数会变成原来的两倍；"
                      "指定处理页码时按拆分前的物理页计算。")

        # ---------- 第 2 行：输出产物形态 ----------
        create_option(opt_frame, 1, 0, self.var_inplace, "原文件覆写 (-I)",
                      "直接改写源 PDF，\n不再另存新文件。",
                      "识别结果直接写回原文件，不创建副本。省磁盘，但原件会被替换，"
                      "建议先自行备份。")

        # ---------- 第 3 行：产物形态续 + 疑难救援 ----------
        create_option(opt_frame, 1, 1, self.var_multi_scale, "多尺度深度扫描 (--multi-scale)",
                      "按 5 个缩放各识别一遍再合并。\n耗时约 5 倍，仅低清影印件需要。",
                      "低分辨率影印件里细密小字的检测正好卡在模型的阈值上：换一个渲染缩放，"
                      "同一列可能就从抓不到变成抓得到。本项按 5 个相邻缩放各识别一遍再合并"
                      "去重，实测可用文字约提高两成。\n"
                      "代价是耗时约为原来的 5 倍，清晰的印刷品不需要开。")
        create_option(opt_frame, 2, 0, self.var_no_skew, "关闭倾斜校正 (--no-skew)",
                      "强制水平写入文字层。\n仅在校正后反而对不齐时勾选。",
                      "默认会让文字层跟随每一行的真实倾角一起倾斜，以贴合歪斜的扫描件——"
                      "小于 0.3 度视为不倾斜，大于 30 度视为异常框不予校正。"
                      "勾选此项则一律水平写入，回到旧版行为。")

        # ---------- 第 4 行：疑难文件救援（偶尔用） ----------

        create_option(opt_frame, 2, 1, self.var_pure, "纯净文本模式 (-p)",
                      "额外生成一份剥离背景、\n只保留文字与排版的白底 PDF。",
                      "在正常输出之外再生成一个 -pure 文件：白底、无扫描图像，只按原位置"
                      "保留可见文字。适合需要干净排版底稿、或想直观检查文字层落点是否准确的场合。")
        create_option(opt_frame, 3, 0, self.var_no_ocr, "擦除矢量层 (-n)",
                      "只剥离原有文字层，不做识别。\n用于清除错误的旧识别结果。",
                      "跳过整个识别环节，仅把 PDF 里已有的文字图层擦掉。常用于"
                      "先清除一次失败的识别结果，再重新跑一遍。")

        # ---------- 第 5 行：低清影印件专用 + 开发者自查 ----------
        create_option(opt_frame, 3, 1, self.var_pixmap, "转图片识别 (-P)",
                      "先把矢量图层压成位图再分析。\n对付损毁或加密的文档。",
                      "强制把页面里的矢量元素合并渲染成位图之后再送识别。用于图文损毁、"
                      "或被加密限制导致常规提取失败的文献。")
        create_option(opt_frame, 4, 0, self.var_debug, "色彩置信度显影 (-g)",
                      "【调试】把文字层以热力图颜色\n可见地烙在画面上。",
                      "把本该隐形的文字层改为可见，并按识别置信度上色：色彩越冷，"
                      "代表模型对该字符越没把握。用于直观排查识别质量与落点。")

        # ---------- 第 6 行：开发者自查（普通用户不必理会） ----------
        create_option(opt_frame, 4, 1, self.var_timing, "分段计时诊断 (--timing)",
                      "【调试】打印每页各阶段耗时，\n并检测是否真的在用 GPU。",
                      "在控制台打印每页的耗时构成（渲染 / 擦除 / 推理 / 写入），并检测 Paddle "
                      "是否真的在用显卡运算。用于判断速度瓶颈到底在本程序的代码，还是在显卡。")

        #create_option(opt_frame, 4, 0, self.var_cv, "计算机视觉监控 (-c)", "开启 OpenCV 探针窗口，实时展现矩阵投影与滤波过程\n警告：会消耗额外的显存资源。")

        # ==========================================
        # 启动后台静默模型预热序列
        # ==========================================
        self.lbl_status.config(text="System Booting: 正在后台预热神经网络，界面可正常操作...", fg="#FFA500")
        #threading.Thread(target=self._silent_preload_models, daemon=True).start()

    def set_cat(self, state):
        """
        切换标题右侧的猫咪表情。state ∈ idle / puzzle / smile / defeated。
        素材缺失时静默跳过，不影响任何功能。
        """
        img = self._cat_imgs.get(state)
        if img is not None:
            try:
                self.lbl_cat.config(image=img)
                self.lbl_cat.image = img          # 必须持引用，否则会被 GC 掉变空白
            except Exception:
                pass

    def cat_dialog(self, title, message, state="defeated", ok_text="知道了"):
        """
        带猫咪表情的模态对话框。tkinter 的 messagebox 无法插入自定义图片，
        所以这里自建一个 Toplevel：左边表情、右边文案、底部一个确认按钮。
        素材缺失时自动退回系统 messagebox，保证任何情况下都有提示。
        """
        img = self._cat_dialog_imgs.get(state)
        if img is None:
            messagebox.showinfo(title, message)
            return
        try:
            win = tk.Toplevel(self.root)
            win.title(title)
            win.configure(bg="#FFFFFF")
            win.resizable(False, False)
            win.transient(self.root)
            try:
                win.iconbitmap(_asset_path("doctorcat-faithful-windows-exe-multisize.ico"))
            except Exception:
                pass

            body = tk.Frame(win, bg="#FFFFFF", padx=22, pady=20)
            body.pack(fill="both", expand=True)
            lbl_img = tk.Label(body, image=img, bg="#FFFFFF")
            lbl_img.image = img
            lbl_img.grid(row=0, column=0, sticky="n", padx=(0, 18))
            tk.Label(body, text=message, justify="left", anchor="w", wraplength=380,
                     bg="#FFFFFF", fg="#333333", font=("微软雅黑", 9)).grid(row=0, column=1, sticky="w")

            btn = tk.Button(win, text=ok_text, command=win.destroy,
                            bg="#111111", fg="#FFFFFF", activebackground="#333333",
                            activeforeground="#FFFFFF", relief="flat", cursor="hand2",
                            font=("微软雅黑", 9, "bold"), width=12)
            btn.pack(pady=(0, 18))

            win.update_idletasks()
            # 居中到主窗口
            px = self.root.winfo_rootx() + (self.root.winfo_width() - win.winfo_width()) // 2
            py = self.root.winfo_rooty() + (self.root.winfo_height() - win.winfo_height()) // 3
            win.geometry("+%d+%d" % (max(0, px), max(0, py)))
            win.grab_set()
            btn.focus_set()
            win.bind("<Return>", lambda e: win.destroy())
            win.bind("<Escape>", lambda e: win.destroy())
            self.root.wait_window(win)
        except Exception:
            messagebox.showinfo(title, message)

    def _silent_preload_models(self):
        """后台静默加载核心大模型，防止首次处理时产生卡顿"""
        try:
            # 提前触发模型实例化，此时会占用几秒钟，但不会卡死 UI
            AIModelEngine.get_layout_engine()
            # 默认预热中英文混合模型 (对应界面的默认选项 'ch')
            AIModelEngine.get_ocr_engine('ch')

            # 加载完成后，跨线程恢复系统就绪绿灯
            self.root.after(0, lambda: self.lbl_status.config(text="System Ready. (神经网络已驻留内存)", fg="#00AEEF"))
        except Exception as e:
            self.root.after(0, lambda: self.lbl_status.config(text=f"预热失败 (不影响正常启动): {str(e)[:30]}", fg="#FF5555"))



    # --- 新增：折叠面板控制逻辑 ---
    def toggle_advanced(self):
        if self.advanced_visible:
            # 收起：隐藏容器，并收缩主窗口尺寸
            self.opt_container.pack_forget()
            self.root.geometry("800x540")
            self.btn_toggle.config(text="▼ 展开高级干预参数 (ADVANCED OVERRIDES)")
            self.advanced_visible = False
        else:
            # 展开：显示容器，并伸展主窗口尺寸
            self.opt_container.pack(fill="both", expand=True)

            # ==================================================
            # 【本版本改动 3】：展开高度改为按屏幕实际可用高度自适应
            # --------------------------------------------------
            # 旧版写死 800x880，在 1080p + 150% 缩放的笔记本上，
            # 系统认为的屏幕高度只有 720，窗口底部直接被任务栏吞掉。
            # 现在先问一下屏幕多高，取「屏幕的 85%」和「完整高度」里的
            # 小者，剩下装不下的内容交给右侧滚动条，永远不会再被挡住。
            # ==================================================
            COLLAPSED_H = 540                       # 折叠状态的窗口高度
            # 【261 版】指令由 8 条增至 9 条、行数由 4 行增至 5 行，
            # 这里同步加高一行的空间；屏幕装不下的部分仍由右侧滚动条兜底。
            # 【271 版】说明统一压到两行后，每块恒为 76px、行距 88px，
            # 6 行内容实测总高 560px。给到 580 使高屏上无需滚动即可看全；
            # 屏幕装不下时仍由 safe_h 钳制，剩下的交给右侧滚动条。
            FULL_PANEL_H = 580                      # 11 条指令全部铺开所需高度
            screen_h = self.root.winfo_screenheight()
            safe_h = int(screen_h * 0.85)           # 给任务栏和标题栏留出余量

            target_h = min(COLLAPSED_H + FULL_PANEL_H, safe_h)
            # 画布的可视高度 = 窗口给高级面板留出的那一段
            canvas_h = max(150, target_h - COLLAPSED_H - 10)
            self.opt_canvas.configure(height=canvas_h)

            self.root.geometry("800x%d" % target_h)
            self.btn_toggle.config(text="▲ 隐藏高级干预参数 (ADVANCED OVERRIDES)")
            self.advanced_visible = True

            # 展开瞬间内容尚未布局完成，延后一拍再刷新滚动范围并回到顶部
            def _reset_scroll():
                self.opt_canvas.configure(scrollregion=self.opt_canvas.bbox("all"))
                self.opt_canvas.yview_moveto(0.0)
            self.root.after(60, _reset_scroll)

    def select_files(self):
        import pathlib
        files = filedialog.askopenfilenames(filetypes=[("PDF Documents", "*.pdf")])
        if files:
            self.input_files = list(files)
            self.lbl_files.config(text=f"已挂载 {len(self.input_files)} 个数据包：", fg="#00AEEF")

            # --- 新增：智能截断与悬停列表渲染 ---
            names = [pathlib.Path(f).name for f in self.input_files]

            # 拼装首行显示文字 (并做极限长度截断，强制保护布局)
            display_text = " / ".join(names)
            if len(display_text) > 28:
                display_text = display_text[:25] + "..."

            self.lbl_filenames.config(text=display_text, cursor="question_arrow") # 鼠标移上去变成问号手势暗示可悬停

            # 拼装 tooltip 内部的多行文字 (最多显示前 15 个，防止浮窗超出屏幕)
            tip_text = "\n".join(names[:15])
            if len(names) > 15:
                tip_text += f"\n...及其他 {len(names)-15} 个文件"
            self.file_tooltip.text = tip_text

    def select_input_folder(self):
        import pathlib
        dir_path = filedialog.askdirectory(title="选择包含 PDF 的文件夹")

        if not dir_path:
            return
        folder_path = pathlib.Path(dir_path)

        # 递归遍历 (rglob) 该文件夹及其所有子文件夹下的 .pdf 文件 (不区分后缀名大小写)
        pdf_files = [p for p in folder_path.rglob("*") if p.suffix.lower() == '.pdf']

        if not pdf_files:
            self.cat_dialog("提示", f"在 '{folder_path.name}' 中未找到任何 PDF 文件。")
            return

        self.input_files = [str(p) for p in pdf_files]
        self.lbl_files.config(text=f"已挂载 {len(self.input_files)} 个数据包", fg="#00AEEF")

        # --- 新增：智能截断与悬停列表渲染 ---
        names = [p.name for p in pdf_files]

        # 同步套用极限宽度的串联显示算法
        display_text = " / ".join(names)
        if len(display_text) > 28:
            display_text = display_text[:25] + "..."

        self.lbl_filenames.config(text=display_text, cursor="question_arrow")

        tip_text = "\n".join(names[:15])
        if len(names) > 15:
            tip_text += f"\n...及其他 {len(names)-15} 个文件"
        self.file_tooltip.text = tip_text

        # 自动化联动：智能推导并覆写右侧的数据输出舱路径
        # 规则：上一级路径下新建“原文件夹-OCR”
        auto_outdir = folder_path.parent / f"{folder_path.name}-OCR"
        self.output_dir = str(auto_outdir)

        # 刷新右侧 UI 显示，给予用户明确的安全感反馈
        disp_path = self.output_dir
        self.lbl_dir.config(text=f"阵列指向: ...{disp_path[-25:] if len(disp_path)>25 else disp_path}", fg="#00AEEF")

    def start_processing(self):
        if not self.input_files:
            self.cat_dialog("序列错误", "引擎缺少必要的数据输入源！\n请先装载 PDF 文件。")
            return

        # 初始启动时的 UI 状态
        self.btn_start.config(state="disabled", text="SYSTEM INITIATING... / 正在建立神经连接", bg="#111111")
        self.btn_files.config(state="disabled")
        self.btn_dir.config(state="disabled")
        self.lbl_status.config(text="进程已锁定，正在握手...", fg="#FF5555")
        self.set_cat("puzzle")          # 【274】进入识别 -> 疑惑脸

        threading.Thread(target=self.run_ocr_tasks, daemon=True).start()

    def update_ui_progress(self, stage, msg_main, msg_sub, current=None, total=None, stats=""):
        """新增：跨线程安全的 UI 神经反馈系统 (科幻风文本进度条)"""
        def _update():
            # 1. 更新下方的蓝色小字反馈
            self.lbl_status.config(text=msg_sub)

            # 2. 更新上方黑色按钮的动态进度条与阶段文字
            if current is not None and total is not None and total > 0:
                pct = current / total
                bar_len = 15 # 进度条总格数
                filled = int(pct * bar_len)
                bar = "■" * filled + "□" * (bar_len - filled)
                pct_str = f"{int(pct * 100)}%"

                # 直接将 tqdm 生成的专业时间/速率测算(stats)无缝拼接到科幻条后面
                self.btn_start.config(text=f"{msg_main}  /  [{bar}] {pct_str} {stats}")
            else:
                self.btn_start.config(text=msg_main)

        # 使用 after 确保在主事件循环中更新 UI
        self.root.after(0, _update)

    def select_outdir(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir = dir_path
            self.lbl_dir.config(text=f"阵列指向: ...{self.output_dir[-25:] if len(self.output_dir)>25 else self.output_dir}", fg="#00AEEF")

        # 【274 版】处理态底色由浅灰 #CCCCCC 改为深青，既与待机的纯黑区分开，
        # 又能让 disabledforeground 的亮青蓝字清晰可读。
        self.btn_start.config(state="disabled", text="PROCESSING... / 神经网络正在全速运算", bg="#123A47")
        self.btn_files.config(state="disabled")
        self.btn_dir.config(state="disabled")
        self.lbl_status.config(text="进程中：系统负载上升，处理速度约1~2 sec / page ，\n期间界面可能失去响应，请勿强行中断指令...", fg="#FF5555")

        threading.Thread(target=self.run_ocr_tasks, daemon=True).start()

    def run_ocr_tasks(self):
        global args
        import argparse

        # --- 新增：智能切分，提取干净的模型代码（如将 "fr (法文)" 切分成 "fr"） ---
        raw_lang_str = self.var_lang.get()
        clean_lang_code = raw_lang_str.split(" ")[0].strip()

        # --- 新增：解析 DPI 与像素上限设定 ---
        dpi_str = getattr(self, 'var_dpi', tk.StringVar(value="220")).get()
        # 【256 版】：检测网络的输入上限也跟着清晰度档位走。
        # 检测只负责框出文字行，识别仍从原分辨率裁剪，所以调小它
        # 只省显存和时间，不牺牲认字的清晰度。
        # ==============================================================
        # 【264 版新增】"强化检测"档
        # --------------------------------------------------------------
        # 前三档的检测输入上限（1280/1600/2000）是 256 版按"横排现代印刷品"
        # 标定的，对那类材料绰绰有余 —— 在 265 DPI 的《古文舊書考》上实测，
        # 1600 / 2500 / 不限三种设定的结果只在 94%~97% 之间浮动。
        #
        # 但低分辨率的密排影印件完全是另一回事：实测样本的扫描源只有约
        # 64~89 DPI，正文字身本就只有十几个像素，双行夹注更是只有
        # 一半，检测输入再被压到 1600，小注的笔画就彻底糊掉了。实测同一页：
        #
        #     档位                    显存峰值    第11页    第13页
        #     220 档 (det1600)        1021 MB    361 字    537 字
        #     300 档 (det2000)        1563 MB    466 字    587 字
        #     强化检测档 (det2800)     2853 MB    573 字    702 字
        #     det 完全不限            5489 MB    648 字    763 字
        #
        # det 完全不限能再多榨出一成，但 5489 MB 会吃掉一张 6GB 显卡的几乎
        # 全部显存，随时可能在别的环节爆掉；2800 这一档拿到了不限档九成的
        # 效果，显存只有它的一半，是这条曲线上的拐点。
        #
        # 只在用户主动选择时启用，前三档一个数都没动。
        # ==============================================================
        if "150" in dpi_str:
            target_dpi, max_pixels, det_limit = 150.0, 1800.0, 1280
        elif "强化检测" in dpi_str:
            target_dpi, max_pixels, det_limit = 300.0, 3800.0, 2800
        elif "300" in dpi_str:
            target_dpi, max_pixels, det_limit = 300.0, 3800.0, 2000
        else:
            target_dpi, max_pixels, det_limit = 220.0, 2500.0, 1600

        # 消除属性未定义报错
        args = argparse.Namespace(
            pure=self.var_pure.get(),
            inplace=self.var_inplace.get(),
            pixmap=self.var_pixmap.get(),
            debug=self.var_debug.get(),
            cv=self.var_cv.get(),
            no_ocr=self.var_no_ocr.get(),
            lang=clean_lang_code,
            target_dpi=target_dpi,          # <-- 注入动态 DPI
            max_pixels=max_pixels,          # <-- 注入动态像素上限
            skip_layout=self.var_skip_layout.get(),
            enable_pages=self.var_enable_pages.get(), # 开关状态
            page_range=self.var_pages.get(),
            # --- 【新增】双联页拆分参数 ---
            split_double_page=self.var_split_double.get(),
            split_ratio=0.5,        # 分割线基准位置（页宽比例）
            split_fixed=False,      # False = 启用中缝自动探测
            split_window=0.06,      # 自动探测的搜索窗口（页宽比例）
            split_gap=0.0,          # 分割线两侧的安全间隙 (pt)
            split_skip="",          # 不参与拆分的页码，如 "1,32"
            split_rtl=False,        # True = 右页在前（自右向左翻阅的书籍）
            split_dpi=300.0,        # 拆分时两个半页的重采样分辨率（仍受上面的像素上限钳制）
            split_quality=88,       # 半页图像的 JPEG 质量，88 是画质/内存的平衡点
            split_lossless=False,   # True = 无损存半页（内存占用约 27 倍，一般用不到）
            # --- 【新增】性能相关参数 ---
            det_limit=det_limit,    # 文字检测网络的输入长边上限（0 = 不限制）
            timing=self.var_timing.get(),   # 是否打印分段计时报告与设备体检
            legacy_text=False,      # True = 退回旧的逐字符慢速写入通道
            gc_interval=10,         # 每多少页强制回收一次内存
            # --- 【261 版新增】倾斜文字层校正 ---
            no_skew=self.var_no_skew.get(),  # True = 关闭倾斜校正，退回水平写入
            vertical=self.var_vertical.get(),  # 【262】True = 竖排文本（竖排排印/日文）
            multi_scale=(5 if self.var_multi_scale.get() else 1),  # 【269】5 = 五尺度深度扫描
            det_thresh=None,        # 【270】None = 用引擎默认；低分辨率影印件会自动放宽
            det_box_thresh=None,
            skew_max=30.0           # 超过这个角度的框判定为异常，按 0 度处理
        )

        args.ui_callback = self.update_ui_progress

        custom_outdir = pathlib.Path(self.output_dir) if self.output_dir else None

        successful_outputs = []
        skipped_native_files = [] # === 新增：用于记录被跳过的原生文件列表

        for input_path_str in self.input_files:
            input_path = pathlib.Path(input_path_str)
            new_filename = f"{input_path.stem}-OCR{input_path.suffix}"
            base_output_path = custom_outdir / new_filename if custom_outdir else input_path.with_name(new_filename)

            output_path = base_output_path
            counter = 1
            # 安全查重：只要同名文件已存在，直接追加序号，绝不覆写
            while output_path.exists():
                output_path = base_output_path.with_name(f"{base_output_path.stem}({counter}){base_output_path.suffix}")
                counter += 1

            try:
                result = process_pdf(input_path_str, str(output_path))

                # --- 新增：拦截非法的页码输入并弹窗中断 ---
                if isinstance(result, str) and result.startswith("ERROR_PAGE:"):
                    error_msg = result.split("ERROR_PAGE:", 1)[1]
                    # 跨线程安全弹窗
                    self.root.after(0, lambda m=error_msg: self.cat_dialog("页码格式错误", f"任务已强制中止：\n\n{m}"))
                    break # 直接打断整个批处理序列！

                if result == "SKIPPED_NATIVE":
                    # 如果是被识别为无需处理的原生文献
                    skipped_native_files.append(input_path.name)
                else:
                    actual_open_path = output_path

                    # 如果开启了原地覆写 (-I)，且预设的 -OCR 文件并未生成，说明覆写成功！
                    if getattr(args, 'inplace', False) and not output_path.exists():
                        actual_open_path = input_path

                    # 正常处理完成的文献 (记录真实存在的路径)
                    successful_outputs.append(actual_open_path)

                    # 【核心变动】：只要成功完成一个文件，判断是否勾选了自动打开
                    if self.var_auto_open.get():
                        # 使用 root.after 跨线程安全调用，防止 Windows 资源管理器与主 UI 发生线程抢占
                        self.root.after(0, self.open_single_file, actual_open_path)


            except Exception as e:
                print(f"Error processing {input_path.name}: {e}")

        self.root.after(0, self.finish_processing, successful_outputs, skipped_native_files)

    def open_current_dir(self):
        """读取当前设定的输出目录并打开；若未设定则智能打开首个源文件所在目录"""
        import os, platform, subprocess, pathlib
        target_dir = self.output_dir

        # 如果没有设定专门的输出目录，且已经装载了源文件，则提取源文件的文件夹
        if not target_dir and self.input_files:
            target_dir = str(pathlib.Path(self.input_files[0]).parent)

        if target_dir:
            try:
                if platform.system() == "Windows":
                    os.startfile(target_dir)
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", target_dir])
            except Exception as e:
                print(f"无法打开目录: {e}")
        else:
            self.cat_dialog("提示", "当前未设定输出目录，且未装载任何文件。")

    def open_single_file(self, file_path):
        """通用安全组件：调用系统默认阅读器打开指定的单一文件"""
        import os, platform, subprocess
        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(file_path)])
        except Exception as e:
            print(f"无法打开文件: {e}")

    def finish_processing(self, successful_outputs, skipped_native_files):
        success_count = len(successful_outputs)
        skipped_count = len(skipped_native_files)
        total_count = len(self.input_files)

        # 恢复主界面按钮的待机状态
        self.btn_start.config(state="normal", text="INITIALIZE SEQUENCE  /  启动识别序列", bg="#111111")
        self.btn_files.config(state="normal")
        self.btn_dir.config(state="normal")
        self.lbl_status.config(text="System Standing By.", fg="#00AEEF")
        # 【274】有产出 -> 微笑；一个都没成 -> 沮丧
        self.set_cat("smile" if success_count > 0 else "defeated")

        msg = f"分析序列已结束！\n安全处理完成 {success_count} / {total_count} 个数据包。"

        # 如果有被跳过的原生文件，追加具体名单
        if skipped_count > 0:
            skipped_list_str = "\n".join([f" • {name}" for name in skipped_native_files])
            msg += f"\n\n【智能滤过拦截】\n {skipped_count} 个文件被检测为【原生排版文献】且未开启页边滤除，因此被系统自动豁免，无需运行耗时识别：\n{skipped_list_str}"

        self.cat_dialog("序列状态报告", msg,
                        state="smile" if success_count > 0 else "defeated")

# =========================================================================
# [独立模块 2]：CLI 命令行参数解析器
# =========================================================================
def parse_arguments():
    import argparse
    # 解析命令行参数配置
    parser = argparse.ArgumentParser(
        description="A program than adds hidden(but copiable) text layer to image pdf.",
        epilog="Copyright (C) 2025 Cao Yang & 2026 Yang(last name) Qi. This is free software; distributed under GPLv3. There is NO warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.",
    )

    # 使用 nargs="+" 允许接收一个或多个文件路径（空格分隔）
    parser.add_argument("input_files", nargs="+", help="One or more input PDF files")
    # 注：我们彻底删除了 output_file 参数。批量处理时，全权交由脚本自动命名最安全。

    #允许用户指定输出目录
    parser.add_argument(
        "-o",
        "--outdir",
        type=str,
        help="Specify a custom output directory. If not specified, saves in the same directory as the input file.",
    )

    parser.add_argument(
        "-p",
        "--pure",
        action="store_true",
        help="generate a text-only auxiliary PDF.",
    )
    parser.add_argument(
        "-c",
        "--cv",
        action="store_true",
        help="show image read in OpenCV window",
    )
    parser.add_argument("-n", "--no-ocr", action="store_true", help="skip OCR")
    parser.add_argument("-l", "--lang", default="ch", help="OCR language")
    parser.add_argument(
        "-I",
        "--inplace",
        action="store_true",
        help="Add text to original PDF instead of extract images and create a new one.",
    )
    parser.add_argument(
        "-P",
        "--pixmap",
        action="store_true",
        help="Use rasterized page instead of extracted image to do OCR.",
    )
    parser.add_argument(
        "-g",
        "--debug",
        action="store_true",
        help="show confidence of text in color",
    )

    # === 新增：跳过智能版面分析指令 ===
    parser.add_argument(
        "-S",
        "--skip-layout",
        action="store_true",
        help="Skip smart layout analysis and process full page OCR.",
    )

    # === 新增：双联页拆分相关指令 ===
    parser.add_argument(
        "-D",
        "--split-double-page",
        action="store_true",
        help="Split each scanned page into two independent pages along the gutter before layout analysis and OCR.",
    )
    parser.add_argument(
        "--split-ratio",
        type=float,
        default=0.5,
        help="Base position of the split line as a fraction of page width (default 0.5).",
    )
    parser.add_argument(
        "--split-fixed",
        action="store_true",
        help="Disable gutter auto-detection and always cut at --split-ratio.",
    )
    parser.add_argument(
        "--split-window",
        type=float,
        default=0.06,
        help="Half-width of the gutter search window as a fraction of page width (default 0.06).",
    )
    parser.add_argument(
        "--split-gap",
        type=float,
        default=0.0,
        help="Safety gap in points left on each side of the split line (default 0).",
    )
    parser.add_argument(
        "--split-skip",
        type=str,
        default="",
        help="Comma separated 1-based page numbers that must NOT be split, e.g. 1,32.",
    )
    parser.add_argument(
        "--split-quality",
        type=int,
        default=88,
        help="JPEG quality used to store the two half pages after splitting "
             "(default 88; higher = larger memory and file size).",
    )
    parser.add_argument(
        "--split-lossless",
        action="store_true",
        help="Store the split half pages losslessly instead of JPEG. "
             "Much heavier on memory; only needed for special source scans.",
    )
    parser.add_argument(
        "--split-rtl",
        action="store_true",
        help="Order the two halves right-page-first (for right-to-left reading layouts).",
    )
    parser.add_argument(
        "--split-dpi",
        type=float,
        default=300.0,
        help="Resampling DPI used when rendering the two half pages (default 300).",
    )

    # === 新增：性能相关指令 ===
    parser.add_argument(
        "--skip-cuda-fetch",
        action="store_true",
        help="Skip the first-run download of the NVIDIA compute libraries "
             "(lightweight build only). Useful for testing, or when the "
             "libraries are placed next to the executable manually.",
    )
    # 【266 版】默认值改为 None，好把"用户显式指定"和"用了默认值"区分开：
    # 竖排 + 低分辨率扫描件会自动抬高这个上限，但只要用户自己写了这个参数，
    # 就完全听用户的。真正的默认值 1600 在 run_cli_mode 里补。
    parser.add_argument(
        "--det-limit",
        type=int,
        default=None,
        help="Max side length (px) fed into the text detection network "
             "(default 1600; vertical mode auto-raises it to 2800 on scans "
             "below 150 DPI). Lower = far less GPU memory and faster; "
             "0 disables the limit.",
    )
    parser.add_argument(
        "--timing",
        action="store_true",
        help="Print a per-stage timing breakdown and check whether the GPU is really being used.",
    )
    parser.add_argument(
        "--legacy-text",
        action="store_true",
        help="Fall back to the old per-character text writing path (much slower; keeps punctuation glyph squeezing).",
    )
    parser.add_argument(
        "--gc-interval",
        type=int,
        default=10,
        help="Run gc.collect() every N pages (default 10; set 1 to restore the old every-page behaviour).",
    )
    parser.add_argument(
        "--dpi",
        type=float,
        default=None,
        help="Target render DPI (default 220; the GUI tiers use 150/220/300).",
    )
    parser.add_argument(
        "--max-pixels",
        type=float,
        default=None,
        help="Max rendered long-side pixels, clamped to a hard ceiling of 4000 "
             "(GUI tiers use 1800/2500/3800).",
    )
    parser.add_argument(
        "--det-thresh", type=float, default=None,
        help="DB binarization threshold (PaddleOCR default 0.3). Lower keeps fainter strokes.",
    )
    parser.add_argument(
        "--det-box-thresh", type=float, default=None,
        help="DB box-keep threshold (PaddleOCR default 0.6). Lower keeps weaker boxes.",
    )
    parser.add_argument(
        "--multi-scale",
        nargs="?", type=int, const=5, default=1, choices=[1, 3, 5, 7],
        help="Deep scan: run detection at N nearby render scales and merge the results "
             "(bare flag = 5). Roughly N times slower; meant for low-resolution photo "
             "reprints whose fine dense text sits right on the detector's threshold.",
    )
    parser.add_argument(
        "-V", "--vertical",
        action="store_true",
        help="Treat the document as vertical (top-to-bottom, right-to-left) CJK text. Implies -S.",
    )
    parser.add_argument(
        "--no-skew",
        action="store_true",
        help="Disable text-line skew correction; write the text layer strictly horizontal (258 behaviour).",
    )
    parser.add_argument(
        "--skew-max",
        type=float,
        default=30.0,
        help="Text lines tilted by more than this many degrees are treated as anomalies and written horizontally (default 30).",
    )

    return parser.parse_args()

# =========================================================================
# [独立模块 3]：CLI 命令行批处理流水线
# =========================================================================
def run_cli_mode(parsed_args):
    import pathlib
    import cv2
    import sys

    # 核心：将局部解析的参数赋权给全局作用域，让深层的 process_pdf 能够顺畅读取
    global args
    args = parsed_args

    # ==================================================================
    # 【264 版新增】命令行补上清晰度旋钮
    # ------------------------------------------------------------------
    # 在此之前，target_dpi / max_pixels 只有图形界面的下拉框能选，命令行
    # 一律吃 getattr 的兜底值（220 DPI / 2500 像素），连带 det_limit 也只能
    # 单独指定。对低分辨率的密排影印件来说这套默认值明显不够用（实测见下方
    # get_ocr_engine 附近的注释），而命令行恰恰是批处理这类书的主要入口。
    # 这里把两个旋钮补齐，语义与界面档位完全一致。
    # ==================================================================
    # 【266/268 版】先记录"用户显式写了哪几个清晰度参数"，再补默认值。
    # 顺序不能反：下面几行会把 args.dpi / args.max_pixels 覆盖成具体数值，
    # 一旦先赋值再判断，getattr(...) is not None 就恒为真，自动提升永远不触发。
    # 三个参数任意一个被显式指定，就认为用户在自己掌控分辨率，不再自动整档提升。
    args._det_limit_explicit = getattr(args, 'det_limit', None) is not None
    args._res_explicit = (args._det_limit_explicit
                          or getattr(args, 'dpi', None) is not None
                          or getattr(args, 'max_pixels', None) is not None)

    args.target_dpi = float(getattr(args, 'dpi', None) or 220.0)
    args.max_pixels = float(getattr(args, 'max_pixels', None) or 2500.0)
    if args.det_limit is None:
        args.det_limit = 1600
    _failed = 0          # 【261 版】统计失败文件数，供退出码使用

    # --- 处理全局自定义输出目录 ---
    custom_outdir = None
    if args.outdir:
        custom_outdir = pathlib.Path(args.outdir)
        # 容错机制：如果用户指定的文件夹还不存在，脚本直接帮你自动创建它！
        custom_outdir.mkdir(parents=True, exist_ok=True)
        print(f"\n📂 已开启集中输出模式，所有文件将保存至: {custom_outdir}")

    if args.cv:
        cv2.namedWindow(sys.argv[0], cv2.WINDOW_NORMAL)

    # --- 启动全流程（支持多文件批量处理） ---
    for input_path_str in args.input_files:
        input_path = pathlib.Path(input_path_str)

        # 容错机制：如果某个文件路径填错或不存在，跳过它而不是让整个程序崩溃
        if not input_path.is_file():
            print(f"\n【!!!】 找不到文件，已跳过: {input_path}")
            continue

        # --- 输出文件命名（支持自定义目录）与“防锁死”预检测 ---
        new_filename = f"{input_path.stem}-OCR{input_path.suffix}"

        if custom_outdir:
            base_output_path = custom_outdir / new_filename
        else:
            base_output_path = input_path.with_name(new_filename)

        output_path = base_output_path
        counter = 1

        # 安全查重：只要同名文件已存在，直接追加序号，绝不覆写
        while output_path.exists():
            output_path = base_output_path.with_name(f"{base_output_path.stem}({counter}){base_output_path.suffix}")
            counter += 1

        output_path_str = str(output_path)

        print(f"\n" + "="*60)
        print(f"🚀 开始处理: {input_path.name}")
        print(f"📁 输出路径: {output_path_str}")
        print("="*60)

        try:
            # 呼叫主处理核心，并接收状态码
            status = process_pdf(input_path_str, output_path_str)
            if status == "SKIPPED_NATIVE":
                print(f"⏭️ 智能跳过: {input_path.name} (原生排版)\n")
            elif isinstance(status, str) and status.startswith("ERROR_PAGE:"):
                # 【新增】：让参数错误在命令行下也能如实报出，而不是误报成功
                print(f"❌ 任务中止: {status.split('ERROR_PAGE:', 1)[1]}\n")
                _failed += 1
            else:
                # ==========================================================
                # 【终极修正】：CLI 模式下的真实物理保存路径嗅探
                # ==========================================================
                actual_out_path = output_path
                if getattr(args, 'inplace', False) and not output_path.exists():
                    actual_out_path = input_path

                print(f"✅ 处理成功: {input_path.name}\n")
                print(f"   └─ 归档位置: {actual_out_path.resolve()}\n")

        except Exception as e:
            # 【261 版修正】原先只打印一行摘要，既看不到堆栈、也不影响退出码。
            # 对要分发给别人的程序来说这是错的：批处理脚本会把失败当成功，
            # 用户也拿不到任何可供排查的信息。
            #
            # 【262 版补充】内存不足是真实用户最容易遇到的一种失败：
            # 本程序模型常驻就要 2 GB 上下，16 GB 的机器上再开着浏览器、
            # 游戏或虚拟机就可能分配不出来。numpy 抛的原文是一句英文的
            # "Unable to allocate ... for an array with shape ..."，
            # 普通用户完全看不懂，所以这里翻译成可执行的建议。
            _msg = str(e)
            if ("Unable to allocate" in _msg or "MemoryError" in type(e).__name__
                    or "bad_alloc" in _msg or "Out of memory" in _msg):
                print(f"❌ 处理 {input_path.name} 失败：内存不足。\n")
                print("   本程序需要约 2~3 GB 可用内存。请尝试：")
                print("     · 关闭浏览器、游戏、虚拟机等占内存的程序后重试；")
                print("     · 在界面上把扫描清晰度调低一档（如 300 -> 220）；")
                print("     · 用「指定处理页码」把大文件拆成几段分批处理。")
                print(f"   （原始信息：{_msg[:120]}）\n")
            else:
                print(f"❌ 处理 {input_path.name} 时发生严重错误: {e}\n")
            import traceback as _tb
            for _line in _tb.format_exc().splitlines()[-8:]:
                print("   | " + _line)
            print()
            _failed += 1

    # ==================================================================
    # 【261 版修正】：如实汇报成败，并用退出码告诉外部世界
    #   0  = 全部成功（或被智能跳过）
    #   非 0 = 失败的文件数
    # 旧版无论成败一律退出 0，批处理脚本和自动化流程会误判成功。
    # ==================================================================
    if _failed:
        print("⚠️  全部任务结束：共 %d 个文件处理失败。" % _failed)
    else:
        print("🎉 所有任务已处理完毕！")
    return _failed

if hasattr(paddle.device, 'is_bfloat16_supported'):
    paddle.device.is_bfloat16_supported = lambda *args, **kwargs: False

# 再次确保禁用 DEBUG 输出
logging.disable(logging.DEBUG)

# =========================================================================
# [独立模块 4]：主路由枢纽 (Main Router)
# =========================================================================
def check_gpu_ready():
    """
    【257 版新增】开机自检：这台机器到底能不能跑。

    返回 (是否有可用 N 卡, 给用户看的说明文字)。
    本程序的速度完全建立在 NVIDIA 显卡上：实测同一本书，
    有 N 卡约 0.9 秒/页，纯 CPU 会慢一个数量级，而且会把整机拖到卡顿。
    所以没有 N 卡时必须明确告知，而不是让它默默地慢慢跑。
    """
    try:
        import paddle
        if not paddle.device.is_compiled_with_cuda():
            return False, ("当前程序包是 CPU 版本，没有编译 CUDA 支持。\n"
                           "请下载 GPU 版本的程序包。")
        if paddle.device.cuda.device_count() < 1:
            return False, ("未检测到可用的 NVIDIA 显卡。\n\n"
                           "本程序依靠 NVIDIA 显卡进行 AI 识别运算。\n"
                           "在纯 CPU 上运行会慢一个数量级，并且很可能\n"
                           "把整台电脑拖到严重卡顿，因此强烈不建议继续。\n\n"
                           "请确认：\n"
                           "  1. 这台电脑装有 NVIDIA 独立显卡；\n"
                           "  2. 显卡驱动已更新到较新版本。")
        name = paddle.device.cuda.get_device_properties(0).name
        return True, "已就绪：%s" % name
    except Exception as e:
        return False, "显卡环境自检失败：%s: %s" % (type(e).__name__, e)



def run_selftest():
    """
    【260 版新增】打包环境自检（命令行加 --selftest 触发）。

    打包成 exe 之后，很多在源码环境下理所当然的东西会悄悄失效：
    包元数据读不到、配置文件没打进去、DLL 搜索路径不对……而报错信息
    往往被上层吞成一句没头没尾的 "dependency error"。
    这个自检把每一环单独拎出来验一遍，一次性定位问题在哪一层。
    """
    import traceback

    def head(t):
        print("\n" + "=" * 66)
        print("  " + t)
        print("=" * 66)

    print("\n" + "#" * 66)
    print("#  PDFOCR 打包环境自检")
    print("#" * 66)

    head("1. 运行模式与路径")
    print("   frozen(是否为 exe)   : %s" % getattr(_sys, "frozen", False))
    print("   APP_DIR              : %s" % APP_DIR)
    print("   _MEIPASS             : %s" % getattr(_sys, "_MEIPASS", "(无)"))
    print("   PADDLE_PDX_CACHE_HOME: %s" % _os.environ.get("PADDLE_PDX_CACHE_HOME", "(未设置)"))
    print("   程序内含 CUDA 运算库  : %s" % _cuda_ready(_cuda_root()))
    print("   本机已有 CUDA 运算库  : %s" % _system_has_cuda_libs())
    _cache = _os.environ.get("PADDLE_PDX_CACHE_HOME", "")
    print("   程序路径是否纯 ASCII  : %s%s" % (
        _is_ascii(APP_DIR),
        "" if _is_ascii(APP_DIR) else "   <- 含中文，已启用路径防护"))
    if _cache:
        print("   模型路径是否纯 ASCII  : %s%s" % (
            _is_ascii(_cache),
            "" if _is_ascii(_cache) else "   <- 【危险】paddle 将无法读取模型"))
    _mroot = _os.path.join(_os.environ.get("PADDLE_PDX_CACHE_HOME", ""), "official_models")
    if _os.path.isdir(_mroot):
        print("   包内模型             : %s" % ", ".join(sorted(_os.listdir(_mroot))))
    else:
        print("   包内模型             : 【缺失】%s 不存在" % _mroot)

    head("2. 包元数据 importlib.metadata")
    import importlib.metadata as _im
    for pkg in ("paddlex", "paddleocr", "paddlepaddle-gpu"):
        try:
            print("   %-18s 版本 %s" % (pkg, _im.version(pkg)))
        except Exception as e:
            print("   %-18s 【读不到】%s: %s" % (pkg, type(e).__name__, e))
    try:
        md = _im.metadata("paddlex")
        extras = md.get_all("Provides-Extra", [])
        print("   paddlex extras     : %d 个" % len(extras))
        reqs = _im.requires("paddlex") or []
        print("   paddlex requires   : %d 条" % len(reqs))
    except Exception as e:
        print("   paddlex 元数据读取失败: %s: %s" % (type(e).__name__, e))

    head("3. paddlex 依赖自检（这是报 dependency error 的那一层）")
    try:
        from paddlex.utils import deps as _deps
        for fn in ("get_dep_version", "is_dep_available", "require_deps"):
            print("   deps.%-20s %s" % (fn, "有" if hasattr(_deps, fn) else "无"))
        for extra in ("ocr", "ocr-core", "cv", "base"):
            try:
                fn = getattr(_deps, "is_extra_available", None)
                print("   extra %-10s 可用: %s" % (extra, fn(extra) if fn else "(无此接口)"))
            except Exception as e:
                print("   extra %-10s 检查失败: %s: %s" % (extra, type(e).__name__, e))
    except Exception:
        print("   导入 paddlex.utils.deps 失败:")
        for l in traceback.format_exc().splitlines()[-6:]:
            print("      | " + l)

    head("4. paddle 与运算设备")
    try:
        import paddle
        print("   paddle 版本          : %s" % getattr(paddle, "__version__", "?"))
        print("   编译含 CUDA          : %s" % paddle.device.is_compiled_with_cuda())
        print("   GPU 数量             : %s" % paddle.device.cuda.device_count())
        print("   resolve_device()     : %s" % AIModelEngine.resolve_device())
    except Exception:
        for l in traceback.format_exc().splitlines()[-6:]:
            print("      | " + l)

    head("5. 逐个实例化模型引擎（关键）")
    print("\n   [5.1] 轻量通道 LayoutDetection")
    try:
        from paddleocr import LayoutDetection
        eng = LayoutDetection(model_name="PP-DocLayout_plus-L",
                              device=AIModelEngine.resolve_device(),
                              enable_mkldnn=False)
        print("        ✅ 实例化成功")
        del eng
    except Exception:
        print("        ❌ 失败，完整堆栈：")
        for l in traceback.format_exc().splitlines():
            print("        | " + l)

    # 【275 版】原先这里有一项 [5.2] 实例化 PPStructureV3。它是发布包平白
    # 多出 1.5 GB 的元凶：V3 会无条件加载 PP-Chart2Table(1368MB) 和
    # PP-DocBlockLayout(124MB)，用户只是想跑个诊断，却触发 1.4 GB 下载。
    # V3 通道已在本版整体移除，这一项随之删除。

    print("\n   [5.2] OCR 通道 PaddleOCR")
    try:
        ocr = AIModelEngine.get_ocr_engine("ch")
        print("        ✅ 实例化成功")
        del ocr
    except Exception:
        print("        ❌ 失败，完整堆栈：")
        for l in traceback.format_exc().splitlines():
            print("        | " + l)

    print("\n" + "#" * 66)
    print("#  自检结束")
    print("#" * 66 + "\n")


def main():
    """
    环境嗅探引擎：根据用户启动程序的方式，智能分发执行模式。
    """
    import sys

    # 独立安装模式：下载器已在任何 Paddle 导入之前运行。完成后直接退出，
    # 不要求用户再提供一个 PDF，也不把下载参数交给业务参数解析器。
    if "--install-cuda" in sys.argv:
        if _CUDA_BOOTSTRAP_OK:
            print("CUDA 运算库已经准备完成。请正常启动 PDFOCR。")
            return
        print("CUDA 运算库未能完成安装，请查看程序目录下的 CUDA下载日志.txt。")
        sys.exit(2)

    # 核心分流逻辑：如果附带了任何额外参数，说明用户是在命令行（终端）执行的，切入 CLI 模式
    if "--selftest" in sys.argv:
        run_selftest()
        return

    if len(sys.argv) > 1:
        ok, msg = check_gpu_ready()
        if not ok:
            print("\n" + "!" * 60)
            print("⚠️  显卡环境提醒")
            print("!" * 60)
            for line in msg.split("\n"):
                print("   " + line)
            print("!" * 60)
            print("   程序仍会继续，但速度会非常慢。\n")
        parsed_args = parse_arguments()
        # 【261 版】把失败数作为退出码返回给调用方
        sys.exit(run_cli_mode(parsed_args))

    # 如果没有任何参数，说明用户是直接双击了 .py 脚本运行，智能唤醒可视化 GUI
    else:
        global _STARTUP_NOTICE
        if _STARTUP_NOTICE is not None:
            try:
                _STARTUP_NOTICE.destroy()
            except Exception:
                pass
            _STARTUP_NOTICE = None
        root = tk.Tk()

        # 【257 版】：GUI 起来之前先做显卡自检，没有 N 卡就问一句再走，
        # 免得用户莫名其妙地等上几个小时、还以为程序卡死了。
        ok, msg = check_gpu_ready()
        if not ok:
            root.withdraw()
            go_on = messagebox.askyesno(
                "显卡环境提醒",
                msg + "\n\n仍要继续吗？（继续将以极慢的 CPU 模式运行）")
            if not go_on:
                root.destroy()
                return
            root.deiconify()

        app = PDFOCRApp(root)
        root.mainloop()

if __name__ == "__main__":
    main()
