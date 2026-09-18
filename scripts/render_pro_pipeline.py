#!/Users/a1-6/GPT-SoVITS/venv/bin/python
import os
import sys
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CHAR_DIR = os.path.join(ASSETS_DIR, "character")

FONT_HEITI = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_LIGHT = "/System/Library/Fonts/STHeiti Light.ttc"

WIDTH, HEIGHT = 1920, 1080
FPS = 30
TOTAL_DURATION = 20.76
TOTAL_FRAMES = int(TOTAL_DURATION * FPS)

# Subtitle timetable with natural pauses (start_frame, end_frame, text)
SUBTITLES = [
    (0, 90, "Sakura，欢迎来到我的计算机小课堂！"),
    (103, 224, "今天我们来聊聊高并发的基石：Linux 的 epoll。"),
    (238, 362, "传统 select 每次都要轮询所有连接，效率很低；"),
    (375, 525, "而 epoll 基于红黑树和就绪事件链表，通知效率直接拉满！"),
    (539, TOTAL_FRAMES, "这就是单机支撑百万并发的核心秘密哦。")
]

# ----------------- EASING FUNCTIONS (剪映经典缓动曲线) -----------------
def ease_out_cubic(t):
    t = max(0.0, min(1.0, float(t)))
    return 1.0 - (1.0 - t) ** 3

def ease_out_back(t, s=1.6):
    t = max(0.0, min(1.0, float(t)))
    t -= 1.0
    return t * t * ((s + 1.0) * t + s) + 1.0

def ease_in_out_quad(t):
    t = max(0.0, min(1.0, float(t)))
    if t < 0.5:
        return 2.0 * t * t
    return 1.0 - ((-2.0 * t + 2.0) ** 2) / 2.0

# ----------------- BACKGROUND & STATIC ASSETS -----------------
def create_grid_background():
    img = Image.new("RGB", (WIDTH, HEIGHT), (248, 250, 252))
    draw = ImageDraw.Draw(img)
    for x in range(0, WIDTH, 48):
        draw.line([(x, 0), (x, HEIGHT)], fill=(226, 232, 240), width=1)
    for y in range(0, HEIGHT, 48):
        draw.line([(0, y), (WIDTH, y)], fill=(226, 232, 240), width=1)
    return img

GRID_BG = create_grid_background()

# ----------------- SPRITE BUILDERS -----------------
def make_cover_card():
    """Left white frosted card with rounded corners and subtle shadow"""
    card = Image.new("RGBA", (1040, 850), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    # Card background
    draw.rounded_rectangle([0, 0, 1040, 850], radius=24, fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), width=2)
    return card

def make_host_card():
    """Erii host identity badge"""
    badge = Image.new("RGBA", (540, 130), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    draw.rounded_rectangle([0, 0, 540, 130], radius=20, fill=(248, 250, 252, 255), outline=(226, 232, 240, 255), width=1)
    
    avatar_path = os.path.join(CHAR_DIR, "erii_avatar.png")
    if os.path.exists(avatar_path):
        av = Image.open(avatar_path).resize((100, 100), Image.Resampling.LANCZOS)
        mask = Image.new("L", (100, 100), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 100, 100), fill=255)
        badge.paste(av, (15, 15), mask)
        
    font_name = ImageFont.truetype(FONT_HEITI, 28)
    font_sub_name = ImageFont.truetype(FONT_LIGHT, 22)
    draw.text((130, 25), "主讲：上杉绘梨衣", font=font_name, fill=(15, 23, 42))
    draw.ellipse((132, 77, 142, 87), fill=(244, 114, 182))
    draw.text((152, 70), "Sakura 的计算机小课堂", font=font_sub_name, fill=(225, 29, 72))
    return badge

def make_node_card(title, sub, bg_color, border_color, title_color, sub_color):
    """Dynamic flowchart node sprite"""
    w, h = 320, 150
    node = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(node)
    draw.rounded_rectangle([0, 0, w, h], radius=16, fill=bg_color, outline=border_color, width=2)
    
    font_t = ImageFont.truetype(FONT_HEITI, 24)
    font_s = ImageFont.truetype(FONT_LIGHT, 20)
    
    bbox_t = draw.textbbox((0, 0), title, font=font_t)
    tw = bbox_t[2] - bbox_t[0]
    draw.text(((w - tw) // 2, 35), title, font=font_t, fill=title_color)
    
    bbox_s = draw.textbbox((0, 0), sub, font=font_s)
    sw = bbox_s[2] - bbox_s[0]
    draw.text(((w - sw) // 2, 80), sub, font=font_s, fill=sub_color)
    return node

# Pre-generate sprites
SPRITE_COVER_CARD = make_cover_card()
SPRITE_HOST = make_host_card()

# Erii key visual presenter
pres_img = Image.open(os.path.join(CHAR_DIR, "erii_presenter.png"))
ph = 960
pw = int(pres_img.width * (ph / pres_img.height))
SPRITE_PRESENTER = pres_img.resize((pw, ph), Image.Resampling.LANCZOS)

# Chibi stickers
stk_think = Image.open(os.path.join(CHAR_DIR, "erii_chibi_think.png"))
SPRITE_CHIBI_THINK = stk_think.resize((390, 390), Image.Resampling.LANCZOS)

stk_happy = Image.open(os.path.join(CHAR_DIR, "erii_chibi_happy.png"))
SPRITE_CHIBI_HAPPY = stk_happy.resize((410, 410), Image.Resampling.LANCZOS)

# Code card sprite
code_img = Image.open(os.path.join(OUTPUT_DIR, "shot3_code.png"))
cw, ch = int(code_img.width * 1.3), int(code_img.height * 1.3)
SPRITE_CODE = code_img.resize((cw, ch), Image.Resampling.LANCZOS)

# 4 Architecture Nodes
NODES = [
    make_node_card("客户端并发连接", "100w Sockets", (255, 255, 255, 255), (203, 213, 225, 255), (15, 23, 42), (100, 116, 139)),
    make_node_card("内核 epoll 红黑树", "高效管理 O(log N)", (239, 246, 255, 255), (96, 165, 250, 255), (30, 58, 138), (37, 99, 235)),
    make_node_card("就绪事件双向链表", "rdlist 就绪队列", (254, 243, 199, 255), (245, 158, 11, 255), (120, 53, 15), (180, 83, 9)),
    make_node_card("epoll_wait 返回", "用户态极速处理 O(1)", (240, 253, 244, 255), (74, 222, 128, 255), (20, 83, 45), (22, 101, 52))
]

NODE_POSITIONS = [
    (100, 460),
    (480, 460),
    (860, 460),
    (1240, 460)
]

# ----------------- LAYERED FRAME COMPOSITORS -----------------
def render_shot1_frame(f):
    """Shot 1 (Frames 0 -> 226): Staggered entrances + Erii breathing idle"""
    frame = GRID_BG.copy()
    
    # 1. Card Container (Slide up with overshoot)
    card_p = ease_out_back(f / 18.0)
    card_y = int(95 + (1.0 - card_p) * 60)
    if card_p > 0:
        frame.paste(SPRITE_COVER_CARD, (120, card_y), SPRITE_COVER_CARD)
    
    draw = ImageDraw.Draw(frame)
    
    # 2. Tag Pill (Pop in)
    if f >= 10:
        tag_p = ease_out_back((f - 10) / 14.0)
        draw.rounded_rectangle([180, card_y + 60, 480, card_y + 110], radius=10, fill=(238, 242, 255), outline=(199, 210, 254), width=1)
        draw.ellipse([198, card_y + 80, 210, card_y + 92], fill=(79, 70, 229))
        font_tag = ImageFont.truetype(FONT_HEITI, 22)
        draw.text((220, card_y + 73), "LINUX 内核底层剖析", font=font_tag, fill=(79, 70, 229))
        
    # 3. Title (Slide down)
    if f >= 8:
        title_p = ease_out_cubic((f - 8) / 16.0)
        title_y = int(card_y + 145 - (1.0 - title_p) * 20)
        font_title = ImageFont.truetype(FONT_HEITI, 72)
        draw.text((180, title_y), "Linux 高并发的秘密", font=font_title, fill=(15, 23, 42))
        
    # 4. Subtitle
    if f >= 16:
        font_sub = ImageFont.truetype(FONT_HEITI, 36)
        draw.text((180, card_y + 250), "为什么 epoll 能比 select 快上百倍？", font=font_sub, fill=(71, 85, 105))
        
    # 5. Staggered Bullet Points
    bullets = [
        (40, "• 深入拆解内核红黑树管理与就绪链表机制"),
        (70, "• 从 O(n) 线性轮询到 O(1) 事件触发的底层飞跃"),
        (105, "• 核心 API 解析：轻松搞定单机百万高并发网络连接")
    ]
    font_bullet = ImageFont.truetype(FONT_LIGHT, 26)
    for idx, (b_frame, text) in enumerate(bullets):
        if f >= b_frame:
            bp = ease_out_cubic((f - b_frame) / 14.0)
            bx = int(180 - (1.0 - bp) * 35)
            by = card_y + 340 + idx * 52
            draw.text((bx, by), text, font=font_bullet, fill=(51, 65, 85))
            
    # 6. Host Card (Pop in)
    if f >= 24:
        host_p = ease_out_back((f - 24) / 16.0)
        hx = int(180 - (1.0 - host_p) * 40)
        hy = card_y + 580
        frame.paste(SPRITE_HOST, (hx, hy), SPRITE_HOST)
        
    # 7. Erii Key Visual (Slide from right + Continuous Breathing)
    pres_p = ease_out_back(f / 24.0)
    px = int(WIDTH - pw - 40 + (1.0 - pres_p) * 200)
    # Natural breathing hover (剪映循环微动效)
    py = int(HEIGHT - ph + math.sin(f / 16.0) * 8.0)
    frame.paste(SPRITE_PRESENTER, (px, py), SPRITE_PRESENTER)
    
    return frame

def render_shot2_frame(f):
    """Shot 2 (Frames 238 -> 527): Dynamic Node Growth + Particle Flow + Tilting Chibi"""
    frame = GRID_BG.copy()
    draw = ImageDraw.Draw(frame)
    local_f = f - 238
    
    # 1. Header
    font_t = ImageFont.truetype(FONT_HEITI, 46)
    font_s = ImageFont.truetype(FONT_LIGHT, 26)
    head_p = ease_out_cubic(local_f / 15.0)
    hy = int(65 - (1.0 - head_p) * 20)
    draw.text((120, hy), "一、内核机制：红黑树 + 就绪链表", font=font_t, fill=(15, 23, 42))
    draw.text((120, hy + 63), "传统 select 遍历全部 O(n)，epoll 事件触发 O(1)", font=font_s, fill=(100, 116, 139))
    
    # Node appearances timetable (local_f):
    # Node 1: f >= 4 (global 242)
    # Node 2: f >= 37 (global 275)
    # Node 3: f >= 137 (global 375, when audio says "而 epoll 基于红黑树和就绪事件链表")
    # Node 4: f >= 194 (global 432, when audio says "通知效率直接拉满")
    node_frames = [4, 37, 137, 194]
    
    # Draw Arrows & Connectors first
    for i in range(3):
        if local_f >= node_frames[i + 1]:
            x1 = NODE_POSITIONS[i][0] + 320
            x2 = NODE_POSITIONS[i + 1][0]
            y = NODE_POSITIONS[i][1] + 75
            # Draw line
            draw.line([(x1 + 10, y), (x2 - 10, y)], fill=(148, 163, 184), width=3)
            # Arrowhead
            draw.polygon([(x2 - 10, y), (x2 - 20, y - 6), (x2 - 20, y + 6)], fill=(148, 163, 184))
            
    # Draw Nodes with pop-in scale
    for i in range(4):
        if local_f >= node_frames[i]:
            np_val = ease_out_back((local_f - node_frames[i]) / 14.0)
            base_node = NODES[i]
            bx, by = NODE_POSITIONS[i]
            
            # Active pulse on Node 3 and Node 4
            if i == 2 and local_f >= node_frames[2]:
                pulse = 1.0 + 0.03 * math.sin((local_f - node_frames[2]) / 8.0)
            elif i == 3 and local_f >= node_frames[3]:
                pulse = 1.0 + 0.03 * math.sin((local_f - node_frames[3]) / 8.0)
            else:
                pulse = 1.0
                
            scale = np_val * pulse
            if scale > 0.02:
                if abs(scale - 1.0) > 0.01:
                    nw = max(1, int(320 * scale))
                    nh = max(1, int(150 * scale))
                    scaled_node = base_node.resize((nw, nh), Image.Resampling.BILINEAR)
                    frame.paste(scaled_node, (bx - (nw - 320) // 2, by - (nh - 150) // 2), scaled_node)
                else:
                    frame.paste(base_node, (bx, by), base_node)
                
    # Dynamic Data Packet Particle moving across arrows
    if local_f >= node_frames[1]:
        # Particle loop every 75 frames (2.5s)
        cycle = local_f % 75
        prog = cycle / 75.0
        start_x = NODE_POSITIONS[0][0] + 320
        end_x = NODE_POSITIONS[3][0]
        curr_x = start_x + (end_x - start_x) * prog
        cy = NODE_POSITIONS[0][1] + 75
        # Glowing particle
        draw.ellipse([curr_x - 8, cy - 8, curr_x + 8, cy + 8], fill=(59, 130, 246, 200))
        draw.ellipse([curr_x - 4, cy - 4, curr_x + 4, cy + 4], fill=(255, 255, 255, 255))
        
    # Erii Thinking Sticker (Bounces in, gentle tilting head & hover)
    if local_f >= 12:
        stk_p = ease_out_back((local_f - 12) / 16.0)
        angle = math.sin(local_f / 12.0) * 3.5
        hover_y = math.sin(local_f / 16.0) * 6.0
        
        # Rotate sticker slightly
        rotated = SPRITE_CHIBI_THINK.rotate(angle, resample=Image.Resampling.BILINEAR, expand=True)
        rx = int(WIDTH - 430 + (1.0 - stk_p) * 80)
        ry = int(HEIGHT - 460 + hover_y)
        frame.paste(rotated, (rx, ry), rotated)
        
    return frame

def render_shot3_frame(f):
    """Shot 3 (Frames 539 -> 622): Code Card Entrance + Spotlight + Chibi Happy Hop"""
    frame = GRID_BG.copy()
    draw = ImageDraw.Draw(frame)
    local_f = f - 539
    
    # 1. Header
    font_t = ImageFont.truetype(FONT_HEITI, 46)
    font_s = ImageFont.truetype(FONT_LIGHT, 26)
    head_p = ease_out_cubic(local_f / 12.0)
    hy = int(65 - (1.0 - head_p) * 20)
    draw.text((120, hy), "二、核心 API：epoll_create 与 epoll_wait", font=font_t, fill=(15, 23, 42))
    draw.text((120, hy + 63), "事件发生内核直接唤醒用户态，单机轻松支撑百万并发", font=font_s, fill=(100, 116, 139))
    
    # 2. Code Card (Spring Pop)
    cp = ease_out_back(local_f / 14.0)
    scale = 0.9 + 0.1 * cp
    cx = 120
    cy = (HEIGHT - ch) // 2 + 25
    frame.paste(SPRITE_CODE, (cx, cy), SPRITE_CODE)
    
    # 3. Dynamic Spotlight Highlight Box over Line 10 (epoll_wait)
    # Pulse animation
    pulse_alpha = int(120 + 40 * math.sin(local_f / 5.0))
    # Code card overlay highlight at Line 10 (y offset inside card)
    hl_y1 = cy + int(ch * 0.82)
    hl_y2 = hl_y1 + 42
    hl_x1 = cx + 50
    hl_x2 = cx + cw - 60
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    draw_ov.rounded_rectangle([hl_x1, hl_y1, hl_x2, hl_y2], radius=8, fill=(254, 240, 138, pulse_alpha), outline=(234, 179, 8, pulse_alpha), width=2)
    frame = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")
    
    # 4. Erii Happy Sticker (Excited Bouncing Hop)
    hp = ease_out_back(local_f / 14.0)
    # Happy hopping motion: jump up and down
    hop_y = -abs(math.sin(local_f / 6.0)) * 14.0
    hx = int(WIDTH - 450 + (1.0 - hp) * 80)
    hy = int(HEIGHT - 470 + hop_y)
    frame.paste(SPRITE_CHIBI_HAPPY, (hx, hy), SPRITE_CHIBI_HAPPY)
    
    return frame

# ----------------- SUBTITLE RENDERING -----------------
def render_light_subtitle(frame, text, alpha, pop_progress=1.0, center_x=None):
    """Dynamic pop-in white frosted subtitle capsule"""
    if not text or alpha <= 0:
        return frame
    
    font = ImageFont.truetype(FONT_HEITI, 32)
    dummy = ImageDraw.Draw(frame)
    bbox = dummy.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    pad_x = 36
    pad_y = 16
    pill_w = tw + pad_x * 2
    pill_h = th + pad_y * 2
    
    if center_x is not None:
        x = int(center_x - pill_w // 2)
    else:
        x = (WIDTH - pill_w) // 2
    # Pop-up animation offset (12px up)
    y_offset = (1.0 - pop_progress) * 12.0
    y = int(HEIGHT - 110 + y_offset)
    
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    
    # Soft drop shadow
    draw_ov.rounded_rectangle(
        [x, y + 4, x + pill_w, y + pill_h + 4],
        radius=pill_h // 2,
        fill=(100, 116, 139, int(35 * alpha))
    )
    
    # Pure white frosted floating capsule
    draw_ov.rounded_rectangle(
        [x, y, x + pill_w, y + pill_h],
        radius=pill_h // 2,
        fill=(255, 255, 255, int(250 * alpha)),
        outline=(203, 213, 225, int(240 * alpha)),
        width=2
    )
    
    # High-contrast dark slate text
    draw_ov.text((x + pad_x, y + pad_y - 2), text, font=font, fill=(15, 23, 42, int(255 * alpha)))
    return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")

def get_current_subtitle(frame_idx):
    for start, end, text in SUBTITLES:
        if start <= frame_idx < end:
            dist_start = frame_idx - start
            dist_end = end - frame_idx
            alpha = min(1.0, dist_start / 5.0, dist_end / 5.0)
            pop_p = ease_out_back(min(1.0, dist_start / 8.0))
            return text, alpha, pop_p
    return None, 0.0, 1.0

# ----------------- MAIN PIPELINE -----------------
def main():
    print("🎬 启动剪映级多图层动效渲染引擎...")
    
    audio_path = os.path.join(OUTPUT_DIR, "voice_with_sfx.wav")
    bgm_path = os.path.join(ASSETS_DIR, "bgm.mp3")
    final_output = os.path.join(OUTPUT_DIR, "epoll_pro_demo.mp4")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS),
        "-i", "-",
        "-i", audio_path,
        "-i", bgm_path,
        "-filter_complex",
        "[1:a]volume=1.0[voice];[2:a]volume=0.10,afade=t=in:ss=0:d=1.5,afade=t=out:st=18.5:d=2.0[bgm];[voice][bgm]amix=inputs=2:duration=first[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        final_output
    ]
    
    pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    TRANSITION_LEN = 12
    
    for i in range(TOTAL_FRAMES):
        if i < 226:
            # Shot 1
            frame = render_shot1_frame(i)
        elif i < 238:
            # Transition 1: Push transition during speech pause
            t_p = ease_in_out_quad((i - 226) / float(TRANSITION_LEN))
            f1 = render_shot1_frame(225)
            f2 = render_shot2_frame(238)
            
            # Smooth slide push
            offset_x = int(t_p * WIDTH)
            frame = Image.new("RGB", (WIDTH, HEIGHT))
            frame.paste(f1, (-offset_x, 0))
            frame.paste(f2, (WIDTH - offset_x, 0))
        elif i < 527:
            # Shot 2
            frame = render_shot2_frame(i)
        elif i < 539:
            # Transition 2: Push transition during speech pause
            t_p = ease_in_out_quad((i - 527) / float(TRANSITION_LEN))
            f2 = render_shot2_frame(526)
            f3 = render_shot3_frame(539)
            
            offset_x = int(t_p * WIDTH)
            frame = Image.new("RGB", (WIDTH, HEIGHT))
            frame.paste(f2, (-offset_x, 0))
            frame.paste(f3, (WIDTH - offset_x, 0))
        else:
            # Shot 3
            frame = render_shot3_frame(i)
            
        # Overlay Subtitle
        sub_text, sub_alpha, pop_p = get_current_subtitle(i)
        if sub_text:
            cx = 640 if i < 226 else None
            frame = render_light_subtitle(frame, sub_text, sub_alpha, pop_p, center_x=cx)
            
        pipe.stdin.write(frame.tobytes())
        if i % 90 == 0:
            print(f"  ⚡ 动效渲染进度: {round(i / TOTAL_FRAMES * 100)}% ...")
            
    pipe.stdin.close()
    pipe.wait()
    print(f"🎉 剪映级全动效新片渲染完成: {final_output}")

if __name__ == "__main__":
    main()
