"""
evaluate.py
Runs every case in test_cases.py through the REAL pipeline (same
rag_core.py used by the web app — nothing faked or mocked), then
reports:
  - Retrieval accuracy: % of answerable questions where the correct
    document was retrieved
  - Answer accuracy: % of answerable questions where the generated
    answer contained the expected key fact(s)
  - Hallucination avoidance: % of unanswerable questions where the
    assistant correctly admitted it didn't know
  - Average response time

Results are also saved to results.csv so you can screenshot/paste
them straight into your report or poster.
"""

import csv
import time

import rag_core
from test_cases import TEST_CASES, NO_ANSWER_PHRASES


def check_retrieval(sources, expected_source):
    # expected_source can be a single filename, or a list of acceptable
    # filenames when more than one document legitimately answers the question.
    if isinstance(expected_source, list):
        return any(exp in sources for exp in expected_source)
    return expected_source in sources


def check_keywords(answer, expected_keywords):
    answer_lower = answer.lower()
    return all(kw.lower() in answer_lower for kw in expected_keywords)


def check_no_answer(answer):
    answer_lower = answer.lower()
    return any(phrase in answer_lower for phrase in NO_ANSWER_PHRASES)


def main():
    results = []
    retrieval_correct = retrieval_total = 0
    keyword_correct = keyword_total = 0
    refusal_correct = refusal_total = 0
    response_times = []

    for i, case in enumerate(TEST_CASES, 1):
        print(f"[{i}/{len(TEST_CASES)}] {case['question']}")

        start = time.time()
        try:
            answer, sources = rag_core.answer_question(case["question"], case["role"])
        except Exception as e:
            print(f"    ERROR: {e}")
            continue
        elapsed = time.time() - start
        response_times.append(elapsed)

        row = {
            "question": case["question"],
            "role": case["role"],
            "type": case["type"],
            "answer": answer,
            "sources": ", ".join(sources),
            "time_sec": round(elapsed, 2),
        }

        if case["type"] == "answerable":
            retrieval_total += 1
            keyword_total += 1
            r_ok = check_retrieval(sources, case["expected_source"])
            k_ok = check_keywords(answer, case["expected_keywords"])
            retrieval_correct += r_ok
            keyword_correct += k_ok
            row["retrieval_correct"] = r_ok
            row["keyword_correct"] = k_ok
            print(f"    Retrieval: {'PASS' if r_ok else 'FAIL'} | Answer keywords: {'PASS' if k_ok else 'FAIL'}")
        else:  # unanswerable
            refusal_total += 1
            no_ans_ok = check_no_answer(answer)
            refusal_correct += no_ans_ok
            row["refusal_correct"] = no_ans_ok
            print(f"    Correctly admitted not knowing: {'PASS' if no_ans_ok else 'FAIL'}")

        results.append(row)

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    if retrieval_total:
        print(f"Retrieval accuracy:      {retrieval_correct}/{retrieval_total} "
              f"({100 * retrieval_correct / retrieval_total:.1f}%)")
        print(f"Answer keyword accuracy: {keyword_correct}/{keyword_total} "
              f"({100 * keyword_correct / keyword_total:.1f}%)")
    if refusal_total:
        print(f"Hallucination avoidance: {refusal_correct}/{refusal_total} "
              f"({100 * refusal_correct / refusal_total:.1f}%)")
    if response_times:
        print(f"Average response time:   {sum(response_times) / len(response_times):.2f} sec")

    with open("results.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["question", "role", "type", "answer", "sources", "time_sec",
                      "retrieval_correct", "keyword_correct", "refusal_correct"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print("\nFull results saved to results.csv")


if __name__ == "__main__":
    main()
