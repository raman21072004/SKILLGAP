import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { EvidenceBar } from "@/charts/EvidenceBar";
import { filterRequirements, SkillTable } from "@/features/analysis/SkillTable";
import { LoginPage } from "@/pages/AuthPages";
import type { Requirement } from "@/types/api";

function req(canonical: string, verdict: Requirement["effective_classification"], importance: Requirement["importance"] = "must_have"): Requirement {
  return {
    match_id: Math.floor(Math.random() * 1e6), canonical, category: "Programming Languages", importance, weight: importance === "must_have" ? 2 : 1,
    requirement_text: null, requirement_source: "extracted", exact_match: verdict === "direct_match", classification: verdict,
    user_classification: null, effective_classification: verdict, classification_label: verdict, similarity: null,
    tfidf_similarity: 0.1, semantic_similarity: null, similarity_backend: null, related_skills_found: [], method: null,
    explanation: "", next_action: `Learn ${canonical}`, uncertainty: null,
    evidence: verdict === "direct_match" ? { text: `Built things in ${canonical}`, section: "projects", start: 0, end: 10, match_start: null, match_end: null, matched_text: canonical, kind: "exact", strength: "demonstrated" } : null,
  };
}

const REQS = [req("Python", "direct_match"), req("Java", "related"), req("Docker", "missing", "nice_to_have")];

describe("SkillTable", () => {
  it("filters by text, verdict and importance", () => {
    expect(filterRequirements(REQS, "pyth", "all", "all").map((r) => r.canonical)).toEqual(["Python"]);
    expect(filterRequirements(REQS, "", "missing", "all").map((r) => r.canonical)).toEqual(["Docker"]);
    expect(filterRequirements(REQS, "", "all", "must_have")).toHaveLength(2);
    expect(filterRequirements(REQS, "built things", "all", "all")).toHaveLength(1); // searches evidence
  });

  it("updates the visible rows when the user searches and filters", async () => {
    const user = userEvent.setup();
    render(<SkillTable requirements={REQS} />);
    expect(screen.getByText("3 of 3 requirements")).toBeInTheDocument();
    await user.type(screen.getByLabelText("Search skills"), "dock");
    expect(screen.getByText("1 of 3 requirements")).toBeInTheDocument();
    await user.clear(screen.getByLabelText("Search skills"));
    await user.selectOptions(screen.getByLabelText("Filter by verdict"), "direct_match");
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.queryByText("Docker")).not.toBeInTheDocument();
  });
});

describe("EvidenceBar", () => {
  it("renders one accessible segment per requirement and reports clicks", async () => {
    const onSelect = vi.fn();
    render(<EvidenceBar animate={false} onSelect={onSelect} items={REQS.map((r) => ({ skill: r.canonical, weight: r.weight, verdict: r.effective_classification }))} />);
    const segments = screen.getAllByRole("listitem").filter((el) => el.tagName === "BUTTON");
    expect(segments).toHaveLength(3);
    await userEvent.click(screen.getByLabelText(/Docker/));
    expect(onSelect).toHaveBeenCalledWith("Docker");
  });
});

describe("LoginPage", () => {
  it("shows validation errors without calling the API", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter><LoginPage /></MemoryRouter>);
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByText("Enter a valid email address.")).toBeInTheDocument();
    expect(screen.getByText("Enter your password.")).toBeInTheDocument();
  });
});
