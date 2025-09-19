<h1 align="center">Hi there, I'm ITgenerat0r.</h1>
If you want to send someone a message in case you can't do it yourself, use this bot. He will deliver your message.

**Install & Run**

Download
```terminal
git clone https://github.com/ITgenerat0r/SOS.git
```
Prepare config
```terminal
rename config_template.py config.py
```
Create new Telegram bot via https://t.me/BotFather
Set your values in the config.

Make database
```terminal
source ./make_database.sql
```

Run bot
```terminal
python3 bot.py 
```


**Some problems and solutions**

ModuleNotFoundError: No module named 'mysql'
```terminal
pip install mysql-connector-python
```