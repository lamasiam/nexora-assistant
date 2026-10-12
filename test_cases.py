"""
test_cases.py
A small hand-written set of question/answer pairs used to measure the
assistant's accuracy. Each case has a "type":

- "answerable": the answer IS in our documents. We check that
  (a) the correct document was retrieved, and
  (b) the generated answer contains the expected key fact(s).

- "unanswerable": the answer is deliberately NOT in our documents.
  We check that the assistant admits it doesn't know, instead of
  making something up (hallucinating).
"""

TEST_CASES = [
    {
        "type": "answerable",
        "question": "How many days of annual leave do I get?",
        "role": "intern/trainee",
        "expected_source": "hr_leave_policy.md",
        "expected_keywords": ["1 day", "month"],
    },
    {
        "type": "answerable",
        "question": "How many days of annual leave do I get?",
        "role": "full-time employee",
        "expected_source": "hr_leave_policy.md",
        "expected_keywords": ["16"],
    },
    {
        "type": "answerable",
        "question": "How do I reset my password?",
        "role": "intern/trainee",
        "expected_source": "it_helpdesk_faq.md",
        "expected_keywords": ["reset"],
    },
    {
        "type": "answerable",
        "question": "What should I do if I lose my access card?",
        "role": "intern/trainee",
        "expected_source": "it_helpdesk_faq.md",
        "expected_keywords": ["Security"],
    },
    {
        "type": "answerable",
        "question": "What are the standard office working hours?",
        "role": "intern/trainee",
        "expected_source": "onboarding_guide.md",
        "expected_keywords": ["8:30"],
    },
    {
        "type": "answerable",
        "question": "Who do I contact for IT setup issues?",
        "role": "intern/trainee",
        "expected_source": ["onboarding_guide.md", "it_helpdesk_faq.md"],
        "expected_keywords": ["2100"],
    },
    {
        "type": "answerable",
        "question": "How much can I claim for a client meeting meal?",
        "role": "full-time employee",
        "expected_source": "expense_claim_policy.md",
        "expected_keywords": ["RM50"],
    },
    {
        "type": "answerable",
        "question": "How many days do I have to submit an expense claim?",
        "role": "full-time employee",
        "expected_source": "expense_claim_policy.md",
        "expected_keywords": ["30"],
    },
    {
        "type": "answerable",
        "question": "Can I work from home on Fridays?",
        "role": "intern/trainee",
        "expected_source": "wfh_policy.md",
        "expected_keywords": ["Friday"],
    },
    {
        "type": "answerable",
        "question": "How many extra ad-hoc WFH days can I request per month?",
        "role": "full-time employee",
        "expected_source": "wfh_policy.md",
        "expected_keywords": ["2"],
    },
    {
        "type": "unanswerable",
        "question": "What is the office WiFi password?",
        "role": "intern/trainee",
    },
    {
        "type": "unanswerable",
        "question": "Who is the CEO of Nexora R&D?",
        "role": "full-time employee",
    },
]

# Phrases that count as "the assistant admitted it doesn't know."
NO_ANSWER_PHRASES = [
    "don't have", "do not have", "doesn't contain", "does not contain",
    "no information", "not sure", "don't know", "do not know",
    "not mentioned", "not provided", "cannot find", "can't find",
]
