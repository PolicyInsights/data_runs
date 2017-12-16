import requests
import csv

fy = 2017
minor_ocs = ["233", "257", "310", "260", "251"]
# create output file
output = csv.writer(open("output/object_class_by_agency.csv", "w"))
output.writerow(["agency_id", "agency_name","obligations_incurred_by_program_object_class_cpe", "program_activity_name", "object_class_name", "object_class_code", "treasury_account_identifier", "main_account_code", "account_title","reporting_fiscal_quarter"])

#output.writerow(("Agency Name", "Communications, utilities, and miscellaneous charges", "Operation and maintenance of equipment", "Equipment", "Supplies and materials", "Advisory and assistance services"))
# get list of top-tier agencies
agencies = requests.get("https://api.usaspending.gov/api/v1/references/agency/?toptier_flag=True&limit=400").json()
data = []
names = []

for agency in agencies["results"]:

    # sometimes we get duplicate agencies back from the API
    if agency["toptier_agency"]["name"] in names:
        continue

    names.append(agency["toptier_agency"]["name"])
    aid = agency["toptier_agency"]["cgac_code"]

    for oc in minor_ocs:

        body = {
        	"limit": 400,
        	"fields":["obligations_incurred_by_program_object_class_cpe", "program_activity__program_activity_name", "object_class__object_class_name", "object_class__object_class", "treasury_account__treasury_account_identifier", "treasury_account__main_account_code", "treasury_account__account_title","submission__reporting_fiscal_quarter"],
        	"filters":[{
        		"field": "object_class__object_class",
        		"operation": "equals",
        		"value": oc
        	},
        	{
        		"field": "treasury_account__agency_id",
        		"operation": "equals",
        		"value": "{0}".format(aid)
        	},
        	{
        		"field":"obligations_incurred_by_program_object_class_cpe",
        		"operation": "greater_than",
        		"value": 0
        	}]
        }

        oc_spending = requests.post("https://api.usaspending.gov/api/v1/tas/categories/", json=body).json()['results']
        for item in oc_spending:
            print(item)
            row = [aid,
                agency["toptier_agency"]["name"],
                item["obligations_incurred_by_program_object_class_cpe"],
                item["program_activity"]["program_activity_name"],
                item["object_class"]["object_class_name"],
                item["object_class"]["object_class"],
                item["treasury_account"]["treasury_account_identifier"],
                item["treasury_account"]["main_account_code"],
                item["treasury_account"]["account_title"],
                item["submission"]["reporting_fiscal_quarter"]]

            data.append(row)

for row in data:
    output.writerow(row)
    #for oc in ["20", "30"]:
    #    oc_spending = requests.get("https://api.usaspending.gov/api/v2/financial_spending/object_class/?funding_agency_id={0}&fiscal_year={1}&major_object_class_code={2}".format(aid, fy, oc)).json()
    #    for result in oc_spending["results"]:
    #        if result["object_class_code"] in minor_ocs:
    #            data[aid][result["object_class_code"]] = result["obligated_amount"]

#for agency in data.values():
#    output.writerow((agency["name"], agency["233"], agency["257"], agency["310"], agency["260"], agency["251"]))
