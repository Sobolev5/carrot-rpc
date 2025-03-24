# Carrot
Carrot-RPC it is a python asyncio RPC server/client for RabbitMQ that allows you to make RPC calls.  


```no-highlight
https://github.com/Sobolev5/carrot-rpc
```

## Install
To install run:
```no-highlight
pip install carrot-rpc
```


## Microservice AA which call

```python
import asyncio
from carrot import CarrotCall

# defer AMQP connection:
AMQP_URI = "amqp://admin:password@127.0.0.1/vhost"

# defer function which call microservice BB:
async def call_sum_a_and_b():
  
    # make dict request:
    d = {}
    d["info"] = "Microservice AA call"
    d["number_a"] = 1
    d["number_b"] = 2

    # get response dict from microservice BB
    carrot = await CarrotCall(AMQP_URI=AMQP_URI).connect()
    response_from_BB = await carrot.call(d, "BB:sum_a_and_b", timeout=5)    
    print(response_from_BB) # {"sum": 3}

    # you can send request to microservice BB without reply (like standart call):
    await carrot.call(dct, "BB:sum_a_and_b", without_reply=True)
    # in this case BB just calculate sum and do not send response to caller.   


loop = asyncio.get_event_loop()
loop.run_until_complete(call_sum_a_and_b())

```


## Microservice BB which ask

```python
import asyncio
import aiormq
from pydantic import BaseModel
from carrot import carrot_ask
from fastapi import FastAPI


# defer AMQP connection:
AMQP_URI = "amqp://admin:password@127.0.0.1/vhost"

# make pydantic schema:
class SumAAndB(BaseModel):
    caller: str
    number_a: int
    number_b: int

# you can protect called function with pydantic schema
@carrot_ask(SumAAndB)
async def sum_a_and_b(sum_model: BaseModel) -> dict:
    dct = {}
    dct["sum"] = sum_model.number_a + sum_model.number_b
    return dct

# or use plain decorator carrot_ask() without protection
@carrot_ask()
async def sum_a_and_b_without_protect(incoming_dict: dict) -> dict:
    dct = {}
    dct["sum"] = incoming_dict["number_a"] + incoming_dict["number_b"]
    return dct

# make amqp router:
async def amqp_router():
    connection = await aiormq.connect(AMQP_URI)
    channel = await connection.channel()
    sum_a_and_b_queue = await channel.queue_declare(f"BB:sum_a_and_b", durable=False)
    await channel.basic_consume(sum_a_and_b_queue.queue, sum_a_and_b, no_ack=False)  
    
app = FastAPI()

@app.on_event("startup")
async def startup_aiormq_router():
    loop = asyncio.get_running_loop()
    loop.create_task(amqp_router())
```


 






