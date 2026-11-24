from app.nlp.skill_extraction.extractor import extract_candidate_skills, extract_required_skills, find_mentions


def names(text, taxonomy):
    return {m.canonical for m in find_mentions("EXPERIENCE\n" + text, taxonomy)}


def test_alias_normalization(taxonomy):
    assert taxonomy.normalize("JS") == "JavaScript"
    assert taxonomy.normalize("Postgres") == "PostgreSQL"
    assert taxonomy.normalize("NLP") == "Natural Language Processing"
    assert taxonomy.normalize("k8s") == "Kubernetes"
    assert taxonomy.normalize("unknown-skill-xyz") is None


def test_exact_matching_respects_word_boundaries(taxonomy):
    found = names("Built front-ends in JavaScript and services in C++.", taxonomy)
    assert "JavaScript" in found and "C++" in found
    assert "Java" not in found      # 'Java' inside 'JavaScript'
    assert "C" not in found         # 'C' inside 'C++'


def test_postgresql_does_not_imply_sql_keyword(taxonomy):
    found = names("Queried PostgreSQL tables.", taxonomy)
    assert "PostgreSQL" in found and "SQL" not in found


def test_case_sensitive_short_aliases(taxonomy):
    assert "Go" in names("Wrote microservices in Go.", taxonomy)
    assert "Go" not in names("Ready to go the extra mile.", taxonomy)
    assert "R" not in names("Worked in R&D on new products.", taxonomy)


def test_multiword_and_hyphen_variants(taxonomy):
    assert "Machine Learning" in names("Applied machine-learning to churn data.", taxonomy)
    assert "Natural Language Processing" in names("Built an NLP pipeline.", taxonomy)


def test_longest_alias_wins_without_double_counting(taxonomy):
    mentions = find_mentions("EXPERIENCE\nUsed Spring Boot daily.", taxonomy)
    assert [m.canonical for m in mentions] == ["Spring Boot"]


def test_urls_are_not_skills(taxonomy):
    found = names("Portfolio: https://github.com/someone/react-app", taxonomy)
    assert found == set()


def test_mention_types(taxonomy):
    text = "SKILLS\nPython, Docker\n\nPROJECTS\nTrained a model in PyTorch.\n\nSUMMARY\nInterested in machine learning."
    skills = extract_candidate_skills(text, taxonomy)
    assert skills["Python"].strength == "listed"
    assert skills["PyTorch"].strength == "demonstrated"
    assert skills["Machine Learning"].strength == "mentioned"


def test_evidence_is_real_resume_text(taxonomy):
    text = "PROJECTS\nBuilt a REST API with Flask."
    m = extract_candidate_skills(text, taxonomy)["Flask"].best_mention
    assert text[m.char_start:m.char_end] == "Flask"
    assert text[m.sentence_start:m.sentence_end] == m.sentence


def test_required_skill_importance(taxonomy):
    jd = "Requirements:\n- Python and SQL.\n\nNice to have:\n- Docker\n- Kubernetes is a plus."
    reqs, _ = extract_required_skills(jd, taxonomy)
    imp = {r.canonical: r.importance for r in reqs}
    assert imp["Python"] == "must_have" and imp["SQL"] == "must_have"
    assert imp["Docker"] == "nice_to_have" and imp["Kubernetes"] == "nice_to_have"
    weights = {r.canonical: r.weight for r in reqs}
    assert weights["Python"] == 2.0 and weights["Docker"] == 1.0


def test_user_overrides_and_weights(taxonomy):
    jd = "We need Python. Docker is a plus."
    reqs, warnings = extract_required_skills(jd, taxonomy, must_have_overrides=["docker", "Postgres"],
                                             nice_to_have_overrides=["NotARealSkill"], custom_weights={"Python": 5})
    by = {r.canonical: r for r in reqs}
    assert by["Docker"].importance == "must_have"
    assert by["PostgreSQL"].source == "user_added"
    assert by["Python"].weight == 5
    assert any("NotARealSkill" in w for w in warnings)


def test_equal_weights(taxonomy):
    reqs, _ = extract_required_skills("Python required. Docker is a plus.", taxonomy, equal_weights=True)
    assert {r.weight for r in reqs} == {1.0}
