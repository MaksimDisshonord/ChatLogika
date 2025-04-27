import threading
import base64
import io
import os
import time  # Додано для відстеження часу останньої активності
from socket import *
from customtkinter import *
from tkinter import filedialog
from PIL import Image

class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.geometry('400x300')
        self.label = None
        self.entry = None

        self.menu_frame = CTkFrame(self, fg_color='light blue', width=30, height=300)
        self.menu_frame.pack_propagate(False)
        self.menu_frame.place(x=0, y=0)
        self.is_show_menu = False
        self.speed_animate_menu = -5
        #кнопка
        self.btn = CTkButton(self, text='▶️', command=self.toggle_show_menu, width=30)
        self.btn.place(x=0, y=0)
        # тема вікна
        self.label_theme = CTkOptionMenu(self.menu_frame, values=['Темна', 'Світла'], command=self.change_theme)
        self.label_theme.pack(side='bottom', pady=20)
        self.theme = None

        self.chat_field = CTkScrollableFrame(self)
        self.chat_field.place(x=0, y=0)

        # Додано фрейм для статусів користувачів
        self.users_frame = CTkScrollableFrame(self, width=150, height=100)
        self.users_frame.place(x=0, y=0)  # Позиція буде оновлена в adaptive_ui

        # Додано словник для зберігання статусів користувачів та їх міток у GUI
        self.online_users = {}  # {username: (last_activity_time, label_widget)}

        self.message_input = CTkEntry(self, placeholder_text='Введіть повідомлення:')
        self.message_input.place(x=0, y=250)
        self.send_button = CTkButton(self, text='▶', width=40, height=30, command=self.send_message)
        self.send_button.place(x=200, y=250)
        self.open_img_button = CTkButton(self, text='📂', width=40, height=30, command=self.open_image)
        self.open_img_button.place(x=0, y=0)  # Точні координати будуть оновлені в функції adaptive_ui
        self.username = 'Користувач'

        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(('localhost', 8080))
            # Змінено формат вітального повідомлення для включення статусу
            hello = f"STATUS@{self.username}@online\n"
            self.sock.send(hello.encode('utf-8'))
            hello_text = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
            self.sock.send(hello_text.encode('utf-8'))
            threading.Thread(target=self.recv_message, daemon=True).start()
            
            # Додано періодичну відправку статусу онлайн
            threading.Thread(target=self.send_online_status, daemon=True).start()
            
            # Додано періодичну перевірку статусів користувачів
            threading.Thread(target=self.check_users_status, daemon=True).start()
        except Exception as e:
            self.add_message(f"Не вдалося підключитися до сервера: {e}")

        self.adaptive_ui()

    # Додано функцію для регулярної відправки статусу "онлайн"
    def send_online_status(self):
        while True:
            try:
                status_msg = f"STATUS@{self.username}@online\n"
                self.sock.send(status_msg.encode('utf-8'))
                time.sleep(10)  # Відправляємо статус кожні 10 секунд
            except:
                break

    # Додано функцію для перевірки статусів користувачів
    def check_users_status(self):
        while True:
            current_time = time.time()
            users_to_remove = []
            
            # Перевіряємо кожного користувача
            for username, (last_activity, label) in self.online_users.items():
                # Якщо немає активності понад 30 секунд, вважаємо користувача офлайн
                if current_time - last_activity > 30:
                    users_to_remove.append(username)
            
            # Оновлюємо статуси для користувачів, які вийшли офлайн
            for username in users_to_remove:
                self.update_user_status(username, "offline")
            
            time.sleep(5)  # Перевіряємо статуси кожні 5 секунд

    # Додано функцію для оновлення статусу користувача у GUI
    def update_user_status(self, username, status):
        if status == "online":
            current_time = time.time()
            if username in self.online_users:
                # Оновлюємо час останньої активності та мітку
                last_activity, label = self.online_users[username]
                self.online_users[username] = (current_time, label)
                label.configure(text=f"{username} 🟢", text_color="green")
            else:
                # Створюємо нову мітку для нового користувача
                label = CTkLabel(self.users_frame, text=f"{username} 🟢", text_color="green")
                label.pack(anchor="w", pady=2)
                self.online_users[username] = (current_time, label)
        elif status == "offline" and username in self.online_users:
            # Позначаємо користувача як офлайн
            _, label = self.online_users[username]
            label.configure(text=f"{username} 🔴", text_color="gray")
            # Видаляємо зі словника через певний час
            # Залишаємо у списку на деякий час, щоб показати що вони вийшли
            self.after(60000, lambda: self.remove_offline_user(username))  # Видаляємо через 1 хвилину

    # Додано функцію для видалення офлайн користувачів з інтерфейсу
    def remove_offline_user(self, username):
        if username in self.online_users:
            _, label = self.online_users.pop(username)
            label.destroy()

    def toggle_show_menu(self):
        if self.is_show_menu:
            self.is_show_menu = False
            self.speed_animate_menu *= -1
            self.btn.configure(text='▶️')
            self.show_menu()
        else:
            self.is_show_menu = True
            self.speed_animate_menu *= -1
            self.btn.configure(text='◀️')
            self.show_menu()
            # setting menu widgets
            self.label = CTkLabel(self.menu_frame, text='Імʼя')
            self.label.pack(pady=30)
            self.entry = CTkEntry(self.menu_frame)
            self.entry.pack()
            self.save_btn = CTkButton(self.menu_frame, text='Зберегти', command=self.save_username)
            self.save_btn.pack(pady=10)
    
    def save_username(self):
        if self.entry and self.entry.get().strip():
            old_username = self.username
            self.username = self.entry.get().strip()
            # Повідомляємо сервер про зміну імені
            self.add_message(f"Ваше ім'я змінено на: {self.username}")
            
            # Оновлюємо статус із новим ім'ям
            status_msg = f"STATUS@{self.username}@online\n"
            self.sock.send(status_msg.encode('utf-8'))
            
            # Повідомляємо інших користувачів про зміну імені
            rename_msg = f"TEXT@{self.username}@[SYSTEM] Користувач {old_username} змінив(ла) ім'я на {self.username}\n"
            self.sock.send(rename_msg.encode('utf-8'))

    def show_menu(self):
        self.menu_frame.configure(width=self.menu_frame.winfo_width() + self.speed_animate_menu)
        if not self.menu_frame.winfo_width() >= 200 and self.is_show_menu:
            self.after(10, self.show_menu)
        elif self.menu_frame.winfo_width() >= 40 and not self.is_show_menu:
            self.after(10, self.show_menu)
            if hasattr(self, 'label') and self.label:
                self.label.destroy()
            if hasattr(self, 'entry') and self.entry:
                self.entry.destroy()
            if hasattr(self, 'save_btn') and self.save_btn:
                self.save_btn.destroy()

    def change_theme(self, value):
        if value == 'Темна':
            set_appearance_mode('dark')
            self.menu_frame.configure(fg_color='dodger blue')
        else:
            set_appearance_mode('light')
            self.menu_frame.configure(fg_color='light blue')

    def adaptive_ui(self):
        self.menu_frame.configure(height=self.winfo_height())
        self.chat_field.place(x=self.menu_frame.winfo_width())
        
        # Оновлено розміщення та розміри елементів інтерфейсу для додавання панелі користувачів
        chat_width = self.winfo_width() - self.menu_frame.winfo_width() - 150  # Виділяємо місце для панелі користувачів
        self.chat_field.configure(width=chat_width, height=self.winfo_height() - 40)
        
        # Розміщуємо панель користувачів справа
        self.users_frame.place(x=self.winfo_width() - 150, y=0)
        self.users_frame.configure(height=self.winfo_height() - 40)
        
        self.send_button.place(x=self.winfo_width() - 100, y=self.winfo_height() - 40)
        self.open_img_button.place(x=self.winfo_width() - 50, y=self.winfo_height() - 40)
        self.message_input.place(x=self.menu_frame.winfo_width(), y=self.send_button.winfo_y())
        self.message_input.configure(
            width=self.winfo_width() - self.menu_frame.winfo_width() - 110)

        self.after(50, self.adaptive_ui)

    def add_message(self, message, img=None):
        message_frame = CTkFrame(self.chat_field, fg_color='grey')
        message_frame.pack(pady=5, anchor='w')
        wrapleng_size = self.chat_field.winfo_width() - 40  # Оновлено з урахуванням нової ширини

        if not img:
            CTkLabel(message_frame, text=message, wraplength=wrapleng_size,
                     text_color='white', justify='left').pack(padx=10, pady=5)
        else:
            CTkLabel(message_frame, text=message, wraplength=wrapleng_size,
                     text_color='white', image=img, compound='top',
                     justify='left').pack(padx=10, pady=5)

    def send_message(self):
        message = self.message_input.get()
        if message:
            # Відправляємо повідомлення
            data = f"TEXT@{self.username}@{message}\n"
            try:
                self.sock.sendall(data.encode())
                self.add_message(f"{self.username}: {message}")
                
                # Оновлюємо статус при відправці повідомлення
                status_msg = f"STATUS@{self.username}@online\n"
                self.sock.send(status_msg.encode('utf-8'))
            except Exception as e:
                self.add_message(f"Помилка надсилання: {e}")
        self.message_input.delete(0, END)

    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    # Підключення закрито
                    self.add_message("[SYSTEM] Підключення до сервера втрачено")
                    break
                buffer += chunk.decode('utf-8', errors='ignore')

                # Обробка отриманих даних
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except Exception as e:
                self.add_message(f"[SYSTEM] Помилка отримання: {e}")
                break
        # Закриття з'єднання
        self.sock.close()
        
        # Повідомляємо про вихід
        status_msg = f"STATUS@{self.username}@offline\n"
        try:
            self.sock.send(status_msg.encode('utf-8'))
        except:
            pass

    def handle_line(self, line):
        if not line:
            return
        parts = line.split("@", 3)
        if len(parts) < 2:
            self.add_message(line)
            return

        msg_type = parts[0]

        if msg_type == "TEXT":
            if len(parts) >= 3:
                author = parts[1]
                message = parts[2]
                # Перевіряємо чи це не наше власне повідомлення
                if author != self.username:
                    self.add_message(f"{author}: {message}")
        elif msg_type == "IMAGE":
            if len(parts) >= 4:
                author = parts[1]
                filename = parts[2]
                b64_img = parts[3]
                try:
                    img_data = base64.b64decode(b64_img)
                    pil_img = Image.open(io.BytesIO(img_data))
                    ctk_img = CTkImage(pil_img, size=(300, 300))
                    self.add_message(f"{author} надіслав(ла) зображення: {filename}", img=ctk_img)
                except Exception as e:
                    self.add_message(f"Помилка відображення зображення: {e}")
        # Додано обробку статусів
        elif msg_type == "STATUS":
            if len(parts) >= 3:
                username = parts[1]
                status = parts[2]
                # Оновлюємо статус користувача
                if username != self.username:  # Не відображаємо власний статус
                    self.update_user_status(username, status)
        else:
            self.add_message(line)

    def open_image(self):
        file_name = filedialog.askopenfilename(
            filetypes=[("Зображення", "*.jpg *.jpeg *.png *.gif *.bmp")])
        if not file_name:
            return
        try:
            # Відкриття та масштабування зображення перед відправкою
            pil_img = Image.open(file_name)
            # Обмежуємо максимальний розмір для відправки
            max_size = (800, 800)
            pil_img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Збереження у буфер для отримання даних
            img_buffer = io.BytesIO()
            pil_img.save(img_buffer, format=pil_img.format if pil_img.format else 'PNG')
            img_buffer.seek(0)
            raw = img_buffer.read()

            b64_data = base64.b64encode(raw).decode()
            short_name = os.path.basename(file_name)
            data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"
            self.sock.sendall(data.encode())

            # Створюємо зображення для відображення в інтерфейсі
            ctk_img = CTkImage(pil_img, size=(300, 300))
            self.add_message(f"{self.username} надіслав(ла) зображення: {short_name}", img=ctk_img)
            
            # Оновлюємо статус при надсиланні зображення
            status_msg = f"STATUS@{self.username}@online\n"
            self.sock.send(status_msg.encode('utf-8'))
        except Exception as e:
            self.add_message(f"Не вдалося надіслати зображення: {e}")

    # Додано функцію для очищення при закритті програми
    def on_closing(self):
        # Відправляємо повідомлення про вихід
        try:
            status_msg = f"STATUS@{self.username}@offline\n"
            self.sock.send(status_msg.encode('utf-8'))
            goodbye_msg = f"TEXT@{self.username}@[SYSTEM] {self.username} покинув(ла) чат\n"
            self.sock.send(goodbye_msg.encode('utf-8'))
            self.sock.close()
        except:
            pass
        self.destroy()

win = MainWindow()
# Додано обробку закриття вікна
win.protocol("WM_DELETE_WINDOW", win.on_closing)
win.mainloop()
