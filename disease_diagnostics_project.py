import flet as ft
import sqlite3
import socket
import os
import json
import calendar
from datetime import datetime


user_ip = ""
current_patient_index = None
current_course_index = -1
current_chat_patient = None
start_date_value = ""
end_date_value = ""
courses = []
data_file = os.path.join(os.path.expanduser("~"), "Desktop", "курсы.xlsx")

# Данные для чатов
patients_chats = {
    "Иванов Иван Иванович": {"messages": [], "chat_ui": ft.ListView(expand=True, spacing=10, auto_scroll=True)},
    "Петрова Светлана Кирриловна": {"messages": [], "chat_ui": ft.ListView(expand=True, spacing=10, auto_scroll=True)},
    "Сидоров Алексей Владимирович": {"messages": [], "chat_ui": ft.ListView(expand=True, spacing=10, auto_scroll=True)}
}

# Данные для лабораторных заказов
lab_orders_file = "lab_orders.json"
lab_tests_list = [
    "Общий анализ крови",
    "Биохимия крови",
    "Анализ мочи",
    "Гормоны щитовидной железы",
    "Глюкоза крови",
    "Липидный профиль"
]

# Текущий выбранный пациент
current_patient_index = None


def get_user_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except:
        return "неизвестен"

def init_users_db():
    if os.path.exists('users.db'):
        os.remove('users.db')

    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE users
                 (ip TEXT, 
                  reg_date TEXT, 
                  last_name TEXT, 
                  first_name TEXT, 
                  middle_name TEXT, 
                  phone TEXT, 
                  password TEXT)''')
    conn.commit()
    conn.close()


def init_patients_db():
    conn = sqlite3.connect('patients.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
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

    # Создаем таблицу для связи пациентов и курсов лечения
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patient_courses (
            patient_id INTEGER,
            course_name TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')

    # Создаем таблицы для курсов лечения
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            start_date TEXT,
            end_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS course_tablets (
            course_id INTEGER,
            name TEXT,
            quantity TEXT,
            measure TEXT,
            time TEXT,
            comment TEXT,
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
    ''')

    conn.commit()
    conn.close()

def init_sample_data():
    conn = sqlite3.connect('patients.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM patients")
    count = cursor.fetchone()[0]

    if count == 0:
        sample_data = [
            (
                "Иванов Иван Иванович",
                "35 лет",
                "Боль в горле, заложенность носа, температура 38.9, слабость",
                None,
                "Горло, нос"
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


def add_chat_message(patient_name, sender, text):
    global patients_chats
    current_time = datetime.now().strftime("%H:%M")
    patients_chats[patient_name]["messages"].append({
        "sender": sender,
        "text": text,
        "time": current_time
    })
    update_chat_ui(patient_name)

def update_chat_ui(patient_name):
    global patients_chats
    chat_ui = patients_chats[patient_name]["chat_ui"]
    chat_ui.controls.clear()
    for msg in patients_chats[patient_name]["messages"]:
        chat_ui.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(f"{msg['sender']} ({msg['time']})", weight="bold", size=12),
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


def load_lab_orders():
    if os.path.exists(lab_orders_file):
        try:
            with open(lab_orders_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_lab_orders(orders):
    try:
        with open(lab_orders_file, "w", encoding="utf-8") as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"Ошибка сохранения данных: {e}")

def create_lab_order(patient_name, patient_dob, doctor_name, department, tests, notes):
    orders = load_lab_orders()
    order_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    order = {
        "patient_name": patient_name,
        "patient_dob": patient_dob,
        "doctor_name": doctor_name,
        "department": department,
        "tests": tests,
        "notes": notes,
        "order_date": order_date,
        "tests_completed": False,
        "diagnosis": ""
    }
    orders.append(order)
    save_lab_orders(orders)
    return order

def mark_lab_tests_completed(order_idx):
    orders = load_lab_orders()
    if 0 <= order_idx < len(orders):
        orders[order_idx]["tests_completed"] = True
        save_lab_orders(orders)

def update_lab_diagnosis(order_idx, diagnosis):
    orders = load_lab_orders()
    if 0 <= order_idx < len(orders):
        orders[order_idx]["diagnosis"] = diagnosis
        save_lab_orders(orders)

def get_lab_orders(sort_by=None):
    orders = load_lab_orders()

    if sort_by == "Дате (новые сначала)":
        orders.sort(key=lambda x: datetime.strptime(x["order_date"], "%d.%m.%Y %H:%M"), reverse=True)
    elif sort_by == "Дате (старые сначала)":
        orders.sort(key=lambda x: datetime.strptime(x["order_date"], "%d.%m.%Y %H:%M"))
    elif sort_by == "ФИО пациента (А-Я)":
        orders.sort(key=lambda x: x["patient_name"].lower())
    elif sort_by == "ФИО пациента (Я-А)":
        orders.sort(key=lambda x: x["patient_name"].lower(), reverse=True)
    elif sort_by == "Отделению":
        orders.sort(key=lambda x: x.get("department", ""))

    return orders


def load_courses_data():
    global courses
    courses = []
    conn = sqlite3.connect('patients.db')
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, name, start_date, end_date FROM courses")
        courses_data = cursor.fetchall()

        for course_id, name, start_date, end_date in courses_data:
            cursor.execute("SELECT name, quantity, measure, time, comment FROM course_tablets WHERE course_id=?",
                           (course_id,))
            tablets = cursor.fetchall()

            course_tablets = []
            for tab_name, quantity, measure, time, comment in tablets:
                course_tablets.append({
                    'name': tab_name,
                    'quantity': quantity,
                    'measure': measure,
                    'time': time,
                    'comment': comment
                })

            courses.append({
                'id': course_id,
                'name': name,
                'start_date': start_date,
                'end_date': end_date,
                'tablets': course_tablets
            })
    except sqlite3.Error as e:
        print(f"Ошибка при загрузке курсов: {e}")
    finally:
        conn.close()

def save_courses_data():
    conn = sqlite3.connect('patients.db')
    cursor = conn.cursor()

    try:
        # Удаляем старые данные
        cursor.execute("DELETE FROM course_tablets")
        cursor.execute("DELETE FROM courses")

        # Сохраняем новые данные
        for course in courses:
            cursor.execute(
                "INSERT INTO courses (name, start_date, end_date) VALUES (?, ?, ?)",
                (course['name'], course['start_date'], course['end_date'])
            )
            course_id = cursor.lastrowid

            for tablet in course['tablets']:
                cursor.execute(
                    "INSERT INTO course_tablets (course_id, name, quantity, measure, time, comment) VALUES (?, ?, ?, ?, ?, ?)",
                    (course_id, tablet['name'], tablet['quantity'], tablet['measure'], tablet['time'], tablet['comment'])
                )

        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении курсов: {e}")
    finally:
        conn.close()

def get_patient_courses(patient_id):
    """Получить курсы лечения для пациента"""
    conn = sqlite3.connect('patients.db')
    cursor = conn.cursor()
    cursor.execute("SELECT course_name FROM patient_courses WHERE patient_id=?", (patient_id,))
    patient_courses = [row[0] for row in cursor.fetchall()]
    conn.close()
    return patient_courses

def assign_course_to_patient(patient_id, course_name):
    """Назначить курс лечения пациенту"""
    conn = sqlite3.connect('patients.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO patient_courses (patient_id, course_name) VALUES (?, ?)", (patient_id, course_name))
    conn.commit()
    conn.close()

def remove_course_from_patient(patient_id, course_name):
    """Удалить курс лечения у пациента"""
    conn = sqlite3.connect('patients.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patient_courses WHERE patient_id=? AND course_name=?", (patient_id, course_name))
    conn.commit()
    conn.close()


def show_date_picker(page, callback):
    now = datetime.now()
    selected_day = now.day
    current_month = now.month
    current_year = now.year

    month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

    selected_date_display = ft.Text(
        value=f"Выбрано: {selected_day:02d}.{current_month:02d}.{current_year}",
        size=18,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE,
        text_align=ft.TextAlign.CENTER
    )

    header = ft.Text(
        value=f"{month_names[current_month - 1]} {current_year}",
        size=24,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
    )

    calendar_grid = ft.Column(spacing=10, alignment=ft.MainAxisAlignment.CENTER)

    def prev_month(e):
        nonlocal current_month, current_year
        current_month -= 1
        if current_month == 0:
            current_month = 12
            current_year -= 1
        header.value = f"{month_names[current_month - 1]} {current_year}"
        update_calendar()

    def next_month(e):
        nonlocal current_month, current_year
        current_month += 1
        if current_month == 13:
            current_month = 1
            current_year += 1
        header.value = f"{month_names[current_month - 1]} {current_year}"
        update_calendar()

    def select_day(day):
        nonlocal selected_day
        selected_day = day
        selected_date_display.value = f"Выбрано: {selected_day:02d}.{current_month:02d}.{current_year}"
        page.update()

    def select_date(e):
        callback(f"{selected_day:02d}.{current_month:02d}.{current_year}")

    def close_dialog(e):
        callback("")

    def update_calendar():
        calendar_grid.controls.clear()
        weekday_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        week_header = ft.Row(
            controls=[ft.Text(day, width=40, text_align=ft.TextAlign.CENTER)
                      for day in weekday_names],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        calendar_grid.controls.append(week_header)

        cal = calendar.monthcalendar(current_year, current_month)
        for week_days in cal:
            week_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER)
            for day in week_days:
                if day == 0:
                    week_row.controls.append(
                        ft.Container(width=40, height=40)
                    )
                    continue
                day_btn = ft.ElevatedButton(
                    text=str(day),
                    width=40,
                    height=40,
                    bgcolor=ft.Colors.BLUE_100 if day == selected_day else None,
                    on_click=lambda e, d=day: select_day(d)
                )
                week_row.controls.append(day_btn)
            calendar_grid.controls.append(week_row)
        page.update()

    update_calendar()

    nav_buttons = ft.Row(
        controls=[
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=prev_month),
            ft.IconButton(ft.Icons.ARROW_FORWARD, on_click=next_month),
            ft.ElevatedButton("Выбрать", on_click=select_date),
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    page.clean()
    page.add(
        ft.Column(
            [
                header,
                nav_buttons,
                selected_date_display,
                ft.Container(
                    content=calendar_grid,
                    alignment=ft.alignment.center
                ),
                ft.ElevatedButton("Назад", on_click=close_dialog),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
        )
    )

def show_courses_ui(page):
    page.clean()
    load_courses_data()

    course_buttons = []
    for i, course in enumerate(courses):
        start_date = course['start_date'] if course['start_date'] else "не указана"
        end_date = course['end_date'] if course['end_date'] else "не указана"

        course_info = ft.Column([
            ft.Text(course['name'], size=18, weight=ft.FontWeight.BOLD),
            ft.Text(f"Даты: {start_date} - {end_date}", size=14, color=ft.Colors.GREY_600)
        ], spacing=5)

        course_buttons.append(
            ft.ElevatedButton(
                content=course_info,
                style=ft.ButtonStyle(padding=20),
                on_click=lambda e, idx=i: show_course_details(page, idx)
            )
        )

    page.add(
        ft.Column([
            ft.Text("Курсы лечения", size=25),
            ft.Column(
                course_buttons,
                spacing=10
            ),
            ft.ElevatedButton(
                "Создать новый курс",
                icon=ft.Icons.ADD,
                on_click=lambda e: create_course_ui(page)
            ),
            ft.ElevatedButton(
                "Назад",
                on_click=lambda e: show_doctor_interface(page)
            )
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
    )

def create_course_ui(page, start_date="", end_date=""):
    global current_course_index, start_date_value, end_date_value
    current_course_index = -1
    page.clean()

    name_field = ft.TextField(label="Название курса", width=400)

    if start_date:
        start_date_value = start_date
    if end_date:
        end_date_value = end_date

    start_date_display = ft.Text(
        f"Дата начала: {start_date_value if start_date_value else 'не выбрана'}",
        size=16
    )
    end_date_display = ft.Text(
        f"Дата окончания: {end_date_value if end_date_value else 'не выбрана'}",
        size=16
    )

    def set_start_date(date_str):
        global start_date_value
        start_date_value = date_str
        create_course_ui(page, start_date=date_str, end_date=end_date_value)

    def set_end_date(date_str):
        global end_date_value
        end_date_value = date_str
        create_course_ui(page, start_date=start_date_value, end_date=date_str)

    def save_course(e):
        global start_date_value, end_date_value
        if name_field.value:
            new_course = {
                'name': name_field.value,
                'start_date': start_date_value,
                'end_date': end_date_value,
                'tablets': []
            }
            courses.append(new_course)
            save_courses_data()
            start_date_value = ""
            end_date_value = ""
            show_courses_ui(page)

    page.add(
        ft.Column([
            ft.Text("Новый курс лечения", size=20),
            name_field,

            ft.Column([
                start_date_display,
                ft.ElevatedButton(
                    "Выбрать дату начала",
                    on_click=lambda e: show_date_picker(page, set_start_date)
                ),
            ], spacing=5),

            ft.Column([
                end_date_display,
                ft.ElevatedButton(
                    "Выбрать дату окончания",
                    on_click=lambda e: show_date_picker(page, set_end_date)
                ),
            ], spacing=5),

            ft.Row([
                ft.ElevatedButton("Сохранить", on_click=save_course),
                ft.ElevatedButton("Отмена", on_click=lambda e: show_courses_ui(page))
            ], spacing=20)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
    )

def show_course_details(page, course_index):
    global current_course_index
    current_course_index = course_index
    course = courses[course_index]

    def add_tablet(e):
        name_field = ft.TextField(label="Название препарата", width=400)
        quantity_field = ft.TextField(
            label="Количество",
            width=400,
            input_filter=ft.NumbersOnlyInputFilter()
        )
        measure_field = ft.TextField(label="Единица измерения (мг, таблетки и т.д.)", width=400)
        time_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(t) for t in ["Утро", "Обед", "Вечер", "Перед сном"]],
            label="Стандартное время",
            width=400,
            editable=True
        )
        comment_field = ft.TextField(label="Комментарий (например: после еды)", width=400)

        def save_tablet(e):
            course['tablets'].append({
                'name': name_field.value,
                'quantity': quantity_field.value,
                'measure': measure_field.value,
                'time': time_dropdown.value,
                'comment': comment_field.value
            })
            save_courses_data()
            show_course_details(page, course_index)
            page.update()

        page.clean()
        page.add(
            ft.Column([
                ft.Text(f"Добавление в курс: {course['name']}", size=20),
                name_field,
                quantity_field,
                measure_field,
                time_dropdown,
                comment_field,
                ft.Row([
                    ft.ElevatedButton("Сохранить", on_click=save_tablet),
                    ft.ElevatedButton("Назад", on_click=lambda e: show_course_details(page, course_index)),
                ], spacing=20)
            ], spacing=15)
        )

    page.clean()

    dates_info = ft.Text(
        f"Даты курса: {course['start_date'] if course['start_date'] else 'не указана'} - {course['end_date'] if course['end_date'] else 'не указана'}",
        size=16,
        color=ft.Colors.GREY_600
    )

    tablets_list = ft.Column(
        [ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"💊 {t['name']} {t['quantity']}{t['measure']}",
                            weight=ft.FontWeight.BOLD),
                    ft.Text(f"⏰ {t['time']} | {t['comment']}",
                            color=ft.Colors.GREY_600)
                ], spacing=5),
                padding=15,
                width=400
            )
        ) for t in course['tablets']],
        spacing=10
    )

    page.add(
        ft.Column([
            ft.Row([
                ft.Text(f"Курс: {course['name']}", size=20),
                ft.ElevatedButton("Назад", on_click=lambda e: show_courses_ui(page))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            dates_info,
            ft.ElevatedButton(
                "Добавить препарат",
                icon=ft.Icons.ADD,
                on_click=add_tablet
            ),
            tablets_list
        ], spacing=20)
    )


def show_start(page):
    page.clean()
    page.add(
        ft.Column([
            ft.Text("Медицинская система", size=24),
            ft.ElevatedButton("Регистрация", width=400, on_click=lambda e: show_reg_name(page)),
            ft.ElevatedButton("Вход", width=400, on_click=lambda e: show_login(page)),
            ft.ElevatedButton("Войти как врач", width=400, on_click=lambda e: show_login2(page))
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
    )

def show_reg_name(page):
    page.clean()
    surname = ft.TextField(label="Фамилия", width=400, autofocus=True)
    name = ft.TextField(label="Имя", width=400)
    middle_name = ft.TextField(label="Отчество", width=400)

    page.add(
        ft.Column([
            ft.Text("Регистрация", size=20),
            surname, name, middle_name,
            ft.Row([
                ft.ElevatedButton("Назад", on_click=lambda e: show_start(page)),
                ft.ElevatedButton("Далее", on_click=lambda e: show_reg_contact(
                    page, surname.value, name.value, middle_name.value))
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

def show_reg_contact(page, surname, name, middle_name):
    page.clean()
    phone = ft.TextField(
        label="Телефон (79991234567)",
        width=400,
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string="")
    )
    password = ft.TextField(
        label="Пароль",
        width=400,
        password=True,
        can_reveal_password=True
    )

    page.add(
        ft.Column([
            ft.Text(f"{surname} {name} {middle_name}", size=16),
            phone, password,
            ft.Row([
                ft.ElevatedButton("Назад", on_click=lambda e: show_reg_name(page)),
                ft.ElevatedButton("Зарегистрировать", on_click=lambda e: register_user(
                    page, surname, name, middle_name, phone.value, password.value))
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

def register_user(page, surname, name, middle_name, phone, password):
    if not phone or len(phone) != 11:
        show_reg_contact(page, surname, name, middle_name)
        return

    conn = sqlite3.connect('users.db', check_same_thread=False)
    try:
        c = conn.cursor()
        c.execute('''INSERT INTO users 
                    (ip, reg_date, last_name, first_name, middle_name, phone, password) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (user_ip,
                   datetime.now().strftime("%d.%m.%Y %H:%M"),
                   surname,
                   name,
                   middle_name,
                   phone,
                   password))
        conn.commit()
        show_success(page, name)
    except Exception as e:
        print(f"Ошибка базы данных: {e}")
        page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка: {str(e)}"))
        page.snack_bar.open = True
        page.update()
    finally:
        conn.close()

def show_success(page, name):
    page.clean()
    page.add(
        ft.Column([
            ft.Icon(ft.Icons.CHECK, color="green", size=50),
            ft.Text(f"{name}, регистрация успешна!", size=20),
            ft.ElevatedButton("OK", width=200, on_click=lambda e: show_start(page))
        ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

def show_login(page):
    page.clean()
    phone = ft.TextField(label="Телефон", width=400)
    password = ft.TextField(
        label="Пароль",
        width=400,
        password=True,
        can_reveal_password=True
    )

    page.add(
        ft.Column([
            ft.Text("Вход", size=20),
            phone, password,
            ft.Row([
                ft.ElevatedButton("Назад", on_click=lambda e: show_start(page)),
                ft.ElevatedButton("Войти", on_click=lambda e: login_user(page, phone.value, password.value))
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

def show_login2(page):
    page.clean()
    phone = ft.TextField(label="Телефон", width=400)
    password = ft.TextField(
        label="Пароль",
        width=400,
        password=True,
        can_reveal_password=True
    )

    def authenticate(e):
        # Проверяем учетные данные
        conn = sqlite3.connect('users.db', check_same_thread=False)
        try:
            c = conn.cursor()
            c.execute('''SELECT * FROM users 
                        WHERE phone=? AND password=?''',
                      (phone.value, password.value))
            user = c.fetchone()
            conn.close()

            if user:
                show_doctor_interface(page)
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Неверный телефон или пароль"))
                page.snack_bar.open = True
                page.update()
        except Exception as e:
            print(f"Ошибка базы данных: {e}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка: {str(e)}"))
            page.snack_bar.open = True
            page.update()

    page.add(
        ft.Column([
            ft.Text("Вход", size=20),
            phone, password,
            ft.Row([
                ft.ElevatedButton("Назад", on_click=lambda e: show_start(page)),
                ft.ElevatedButton("Войти", on_click=authenticate)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

def login_user(page, phone, password):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE phone=? AND password=?", (phone, password))
        user = c.fetchone()

        if not user:
            show_login(page)
            return

        show_profile(page, user)
    except Exception as e:
        print(f"Ошибка базы данных: {e}")
        page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка: {str(e)}"))
        page.snack_bar.open = True
        page.update()
    finally:
        conn.close()

def show_profile(page, user):
    page.clean()
    page.add(
        ft.Column([
            ft.Text("Профиль", size=20),
            ft.Text(f"{user[2]} {user[3]} {user[4]}"),
            ft.Text(f"Телефон: {user[5]}"),
            ft.Text(f"Дата регистрации: {user[1]}"),
            ft.ElevatedButton("Выйти", width=200, on_click=lambda e: show_start(page))
        ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )


def show_doctor_interface(page):
    page.clean()
    load_courses_data()

    # Создаем элементы для интерфейса врача
    patient_list = ft.ListView(expand=True, spacing=10)
    patient_details = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    status_dropdown = ft.Dropdown()
    diagnosis_field = ft.TextField(label="Диагноз", multiline=True, min_lines=3)
    treatment_field = ft.TextField(label="Лечение", multiline=True, min_lines=3)
    notes_field = ft.TextField(label="Заметки", multiline=True, min_lines=2)
    patient_image = ft.Image(width=300, height=200, fit=ft.ImageFit.CONTAIN)
    assigned_courses_column = ft.Column([])

    available_courses_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(course['name']) for course in courses],
        label="Доступные курсы",
        width=300
    )

    # Статусы пациентов
    statuses = ["Новый", "В работе", "Ожидание анализов", "Назначено лечение", "Закрыто"]
    status_dropdown.options = [ft.dropdown.Option(s) for s in statuses]

    # Загружаем пациентов при открытии интерфейса
    def load_patients():
        conn = sqlite3.connect('patients.db')
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, name, age, status, date FROM patients ORDER BY status = 'Новый' DESC, date DESC")
        patients = cursor.fetchall()
        conn.close()

        patient_list.controls.clear()
        for rowid, name, age, status, date in patients:
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

    # Элементы для чата
    global current_chat_patient
    current_chat_patient = None
    new_message_field = ft.TextField(hint_text="Сообщение...", expand=True)
    chat_column = ft.Column(controls=[ft.Text("Выберите пациента для чата")], expand=True)

    # Элементы для лабораторных заказов
    lab_patient_name = ft.TextField(label="ФИО пациента", width=400)
    lab_patient_dob = ft.TextField(label="Дата рождения (ДД.ММ.ГГГГ)", width=200)
    lab_doctor_name = ft.TextField(label="ФИО врача", width=400)
    lab_department = ft.Dropdown(
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
    lab_tests_checkboxes = [ft.Checkbox(label=test, value=False) for test in lab_tests_list]
    lab_notes = ft.TextField(label="Примечания", multiline=True, min_lines=2, max_lines=4, width=600)
    lab_sort_by = ft.Dropdown(
        label="Сортировать по",
        options=[
            ft.dropdown.Option("Дате (новые сначала)"),
            ft.dropdown.Option("Дате (старые сначала)"),
            ft.dropdown.Option("ФИО пациента (А-Я)"),
            ft.dropdown.Option("ФИО пациента (Я-А)"),
            ft.dropdown.Option("Отделению"),
        ],
        width=200,
    )
    lab_orders_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("№")),
            ft.DataColumn(ft.Text("ФИО пациента")),
            ft.DataColumn(ft.Text("Дата заказа")),
            ft.DataColumn(ft.Text("Анализы")),
            ft.DataColumn(ft.Text("Отделение")),
            ft.DataColumn(ft.Text("Диагноз")),
            ft.DataColumn(ft.Text("Действия")),
        ],
    )

    def select_patient(rowid):
        global current_patient_index
        current_patient_index = rowid
        conn = sqlite3.connect('patients.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients WHERE rowid=?", (rowid,))
        patient = cursor.fetchone()

        # Получаем назначенные курсы
        cursor.execute("SELECT course_name FROM patient_courses WHERE patient_id=?", (rowid,))
        assigned_courses = [row[0] for row in cursor.fetchall()]
        conn.close()

        if patient:
            _, name, age, symptoms, photo, pain_area, status, date, diagnosis, treatment, notes = patient

            # Обновляем список назначенных курсов
            assigned_courses_column.controls.clear()
            for course_name in assigned_courses:
                assigned_courses_column.controls.append(
                    ft.Row([
                        ft.Text(course_name),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            on_click=lambda e, c=course_name: remove_course_from_patient(rowid, c))
                    ]))

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
                ft.Divider(),
                ft.Text("Назначенные курсы лечения:", weight=ft.FontWeight.BOLD),
                assigned_courses_column,
                ft.Row([
                    available_courses_dropdown,
                    ft.ElevatedButton(
                        "Назначить курс",
                        on_click=lambda e: assign_course(rowid))
                ]),
                ft.Row([
                    ft.ElevatedButton("Сохранить", on_click=lambda e: save_patient(page)),
                    ft.ElevatedButton("Закрыть обращение", on_click=lambda e: close_patient(page))
                ],
                    spacing=10)
            ]

            status_dropdown.value = status
            diagnosis_field.value = diagnosis
            treatment_field.value = treatment
            notes_field.value = notes

            # Обновляем список доступных курсов
            available_courses_dropdown.options = [
                ft.dropdown.Option(course['name'])
                for course in courses
                if course['name'] not in assigned_courses
            ]

            if photo:
                patient_image.src = photo
                patient_image.visible = True
            else:
                patient_image.visible = False

        page.update()

    def save_patient(page):
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

            # Перезагружаем данные пациента для обновления интерфейса
            select_patient(current_patient_index)

            # ОБНОВЛЯЕМ СПИСОК ПАЦИЕНТОВ
            load_patients()

            page.snack_bar = ft.SnackBar(ft.Text("Данные сохранены!"))
            page.snack_bar.open = True
            page.update()

    def close_patient(page):
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

            # Обновляем список пациентов
            load_patients()

            # Сбрасываем детали пациента
            patient_details.controls = []
            page.update()

            page.snack_bar = ft.SnackBar(ft.Text("Обращение закрыто!"))
            page.snack_bar.open = True
            page.update()

    def assign_course(patient_id):
        """Назначить выбранный курс пациенту"""
        if available_courses_dropdown.value:
            assign_course_to_patient(patient_id, available_courses_dropdown.value)
            select_patient(patient_id)  # Обновляем интерфейс

    def select_chat_patient(patient_name):
        global current_chat_patient
        current_chat_patient = patient_name
        chat_column.controls.clear()
        chat_column.controls.append(patients_chats[patient_name]["chat_ui"])
        page.update()

    def send_message(e):
        global current_chat_patient
        if current_chat_patient and new_message_field.value:
            add_chat_message(current_chat_patient, "Вы", new_message_field.value)
            new_message_field.value = ""
            page.update()

    def create_chat_tab():
        patient_buttons = [
            ft.ElevatedButton(
                text=name,
                on_click=lambda e, name=name: select_chat_patient(name),
                width=200,
                style=ft.ButtonStyle(
                    padding=10,
                    shape=ft.RoundedRectangleBorder(radius=10)
                ))
            for name in patients_chats.keys()
        ]

        return ft.Row([
            ft.Column(
                [
                    ft.Text("Пациенты", size=20, weight="bold"),
                    *patient_buttons
                ],
                width=250,
                scroll=ft.ScrollMode.AUTO,
                alignment=ft.MainAxisAlignment.START
            ),
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
                            new_message_field,
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

    def create_lab_orders_tab():
        """Создает вкладку для лабораторных заказов"""
        form_column = ft.Column(
            [
                ft.Row([lab_patient_name, lab_patient_dob]),
                ft.Row([lab_doctor_name, lab_department]),
                ft.Text("Назначенные анализы:", size=16),
                ft.Column(lab_tests_checkboxes, spacing=5),
                lab_notes,
                ft.Row([
                    ft.ElevatedButton("Добавить заказ", on_click=lambda e: add_lab_order(page)),
                    ft.ElevatedButton("Печать последний", on_click=lambda e: print_lab_order(page))
                ], spacing=20)
            ],
            spacing=15
        )

        return ft.Column(
            [
                ft.Text("Система лабораторных заказов", size=24, weight="bold"),
                form_column,
                ft.Divider(),
                ft.Row([
                    ft.Text("История заказов", size=20),
                    lab_sort_by
                ], alignment="spaceBetween"),
                ft.Container(lab_orders_table, height=300)
            ],
            scroll=ft.ScrollMode.AUTO
        )

    def add_lab_order(page):
        """Добавляет новый лабораторный заказ"""
        if not lab_patient_name.value:
            lab_patient_name.error_text = "Введите ФИО пациента"
            page.update()
            return

        tests = [cb.label for cb in lab_tests_checkboxes if cb.value]
        if not tests:
            lab_tests_checkboxes[0].error_text = "Выберите хотя бы один анализ"
            page.update()
            return

        create_lab_order(
            lab_patient_name.value,
            lab_patient_dob.value,
            lab_doctor_name.value,
            lab_department.value,
            tests,
            lab_notes.value
        )

        # Обновляем таблицу
        lab_orders_table.rows = create_lab_table_rows()

        # Очищаем форму
        clear_lab_form()
        page.update()

    def clear_lab_form():
        """Очищает форму лабораторного заказа"""
        lab_patient_name.value = ""
        lab_patient_dob.value = ""
        lab_doctor_name.value = ""
        lab_department.value = ""
        lab_notes.value = ""
        for cb in lab_tests_checkboxes:
            cb.value = False
        lab_patient_name.error_text = None
        lab_tests_checkboxes[0].error_text = None

    def print_lab_order(page):
        """Показывает диалог с последним заказом"""
        orders = load_lab_orders()
        if not orders:
            return

        last_order = orders[-1]

        print_content = [
            f"ЛАБОРАТОРНЫЙ ЗАКАЗ №{len(orders)}",
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
                ft.TextButton("Закрыть", on_click=lambda e: setattr(dlg, "open", False) or page.update()),
                ft.TextButton("Печать", on_click=lambda e: print("Печать заказа..."))
            ],
            actions_alignment="end"
        )

        page.dialog = dlg
        dlg.open = True
        page.update()

    def create_lab_table_rows():
        """Создает строки таблицы лабораторных заказов"""
        rows = []
        orders = get_lab_orders(lab_sort_by.value)

        for idx, order in enumerate(orders, 1):
            diagnosis_field = ft.TextField(
                value=order.get("diagnosis", ""),
                width=300,
                on_change=lambda e, order_idx=orders.index(order): update_lab_diagnosis(order_idx, e.control.value),
                disabled=not order.get("tests_completed", False)
            )

            complete_tests_btn = ft.ElevatedButton(
                "Анализы выполнены",
                on_click=lambda e, order_idx=orders.index(order): mark_lab_tests_completed(order_idx),
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

    def update_lab_diagnosis(order_idx, diagnosis):
        """Обновляет диагноз лабораторного заказа"""
        update_lab_diagnosis(order_idx, diagnosis)

    def mark_lab_tests_completed(order_idx):
        """Отмечает анализы как выполненные"""
        mark_lab_tests_completed(order_idx)
        lab_orders_table.rows = create_lab_table_rows()
        page.update()

    def sort_lab_orders(e):
        """Сортирует лабораторные заказы"""
        lab_orders_table.rows = create_lab_table_rows()
        page.update()

    # Загружаем пациентов при первом открытии
    load_patients()

    # Создаем вкладки для интерфейса врача
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Пациенты", content=ft.Column([
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
            ])),
            ft.Tab(text="Чат с пациентами", content=create_chat_tab()),
            ft.Tab(text="Лабораторные заказы", content=create_lab_orders_tab()),
            ft.Tab(text="Курсы лечения", content=ft.Column([
                ft.ElevatedButton(
                    "Управление курсами лечения",
                    on_click=lambda e: show_courses_ui(page)
                )
            ]))
        ],
        expand=1
    )

    page.add(
        ft.Column([
            tabs,
            ft.ElevatedButton("Выйти", on_click=lambda e: show_start(page))
        ], expand=True)
    )


def main(page: ft.Page):
    # Настройки страницы
    page.title = "Медицинская система"
    page.window_width = 1200
    page.window_height = 800
    page.padding = 20

    # Инициализация данных
    global user_ip
    user_ip = get_user_ip()

    init_users_db()
    init_patients_db()
    init_sample_data()
    load_courses_data()

    # Запуск приложения
    show_start(page)

ft.app(target=main)