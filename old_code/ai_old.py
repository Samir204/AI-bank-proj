import os
import json
import concurrent.futures
from datetime import datetime

from google import genai
from google.genai import types

from DBsys import (
    get_account_overview,
    get_transaction_history,
    get_upcoming_payments_for_user,
    get_recommendations_for_user,
    log_audit_event,
)

# ============================================================================
# Client setup
# ============================================================================
# NEVER hardcode API keys in source, especially in a repo you plan to push to
# GitHub  a key sitting in plaintext in your portfolio project is a leaked
# key the moment the repo goes public. Set it in your shell instead:



#   export GEMINI_API_KEY="your-key-here"
#
# (or put it in a .env file loaded with python dotenv, if you'd rather not
# type it every session).



client = genai.Client(api_key="")
MODEL = "gemini-3.1-flash-lite"

COMMODITIES_FILE = "commodities.json"
SEARCH_TIMEOUT_SECONDS = 8  # how long we wait for a live web grounded answer
                            # before falling back to the cached JSON

history = []


# ============================================================================
# Helpers
# ============================================================================

def _parse_json_response(text):
    """
    Gemini sometimes wraps JSON in ```json ... ``` fences even when told to
    return ONLY JSON. Strip that before parsing instead of letting
    json.loads() blow up on real (if uncommon) responses.
    """
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def _load_commodities_cache():
    with open(COMMODITIES_FILE, "r") as f:
        return json.load(f)


def _build_bank_context(user_id):
    """
    Pulls the user's own bank data (READ-ONLY) so the assistant can answer
    'my balance/my payments/my recommendations' questions accurately.

    IMPORTANT: this only ever calls read functions from DBsys get_*, never
    transfer_funds/withdraw_*/deposit_funds/etc. The chat assistant can look
    things up and advise, but it never gets a path to actually move money;
    any real transaction still has to go through your normal, explicitly
    confirmed flow.
    """
    accounts = get_account_overview(user_id)
    account_lines = [
        f"- Account #{a[3]} (IBAN {a[4]}): balance {a[5]} {a[6]}, status {a[7]}"
        for a in accounts
    ] or ["- no accounts found"]

    upcoming = get_upcoming_payments_for_user(user_id)
    upcoming_lines = [
        f"- {u[4]} {u[3]} due {u[5]}" for u in upcoming
    ] or ["- none"]

    recs = get_recommendations_for_user(user_id, limit=5)
    rec_lines = [
        f"- {r[1]}: {r[2]} (confidence {r[3]})" for r in recs
    ] or ["- none yet"]

    return (
        "USER'S BANK ACCOUNTS:\n" + "\n".join(account_lines) +
        "\n\nUPCOMING PAYMENTS:\n" + "\n".join(upcoming_lines) +
        "\n\nRECENT AI RECOMMENDATIONS ALREADY GIVEN TO THIS USER:\n" + "\n".join(rec_lines)
    )


def _ask_with_search(prompt, timeout=SEARCH_TIMEOUT_SECONDS):
    """
    Tries to answer using live Google Search grounding so price/market
    questions get real, current data instead of the model's training data
    guess. Returns the response text, or None if it didn't come back within
    `timeout` seconds the caller should fall back to the cached
    commodities.json in that case.
    """
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(tools=[grounding_tool])

    def _call():
        return client.models.generate_content(model=MODEL, contents=prompt, config=config)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_call)
        try:
            response = future.result(timeout=timeout)
            return response.text
        except concurrent.futures.TimeoutError:
            return None
        except Exception as err:
            print(f"[web search warning] {err}")
            return None


def _ask_with_cache(prompt):
    """Fallback path: no live web access in time, answer using the cached commodities.json."""
    cache = _load_commodities_cache()
    cache_note = (
        f"NOTE: live web search wasn't available in time, so answer using ONLY "
        f"the cached prices below (as of {cache['LastUpdated']}). Clearly tell "
        f"the user these prices may be out of date and to double check before "
        f"acting on them.\n\nCACHED MARKET DATA:\n{json.dumps(cache, indent=2)}"
    )
    full_prompt = f"{cache_note}\n\n{prompt}"
    response = client.models.generate_content(model=MODEL, contents=full_prompt)
    return response.text


# ============================================================================
# Chat
# ============================================================================

def chat(user_id):
    """
    Interactive chat loop for an already authenticated user.

    user_id should come from your login flow (e.g. validate_session()) 
    this function assumes login already happened; it doesn't do auth itself.
    Every question is answered with the user's own bank context attached,
    and every exchange is written to the audit log for traceability (the
    same principle as logging any other sensitive account activity).
    """
    bank_context = _build_bank_context(user_id)

    while True:
        user_input = input(" --> You: ")

        if user_input.lower() in ("quit", "exit"):
            print("bye <3")
            break

        history.append({"role": "user", "input": user_input})

        prompt = (
            "You are a banking assistant. Use the account data below to answer "
            "the user's question about their own finances or about markets/"
            "commodities/currencies they ask about. You are NOT able to move "
            "money yourself if the user wants to actually make a transaction, "
            "tell them to do it through the app directly; only give information "
            "and advice.\n\n"
            f"{bank_context}\n\nUSER QUESTION: {user_input}"
        )

        response_text = _ask_with_search(prompt)
        used_cache = False
        if response_text is None:
            response_text = _ask_with_cache(prompt)
            used_cache = True

        history.append({"role": "AI", "output": response_text})

        log_audit_event(
            user_id, "AI_CHAT_QUERY",
            details={"question": user_input, "used_cached_prices": used_cache}
        )

        print(response_text)
        print()


def get_history(history):
    for entry in history:
        print()
        print(entry)
        print()


# ============================================================================
# Commodities refresh (batch job run periodically, e.g. via cron)
# ============================================================================

def update_commodities():
    """
    Refreshes commodities.json with live prices via Google Search grounding.

    Without the grounding tool, Gemini has no way to know today's actual
    commodity/currency prices and would just generate plausible looking
    numbers from its training data which is what this function did before.
    Every call below now includes the search tool and explicitly asks the
    model to look the price up, so the cache this feeds chat()'s fallback
    path actually holds real data.
    """
    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(tools=[grounding_tool])

    def _fetch(prompt):
        response = client.models.generate_content(model=MODEL, contents=prompt, config=config)
        return _parse_json_response(response.text)

    with open(COMMODITIES_FILE, "r") as f:
        data = json.load(f)

    precious_metals = _fetch("""
        Search for today's spot prices in USD and return ONLY JSON in this format,
        no markdown, no commentary:
        {"Gold": number, "Silver": number, "Platinum": number, "Palladium": number}
    """)

    energy = _fetch("""
        Search for today's prices in USD and return ONLY JSON in this format,
        no markdown, no commentary:
        {"BrentCrude": number, "WTICrude": number, "NaturalGas": number,
         "HeatingOil": number, "Gasoline": number}
    """)

    industrial_metals = _fetch("""
        Search for today's prices in USD per metric ton and return ONLY JSON in
        this format, no markdown, no commentary:
        {"Copper": number, "Aluminium": number, "Nickel": number,
         "Zinc": number, "Lead": number, "Tin": number}
    """)

    agriculture = _fetch("""
        Search for today's prices in USD and return ONLY JSON in this format,
        no markdown, no commentary:
        {"Wheat": number, "Corn": number, "Soybeans": number, "Rice": number,
         "Coffee": number, "Cocoa": number, "Sugar": number, "Cotton": number}
    """)

    livestock = _fetch("""
        Search for today's prices in USD and return ONLY JSON in this format,
        no markdown, no commentary:
        {"LiveCattle": number, "LeanHogs": number, "FeederCattle": number}
    """)

    currencies = _fetch("""
        Search for today's exchange rates against USD and return ONLY JSON in
        this format, no markdown, no commentary:
        {"USD": number, "EUR": number, "GBP": number, "JPY": number, "CAD": number,
         "AUD": number, "CHF": number, "NZD": number, "CNY": number, "HKD": number,
         "SEK": number, "NOK": number, "DKK": number, "SGD": number, "INR": number,
         "BRL": number, "MXN": number, "ZAR": number, "TRY": number, "RUB": number}
    """)

    data["LastUpdated"] = datetime.now().isoformat()
    data["Commodities"]["PreciousMetals"].update(precious_metals)
    data["Commodities"]["Energy"].update(energy)
    data["Commodities"]["IndustrialMetals"].update(industrial_metals)
    data["Commodities"]["Agriculture"].update(agriculture)
    data["Commodities"]["Livestock"].update(livestock)
    data["Currencies"].update(currencies)

    with open(COMMODITIES_FILE, "w") as f:
        json.dump(data, f, indent=4)

    print("Commodity prices updated.")


# update_commodities()
chat(user_id=1)
# get_history(history)
