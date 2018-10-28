from typing import Dict, Union, List
import aiohttp.web
from app.utils import GLOBAL_STATE, string_to_base64


async def get_oauth_token() -> Union[Dict[str, str], None]:
    environment_settings = GLOBAL_STATE.get_environment_settings()
    base_api_url = environment_settings.get("EBAY_BASE_API_URL")
    authorization_token = string_to_base64(
        "{client_id}:{client_secret}".format(
            client_id=environment_settings.get("EBAY_CLIENT_ID"),
            client_secret=environment_settings.get("EBAY_CLIENT_SECRET")
        )
    )

    GLOBAL_STATE.access_token = None
    session = aiohttp.ClientSession()
    async with session.post(
        url="{base_api_url}/identity/v1/oauth2/token".format(base_api_url=base_api_url),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic {authorization_token}".format(
                authorization_token=authorization_token
            )
        },
        data={
            "grant_type": "client_credentials",
            "redirect_uri": "{hostname}".format(
                hostname=environment_settings.get('HOSTNAME')
            ),
            "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/buy.guest.order"
        }
    ) as response:
        response_body = await response.json()
        GLOBAL_STATE.access_token = response_body.get('access_token')
    await session.close()

    return GLOBAL_STATE.access_token


class Address:
    addressLine1 = None
    addressLine2 = None
    city = None
    country = "US"
    postalCode = None
    stateOrProvince = None


class StreamerPlaceOrderRequest:
    class CreditCard:
        billingAddress = Address()
        accountHolderName = None
        firstName = None
        lastName = None
        brand = None  # Visa, MasterCard, AmEx, Discover
        cardNumber = None
        cvvNumber = None
        expireMonth = None
        expireYear = None

    creditCard: CreditCard = CreditCard()
    itemIds: List[str] = []
    contactEmail = None
    phoneNumber = None


class ViewerPlaceOrderRequest:
    class Recipient:
        shippingAddress = Address()
        phoneNumber = None
        firstName = None
        lastName = None

    recipient: Recipient = Recipient()


async def streamer_place_order(place_order_request: StreamerPlaceOrderRequest) -> str:
    environment_settings = GLOBAL_STATE.get_environment_settings()
    base_api_url = environment_settings.get("EBAY_BASE_API_URL")

    checkout_session_id = None
    session = aiohttp.ClientSession()
    token: str = await get_oauth_token()
    async with session.post(
        url="{base_api_url}/buy/order/v1/guest_checkout_session/initiate".format(
            base_api_url=base_api_url
        ),
        json={
            "contactEmail": place_order_request.contactEmail,
            "contactFirstName": place_order_request.creditCard.firstName,
            "contactLastName": place_order_request.creditCard.lastName,
            "creditCard": {
                "accountHolderName": place_order_request.creditCard.accountHolderName,
                "billingAddress": {
                  "addressLine1": place_order_request.creditCard.billingAddress.addressLine1,
                  "addressLine2": place_order_request.creditCard.billingAddress.addressLine2,
                  "city": place_order_request.creditCard.billingAddress.city,
                  "country": place_order_request.creditCard.billingAddress.country,
                  "firstName": place_order_request.creditCard.firstName,
                  "lastName": place_order_request.creditCard.lastName,
                  "postalCode": place_order_request.creditCard.billingAddress.postalCode,
                  "stateOrProvince": place_order_request.creditCard.billingAddress.stateOrProvince
                },
                "brand": place_order_request.creditCard.brand,
                "cardNumber": place_order_request.creditCard.cardNumber,
                "cvvNumber": place_order_request.creditCard.cvvNumber,
                "expireMonth": place_order_request.creditCard.expireMonth,
                "expireYear": place_order_request.creditCard.expireYear
              },
            "lineItemInputs": [
                {
                  "itemId": item_id,
                  "quantity": 1
                }
                for item_id in place_order_request.itemIds
            ],
            "shippingAddress": {
                "addressLine1": place_order_request.creditCard.billingAddress.addressLine1,
                "addressLine2": place_order_request.creditCard.billingAddress.addressLine2,
                "city": place_order_request.creditCard.billingAddress.city,
                "country": place_order_request.creditCard.billingAddress.country,
                "phoneNumber": place_order_request.phoneNumber,
                "postalCode": place_order_request.creditCard.billingAddress.postalCode,
                "recipient": "{first_name} {last_name}".format(
                    first_name=place_order_request.creditCard.firstName,
                    last_name=place_order_request.creditCard.lastName
                ),
                "stateOrProvince": place_order_request.creditCard.billingAddress.stateOrProvince
            }
        },
        headers={
            "Authorization": "Bearer {token}".format(
                token=token
            )
        }
    ) as response:
        response_body = await response.json()
        checkout_session_id = response_body.get('checkoutSessionId')
    await session.close()

    return checkout_session_id


async def viewer_place_order(checkout_session_id: str, place_order_request: ViewerPlaceOrderRequest) -> str:
    environment_settings = GLOBAL_STATE.get_environment_settings()
    base_api_url = environment_settings.get("EBAY_BASE_API_URL")

    purchase_order_id = None
    session = aiohttp.ClientSession()
    token: str = await get_oauth_token()
    async with session.post(
        url="{base_api_url}/buy/order/v1/guest_checkout_session/{checkout_session_id}/update_shipping_address".format(
            base_api_url=base_api_url,
            checkout_session_id=checkout_session_id
        ),
        json={
            "shippingAddress": {
                "addressLine1": place_order_request.recipient.shippingAddress.addressLine1,
                "addressLine2": place_order_request.recipient.shippingAddress.addressLine2,
                "city": place_order_request.recipient.shippingAddress.city,
                "country": place_order_request.recipient.shippingAddress.country,
                "phoneNumber": place_order_request.recipient.phoneNumber,
                "postalCode": place_order_request.recipient.shippingAddress.postalCode,
                "recipient": "{first_name} {last_name}".format(
                    first_name=place_order_request.recipient.firstName,
                    last_name=place_order_request.recipient.lastName
                ),
                "stateOrProvince": place_order_request.recipient.shippingAddress.stateOrProvince
            }
        }
    ) as response:
        response_body = await response.json()
        checkout_session_id = response_body.get("checkoutSessionId")
    async with session.post(
        url="https://apix.sandbox.ebay.com/buy/order/v1/guest_checkout_session/{checkout_id}/place_order".format(
            checkout_id=checkout_session_id
        ),
        headers={
            "Authorization": "Bearer {token}".format(
                token=token
            )
        },
        json={}
    ) as response:
        response_body = await response.json()
        purchase_order_id = response_body.get("purchaseOrderId")
    await session.close()

    return purchase_order_id
