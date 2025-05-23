from flask import Flask, request
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, Updater
import stripe
import os

# ========== CONFIGURAÇÕES ==========
BOT_TOKEN = '7689566074:AAHuRa5oikd0MHFkiVovlNVFC0XhLQ2QZb8'
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PAYMENT_LINK = os.getenv("STRIPE_PAYMENT_LINK")  # Ex: https://buy.stripe.com/test_xxx
PIX_INSTRUCAO = os.getenv("PIX_INSTRUCAO")  # Ex: chave aleatória ou CNPJ

CANAL_LINK = os.getenv("CANAL_LINK")  # Ex: https://t.me/+seu_link
PORT = int(os.environ.get("PORT", 5000))

# Bot e Stripe
bot = telegram.Bot(token=BOT_TOKEN)
stripe.api_key = STRIPE_SECRET_KEY
app = Flask(__name__)

# Armazena país escolhido
user_country = {}

# ========== BOT ==========
def start(update, context):
    telegram_id = update.effective_user.id

    keyboard = [
        [InlineKeyboardButton("Brasil", callback_data='pais_BR')],
        [InlineKeyboardButton("United States", callback_data='pais_US')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(
        chat_id=telegram_id,
        text="Olá! Welcome!\n\nPor favor selecione seu país meu amor / Please select your country, sweetie:",
        reply_markup=reply_markup
    )

def responder_pais(update, context):
    query = update.callback_query
    telegram_id = query.from_user.id
    pais = query.data.split("_")[1]
    user_country[telegram_id] = pais

    if pais == 'BR':
        query.message.reply_text(
            "O acesso ao canal meu canal VIP custa R$25.\n\n"
            f"Realize o pagamento via Pix usando a chave abaixo:\n\n{PIX_INSTRUCAO}\n\n"
            "Após o pagamento, envie o comprovante aqui mesmo para liberar o acesso.",
            parse_mode="Markdown"
        )
    elif pais == 'US':
        query.message.reply_text(
            "Access costs **$6.99 USD**.\n\n"
            "Click below to pay securely with Stripe:",
            parse_mode="Markdown"
        )
        query.message.reply_text(STRIPE_PAYMENT_LINK)

# ========== WEBHOOK STRIPE ==========
@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            metadata = session.get('metadata', {})
            telegram_id = metadata.get('telegram_id')

            if telegram_id:
                bot.send_message(
                    chat_id=int(telegram_id),
                    text=f"Pagamento confirmado com sucesso!\n\nAcesse agora o canal VIP:\n{CANAL_LINK}"
                )
    except Exception as e:
        print(f"Erro no webhook: {e}")
        return "Erro", 400

    return "OK", 200

# ========== ROTA DE PING ==========
@app.route("/", methods=["GET", "HEAD"])
def health_check():
    return "Bot ativo!", 200

# ========== INICIALIZAÇÃO ==========
def iniciar_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(responder_pais, pattern="^pais_"))
    updater.start_polling()
    print("Bot rodando...")
    updater.idle()

# Iniciar tudo
if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT)).start()
    iniciar_bot()
