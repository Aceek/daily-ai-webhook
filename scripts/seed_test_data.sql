-- Seed test data for weekly digest testing
-- Week: December 15-21, 2025 (previous week from Dec 24, 2025)

-- First, clean up any existing test data for this period
DELETE FROM articles WHERE mission_id = 'ai-news' AND created_at >= '2025-12-15' AND created_at <= '2025-12-22';

-- Category IDs: headlines=2, research=3, industry=4, watching=5

-- Monday December 15, 2025
INSERT INTO articles (mission_id, category_id, title, url, source, description, pub_date, created_at) VALUES
('ai-news', 2, 'OpenAI Announces GPT-5 Preview Program for Enterprise Customers', 'https://openai.com/blog/gpt5-preview', 'OpenAI Blog', 'OpenAI has unveiled a preview program for GPT-5, offering early access to enterprise customers. The new model reportedly features improved reasoning capabilities and a 500K context window.', '2025-12-15 09:00:00', '2025-12-15 09:00:00'),
('ai-news', 3, 'New Paper: Efficient Attention Mechanisms for Long Context Windows', 'https://arxiv.org/abs/2512.12345', 'arXiv', 'Researchers propose a novel attention mechanism that reduces computational complexity from O(n²) to O(n log n) while maintaining performance on long-context tasks.', '2025-12-15 11:00:00', '2025-12-15 11:00:00'),
('ai-news', 4, 'Anthropic Secures $2B in New Funding Round Led by Google', 'https://anthropic.com/news/series-e', 'Anthropic', 'Anthropic closes its largest funding round to date, bringing total valuation to $30 billion. Funds will be used for compute infrastructure and safety research.', '2025-12-15 14:00:00', '2025-12-15 14:00:00'),
('ai-news', 5, 'Growing Concerns Over AI-Generated Content in Academic Publishing', 'https://nature.com/articles/ai-academic-integrity-2025', 'Nature', 'Major publishers report a surge in AI-generated paper submissions, prompting new detection and review policies across scientific journals.', '2025-12-15 16:00:00', '2025-12-15 16:00:00');

-- Tuesday December 16, 2025
INSERT INTO articles (mission_id, category_id, title, url, source, description, pub_date, created_at) VALUES
('ai-news', 2, 'Google DeepMind Releases Gemini 2.5 with Native Multimodal Generation', 'https://blog.google/gemini-2-5', 'Google AI Blog', 'Gemini 2.5 introduces native image, audio, and video generation capabilities. The model is available through Vertex AI for enterprise customers.', '2025-12-16 08:00:00', '2025-12-16 08:00:00'),
('ai-news', 3, 'Stanford Researchers Achieve Breakthrough in AI Alignment', 'https://stanford.edu/ai-alignment-breakthrough-2025', 'Stanford HAI', 'New technique called Constitutional AI 3.0 shows promising results in making AI systems more reliable and aligned with human values without sacrificing capability.', '2025-12-16 10:00:00', '2025-12-16 10:00:00'),
('ai-news', 4, 'Microsoft Expands Copilot to All Office 365 Users', 'https://microsoft.com/copilot-expansion-2025', 'Microsoft Blog', 'Microsoft announces Copilot will be available to all Office 365 subscribers starting January 2026, no longer requiring enterprise licenses.', '2025-12-16 13:00:00', '2025-12-16 13:00:00'),
('ai-news', 4, 'Mistral AI Raises $600M at $8B Valuation', 'https://mistral.ai/news/series-c', 'Mistral AI', 'French AI startup Mistral AI closes Series C funding, positioning itself as the leading European AI company. Plans to expand compute infrastructure in EU.', '2025-12-16 15:00:00', '2025-12-16 15:00:00'),
('ai-news', 5, 'AI Agents Market Expected to Reach $80B by 2028', 'https://techcrunch.com/ai-agents-market-2025', 'TechCrunch', 'Industry analysts predict explosive growth in AI agents market as enterprises adopt autonomous AI systems for complex workflows.', '2025-12-16 17:00:00', '2025-12-16 17:00:00');

-- Wednesday December 17, 2025
INSERT INTO articles (mission_id, category_id, title, url, source, description, pub_date, created_at) VALUES
('ai-news', 2, 'EU AI Act Full Implementation Takes Effect', 'https://ec.europa.eu/ai-act-implementation', 'European Commission', 'European Commission announces full AI Act implementation. High-risk AI systems must now comply with all requirements. Penalties can reach 7% of global revenue.', '2025-12-17 09:00:00', '2025-12-17 09:00:00'),
('ai-news', 3, 'Meta Releases Llama 4 with Advanced Reasoning Capabilities', 'https://ai.meta.com/llama-4', 'Meta AI', 'Latest Llama release includes advanced reasoning models in 70B and 400B parameter sizes, available for commercial use under permissive license.', '2025-12-17 11:00:00', '2025-12-17 11:00:00'),
('ai-news', 3, 'Hugging Face Introduces Transformers 6.0 with Native JAX Support', 'https://huggingface.co/blog/transformers-6', 'Hugging Face', 'Major update to the popular library adds native JAX support, improved memory efficiency, and faster inference for large models.', '2025-12-17 14:00:00', '2025-12-17 14:00:00'),
('ai-news', 4, 'NVIDIA Reports Record AI Chip Revenue in Q4 2025', 'https://nvidia.com/investor/q4-2025', 'NVIDIA', 'NVIDIA data center revenue reaches $25B in Q4, driven by continued demand for H200 GPUs and Blackwell shipments.', '2025-12-17 16:00:00', '2025-12-17 16:00:00'),
('ai-news', 5, 'Open Source AI Models Now Surpass Proprietary Performance on Key Benchmarks', 'https://huggingface.co/blog/open-source-leadership', 'Hugging Face', 'Analysis shows open-source models like Llama 4 and Mixtral now exceed GPT-4o level performance on standard benchmarks, signaling shift in AI landscape.', '2025-12-17 18:00:00', '2025-12-17 18:00:00');

-- Thursday December 18, 2025
INSERT INTO articles (mission_id, category_id, title, url, source, description, pub_date, created_at) VALUES
('ai-news', 2, 'xAI Launches Grok-3 with Real-Time Web Access and Reasoning', 'https://x.ai/grok-3', 'xAI', 'Elon Musks xAI releases Grok-3 with real-time web browsing, image generation, and improved reasoning. Available to X Premium subscribers.', '2025-12-18 08:00:00', '2025-12-18 08:00:00'),
('ai-news', 3, 'Berkeley Researchers Propose New Approach to AI Safety', 'https://bair.berkeley.edu/safety-paper-2025', 'Berkeley AI Research', 'Novel framework combines formal verification with empirical testing to provide stronger guarantees about AI system behavior in deployment.', '2025-12-18 10:00:00', '2025-12-18 10:00:00'),
('ai-news', 4, 'Amazon Announces Custom AI Chips for AWS Customers', 'https://aws.amazon.com/trainium3', 'AWS Blog', 'AWS unveils Trainium3 chips with 6x performance improvement over previous generation, challenging NVIDIA dominance in cloud AI compute.', '2025-12-18 12:00:00', '2025-12-18 12:00:00'),
('ai-news', 4, 'Cohere Acquired by Oracle for $5B', 'https://oracle.com/cohere-acquisition-2025', 'Oracle', 'Oracle acquires enterprise AI startup Cohere to strengthen its cloud AI offerings, marking one of the largest AI acquisitions of 2025.', '2025-12-18 14:00:00', '2025-12-18 14:00:00'),
('ai-news', 5, 'China Announces Updated AI Governance Framework', 'https://reuters.com/china-ai-governance-2025', 'Reuters', 'Chinese regulators release updated AI governance framework, establishing stricter requirements for foundation model developers and deployers.', '2025-12-18 16:00:00', '2025-12-18 16:00:00');

-- Friday December 19, 2025
INSERT INTO articles (mission_id, category_id, title, url, source, description, pub_date, created_at) VALUES
('ai-news', 2, 'Claude 4 Released with Extended Context and Advanced Tool Use', 'https://anthropic.com/claude-4', 'Anthropic', 'Anthropic releases Claude 4 featuring 500K context window, improved tool use, and new computer use capabilities for enterprise automation.', '2025-12-19 09:00:00', '2025-12-19 09:00:00'),
('ai-news', 3, 'MIT Study Shows AI Can Predict Protein Structures with 99.5% Accuracy', 'https://mit.edu/protein-ai-study-2025', 'MIT News', 'Researchers achieve near-perfect accuracy in protein structure prediction, surpassing AlphaFold 3 performance on novel protein families.', '2025-12-19 11:00:00', '2025-12-19 11:00:00'),
('ai-news', 3, 'New Benchmark Reveals Improvements in LLM Mathematical Reasoning', 'https://arxiv.org/abs/2512.67890', 'arXiv', 'Comprehensive benchmark shows significant improvements in current LLMs ability to perform multi-step mathematical reasoning compared to 2024 models.', '2025-12-19 13:00:00', '2025-12-19 13:00:00'),
('ai-news', 4, 'Salesforce Integrates AI Agents Across Entire Product Suite', 'https://salesforce.com/ai-agents-2025', 'Salesforce', 'Salesforce announces autonomous AI agents for sales, service, and marketing clouds, capable of handling complex customer interactions end-to-end.', '2025-12-19 15:00:00', '2025-12-19 15:00:00'),
('ai-news', 5, 'AI Coding Assistants Used by 90% of Professional Developers', 'https://stackoverflow.com/survey/2025-ai', 'Stack Overflow', 'Annual developer survey shows AI coding assistants have become essential tools, with GitHub Copilot and Claude leading adoption.', '2025-12-19 17:00:00', '2025-12-19 17:00:00');

-- Saturday December 20, 2025
INSERT INTO articles (mission_id, category_id, title, url, source, description, pub_date, created_at) VALUES
('ai-news', 3, 'DeepMind Publishes New Approach to AI Interpretability', 'https://deepmind.google/interpretability-2025', 'DeepMind', 'Research team introduces mechanistic interpretability techniques that can identify specific circuits in large language models responsible for behaviors.', '2025-12-20 10:00:00', '2025-12-20 10:00:00'),
('ai-news', 4, 'Character.AI Reaches 50 Million Daily Active Users', 'https://character.ai/blog/growth-2025', 'Character.AI', 'Conversational AI platform reports massive growth, with users spending average of 3 hours daily interacting with AI characters.', '2025-12-20 12:00:00', '2025-12-20 12:00:00'),
('ai-news', 5, 'Growing Debate Over AI Model Weights as Export-Controlled Technology', 'https://wired.com/ai-export-control-2025', 'Wired', 'US lawmakers debate whether advanced AI model weights should be classified as export-controlled technology, potentially limiting open-source releases.', '2025-12-20 14:00:00', '2025-12-20 14:00:00');

-- Sunday December 21, 2025
INSERT INTO articles (mission_id, category_id, title, url, source, description, pub_date, created_at) VALUES
('ai-news', 2, 'OpenAI Announces Partnership with Major Healthcare Providers', 'https://openai.com/healthcare-partnership-2025', 'OpenAI Blog', 'OpenAI partners with ten leading US health systems to develop specialized medical AI models, with strict data privacy protections.', '2025-12-21 09:00:00', '2025-12-21 09:00:00'),
('ai-news', 3, 'New Open Source LLM Training Framework Reduces Costs by 80%', 'https://github.com/efficient-llm-training-2025', 'GitHub', 'Community-developed framework enables training of 100B parameter models on consumer hardware through novel memory optimization techniques.', '2025-12-21 11:00:00', '2025-12-21 11:00:00'),
('ai-news', 4, 'Apple Releases Apple Intelligence 2.0 for All Devices', 'https://apple.com/apple-intelligence-2', 'Apple', 'Apple announces major update to Apple Intelligence with on-device AI features powered by custom neural processing units.', '2025-12-21 14:00:00', '2025-12-21 14:00:00'),
('ai-news', 5, 'AI Safety Summit 2026 Dates Announced', 'https://gov.uk/ai-safety-summit-2026', 'UK Government', 'UK government announces AI Safety Summit 2026 will be held in London, with focus on frontier model governance and international cooperation.', '2025-12-21 16:00:00', '2025-12-21 16:00:00');
