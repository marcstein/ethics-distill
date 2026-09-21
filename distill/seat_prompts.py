"""v3 seat prompt: use the framework rather than explain it; commit to the facts first; rate the action exactly as stated."""
import seat_prompts_v1 as P
SEATS = P.SEATS
SEAT_COMMON = """
You are one member of a panel of seven moral philosophers analyzing a concrete case. Analyze it strictly from your own framework; do not try to be balanced across schools or to anticipate the other panelists.

Rules:
- Use the framework, do not explain it. Do not summarize the philosopher's system or define his terms at length. Start from where the agent in the case actually stands and reason to a conclusion, bringing in each concept only at the point where it does work on these facts.
- Facts first. Before reasoning, record what the case establishes and what it leaves open. Your reasoning may rely only on established facts and on general background knowledge that no one would dispute. Do not add case-specific facts, causes, histories, motives or consequences that the case does not state. Where your argument needs a fact the case leaves open, argue conditionally: say what follows if it holds and what follows if it does not.
- Where you extend the philosopher's approach to something he never addressed (modern institutions, technologies, regulation), say in one sentence that this is a contemporary application rather than his own prescription.
- Plain contemporary English, third person about the case, no theatrical role-play, no archaic diction. Do not fabricate quotations and do not cite section or page numbers.
- Rate the action exactly as it is stated in the question, not a modified version of it. +2 = the action as stated clearly should be done; +1 = it probably should be done or is permissible; 0 = the framework cannot decide; -1 = it probably should not be done; -2 = it clearly should not be done. If your answer to the question is "no", the position must be negative, even when a modified version of the action would be acceptable; record that separately.
- Reason first, then decide: your position must follow from the reasoning you give.
Record your analysis with the record_analysis tool."""

SEAT_TOOL = {
    "name": "record_analysis",
    "description": "Record this philosopher's analysis of the case.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action_rated": {"type": "string", "description": "One sentence restating the exact action the question asks about, which is what your position will rate."},
            "established_facts": {"type": "string", "description": "3-6 facts the case actually states that matter within this framework, one per line, each starting with '- '. Plain text, no markup."},
            "open_facts": {"type": "string", "description": "0-4 things the case does not settle that would matter to this framework's answer, one per line, each starting with '- '. Write 'none' if there are none. Plain text, no markup."},
            "reasoning": {"type": "string", "description": "The argument, 250-400 words of plain prose, relying only on established facts, arguing conditionally where an open fact matters."},
            "strongest_objection": {"type": "string", "description": "The strongest consideration against your conclusion and your reply. 2-4 sentences."},
            "position": {"type": "integer", "enum": [-2, -1, 0, 1, 2]},
            "verdict": {"type": "string", "description": "One or two sentences answering the question as asked."},
            "modified_version_acceptable": {"type": "string", "enum": ["yes", "no", "not_applicable"], "description": "If your answer to the action as stated is negative: would a modified version of the action be acceptable?"},
            "modification": {"type": "string", "description": "If yes: the modification, in one sentence. Otherwise an empty string."},
            "would_change_if": {"type": "string", "description": "One sentence: the change of fact that would change your position."}
        },
        "required": ["action_rated", "established_facts", "open_facts", "reasoning", "strongest_objection", "position", "verdict", "modified_version_acceptable", "modification", "would_change_if"]
    }
}
def seat_user(s): return P.seat_user(s)

NEW_PAIR = [
 {"id": "P11A", "pair": "P11", "pair_type": "relevant", "domain": "credit", "text": "A consumer lender finds that adding retail purchase-pattern data (for example, how often an applicant buys discount-brand goods) measurably improves its default predictions. The feature is strongly correlated with neighborhood and, through that, with race, so approval rates for minority applicants would fall even though race is never used directly. Internal testing shows that once the model controls for neighborhood, the feature adds no predictive power at all: everything it predicts, it predicts by standing in for where the applicant lives. Using the feature is legal in the lender's jurisdiction.", "question": "Should the lender deploy the feature?"},
 {"id": "P11B", "pair": "P11", "pair_type": "relevant", "domain": "credit", "text": "A consumer lender finds that adding retail purchase-pattern data (for example, how often an applicant buys discount-brand goods) measurably improves its default predictions. The feature is strongly correlated with neighborhood and, through that, with race, so approval rates for minority applicants would fall even though race is never used directly. Internal testing shows that the feature predicts default just as well among applicants within the same neighborhood and within each racial group: it carries information about the individual applicant's finances that is not explained by where the applicant lives. Using the feature is legal in the lender's jurisdiction.", "question": "Should the lender deploy the feature?"}]
