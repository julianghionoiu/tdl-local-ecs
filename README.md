# tdl-local-ecs

A Local ECS Server Stub that uses Docker as backend

The server simulates one cluster with the following settings:
```
EXPECTED_CLUSTER_NAME = 'local-test-cluster'
EXPECTED_LAUNCH_TYPE = 'FARGATE'
EXPECTED_SUBNET = 'local-subnet-x'
EXPECTED_SECURITY_GROUP = 'sg-local-security'
EXPECTED_ASSIGN_PUBLIC_IP = 'DISABLED'
```

The task definitions will be matched against locally defined Docker containers.
When matching a container image, only the `latest` tag will be used.

To inject ENV variables in the ECS Run task, create a configuration file `local.ecstask.json`:
```
[
  {
    "ParameterKey": "X_KEY",
    "ParameterValue": "x"
  },
  {
    "ParameterKey": "Y_KEY",
    "ParameterValue": "y"
  }
]
```


To run:
```bash
python local-ecs/ecs-server-wrapper.py start config/local.ecstask.json
```

Console mode (blocking):
```bash
python local-ecs/ecs-server-wrapper.py console config/local.ecstask.json
```

To stop:
```bash
python local-ecs/ecs-server-wrapper.py stop
```

