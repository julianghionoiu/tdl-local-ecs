# tdl-local-ecs

A Local ECS Server Stub that uses Docker as backend

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
python local-ecs/ecs-server-wrapper.py start config/local.ecstask.json
```

To stop:
```bash
python local-ecs/ecs-server-wrapper.py stop
```

