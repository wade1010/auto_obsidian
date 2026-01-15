"""
统计面板模块
显示任务执行统计信息和图表
"""
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import pyqtgraph as pg
import numpy as np

logger = logging.getLogger(__name__)


class StatsPanel(QWidget):
    """统计面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scheduler = None
        self._init_ui()

        # 自动刷新定时器（每10秒刷新一次）
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 统计卡片区域
        stats_cards_group = self._create_stats_cards()
        layout.addWidget(stats_cards_group)

        # 图表区域
        charts_group = self._create_charts_area()
        layout.addWidget(charts_group)

        # 错误摘要和执行历史（使用水平布局并排显示）
        bottom_layout = QHBoxLayout()

        error_group = self._create_error_summary()
        bottom_layout.addWidget(error_group)

        history_group = self._create_history_list()
        bottom_layout.addWidget(history_group)

        layout.addLayout(bottom_layout)

        layout.addStretch()

    def _create_stats_cards(self) -> QGroupBox:
        """创建统计卡片区域"""
        group = QGroupBox("总体统计")
        layout = QHBoxLayout()

        # 执行次数卡片
        self.total_card = self._create_stat_card("执行次数", "0", "#3498db")
        layout.addWidget(self.total_card)

        # 成功次数卡片
        self.success_card = self._create_stat_card("成功次数", "0", "#2ecc71")
        layout.addWidget(self.success_card)

        # 失败次数卡片
        self.failed_card = self._create_stat_card("失败次数", "0", "#e74c3c")
        layout.addWidget(self.failed_card)

        # 成功率卡片
        self.rate_card = self._create_stat_card("成功率", "0%", "#9b59b6")
        layout.addWidget(self.rate_card)

        group.setLayout(layout)
        return group

    def _create_stat_card(self, title: str, value: str, color: str) -> QWidget:
        """创建统计卡片"""
        card = QWidget()
        card.setFixedSize(180, 120)
        card.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)

        layout = QVBoxLayout(card)

        # 标题
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        layout.addWidget(title_label)

        # 数值
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(22)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)

        layout.addStretch()

        # 保存value_label的引用以便更新
        card.value_label = value_label

        return card

    def _create_charts_area(self) -> QGroupBox:
        """创建图表区域"""
        group = QGroupBox("数据可视化")
        layout = QHBoxLayout()

        # 配置pyqtgraph使用中文字体
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        pg.setConfigOptions(antialias=True)

        # 成功率趋势图
        self.success_rate_chart = pg.PlotWidget(title="成功率趋势（最近20次）")
        self.success_rate_chart.setLabel('left', '成功率', units='%')
        self.success_rate_chart.setLabel('bottom', '执行次数')
        self.success_rate_chart.showGrid(x=True, y=True, alpha=0.3)
        self.success_rate_chart.setYRange(0, 100)
        self.success_rate_chart.setMaximumHeight(250)

        # 设置中文字体
        font = QFont('Microsoft YaHei', 9)
        self.success_rate_chart.getAxis('left').setTickFont(font)
        self.success_rate_chart.getAxis('bottom').setTickFont(font)
        self.success_rate_chart.getAxis('left').labelStyle = {'font': font}
        self.success_rate_chart.getAxis('bottom').labelStyle = {'font': font}

        layout.addWidget(self.success_rate_chart)

        # 每日生成数量图
        self.daily_count_chart = pg.PlotWidget(title="每日生成数量（最近7天）")
        self.daily_count_chart.setLabel('left', '数量', units='篇')
        self.daily_count_chart.setLabel('bottom', '日期')
        self.daily_count_chart.showGrid(x=True, y=True, alpha=0.3)
        self.daily_count_chart.setMaximumHeight(250)

        # 设置中文字体
        self.daily_count_chart.getAxis('left').setTickFont(font)
        self.daily_count_chart.getAxis('bottom').setTickFont(font)
        self.daily_count_chart.getAxis('left').labelStyle = {'font': font}
        self.daily_count_chart.getAxis('bottom').labelStyle = {'font': font}

        layout.addWidget(self.daily_count_chart)

        group.setLayout(layout)
        return group

    def _create_error_summary(self) -> QGroupBox:
        """创建错误摘要区域"""
        group = QGroupBox("最近错误（10条）")
        layout = QVBoxLayout()

        self.error_text = QLabel("暂无错误记录")
        self.error_text.setWordWrap(True)
        self.error_text.setAlignment(Qt.AlignTop)
        self.error_text.setStyleSheet("color: #e74c3c; font-size: 11px;")
        layout.addWidget(self.error_text)

        group.setLayout(layout)
        group.setMaximumHeight(200)
        return group

    def _create_history_list(self) -> QGroupBox:
        """创建执行历史列表"""
        group = QGroupBox("执行历史（最近20条）")
        layout = QVBoxLayout()

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["时间", "主题", "状态", "详情"])

        # 设置列宽
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        # 设置表格样式
        self.history_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)

        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.verticalHeader().setVisible(False)

        layout.addWidget(self.history_table)
        group.setLayout(layout)
        return group

    def set_scheduler(self, scheduler):
        """设置调度器实例"""
        self.scheduler = scheduler

    def refresh_data(self):
        """刷新统计数据"""
        try:
            main_window = self._get_main_window()
            if not main_window or not main_window.scheduler:
                return

            scheduler = main_window.scheduler

            # 更新统计卡片
            stats = scheduler.get_stats()
            self._update_stats_cards(stats)

            # 更新图表
            history = scheduler.get_history()
            self._update_charts(history)

            # 更新错误摘要
            self._update_error_summary(history)

            # 更新执行历史
            self._update_history_table(history)

            logger.debug("统计面板已刷新")

        except Exception as e:
            logger.error(f"刷新统计面板失败: {e}")

    def _update_stats_cards(self, stats: dict):
        """更新统计卡片"""
        stats_data = stats.get("stats", {})

        total_runs = stats_data.get('total_runs', 0)
        success_count = stats_data.get('success_count', 0)
        failed_count = stats_data.get('failed_count', 0)

        # 计算成功率
        if total_runs > 0:
            success_rate = (success_count / total_runs) * 100
        else:
            success_rate = 0

        # 更新卡片数值
        self.total_card.value_label.setText(str(total_runs))
        self.success_card.value_label.setText(str(success_count))
        self.failed_card.value_label.setText(str(failed_count))
        self.rate_card.value_label.setText(f"{success_rate:.1f}%")

    def _update_charts(self, history: list):
        """更新图表"""
        if not history:
            # 清空图表
            self.success_rate_chart.clear()
            self.daily_count_chart.clear()
            return

        # 更新成功率趋势图
        self._update_success_rate_chart(history)

        # 更新每日生成数量图
        self._update_daily_count_chart(history)

    def _update_success_rate_chart(self, history: list):
        """更新成功率趋势图"""
        try:
            # 取最近20条记录
            recent_history = history[-20:] if len(history) > 20 else history

            # 计算累计成功率
            success_rates = []
            total = 0
            success = 0

            for record in recent_history:
                total += 1
                if record.get('status') == 'success':
                    success += 1
                success_rates.append((success / total) * 100 if total > 0 else 0)

            if success_rates:
                x = np.arange(1, len(success_rates) + 1)
                y = np.array(success_rates)

                self.success_rate_chart.clear()
                self.success_rate_chart.plot(x, y, pen=pg.mkPen('#2ecc71', width=2))

        except Exception as e:
            logger.error(f"更新成功率图表失败: {e}")

    def _update_daily_count_chart(self, history: list):
        """更新每日生成数量图"""
        try:
            # 计算最近7天的统计
            daily_stats = self._calculate_daily_stats(history)

            if daily_stats:
                dates = list(daily_stats.keys())
                counts = list(daily_stats.values())

                x = np.arange(len(dates))
                y = np.array(counts)

                self.daily_count_chart.clear()

                # 设置x轴标签为日期
                ax = self.daily_count_chart.getAxis('bottom')
                ax.setTicks([[(i, date) for i, date in enumerate(dates)]])

                # 绘制柱状图
                bar_item = pg.BarGraphItem(x=x, height=y, width=0.6, brush='#3498db')
                self.daily_count_chart.addItem(bar_item)

        except Exception as e:
            logger.error(f"更新每日数量图表失败: {e}")

    def _calculate_daily_stats(self, history: list) -> dict:
        """计算每日统计数据"""
        try:
            # 按日期聚合
            daily_counts = defaultdict(int)

            for record in history:
                time_str = record.get('time', '')
                if not time_str:
                    continue

                # 解析时间字符串（格式：2025-01-15 14:30:25）
                try:
                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    date_str = dt.strftime("%m-%d")
                    daily_counts[date_str] += 1
                except ValueError:
                    continue

            # 按日期排序并取最近7天
            sorted_dates = sorted(daily_counts.keys())
            recent_dates = sorted_dates[-7:] if len(sorted_dates) > 7 else sorted_dates

            return {date: daily_counts[date] for date in recent_dates}

        except Exception as e:
            logger.error(f"计算每日统计失败: {e}")
            return {}

    def _update_error_summary(self, history: list):
        """更新错误摘要"""
        # 筛选失败的记录
        failed_records = [r for r in history if r.get('status') == 'failed']

        if not failed_records:
            self.error_text.setText("暂无错误记录")
            return

        # 取最近10条错误
        recent_errors = failed_records[-10:] if len(failed_records) > 10 else failed_records

        error_lines = []
        for record in reversed(recent_errors):
            time_str = record.get('time', '')
            topic = record.get('topic', '')
            error = record.get('error', '未知错误')
            error_lines.append(f"[{time_str}] {topic}\n  错误: {error}")

        self.error_text.setText('\n\n'.join(error_lines))

    def _update_history_table(self, history: list):
        """更新执行历史表格"""
        if not history:
            self.history_table.setRowCount(0)
            return

        # 取最近20条记录
        recent_history = history[-20:] if len(history) > 20 else history

        self.history_table.setRowCount(len(recent_history))

        for row, record in enumerate(reversed(recent_history)):
            time_str = record.get('time', '')
            topic = record.get('topic', '')
            status = record.get('status', '')
            error = record.get('error', '')

            # 创建表格项
            time_item = QTableWidgetItem(time_str)
            topic_item = QTableWidgetItem(topic)
            status_item = QTableWidgetItem("成功" if status == "success" else "失败")
            detail_item = QTableWidgetItem(error if error else "-")

            # 设置状态颜色
            if status == "success":
                status_item.setForeground(Qt.green)
            else:
                status_item.setForeground(Qt.red)

            # 设置行内容
            self.history_table.setItem(row, 0, time_item)
            self.history_table.setItem(row, 1, topic_item)
            self.history_table.setItem(row, 2, status_item)
            self.history_table.setItem(row, 3, detail_item)

    def _get_main_window(self):
        """获取主窗口对象"""
        try:
            # 方法1: 通过parent链
            parent = self.parent()
            if parent:
                main_window = parent.parent()
                if hasattr(main_window, 'scheduler'):
                    return main_window

            # 方法2: 通过QApplication
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                widgets = app.topLevelWidgets()
                for widget in widgets:
                    if hasattr(widget, 'scheduler'):
                        return widget

            return None
        except Exception as e:
            logger.error(f"获取main_window失败: {e}")
            return None

    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        # 启动自动刷新定时器
        if not self.refresh_timer.isActive():
            self.refresh_timer.start(10000)  # 10秒刷新一次
            # 立即刷新一次数据
            self.refresh_data()
            logger.debug("统计面板可见，启动自动刷新")

    def hideEvent(self, event):
        """窗口隐藏事件"""
        super().hideEvent(event)
        # 停止刷新定时器
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
            logger.debug("统计面板不可见，停止自动刷新")
