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
"""

# （注：以下为注入了“核心锚定、奇偶分流、逆向滤波”等高级版面分析算法的智能识别脚本）

#!/usr/bin/env python3
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
import paddle

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

# =========================================================================
# [独立模块 0.5]：全局 AI 模型生命周期调度器 (单例缓存池)
# =========================================================================
class AIModelEngine:
    _layout_engine = None
    _ocr_engines = {} # 使用字典缓存不同语种的 OCR 模型，防止切换语种失效

    @classmethod
    def get_layout_engine(cls):
        """单例获取版面分析大模型"""
        if cls._layout_engine is None:
            from paddleocr import PPStructureV3
            cls._layout_engine = PPStructureV3(
                use_region_detection=True,           
                use_table_recognition=False,         
                use_formula_recognition=False,       
                use_seal_recognition=False,          
                use_chart_recognition=False,         
                use_doc_orientation_classify=False,  
                use_doc_unwarping=False,             
                use_textline_orientation=False,    
                device="gpu:0",           
                precision="fp32",
                enable_mkldnn=False     
            )
        return cls._layout_engine

    @classmethod
    def get_ocr_engine(cls, lang):
        """单例获取对应语种的 OCR 识别大模型"""
        if lang not in cls._ocr_engines:
            from paddleocr import PaddleOCR
            cls._ocr_engines[lang] = PaddleOCR(
                use_textline_orientation=True,      
                lang=lang,                     
                use_doc_unwarping=False,            
                use_doc_orientation_classify=False,
                device="gpu:0",          
                precision="fp32",       
                enable_mkldnn=False     
            )
        return cls._ocr_engines[lang]

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

def analyze_smart_layout(pdf_doc, args):
    """
    [阶段一独立模块]：全局智能版面抽样分析与边界拟合
    功能：加载 PPStructureV3 大模型，抽取连续页进行结构嗅探，并运行滤波算法剔除页眉页脚噪音。
    返回：包含 6 个全局安全边界参数的字典 dict。
    """
    from paddleocr import PPStructureV3
    import numpy as np

    if hasattr(args, 'ui_callback'):
        args.ui_callback(2, "STAGE 2: ALIGNING LAYOUT AI", "阶段 2/6: 正在调取版面分析大模型...")
    
    # 【改动】：直接从全局缓存池获取模型，首次调用耗时，后续瞬间完成
    layout_engine = AIModelEngine.get_layout_engine()

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
            
        res_json = outputs[0].json
        if 'res' not in res_json or 'layout_det_res' not in res_json['res']:
            continue
            
        layout_results = res_json['res']['layout_det_res'].get('boxes', [])

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
    if args.pure:
        pure = fitz.open()

    if hasattr(args, 'ui_callback'):
        args.ui_callback(4, "STAGE 4: ALIGNING OCR CORE", "阶段 4/6: 正在调取OCR 核心识别模型...")
    
    # 【改动】：向全局引擎请求对应语种的模型
    ocr = AIModelEngine.get_ocr_engine(args.lang)
    
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
        
        # 预处理：擦除 PDF 现有的文字图层，防止原有乱码干扰
        page.add_redact_annot(page.rect)
        page.apply_redactions(images=0)
        
        # ==========================================================
        # 智能动态分辨率 (Dynamic Resolution) - 支持手动调整清晰度
        # ==========================================================
        # 获取当前页面的真实物理尺寸（PDF 默认单位为 Point，72 Point = 1 英寸）
        max_side_points = max(page.rect.width, page.rect.height)
        
        # 1. 目标基准：从用户面板获取的目标 DPI (兼顾 CLI 的 220 默认兜底)
        target_dpi = getattr(args, 'target_dpi', 220.0)
        theoretical_zoom = target_dpi / 72.0
        
        # 2. 深度学习安全阈值钳制：从用户面板获取的像素上限
        max_safe_pixels = getattr(args, 'max_pixels', 2500.0)
        
        if max_side_points * theoretical_zoom > max_safe_pixels:
            # 如果按目标 DPI 放大后超出了安全红线，则动态计算一个更小的倍率
            actual_zoom = max_safe_pixels / max_side_points
        else:
            actual_zoom = theoretical_zoom
            
        # 3. 终极自适应：允许向下缩小！
        # 解除了之前 max(1.0, zoom) 的死锁。如果源 PDF 本身的长边高达 5000 Point，
        # actual_zoom 将自动计算为 0.7，实现对巨型页面的物理级“缩小”。
        # 设立 0.3 为兜底极限，防止遇到异常参数导致画面彻底坍缩。
        zoom = max(0.3, actual_zoom)
        
        mat = fitz.Matrix(zoom, zoom)
        
        # alpha=False 强制生成实心白色背景，防止黑底报错
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # 将 PyMuPDF 提取的像素流转为 numpy 数组，再调换 RGB 通道为 BGR 供 PaddleOCR 读取
        cim = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        cim = np.ascontiguousarray(cim[..., [2, 1, 0]])

        # OpenCV 的 debug 可视化界面支持 (放在涂白之后，这样你能通过开启 -c 直观看到画面被裁切的效果)
        if args.cv:
            cv2.imshow(sys.argv[0], cim)
            cv2.waitKey(1)
            
        # 跳过实际 OCR 运算（用于单纯擦除旧文本等目的）
        if args.no_ocr:
            continue
            
        # 新建纯净文本页（针对 -p 参数）
        if args.pure:
            new_page = pure.new_page(width=page.rect.width, height=page.rect.height)
            
        # 调用引擎进行全图 OCR 识别（此时大模型看到的只有纯净的正文！）
        text = ocr.predict(cim)
        if not text[0]:
            continue
        t0 = text[0]
        
        import math  # 如果文件开头没有，请在这里或者顶部引入

        # 遍历全页所有识别出的文字框
        for rec_box, rec_text, rec_score in zip(
            t0["rec_boxes"], t0["rec_texts"], t0["rec_scores"]
        ):
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
            # --- 拦截器结束 ---

            # --- 拦截器结束 ---

            # ==========================================================
            # 【终极修正 6.1】：安全实例化内置字体对象
            # ==========================================================
            font_en = fitz.Font("tiro")      
            font_cn = fitz.Font("china-ss")  
            
            # 1. 定义需要被强行压缩宽度的全角标点集合
            cn_punctuation = set("，。、；：？！“”‘’（）《》〈〉【】『』—…")

            # 2. 逐字符测算物理长度 (针对标点启用 50% 折半测算)
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
            fs = R.width / total_length_1 if total_length_1 > 0 else 1

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

                if args.pure:
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
                char_w = f_obj.text_length(char, fontsize=fs)
                if is_punc:
                    char_w *= 0.5  # 下一个字符的起点也会跟着向左平移，消除空隙
                current_x_offset += char_w

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
        import gc
        gc.collect()

        
                
    # 扫尾与保存工作
    if args.cv:
        cv2.destroyAllWindows()

    # 扫尾与保存工作
    if args.cv:
        cv2.destroyAllWindows()
        
    # 保存提取出的纯净文本 PDF
    if args.pure:
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
    
    # 打开源 PDF 文件
    pdf_doc = fitz.open(input_pdf_path)
    
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
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.text = ""
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

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
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True) # 去除系统窗口边框
        tw.wm_geometry("+%d+%d" % (x, y))
        
        # 【修改配色】：改为高辨识度的护眼明亮模式 (白底深灰字)
        label = tk.Label(tw, text=self.text, justify="left",
                      background="#FFFFFF", foreground="#333333", relief="solid", borderwidth=1,
                      font=("微软雅黑", 8))
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
        
        main_frame = tk.Frame(root, bg="#FFFFFF", padx=40, pady=25)
        # 【修改点1】：增加 anchor="n" 确保主框架内的组件永远置顶对齐，避免因窗口高度变化导致的内部垂直重绘（上下跳动）
        main_frame.pack(fill="both", expand=True, anchor="n")

        # 标题区
        tk.Label(main_frame, text="N E X U S  P D F - O C R   E N G I N E", font=("Arial", 22, "bold"), bg="#FFFFFF", fg="#111111").pack(pady=(0, 5))
        tk.Label(main_frame, text="智能排版分析与OCR识别覆写系统", font=("微软雅黑", 9), bg="#FFFFFF", fg="#888888").pack(pady=(0, 20))

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
        tk.Label(left_config, text="*小语种支持手动键入，参考Paddle官方识别手册", font=("微软雅黑", 8), bg="#FFFFFF", fg="#AAAAAA").pack(side="left")
        
        # --- [新增] 中间视觉分隔符 (利用 expand=True 实现动态居中悬浮) ---
        tk.Label(config_frame, text=" | ", font=("Arial", 10), bg="#FFFFFF", fg="#DDDDDD").pack(side="left", expand=True)

        # --- 2. 右侧容器：设定扫描清晰度 ---
        tk.Label(right_config, text="◧ 扫描清晰度:", font=("微软雅黑", 9, "bold"), bg="#FFFFFF", fg="#333333").pack(side="left")
        
        self.var_dpi = tk.StringVar()
        self.dpi_cb = ttk.Combobox(right_config, textvariable=self.var_dpi, font=("微软雅黑", 9), width=16)
        self.dpi_cb['values'] = [
            "150 DPI (极速)",
            "220 DPI (适中/默认)",
            "300 DPI (缓慢/高精)"
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
        
        page_toggle_box = tk.Frame(ctrl_frame, bg="#FFFFFF", cursor="hand2")
        page_toggle_box.pack(side="left")
        
        self.icon_page_lbl = tk.Label(page_toggle_box, text="□", font=("Arial", 14), bg="#FFFFFF", fg="#BBBBBB")
        self.icon_page_lbl.pack(side="left", padx=(0, 6))
        
        page_title_lbl = tk.Label(page_toggle_box, text="【可选】指定处理页码:", font=("微软雅黑", 9, "bold"), bg="#FFFFFF", fg="#333333")
        page_title_lbl.pack(side="left")
        
        self.entry_pages = tk.Entry(ctrl_frame, textvariable=self.var_pages, font=("Arial", 9), width=10, relief="solid", bd=1, state="disabled", disabledbackground="#F0F0F0")
        self.entry_pages.pack(side="left", padx=8)
        
        tk.Label(ctrl_frame, text="请先勾选，再输入绝对页码。格式: 5 或 5-10", font=("微软雅黑", 8), bg="#FFFFFF", fg="#999999").pack(side="left")

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
        tk.Label(ctrl_frame, text=" | ", font=("Arial", 10), bg="#FFFFFF", fg="#DDDDDD").pack(side="left", padx=15)

        # --- 2. 自动打开文档组件 ---
        self.var_auto_open = tk.BooleanVar(value=True) 
        
        auto_toggle_frame = tk.Frame(ctrl_frame, bg="#FFFFFF", cursor="hand2")
        auto_toggle_frame.pack(side="left")
        
        self.icon_auto_open = tk.Label(auto_toggle_frame, text="■", font=("Arial", 14), bg="#FFFFFF", fg="#00AEEF")
        self.icon_auto_open.pack(side="left", padx=(0, 4))
        
        lbl_auto_open = tk.Label(auto_toggle_frame, text="【可选】完成时自动打开文档", font=("微软雅黑", 9, "bold"), bg="#FFFFFF", fg="#333333")
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
        
        opt_frame = tk.Frame(self.opt_container, bg="#FFFFFF", highlightbackground="#EEEEEE", highlightthickness=1, padx=20, pady=15)
        opt_frame.pack(fill="both", expand=True, pady=(10, 0))
        opt_frame.columnconfigure(0, weight=1)
        opt_frame.columnconfigure(1, weight=1)

        self.var_pure = tk.BooleanVar(value=False)
        self.var_inplace = tk.BooleanVar(value=False)
        self.var_pixmap = tk.BooleanVar(value=False)
        self.var_debug = tk.BooleanVar(value=False)
        self.var_cv = tk.BooleanVar(value=False)
        self.var_no_ocr = tk.BooleanVar(value=False)
        self.var_skip_layout = tk.BooleanVar(value=False)
        
        def create_option(parent, row, col, var, title, desc):
            f = tk.Frame(parent, bg="#FFFFFF")
            f.grid(row=row, column=col, sticky="w", padx=10, pady=6)
            
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
            tk.Label(f, text=desc, font=("微软雅黑", 8), bg="#FFFFFF", fg="#999999", justify="left", wraplength=310).pack(anchor="w", padx=26)

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

        create_option(opt_frame, 0, 0, self.var_inplace, "原地覆写模式 (-I)", "直接向源 PDF 覆写文字层，建议提前备份。\n")
        create_option(opt_frame, 1, 0, self.var_pure, "纯净文本模式 (-p)", "额外生成一份剥离背景仅保留排版与文字的纯白 PDF。\n")
        create_option(opt_frame, 2, 0, self.var_debug, "色彩置信度显影 (-g)", "将识别出的文字层，以热力图的色彩烙印在画面上。\n色彩越冷，代表神经网络对该字符的置信概率越低。")

        #create_option(opt_frame, 1, 1, self.var_cv, "计算机视觉监控 (-c)", "开启 OpenCV 探针窗口，实时展现矩阵投影与滤波过程\n警告：会消耗额外的显存资源。")
        create_option(opt_frame, 0, 1, self.var_skip_layout, "关闭页边滤除 (-S)", "跳过版面分析引擎，不进行页眉页脚拦截。\n强制对全部画面进行基于大模型的OCR扫描。")
        create_option(opt_frame, 1, 1, self.var_no_ocr, "擦除矢量层 (-n)", "关闭大模型识别，仅执行简单的页面图层剥离\n用于快速擦除之前生成的错误识别结果。")
        create_option(opt_frame, 2, 1, self.var_pixmap, "光栅化页面渲染 (-P)", "强制将矢量图层合并为位图后再分析，\n对付图文损毁文档、或被恶意加密的文献。")

        # ==========================================
        # 启动后台静默模型预热序列
        # ==========================================
        self.lbl_status.config(text="System Booting: 正在后台预热神经网络，界面可正常操作...", fg="#FFA500")
        #threading.Thread(target=self._silent_preload_models, daemon=True).start()

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
            # 【修改点3】：将 fill="x" 改为 fill="both", expand=True，配合容器的舒展
            self.opt_container.pack(fill="both", expand=True)
            # 【修改点4】：将 800x800 降为安全的 800x820。避免在 125%/150% 缩放的笔记本屏幕上超出物理边界
            self.root.geometry("800x800")
            self.btn_toggle.config(text="▲ 隐藏高级干预参数 (ADVANCED OVERRIDES)")
            self.advanced_visible = True

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
            messagebox.showinfo("提示", f"在 '{folder_path.name}' 中未找到任何 PDF 文件。")
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
            messagebox.showwarning("序列错误", "引擎缺少必要的数据输入源！\n请先装载 PDF 文件。")
            return
        
        # 初始启动时的 UI 状态
        self.btn_start.config(state="disabled", text="SYSTEM INITIATING... / 正在建立神经连接", bg="#111111")
        self.btn_files.config(state="disabled")
        self.btn_dir.config(state="disabled")
        self.lbl_status.config(text="进程已锁定，正在握手...", fg="#FF5555")
        
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
      
        self.btn_start.config(state="disabled", text="PROCESSING... / 神经网络正在全速运算", bg="#CCCCCC")
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
        if "150" in dpi_str:
            target_dpi, max_pixels = 150.0, 1800.0
        elif "300" in dpi_str:
            target_dpi, max_pixels = 300.0, 3800.0
        else:
            target_dpi, max_pixels = 220.0, 2500.0

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
            page_range=self.var_pages.get()
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
                    self.root.after(0, lambda m=error_msg: messagebox.showerror("页码格式错误", f"任务已强制中止：\n\n{m}"))
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
            messagebox.showinfo("提示", "当前未设定输出目录，且未装载任何文件。")

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
        
        msg = f"分析序列已结束！\n安全处理完成 {success_count} / {total_count} 个数据包。"
        
        # 如果有被跳过的原生文件，追加具体名单
        if skipped_count > 0:
            skipped_list_str = "\n".join([f" • {name}" for name in skipped_native_files])
            msg += f"\n\n【智能滤过拦截】\n {skipped_count} 个文件被检测为【原生排版文献】且未开启页边滤除，因此被系统自动豁免，无需运行耗时识别：\n{skipped_list_str}"
        
        messagebox.showinfo("序列状态报告", msg)

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
            print(f"❌ 处理 {input_path.name} 时发生严重错误: {e}\n")
            
    print("🎉 所有任务已处理完毕！")

if hasattr(paddle.device, 'is_bfloat16_supported'):
    paddle.device.is_bfloat16_supported = lambda *args, **kwargs: False

# 再次确保禁用 DEBUG 输出
logging.disable(logging.DEBUG)

# =========================================================================
# [独立模块 4]：主路由枢纽 (Main Router)
# =========================================================================
def main():
    """
    环境嗅探引擎：根据用户启动程序的方式，智能分发执行模式。
    """
    import sys
    
    # 核心分流逻辑：如果附带了任何额外参数，说明用户是在命令行（终端）执行的，切入 CLI 模式
    if len(sys.argv) > 1:
        parsed_args = parse_arguments()
        run_cli_mode(parsed_args)
        
    # 如果没有任何参数，说明用户是直接双击了 .py 脚本运行，智能唤醒可视化 GUI
    else:
        root = tk.Tk()
        app = PDFOCRApp(root)
        root.mainloop()

if __name__ == "__main__":
    main()