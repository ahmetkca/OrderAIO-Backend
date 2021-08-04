from datetime import datetime, timedelta
import pytz
from typing import List
from MyLogger import Logger
logging = Logger().logging


def bday(from_date: datetime, n_days: int) -> datetime:
	temp_date: datetime = from_date + timedelta(days=1)
	comp_date: datetime = datetime(temp_date.year, temp_date.month, temp_date.day)
	n_days = n_days - 1
	while n_days > 0 or comp_date.weekday() == 5 or comp_date.weekday() == 6:
		# print(comp_date, "weekday = " + str(comp_date.weekday()), comp_date.strftime("%A"), n_days)
		if comp_date.weekday() == 5 or comp_date.weekday() == 6:
			comp_date += timedelta(days=1)
			continue
		n_days -= 1
		comp_date += timedelta(days=1)
	return comp_date


def find_bigger_max_processing(receipt: dict) -> int:
	listings = []
	try:
		listings: List[dict] = receipt["Listings"]
	except KeyError:
		return -1
	max_pro_day: int = -1
	for listing in listings:
		max_pro_day = max(max_pro_day, listing["processing_max"])
	return max_pro_day


def find_smaller_min_processing(receipt: dict) -> int:
	listings = []
	try:
		listings: List[dict] = receipt["Listings"]
	except KeyError:
		return -1
	min_pro_day: int = 999
	for listing in listings:
		min_pro_day = min(min_pro_day, listing["processing_min"])
	return min_pro_day


def calculate_max_min_due_date(receipt: dict) -> None:
	logging.info(f"number of transactions: {len(receipt['Transactions'])}")
	logging.info(f"number of listings: {len(receipt['Listings'])}")
	# pprint.pprint(receipt['Transactions'])
	receipt["is_completed"] = False
	paid_date = datetime.fromtimestamp(int(receipt["Transactions"][0]["paid_tsz"]), pytz.timezone('Canada/Eastern'))
	
	max_pro_n_day: int = find_bigger_max_processing(receipt)
	max_due_date = bday(paid_date, max_pro_n_day)
	min_pro_n_day: int = find_smaller_min_processing(receipt)
	min_due_date = bday(paid_date, min_pro_n_day)
	receipt["max_due_date"] = max_due_date
	receipt["min_due_date"] = min_due_date
	logging.info(f"{receipt['receipt_id']}'s due dates:")
	logging.info(f"\tmax_due_date => is {paid_date} +{max_pro_n_day} business day ({max_due_date})")
	logging.info(f"\tmin_due_date => is {paid_date} +{min_pro_n_day} business day ({min_due_date})")


if __name__ == '__main__':
	print(bday(datetime(2021, 5, 7), 7))
