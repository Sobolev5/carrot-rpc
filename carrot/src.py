import asyncio
import functools
import uuid

import aiormq
import orjson
from orjson import JSONDecodeError
from pydantic import ValidationError


class CarrotCall:

    def __init__(self, *, AMQP_URI): # noqa
        self.AMQP_URI = AMQP_URI
        self.connection = None
        self.channel = None
        self.callback_queue = ""
        self.futures = {}
        self.loop = asyncio.get_event_loop()

    async def connect(self):
        """Connect to AMQP."""
        self.connection = await aiormq.connect(self.AMQP_URI)
        self.channel = await self.connection.channel()
        declare_ok = await self.channel.queue_declare(exclusive=True, auto_delete=True)
        await self.channel.basic_consume(declare_ok.queue, self.on_response)
        self.callback_queue = declare_ok.queue
        return self

    async def on_response(self, message):
        """Catch response from future."""
        future = self.futures.pop(message.header.properties.correlation_id)
        future.set_result(message.body)

    async def call(
            self,
            outcoming_message_dict:dict,
            routing_key:str,
            reply:bool=True,
            timeout:int=7) -> dict | None:
        """Call related function."""
        correlation_id = str(uuid.uuid4()) if reply else "no_reply"
        future = self.loop.create_future()
        self.futures[correlation_id] = future
        outcoming_message_bytes = orjson.dumps(outcoming_message_dict)
        await self.channel.basic_publish(
            outcoming_message_bytes,
            routing_key=routing_key,
            properties=aiormq.spec.Basic.Properties(
                content_type="text/plain",
                correlation_id=correlation_id,
                reply_to=self.callback_queue if reply else "no_reply",
            ),
        )

        if reply:
            try:
                body = await asyncio.wait_for(future, timeout=timeout)
            except asyncio.TimeoutError as exc:
                raise asyncio.TimeoutError(
                    f"Remote service is not response timeout={timeout}"
                ) from exc

            incoming_message_dict = orjson.loads(body.decode())
            return incoming_message_dict
        else:
            return None


def carrot_ask(schema=None, force_ask=True):
    """Ask to CarrotCall.call."""
    def wrapper(func, *args, **kwargs):
        @functools.wraps(func)
        async def wrapped(message):

            if force_ask:
                await message.channel.basic_ack(message.delivery.delivery_tag)

            incoming_data = None
            outcoming_data = None

            try:
                incoming_data = orjson.loads(message.body.decode())
                if schema:
                    incoming_data = schema(**incoming_data)
            except ValidationError as exc:
                raise Exception(
                    f"Msg body={message.body}; Error={exc}"
                ) from exc
            except JSONDecodeError as exc:
                raise Exception(
                    f"Msg body={message.body}; Error={exc}"
                ) from exc

            if incoming_data:

                try:
                    outcoming_data = await func(incoming_data)
                    if not isinstance(outcoming_data, dict):
                        raise Exception("Output data must be dict")
                except Exception as exc:
                    raise Exception(f"{exc}") from exc

            else:
                raise Exception("Msg body empty")

            if message.header.properties.reply_to != "no_reply":
                outcoming_data_bytes = orjson.dumps(outcoming_data)
                await message.channel.basic_publish(
                    outcoming_data_bytes,
                    routing_key=message.header.properties.reply_to,
                    properties=aiormq.spec.Basic.Properties(
                        correlation_id=message.header.properties.correlation_id
                    ),
                )

            if not force_ask:
                await message.channel.basic_ack(message.delivery.delivery_tag)

        return wrapped
    return wrapper
