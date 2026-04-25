from fairness.blind_screening import (
    redact_identifiers_in_text,
    blind_screen_resume_profile,
    blind_screen_background_for_scoring,
)

def test_redact_identifiers_in_text():
    text = "Contact me at alice@example.com or call 123-456-7890. I am Jane Doe (female)."
    redacted = redact_identifiers_in_text(text)
    assert "alice@example.com" not in redacted
    assert "123-456-7890" not in redacted
    assert "[identifier removed]" in redacted
    assert "[blinded]" in redacted

def test_blind_screen_resume_profile():
    profile = {
        "candidate_name": "John Smith",
        "headline": "Software Engineer at Google. Contact: john.smith@gmail.com",
        "summary": "Experienced male developer.",
        "education": [{"school": "MIT", "summary": "Graduated with John Smith."}],
        "experience": [{"company": "Meta", "highlights": ["Worked with Mr. Smith on React."]}],
        "skills": [{"name": "Python", "source_evidence": "Used at Meta by John Smith."}]
    }
    blinded = blind_screen_resume_profile(profile)
    assert blinded["candidate_name"] is None
    assert "John Smith" not in blinded["headline"]
    assert "john.smith@gmail.com" not in blinded["headline"]
    # "male" matches _RE_GENDER_TOKEN (re.I)
    assert "[blinded]" in blinded["summary"]
    assert "[identifier removed]" in blinded["experience"][0]["highlights"][0]
    assert blinded["_blind_screening"]["applied"] is True

def test_blind_screen_background_for_scoring():
    bg = {
        "github": {
            "login": "jsmith",
            "profile_url": "https://github.com/jsmith",
            "bio": "I am John Smith from London."
        },
        "academic": {
            "display_name": "John Smith",
            "top_papers": [{"title": "AI paper", "external_url": "http://arxiv.org/abs/123"}]
        }
    }
    blinded = blind_screen_background_for_scoring(bg)
    assert blinded["github"]["login"] is None
    assert blinded["github"]["profile_url"] is None
    assert "John Smith" not in blinded["github"]["bio"]
    assert blinded["academic"]["display_name"] is None
    assert blinded["academic"]["top_papers"][0]["external_url"] is None
    assert blinded["_blind_screening"]["applied"] is True
