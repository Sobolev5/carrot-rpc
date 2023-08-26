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

# defer function which call microservice «BB»:
async def call_sum_a_and_b():
  
    # make dict request:
    d = {}
    d["info"] = "Microservice AA call"
    d["number_a"] = 1
    d["number_b"] = 2

    # get response dict from microservice «BB»
    carrot = await CarrotCall(AMQP_URI).connect()
    response_from_BB = await carrot.call(d, "BB:sum_a_and_b", timeout=5)    
    print(response_from_BB) # {"sum": 3}

    # you can send request to another microservice without reply (like standart call):
    await carrot.call(dct, "BB:sum_a_and_b", without_reply=True)
    # in this case «BB» just calculate sum and do not send response to caller.   


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
from fastapi import APIRouter


# set amqp connection:
AMQP_URI = "amqp://admin:password@127.0.0.1/vhost"

# make pydantic schema:
class SumAAndB(BaseModel):
    caller: str
    number_a: int
    number_b: int

# protect called function with pydantic schema
@carrot_ask(SumAAndB)
async def sum_a_and_b(incoming_dict: dict) -> dict:
    print(incoming_dict, c="green")
    dct = {}
    dct["sum"] = incoming_dict["number_a"] + incoming_dict["number_b"]
    return dct

# make amqp router:
async def amqp_router():
    connection = await aiormq.connect(AMQP_URI)
    channel = await connection.channel()
    print(f"AMQP:     ready [yes]", c="green")
    sum_a_and_b_queue = await channel.queue_declare(f"BB:sum_a_and_b", durable=False)
    await channel.basic_consume(sum_a_and_b_queue.queue, sum_a_and_b, no_ack=False)  
    
app = FastAPI()

@app.on_event("startup")
async def startup_aiormq_router():
    """Запускаем роутер aiormq."""
    loop = asyncio.get_running_loop()
    loop.create_task(amqp_router())
```

## Live examples 
http://5.187.4.179:5888/  (https://github.com/Sobolev5/Carrot-RPC-Example)  
http://89.108.77.63:1025/  (https://github.com/Sobolev5/LordaeronChat)  






