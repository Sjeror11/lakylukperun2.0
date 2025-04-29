"""
Modul pro přihlašovací obrazovku
"""

from textual.app import App
from textual.widgets import Header, Footer, Input, Button, Label
from textual.screen import Screen

class LoginScreen(Screen):
    """
    Přihlašovací obrazovka aplikace
    """

    CSS = """
    Screen {
        background: #000000;
    }

    #login-container {
        width: 60%;
        height: auto;
        margin: 2 auto;
        border: solid #333333;
        padding: 2;
    }

    .title {
        text-align: center;
        color: #00ff00;
        margin-bottom: 1;
    }

    .input-label {
        color: #cccccc;
        margin-bottom: 1;
    }

    .error-message {
        color: #ff0000;
        text-align: center;
        margin-top: 1;
    }

    Button {
        margin: 1 1;
    }

    #button-container {
        align: center;
        margin-top: 2;
    }
    """

    def __init__(self, user_db):
        """
        Inicializace přihlašovací obrazovky
        """
        super().__init__()
        self.user_db = user_db
        self.authenticated_user = None

    def compose(self):
        """
        Sestavení UI
        """
        # Vytvoření widgetů
        header = Header(show_clock=True)

        title = Label("TermiSignal - Přihlášení", classes="title")
        username_label = Label("Uživatelské jméno:", classes="input-label")
        username_input = Input(placeholder="Zadejte uživatelské jméno", id="username")
        password_label = Label("Heslo:", classes="input-label")
        password_input = Input(placeholder="Zadejte heslo", id="password", password=True)
        error_message = Label("", id="error-message", classes="error-message")

        login_button = Button("Přihlásit", id="login-button", variant="primary")
        register_button = Button("Registrovat", id="register-button")
        exit_button = Button("Ukončit", id="exit-button", variant="error")

        footer = Footer()

        # Přidání widgetů do layoutu
        self.add_widget(header)

        # Vytvoření kontejneru pro přihlašovací formulář
        login_container = self.make_container("login-container")
        login_container.add_widget(title)
        login_container.add_widget(username_label)
        login_container.add_widget(username_input)
        login_container.add_widget(password_label)
        login_container.add_widget(password_input)
        login_container.add_widget(error_message)

        # Vytvoření kontejneru pro tlačítka
        button_container = self.make_container("button-container")
        button_container.add_widget(login_button)
        button_container.add_widget(register_button)
        button_container.add_widget(exit_button)

        login_container.add_widget(button_container)

        self.add_widget(login_container)
        self.add_widget(footer)

    def make_container(self, id):
        """
        Vytvoření kontejneru
        """
        from rich.panel import Panel
        from textual.widget import Widget

        class Container(Widget):
            def __init__(self, id):
                super().__init__(id=id)
                self.children = []

            def add_widget(self, widget):
                self.children.append(widget)
                self.mount(widget)

            def render(self):
                return Panel("")

        return Container(id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Obsluha stisknutí tlačítka
        """
        button_id = event.button.id

        if button_id == "login-button":
            self.handle_login()
        elif button_id == "register-button":
            self.handle_register()
        elif button_id == "exit-button":
            self.app.exit()

    def handle_login(self) -> None:
        """
        Obsluha přihlášení
        """
        username = self.query_one("#username").value
        password = self.query_one("#password").value

        if not username or not password:
            self.query_one("#error-message").update("Vyplňte všechna pole")
            return

        success, result = self.user_db.authenticate_user(username, password)

        if success:
            self.authenticated_user = {
                "username": username,
                "display_name": result.get("display_name", username)
            }
            self.app.exit()
        else:
            self.query_one("#error-message").update(result)

    def handle_register(self) -> None:
        """
        Obsluha registrace
        """
        username = self.query_one("#username").value
        password = self.query_one("#password").value

        if not username or not password:
            self.query_one("#error-message").update("Vyplňte všechna pole")
            return

        success, message = self.user_db.register_user(username, password)

        if success:
            self.query_one("#error-message").update(f"Registrace úspěšná: {message}")
        else:
            self.query_one("#error-message").update(f"Chyba registrace: {message}")

    def run(self):
        """
        Spuštění přihlašovací obrazovky
        """
        app = App()
        app.install_screen(self, name="login")
        app.push_screen("login")
        app.run()

        return self.authenticated_user
