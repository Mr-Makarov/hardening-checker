from django import forms


class ConnectServerForm(forms.Form):
    """Класс для ввода данных для подключения к серверу"""

    host = forms.CharField(max_length=15, label='IP-адрес')
    port = forms.IntegerField(initial=22, label='SSH порт')
    username = forms.CharField(max_length=15, label='Логин')
    password = forms.CharField(widget=forms.PasswordInput(render_value=True), label='Пароль')
    check = forms.ChoiceField(choices=[], label="Профиль сканирования")



class ServerAddForm(forms.Form):
    """Класс для добавления сервера"""

    name = forms.CharField(max_length=255, label='Имя сервера')
    host = forms.CharField(max_length=255, label='IP-адрес или домен')
    port = forms.IntegerField(initial=22, label='SSH порт')
    username = forms.CharField(max_length=100, label='Имя пользователя')
    password = forms.CharField(widget=forms.PasswordInput(render_value=True), label='Пароль')
    is_active = forms.BooleanField(required=False, initial=True, label='Активен')
