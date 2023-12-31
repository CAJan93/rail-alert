# Telegram Rail Alert

Watch for a connection with ÖBB Nightjet and send a notification to your Telegram if its available to book.

## How to install? 

```
pip3 install -r requirements.txt
```

## How to run?

Get your telegram API keys using [these instructions](https://medium.com/geekculture/generate-telegram-token-for-bot-api-d26faf9bf064)

To watch for a connection between Berlin and Strassburg on the 9th or 10th of February 2024 run:

```
python3 main.py -b <your_tele_token> nightjet -y 2024 -m 2 -d 9 -f Berlin -t Strassburg -a 2 -i 60
```

Query will be executed every 60 minutes. Upon execution you should receive a test notification on your telegram account. 
You will receive further notifications when a bookable connection is found.



## Credits

This project was inspired by the following projects 

- [nightjetter](https://github.com/KevinW1998/nightjetter) for retrieving information about the ÖBB nightjet trains
- telepot for sending notifications to your telegram account


