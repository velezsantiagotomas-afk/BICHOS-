"""Borra el ventilador negro de la pared: detecta la mancha oscura grande en la parte
de arriba de la imagen y la rellena con el color de la pared (inpainting)."""
import cv2, numpy as np


def remove_fan(rgb, ymax_frac=0.5, min_area_frac=0.004, top_frac=0.22, dark=95, sat=110, dil=0.012, touch_top=True):
    h, w = rgb.shape[:2]
    s = 540 / w                                     # trabajar en baja resolución (rápido)
    small = cv2.resize(rgb, (540, int(h * s)), interpolation=cv2.INTER_AREA)
    sh, sw = small.shape[:2]
    hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
    m = ((hsv[..., 2] < dark) & (hsv[..., 1] < sat)).astype(np.uint8)
    m[int(sh * ymax_frac):] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area >= min_area_frac * sw * sh and y <= top_frac * sh and (not touch_top or y <= 2):
            keep[lab == i] = 1
    if not keep.any():
        return rgb, keep
    k = max(3, int(dil * sw) | 1)
    keep = cv2.dilate(keep, np.ones((k, k), np.uint8))
    # relleno con un plano de color de pared (sin arrastrar colores de las bolsas)
    wall = (hsv[..., 2] > 140) & (hsv[..., 1] > 20) & (hsv[..., 1] < 110) & (hsv[..., 0] > 8) & (hsv[..., 0] < 30) & (keep == 0)
    wall[int(sh * ymax_frac):] = False
    ys, xs = np.nonzero(wall)
    A = np.stack([np.ones_like(xs), xs, ys], 1).astype(np.float32)
    filled = small.copy().astype(np.float32)
    yy, xx = np.mgrid[0:sh, 0:sw]
    for c in range(3):
        coef, *_ = np.linalg.lstsq(A, small[ys, xs, c].astype(np.float32), rcond=None)
        filled[..., c] = coef[0] + coef[1] * xx + coef[2] * yy
    noise = np.random.default_rng(0).normal(0, 1.2, filled.shape)
    filled = np.clip(filled + noise, 0, 255).astype(np.uint8)
    big = cv2.resize(filled, (w, h), interpolation=cv2.INTER_LINEAR)
    mk = cv2.resize(keep.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
    mk = cv2.GaussianBlur(mk, (0, 0), 3 * w / 540)[..., None]
    out = (rgb * (1 - mk) + big * mk).astype(np.uint8)
    return out, keep
