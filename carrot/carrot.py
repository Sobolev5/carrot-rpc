from simple_print import sprint
import asyncio
import orjson
import uuid
import aiormq
import functools
from orjson import JSONDecodeError
from pydantic import ValidationError


class Carrot:
    def __init__(self, AMQP_URI, DEBUG=False):
        self.AMQP_URI = AMQP_URI
        self.DEBUG = DEBUG
        self.connection = None
        self.channel = None
        self.callback_queue = ""
        self.futures = {}
        self.loop = asyncio.get_event_loop()
        
    async def connect(self):
        self.connection = await aiormq.connect(self.AMQP_URI)
        self.channel = await self.connection.channel()
        declare_ok = await self.channel.queue_declare(exclusive=True, auto_delete=True)
        await self.channel.basic_consume(declare_ok.queue, self.on_response)
        self.callback_queue = declare_ok.queue
        if self.DEBUG:
            sprint(f"Carrot [DEBUG MODE] > declare_ok [OK] callback_queue={declare_ok.queue}", c="green", f=1) 
        return self

    async def on_response(self, message):
        future = self.futures.pop(message.header.properties.correlation_id)
        future.set_result(message.body)
        if self.DEBUG:
            sprint(f"Carrot [DEBUG MODE] > on_response [OK] message.body={message.body}", c="yellow", i=4, f=1)         

    async def call(self, outcoming_message_dict: dict, routing_key: str, no_reply=False) -> dict | None:
        correlation_id = "null" if no_reply else str(uuid.uuid4())
        future = self.loop.create_future()
        self.futures[correlation_id] = future
        outcoming_message_bytes = orjson.dumps(outcoming_message_dict)
        await self.channel.basic_publish(
            outcoming_message_bytes,
            routing_key=routing_key,
            properties=aiormq.spec.Basic.Properties(
                content_type="text/plain",
                correlation_id=correlation_id,
                reply_to="null" if no_reply else self.callback_queue,
            ),
        )

        if self.DEBUG:
            reply_to = "null" if no_reply else self.callback_queue
            sprint(f"Carrot [DEBUG MODE] > Call [OK] routing_key={routing_key} correlation_id={correlation_id} reply_to={reply_to}", c="yellow", i=4, f=1)  

        if no_reply:
            if self.DEBUG:
                sprint(f"Carrot [DEBUG MODE] > Finish [OK] no_reply={no_reply}", c="magenta", i=4, f=1)                
            return None
        else: 
            body = await future
            incoming_message_dict = orjson.loads(body.decode())
            if self.DEBUG:
                sprint(f"Carrot [DEBUG MODE] > Finish [OK] incoming_message_dict={incoming_message_dict}", c="magenta", i=4, f=1)             
            return incoming_message_dict


def carrot_ask(schema=None, DEBUG=None):
    def wrapper(func, *args, **kwargs):
        @functools.wraps(func)
        async def wrapped(message):

            if DEBUG:
                sprint(f"carrot_ask [DEBUG MODE] > Message.header.properties.reply_to={message.header.properties.reply_to}", c="green")    

            incoming_dict = None
            outcoming_dict = None
            error = None

            try:
                incoming_dict = orjson.loads(message.body.decode())  
                if schema:
                    incoming_dict = schema.validate(incoming_dict).dict()
            except ValidationError as error_message:
                error = f"carrot_ask [DEBUG MODE] > Pydantic schema error. Request body={message.body}. Error={error_message}"
            except JSONDecodeError as error_message:
                error = f"carrot_ask [DEBUG MODE] > Orjson parse dictionary error. Request body={message.body}. Error={error_message}"                  

            if incoming_dict and not error:
                if DEBUG:
                    sprint(incoming_dict, c="yellow", i=4)                    
                try:
                    outcoming_dict = await func(incoming_dict)
                    if not isinstance(outcoming_dict, dict):
                        raise Exception("Output data must be dict")
                except Exception as error_message:
                    error = f"carrot_ask [DEBUG MODE] > Error while call function={func.__name__} error={error_message}"

            if not error and outcoming_dict:
                if DEBUG:
                    sprint(f"carrot_ask [DEBUG MODE] > {outcoming_dict}", c="yellow", i=4) 
            else:
                error = {"error": error}
                if DEBUG:
                    sprint(f"carrot_ask [DEBUG MODE] > error={error}", c="red", i=4) 

            if message.header.properties.reply_to != "null":
                outcoming_dict_bytes = orjson.dumps(outcoming_dict or error)
                await message.channel.basic_publish(
                    outcoming_dict_bytes, routing_key=message.header.properties.reply_to,
                    properties=aiormq.spec.Basic.Properties(
                        correlation_id=message.header.properties.correlation_id
                    ),
                )
                if DEBUG:
                    sprint(f"carrot_ask [DEBUG MODE] > Reply message sended correlation_id={message.header.properties.correlation_id}", i=4, c="yellow")    

            await message.channel.basic_ack(message.delivery.delivery_tag)
            if DEBUG:
                sprint(f"carrot_ask [DEBUG MODE] > Basic_ack ok", c="magenta")   

        return wrapped
    return wrapper