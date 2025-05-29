import flet as ft
import sqlite3
import socket
import os
from datetime import datetime


def get_user_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except:
        return "неизвестен"


def init_db():
    # Удаляем старую базу данных, если она существует
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


# Инициализация базы данных
init_db()
user_ip = get_user_ip()


def main(page: ft.Page):
    page.title = "Регистрация"
    page.window_width = 500
    page.window_height = 650
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.padding = 20

    def show_start():
        page.clean()
        page.add(
            ft.Column([
                ft.Text("Регистрация", size=24),
                ft.Text(f"Ваш IP: {user_ip}", color="grey"),
                ft.ElevatedButton("Регистрация", width=400, on_click=lambda e: show_reg_name()),
                ft.ElevatedButton("Вход", width=400, on_click=lambda e: show_login())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
        )

    def show_reg_name():
        page.clean()
        surname = ft.TextField(label="Фамилия", width=400, autofocus=True)
        name = ft.TextField(label="Имя", width=400)
        middle_name = ft.TextField(label="Отчество", width=400)

        page.add(
            ft.Column([
                ft.Text("Регистрация", size=20),
                surname, name, middle_name,
                ft.Row([
                    ft.ElevatedButton("Назад", on_click=lambda e: show_start()),
                    ft.ElevatedButton("Далее", on_click=lambda e: show_reg_contact(
                        surname.value, name.value, middle_name.value))
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def show_reg_contact(surname, name, middle_name):
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
                    ft.ElevatedButton("Назад", on_click=lambda e: show_reg_name()),
                    ft.ElevatedButton("Зарегистрировать", on_click=lambda e: register_user(
                        surname, name, middle_name, phone.value, password.value))
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def register_user(surname, name, middle_name, phone, password):
        if not phone or len(phone) != 11:
            show_reg_contact(surname, name, middle_name)
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
            show_success(name)
        except Exception as e:
            print(f"Ошибка базы данных: {e}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка: {str(e)}"))
            page.snack_bar.open = True
            page.update()
        finally:
            conn.close()

    def show_success(name):
        page.clean()
        page.add(
            ft.Column([
                ft.Icon(ft.icons.CHECK, color="green", size=50),
                ft.Text(f"{name}, регистрация успешна!", size=20),
                ft.ElevatedButton("OK", width=200, on_click=lambda e: show_start())
            ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def show_login():
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
                    ft.ElevatedButton("Назад", on_click=lambda e: show_start()),
                    ft.ElevatedButton("Войти", on_click=lambda e: login_user(phone.value, password.value))
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def login_user(phone, password):
        conn = sqlite3.connect('users.db', check_same_thread=False)
        try:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE phone=? AND password=?", (phone, password))
            user = c.fetchone()

            if not user:
                show_login()
                return

            show_profile(user)
        except Exception as e:
            print(f"Ошибка базы данных: {e}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка: {str(e)}"))
            page.snack_bar.open = True
            page.update()
        finally:
            conn.close()

    def show_profile(user):
        page.clean()
        page.add(
            ft.Column([
                ft.Text("Профиль", size=20),
                ft.Text(f"{user[2]} {user[3]} {user[4]}"),
                ft.Text(f"Телефон: {user[5]}"),
                ft.Text(f"IP: {user[0]}"),
                ft.Text(f"Дата регистрации: {user[1]}"),
                ft.ElevatedButton("Выйти", width=200, on_click=lambda e: show_start())
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    show_start()


ft.app(target=main)