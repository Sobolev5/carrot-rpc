import asyncio
import aiormq
from carrot import carrot_ask
from simple_print import sprint
from settings import AMQP_URI


@carrot_ask
async def sum_a_and_b(incoming_dict: dict) -> dict:
    sprint(incoming_dict, c="yellow", p=1)
    dct = {}
    dct["who_am_i"] = "i am rpc function mounted on another microservice"
    dct["sum"] = incoming_dict["a"] + incoming_dict["b"]
    return dct


async def rpc_subscriptions():
    connection = await aiormq.connect(AMQP_URI)
    channel = await connection.channel()
    sprint(f"AMQP RPC:     ready [yes]", c="green", p=1)
    sum_a_and_b__declared = await channel.queue_declare(f"another_microservice:sum_a_and_b", durable=True)
    await channel.basic_consume(sum_a_and_b__declared.queue, sum_a_and_b, no_ack=False)  
    

loop = asyncio.get_event_loop()
loop.create_task(rpc_subscriptions())
loop.run_forever()

# to run use:  python carrot_ask.py