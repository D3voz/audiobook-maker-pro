"""Background installation worker for optional engine runtimes."""

from PySide6.QtCore import QThread, Signal

from core.qwen_runtime import QwenRuntimeManager


class QwenRuntimeInstallWorker(QThread):
    progress = Signal(str)
    installation_finished = Signal(bool, str)

    def __init__(self, runtime_manager: QwenRuntimeManager):
        super().__init__()
        self.runtime_manager = runtime_manager

    def run(self):
        try:
            self.runtime_manager.install(self.progress.emit)
            self.installation_finished.emit(True, self.runtime_manager.status_text())
        except Exception as exc:
            self.installation_finished.emit(False, str(exc))
