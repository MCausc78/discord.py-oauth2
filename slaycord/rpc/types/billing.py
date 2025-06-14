from __future__ import annotations

from typing import Literal

PaymentSourceType = Literal[
    0,  # UNKNOWN
    1,  # CARD
    2,  # PAYPAL
    3,  # GIROPAY
    4,  # SOFORT
    5,  # PRZELEWY24
    6,  # SEPA_DEBIT
    7,  # PAYSAFE_CARD
    8,  # GCASH
    9,  # GRABPAY_MY
    10,  # MOMO_WALLET
    11,  # VENMO
    12,  # GOPAY_WALLET
    13,  # KAKAOPAY
    14,  # BANCONTACT
    15,  # EPS
    16,  # IDEAL
    17,  # CASH_APP
    18,  # APPLE
    99,  # PAYMENT_REQUEST
]
