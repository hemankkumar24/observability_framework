from langgraph.graph import StateGraph, END
from retrieval import retrieve_context
from evaluation import evaluate_response
from observability import trace_node
import uuid
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


class State(dict):
    pass


def intent_node(state):
    text = state["user_input"].lower()
    if "explain" in text:
        state["intent"] = "explain"
    else:
        state["intent"] = "general"
    return state


def retrieval_node(state):
    state["docs"] = retrieve_context(state["user_input"])
    return state



def llm_node(state):
    context = "\n".join(state.get("docs", []))
    prompt = f"{context}\nUser: {state['user_input']}"

    response = model.generate_content(prompt)
    answer = response.text

    state["response"] = answer

    eval_output = evaluate_response(
        model,
        state["user_input"],
        answer,
        state.get("docs", [])
    )

    state["evaluation"] = eval_output

    return state


def route(state):
    if state["intent"] == "explain":
        return "retrieve"
    return "llm"


def build_graph():
    builder = StateGraph(State)

    builder.add_node("intent", intent_node)
    builder.add_node("retrieve", retrieval_node)
    builder.add_node("llm", llm_node)

    builder.set_entry_point("intent")

    builder.add_conditional_edges("intent", route)
    builder.add_edge("retrieve", "llm")
    builder.add_edge("llm", END)

    return builder.compile()


def run_graph(user_input):
    graph = build_graph()
    trace_id = str(uuid.uuid4())

    state = {
        "user_input": user_input,
        "intent": "",
        "docs": [],
        "response": "",
         "evaluation": ""
    }

    state = trace_node(trace_id, "intent", intent_node, state)

    if state["intent"] == "explain":
        state = trace_node(trace_id, "retrieve", retrieval_node, state)

    state = trace_node(trace_id, "llm", llm_node, state)

    return state, trace_id
