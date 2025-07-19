"""
The MIT License (MIT)

Copyright (c) 2025-present MCausc78

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

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
