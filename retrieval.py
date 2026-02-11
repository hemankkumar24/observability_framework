def retrieve_context(query):
    docs = {
        "os": "Operating systems manage hardware and processes.",
        "transformer": "Transformers use self-attention for sequence modeling."
    }

    results = []
    for k in docs:
        if k in query.lower():
            results.append(docs[k])

    return results
