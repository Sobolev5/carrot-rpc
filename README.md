# Carrot
Carrot it is a simple tool for RabbitMQ that allows you to make RPC calls.

```no-highlight
https://github.com/Sobolev5/carrot-rpc
```

## Install
To install run:
```no-highlight
pip install carrot-rpc
```

## Example (microservice A which call)

```python
import asyncio
from carrot import Carrot
from simple_print import sprint


AMQP_URI = "amqp://admin:password@127.0.0.1/vhost"


async def call_sum_a_and_b():
    # test_carrot_rpc - function in another microservice (we want to call it)
  
    sprint(f"call_test_carrot_rpc", с="green", s=1, p=1)

    dct = {}
    dct["who_am_i"] = "i'm function which call RPC in another microservice"
    dct["a"] = 1
    dct["b"] = 2

    carrot = await Carrot(AMQP_URI).connect()
    response_from_another_microservice = await carrot.call(dct, "another_microservice:sum_a_and_b")    

    # dct: first arg is dict with data
    # "another_microservice:sum_a_and_b": second arg it is name of routing key (through default AMQP exchange) 

    sprint(f'Sum a and b: {response_from_another_microservice["sum"]}', c="yellow", s=1, p=1)


loop = asyncio.get_event_loop()
loop.run_until_complete(call_sum_a_and_b())

# to run use:  python carrot_call.py
```


## Example (microservice B which ask)

Send message to any group from any part of your code:
```python
import asyncio
import aiormq
from carrot import carrot_ask
from simple_print import sprint


AMQP_URI = "amqp://admin:password@127.0.0.1/vhost"


@carrot_ask
async def sum_a_and_b(incoming_dict: dict) -> dict:
    sprint(incoming_dict, c="yellow", s=1, p=1)
    dct = {}
    dct["who_am_i"] = "i am rpc function mounted on another microservice"
    dct["sum"] = incoming_dict["a"] + incoming_dict["b"]
    return dct


async def rpc_subscriptions():
    connection = await aiormq.connect(AMQP_URI)
    channel = await connection.channel()
    sprint(f"AMQP RPC:     ready [yes]", c="green", s=1, p=1)
    sum_a_and_b__declared = await channel.queue_declare(f"another_microservice:sum_a_and_b", durable=False)
    await channel.basic_consume(sum_a_and_b__declared.queue, sum_a_and_b, no_ack=False)  
    

loop = asyncio.get_event_loop()
loop.create_task(rpc_subscriptions())
loop.run_forever()

# to run use:  python carrot_ask.py
```

## Buy me a coffee [thanks]
```no-highlight
0x6817b29f6a25B7BaE42158FAFad7b782415e4209 ETH
TZ1Hs1tkpPJFrPzmvo8xtHEKErXniV3x21 TRC (TRON)
```





