import flet as ft
import datetime


class PatientChat:
    def __init__(self, patient_name):
        self.patient_name = patient_name
        self.messages = []
        self.chat_ui = ft.ListView(expand=True, spacing=10, auto_scroll=True)

    def add_message(self, sender, text):
        current_time = datetime.datetime.now().strftime("%H:%M")
        self.messages.append({
            "sender": sender,
            "text": text,
            "time": current_time
        })
        self.update_chat_ui()

    def update_chat_ui(self):
        self.chat_ui.controls.clear()
        for msg in self.messages:
            self.chat_ui.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"{msg['sender']} ({msg['time']})",
                                weight="bold", size=12),
                        ft.Text(msg['text'])
                    ]),
                    bgcolor=ft.Colors.BLUE_100 if msg['sender'] == "Вы" else ft.Colors.GREEN_100,
                    border_radius=10,
                    padding=10,
                    margin=5,
                    width=300,
                    alignment=ft.alignment.top_left if msg['sender'] == "Вы" else ft.alignment.top_right
                )
            )


def main(page: ft.Page):
    page.title = "Мед. Чат"
    page.theme_mode = ft.ThemeMode.LIGHT

    # Создаем пациентов и их чаты
    patients = {
        "Иванов И.И.": PatientChat("Иванов И.И."),
        "Петрова С.К.": PatientChat("Петрова С.К."),
        "Сидоров А.В.": PatientChat("Сидоров А.В.")
    }

    current_patient = None
    new_message = ft.TextField(hint_text="Сообщение...", expand=True)
    chat_column = ft.Column(controls=[ft.Text("Выберите пациента")], expand=True)

    def send_message(e):
        nonlocal current_patient
        if current_patient and new_message.value:
            patients[current_patient].add_message("Вы", new_message.value)
            new_message.value = ""
            page.update()

    def select_patient(e):
        nonlocal current_patient
        current_patient = e.control.text
        chat_column.controls.clear()
        chat_column.controls.append(patients[current_patient].chat_ui)
        page.update()

    # Создаем кнопки пациентов
    patient_buttons = [
        ft.ElevatedButton(
            text=name,
            on_click=select_patient,
            width=200,
            style=ft.ButtonStyle(
                padding=10,
                shape=ft.RoundedRectangleBorder(radius=10)
            )) for name in patients.keys()
    ]

    # Разметка страницы
    page.add(
        ft.Row([
            # Левая панель с пациентами
            ft.Column(
                [
                    ft.Text("Пациенты", size=20, weight="bold"),
                    *patient_buttons
                ],
                width=250,
                scroll=ft.ScrollMode.AUTO,
                alignment=ft.MainAxisAlignment.START
            ),

            # Правая часть с чатом
            ft.Column(
                [
                    ft.Text("Чат с пациентом", size=20, weight="bold"),
                    ft.Container(
                        content=chat_column,
                        border=ft.border.all(1),
                        border_radius=5,
                        padding=10,
                        expand=True
                    ),
                    ft.Row(
                        [
                            new_message,
                            ft.IconButton(
                                icon=ft.Icons.SEND,
                                on_click=send_message,
                                tooltip="Отправить"
                            )
                        ]
                    )
                ],
                expand=True
            )
        ], expand=True)
    )

ft.app(target=main)
