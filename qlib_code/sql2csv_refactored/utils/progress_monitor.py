"""
进度监控工具模块

提供可选的进度条和性能指标显示
"""

import time
from typing import Optional, Dict, Any
from contextlib import contextmanager


class ProgressMonitor:
    """
    进度监控器

    提供进度跟踪和性能指标显示功能
    """

    def __init__(self, enabled: bool = True, use_tqdm: bool = True):
        """
        初始化进度监控器

        Args:
            enabled: 是否启用进度监控
            use_tqdm: 是否使用tqdm进度条（如果可用）
        """
        self.enabled = enabled
        self.use_tqdm = use_tqdm and self._check_tqdm_available()
        self.metrics = {}

    def _check_tqdm_available(self) -> bool:
        """检查tqdm是否可用"""
        try:
            import tqdm
            return True
        except ImportError:
            return False

    @contextmanager
    def track_batch(self, total: int, desc: str = "Processing"):
        """
        跟踪批次处理进度

        Args:
            total: 总数量
            desc: 描述文本

        Yields:
            进度更新函数
        """
        if not self.enabled:
            yield lambda: None
            return

        if self.use_tqdm:
            try:
                from tqdm import tqdm
                pbar = tqdm(total=total, desc=desc, unit="items")

                def update():
                    pbar.update(1)

                try:
                    yield update
                finally:
                    pbar.close()

            except ImportError:
                # Fallback to simple counter
                yield self._simple_progress(total, desc)
        else:
            yield self._simple_progress(total, desc)

    def _simple_progress(self, total: int, desc: str):
        """简单的进度显示（不使用tqdm）"""
        counter = {'current': 0}
        start_time = time.time()

        def update():
            counter['current'] += 1
            if counter['current'] % max(1, total // 10) == 0 or counter['current'] == total:
                elapsed = time.time() - start_time
                rate = counter['current'] / elapsed if elapsed > 0 else 0
                percent = (counter['current'] / total * 100) if total > 0 else 0
                print(f"{desc}: {counter['current']}/{total} ({percent:.1f}%) - {rate:.1f} items/s")

        return update

    def record_metric(self, name: str, value: Any):
        """
        记录性能指标

        Args:
            name: 指标名称
            value: 指标值
        """
        if self.enabled:
            self.metrics[name] = value

    def get_metrics(self) -> Dict[str, Any]:
        """获取所有记录的指标"""
        return self.metrics.copy()

    def print_summary(self):
        """打印性能指标摘要"""
        if not self.enabled or not self.metrics:
            return

        print("\n" + "=" * 60)
        print("Performance Metrics Summary")
        print("=" * 60)
        for name, value in self.metrics.items():
            if isinstance(value, float):
                print(f"{name}: {value:.3f}")
            else:
                print(f"{name}: {value}")
        print("=" * 60)


# 全局进度监控器实例（可选）
_global_monitor: Optional[ProgressMonitor] = None


def get_progress_monitor(enabled: bool = True) -> ProgressMonitor:
    """
    获取全局进度监控器实例

    Args:
        enabled: 是否启用进度监控

    Returns:
        ProgressMonitor实例
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ProgressMonitor(enabled=enabled)
    return _global_monitor


def set_progress_monitor(monitor: Optional[ProgressMonitor]):
    """
    设置全局进度监控器实例

    Args:
        monitor: ProgressMonitor实例或None
    """
    global _global_monitor
    _global_monitor = monitor
