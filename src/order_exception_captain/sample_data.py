"""Demo-only store data. It contains no real customer or order information."""

from datetime import datetime, timedelta, timezone

from .domain import CarrierStatus, Order, OrderLine


def demo_orders() -> list[Order]:
    now = datetime.now(timezone.utc)
    return [
        Order(
            id="order-1042",
            customer_name="Alicja Nowak",
            customer_email="alicja@example.com",
            carrier="NorthStar Parcel",
            carrier_status=CarrierStatus.STALLED,
            hours_without_tracking_update=61,
            promised_delivery_date=now - timedelta(days=1),
            total_amount=18900,
            currency="PLN",
            lines=[OrderLine(sku="LAMP-01", title="Desk Lamp", quantity=1)],
        ),
        Order(
            id="order-1043",
            customer_name="Marek Kowalski",
            customer_email="marek@example.com",
            carrier="NorthStar Parcel",
            carrier_status=CarrierStatus.IN_TRANSIT,
            hours_without_tracking_update=10,
            promised_delivery_date=now + timedelta(days=2),
            total_amount=6500,
            currency="PLN",
            lines=[OrderLine(sku="MUG-02", title="Ceramic Mug", quantity=2)],
        ),
        Order(
            id="order-1044",
            customer_name="Tomasz Zielinski",
            customer_email="tomasz@example.com",
            carrier="NorthStar Parcel",
            carrier_status=CarrierStatus.LOST,
            hours_without_tracking_update=36,
            promised_delivery_date=now - timedelta(days=2),
            total_amount=8900,
            currency="PLN",
            lines=[OrderLine(sku="BAG-01", title="Canvas Tote Bag", quantity=1)],
        ),
    ]
