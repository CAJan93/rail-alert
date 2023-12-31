# Telegram Rail Alert

Watch for a connection with ÖBB Nightjet and send a notification to your Telegram if its available to book.

I am still working on the messages, but they look something like this: 

![](Screenshot.png)

For the first query on February connections where found. For the query for April there were no bookable connections yet. 

## How to install? 

```sh
pip3 install -r requirements.txt
```

## How to run?

Get your telegram API keys using [these instructions](https://medium.com/geekculture/generate-telegram-token-for-bot-api-d26faf9bf064)

To watch for a connection between Berlin and Strassburg on the 9th or 10th of February 2024 run:

```sh
python3 main.py -b <your_tele_token> nightjet -y 2024 -m 2 -d 9 -f Berlin -t Strassburg -a 2 -i 60
```

Query will be executed every 60 minutes. Upon execution you should receive a test notification on your telegram account. 
You will receive further notifications when a bookable connection is found.



## Credits

This project was inspired by the following projects 

- [nightjetter](https://github.com/KevinW1998/nightjetter) for retrieving information about the ÖBB nightjet trains
- [telepot](https://github.com/nickoala/telepot) for sending notifications to your telegram account


