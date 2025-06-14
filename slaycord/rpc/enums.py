from __future__ import annotations

from ..enums import Enum


class Opcode(Enum):
    handshake = 0
    frame = 1
    close = 2
    ping = 3
    pong = 4


class PaymentSourceType(Enum):
    unknown = 0
    card = 1
    paypal = 2
    giropay = 3
    sofort = 4
    przzelewy24 = 5
    sepa_debit = 6
    paysafecard = 7
    gcash = 8
    grabpay = 9
    momo_wallet = 10
    venmo = 11
    gopay_wallet = 12
    kakaopay = 13
    bancontact = 14
    eps = 15
    ideal = 16
    cash_app = 17
    payment_request = 99
