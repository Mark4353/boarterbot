from aiohttp import web

from app.payment_api import get_payment_api
from app.order_repo import find_order_by_payment_session_id, get_order_by_id, mark_order_paid, mark_revision_paid, set_payment_status
from app.models import get_user_by_id
from app import texts


def create_web_app(bot) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app.router.add_post("/webhook/payment", payment_webhook)
    return app


async def payment_webhook(request: web.Request) -> web.Response:
    data = await request.post()
    data_field = data.get("data", "")
    signature = data.get("signature", "")

    api = get_payment_api()
    if not api.verify_callback_signature(data_field, signature):
        return web.Response(status=400, text="invalid signature")

    payload = api.decode_callback_data(data_field)
    if not payload:
        return web.Response(status=400, text="invalid data")

    order_id_raw = str(payload.get("order_id") or "").strip()
    status = str(payload.get("status") or "").lower()
    if not order_id_raw:
        return web.Response(text="ok")

    order, payment_kind = await find_order_by_payment_session_id(order_id_raw)
    if not order and order_id_raw.isdigit():
        order = await get_order_by_id(int(order_id_raw))
        payment_kind = "order"

    if not order:
        return web.Response(text="ok")

    if status in {"success", "sandbox"}:
        if payment_kind == "revision":
            await mark_revision_paid(int(order["id"]))
        else:
            await mark_order_paid(int(order["id"]))
            await set_payment_status(int(order["id"]), "paid")

        bot = request.app.get("bot")
        if bot:
            client = await get_user_by_id(int(order["client_id"]))
            editor = await get_user_by_id(int(order["editor_id"])) if order.get("editor_id") else None
            amount_minor = int(order.get("agreed_price_minor") or 0)
            amount_label = f"{amount_minor / 100:.2f} {order.get('currency') or 'USD'}"

            if client:
                await bot.send_message(
                    client.telegram_id,
                    texts.tr(client.language, f"✅ Payment received for order #{order['id']}. Amount: {amount_label}", f"✅ Оплату за замовлення #{order['id']} отримано. Сума: {amount_label}"),
                )
            if editor:
                await bot.send_message(
                    editor.telegram_id,
                    texts.tr(editor.language, f"✅ Client paid for order #{order['id']}. You can start.", f"✅ Замовник оплатив замовлення #{order['id']}. Можете починати роботу."),
                )

    return web.Response(text="ok")
