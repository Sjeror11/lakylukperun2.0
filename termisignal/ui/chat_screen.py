"""
Modul pro chatovací obrazovku
"""

import time
import random
from textual.app import App
from textual.widgets import Header, Footer, Input, Button, Label
from textual.screen import Screen
from textual import events

class Message:
    """
    Třída pro zprávu
    """

    def __init__(self, sender, content, timestamp=None, sender_color=None):
        """
        Inicializace zprávy
        """
        self.sender = sender
        self.content = content
        self.timestamp = timestamp or time.time()
        self.sender_color = sender_color or self._generate_color()

    def _generate_color(self):
        """
        Generování barvy pro odesílatele
        """
        # Seznam barev pro odesílatele (bez černé a bílé)
        colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff",
                 "#ff8000", "#8000ff", "#0080ff", "#ff0080"]

        # Výběr náhodné barvy
        return random.choice(colors)

    def get_text(self):
        """
        Získání textu zprávy
        """
        time_str = time.strftime("%H:%M:%S", time.localtime(self.timestamp))
        return f"[{time_str}] [{self.sender_color}]{self.sender}[/]: {self.content}"

class ChatScreen(Screen):
    """
    Chatovací obrazovka aplikace
    """

    CSS = """
    Screen {
        background: #000000;
    }

    #chat-container {
        width: 100%;
        height: 100%;
        layout: grid;
        grid-size: 1 2;
        grid-rows: 1fr auto;
        grid-gutter: 1;
    }

    #messages-container {
        height: 100%;
        border: solid #333333;
        background: #000000;
        color: #ffffff;
        overflow-y: auto;
    }

    #input-container {
        height: auto;
        layout: horizontal;
        margin: 1 0;
    }

    #message-input {
        width: 1fr;
        height: 3;
        margin-right: 1;
    }

    #send-button {
        width: auto;
    }
    """

    def __init__(self, user):
        """
        Inicializace chatovací obrazovky
        """
        super().__init__()
        self.user = user

        # Simulace zpráv pro ukázku
        self.messages = [
            Message("system@termisignal", "Vítejte v TermiSignal chatu!", sender_color="#00ff00"),
            Message("lucky@admin", "Ahoj, jak se máš?", sender_color="#ff0000"),
            Message(f"{user['username']}@termisignal", "Já se mám dobře, díky za optání!", sender_color="#0000ff")
        ]

    def compose(self):
        """
        Sestavení UI
        """
        # Vytvoření widgetů
        header = Header(show_clock=True)

        # Vytvoření kontejneru pro zprávy
        messages_container = self.make_container("messages-container")
        for message in self.messages:
            message_label = Label(message.get_text())
            messages_container.add_widget(message_label)

        # Vytvoření kontejneru pro vstup
        input_container = self.make_container("input-container")
        message_input = Input(placeholder="Napište zprávu...", id="message-input")
        send_button = Button("Odeslat", id="send-button", variant="primary")
        input_container.add_widget(message_input)
        input_container.add_widget(send_button)

        # Vytvoření hlavního kontejneru
        chat_container = self.make_container("chat-container")
        chat_container.add_widget(messages_container)
        chat_container.add_widget(input_container)

        footer = Footer()

        # Přidání widgetů do layoutu
        self.add_widget(header)
        self.add_widget(chat_container)
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
        if event.button.id == "send-button":
            self.send_message()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Obsluha odeslání zprávy pomocí klávesy Enter
        """
        if event.input.id == "message-input":
            self.send_message()

    def send_message(self) -> None:
        """
        Odeslání zprávy
        """
        message_input = self.query_one("#message-input")
        message_text = message_input.value

        if message_text.strip():
            # Vytvoření nové zprávy
            new_message = Message(
                f"{self.user['username']}@termisignal",
                message_text
            )

            # Přidání zprávy do kontejneru
            messages_container = self.query_one("#messages-container")
            message_label = Label(new_message.get_text())
            messages_container.add_widget(message_label)

            # Simulace odpovědi (pro ukázku)
            if random.random() > 0.5:
                time.sleep(random.uniform(0.5, 2.0))
                response = Message(
                    "lucky@admin",
                    f"Odpověď na: {message_text}",
                    sender_color="#ff0000"
                )
                response_label = Label(response.get_text())
                messages_container.add_widget(response_label)

            # Vyčištění vstupního pole
            message_input.value = ""

    def run(self):
        """
        Spuštění chatovací obrazovky
        """
        app = App()
        app.install_screen(self, name="chat")
        app.push_screen("chat")
        app.run()
