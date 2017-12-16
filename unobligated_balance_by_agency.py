import requests
import csv

fy = 2017
fields = ["unobligated_balance_cpe", "status_of_budgetary_resources_total_cpe", "budget_authority_unobligated_balance_brought_forward_fyb","adjustments_to_unobligated_balance_brought_forward_cpe", "obligations_incurred_total_by_tas_cpe","treasury_account_identifier__agency_id", "treasury_account_identifier__beginning_period_of_availability", "treasury_account_identifier__ending_period_of_availability", "treasury_account_identifier__treasury_account_identifier", "treasury_account_identifier__main_account_code", "treasury_account_identifier__availability_type_code", "treasury_account_identifier__account_title", "submission__reporting_fiscal_quarter", "submission__reporting_fiscal_year" ]

headers = ["agency_name",]
headers.extend(fields)
output = csv.writer(open("output/unobligated_balance_by_accounts.csv", "w"))
output.writerow(headers)
# get list of top-tier agencies
agencies = requests.get("https://api.usaspending.gov/api/v1/references/agency/?toptier_flag=True&limit=200").json()
names = []
account_ids = {}
data = {}

for agency in agencies["results"]:

    if agency["toptier_agency"]["name"] in names:
        continue

    aname = agency["toptier_agency"]["name"]
    names.append(aname)
    cgac_code = agency["toptier_agency"]["cgac_code"]
    # catch labor which doesn't have a real cgac in the API for some reason
    if cgac_code == "1601" or cgac_code == "1602":
        cgac_code = "016"

    if len(cgac_code) > 3:
        print("warning: CGAC Code longer than 3 characters -- may not map to any account balances. Agency: " + aname)
    body = {
         "limit":800,
         "fields": fields,
         "filters": [{
           "field": "unobligated_balance_cpe",
           "operation":"greater_than",
           "value": 0
          },
          {
          	"field": "final_of_fy",
          	"operation": "equals",
          	"value": True
          },
          {
          	"field":"treasury_account_identifier__main_account_code",
          	"operation": "less_than",
          	"value": "4999"
          },
          {
          	"field": "treasury_account_identifier__agency_id",
          	"operation":"equals",
          	"value": cgac_code
          }
          ]
    }

    accounts = requests.post("https://api.usaspending.gov/api/v1/tas/balances/", json=body).json()

    if "labor" in agency["toptier_agency"]["name"].lower():
        print(accounts)
    for account in accounts['results']:
        account_id = account["treasury_account_identifier"]["treasury_account_identifier"]
        # Check to see if we've already seen a row for this account
        # There should only be the latest balance for each account but we were
        # getting multiples from the API. If this row is from a later quarter,
        # discard the old row
        if account_id in account_ids:
            if account_ids[account_id]['latest_quarter'] < account['submission']['reporting_fiscal_quarter']:
                del data[account_id]
            else:
                # The row we already have is newer, so skip
                continue

        # Store the id
        try:
            account_ids[account_id]['latest_quarter'] = account['submission']['reporting_fiscal_quarter']
        except KeyError:
            account_ids[account_id] = {'latest_quarter': account['submission']['reporting_fiscal_quarter']}

        # Store the data for this row
        row = [agency["toptier_agency"]["name"],]
        for f in fields:
            if "treasury_account_identifier" in f:
                row.append(account['treasury_account_identifier'][f.split("treasury_account_identifier__")[1]])
            elif "submission" in f:
                row.append(account['submission'][f.split("submission__")[1]])
            else:
                row.append(account[f])

        data[account_id] = row

for data_row in data.values():
    output.writerow(data_row)
