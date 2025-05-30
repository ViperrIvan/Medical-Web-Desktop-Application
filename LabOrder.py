import flet as ft
from datetime import datetime
import json
import os


class LabOrderApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_page()
        self.data_file = "lab_orders.json"
        self.patients = self.load_data()
        self.setup_ui()

    def setup_page(self):
        self.page.title = "LabOrder System"
        self.page.window_width = 1000
        self.page.window_height = 700
        self.page.scroll = "adaptive"

    def load_data(self):
        """Загружает данные из файла, если он существует"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_data(self):
        """Сохраняет данные в файл"""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.patients, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Ошибка сохранения данных: {e}")

    def setup_ui(self):
        # Список доступных анализов
        self.lab_tests = [
            "Общий анализ крови",
            "Биохимия крови",
            "Анализ мочи",
            "Гормоны щитовидной железы",
            "Глюкоза крови",
            "Липидный профиль"
        ]

        # Элементы формы
        self.patient_name = ft.TextField(label="ФИО пациента", width=400)
        self.patient_dob = ft.TextField(label="Дата рождения (ДД.ММ.ГГГГ)", width=200)
        self.doctor_name = ft.TextField(label="ФИО врача", width=400)
        self.department = ft.Dropdown(
            label="Отделение",
            options=[
                ft.dropdown.Option("Терапия"),
                ft.dropdown.Option("Хирургия"),
                ft.dropdown.Option("Кардиология"),
                ft.dropdown.Option("Неврология"),
                ft.dropdown.Option("Гинекология"),
            ],
            width=200
        )

        # Чекбоксы анализов
        self.tests_checkboxes = []
        for test in self.lab_tests:
            cb = ft.Checkbox(label=test, value=False)
            self.tests_checkboxes.append(cb)

        self.notes = ft.TextField(label="Примечания", multiline=True, min_lines=2, max_lines=4, width=600)

        # Выпадающий список для сортировки
        self.sort_by = ft.Dropdown(
            label="Сортировать по",
            options=[
                ft.dropdown.Option("Дате (новые сначала)"),
                ft.dropdown.Option("Дате (старые сначала)"),
                ft.dropdown.Option("ФИО пациента (А-Я)"),
                ft.dropdown.Option("ФИО пациента (Я-А)"),
                ft.dropdown.Option("Отделению"),
            ],
            width=200,
            on_change=self.sort_orders
        )

        # Таблица заказов
        self.orders_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("№")),
                ft.DataColumn(ft.Text("ФИО пациента")),
                ft.DataColumn(ft.Text("Дата заказа")),
                ft.DataColumn(ft.Text("Анализы")),
                ft.DataColumn(ft.Text("Отделение")),
                ft.DataColumn(ft.Text("Диагноз")),
                ft.DataColumn(ft.Text("Действия")),
            ],
            rows=self.create_table_rows(),
        )

        # Кнопки
        self.add_order_btn = ft.ElevatedButton("Добавить заказ", on_click=self.add_order)
        self.print_order_btn = ft.ElevatedButton("Печать последний", on_click=self.print_order)

        # Компоновка интерфейса
        form_column = ft.Column(
            [
                ft.Row([self.patient_name, self.patient_dob]),
                ft.Row([self.doctor_name, self.department]),
                ft.Text("Назначенные анализы:", size=16),
                ft.Column(self.tests_checkboxes, spacing=5),
                self.notes,
                ft.Row([
                    self.add_order_btn,
                    self.print_order_btn
                ], spacing=20)
            ],
            spacing=15
        )

        self.page.add(
            ft.Text("Система лабораторных заказов", size=24, weight="bold"),
            form_column,
            ft.Divider(),
            ft.Row([
                ft.Text("История заказов", size=20),
                self.sort_by
            ], alignment="spaceBetween"),
            ft.Container(self.orders_table, height=300)
        )

    def create_table_rows(self):
        """Создает строки таблицы из сохраненных данных"""
        rows = []
        for idx, order in enumerate(self.patients, 1):
            # Поле для ввода диагноза
            diagnosis_field = ft.TextField(
                value=order.get("diagnosis", ""),
                width=300,  # Увеличенное поле для диагноза
                on_change=lambda e, order_idx=idx - 1: self.update_diagnosis(e, order_idx),
                disabled=not order.get("tests_completed", False)
            )

            # Кнопка для отметки выполнения анализов
            complete_tests_btn = ft.ElevatedButton(
                "Анализы выполнены",
                on_click=lambda e, order_idx=idx - 1: self.mark_tests_completed(order_idx),
                disabled=order.get("tests_completed", False)
            )

            actions = ft.Row([complete_tests_btn], spacing=5)

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(idx))),
                        ft.DataCell(ft.Text(order["patient_name"])),
                        ft.DataCell(ft.Text(order["order_date"])),
                        ft.DataCell(ft.Text(", ".join(order["tests"]))),
                        ft.DataCell(ft.Text(order.get("department", ""))),
                        ft.DataCell(diagnosis_field),
                        ft.DataCell(actions),
                    ]
                )
            )
        return rows

    def update_diagnosis(self, e, order_idx):
        """Обновляет диагноз при изменении текста"""
        self.patients[order_idx]["diagnosis"] = e.control.value
        self.save_data()

    def mark_tests_completed(self, order_idx):
        """Отмечает анализы как выполненные"""
        self.patients[order_idx]["tests_completed"] = True
        self.save_data()
        self.orders_table.rows = self.create_table_rows()
        self.page.update()

    def sort_orders(self, e):
        """Сортирует заказы по выбранному критерию"""
        sort_option = self.sort_by.value

        if sort_option == "Дате (новые сначала)":
            self.patients.sort(key=lambda x: datetime.strptime(x["order_date"], "%d.%m.%Y %H:%M"), reverse=True)
        elif sort_option == "Дате (старые сначала)":
            self.patients.sort(key=lambda x: datetime.strptime(x["order_date"], "%d.%m.%Y %H:%M"))
        elif sort_option == "ФИО пациента (А-Я)":
            self.patients.sort(key=lambda x: x["patient_name"].lower())
        elif sort_option == "ФИО пациента (Я-А)":
            self.patients.sort(key=lambda x: x["patient_name"].lower(), reverse=True)
        elif sort_option == "Отделению":
            self.patients.sort(key=lambda x: x.get("department", ""))

        self.orders_table.rows = self.create_table_rows()
        self.page.update()

    def add_order(self, e):
        """Добавляет новый заказ"""
        if not self.patient_name.value:
            self.patient_name.error_text = "Введите ФИО пациента"
            self.page.update()
            return

        tests = [cb.label for cb in self.tests_checkboxes if cb.value]
        if not tests:
            self.tests_checkboxes[0].error_text = "Выберите хотя бы один анализ"
            self.page.update()
            return

        order_date = datetime.now().strftime("%d.%m.%Y %H:%M")
        order = {
            "patient_name": self.patient_name.value,
            "patient_dob": self.patient_dob.value,
            "doctor_name": self.doctor_name.value,
            "department": self.department.value,
            "tests": tests,
            "notes": self.notes.value,
            "order_date": order_date,
            "tests_completed": False,
            "diagnosis": ""
        }

        self.patients.append(order)
        self.save_data()

        # Обновляем таблицу
        self.orders_table.rows = self.create_table_rows()

        # Очищаем форму
        self.clear_form()
        self.page.update()

    def clear_form(self):
        """Очищает форму ввода"""
        self.patient_name.value = ""
        self.patient_dob.value = ""
        self.doctor_name.value = ""
        self.department.value = ""
        self.notes.value = ""
        for cb in self.tests_checkboxes:
            cb.value = False
        self.patient_name.error_text = None
        self.tests_checkboxes[0].error_text = None

    def print_order(self, e):
        """Показывает диалог с последним заказом"""
        if not self.patients:
            return

        last_order = self.patients[-1]

        print_content = [
            f"ЛАБОРАТОРНЫЙ ЗАКАЗ №{len(self.patients)}",
            f"Дата: {last_order['order_date']}",
            f"\nПациент: {last_order['patient_name']}",
            f"Дата рождения: {last_order['patient_dob']}",
            f"\nВрач: {last_order['doctor_name']}",
            f"Отделение: {last_order['department']}",
            f"\nНазначенные анализы:",
            *[f" - {test}" for test in last_order['tests']],
            f"\nСтатус анализов: {'Выполнены' if last_order.get('tests_completed', False) else 'Не выполнены'}",
            f"\nДиагноз: {last_order.get('diagnosis', 'Не указан')}",
            f"\nПримечания: {last_order['notes']}",
            f"\n\nДата и время забора: ________________________",
            f"\nФИО медсестры: _______________________________"
        ]

        dlg = ft.AlertDialog(
            title=ft.Text("Лабораторный заказ"),
            content=ft.Column(
                [ft.Text(line) for line in print_content],
                scroll="always",
                height=500,
                width=600
            ),
            actions=[
                ft.TextButton("Закрыть", on_click=lambda e: setattr(dlg, "open", False) or self.page.update()),
                ft.TextButton("Печать", on_click=lambda e: print("Печать заказа..."))
            ],
            actions_alignment="end"
        )

        self.page.dialog = dlg
        dlg.open = True
        self.page.update()


def main(page: ft.Page):
    app = LabOrderApp(page)


ft.app(target=main)
