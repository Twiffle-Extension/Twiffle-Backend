from aiohttp import web
import aiohttp_cors
from app.utils import GLOBAL_STATE
from app.ebay_utils import get_oauth_token, \
    streamer_place_order, StreamerPlaceOrderRequest

routes = web.RouteTableDef()


@routes.get('/queue/{queue_name}', name='auth_token')
async def queue_message(request):
    queue = GLOBAL_STATE.get_pubsub_or_create(request.match_info['queue_name'])
    queue.put(request)

    return web.json_response({
        "queue_size": queue.qsize()
    }, status=200, headers={
        "Access-Control-Allow-Origin": "*"
    })


@routes.post('/stream/raffle/start/{stream_id}')
async def raffle_start(request: web.Request):
    json_body = await request.json()

    raffle_type = json_body.get("raffle_type")  # custom, trivia, boundary, random
    raffle_metadata = json_body.get("raffle_metadata")
    if not raffle_type or raffle_type not in ["custom", "trivia", "boundary", "random"]:
        return web.json_response(status=400)

    return web.json_response({
        "start_time": "1540704237415",
        "raffle_id": "123",
        "payload": {
        }
    })


@routes.post('/stream/raffle/join/{raffle_id}')
async def raffle_join(request: web.Request):
    json_body = await request.json()

    stream_id = request.match_info.get('raffle_id')
    user_id = json_body.get('user_id')
    if not stream_id or not user_id:
        return web.json_response(status=400)

    return web.Response(status=200)


@routes.get('/stream/raffle/exists/{raffle_id}')
async def raffle_exist(request: web.Request):
    stream_id = request.match_info.get('raffle_id')
    if not stream_id:
        return web.json_response(status=400)

    return web.json_response({
        "exists": True if stream_id == '123' else False
    })


@routes.get('/stream/raffle/end/{raffle_id}')
async def raffle_end(request: web.Request):
    return web.json_response(status=200)


@routes.get('/stream/raffle/winner/{raffle_id}')
async def raffle_winner(request: web.Request):
    stream_id = request.match_info.get('raffle_id')

    return web.json_response({
        "user_id": '123'
    })


@routes.post('/stream/raffle/accept_win/{raffle_id}')
async def accept_win(request: web.Request):
    json_body = await request.json()

    stream_id = request.match_info.get('raffle_id')
    user_id = json_body.get('user_id')
    if not stream_id or not user_id:
        return web.json_response(status=400)

    return web.Response(status=200)


@routes.post('/stream/raffle/winner_details/{raffle_id}')
async def raffle_winner(request: web.Request):
    json_body = await request.json()

    stream_id = request.match_info.get('raffle_id')
    user_id = json_body.get('user_id')
    if not stream_id or not user_id:
        return web.json_response(status=400)

    return web.json_response({
        "user_id": '123'
    })


@routes.get('/test/ebay_oauth')
async def test_func_output(request):
    return web.json_response(
        await get_oauth_token()
    )


@routes.get('/test/place_order')
async def test_streamer_place_order(request):
    request_payload = StreamerPlaceOrderRequest()
    request_payload.contactEmail = "alastairparagas@gmail.com"
    request_payload.phoneNumber = "3054567710"
    request_payload.itemIds = ["v1|110384331764|410091898866"]
    request_payload.creditCard.billingAddress.addressLine1 = "5510 Imperial Drive"
    request_payload.creditCard.billingAddress.addressLine2 = "Apt 1234"
    request_payload.creditCard.billingAddress.city = "San Jose"
    request_payload.creditCard.billingAddress.postalCode = "95136"
    request_payload.creditCard.billingAddress.stateOrProvince = "CA"
    request_payload.creditCard.accountHolderName = "Alastair Paragas"
    request_payload.creditCard.firstName = "Alastair"
    request_payload.creditCard.lastName = "Paragas"
    request_payload.creditCard.brand = "Visa"
    request_payload.creditCard.cardNumber = "4111111111111111"
    request_payload.creditCard.cvvNumber = "012"
    request_payload.creditCard.expireMonth = "10"
    request_payload.creditCard.expireYear = "2023"

    return web.json_response(
        await streamer_place_order(request_payload)
    )


app = web.Application()
app.add_routes(routes)
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
})
for route in app.router.routes():
    cors.add(route)
web.run_app(app)
