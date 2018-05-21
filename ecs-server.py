# See AWS API: https://docs.aws.amazon.com/ses/latest/DeveloperGuide/query-interface-requests.html

# This stub should be able to receive Action=SendEmail calls and should store the messages as files on the file system

# There should also be an endpoint that allows the retrieval of the latest N messages

import BaseHTTPServer
import json
import os
from subprocess import call
from urlparse import urlparse

import time

HOST_NAME = 'localhost'
PORT_NUMBER = 9988

EXPECTED_CLUSTER_NAME = 'local-test-cluster'
EXPECTED_LAUNCH_TYPE = 'FARGATE'
EXPECTED_SUBNET = 'local-subnet-x'
EXPECTED_SECURITY_GROUP = 'sg-local-security'
EXPECTED_ASSIGN_PUBLIC_IP = 'DISABLED'

SCRIPT_FOLDER = os.path.dirname(os.path.realpath(__file__))
CACHE_FOLDER = os.path.join(SCRIPT_FOLDER, ".taskRepository")

A_VALID_RESPONSE = """
{
    "failures": [],
    "tasks": [
        {
            "taskArn": "arn:aws:ecs:eu-west-1:577770582757:task/3723fca1-4e11-42a2-aece-0fd8265033af",
            "group": "family:test-coverage",
            "attachments": [
                {
                    "status": "PRECREATED",
                    "type": "ElasticNetworkInterface",
                    "id": "2414d1f3-b00b-4ccc-af44-49c939800c2f",
                    "details": [
                        {
                            "name": "subnetId",
                            "value": "subnet-cf2386b9"
                        }
                    ]
                }
            ],
            "overrides": {
                "containerOverrides": [
                    {
                        "name": "dpnt-coverage-java"
                    }
                ]
            },
            "launchType": "FARGATE",
            "lastStatus": "PROVISIONING",
            "createdAt": 1526911643.114,
            "version": 1,
            "clusterArn": "arn:aws:ecs:eu-west-1:577770582757:cluster/dpnt-coverage-cluster",
            "memory": "2048",
            "platformVersion": "1.1.0",
            "desiredStatus": "RUNNING",
            "taskDefinitionArn": "arn:aws:ecs:eu-west-1:577770582757:task-definition/test-coverage:1",
            "cpu": "1024",
            "containers": [
                {
                    "containerArn": "arn:aws:ecs:eu-west-1:577770582757:container/886c4de4-7c23-4bc9-9043-1637bd5c68fa",
                    "taskArn": "arn:aws:ecs:eu-west-1:577770582757:task/3723fca1-4e11-42a2-aece-0fd8265033af",
                    "lastStatus": "PENDING",
                    "name": "dpnt-coverage-java",
                    "networkInterfaces": []
                }
            ]
        }
    ]
}
                      """


class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    # noinspection PyPep8Naming,PyMethodParameters
    def do_POST(request):
        """Respond to a POST request."""
        display_raw_request_retails_on_the_console(request)
        request_raw_content = convert_raw_http_request_data_to_string(request)
        log_debug("Request body: \n%s" % request_raw_content)

        # Ensure RunTask action
        requested_action = request.headers['X-Amz-Target']
        if not requested_action.endswith('RunTask'):
            send_error_response(request, "ClientException", "Request not supported")
            return

        # Deserialise
        content = json.loads(request_raw_content)

        # Validate Cluster, TaskDefinition, LaunchType and Network Configuration
        if "cluster" not in content or content["cluster"] != EXPECTED_CLUSTER_NAME:
            return send_error_response(request, "ClusterNotFoundException", "Cluster not found")

        # Validate TaskDefinition
        if "taskDefinition" not in content:
            return send_error_response(request, "ClientException", "Task definition not provided")

        docker_image = content["taskDefinition"] + ":latest"
        if not is_valid_docker_image(docker_image):
            return send_error_response(request, "ClientException",
                                       " TaskDefinition not found. No Docker image: " + docker_image)

        # Validate Network Configuration
        if "networkConfiguration" not in content or "awsvpcConfiguration" not in content["networkConfiguration"]:
            return send_error_response(request, "InvalidParameterException",
                                       "Network Configuration must be provided when "
                                       "networkMode 'awsvpc' is specified")

        awsvpcConfiguration = content["networkConfiguration"]["awsvpcConfiguration"]
        if "subnets" not in awsvpcConfiguration or not awsvpcConfiguration["subnets"]:
            return send_error_response(request, "InvalidParameterException", "subnets can not be empty")

        subnet_id = awsvpcConfiguration["subnets"][0]
        if subnet_id != EXPECTED_SUBNET:
            return send_error_response(request, "InvalidParameterException",
                                       "The subnet ID " + subnet_id + " does not exist")

        if "securityGroups" not in awsvpcConfiguration or not awsvpcConfiguration["securityGroups"]:
            return send_error_response(request, "InvalidParameterException", "securityGroups can not be empty")

        security_group_id = awsvpcConfiguration["securityGroups"][0]
        if security_group_id != EXPECTED_SECURITY_GROUP:
            return send_error_response(request, "InvalidParameterException",
                                       "The security group " + security_group_id + " does not exist")

        if "assignPublicIp" not in awsvpcConfiguration \
                or awsvpcConfiguration["assignPublicIp"] != EXPECTED_ASSIGN_PUBLIC_IP:
            return send_error_response(request, "InvalidParameterException",
                                       "The assignPublicIp policy for this deployment should be " +
                                       EXPECTED_ASSIGN_PUBLIC_IP)

        # Extract Env parameters from request
        try:
            environment_overrides = content["overrides"]["containerOverrides"][0]["environment"]
        except KeyError:
            environment_overrides = []

        # Handle RunTask
        run_docker_task(docker_image, environment_overrides)

        # Send response
        send_successful_response(request)


# ~~~ Docker

def is_valid_docker_image(image_name):
    return_code = call_and_log(["docker", "image", "inspect", "--format='{{.Container}}'", image_name])
    return return_code == 0


def run_docker_task(image_name, environment_overrides):
    cmd = ["docker", "run", "--detach"]
    for key_pair in environment_overrides:
        cmd.append("--env")
        cmd.append(key_pair["name"] + "=" + key_pair["value"])
    cmd.append(image_name)
    return_code = call_and_log(cmd)
    if return_code != 0:
        raise Exception("Docker run failed")


def call_and_log(cmd):
    log_info("Executing command: " + " ".join(cmd))
    return call(cmd)


# ~~~ Response handling

def send_successful_response(request):
    request.send_response(200)
    request.send_header('Content-type', 'application/json')
    request.end_headers()
    request.wfile.write(A_VALID_RESPONSE)
    log_info("Finished sending successful response")


def send_error_response(request, error_class, error_message):
    request.send_response(400)
    request.send_header('Content-type', 'application/json')
    request.end_headers()
    formatted_message = '{"__type":"' + error_class + '","message":"' + error_message + '"}'
    request.wfile.write(formatted_message)
    log_info("Finished sending error:" + formatted_message)


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
