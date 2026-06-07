#!/usr/bin/env python3
"""
微信公众号封面图生成器
根据文章关键词自动生成品牌封面，支持多种主题风格
"""

import textwrap
import random
import os
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import urllib.request
import io

# 封面尺寸（微信公众号标准）
WIDTH = 900
HEIGHT = 383

# 品牌色系
COLORS = {
    'bg_dark': (10, 14, 23),           # 深蓝黑背景
    'bg_gradient_top': (20, 30, 60),    # 渐变顶部
    'primary': (59, 130, 246),          # 科技蓝
    'secondary': (139, 92, 246),        # 紫色
    'accent': (34, 211, 238),           # 青色
    'gold': (251, 191, 36),            # 金色
    'red': (239, 68, 68),              # 红色
    'green': (52, 211, 153),           # 绿色
    'text': (255, 255, 255),           # 白色文字
    'text_dim': (148, 163, 184),       # 暗淡文字
    'brand': (59, 130, 246),           # 品牌色
}

# 主题配置
THEMES = {
    'trading_agents': {
        'keywords': ['trading', 'agent', '量化', '交易', 'finance', 'stock'],
        'gradient': [(10, 14, 23), (20, 40, 80), (10, 14, 23)],
        'elements': [
            {'type': 'chart', 'x': 650, 'y': 50, 'w': 220, 'h': 130, 'color': (52, 211, 153)},
            {'type': 'chart', 'x': 680, 'y': 100, 'w': 180, 'h': 80, 'color': (239, 68, 68)},
            {'type': 'node', 'x': 750, 'y': 250, 'r': 25, 'color': COLORS['primary']},
            {'type': 'node', 'x': 680, 'y': 300, 'r': 20, 'color': COLORS['secondary']},
            {'type': 'node', 'x': 820, 'y': 300, 'r': 20, 'color': COLORS['accent']},
            {'type': 'line', 'x1': 750, 'y1': 275, 'x2': 700, 'y2': 280, 'color': COLORS['text_dim']},
            {'type': 'line', 'x1': 750, 'y1': 275, 'x2': 800, 'y2': 280, 'color': COLORS['text_dim']},
        ],
        'badge': 'AI AGENTS',
        'badge_color': COLORS['gold'],
    },
    'ai_news': {
        'keywords': ['ai', '大模型', 'llm', 'gpt', 'claude', 'deepseek', '苹果', 'apple'],
        'gradient': [(15, 15, 30), (30, 20, 60), (15, 15, 30)],
        'elements': [
            {'type': 'grid', 'x': 600, 'y': 30, 'w': 280, 'h': 200, 'color': COLORS['secondary']},
            {'type': 'glow', 'x': 740, 'y': 130, 'r': 60, 'color': COLORS['accent']},
        ],
        'badge': 'AI',
        'badge_color': COLORS['accent'],
    },
    'open_source': {
        'keywords': ['开源', 'open source', 'github', 'star', 'fork'],
        'gradient': [(20, 14, 10), (40, 25, 15), (20, 14, 10)],
        'elements': [
            {'type': 'hex', 'x': 700, 'y': 120, 'size': 50, 'color': (255, 165, 0)},
            {'type': 'hex', 'x': 780, 'y': 180, 'size': 40, 'color': (255, 200, 0)},
            {'type': 'hex', 'x': 640, 'y': 200, 'size': 35, 'color': (255, 140, 0)},
        ],
        'badge': 'OPEN SOURCE',
        'badge_color': (255, 165, 0),
    },
    'hardware': {
        'keywords': ['芯片', 'gpu', 'nvidia', '硬件', 'cpu', '硬件'],
        'gradient': [(14, 20, 14), (20, 40, 20), (14, 20, 14)],
        'elements': [
            {'type': 'chip', 'x': 720, 'y': 120, 'size': 80, 'color': COLORS['green']},
        ],
        'badge': 'HARDWARE',
        'badge_color': COLORS['green'],
    },
    'coding': {
        'keywords': ['编程', 'code', 'python', 'javascript', 'rust', '程序员'],
        'gradient': [(14, 20, 30), (20, 35, 50), (14, 20, 30)],
        'elements': [
            {'type': 'terminal', 'x': 650, 'y': 60, 'w': 230, 'h': 180, 'color': (34, 211, 238)},
            {'type': 'cursor', 'x': 670, 'y': 100, 'w': 60, 'h': 8, 'color': COLORS['accent']},
        ],
        'badge': 'CODING',
        'badge_color': COLORS['accent'],
    },
    'default': {
        'keywords': [],
        'gradient': [(15, 15, 35), (25, 25, 65), (15, 15, 35)],
        'elements': [],
        'badge': 'TECH',
        'badge_color': COLORS['primary'],
    }
}


def detect_theme(title: str, content: str = '') -> dict:
    """根据标题和内容检测主题"""
    text = (title + ' ' + content).lower()
    for theme_name, config in THEMES.items():
        if theme_name == 'default':
            continue
        for kw in config['keywords']:
            if kw.lower() in text:
                return THEMES[theme_name]
    return THEMES['default']


def create_gradient_background(draw, colors, direction='horizontal'):
    """创建渐变背景"""
    for i in range(HEIGHT):
        ratio = i / HEIGHT
        r = int(colors[0][0] * (1 - ratio) + colors[2][0] * ratio)
        g = int(colors[0][1] * (1 - ratio) + colors[2][1] * ratio)
        b = int(colors[0][2] * (1 - ratio) + colors[2][2] * ratio)
        draw.line([(0, i), (WIDTH, i)], fill=(r, g, b))


def draw_grid_pattern(draw, x, y, w, h, color, alpha=40):
    """绘制科技感网格"""
    for i in range(0, w, 20):
        draw.line([(x+i, y), (x+i, y+h)], fill=color + (alpha,), width=1)
    for j in range(0, h, 20):
        draw.line([(x, y+j), (x+w, y+j)], fill=color + (alpha,), width=1)


def draw_glowing_circle(draw, x, y, r, color):
    """绘制发光圆点"""
    for i in range(r, 0, -2):
        alpha = int(255 * (1 - i/r) * 0.3)
        draw.ellipse([x-i, y-i, x+i, y+i], fill=color + (alpha,))


def draw_chart(draw, x, y, w, h, color, chart_type='line'):
    """绘制K线/折线图"""
    import random
    random.seed(x + y)
    points_up = [(x + i * w//5, y + h - random.randint(10, h-10)) for i in range(6)]
    points_down = [(x + i * w//5, y + h - random.randint(10, h-10)) for i in range(6)]

    for i in range(len(points_up)-1):
        alpha = 150
        c = (52, 211, 153)
        draw.line([points_up[i], points_up[i+1]], fill=c + (alpha,), width=2)
    for i in range(len(points_down)-1):
        draw.line([points_down[i], points_down[i+1]], fill=(239, 68, 68) + (150,), width=2)


def draw_terminal_window(draw, x, y, w, h, color):
    """绘制终端窗口"""
    draw.rectangle([x, y, x+w, y+h], outline=color + (100,), width=2)
    draw.rectangle([x, y, x+w, y+20], fill=color + (30,))
    for i in range(3):
        cx = x + 12 + i * 18
        draw.ellipse([cx-4, y+8, cx+4, y+16], fill=(239, 68, 68) + (200,))
        draw.ellipse([cx+14, y+8, cx+22, y+16], fill=(251, 191, 36) + (200,))
        draw.ellipse([cx+28, y+8, cx+36, y+16], fill=(52, 211, 153) + (200,))


def draw_hexagon(draw, cx, cy, size, color):
    """绘制六边形"""
    points = []
    for i in range(6):
        angle = 3.14159 / 180 * (60 * i - 30)
        points.append((cx + size * 0.9 * (0.5 + 0.5 * 0.5 * (1 + 0.5)),
                       cy + size * 0.9 * (0.5 + 0.5 * 0.866 * (1 - 0.5))))
    points2 = [(cx + size * 0.7 * (0.5 + 0.5 * 0.5 * (1 + 0.5)),
                cy + size * 0.7 * (0.5 + 0.5 * 0.866 * (1 - 0.5))) for i in range(6)]
    draw.polygon([(p[0], p[1]) for p in points], outline=color + (200,), width=2)


def draw_chip(draw, x, y, size, color):
    """绘制芯片图标"""
    draw.rectangle([x-size//2, y-size//2, x+size//2, y+size//2], outline=color + (200,), width=2)
    draw.rectangle([x-size//4, y-size//4, x+size//4, y+size//4], fill=color + (50,))
    for i in range(-2, 3):
        if i == 0: continue
        draw.line([(x + i*size//3, y-size//2), (x + i*size//3, y-size//2-10)], fill=color + (150,), width=2)
        draw.line([(x + i*size//3, y+size//2), (x + i*size//3, y+size//2+10)], fill=color + (150,), width=2)


def draw_elements(draw, elements):
    """绘制装饰元素"""
    for el in elements:
        t = el['type']
        if t == 'grid':
            draw_grid_pattern(draw, el['x'], el['y'], el['w'], el['h'], COLORS[el.get('color_name', 'text_dim')])
        elif t == 'glow':
            draw_glowing_circle(draw, el['x'], el['y'], el['r'], el['color'])
        elif t == 'chart':
            draw_chart(draw, el['x'], el['y'], el['w'], el['h'], el['color'])
        elif t == 'terminal':
            draw_terminal_window(draw, el['x'], el['y'], el['w'], el['h'], el['color'])
        elif t == 'hex':
            draw_hexagon(draw, el['x'], el['y'], el['size'], el['color'])
        elif t == 'chip':
            draw_chip(draw, el['x'], el['y'], el['size'], el['color'])
        elif t == 'node':
            draw_glowing_circle(draw, el['x'], el['y'], el['r'], el['color'])


def wrap_text(text, font, max_width):
    """智能换行"""
    chars = list(text)
    lines = []
    current = ''
    for char in chars:
        test = current + char
        if font.getlength(test) > max_width:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def draw_title_text(draw, title, font_path=None):
    """绘制标题文字"""
    try:
        if font_path and os.path.exists(font_path):
            title_font = ImageFont.truetype(font_path, 36)
            subtitle_font = ImageFont.truetype(font_path, 20)
        else:
            title_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 36)
            subtitle_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    lines = wrap_text(title, title_font, WIDTH - 80)
    y = HEIGHT // 2 - (len(lines) * 40) // 2
    for line in lines[:3]:
        draw.text((40, y), line, font=title_font, fill=COLORS['text'])
        y += 45

    return len(lines) * 45


def draw_badge(draw, text, color, x=None, y=30):
    """绘制角标"""
    try:
        badge_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14)
    except:
        badge_font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=badge_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = x or WIDTH - tw - 50

    draw.rounded_rectangle([x-10, y-5, x+tw+10, y+th+10], radius=4, fill=color + (30,))
    draw.text((x, y), text, font=badge_font, fill=color)


def draw_brand(draw):
    """绘制品牌标识"""
    try:
        brand_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    except:
        brand_font = ImageFont.load_default()

    brand_text = 'Python工作圈'
    bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = 40
    y = HEIGHT - th - 25

    draw.rounded_rectangle([x-8, y-4, x+tw+8, y+th+8], radius=3, fill=COLORS['brand'] + (40,))
    draw.text((x, y), brand_text, font=brand_font, fill=COLORS['brand'])


def draw_decorative_lines(draw):
    """绘制装饰线条"""
    draw.line([(40, HEIGHT//2 - 30), (40, HEIGHT//2 + 60)], fill=COLORS['primary'], width=3)
    draw.line([(45, HEIGHT//2 - 30), (45, HEIGHT//2 + 60)], fill=COLORS['secondary'], width=2)


def generate_cover(title: str, output_path: str, theme_config: dict = None) -> str:
    """生成封面图"""
    img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if theme_config is None:
        theme_config = detect_theme(title)

    create_gradient_background(draw, theme_config['gradient'])
    draw_elements(draw, theme_config['elements'])
    draw_decorative_lines(draw)
    draw_title_text(draw, title)
    draw_badge(draw, theme_config['badge'], theme_config['badge_color'])
    draw_brand(draw)

    img.save(output_path, 'PNG', quality=95)
    return output_path


def get_cover_from_url(url: str, output_path: str) -> str:
    """从URL下载封面图"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            img_data = resp.read()
        img = Image.open(io.BytesIO(img_data))
        img = img.convert('RGBA')
        img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
        img.save(output_path, 'PNG', quality=95)
        return output_path
    except Exception as e:
        print(f'下载封面失败: {e}')
        return None


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('用法: python 封面生成器.py <文章标题> [输出路径]')
        sys.exit(1)

    title = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else '/tmp/cover.png'

    theme = detect_theme(title)
    print(f'检测到主题: {theme["badge"]}')

    path = generate_cover(title, output, theme)
    print(f'封面已生成: {path}')
