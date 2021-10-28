import asyncio
import json
import uuid
import aiormq
from simple_print import sprint


class Carrot:
    def __init__(self, AMQP_URI):
        self.AMQP_URI = AMQP_URI
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
        return self

    async def on_response(self, message):
        future = self.futures.pop(message.header.properties.correlation_id)
        future.set_result(message.body)

    async def call(self, outcoming_message_dict, routing_key):
        correlation_id = str(uuid.uuid4())
        future = self.loop.create_future()
        self.futures[correlation_id] = future
        outcoming_message_bytes = json.dumps(outcoming_message_dict).encode()
        await self.channel.basic_publish(
            outcoming_message_bytes,
            routing_key=routing_key,
            properties=aiormq.spec.Basic.Properties(
                content_type="text/plain",
                correlation_id=correlation_id,
                reply_to=self.callback_queue,
            ),
        )
        body = await future
        incoming_message_dict = json.loads(body.decode())
        return incoming_message_dict


def carrot_ask(func):
    async def wrapped(message):
        
        incoming_dict = None
        try:
            incoming_dict = json.loads(message.body.decode())  
        except Exception as error_message:
            sprint(f"ERROR REQUEST. Dictionary required. Request body={message.body}. Error={error_message}", c="red", s=1, p=1)
        
        outcoming_dict = None
        if incoming_dict:
            try:
                outcoming_dict = await func(incoming_dict)
            except Exception as error_message:
                sprint(f"ERROR RESPONSE. Error {error_message}", c="red", s=1, p=1)

        if outcoming_dict and isinstance(outcoming_dict, dict):
            outcoming_dict_bytes = json.dumps(outcoming_dict).encode()
            await message.channel.basic_publish(
                outcoming_dict_bytes, routing_key=message.header.properties.reply_to,
                properties=aiormq.spec.Basic.Properties(
                    correlation_id=message.header.properties.correlation_id
                ),
            )
            await message.channel.basic_ack(message.delivery.delivery_tag)
        else:
            if outcoming_dict is not None:
                sprint(f"ERROR RESPONSE. Function with decorator @carrot_ask must return a dictionary", c="red", s=1, p=1)

    return wrapped