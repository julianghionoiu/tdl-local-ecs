# See AWS API: https://docs.aws.amazon.com/ses/latest/DeveloperGuide/query-interface-requests.html

# This stub should be able to receive Action=SendEmail calls and should store the messages as files on the file system

# There should also be an endpoint that allows the retrieval of the latest N messages

import BaseHTTPServer
import json
import os
from urlparse import urlparse

import time

HOST_NAME = 'localhost'
PORT_NUMBER = 9988

SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))
CACHE_FOLDER = os.path.join(SCRIPT_FOLDER, ".taskRepository")

SENT_EMAIL_RESPONSE = """
                        <SendEmailResponse xmlns='https://email.amazonaws.com/doc/2010-03-31/'>
                           <SendEmailResult>
                               <MessageId>000001271b15238a-fd3ae762-2563-11df-8cd4-6d4e828a9ae8-000000</MessageId>
                           </SendEmailResult>
                           <ResponseMetadata>
                               <RequestId>fd3ae762-2563-11df-8cd4-6d4e828a9ae8</RequestId>
                           </ResponseMetadata>
                        </SendEmailResponse>
                      """
"""
{
    "networkConfiguration": {
        "awsvpcConfiguration": { 
            "subnets": ["subnet-cf2386b9"], 
            "securityGroups": ["sg-ee159989"], 
            "assignPublicIp": "DISABLED"
            }
        }, 
    "cluster": "dpnt-coverage-cluster", 
    "launchType": "FARGATE", 
    "taskDefinition": "test-coverage"
}
"""

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    # noinspection PyPep8Naming,PyMethodParameters
    def do_POST(request):
        """Respond to a POST request."""
        display_raw_request_retails_on_the_console(request)
        request_raw_content = convert_raw_http_request_data_to_string(request)
        log_debug("Request body: \n%s" % request_raw_content)

        # Validate action
        requested_action = request.headers['X-Amz-Target']
        if not requested_action.endswith('RunTask'):
            send_invalid_request_to_the_client(request)
            return

        # Handle RunTask
        content = json.loads(request_raw_content)

        send_successful_response_to_client(request)


# ~~~ Response handling

def send_successful_response_to_client(request):
    request.send_response(200)
    request.send_header('Content-type', 'application/json')
    request.end_headers()
    request.wfile.write(SENT_EMAIL_RESPONSE)
    log_info("Finished sending.")


def send_invalid_request_to_the_client(request):
    request.send_response(400)
    request.send_header('Content-type', 'application/json')
    request.end_headers()
    request.wfile.write('{"__type":"ClientException","message":"Request not supported"}')
    log_info("Finished sending.")


# ~~~ Request handling

def display_raw_request_retails_on_the_console(request):
    parsed_url = urlparse(request.path)
    log_debug("Request path: %s" % parsed_url.path)
    log_debug("Request query string: %s" % parsed_url.query)
    log_debug("Request headers: \n%s" % request.headers)


def convert_raw_http_request_data_to_string(request):
    content_length = int(request.headers.getheader('content-length'))
    return request.rfile.read(content_length)


# ~~~ Logging

def log_debug(message):
    log("[DEBUG] " + message)


def log_error(message):
    log("[ERROR] " + message)


def log_info(message):
    log("[INFO] " + message)


def log(message):
    print time.asctime(), message


# ~~~ Http server

if __name__ == '__main__':
    if not os.path.exists(CACHE_FOLDER):
        os.mkdir(CACHE_FOLDER)

    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    log_info("Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    log_info("Kill process using: ")
    log_info("     $ python ecs-server-wrapper.py stop")
    log_info("In case, unsuccessful, use this to find out process id: ")
    log_info("     $ netstat -tulpn | grep :" + str(PORT_NUMBER))
    log_info("...and kill it manually: ")
    log_info("     $ kill -9 <pid>")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    log_info("Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))
