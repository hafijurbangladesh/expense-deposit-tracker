import json
import logging

import anthropic
import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import ChatMessage

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_conversation_history(phone_number: str, limit: int = 10) -> list[dict]:
    """Return the last `limit` messages for a phone number as Anthropic turns."""
    messages = ChatMessage.objects.filter(phone_number=phone_number).order_by('-created_at')[:limit]
    history = []
    for msg in reversed(messages):
        role = 'user' if msg.direction == 'incoming' else 'assistant'
        history.append({'role': role, 'content': msg.message})
    return history


# ---------------------------------------------------------------------------
# Web chatbot (system UI)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    'You are a helpful assistant for Samprity Abason, a house expense management system. '
    'You help flat owners and managers with questions about expenses, service charges, '
    'payments, reports, and general house management queries. '
    'Keep replies concise, clear, and friendly.'
)


@login_required
def web_chat(request):
    if request.method == 'GET':
        if request.GET.get('new'):
            request.session.pop('web_chat_history', None)
        return render(request, 'chatbot/chat.html')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid request'}, status=400)

        if not user_message:
            return JsonResponse({'error': 'Empty message'}, status=400)

        history = request.session.get('web_chat_history', [])
        history.append({'role': 'user', 'content': user_message})

        try:
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=history[-20:],
            )
            reply = response.content[0].text
        except Exception as exc:
            logger.error('Claude API error: %s', exc)
            return JsonResponse({'error': 'AI service unavailable. Please try again.'}, status=500)

        history.append({'role': 'assistant', 'content': reply})
        request.session['web_chat_history'] = history
        request.session.modified = True

        return JsonResponse({'reply': reply})

    return HttpResponse(status=405)


# ---------------------------------------------------------------------------
# WhatsApp helpers
# ---------------------------------------------------------------------------

def _ask_claude(phone_number: str, user_message: str) -> str:
    """Send message to Claude with conversation history and return reply text."""
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    history = _get_conversation_history(phone_number)
    history.append({'role': 'user', 'content': user_message})

    response = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=1024,
        system=(
            'You are a helpful assistant for a house expense management system. '
            'You help flat owners and managers with questions about expenses, '
            'service charges, payments, and general house management queries. '
            'Keep replies concise and friendly.'
        ),
        messages=history,
    )
    return response.content[0].text


def _send_whatsapp_message(to: str, text: str) -> None:
    """Send a text message via the WhatsApp Business API."""
    url = f'https://graph.facebook.com/v18.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages'
    headers = {
        'Authorization': f'Bearer {settings.WHATSAPP_TOKEN}',
        'Content-Type': 'application/json',
    }
    payload = {
        'messaging_product': 'whatsapp',
        'recipient_type': 'individual',
        'to': to,
        'type': 'text',
        'text': {'body': text},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    if not resp.ok:
        logger.error('WhatsApp send failed: %s %s', resp.status_code, resp.text)
    resp.raise_for_status()


# ---------------------------------------------------------------------------
# Webhook
# ---------------------------------------------------------------------------

@csrf_exempt
def webhook(request):
    if request.method == 'GET':
        return _verify_webhook(request)
    if request.method == 'POST':
        return _handle_incoming(request)
    return HttpResponse(status=405)


def _verify_webhook(request):
    """Handle Meta webhook verification challenge."""
    mode = request.GET.get('hub.mode')
    token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')

    if mode == 'subscribe' and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info('WhatsApp webhook verified.')
        return HttpResponse(challenge, content_type='text/plain')

    logger.warning('Webhook verification failed.')
    return HttpResponse('Forbidden', status=403)


def _handle_incoming(request):
    """Process incoming WhatsApp messages."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        entry = data['entry'][0]
        change = entry['changes'][0]
        value = change['value']

        # Ignore status updates (delivered, read, etc.)
        if 'messages' not in value:
            return HttpResponse('OK')

        message = value['messages'][0]
        if message.get('type') != 'text':
            return HttpResponse('OK')

        phone_number = message['from']
        user_text = message['text']['body']

        # Persist incoming message
        ChatMessage.objects.create(
            phone_number=phone_number,
            direction='incoming',
            message=user_text,
        )

        # Get Claude's reply
        reply = _ask_claude(phone_number, user_text)

        # Persist outgoing message
        ChatMessage.objects.create(
            phone_number=phone_number,
            direction='outgoing',
            message=reply,
        )

        # Send reply via WhatsApp
        _send_whatsapp_message(phone_number, reply)

    except (KeyError, IndexError) as exc:
        logger.error('Unexpected webhook payload: %s', exc)

    return HttpResponse('OK')
