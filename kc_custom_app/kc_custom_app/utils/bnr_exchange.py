import requests
import frappe
from frappe.utils import today, flt

def fetch_bnr_rates():
    today_date = today()
    from_currency = "USD"
    to_currency = "RWF"
    
    # 1. Fetch API Key from site config
    api_key = frappe.conf.get("bnr_api_key")
    
    headers = {
        "Accept": "application/json"
    }
    if api_key:
        headers["X-API-KEY"] = api_key
    
    url = f"https://fxrates.bnr.rw/ExchangeRate?currency_name={from_currency}&start_date={today_date}&end_date={today_date}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data or not isinstance(data, list):
            frappe.log_error(message=f"No exchange rate data returned for {today_date}", title="BNR Fetch Warning")
            return

        rate_data = data[0]
        
        # 2. Confirm Date and Currency match expected values
        post_date = rate_data.get("post_date", "").replace("/", "-")
        returned_currency = rate_data.get("currency_name")
        average_rate = flt(rate_data.get("average_rate"))
        
        if returned_currency != from_currency or today_date not in post_date:
            frappe.log_error(
                message=f"Validation failed. Expected {from_currency} on {today_date}, got {returned_currency} on {post_date}", 
                title="BNR Fetch Mismatch"
            )
            return

        if not average_rate:
            frappe.log_error(message="Average rate is missing or 0", title="BNR Fetch Error")
            return

        # 3. Prevent duplicate creation for today's rate
        existing_doc = frappe.db.exists("Currency Exchange", {
            "date": today_date,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "for_buying": 1,
            "for_selling": 1
        })
        
        if existing_doc:
            # Update existing rate if already present
            doc = frappe.get_doc("Currency Exchange", existing_doc)
            doc.exchange_rate = average_rate
            doc.save(ignore_permissions=True)
            frappe.logger().info(f"Updated BNR rate for {today_date}: {average_rate}")
        else:
            # Create new Currency Exchange
            doc = frappe.get_doc({
                "doctype": "Currency Exchange",
                "date": today_date,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "exchange_rate": average_rate,
                "for_buying": 1,
                "for_selling": 1
            })
            doc.insert(ignore_permissions=True)
            frappe.logger().info(f"Successfully created BNR rate for {today_date}: {average_rate}")

    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="BNR Fetch Failed")