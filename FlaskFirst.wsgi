#! /usr/bin/python3.6

import logging
import sys
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/var/www/Text_to_PDF_Service')
from FlaskFirst import application as application
application.secret_key = 'anything you wish'
