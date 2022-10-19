import csv
import datetime
import json
from operator import itemgetter
import locale


def findMostExpensiveNumber(callLogFilepath):
    # set locale for use in formatting the currency output
    locale.setlocale(locale.LC_MONETARY, "")
    cheaper_start_time = datetime.datetime.strptime("20:00", "%H:%M").time()
    cheaper_end_time = datetime.datetime.strptime("08:00", "%H:%M").time()
    free_international_minutes = 10
    free_landline_mobile_minutes = 100
    cost_modifer_rate = 3

    with open(callLogFilepath) as csv_file:
        raw_call_data = csv.DictReader(csv_file)
        # Sorting by call time to count free minutes as used chronologically
        sorted_call_data = sorted(list(raw_call_data), key=itemgetter("CallStartTime"))

    number_totals = {}
    for call_info in sorted_call_data:
        phone_number = call_info["PhoneNumber"]
        # skip incoming and free numbers
        if call_info["CallDirection"] == "INCOMING" or phone_number.startswith("080"):
            continue

        call_minutes_started = datetime.datetime.strptime(
            call_info["CallDuration"], "%M:%S"
        ).minute

        call_start_time = datetime.datetime.strptime(
            call_info["CallStartTime"], "%Y-%m-%dT%H:%M:%S.%fZ"
        ).time()

        # Set the cheaper rate modifier
        cost_modifer = 1
        if call_start_time > cheaper_start_time or call_start_time < cheaper_end_time:
            cost_modifer = cost_modifer_rate

        # default minutes used and total cost
        number_totals.setdefault(phone_number, 0.0)

        # international
        if phone_number.startswith(("00", "+")) and not phone_number.startswith(
            ("0044", "+44")
        ):
            # take away minutes from free ones - or charge remainder
            if free_international_minutes < call_minutes_started:
                call_minutes_started -= free_international_minutes
                free_international_minutes = 0
                number_totals[phone_number] += ((call_minutes_started * 0.8)) + 0.5
            else:
                free_international_minutes -= call_minutes_started

        # landline
        elif phone_number.startswith(("01", "02")):
            if free_landline_mobile_minutes < call_minutes_started:
                call_minutes_started -= free_landline_mobile_minutes
                free_landline_mobile_minutes = 0
                number_totals[phone_number] += (
                    call_minutes_started * 0.15
                ) / cost_modifer
            else:
                free_landline_mobile_minutes -= call_minutes_started
        # mobile
        elif phone_number.startswith("07") and (
            phone_number.startswith("07624") or not phone_number.startswith("076")
        ):
            if free_landline_mobile_minutes < call_minutes_started:
                call_minutes_started -= free_landline_mobile_minutes
                free_landline_mobile_minutes = 0
                number_totals[phone_number] += (
                    call_minutes_started * 0.30
                ) / cost_modifer
            else:
                free_landline_mobile_minutes -= call_minutes_started
        else:
            continue

    if number_totals:
        # No handling of multiple of the same max value
        most_expensive_total = max(number_totals.items(), key=lambda kv: kv[1])
        most_expensive_dict = {
            "PhoneNumber": most_expensive_total[0],
            "TotalAmount": most_expensive_total[1],
        }
        if most_expensive_dict["TotalAmount"] > 0:
            # cleaner to use locale to clean cost output - easier to switch if needed
            most_expensive_dict["TotalAmount"] = locale.currency(
                most_expensive_dict["TotalAmount"]
            )
            return json.dumps(most_expensive_dict, ensure_ascii=False)
    return None


findMostExpensiveNumber("test")
