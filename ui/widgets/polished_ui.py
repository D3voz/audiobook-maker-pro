"""Small presentation widgets used by the polished application shell."""

from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    QVariantAnimation,
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

    # The minimum app width produces a banner close to this ratio. Keeping the
    # artwork at that ratio prevents horizontal resizing from zooming into the
    # character; wider banners extend only the quiet background on the left.
    ARTWORK_DISPLAY_RATIO = 5.1

    def __init__(self, artwork_path: str, engine_artworks=None, parent=None):
        super().__init__(parent)
        default_artwork = QPixmap(str(Path(artwork_path)))
        self._artworks = {
            "local": default_artwork,
            "api": default_artwork,
        }
        for engine_type, path in (engine_artworks or {}).items():
            self._artworks[engine_type] = QPixmap(str(Path(path)))
        self._engine_type = "local"
        self._artwork = default_artwork
        self._previous_artwork = QPixmap()
        self._artwork_blend = 1.0
        self._theme_name = "aurora"

        self._artwork_transition = QVariantAnimation(self)
        self._artwork_transition.setDuration(260)
        self._artwork_transition.setEasingCurve(QEasingCurve.InOutCubic)
        self._artwork_transition.valueChanged.connect(self._set_artwork_blend)
        self._artwork_transition.finished.connect(self._finish_artwork_transition)

        self.setObjectName("heroBanner")
        self.setMinimumHeight(184)
        self.setMaximumHeight(218)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setAccessibleName("Audiobook Maker welcome banner")

    def set_theme(self, theme_name: str):
        self._theme_name = theme_name
        self.update()

    def set_engine(self, engine_type: str):
        """Switch artwork and copy after an engine change is confirmed."""
        engine_type = engine_type if engine_type in self._artworks else "local"
        next_artwork = self._artworks[engine_type]
        artwork_changed = next_artwork.cacheKey() != self._artwork.cacheKey()
        self._engine_type = engine_type

        if artwork_changed:
            self._artwork_transition.stop()
            self._previous_artwork = self._artwork
            self._artwork = next_artwork
            self._artwork_blend = 0.0
            self._artwork_transition.setStartValue(0.0)
            self._artwork_transition.setEndValue(1.0)
            self._artwork_transition.start()
        else:
            self.update()

    def _set_artwork_blend(self, value):
        self._artwork_blend = float(value)
        self.update()

    def _finish_artwork_transition(self):
        self._artwork_blend = 1.0
        self._previous_artwork = QPixmap()
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

        self._paint_artwork_background(painter, card)

        if not self._artwork.isNull():
            artwork_target = self._artwork_destination(card)
            if not self._previous_artwork.isNull() and self._artwork_blend < 1.0:
                previous_source = self._source_crop(
                    artwork_target, self._previous_artwork
                )
                painter.drawPixmap(
                    artwork_target, self._previous_artwork, previous_source
                )
                painter.setOpacity(self._artwork_blend)
            source = self._source_crop(artwork_target, self._artwork)
            painter.drawPixmap(artwork_target, self._artwork, source)
            painter.setOpacity(1.0)
            self._paint_artwork_seam(painter, card, artwork_target)

        self._paint_readability_overlay(painter, card)
        self._paint_copy(painter, card)

        painter.setClipping(False)
        border = QColor("#B8EAF1") if self._theme_name == "aurora" else QColor("#736AA8")
        border.setAlpha(175)
        painter.setPen(QPen(border, 1.25))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(card, 24.0, 24.0)

    def _artwork_destination(self, card: QRectF) -> QRectF:
        """Keep character scale stable and anchor additional width to the left."""
        artwork_width = min(
            card.width(),
            card.height() * self.ARTWORK_DISPLAY_RATIO,
        )
        return QRectF(
            card.left() + card.width() - artwork_width,
            card.top(),
            artwork_width,
            card.height(),
        )

    def _paint_artwork_background(self, painter: QPainter, card: QRectF):
        """Fill the area exposed when a wide window exceeds the artwork ratio."""
        background = QLinearGradient(card.topLeft(), card.topRight())
        for position, color in self._artwork_background_stops():
            background.setColorAt(position, color)
        painter.fillRect(card, background)

    def _paint_artwork_seam(
        self,
        painter: QPainter,
        card: QRectF,
        artwork_target: QRectF,
    ):
        """Feather the left edge of right-anchored art into its extension."""
        extension_width = artwork_target.left() - card.left()
        if extension_width <= 1.0:
            return

        position = extension_width / max(card.width(), 1.0)
        seam_color = self._background_color_at(position)
        transparent = QColor(seam_color)
        transparent.setAlpha(0)
        feather_width = min(230.0, artwork_target.width() * 0.28)
        seam = QLinearGradient(
            artwork_target.left(),
            card.top(),
            artwork_target.left() + feather_width,
            card.top(),
        )
        seam.setColorAt(0.0, seam_color)
        seam.setColorAt(1.0, transparent)
        painter.fillRect(
            QRectF(
                artwork_target.left(),
                card.top(),
                feather_width,
                card.height(),
            ),
            seam,
        )

    def _artwork_background_stops(self):
        if self._theme_name == "midnight":
            return (
                (0.0, QColor("#191832")),
                (0.72, QColor("#282A50")),
                (1.0, QColor("#343A65")),
            )
        return (
            (0.0, QColor("#F1FDFF")),
            (0.72, QColor("#E5F1FF")),
            (1.0, QColor("#E6E0FF")),
        )

    def _background_color_at(self, position: float) -> QColor:
        stops = self._artwork_background_stops()
        position = min(max(position, 0.0), 1.0)
        for index in range(1, len(stops)):
            left_position, left_color = stops[index - 1]
            right_position, right_color = stops[index]
            if position <= right_position:
                span = max(right_position - left_position, 0.001)
                amount = (position - left_position) / span
                return QColor(
                    round(left_color.red() + (right_color.red() - left_color.red()) * amount),
                    round(left_color.green() + (right_color.green() - left_color.green()) * amount),
                    round(left_color.blue() + (right_color.blue() - left_color.blue()) * amount),
                )
        return QColor(stops[-1][1])

    def _source_crop(self, target: QRectF, artwork: QPixmap) -> QRectF:
        """Crop the wide art around the character's face without stretching it."""
        pix_w = float(artwork.width())
        pix_h = float(artwork.height())
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
        banner_copy = {
            "local": (
                "LOCAL VOICE STUDIO",
                "Create expressive audiobooks locally with Chatterbox — fast, private, and beautifully simple.",
            ),
            "qwen3": (
                "QWEN VOICE STUDIO",
                "Shape voices locally with Faster Qwen3-TTS — CUDA-graph accelerated and beautifully expressive.",
            ),
            "api": (
                "REMOTE VOICE STUDIO",
                "Connect to TTS-WebUI and create expressive audiobooks through your remote voice server.",
            ),
        }
        badge_text, body_text = banner_copy.get(
            self._engine_type, banner_copy["local"]
        )
        painter.drawText(pill, Qt.AlignCenter, badge_text)

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
            body_text,
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
