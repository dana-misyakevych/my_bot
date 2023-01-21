import datetime


def last_month():

    today = datetime.date.today()
    first = today.replace(day=1)
    return first - datetime.timedelta(days=1)


def get_yesterday_today_date():

    yesterday = (datetime.date.today() - datetime.timedelta(days=1))
    today = datetime.date.today()
    return yesterday, today
