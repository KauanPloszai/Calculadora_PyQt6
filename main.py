from __future__ import annotations

import sys
from decimal import Decimal, InvalidOperation, getcontext

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


getcontext().prec = 28


class CalculatorButton(QPushButton):
    def __init__(self, text: str, role: str, min_height: int = 66) -> None:
        super().__init__(text)
        self.setObjectName(f"{role}Button")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(min_height)


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

        self.expression_label: QLabel
        self.result_label: QLabel
        self.memory_indicator_label: QLabel

        self.setWindowTitle("Calculadora")
        self.setMinimumSize(420, 720)
        self.resize(430, 760)

        self.build_ui()
        self.update_display()

    def build_ui(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f3f3f3;
            }
            QLabel {
                color: #1f1f1f;
            }
            QFrame#displayFrame {
                background-color: #fbfbfb;
                border: 1px solid #e4e4e4;
                border-radius: 20px;
            }
            QPushButton {
                border-radius: 16px;
                border: 1px solid #dadada;
                font-size: 20px;
                color: #1f1f1f;
            }
            QPushButton#numberButton {
                background-color: #ffffff;
            }
            QPushButton#numberButton:hover {
                background-color: #f5f5f5;
            }
            QPushButton#numberButton:pressed {
                background-color: #ececec;
            }
            QPushButton#actionButton,
            QPushButton#operatorButton {
                background-color: #f0f0f0;
            }
            QPushButton#actionButton:hover,
            QPushButton#operatorButton:hover {
                background-color: #e8e8e8;
            }
            QPushButton#actionButton:pressed,
            QPushButton#operatorButton:pressed {
                background-color: #dddddd;
            }
            QPushButton#equalButton {
                background-color: #8fb9ff;
                border-color: #7eaefb;
                color: #0b1f44;
                font-weight: 600;
            }
            QPushButton#equalButton:hover {
                background-color: #84b1ff;
            }
            QPushButton#equalButton:pressed {
                background-color: #76a6fc;
            }
            QPushButton#memoryButton {
                background-color: transparent;
                border: none;
                color: #505050;
                font-size: 15px;
                padding: 6px 0;
            }
            QPushButton#memoryButton:hover {
                background-color: #e9e9e9;
                border-radius: 10px;
            }
            QPushButton#memoryButton:disabled {
                color: #b0b0b0;
            }
            """
        )

        root = QWidget()
        root.setFont(QFont("Segoe UI", 11))
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 0, 4, 0)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title_label = QLabel("Calculadora")
        title_font = QFont("Segoe UI Semibold", 11)
        title_label.setFont(title_font)

        mode_label = QLabel("Padrão")
        mode_font = QFont("Segoe UI Semibold", 22)
        mode_label.setFont(mode_font)

        title_box.addWidget(title_label)
        title_box.addWidget(mode_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        hint_label = QLabel("F9 alterna sinal")
        hint_label.setStyleSheet("color: #707070; font-size: 12px;")
        header_layout.addWidget(hint_label)
        main_layout.addLayout(header_layout)

        display_frame = QFrame()
        display_frame.setObjectName("displayFrame")

        display_layout = QVBoxLayout(display_frame)
        display_layout.setContentsMargins(18, 18, 18, 18)
        display_layout.setSpacing(10)

        expression_row = QHBoxLayout()
        expression_row.setSpacing(8)

        self.memory_indicator_label = QLabel("")
        self.memory_indicator_label.setStyleSheet("color: #6e6e6e; font-size: 14px;")
        self.memory_indicator_label.setFixedWidth(18)

        self.expression_label = QLabel("")
        self.expression_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.expression_label.setStyleSheet("color: #707070; font-size: 15px;")

        expression_row.addWidget(self.memory_indicator_label)
        expression_row.addWidget(self.expression_label, 1)

        self.result_label = QLabel("0")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        result_font = QFont("Segoe UI Semibold", 34)
        self.result_label.setFont(result_font)

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
                role = self.button_role(label)
                button = CalculatorButton(label, role)
                button.clicked.connect(lambda checked=False, action=label: self.handle_action(action))
                grid_layout.addWidget(button, row_index, column_index)

        main_layout.addLayout(grid_layout)

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
