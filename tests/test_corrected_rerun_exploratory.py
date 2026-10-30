from src.evaluation.analyze_corrected_rerun_exploratory import answer_in, outcome_class


def test_outcome_class_uses_fixed_thresholds():
    assert outcome_class("I don't know.", 1) == "abstained"
    assert outcome_class("PSLV-C30", 5) == "correct"
    assert outcome_class("PSLV-C30", 4) == "correct"
    assert outcome_class("PSLV", 3) == "partial"
    assert outcome_class("GSLV", 2) == "wrong"


def test_answer_in_matches_any_acceptable_answer_normalised():
    question = {"reference_answer": "Moon", "acceptable_answers": ["Physical Research  Laboratory", "PRL"]}
    assert answer_in("developed by the physical research laboratory (PRL)", question)
    assert not answer_in("developed by ISRO", question)
    assert answer_in("the moon", {"reference_answer": "Moon"})
