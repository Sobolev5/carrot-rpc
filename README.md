# Carrot
Carrot-RPC it is a python asyncio RPC server/client for RabbitMQ that allows you to make RPC calls.  
*Note:* This project in active development and can be unstable.  
You can see live example here: http://5.187.4.179:5888/

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
from carrot import CarrotCall
from simple_print import sprint

# set amqp connection:
AMQP_URI = "amqp://admin:password@127.0.0.1/vhost"

# defer function which call «MICROSERVICE_SUM»:
async def call_sum_a_and_b():
  
    # make dict request:
    dct = {}
    dct["caller"] = "Function on microservice_interface which call RPC in microservice_sum"
    dct["number_a"] = int(data["number_a"])
    dct["number_b"] = int(data["number_b"])

    # defer carrot instance and make rpc call:
    carrot = await CarrotCall(AMQP_URI).connect()
    response_from_another_microservice = await carrot.call(dct, "microservice_sum:sum_a_and_b", timeout=5)    
    # first arg is dict with data
    # second arg it routing key (through default AMQP exchange) 
    # third arg is optional (response timeout in seconds, 5 seconds by default) 

    # get response dict from microservice «MICROSERVICE_SUM»
    sprint(f'Sum a and b: {response_from_another_microservice["sum"]}', c="yellow")

    # you can send request to another microservice without reply (like standart call):
    await carrot.call(dct, "microservice_sum:sum_a_and_b", without_reply=True)
    # in this case «MICROSERVICE_SUM» just calculate sum and do not send response to caller.   


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
    number_a: int
    number_b: int

# decorate called function with pydantic schema
@carrot_ask(SumAAndB)
async def sum_a_and_b(incoming_dict: dict) -> dict:
    sprint(incoming_dict, c="green")
    dct = {}
    dct["caller"] = "i am sum_a_and_b function mounted on microservice_sum"
    dct["sum"] = incoming_dict["number_a"] + incoming_dict["number_b"]
    return dct

# make amqp router:
async def amqp_router():
    connection = await aiormq.connect(AMQP_URI)
    channel = await connection.channel()
    sprint(f"AMQP:     ready [yes]", c="green")
    sum_a_and_b__declared = await channel.queue_declare(f"microservice_sum:sum_a_and_b", durable=False)
    await channel.basic_consume(sum_a_and_b__declared.queue, sum_a_and_b, no_ack=False)  
    

class App(FastAPI):
    def __init__(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.create_task(amqp_router())
        super().__init__(*args, **kwargs)

app = App()

```

## Full working example [1]
https://github.com/Sobolev5/Carrot-RPC-Example

## Full working example [2]
https://github.com/Sobolev5/LordaeronChat

## TODO
tests, docstrings, extended documentation






