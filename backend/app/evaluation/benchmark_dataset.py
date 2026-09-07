"""
benchmark_dataset.py
--------------------
Curated benchmark evaluation dataset for Nutri-RAG.

Contains diverse representative test cases across:
- Core biochemistry and nutrition textbook facts
- Multi-turn follow-up and clinical questions
- Direct conversational greeting & off-topic routing
- Missing context / fallback refusal adherence
- Adversarial false-premise questions
"""

from app.evaluation.schemas import EvaluationDataset, EvaluationSample


def get_benchmark_dataset() -> EvaluationDataset:
    """Return the canonical benchmark dataset for Nutri-RAG evaluation."""
    samples = [
        # --- Test Case 1: Vitamin C in Collagen Synthesis (High Grounding) ---
        EvaluationSample(
            sample_id="NUTRITION_001_VITAMIN_C_COLLAGEN",
            query="What is the role of Vitamin C in collagen synthesis?",
            context_chunks=[
                {
                    "doc_id": "human_nutrition_textbook_ch10.pdf",
                    "chunk_index": 42,
                    "similarity": 0.934,
                    "content": (
                        "Ascorbic acid (Vitamin C) acts as an essential electron donor and cofactor for "
                        "prolyl hydroxylase and lysyl hydroxylase. These enzymes post-translationally hydroxylate "
                        "proline and lysine residues within procollagen peptide chains. This hydroxylation is critical "
                        "for the formation of stable collagen triple-helix structures and intermolecular cross-linking."
                    ),
                },
                {
                    "doc_id": "human_nutrition_textbook_ch10.pdf",
                    "chunk_index": 43,
                    "similarity": 0.887,
                    "content": (
                        "A deficiency in ascorbic acid impairs collagen synthesis, leading to clinical scurvy. "
                        "Symptoms include capillary fragility, petechial hemorrhages, impaired wound healing, "
                        "and gingival bleeding due to defective connective tissue maintenance."
                    ),
                },
            ],
            response=(
                "**Vitamin C (ascorbic acid)** plays a fundamental biochemical role in **collagen synthesis**:\n\n"
                "- **Enzymatic Cofactor**: It acts as an essential electron donor and cofactor for **prolyl hydroxylase** "
                "and **lysyl hydroxylase** [1].\n"
                "- **Triple-Helix Stabilization**: These enzymes post-translationally hydroxylate proline and lysine residues, "
                "which is necessary for the proper folding and cross-linking of the collagen triple helix [1].\n"
                "- **Clinical Relevance**: Inadequate Vitamin C intake impairs connective tissue synthesis, resulting in **scurvy** "
                "characterized by capillary fragility and poor wound healing [2]."
            ),
            ground_truth=(
                "Vitamin C is a cofactor for prolyl and lysyl hydroxylases, which hydroxylate collagen fibers "
                "to stabilize the triple-helix structure. Deficiency leads to scurvy."
            ),
            intent="RETRIEVAL_QUERY",
            metadata={"category": "micronutrients", "difficulty": "medium"},
        ),

        # --- Test Case 2: Vitamin D and Calcium Homeostasis ---
        EvaluationSample(
            sample_id="NUTRITION_002_VITAMIN_D_CALCIUM",
            query="How does active Vitamin D regulate calcium absorption in the intestine?",
            context_chunks=[
                {
                    "doc_id": "human_nutrition_textbook_ch11.pdf",
                    "chunk_index": 18,
                    "similarity": 0.912,
                    "content": (
                        "Calcitriol (1,25-dihydroxyvitamin D3), the active hormonal form of Vitamin D, binds to the "
                        "nuclear Vitamin D Receptor (VDR) in enterocytes. This upregulates the transcription of calbindin-D9k, "
                        "the apical calcium channel TRPV6, and the basolateral plasma membrane Ca2+-ATPase (PMCA1b), "
                        "significantly increasing transcellular calcium absorption in the duodenum."
                    ),
                }
            ],
            response=(
                "**Active Vitamin D (calcitriol / 1,25-dihydroxyvitamin D3)** regulates intestinal calcium absorption through genomic pathways [1]:\n\n"
                "- **Receptor Activation**: Calcitriol binds to the intracellular **Vitamin D Receptor (VDR)** in intestinal enterocytes [1].\n"
                "- **Transport Protein Upregulation**: This transcriptional activation stimulates the synthesis of **calbindin-D9k**, "
                "the apical calcium channel **TRPV6**, and the basolateral calcium pump **PMCA1b** [1].\n"
                "- **Net Effect**: Enhances active transcellular calcium transport across the duodenal mucosa into circulation [1]."
            ),
            ground_truth=(
                "Calcitriol binds to VDR in enterocytes, upregulating calbindin-D9k, TRPV6, and PMCA1b to increase calcium absorption."
            ),
            intent="RETRIEVAL_QUERY",
            metadata={"category": "minerals_vitamins", "difficulty": "advanced"},
        ),

        # --- Test Case 3: Dietary Iron Absorption Inhibitors ---
        EvaluationSample(
            sample_id="NUTRITION_003_IRON_INHIBITORS",
            query="What dietary compounds inhibit non-heme iron absorption?",
            context_chunks=[
                {
                    "doc_id": "human_nutrition_textbook_ch12.pdf",
                    "chunk_index": 77,
                    "similarity": 0.895,
                    "content": (
                        "Non-heme iron absorption is inhibited by several dietary factors: (1) Phytates found in whole grains "
                        "and legumes, which bind iron into insoluble complexes; (2) Polyphenols and tannins in tea and coffee; "
                        "and (3) Excess calcium, which competitively interferes with both non-heme and heme iron transport."
                    ),
                }
            ],
            response=(
                "Dietary compounds that inhibit **non-heme iron** absorption include [1]:\n\n"
                "- **Phytates**: Found in whole grains and legumes, which bind iron into insoluble complexes [1].\n"
                "- **Polyphenols & Tannins**: Present in tea and coffee, which inhibit non-heme iron absorption [1].\n"
                "- **Calcium**: Excess calcium competitively interferes with iron transport [1]."
            ),
            ground_truth="Phytates in grains/legumes, polyphenols in tea/coffee, and high doses of calcium inhibit non-heme iron absorption.",
            intent="RETRIEVAL_QUERY",
            metadata={"category": "minerals", "difficulty": "easy"},
        ),

        # --- Test Case 4: Conversational Greeting (Direct Chat, No Retrieval) ---
        EvaluationSample(
            sample_id="CONVERSATION_001_GREETING",
            query="Hello! Can you introduce yourself?",
            context_chunks=[],
            response=(
                "Hello! I am **Nutri-RAG**, your AI Research Assistant specialised in human nutrition science. "
                "I can help you explore nutritional biochemistry, micronutrient metabolism, dietary guidelines, and clinical nutrition research grounded in peer-reviewed textbooks. How can I assist you today?"
            ),
            ground_truth="A polite greeting introducing Nutri-RAG as a human nutrition assistant.",
            intent="DIRECT_CHAT",
            metadata={"category": "dialogue", "difficulty": "basic"},
        ),

        # --- Test Case 5: Missing / Out-of-Domain Context (Fallback Adherence) ---
        EvaluationSample(
            sample_id="FALLBACK_001_UNGROUNDED_QUERY",
            query="What is the latest quantum computing algorithm for Shor's factorization?",
            context_chunks=[],
            response=(
                "Based on the provided research documents, I cannot find enough information in the database to answer this specific query reliably. "
                "Please feel free to ask questions related to human nutrition, biochemistry, or dietary health."
            ),
            ground_truth="Polite refusal indicating lack of relevant nutrition textbook sources.",
            intent="RETRIEVAL_QUERY",
            metadata={"category": "out_of_domain", "difficulty": "easy"},
        ),
    ]

    return EvaluationDataset(
        name="Nutri-RAG Gold Standard Benchmark",
        description="Curated benchmark test suite testing grounding, precision, relevance, and safety.",
        samples=samples,
    )
