import asyncio
from carrot import Carrot
from simple_print import sprint


AMQP_URI = "amqp://admin:password@127.0.0.1/vhost"


async def call_sum_a_and_b():
    # call_sum_a_and_b - function in another microservice (we want to call it)
  
    sprint(f"call_sum_a_and_b", с="green", s=1, p=1)

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