import json
import logging
from datetime import date

import anthropic
import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import ChatMessage
from houseexpense.core.models import Deposit, Expense, Flat, House, MonthlySummary

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

def _prev_month(d):
    if d.month == 1:
        return d.replace(year=d.year - 1, month=12)
    return d.replace(month=d.month - 1)


def _build_user_context(user) -> str:
    today = date.today()
    current_month = today.replace(day=1)
    three_months_ago = _prev_month(_prev_month(current_month))

    lines = [
        f"=== LIVE DATA FROM SAMPRITY ABASON SYSTEM ===",
        f"User: {user.get_full_name() or user.username}",
        f"Role: {user.get_role_display()}",
        f"Today: {today.strftime('%B %d, %Y')}",
    ]

    # Flat owner's own flats
    flats = list(Flat.objects.filter(owner=user).select_related('house'))
    if flats:
        lines.append("\n--- Your Flats ---")
        for flat in flats:
            lines.append(
                f"Flat {flat.flat_number} | {flat.house.name} | "
                f"Monthly Charge: ৳{flat.monthly_charge}"
            )

    # Deposits for flat owner (last 3 months)
    if flats:
        deposits = Deposit.objects.filter(
            flat__in=flats, month__gte=three_months_ago
        ).select_related('category', 'flat').order_by('-month', '-deposit_date')

        lines.append("\n--- Your Deposits (Last 3 Months) ---")
        if deposits.exists():
            for d in deposits:
                lines.append(
                    f"{d.month.strftime('%B %Y')} | ৳{d.amount} | "
                    f"{d.category.name if d.category else 'Deposit'} | "
                    f"Flat {d.flat.flat_number} | Date: {d.deposit_date}"
                )
        else:
            lines.append("No deposits in the last 3 months.")

    # Houses: flat owner's houses + manager's house
    house_set = {flat.house for flat in flats}
    try:
        if user.role == 'manager' and hasattr(user, 'managed_house'):
            house_set.add(user.managed_house)
    except House.DoesNotExist:
        pass

    for house in house_set:
        lines.append(f"\n--- House: {house.name} ---")

        # Monthly summaries
        summaries = MonthlySummary.objects.filter(
            house=house, month__gte=three_months_ago
        ).order_by('-month')
        if summaries.exists():
            lines.append("Monthly Summaries:")
            for s in summaries:
                lines.append(
                    f"  {s.month.strftime('%B %Y')}: "
                    f"Income=৳{s.total_deposits} | "
                    f"Expenses=৳{s.total_expenses} | "
                    f"Balance=৳{s.balance}"
                )

        # Manager sees all expenses and deposits
        if user.role == 'manager':
            expenses = Expense.objects.filter(
                house=house, month__gte=three_months_ago
            ).select_related('category').order_by('-month', '-bill_date')
            if expenses.exists():
                lines.append("Expenses:")
                for e in expenses:
                    lines.append(
                        f"  {e.month.strftime('%B %Y')} | ৳{e.amount} | "
                        f"{e.category.name if e.category else 'Expense'} | "
                        f"{e.description[:60] if e.description else ''}"
                    )

            all_deposits = Deposit.objects.filter(
                house=house, month__gte=three_months_ago
            ).select_related('category', 'flat').order_by('-month', '-deposit_date')
            if all_deposits.exists():
                lines.append("All Deposits:")
                for d in all_deposits:
                    flat_info = f"Flat {d.flat.flat_number}" if d.flat else "General"
                    lines.append(
                        f"  {d.month.strftime('%B %Y')} | ৳{d.amount} | "
                        f"{flat_info} | {d.category.name if d.category else 'Deposit'}"
                    )

    return '\n'.join(lines)


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

        user_context = _build_user_context(request.user)
        system_prompt = (
            'You are a helpful AI assistant for Samprity Abason, a house expense management system. '
            'You have access to the user\'s real data shown below. '
            'Use this data to answer questions accurately and specifically. '
            'Format amounts with the ৳ symbol. Be concise and friendly.\n\n'
            + user_context
        )

        history = request.session.get('web_chat_history', [])
        history.append({'role': 'user', 'content': user_message})

        try:
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=1024,
                system=system_prompt,
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
