"""Small presentation widgets used by the polished application shell."""

from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class HeroBanner(QWidget):
    """Responsive, theme-aware banner with live text over supplied artwork."""

    def __init__(self, artwork_path: str, parent=None):
        super().__init__(parent)
        self._artwork = QPixmap(str(Path(artwork_path)))
        self._theme_name = "aurora"
        self.setObjectName("heroBanner")
        self.setMinimumHeight(184)
        self.setMaximumHeight(218)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setAccessibleName("Audiobook Maker welcome banner")

    def set_theme(self, theme_name: str):
        self._theme_name = theme_name
        self.update()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform
        )

        card = QRectF(self.rect()).adjusted(1.0, 1.0, -1.0, -1.0)
        clip_path = QPainterPath()
        clip_path.addRoundedRect(card, 24.0, 24.0)
        painter.setClipPath(clip_path)

        if not self._artwork.isNull():
            source = self._source_crop(card)
            painter.drawPixmap(card, self._artwork, source)
        else:
            fallback = QLinearGradient(card.topLeft(), card.bottomRight())
            fallback.setColorAt(0.0, QColor("#DDF9FF"))
            fallback.setColorAt(1.0, QColor("#E7DFFF"))
            painter.fillRect(card, fallback)

        self._paint_readability_overlay(painter, card)
        self._paint_copy(painter, card)

        painter.setClipping(False)
        border = QColor("#B8EAF1") if self._theme_name == "aurora" else QColor("#736AA8")
        border.setAlpha(175)
        painter.setPen(QPen(border, 1.25))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(card, 24.0, 24.0)

    def _source_crop(self, target: QRectF) -> QRectF:
        """Crop the wide art around the character's face without stretching it."""
        pix_w = float(self._artwork.width())
        pix_h = float(self._artwork.height())
        target_ratio = max(target.width() / max(target.height(), 1.0), 1.0)
        source_h = min(pix_h, pix_w / target_ratio)
        # The generated composition keeps the character's face in the upper-right.
        # Keep the eyes and smile centered even when the banner becomes very wide.
        source_y = 310.0 - (source_h * 0.45)
        source_y = min(max(24.0, source_y), max(0.0, pix_h - source_h))
        return QRectF(0.0, source_y, pix_w, source_h)

    def _paint_readability_overlay(self, painter: QPainter, card: QRectF):
        overlay = QLinearGradient(card.left(), card.top(), card.left() + card.width() * 0.72, card.top())
        if self._theme_name == "midnight":
            overlay.setColorAt(0.0, QColor(24, 22, 51, 244))
            overlay.setColorAt(0.62, QColor(27, 25, 57, 214))
            overlay.setColorAt(1.0, QColor(27, 25, 57, 0))
        else:
            overlay.setColorAt(0.0, QColor(241, 253, 255, 247))
            overlay.setColorAt(0.62, QColor(239, 246, 255, 205))
            overlay.setColorAt(1.0, QColor(239, 246, 255, 0))
        painter.fillRect(card, overlay)

    def _paint_copy(self, painter: QPainter, card: QRectF):
        dark = self._theme_name == "midnight"
        title_color = QColor("#F8F6FF") if dark else QColor("#243153")
        body_color = QColor("#C8C5E8") if dark else QColor("#536383")
        pill_fill = QColor(117, 214, 240, 45) if dark else QColor(255, 255, 255, 185)
        pill_border = QColor("#746EA9") if dark else QColor("#BCEAF1")

        left = card.left() + 30.0
        top = card.top() + 25.0
        pill = QRectF(left, top, 146.0, 27.0)
        painter.setPen(QPen(pill_border, 1.0))
        painter.setBrush(pill_fill)
        painter.drawRoundedRect(pill, 13.5, 13.5)

        badge_font = QFont("Segoe UI", 8)
        badge_font.setWeight(QFont.DemiBold)
        badge_font.setLetterSpacing(QFont.AbsoluteSpacing, 0.8)
        painter.setFont(badge_font)
        painter.setPen(QColor("#3C91A7") if not dark else QColor("#8CDDEC"))
        painter.drawText(pill, Qt.AlignCenter, "LOCAL VOICE STUDIO")

        title_font = QFont("Segoe UI", 22)
        title_font.setWeight(QFont.Bold)
        painter.setFont(title_font)
        painter.setPen(title_color)
        title_rect = QRectF(left, top + 38.0, card.width() * 0.52, 39.0)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, "Give every page a voice")

        body_font = QFont("Segoe UI", 10)
        body_font.setWeight(QFont.Medium)
        painter.setFont(body_font)
        painter.setPen(body_color)
        body_rect = QRectF(left, top + 82.0, card.width() * 0.48, 46.0)
        painter.drawText(
            body_rect,
            Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
            "Create expressive audiobooks locally with Chatterbox — fast, private, and beautifully simple.",
        )


class AnimatedButton(QPushButton):
    """QPushButton with a subtle animated lift and press response."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setColor(QColor(73, 70, 135, 70))
        self._shadow.setBlurRadius(15.0)
        self._shadow.setOffset(QPointF(0.0, 3.0))
        self.setGraphicsEffect(self._shadow)

        self._animation_group = QParallelAnimationGroup(self)
        self._blur_animation = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._offset_animation = QPropertyAnimation(self._shadow, b"offset", self)
        self._animation_group.addAnimation(self._blur_animation)
        self._animation_group.addAnimation(self._offset_animation)

    def enterEvent(self, event):
        if self.isEnabled():
            self._animate_shadow(25.0, QPointF(0.0, 6.0), 150)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.isEnabled():
            self._animate_shadow(15.0, QPointF(0.0, 3.0), 150)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self.isEnabled() and event.button() == Qt.LeftButton:
            self._animate_shadow(7.0, QPointF(0.0, 1.0), 80)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.isEnabled():
            if self.underMouse():
                self._animate_shadow(25.0, QPointF(0.0, 6.0), 120)
            else:
                self._animate_shadow(15.0, QPointF(0.0, 3.0), 120)

    def _animate_shadow(self, blur: float, offset: QPointF, duration: int):
        self._animation_group.stop()
        easing = QEasingCurve.OutCubic

        self._blur_animation.setDuration(duration)
        self._blur_animation.setStartValue(self._shadow.blurRadius())
        self._blur_animation.setEndValue(blur)
        self._blur_animation.setEasingCurve(easing)

        self._offset_animation.setDuration(duration)
        self._offset_animation.setStartValue(self._shadow.offset())
        self._offset_animation.setEndValue(offset)
        self._offset_animation.setEasingCurve(easing)
        self._animation_group.start()
