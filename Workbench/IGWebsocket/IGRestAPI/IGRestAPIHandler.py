from requests import Session
import logging

class IGRestAPIHandler:
    def __init__(self,username,password,api_key) -> None:
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.ig.com/gateway/"
        self.session = Session()
        self.username = username
        self.password = password
        self.api_key = api_key
        self.oauth_token = None
        self.refresh_token = None
        self.cst = None
        self.x_security_token = None

    def get_cst_token(self):
        url = self.base_url + "deal/session"
        payload = {
            "identifier": self.username,
            "password": self.password
        }
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json; charset=UTF-8",
            "X-IG-API-KEY": self.api_key,
        }
        response = self.session.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get session token. {response.text}")
        ret = response.json()
        CST = response.headers.get("CST")
        X_SECURITY_TOKEN = response.headers.get("X-SECURITY-TOKEN")
        self.cst = CST
        self.x_security_token = X_SECURITY_TOKEN
        return CST , X_SECURITY_TOKEN

    def get_endpoint(self):
        url = self.base_url + "deal/session"
        print(f"Getting session token from {url}")
        payload = {
            "identifier": self.username,
            "password": self.password
        }
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json; charset=UTF-8",
            "X-IG-API-KEY": self.api_key,
            "version":"3"
        }
        response = self.session.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get session token. {response.text}")
        return  response.json()['lightstreamerEndpoint']


    def get_session_token(self):
        url = self.base_url + "deal/session?fetchSessionTokens=true"
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json; charset=UTF-8",
            "X-IG-API-KEY": self.api_key,
            'x-security-token': "d6790ac9766bb045b266c69e26a02cfe28a178d435a3a0d6a78cb7961619b7CD01115",
            "version":"1"
        }
        response = self.session.get(url, headers=headers)




