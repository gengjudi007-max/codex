import schedule
import time

from scheduler.daily_jobs import DailyJobRunner


runner = DailyJobRunner()

schedule.every().day.at('08:00').do(runner.run_all)
schedule.every().day.at('12:00').do(runner.run_announcement_jobs)
schedule.every().day.at('18:00').do(runner.run_report_jobs)


if __name__ == '__main__':
    print('Scheduler started...')

    while True:
        schedule.run_pending()
        time.sleep(60)
