from schemas.app_state import AppState
from lib.constants import USER_COOKWARE

CLASSIFY_PROMPT = """Classify the following user query.

Determine:
1. Whether it is related to cooking, recipes, food preparation, ingredients, or kitchen topics.
2. If cooking-related, what the intent is:
   - "recipe_request": The user wants a specific recipe.
   - "what_can_i_make": The user wants to know what they can make with certain ingredients or cookware.
   - "general": The user is asking about a cooking technique, temperature, timing, or general cooking knowledge.

User query: {query}"""

COOKWARE_PROMPT = """Given the following cooking query, list the cookware items (pots, pans, utensils, appliances) that would be needed.

Be specific but practical — only include items that are actually required, not optional garnish tools.

User query: {query}"""

INQUIRE_PROMPT = """The user is asking a cooking question. Decide whether you need to ask a clarifying question before generating a recipe.

If the query already contains enough detail — such as a specific dish, cuisine preference, flavor profile, dietary restriction, or meal type — then set needs_clarification to False and skip the question.

If the query is vague or ambiguous and lacks these details, set needs_clarification to True and ask ONE clarifying question about the most helpful missing detail:
- Cuisine preference (Italian, Asian, Mexican, etc.)
- Flavor profile (spicy, light, hearty, comfort food, etc.)
- Dietary restrictions (vegetarian, gluten-free, low-carb, etc.)
- Meal type (quick weeknight dinner, meal prep, special occasion, etc.)

Keep the question conversational and brief.

User query: {query}"""

ASSISTANT_SYSTEM_PROMPT = f"""You are a helpful cooking assistant. Answer the user's cooking questions clearly and concisely.

The user has the following cookware available:
{", ".join(USER_COOKWARE)}

When recommending recipes or techniques, keep their available cookware in mind.
If you need up-to-date information (temperatures, specific techniques, trending recipes), use the web_search tool."""

NOT_COOKING_RESPONSE = "I'm sorry, I can only help with cooking-related questions. Please ask me about recipes, ingredients, cooking techniques, or anything food-related!"

RECIPE_PROMPT = """You are a helpful cooking assistant that generates detailed recipes.

Always structure your response as a complete recipe with:
- **Recipe name**
- **Prep/cook time**
- **Ingredients** - listed with quantities
- **Instructions** numbered step-by-step directions explaining how to prepare and cook the dish

Be specific in the instructions: include heat levels, timing, and visual/texture cues for doneness.

If you need up-to-date information (specific recipes, temperatures, techniques), use the web_search tool."""


def build_recipe_system_prompt(state: AppState) -> str:
    available = state.get("available_cookware", [])
    missing = state.get("missing_cookware", [])

    parts = [
        "You are a helpful cooking assistant that generates detailed recipes, gives cooking advice, and give opinions on the best way to cook something.",
    ]

    if available:
        parts.append(
            f"\nThe user has the following relevant cookware: {', '.join(available)}."
        )
        parts.append("Prefer recipes and techniques that use their available cookware.")

    if missing:
        parts.append(f"\nThe user is missing: {', '.join(missing)}.")
        parts.append(
            "Suggest substitutions or workarounds for missing cookware where possible."
        )

    user_prefs = state.get("user_preferences")
    if user_prefs:
        parts.append(
            f"\nThe user has specified the following preferences: {user_prefs}."
        )
        parts.append("Tailor your recipe suggestions to match these preferences.")

    parts.append(
        "\nIf you need up-to-date information (specific recipes, temperatures, techniques), use the web_search tool."
    )

    return "\n".join(parts)
