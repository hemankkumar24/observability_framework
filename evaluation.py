import json
import re

def evaluate_response(model, user_input, response, docs):

    context_used = "\n".join(docs) if docs else "No external context used."

    prompt = f"""
        Evaluate strictly between 0 and 1.

        User question:
        {user_input}

        Retrieved context:
        {context_used}

        Assistant response:
        {response}

        Return ONLY JSON:

        {{
        "quality": 0.0,
        "confidence": 0.0,
        "reason": "text"
        }}
    """

    raw = model.generate_content(prompt).text.strip()

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return '{"quality":0.0,"confidence":0.0,"reason":"Parsing failed."}'

    data = json.loads(match.group(0))

    quality = float(data.get("quality", 0.0))
    confidence = float(data.get("confidence", 0.0))
    reason = data.get("reason", "")

    if not docs:
        quality = min(quality, 0.8)
        confidence = min(confidence, 0.8)
        reason += " Reduced due to lack of grounding."

    if len(response) < 60:
        quality = min(quality, 0.75)
        confidence = min(confidence, 0.75)
        reason += " Reduced due to short response."

    quality = round(quality, 3)
    confidence = round(confidence, 3)

    return json.dumps({
        "quality": quality,
        "confidence": confidence,
        "reason": reason
    })
