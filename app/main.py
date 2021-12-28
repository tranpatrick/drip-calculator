import json
import logging
import sys

from environs import Env
from flask import Flask
from flask import request, make_response
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

log = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
out_hdlr.setLevel(logging.DEBUG)
log.addHandler(out_hdlr)
log.setLevel(logging.DEBUG)

env = Env()
env.read_env()

DEFAULT_HYDRATE_TAX_RATE = 0.05
DEFAULT_DAILY_ROI = 0.01

if __name__ == "__main__":
    flask_app = Flask(__name__)

    def parameter_validation(deposit: float, hydrate_period: int):
        try:
            assert type(deposit) is float, 'deposit parameter must be of type float'
            assert deposit >= 0, 'deposit parameter must be a positive value'
            assert deposit <= 1000000000, 'deposit parameter must inferior to a billion'
            assert type(hydrate_period) is int, 'hydrate period parameter must be of type int'
            assert hydrate_period >= 0, 'hydrate period parameter must superior or equal to 0'
            assert hydrate_period <= 365, 'hydrate period parameter must be inferior or equal to a 365'
        except AssertionError as ae:
            log.error(ae)
            return {
                "status": 400,
                "error": "Bad Request",
                "message": str(ae)
            }

    def fetch_drip_price() -> float:
        log.info('Fetching current DRIP token USD price')
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
        parameters = {
            'symbol':'DRIP'
        }
        headers = {
          'Accepts': 'application/json',
          'X-CMC_PRO_API_KEY': env('CMC_PRO_API_KEY'),
        }
        session = Session()
        session.headers.update(headers)

        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
            price = data['data']['DRIP']['quote']['USD']['price']
            log.info(f"DRIP token USD price = {data['data']['DRIP']['quote']['USD']['price']}")
            return price
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            log.error(e)

    def convert_tab_in_usd(data_overtime: dict, drip_price: float) -> dict:
        res = {}
        for tab in data_overtime:
            res[tab] = {}
            for k in data_overtime[tab]:
                res[tab][k] = round(data_overtime[tab][k] * drip_price, 2)
        return res


    @flask_app.route('/compute', methods=['GET'])
    def compute():
        deposit = request.args.get('deposit', default=0, type=float)
        hydrate_period = request.args.get('hydrate_period', default=1, type=int)
        drip_price = request.args.get('drip_price', type=float)
        param_validation_res = parameter_validation(deposit, hydrate_period)

        if drip_price is None:
            drip_price = fetch_drip_price()

        # checking parameters
        if param_validation_res is not None:
            return param_validation_res

        accumulated_deposit = deposit
        accumulated_interest = 0
        total_interest_earned = 0
        total_tax_payed = 0
        data_overtime = {
            'interest': {0: 0},
            'tax': {0: 0},
            'total': {0: accumulated_deposit}
        }

        for i in range (1, 366):
            daily_interest = accumulated_deposit * DEFAULT_DAILY_ROI
            accumulated_interest += daily_interest
            total_interest_earned += daily_interest

            if hydrate_period != 0 and i % hydrate_period == 0:
                compound_tax_amount = accumulated_interest * DEFAULT_HYDRATE_TAX_RATE
                total_tax_payed += compound_tax_amount
                accumulated_deposit += accumulated_interest - compound_tax_amount
                accumulated_interest = 0

            if i % 30 == 0:
                data_overtime['interest'][i] = round(total_interest_earned, 2)
                data_overtime['tax'][i] = round(total_tax_payed, 2)
                data_overtime['total'][i] = round(accumulated_deposit + accumulated_interest, 2)

        data_overtime['interest'][365] = round(total_interest_earned, 2)
        data_overtime['tax'][365] = round(total_tax_payed, 2)
        data_overtime['total'][365] = round(accumulated_deposit + accumulated_interest, 2)

        res = {
            "status": 200,
            "body": {
                "data_overtime": data_overtime,
                "data_overtime_usd": convert_tab_in_usd(data_overtime, drip_price)
            }
        }

        response = make_response(res)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response


    flask_app.run(host="0.0.0.0", port=8080, debug=False)
