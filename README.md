# Ariadne Route Planner

Route planner backend for Ariadne's Thread project.

# Building & running

Make sure you have installed all of the dependencies from `requirements.txt`.

You'll need to create a `config.json` in `planner/config` to build/run the app. An example config has been provided for you at 
`config.example.json`. You can run the `run-db-demo.py` script to check if the DB details you've specified in the config
are valid. 

To start Router Planner gRPC server, use `planner/start_server.py` script. This service is used by [Ariadne HTTP API](https://github.com/ariadnes-thread/ariadne-api).

# Rebuilding gRPC code

After editing `grpc_protos/planner.proto` you can rebuild relevant Python code using:

```bash
python -m grpc_tools.protoc -I./grpc_protos --python_out=./planner --grpc_python_out=./planner ./grpc_protos/planner.proto
```
