import base64
import colorsys
import io
import random
import string
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

# 输出尺寸与超采样倍数：先在 3 倍分辨率上绘制，再 LANCZOS 降采样，得到抗锯齿的圆润笔画
WIDTH, HEIGHT = 160, 48
SS = 3


def _quad_bezier(
    p0: Tuple[float, float], p1: Tuple[float, float], p2: Tuple[float, float], n: int = 48
) -> List[Tuple[float, float]]:
    """二次贝塞尔曲线取 n 个采样点，用于画平滑弧线。"""
    pts: List[Tuple[float, float]] = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
        pts.append((x, y))
    return pts


class CaptchaTool:
    """
    生成图片验证码。

    视觉设计：柔和浅色纸底（随机色相）+ 同色系深色粗体数字，
    每个字符独立小画布旋转后合成，配少量平滑弧线与细噪点。
    全程使用 Pillow 自带的可缩放字体（load_default(size=...)），
    不依赖系统字体，容器内行为一致。
    """

    def __init__(self, width: int = WIDTH, height: int = HEIGHT) -> None:
        self.width = width
        self.height = height
        # 每次实例化随机一个基础色相，保证整张图色调统一
        self.hue = random.random()

    # ---- 配色：同一色相下取不同明度的层（背景浅、字符深、弧线居中） ----

    def _bg_color(self) -> Tuple[int, int, int]:
        r, g, b = colorsys.hls_to_rgb(self.hue, 0.95, 0.25)
        return (int(r * 255), int(g * 255), int(b * 255))

    def _text_color(self) -> Tuple[int, int, int]:
        # 明度压到 0.20-0.28，与浅底(0.95)保持足够亮度差；再用感知亮度钳制兜底——
        # 黄/绿等色相在同等 HSL 明度下视觉偏亮，按相对亮度等比压暗，杜绝同色系低对比
        r, g, b = colorsys.hls_to_rgb(self.hue, random.uniform(0.20, 0.28), 0.65)
        luma = 0.299 * r + 0.587 * g + 0.114 * b
        if luma > 0.33:
            scale = 0.33 / luma
            r, g, b = r * scale, g * scale, b * scale
        return (int(r * 255), int(g * 255), int(b * 255))

    def _line_color(self) -> Tuple[int, int, int]:
        r, g, b = colorsys.hls_to_rgb(self.hue, random.uniform(0.60, 0.72), 0.45)
        return (int(r * 255), int(g * 255), int(b * 255))

    def _draw_char(self, ch: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont) -> Image.Image:
        """单字符画到独立 RGBA 层并随机旋转 ±20°，返回带透明背景的字符图。"""
        bbox = font.getbbox(ch)
        pad = 8 * SS
        size = (int(bbox[2] - bbox[0]) + pad * 2, int(bbox[3] - bbox[1]) + pad * 2)
        layer = Image.new("RGBA", size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.text((pad - bbox[0], pad - bbox[1]), ch, font=font, fill=self._text_color() + (255,))
        return layer.rotate(random.uniform(-25, 25), resample=Image.Resampling.BICUBIC, expand=True)

    def get_verify_code(self) -> Tuple[bytes, str]:
        """
        生成验证码图形，返回 (data URI, code)。
        """
        code = "".join(random.sample(string.digits, 4))

        # 超采样画布
        w, h = self.width * SS, self.height * SS
        canvas = Image.new("RGBA", (w, h), self._bg_color() + (255,))
        draw = ImageDraw.Draw(canvas)

        # 平滑弧线：2 条贯穿画面的贝塞尔曲线，宽笔画低对比
        for _ in range(2):
            p0 = (0, random.uniform(0.2, 0.8) * h)
            p2 = (w, random.uniform(0.2, 0.8) * h)
            p1 = (random.uniform(0.3, 0.7) * w, random.uniform(-0.1, 1.1) * h)
            draw.line(_quad_bezier(p0, p1, p2), fill=self._line_color() + (160,), width=2 * SS, joint="curve")

        # 字符：Pillow 自带可缩放字体，粗细随机取两档
        font = ImageFont.load_default(size=random.choice([30, 34]) * SS)
        slot = w / (len(code) + 0.6)
        for i, ch in enumerate(code):
            layer = self._draw_char(ch, font)
            # 字符轻微缩放 + 更大的位移扰动，打破等距等大的规整感
            scale = random.uniform(0.92, 1.08)
            layer = layer.resize(
                (max(1, int(layer.width * scale)), max(1, int(layer.height * scale))),
                Image.Resampling.LANCZOS,
            )
            x = int(slot * (i + 0.3) + random.uniform(-6, 6) * SS)
            y = int((h - layer.height) / 2 + random.uniform(-5, 5) * SS)
            canvas.alpha_composite(layer, (x, y))

        # 细噪点
        for _ in range(28):
            nx, ny = random.uniform(0, w), random.uniform(0, h)
            nr = random.uniform(0.6, 1.6) * SS
            draw.ellipse((nx - nr, ny - nr, nx + nr, ny + nr), fill=self._line_color() + (90,))

        # 降采样抗锯齿并导出（PNG 无损，data URI 与真实格式一致）
        img = canvas.resize((self.width, self.height), Image.Resampling.LANCZOS).convert("RGB")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return b"data:image/png;base64," + base64.b64encode(buffered.getvalue()), code
