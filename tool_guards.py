# example function to base off of:
MAX_RETRIEVAL_CALLS = 3
retrieval_calls = 0

def retrieval_tool_guarded(query):
    global retrieval_calls
    if retrieval_calls >= MAX_RETRIEVAL_CALLS:
        raise RuntimeError("Retrieval call limit exceeded")
    retrieval_calls += 1
    return retrieval_tool(query)

# prompt adjustments:

#You have a maximum retrieval budget of 3 calls.
#Use the fewest retrieval calls necessary.
#Prefer broader queries over many narrow ones.

#Before calling retrieval_tool, briefly plan:
#- What information is required?
#- How many retrieval calls are needed?
#- What queries will be used?
#Then execute the plan.

#Stop retrieving once you have:
#- A formal definition
#- At least one property
#- At least one example

#After each retrieval, assess:
#"Can I generate at least 3 high-quality Anki questions?"
#If yes, stop retrieving.

#You may perform:
#- One primary retrieval (required)
#- One secondary retrieval only if critical information is missing

#Good mix:
#- You have a maximum of 3 retrieval calls.
#- Prefer broad queries.
#- Stop retrieving once definition + property + example are obtained.