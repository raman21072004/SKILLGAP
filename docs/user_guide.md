# User guide

1. **Create an account** (name, email, password with a letter and a number).
2. **New analysis:** upload a PDF/DOCX/TXT resume (or paste it), review the extracted text, paste the job
   description, optionally add a job title and extra must-have / nice-to-have skills, choose a method:
   - *Deep semantic (recommended)* – recognises paraphrases; the first run loads the model (≤ 1 minute).
   - *TF-IDF* – fast, no model needed. *Keyword only* – strict name matching.
3. **Results**
   - *Requirement coverage* – weighted share of requirements your resume shows.
   - *Evidence bar* – one block per requirement, width = weight, colour = verdict:
     green **Shown**, amber **Verify** (similar wording, confirm it yourself), violet **Related** (you have a
     transferable skill), red **Not shown**. Faded blocks are nice-to-haves. Click a block to jump to its evidence.
   - *Requirements list* – open any item for the explanation, the exact resume sentence, the method and
     similarity scores, and the next step. Use **Correct this result** if the system is wrong; your change is
     saved separately and the score and roadmap update.
   - *Your resume* – every evidence sentence is highlighted; the selected one turns amber.
   - *Method comparison* – keyword vs TF-IDF vs dense embeddings on your documents.
   - **Export JSON** / **Delete**.
4. **Skill explorer** – searchable, filterable, sortable table of all requirements.
5. **Roadmap** – ordered tasks with priority, prerequisites, project, effort estimate, resources and a
   checklist. Set status Not started → Learning → Practiced → Completed. Progress is self-reported; update
   your resume and run a new analysis to verify new skills.
6. **History** – all analyses with date, role, score and method; delete any of them.
7. **NLP Lab** – nine modules demonstrating the syllabus on your own text, each with an explanation.
8. **Settings** – profile, default method and weights, retention period, export all data, delete account.

A yellow banner saying the TF-IDF fallback was used means the deep-learning model is not installed; see the
README "Model installation".
