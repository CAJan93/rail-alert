import telepot
import time


# Telegram Bot class
class TelegramBot:
    def __init__(self, KEY):
        self.bot = telepot.Bot(KEY)
        self.subscriber_list = set()
        #  self.subscriber_list.add(-1001492640968)
        self.scan_counter = 0
        self.start = time.time()
        self.update_subscribers()

    def update_subscribers(self):
        response = self.bot.getUpdates()
        for el in response:
            self.subscriber_list.add(el["message"]["chat"]["id"])

    def send_messages(self, msg):
        self.has_timeout()
        for id in self.subscriber_list:
            self.bot.sendMessage(id, msg)

    def has_timeout(self):
        cur = time.time()
        if (cur - self.start) > 21000:
            self.send_messages(
                "Please send me a message, so I can continue sending you super cool offers on apartments."
            )
            return True

    def print_status(self):
        print("New Scan... {}".format(self.scan_counter))
        self.scan_counter += 1
