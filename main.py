import time
import telebot
import sys


def main(): 

    # Grab Bot Key & init Telebot
    BOT_KEY = sys.argv[1]
    bot = telebot.TelegramBot(BOT_KEY)

    # Init vars
    appartment_links = []


    count = 0

    while True:
        if count == 0: 
            bot.send_message("program is still running...")
        count = (count + 1) % 24
        
        try:
            bot.print_status()

            # call the other program here!
            
            
            # if success 
            bot.send_message("found a valid connection from to at date")

        except (KeyboardInterrupt, SystemExit):
            # Allow to terminate the script using CTRL-C
            raise
        except Exception as e:
            print(e)

        # sleep for an hour no matter what
        time.sleep(60*60) 

if __name__ == '__main__':
    print("entering the fun here")
    main()

