import time
import telebot
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description = "find routes at date")
    sp = parser.add_subparsers(title="subparser")
    
    nj = sp.add_parser("nightjet", description="search for ÖBB nightjet connections")
    nj.add_argument("-f", "--from_city", type = str, help = "Departure city.", required=True)
    nj.add_argument("-t", "--to_city", type = str, help = "Destination city.", required=True)
    nj.add_argument("-y", "--year", type = int, help = "year.", required=True)
    nj.add_argument("-m", "--month", type = int, help = "month.", required=True)
    nj.add_argument("-d", "--day", type = int, help = "day.", required=True)
    
    tl = sp.add_parser("trainline", description="search for trainline connections")
    tl.add_argument("-f", "--from_city", type = str, help = "Departure city.", required=True)
    tl.add_argument("-t", "--to_city", type = str, help = "Destination city.", required=True)
    tl.add_argument("-y", "--year", type = int, help = "year.", required=True)
    tl.add_argument("-m", "--month", type = int, help = "month.", required=True)
    tl.add_argument("-d", "--day", type = int, help = "day.", required=True)
    
    args = parser.parse_args()

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

