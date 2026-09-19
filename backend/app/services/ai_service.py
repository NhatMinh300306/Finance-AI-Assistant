"""
AI Service — Gemini integration with tool/function-based architecture.

The AI does NOT directly invent financial data. Instead, it uses structured
tool calls to query the database, and then generates natural-language
responses based on real data.

This module is isolated so another LLM provider can easily replace Gemini.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import google.generativeai as genai
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import DEFAULT_CATEGORIES
from app.services.transaction_service import (
    create_transaction,
    calculate_balance,
    calculate_category_spending,
    get_monthly_summary,
    get_recent_transactions,
    get_transactions,
    get_spending_for_period,
    get_income_for_period,
)
from app.services.analytics_service import (
    get_financial_summary,
    detect_unusual_spending,
    get_spending_trend,
)

logger = logging.getLogger(__name__)

settings = get_settings()

# Configure Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

# ---------- Tool definitions for Gemini function calling ----------

TOOL_DEFINITIONS = [
    {
        "name": "add_transaction",
        "description": (
            "Add a new financial transaction (income or expense) to the user's records. "
            "Use this when the user tells you about money they spent or received."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "The transaction amount in yuan (must be positive)",
                },
                "transaction_type": {
                    "type": "string",
                    "enum": ["income", "expense"],
                    "description": "Whether this is income or an expense",
                },
                "category": {
                    "type": "string",
                    "description": f"Category for the transaction. Choose from: {', '.join(DEFAULT_CATEGORIES)}",
                },
                "description": {
                    "type": "string",
                    "description": "A brief description of the transaction",
                },
            },
            "required": ["amount", "transaction_type", "category"],
        },
    },
    {
        "name": "get_balance",
        "description": "Get the user's current financial balance, total income, and total expenses.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_category_spending",
        "description": "Get spending breakdown by category, optionally for a specific time period.",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["all", "this_month", "last_month", "this_week"],
                    "description": "Time period to analyze",
                },
            },
        },
    },
    {
        "name": "get_monthly_summary",
        "description": "Get monthly income, expense, and savings summary for recent months.",
        "parameters": {
            "type": "object",
            "properties": {
                "months": {
                    "type": "integer",
                    "description": "Number of months to look back (default 6)",
                },
            },
        },
    },
    {
        "name": "get_recent_transactions",
        "description": "Get the user's recent transactions for the last N days.",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back (default 7)",
                },
            },
        },
    },
    {
        "name": "get_financial_summary",
        "description": "Get a comprehensive financial overview including balance, category breakdown, and monthly trends.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "detect_unusual_spending",
        "description": "Check if any spending categories are unusually high compared to last month.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_spending_for_category",
        "description": "Get total spending for a specific category, optionally for a specific period.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "The spending category to query",
                },
                "period": {
                    "type": "string",
                    "enum": ["all", "this_month", "last_month", "this_week", "today"],
                    "description": "Time period to query",
                },
            },
            "required": ["category"],
        },
    },
    {
        "name": "create_budget_plan",
        "description": "Generate a budget plan based on the user's actual spending data.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
]


def _get_period_dates(period: str) -> tuple[datetime, datetime]:
    """Convert period string to start/end datetime."""
    now = datetime.now(timezone.utc)
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now
    elif period == "this_week":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now
    elif period == "this_month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, now
    elif period == "last_month":
        first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = first_of_this_month - timedelta(seconds=1)
        start = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, end
    else:  # "all"
        return datetime(2000, 1, 1, tzinfo=timezone.utc), now


def _execute_tool(
    tool_name: str,
    args: dict,
    db: Session,
    user_id: int,
) -> dict:
    """Execute a tool call and return the result as a dictionary."""
    try:
        if tool_name == "add_transaction":
            txn = create_transaction(
                db=db,
                user_id=user_id,
                amount=args["amount"],
                transaction_type=args["transaction_type"],
                category=args.get("category", "Other"),
                description=args.get("description"),
            )
            return {
                "success": True,
                "transaction": {
                    "id": txn.id,
                    "amount": txn.amount,
                    "type": txn.transaction_type.value,
                    "category": txn.category,
                    "description": txn.description,
                    "date": txn.transaction_date.isoformat(),
                },
            }

        elif tool_name == "get_balance":
            return calculate_balance(db, user_id)

        elif tool_name == "get_category_spending":
            period = args.get("period", "all")
            start_date, end_date = _get_period_dates(period)
            categories = calculate_category_spending(
                db, user_id, start_date=start_date, end_date=end_date
            )
            return {"period": period, "categories": categories}

        elif tool_name == "get_monthly_summary":
            months = args.get("months", 6)
            return {"months": get_monthly_summary(db, user_id, months)}

        elif tool_name == "get_recent_transactions":
            days = args.get("days", 7)
            txns = get_recent_transactions(db, user_id, days=days)
            return {
                "days": days,
                "transactions": [
                    {
                        "id": t.id,
                        "amount": t.amount,
                        "type": t.transaction_type.value,
                        "category": t.category,
                        "description": t.description,
                        "date": t.transaction_date.isoformat(),
                    }
                    for t in txns
                ],
            }

        elif tool_name == "get_financial_summary":
            return get_financial_summary(db, user_id)

        elif tool_name == "detect_unusual_spending":
            alerts = detect_unusual_spending(db, user_id)
            return {"alerts": alerts}

        elif tool_name == "get_spending_for_category":
            category = args["category"]
            period = args.get("period", "all")
            start_date, end_date = _get_period_dates(period)
            total = get_spending_for_period(
                db, user_id, start_date, end_date, category=category
            )
            return {
                "category": category,
                "period": period,
                "total_spending": total,
            }

        elif tool_name == "create_budget_plan":
            # Build budget suggestions from actual spending data
            categories = calculate_category_spending(db, user_id)
            balance_data = calculate_balance(db, user_id)
            monthly = get_monthly_summary(db, user_id, months=3)

            avg_monthly_expense = 0.0
            avg_monthly_income = 0.0
            if monthly:
                avg_monthly_expense = sum(m["total_expense"] for m in monthly) / len(monthly)
                avg_monthly_income = sum(m["total_income"] for m in monthly) / len(monthly)

            return {
                "current_spending": categories,
                "average_monthly_income": round(avg_monthly_income, 2),
                "average_monthly_expense": round(avg_monthly_expense, 2),
                "balance": balance_data["balance"],
                "suggestion": (
                    "Based on your actual spending data. "
                    "The AI should provide personalized budget recommendations."
                ),
            }

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        logger.error(f"Tool execution error ({tool_name}): {e}")
        return {"error": str(e)}


# System prompt for the AI
SYSTEM_PROMPT = """You are FinMate, an AI personal finance assistant. You help users manage their personal finances by recording transactions, analyzing spending, and providing budgeting advice.

IMPORTANT RULES:
1. You MUST use the provided tools to access financial data. NEVER invent or guess financial numbers.
2. If data is not available, clearly say so. Do NOT fabricate transactions or statistics.
3. You are a financial management assistant, NOT a financial investment advisor. Avoid making high-risk investment recommendations.
4. When a user tells you about spending or income, extract the amount, type, category, and description.
5. If important information is missing or ambiguous, ASK the user to clarify before proceeding.
6. Use the currency "yuan" (¥) for amounts.
7. Be concise, friendly, and helpful.
8. When showing financial data, format numbers clearly.
9. For budgeting advice, base recommendations ONLY on the user's actual data.
10. Available categories: Food, Transportation, Shopping, Entertainment, Bills, Healthcare, Education, Salary, Freelance, Investment, Gift, Housing, Other.

When a user says something like "I spent 50 on lunch", you should call add_transaction with:
- amount: 50
- transaction_type: expense
- category: Food
- description: lunch

When a user asks about their finances, use the appropriate tool to fetch real data first."""


def process_chat_message(
    db: Session,
    user_id: int,
    message: str,
) -> dict:
    """
    Process a user chat message using Gemini with function calling.

    Flow:
    1. Send user message + tool definitions to Gemini
    2. If Gemini wants to call a tool, execute it with real DB data
    3. Send tool results back to Gemini
    4. Gemini generates final natural-language response

    Returns dict with 'reply', 'action_taken', and 'data'.
    """
    current_settings = get_settings()
    if not current_settings.GEMINI_API_KEY:
        return {
            "reply": (
                "⚠️ The AI service is not configured. "
                "Please set GEMINI_API_KEY in the .env file to enable the AI assistant."
            ),
            "action_taken": None,
            "data": None,
        }

    try:
        genai.configure(api_key=current_settings.GEMINI_API_KEY)

        # Build the tools for Gemini
        tools = genai.types.Tool(
            function_declarations=[
                genai.types.FunctionDeclaration(
                    name=tool["name"],
                    description=tool["description"],
                    parameters=tool["parameters"],
                )
                for tool in TOOL_DEFINITIONS
            ]
        )

        model = genai.GenerativeModel(
            model_name=current_settings.GEMINI_MODEL,
            tools=[tools],
            system_instruction=SYSTEM_PROMPT,
        )

        chat = model.start_chat()

        # Send user message
        response = chat.send_message(message)

        action_taken = None
        tool_data = None
        max_tool_rounds = 5
        round_count = 0

        # Handle tool calls iteratively
        while round_count < max_tool_rounds:
            round_count += 1

            # Check if there are function calls
            function_calls = []
            for part in response.parts:
                if hasattr(part, "function_call") and part.function_call:
                    function_calls.append(part.function_call)

            if not function_calls:
                break

            # Execute each function call
            tool_responses = []
            for fc in function_calls:
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

                result = _execute_tool(tool_name, tool_args, db, user_id)

                if tool_name == "add_transaction" and result.get("success"):
                    action_taken = "transaction_added"
                    tool_data = result.get("transaction")

                tool_responses.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=tool_name,
                            response={"result": result},
                        )
                    )
                )

            # Send tool results back
            response = chat.send_message(tool_responses)

        # Extract final text response
        reply_text = ""
        for part in response.parts:
            if hasattr(part, "text") and part.text:
                reply_text += part.text

        if not reply_text:
            reply_text = "I processed your request but couldn't generate a response. Please try again."

        return {
            "reply": reply_text,
            "action_taken": action_taken,
            "data": tool_data,
        }

    except Exception as e:
        logger.error(f"AI service error: {e}", exc_info=True)
        error_msg = str(e)
        if "quota" in error_msg.lower() or "rate" in error_msg.lower():
            return {
                "reply": "⚠️ The AI service is currently rate-limited. Please try again in a moment.",
                "action_taken": None,
                "data": None,
            }
        return {
            "reply": (
                "⚠️ I encountered an error processing your message. "
                "Please try again or rephrase your question."
            ),
            "action_taken": None,
            "data": None,
        }
