import flet as ft
import pandas as pd
import os
import sys
import calendar
from datetime import datetime

# Глобальные переменные для хранения данных
courses = []
current_course_index = -1
data_file = ""
start_date_value = ""
end_date_value = ""


def get_desktop_path():
    if sys.platform == "win32":
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        )
        return winreg.QueryValueEx(key, "Desktop")[0]
    else:
        return os.path.join(os.path.expanduser("~"), "Desktop")


def init_data():
    global data_file, courses
    data_file = os.path.join(get_desktop_path(), "курсы.xlsx")
    courses = []
    load_data()


def load_data():
    global courses
    try:
        df = pd.read_excel(data_file)
        if not df.empty and 'Курс' in df.columns:
            for _, row in df.iterrows():
                course_name = row['Курс']
                course = next((c for c in courses if c['name'] == course_name), None)
                if not course:
                    course = {
                        'name': course_name,
                        'start_date': row.get('Дата начала', ''),
                        'end_date': row.get('Дата окончания', ''),
                        'tablets': []
                    }
                    courses.append(course)
                course['tablets'].append({
                    'name': row.get('Препарат', ''),
                    'quantity': row.get('Количество', ''),
                    'measure': row.get('Мера', ''),
                    'time': row.get('Время', ''),
                    'comment': row.get('Комментарий', '')
                })
    except FileNotFoundError:
        pass


def save_data():
    data = []
    for course in courses:
        for tablet in course['tablets']:
            data.append({
                "Курс": course['name'],
                "Дата начала": course['start_date'],
                "Дата окончания": course['end_date'],
                "Препарат": tablet['name'],
                "Количество": tablet['quantity'],
                "Мера": tablet['measure'],
                "Время": tablet['time'],
                "Комментарий": tablet['comment']
            })
    df = pd.DataFrame(data)
    df.to_excel(data_file, index=False)


def show_main(page):
    page.clean()

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
                on_click=lambda e, idx=i: show_course(page, idx)
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
            )
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
    )


def create_course_ui(page, start_date="", end_date=""):
    global current_course_index, start_date_value, end_date_value
    current_course_index = -1
    page.clean()

    name_field = ft.TextField(label="Название курса", width=400)

    # Сохраняем переданные даты
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
        global start_date_value, end_date_value  # Moved to top of function
        if name_field.value:
            new_course = {
                'name': name_field.value,
                'start_date': start_date_value,
                'end_date': end_date_value,
                'tablets': []
            }
            courses.append(new_course)
            save_data()
            # Сброс значений дат после сохранения
            start_date_value = ""
            end_date_value = ""
            show_main(page)

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
                ft.ElevatedButton("Отмена", on_click=lambda e: show_main(page))
            ], spacing=20)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
    )
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


def show_course(page, course_index):
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
            save_data()
            show_course(page, course_index)

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
                    ft.ElevatedButton("Назад", on_click=lambda e: show_course(page, course_index)),
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
                ft.ElevatedButton("Назад", on_click=lambda e: show_main(page))
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


def main(page: ft.Page):
    page.title = "Управление курсами лечения"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20

    init_data()
    show_main(page)


ft.app(target=main)