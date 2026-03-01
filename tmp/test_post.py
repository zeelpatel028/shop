import requests

data = {
    'name': 'Zeel Dobariya Edited',
    'phone_no': '6353807407',
    'address': 'Mendarda',
    'status': 'Active',
    'panding_bill_count': '2',
    'all_bill_count': '3',
    'padin_amount_last': '50.00',
    'padin_amount_total': '1477.70'
}

response = requests.post('http://127.0.0.1:5000/customer/edit/1', data=data, allow_redirects=False)
print("Status Code:", response.status_code)
print("Response Headers:", response.headers)
if response.status_code != 302:
    print("Response Body:", response.text)
