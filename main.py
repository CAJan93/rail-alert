import time
import sys
from datetime import date, datetime, timedelta
import argparse
from nightjetter.watcher import find_connections
from localtelebot.telebot import TelegramBot


def main():
    parser = argparse.ArgumentParser(description="find routes at date")
    parser.add_argument(
        "-b", "--bot_key", help="key for the telegram bot", type=str, required=True
    )
    parser.add_argument(
        "-i",
        "--interval",
        help="sleep interval in minutes between queries",
        type=int,
        required=False,
        default=60,
    )

    sp = parser.add_subparsers(title="subparser", dest="sub")
    nj = sp.add_parser("nightjet", description="search for ÖBB nightjet connections")
    nj.add_argument(
        "-f", "--from_city", type=str, help="Departure city.", required=True
    )
    nj.add_argument(
        "-t", "--to_city", type=str, help="Destination city.", required=True
    )
    nj.add_argument("-y", "--year", type=int, help="year.", required=True)
    nj.add_argument("-m", "--month", type=int, help="month.", required=True)
    nj.add_argument("-d", "--day", type=int, help="day.", required=True)
    nj.add_argument(
        "-a", "--advance", type=int, help="day + a days to search.", required=True
    )

    tl = sp.add_parser("trainline", description="search for trainline connections")
    tl.add_argument(
        "-f", "--from_city", type=str, help="Departure city.", required=True
    )
    tl.add_argument(
        "-t", "--to_city", type=str, help="Destination city.", required=True
    )
    tl.add_argument("-y", "--year", type=int, help="year.", required=True)
    tl.add_argument("-m", "--month", type=int, help="month.", required=True)
    tl.add_argument("-d", "--day", type=int, help="day.", required=True)
    tl.add_argument(
        "-a", "--advance", type=int, help="day + a days to search.", required=True
    )
    args = parser.parse_args()

    # Grab Bot Key & init Telebot
    bot = TelegramBot(args.bot_key)

    count = 0
    while True:
        if count == 0:
            bot.send_messages("program is still running...")
        count = (count + 1) % 24

        try:
            bot.print_status()

            if args.sub == "nightjet":
                date_start = date(args.year, args.month, args.day)
                conns = find_connections(
                    args.from_city,
                    args.to_city,
                    date_start,
                    advance_days=args.advance,
                )
                print(conns)  # TODO  remove prints
                if len(conns) > 0:
                    print("found a connection: Happy!")
                    for conn in conns:
                        print(conn)
                    bot.send_messages(
                        f"For the connection from {args.from_city} to {args.to_city} on {str(date_start)} + {args.advance} days the following connections where found: {', '.join(conns)}"
                    )

            else:
                print("no other watchers implemented")

        except (KeyboardInterrupt, SystemExit):
            # Allow to terminate the script using CTRL-C
            raise
        except Exception as e:
            print(e)

        # sleep for number of minutes
        time.sleep(60 * args.interval)


if __name__ == "__main__":
    main()
