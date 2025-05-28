import flet as ft
from datetime import datetime
import sqlite3
import os


# Инициализация базы данных
def init_db():
    if not os.path.exists('patients.db'):
        conn = sqlite3.connect('patients.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                age TEXT,
                symptoms TEXT,
                photo TEXT,
                pain_area TEXT,
                status TEXT,
                date TEXT,
                diagnosis TEXT,
                treatment TEXT,
                notes TEXT
            )
        ''')
        conn.commit()
        conn.close()


# Начальные данные пациентов
def init_sample_data():
    conn = sqlite3.connect('patients.db')
    cursor = conn.cursor()

    # Проверяем, есть ли уже данные в таблице
    cursor.execute("SELECT COUNT(*) FROM patients")
    count = cursor.fetchone()[0]

    if count == 0:
        sample_data = [
            (
                "Иванов Иван Иванович",
                "35 лет",
                "Боль в горле, заложенность носа, температура 38.9, слабость",
                None,
                "Горло, нос",
                "Новый",
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                "",
                "",
                ""
            ),
            (
                "Петрова Светлана Кирриловна",
                "35 лет",
                "Головные боли, ощущение холода, температура 37.1, бессонница",
                None,
                "Голова",
                "Новый",
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                "",
                "",
                ""
            ),
            (
                "Сидоров Алексей Владимирович",
                "46 лет",
                "Боль в груди, мышечная боль, температура 36.4, слабость",
                "https://upload.wikimedia.org/wikipedia/commons/d/db/Chest.jpg",
                "мышцы",
                "Новый",
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                "",
                "",
                ""
            )
        ]

        cursor.executemany('''
            INSERT INTO patients (name, age, symptoms, photo, pain_area, status, date, diagnosis, treatment, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_data)
        conn.commit()

    conn.close()


# Инициализируем базу данных
init_db()
init_sample_data()

# Текущий выбранный пациент
current_patient_index = None


def main(page: ft.Page):
    page.title = "Медицинская система для врачей"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800
    page.padding = 20

    # Элементы интерфейса
    patient_list = ft.ListView(expand=True, spacing=10)
    patient_details = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    status_dropdown = ft.Dropdown()
    diagnosis_field = ft.TextField(label="Диагноз", multiline=True, min_lines=3)
    treatment_field = ft.TextField(label="Лечение", multiline=True, min_lines=3)
    notes_field = ft.TextField(label="Заметки", multiline=True, min_lines=2)
    patient_image = ft.Image(width=300, height=200, fit=ft.ImageFit.CONTAIN)

    # Статусы
    statuses = ["Новый", "В работе", "Ожидание анализов", "Назначено лечение", "Закрыто"]
    status_dropdown.options = [ft.dropdown.Option(s) for s in statuses]

    def load_patients():
        patient_list.controls.clear()
        conn = sqlite3.connect('patients.db')
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, name, age, status, date FROM patients ORDER BY status = 'Новый' DESC, date DESC")
        patients = cursor.fetchall()
        conn.close()

        for patient in patients:
            rowid, name, age, status, date = patient
            patient_list.controls.append(
                ft.ListTile(
                    title=ft.Text(name),
                    subtitle=ft.Text(f"{age} | {status} | {date}"),
                    leading=ft.Icon(ft.Icons.PERSON),
                    on_click=lambda e, rowid=rowid: select_patient(rowid),
                    bgcolor=ft.Colors.BLUE_50 if status == "Новый" else None
                )
            )
        page.update()

    def select_patient(rowid):
        global current_patient_index
        current_patient_index = rowid

        conn = sqlite3.connect('patients.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE rowid=?", (rowid,))
        patient = cursor.fetchone()
        conn.close()

        if patient:
            _, name, age, symptoms, photo, pain_area, status, date, diagnosis, treatment, notes = patient

            patient_details.controls = [
                ft.Text(f"Пациент: {name}", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(f"Возраст: {age}"),
                ft.Text(f"Дата обращения: {date}"),
                ft.Divider(),
                ft.Text("Симптомы:", weight=ft.FontWeight.BOLD),
                ft.Text(symptoms),
                ft.Text("Область боли:", weight=ft.FontWeight.BOLD),
                ft.Text(pain_area),
                ft.Divider(),
                ft.Text("Фото:", weight=ft.FontWeight.BOLD),
                patient_image,
                ft.Divider(),
                ft.Text("Диагностика:", weight=ft.FontWeight.BOLD),
                status_dropdown,
                diagnosis_field,
                ft.Text("Лечение:", weight=ft.FontWeight.BOLD),
                treatment_field,
                ft.Text("Заметки:", weight=ft.FontWeight.BOLD),
                notes_field,
                ft.Row([
                    ft.ElevatedButton("Сохранить", on_click=save_patient),
                    ft.ElevatedButton("Закрыть обращение", on_click=close_patient,
                                      visible=status == "Назначено лечение")
                ], spacing=10)
            ]

            status_dropdown.value = status
            diagnosis_field.value = diagnosis
            treatment_field.value = treatment
            notes_field.value = notes

            if photo:
                patient_image.src = photo
                patient_image.visible = True
            else:
                patient_image.visible = False

            page.update()

    def save_patient(e):
        if current_patient_index is not None:
            conn = sqlite3.connect('patients.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE patients 
                SET status=?, diagnosis=?, treatment=?, notes=?
                WHERE rowid=?
            ''', (
                status_dropdown.value,
                diagnosis_field.value,
                treatment_field.value,
                notes_field.value,
                current_patient_index
            ))
            conn.commit()
            conn.close()

            load_patients()
            page.snack_bar = ft.SnackBar(ft.Text("Данные сохранены!"))
            page.snack_bar.open = True
            page.update()

    def close_patient(e):
        if current_patient_index is not None:
            conn = sqlite3.connect('patients.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE patients 
                SET status=?
                WHERE rowid=?
            ''', ("Закрыто", current_patient_index))
            conn.commit()
            conn.close()

            load_patients()
            page.snack_bar = ft.SnackBar(ft.Text("Обращение закрыто!"))
            page.snack_bar.open = True
            page.update()

    # Инициализация интерфейса
    load_patients()

    page.add(
        ft.Row([
            ft.Column([
                ft.Text("Очередь пациентов", size=20, weight=ft.FontWeight.BOLD),
                patient_list
            ], width=300),
            ft.VerticalDivider(width=10),
            ft.Column([
                ft.Text("Карта пациента", size=20, weight=ft.FontWeight.BOLD),
                patient_details
            ], expand=True)
        ], expand=True)
    )


ft.app(target=main)
