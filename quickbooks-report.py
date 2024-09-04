#!/usr/bin/python3
import requests
import os
import json
import argparse
from intuitlib.client import AuthClient
from quickbooks import QuickBooks
from quickbooks.objects.customer import Customer
from datetime import datetime
from dotenv import load_dotenv

# Load configuration from .env
load_dotenv()
qb_company_id = os.getenv("QB_COMPANY_ID")
qb_client_id = os.getenv("QB_CLIENT_ID")
qb_client_secret = os.getenv("QB_CLIENT_SECRET")

auth_client = AuthClient(
        client_id=qb_client_id,
        client_secret=qb_client_secret,        
        environment='sandbox',
        redirect_uri='http://localhost:8000/callback',
    )

client = QuickBooks(
        auth_client=auth_client,
        refresh_token='REFRESH_TOKEN',
        company_id=qb_company_id,
    )

customers = Customer.all(qb=client)