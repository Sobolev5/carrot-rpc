# Carrot
Carrot it is a python asyncio RPC server/client for RabbitMQ that allows you to make RPC calls.  
*Note:* This project in active development and can be unstable.  
You can see live example here: http://5.187.4.179:8588/

```no-highlight
https://github.com/Sobolev5/carrot-rpc
```

## Install
To install run:
```no-highlight
pip install carrot-rpc
```


## Microservice A which call

```python
import asyncio
from carrot import Carrot
from simple_print import sprint

# set amqp connection:
AMQP_URI = "amqp://admin:password@127.0.0.1/vhost"

# defer function which call microservice «microservice_sum»:
async def call_sum_a_and_b():
  
    # make dict request:
    dct = {}
    dct["caller"] = "Function on microservice_interface which call RPC in microservice_sum"
    dct["number_a"] = int(data["number_a"])
    dct["number_b"] = int(data["number_b"])

    # defer carrot instance and make rpc call:
    carrot = await Carrot(AMQP_URI).connect()
    response_from_another_microservice = await carrot.call(dct, "microservice_sum:sum_a_and_b")    

    # dct: first arg is dict with data
    # another_microservice:sum_a_and_b: second arg it routing key (through default AMQP exchange) 

    # get response dict from microservice «microservice_sum»
    sprint(f'Sum a and b: {response_from_another_microservice["sum"]}', c="yellow", s=1, p=1)


loop = asyncio.get_event_loop()
loop.run_until_complete(call_sum_a_and_b())

```


## Microservice B which ask

```python
import asyncio
import aiormq
from pydantic import BaseModel
from carrot import carrot_ask
from simple_print import sprint
from fastapi import FastAPI
from fastapi import APIRouter


# set amqp connection:
AMQP_URI = "amqp://admin:password@127.0.0.1/vhost"

# make pydantic schema:
class SumAAndB(BaseModel):
    caller: str
    a: int
    b: int

# decorate called function with pydantic schema
@carrot_ask(SumAAndB)
async def sum_a_and_b(incoming_dict: dict) -> dict:
    sprint(incoming_dict, c="yellow", s=1, p=1)
    dct = {}
    dct["caller"] = "i am sum_a_and_b function mounted on microservice_sum"
    dct["sum"] = incoming_dict["number_a"] + incoming_dict["number_b"]
    return dct

# make amqp router:
async def amqp_router():
    connection = await aiormq.connect(AMQP_URI)
    channel = await connection.channel()
    sprint(f"AMQP:     ready [yes]", c="green", s=1, p=1)
    sum_a_and_b__declared = await channel.queue_declare(f"microservice_sum:sum_a_and_b", durable=False)
    await channel.basic_consume(sum_a_and_b__declared.queue, sum_a_and_b, no_ack=False)  
    

class App(FastAPI):
    def __init__(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.create_task(amqp_router())
        super().__init__(*args, **kwargs)

app = App()

```

## Full working example with docker-compose
https://github.com/Sobolev5/FastAPI-plus-RabbitMQ


## TODO
tests, docstrings, extended documentation


# Try my free time tracker
My free time tracker for developers [Workhours.space](https://workhours.space/). 




