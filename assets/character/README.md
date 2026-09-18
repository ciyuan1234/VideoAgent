# 🌸 上杉绘梨衣 (Uesugi Erii) 专属角色素材库

本目录存放视频管线专属的**上杉绘梨衣**高保真立绘与贴纸表情包，支持在各类视频封面、分镜卡片、头像气泡与互动转场中多次复用。

所有素材均提供两种格式：
- `.png`：**已透明抠图**，具备完美 Alpha 透明通道，可直接叠加在任何背景（白色格子、深色卡片、渐变壁纸）上。
- `.jpg`：原始高分辨率原图。

---

## 🎨 素材清单与应用场景

| 文件名 | 分辨率 | 类别 | 推荐应用场景 |
| :--- | :--- | :--- | :--- |
| **`erii_presenter.png`** | 896 × 1200 | 优雅主讲人立绘 (Key Visual) | **视频封面大图 / 开场主讲人亮相**。<br>身着现代红白巫女风短裙，右手优雅手势指引画面，头戴小黄鸭发夹。纯净无文字与LOGO。 |
| **`erii_avatar.png`** | 1024 × 1024 | 圆形头像 / 特写立绘 (Portrait) | **左下角主讲人名片 / 评论区置顶头像 / 视频角标**。<br>樱花发饰与纯净温暖微笑，适合作为官方 Channel 头像。 |
| **`erii_chibi_happy.png`** | 1024 × 1024 | Q版开心表情包 (Sticker) | **代码讲解 / 难点解析完成 / 知识点总结**。<br>双手举着空白螺旋笔记本，头顶憨态可掬的经典小黄鸭。 |
| **`erii_chibi_think.png`** | 1024 × 1024 | Q版思考表情包 (Sticker) | **问题引出 / 对比分析（如 select 缺点） / 悬念设置**。<br>歪头托腮沉思，漂浮问号与好奇小黄鸭。 |
| **`erii_chibi_cheer.png`** | 1024 × 1024 | Q版欢呼挥手表情包 (Sticker) | **视频结尾致谢 / 催三连关注 / 欢迎片头**。<br>手持粉色小黄鸭掌机，挥手致意，四周伴随樱花瓣与星光。 |

---

## 💡 Python 代码调用示例

```python
from PIL import Image

# 1. 加载带透明通道的表情贴纸
chibi = Image.open("assets/character/erii_chibi_happy.png")
chibi_resized = chibi.resize((400, 400), Image.Resampling.LANCZOS)

# 2. 贴入底板（利用 alpha 通道遮罩保持背景透明）
base_frame.paste(chibi_resized, (x, y), chibi_resized)
```
