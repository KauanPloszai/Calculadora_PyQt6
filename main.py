from __future__ import annotations

import sys
from decimal import Decimal, InvalidOperation, getcontext

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QKeyEvent, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


getcontext().prec = 28

LIGHT_THEME = {
    "window_bg": "#f3f3f3",
    "text_primary": "#1f1f1f",
    "card_bg": "#fbfbfb",
    "card_border": "#e4e4e4",
    "button_border": "#dadada",
    "number_bg": "#ffffff",
    "number_hover": "#f5f5f5",
    "number_pressed": "#ececec",
    "action_bg": "#f0f0f0",
    "action_hover": "#e8e8e8",
    "action_pressed": "#dddddd",
    "equal_bg": "#8fb9ff",
    "equal_hover": "#84b1ff",
    "equal_pressed": "#76a6fc",
    "equal_fg": "#0b1f44",
    "memory_fg": "#505050",
    "memory_hover": "#e9e9e9",
    "memory_disabled": "#b0b0b0",
    "header_hover": "#e9e9e9",
    "header_checked": "#e0e0e0",
    "ghost_fg": "#4f4f4f",
    "ghost_hover": "#ececec",
    "ghost_disabled": "#b8b8b8",
    "history_item_hover": "#f1f4f9",
    "history_item_selected": "#e8f0ff",
    "secondary_fg": "#707070",
    "muted_fg": "#7d7d7d",
    "memory_indicator_fg": "#6e6e6e",
    "icon_fg": "#3e3e3e",
    "theme_bg": "#ffffff",
    "theme_hover": "#f1f1f1",
    "theme_fg": "#2f2f2f",
    "theme_border": "#d4d4d4",
    "theme_checked_bg": "#dce9ff",
    "theme_checked_border": "#7eaefb",
    "theme_checked_fg": "#123564",
}

DARK_THEME = {
    "window_bg": "#181818",
    "text_primary": "#f3f3f3",
    "card_bg": "#212121",
    "card_border": "#353535",
    "button_border": "#3f3f3f",
    "number_bg": "#2b2b2b",
    "number_hover": "#343434",
    "number_pressed": "#3d3d3d",
    "action_bg": "#323232",
    "action_hover": "#3a3a3a",
    "action_pressed": "#464646",
    "equal_bg": "#4f8cff",
    "equal_hover": "#5b96ff",
    "equal_pressed": "#6aa0ff",
    "equal_fg": "#ffffff",
    "memory_fg": "#d0d0d0",
    "memory_hover": "#2e2e2e",
    "memory_disabled": "#747474",
    "header_hover": "#2d2d2d",
    "header_checked": "#3a3a3a",
    "ghost_fg": "#d5d5d5",
    "ghost_hover": "#303030",
    "ghost_disabled": "#757575",
    "history_item_hover": "#293342",
    "history_item_selected": "#324259",
    "secondary_fg": "#a7a7a7",
    "muted_fg": "#8f8f8f",
    "memory_indicator_fg": "#b1b1b1",
    "icon_fg": "#f3f3f3",
    "theme_bg": "#252525",
    "theme_hover": "#313131",
    "theme_fg": "#f1f1f1",
    "theme_border": "#414141",
    "theme_checked_bg": "#143968",
    "theme_checked_border": "#4f8cff",
    "theme_checked_fg": "#f4f8ff",
}


class CalculatorButton(QPushButton):
    def __init__(self, text: str, role: str, min_height: int = 66) -> None:
        super().__init__(text)
        self.setObjectName(f"{role}Button")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(min_height)


class HistoryEntryWidget(QWidget):
    def __init__(self, expression: str, result: str) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        expression_label = QLabel(expression)
        expression_label.setObjectName("historyExpressionLabel")
        expression_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        result_label = QLabel(result)
        result_label.setObjectName("historyResultLabel")
        result_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        result_label.setFont(QFont("Segoe UI Semibold", 18))

        layout.addWidget(expression_label)
        layout.addWidget(result_label)


class CalculatorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.current_entry = "0"
        self.expression_text = ""
        self.stored_operand: Decimal | None = None
        self.pending_operator: str | None = None
        self.last_operator: str | None = None
        self.last_operand: Decimal | None = None
        self.waiting_for_new_operand = False
        self.reset_on_next_digit = False
        self.error_state = False

        self.memory_value = Decimal("0")
        self.memory_has_value = False
        self.memory_buttons: dict[str, QPushButton] = {}
        self.current_theme = "light"

        self.compact_width = 430
        self.expanded_width = 720

        self.expression_label: QLabel
        self.result_label: QLabel
        self.memory_indicator_label: QLabel
        self.theme_toggle_button: QPushButton
        self.history_toggle_button: QPushButton
        self.history_frame: QFrame
        self.history_list: QListWidget
        self.empty_history_label: QLabel
        self.clear_history_button: QPushButton

        self.setWindowTitle("Calculadora")
        self.setMinimumSize(420, 720)
        self.resize(self.compact_width, 760)

        self.build_ui()
        self.apply_theme()
        self.update_display()
        self.update_history_state()

    def build_ui(self) -> None:
        root = QWidget()
        root.setFont(QFont("Segoe UI", 11))
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(14)

        calculator_widget = QWidget()
        main_layout = QVBoxLayout(calculator_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 0, 4, 0)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title_label = QLabel("Calculadora")
        title_label.setObjectName("titleLabel")
        title_label.setFont(QFont("Segoe UI Semibold", 11))

        mode_label = QLabel("Padrão")
        mode_label.setFont(QFont("Segoe UI Semibold", 22))
        mode_label.setObjectName("modeLabel")

        title_box.addWidget(title_label)
        title_box.addWidget(mode_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.theme_toggle_button = QPushButton()
        self.theme_toggle_button.setObjectName("themeToggleButton")
        self.theme_toggle_button.setCheckable(True)
        self.theme_toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_toggle_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.theme_toggle_button.setMinimumHeight(40)
        self.theme_toggle_button.setMinimumWidth(92)
        self.theme_toggle_button.setToolTip("Alternar entre modo Light e Dark")
        self.theme_toggle_button.toggled.connect(self.set_theme_from_toggle)
        header_layout.addWidget(self.theme_toggle_button)

        self.history_toggle_button = QPushButton()
        self.history_toggle_button.setObjectName("headerIconButton")
        self.history_toggle_button.setCheckable(True)
        self.history_toggle_button.setIcon(self.create_history_icon())
        self.history_toggle_button.setIconSize(QSize(22, 22))
        self.history_toggle_button.setToolTip("Mostrar histórico")
        self.history_toggle_button.clicked.connect(self.toggle_history)
        header_layout.addWidget(self.history_toggle_button)

        main_layout.addLayout(header_layout)

        display_frame = QFrame()
        display_frame.setObjectName("displayFrame")

        display_layout = QVBoxLayout(display_frame)
        display_layout.setContentsMargins(18, 18, 18, 18)
        display_layout.setSpacing(10)

        expression_row = QHBoxLayout()
        expression_row.setSpacing(8)

        self.memory_indicator_label = QLabel("")
        self.memory_indicator_label.setObjectName("memoryIndicatorLabel")
        self.memory_indicator_label.setStyleSheet("color: #6e6e6e; font-size: 14px;")
        self.memory_indicator_label.setFixedWidth(18)

        self.expression_label = QLabel("")
        self.expression_label.setObjectName("expressionLabel")
        self.expression_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.expression_label.setStyleSheet("color: #707070; font-size: 15px;")

        expression_row.addWidget(self.memory_indicator_label)
        expression_row.addWidget(self.expression_label, 1)

        self.result_label = QLabel("0")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.result_label.setFont(QFont("Segoe UI Semibold", 34))

        display_layout.addLayout(expression_row)
        display_layout.addStretch()
        display_layout.addWidget(self.result_label)
        main_layout.addWidget(display_frame)

        memory_layout = QHBoxLayout()
        memory_layout.setSpacing(6)

        for label in ("MC", "MR", "M+", "M-", "MS"):
            button = CalculatorButton(label, "memory", min_height=34)
            button.clicked.connect(lambda checked=False, action=label: self.handle_action(action))
            self.memory_buttons[label] = button
            memory_layout.addWidget(button)

        main_layout.addLayout(memory_layout)

        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(10)
        grid_layout.setVerticalSpacing(10)

        rows = [
            ["%", "CE", "C", "⌫"],
            ["1/x", "x²", "√x", "÷"],
            ["7", "8", "9", "×"],
            ["4", "5", "6", "−"],
            ["1", "2", "3", "+"],
            ["+/-", "0", ".", "="],
        ]

        for row_index, row in enumerate(rows):
            for column_index, label in enumerate(row):
                button = CalculatorButton(label, self.button_role(label))
                button.clicked.connect(lambda checked=False, action=label: self.handle_action(action))
                grid_layout.addWidget(button, row_index, column_index)

        main_layout.addLayout(grid_layout)

        self.history_frame = QFrame()
        self.history_frame.setObjectName("historyFrame")
        self.history_frame.setFixedWidth(230)

        history_layout = QVBoxLayout(self.history_frame)
        history_layout.setContentsMargins(16, 16, 16, 16)
        history_layout.setSpacing(10)

        history_header = QHBoxLayout()

        history_title = QLabel("Histórico")
        history_title.setFont(QFont("Segoe UI Semibold", 16))
        history_title.setObjectName("sectionTitleLabel")

        self.clear_history_button = QPushButton("Limpar")
        self.clear_history_button.setObjectName("ghostButton")
        self.clear_history_button.clicked.connect(self.clear_history)

        history_header.addWidget(history_title)
        history_header.addStretch()
        history_header.addWidget(self.clear_history_button)

        self.empty_history_label = QLabel("Nenhum cálculo ainda")
        self.empty_history_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_history_label.setObjectName("emptyStateLabel")
        self.empty_history_label.setStyleSheet("color: #7d7d7d; font-size: 13px;")

        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        self.history_list.itemClicked.connect(self.load_history_item)

        history_layout.addLayout(history_header)
        history_layout.addWidget(self.empty_history_label, 1)
        history_layout.addWidget(self.history_list, 1)

        self.history_frame.hide()

        root_layout.addWidget(calculator_widget, 1)
        root_layout.addWidget(self.history_frame)

    def set_theme_from_toggle(self, checked: bool) -> None:
        self.current_theme = "dark" if checked else "light"
        self.apply_theme()

    def theme_colors(self) -> dict[str, str]:
        return DARK_THEME if self.current_theme == "dark" else LIGHT_THEME

    def build_stylesheet(self, colors: dict[str, str]) -> str:
        return f"""
            QMainWindow {{
                background-color: {colors["window_bg"]};
            }}
            QLabel {{
                color: {colors["text_primary"]};
            }}
            QLabel#historyExpressionLabel {{
                color: {colors["secondary_fg"]};
                font-size: 12px;
            }}
            QLabel#historyResultLabel {{
                color: {colors["text_primary"]};
            }}
            QFrame#displayFrame,
            QFrame#historyFrame {{
                background-color: {colors["card_bg"]};
                border: 1px solid {colors["card_border"]};
                border-radius: 20px;
            }}
            QPushButton {{
                border-radius: 16px;
                border: 1px solid {colors["button_border"]};
                font-size: 20px;
                color: {colors["text_primary"]};
            }}
            QPushButton#numberButton {{
                background-color: {colors["number_bg"]};
            }}
            QPushButton#numberButton:hover {{
                background-color: {colors["number_hover"]};
            }}
            QPushButton#numberButton:pressed {{
                background-color: {colors["number_pressed"]};
            }}
            QPushButton#actionButton,
            QPushButton#operatorButton {{
                background-color: {colors["action_bg"]};
            }}
            QPushButton#actionButton:hover,
            QPushButton#operatorButton:hover {{
                background-color: {colors["action_hover"]};
            }}
            QPushButton#actionButton:pressed,
            QPushButton#operatorButton:pressed {{
                background-color: {colors["action_pressed"]};
            }}
            QPushButton#equalButton {{
                background-color: {colors["equal_bg"]};
                border-color: {colors["equal_bg"]};
                color: {colors["equal_fg"]};
                font-weight: 600;
            }}
            QPushButton#equalButton:hover {{
                background-color: {colors["equal_hover"]};
            }}
            QPushButton#equalButton:pressed {{
                background-color: {colors["equal_pressed"]};
            }}
            QPushButton#memoryButton {{
                background-color: transparent;
                border: none;
                color: {colors["memory_fg"]};
                font-size: 15px;
                padding: 6px 0;
            }}
            QPushButton#memoryButton:hover {{
                background-color: {colors["memory_hover"]};
                border-radius: 10px;
            }}
            QPushButton#memoryButton:disabled {{
                color: {colors["memory_disabled"]};
            }}
            QPushButton#themeToggleButton {{
                background-color: {colors["theme_bg"]};
                color: {colors["theme_fg"]};
                border: 1px solid {colors["theme_border"]};
                border-radius: 12px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 14px;
            }}
            QPushButton#themeToggleButton:hover {{
                background-color: {colors["theme_hover"]};
            }}
            QPushButton#themeToggleButton:checked {{
                background-color: {colors["theme_checked_bg"]};
                color: {colors["theme_checked_fg"]};
                border-color: {colors["theme_checked_border"]};
            }}
            QPushButton#headerIconButton {{
                background-color: transparent;
                border: none;
                border-radius: 12px;
                min-width: 40px;
                max-width: 40px;
                min-height: 40px;
                max-height: 40px;
                padding: 0;
            }}
            QPushButton#headerIconButton:hover {{
                background-color: {colors["header_hover"]};
            }}
            QPushButton#headerIconButton:checked {{
                background-color: {colors["header_checked"]};
            }}
            QPushButton#ghostButton {{
                background-color: transparent;
                border: none;
                color: {colors["ghost_fg"]};
                font-size: 13px;
                padding: 4px 8px;
            }}
            QPushButton#ghostButton:hover {{
                background-color: {colors["ghost_hover"]};
                border-radius: 10px;
            }}
            QPushButton#ghostButton:disabled {{
                color: {colors["ghost_disabled"]};
            }}
            QListWidget#historyList {{
                background: transparent;
                border: none;
                outline: none;
                padding: 0;
            }}
            QListWidget#historyList::item {{
                border-radius: 14px;
                margin: 4px 0;
            }}
            QListWidget#historyList::item:hover {{
                background-color: {colors["history_item_hover"]};
            }}
            QListWidget#historyList::item:selected {{
                background-color: {colors["history_item_selected"]};
            }}
        """

    def apply_theme(self) -> None:
        colors = self.theme_colors()
        is_dark = self.current_theme == "dark"

        self.setStyleSheet(self.build_stylesheet(colors))
        self.theme_toggle_button.setText("Dark" if is_dark else "Light")
        self.theme_toggle_button.setToolTip(
            "Alternar para modo Light" if is_dark else "Alternar para modo Dark"
        )
        self.history_toggle_button.setIcon(self.create_history_icon(color=colors["icon_fg"]))

        self.memory_indicator_label.setStyleSheet(
            f"color: {colors['memory_indicator_fg']}; font-size: 14px;"
        )
        self.expression_label.setStyleSheet(
            f"color: {colors['secondary_fg']}; font-size: 15px;"
        )
        self.empty_history_label.setStyleSheet(
            f"color: {colors['muted_fg']}; font-size: 13px;"
        )

    def create_history_icon(self, size: int = 22, color: str | None = None) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(
            QColor(color or self.theme_colors()["icon_fg"]),
            2.0,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        arc_rect = QRectF(4, 4, size - 8, size - 8)
        painter.drawArc(arc_rect, 35 * 16, 285 * 16)

        painter.drawLine(QPointF(6.5, 7.0), QPointF(4.2, 4.7))
        painter.drawLine(QPointF(6.5, 7.0), QPointF(6.6, 3.6))

        center = QPointF(size / 2, size / 2)
        painter.drawLine(center, QPointF(center.x(), center.y() - 4.0))
        painter.drawLine(center, QPointF(center.x() + 3.4, center.y() + 1.8))

        painter.end()
        return QIcon(pixmap)

    def button_role(self, label: str) -> str:
        if label.isdigit() or label == ".":
            return "number"
        if label == "=":
            return "equal"
        if label in {"÷", "×", "−", "+"}:
            return "operator"
        return "action"

    def handle_action(self, action: str) -> None:
        if action in "0123456789":
            self.input_digit(action)
            return

        if action == ".":
            self.input_decimal()
        elif action in {"÷", "×", "−", "+"}:
            self.select_operator(action)
        elif action == "=":
            self.calculate_result()
        elif action == "C":
            self.clear_all()
        elif action == "CE":
            self.clear_entry()
        elif action == "⌫":
            self.backspace()
        elif action == "+/-":
            self.toggle_sign()
        elif action == "%":
            self.apply_percent()
        elif action in {"1/x", "x²", "√x"}:
            self.apply_unary(action)
        elif action in {"MC", "MR", "M+", "M-", "MS"}:
            self.handle_memory(action)

    def input_digit(self, digit: str) -> None:
        if self.error_state:
            self.clear_all()

        if self.waiting_for_new_operand or self.reset_on_next_digit:
            self.current_entry = digit
            self.waiting_for_new_operand = False
            if self.reset_on_next_digit and self.pending_operator is None:
                self.expression_text = ""
            self.reset_on_next_digit = False
        elif self.current_entry == "0":
            self.current_entry = digit
        elif self.current_entry == "-0":
            self.current_entry = f"-{digit}"
        else:
            self.current_entry += digit

        self.update_display()

    def input_decimal(self) -> None:
        if self.error_state:
            self.clear_all()

        if self.waiting_for_new_operand or self.reset_on_next_digit:
            self.current_entry = "0."
            self.waiting_for_new_operand = False
            if self.reset_on_next_digit and self.pending_operator is None:
                self.expression_text = ""
            self.reset_on_next_digit = False
        elif "." not in self.current_entry:
            self.current_entry += "."

        self.update_display()

    def clear_entry(self) -> None:
        if self.error_state:
            self.clear_all()
            return

        self.current_entry = "0"
        self.waiting_for_new_operand = False
        self.reset_on_next_digit = False
        self.update_display()

    def clear_all(self) -> None:
        self.current_entry = "0"
        self.expression_text = ""
        self.stored_operand = None
        self.pending_operator = None
        self.last_operator = None
        self.last_operand = None
        self.waiting_for_new_operand = False
        self.reset_on_next_digit = False
        self.error_state = False
        self.update_display()

    def backspace(self) -> None:
        if self.error_state or self.waiting_for_new_operand or self.reset_on_next_digit:
            return

        if len(self.current_entry) <= 1 or self.current_entry in {"-0", "0"}:
            self.current_entry = "0"
        else:
            self.current_entry = self.current_entry[:-1]
            if self.current_entry in {"", "-"}:
                self.current_entry = "0"

        self.update_display()

    def toggle_sign(self) -> None:
        if self.error_state:
            return

        if self.waiting_for_new_operand:
            self.current_entry = "-0"
            self.waiting_for_new_operand = False
            self.update_display()
            return

        if self.current_entry.startswith("-"):
            self.current_entry = self.current_entry[1:]
        elif self.current_entry != "0":
            self.current_entry = f"-{self.current_entry}"
        else:
            self.current_entry = "-0"

        self.update_display()

    def select_operator(self, operator: str) -> None:
        if self.error_state:
            return

        current_value = self.current_decimal()

        if self.pending_operator and not self.waiting_for_new_operand:
            result = self.perform_binary(self.stored_operand or Decimal("0"), current_value, self.pending_operator)
            if result is None:
                return
            self.stored_operand = result
            self.current_entry = self.format_decimal(result)
        elif self.pending_operator is None:
            self.stored_operand = current_value

        self.pending_operator = operator
        self.waiting_for_new_operand = True
        self.reset_on_next_digit = False
        self.last_operator = None
        self.last_operand = None
        self.expression_text = f"{self.format_decimal(self.stored_operand or Decimal('0'))} {operator}"
        self.update_display()

    def calculate_result(self) -> None:
        if self.error_state:
            return

        if self.pending_operator:
            left = self.stored_operand if self.stored_operand is not None else self.current_decimal()

            if self.waiting_for_new_operand:
                right = self.last_operand if self.last_operand is not None else left
                self.last_operand = right
            else:
                right = self.current_decimal()
                self.last_operand = right

            result = self.perform_binary(left, right, self.pending_operator)
            if result is None:
                return

            self.expression_text = f"{self.format_decimal(left)} {self.pending_operator} {self.format_decimal(right)} ="
            self.current_entry = self.format_decimal(result)
            self.stored_operand = result
            self.last_operator = self.pending_operator
            self.pending_operator = None
            self.waiting_for_new_operand = False
            self.reset_on_next_digit = True
            self.add_history_entry(self.expression_text, self.current_entry)
            self.update_display()
            return

        if self.last_operator and self.last_operand is not None:
            left = self.current_decimal()
            result = self.perform_binary(left, self.last_operand, self.last_operator)
            if result is None:
                return

            self.expression_text = (
                f"{self.format_decimal(left)} {self.last_operator} {self.format_decimal(self.last_operand)} ="
            )
            self.current_entry = self.format_decimal(result)
            self.stored_operand = result
            self.reset_on_next_digit = True
            self.add_history_entry(self.expression_text, self.current_entry)
            self.update_display()

    def apply_unary(self, action: str) -> None:
        if self.error_state:
            return

        current_value = self.current_decimal()

        if action == "1/x":
            if current_value == 0:
                self.set_error("Não é possível dividir por zero")
                return
            result = Decimal("1") / current_value
            operation_text = f"1/({self.format_decimal(current_value)})"
        elif action == "x²":
            result = current_value * current_value
            operation_text = f"sqr({self.format_decimal(current_value)})"
        else:
            if current_value < 0:
                self.set_error("Raiz inválida para número negativo")
                return
            result = current_value.sqrt()
            operation_text = f"sqrt({self.format_decimal(current_value)})"

        self.current_entry = self.format_decimal(result)
        self.waiting_for_new_operand = False
        self.reset_on_next_digit = False

        if self.pending_operator and self.stored_operand is not None:
            self.expression_text = f"{self.format_decimal(self.stored_operand)} {self.pending_operator} {operation_text}"
        else:
            self.expression_text = operation_text

        self.add_history_entry(f"{self.expression_text} =", self.current_entry)
        self.update_display()

    def apply_percent(self) -> None:
        if self.error_state:
            return

        current_value = self.current_decimal()

        if self.pending_operator and self.stored_operand is not None:
            percent_value = (self.stored_operand * current_value) / Decimal("100")
            self.current_entry = self.format_decimal(percent_value)
            self.expression_text = (
                f"{self.format_decimal(self.stored_operand)} {self.pending_operator} "
                f"{self.format_decimal(percent_value)}"
            )
            self.waiting_for_new_operand = False
        else:
            percent_value = current_value / Decimal("100")
            self.current_entry = self.format_decimal(percent_value)
            self.expression_text = f"{self.format_decimal(current_value)}%"

        self.reset_on_next_digit = False
        self.update_display()

    def handle_memory(self, action: str) -> None:
        if self.error_state:
            return

        current_value = self.current_decimal()

        if action == "MC":
            self.memory_value = Decimal("0")
            self.memory_has_value = False
        elif action == "MR":
            if not self.memory_has_value:
                return
            self.current_entry = self.format_decimal(self.memory_value)
            self.waiting_for_new_operand = False
            self.reset_on_next_digit = False
        elif action == "MS":
            self.memory_value = current_value
            self.memory_has_value = True
        elif action == "M+":
            if not self.memory_has_value:
                self.memory_value = Decimal("0")
            self.memory_value += current_value
            self.memory_has_value = True
        elif action == "M-":
            if not self.memory_has_value:
                self.memory_value = Decimal("0")
            self.memory_value -= current_value
            self.memory_has_value = True

        self.update_display()

    def perform_binary(self, left: Decimal, right: Decimal, operator: str) -> Decimal | None:
        try:
            if operator == "+":
                return left + right
            if operator == "−":
                return left - right
            if operator == "×":
                return left * right
            if operator == "÷":
                if right == 0:
                    self.set_error("Não é possível dividir por zero")
                    return None
                return left / right
        except InvalidOperation:
            self.set_error("Operação inválida")
            return None

        return None

    def current_decimal(self) -> Decimal:
        try:
            return Decimal(self.current_entry)
        except InvalidOperation:
            self.set_error("Valor inválido")
            return Decimal("0")

    def format_decimal(self, value: Decimal) -> str:
        if value == 0:
            return "0"

        normalized = value.normalize()
        if normalized == normalized.to_integral():
            text = format(normalized.quantize(Decimal("1")), "f")
        else:
            text = format(normalized, "f").rstrip("0").rstrip(".")

        if text in {"-0", ""}:
            text = "0"

        visible_digits = text.replace("-", "").replace(".", "")
        if len(visible_digits) > 16:
            scientific = format(value.normalize(), ".10E")
            mantissa, exponent = scientific.split("E")
            mantissa = mantissa.rstrip("0").rstrip(".")
            exponent = exponent.replace("+", "")
            return f"{mantissa}e{exponent}"

        return text

    def set_error(self, message: str) -> None:
        self.current_entry = message
        self.expression_text = ""
        self.stored_operand = None
        self.pending_operator = None
        self.last_operator = None
        self.last_operand = None
        self.waiting_for_new_operand = False
        self.reset_on_next_digit = True
        self.error_state = True
        self.update_display()

    def add_history_entry(self, expression: str, result: str) -> None:
        if not expression.strip() or not result.strip() or self.error_state:
            return

        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, {"expression": expression, "result": result})

        widget = HistoryEntryWidget(expression, result)
        item.setSizeHint(widget.sizeHint())

        self.history_list.insertItem(0, item)
        self.history_list.setItemWidget(item, widget)

        while self.history_list.count() > 30:
            self.history_list.takeItem(self.history_list.count() - 1)

        self.update_history_state()

    def load_history_item(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(data, dict):
            return

        result = data.get("result", "0")
        expression = data.get("expression", "")

        self.current_entry = result
        self.expression_text = expression
        self.stored_operand = self.current_decimal()
        self.pending_operator = None
        self.last_operator = None
        self.last_operand = None
        self.waiting_for_new_operand = False
        self.reset_on_next_digit = True
        self.error_state = False
        self.update_display()

    def clear_history(self) -> None:
        self.history_list.clear()
        self.update_history_state()

    def update_history_state(self) -> None:
        has_history = self.history_list.count() > 0
        self.empty_history_label.setVisible(not has_history)
        self.history_list.setVisible(has_history)
        self.clear_history_button.setEnabled(has_history)

    def toggle_history(self) -> None:
        show_history = self.history_toggle_button.isChecked()
        self.history_frame.setVisible(show_history)
        target_width = self.expanded_width if show_history else self.compact_width
        self.resize(target_width, self.height())

    def update_display(self) -> None:
        self.expression_label.setText(self.expression_text)
        self.result_label.setText(self.current_entry)
        self.memory_indicator_label.setText("M" if self.memory_has_value else "")

        font_size = 34
        if len(self.current_entry) > 14:
            font_size = 26
        if len(self.current_entry) > 22:
            font_size = 20

        result_font = self.result_label.font()
        result_font.setPointSize(font_size)
        self.result_label.setFont(result_font)

        for name in ("MC", "MR"):
            self.memory_buttons[name].setEnabled(self.memory_has_value)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        text = event.text()

        if text.isdigit():
            self.input_digit(text)
            return

        if text in {"+", "-", "*", "/"}:
            key_map = {
                "+": "+",
                "-": "−",
                "*": "×",
                "/": "÷",
            }
            self.select_operator(key_map[text])
            return

        if text in {".", ","}:
            self.input_decimal()
            return

        if text == "%":
            self.apply_percent()
            return

        key = event.key()

        if key in {Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Equal}:
            self.calculate_result()
        elif key == Qt.Key.Key_Backspace:
            self.backspace()
        elif key == Qt.Key.Key_Escape:
            self.clear_all()
        elif key == Qt.Key.Key_Delete:
            self.clear_entry()
        elif key == Qt.Key.Key_F9:
            self.toggle_sign()
        else:
            super().keyPressEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = CalculatorWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
