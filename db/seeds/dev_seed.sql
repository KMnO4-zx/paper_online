DELETE FROM authors
WHERE paper_id IN ('0wSlFpMsGb', 'KurYdcCbjv', '2GmXJnyNM4');

DELETE FROM keywords
WHERE paper_id IN ('0wSlFpMsGb', 'KurYdcCbjv', '2GmXJnyNM4');

DELETE FROM papers
WHERE id IN ('0wSlFpMsGb', 'KurYdcCbjv', '2GmXJnyNM4');

INSERT INTO papers (id, title, abstract, keywords, pdf, venue, primary_area, llm_response)
VALUES
  (
    '0wSlFpMsGb',
    'Common Corpus: The Largest Collection of Ethical Data for LLM Pre-Training',
    'Large Language Models (LLMs) are pre-trained on large data from different sources and domains. In this paper, we introduce Common Corpus, the largest open dataset for LLM pre-training, assembled from uncopyrighted or permissively licensed data and amounting to about two trillion tokens.',
    '["dataset", "pre-training", "large language models"]'::jsonb,
    'https://openreview.net/pdf?id=0wSlFpMsGb',
    'ICLR 2026 Oral',
    'datasets and benchmarks',
    NULL
  ),
  (
    'KurYdcCbjv',
    'Generalized Linear Mode Connectivity for Transformers',
    'We introduce a unified framework that captures four symmetry classes and reveals low- and zero-barrier linear interpolation paths between independently trained Vision Transformers and GPT-2 models.',
    '["Transformer", "Model Fusion", "Linear Mode Connectivity"]'::jsonb,
    'https://openreview.net/pdf?id=KurYdcCbjv',
    'NeurIPS 2025 oral',
    'deep_learning',
    NULL
  ),
  (
    '2GmXJnyNM4',
    'Implicit Regularization for Tubal Tensor Factorizations via Gradient Descent',
    'We provide a rigorous analysis showing that gradient descent in an overparametrized tensor factorization model with a small random initialization exhibits an implicit bias toward solutions of low tubal rank.',
    '["implicit regularization", "tensor factorization", "overparameterization"]'::jsonb,
    'https://openreview.net/pdf?id=2GmXJnyNM4',
    'ICML 2025 oral',
    'theory->learning_theory',
    NULL
  );

INSERT INTO authors (paper_id, author_name, author_order)
VALUES
  ('0wSlFpMsGb', 'Pierre-Carl Langlais', 0),
  ('0wSlFpMsGb', 'Pavel Chizhov', 1),
  ('0wSlFpMsGb', 'Catherine Arnett', 2),
  ('KurYdcCbjv', 'Alexander Theus', 0),
  ('KurYdcCbjv', 'Alessandro Cabodi', 1),
  ('KurYdcCbjv', 'Sotiris Anagnostidis', 2),
  ('2GmXJnyNM4', 'Santhosh Karnik', 0),
  ('2GmXJnyNM4', 'Anna Veselovska', 1),
  ('2GmXJnyNM4', 'Mark Iwen', 2);

INSERT INTO keywords (paper_id, keyword)
VALUES
  ('0wSlFpMsGb', 'dataset'),
  ('0wSlFpMsGb', 'pre-training'),
  ('0wSlFpMsGb', 'large language models'),
  ('KurYdcCbjv', 'Transformer'),
  ('KurYdcCbjv', 'Model Fusion'),
  ('KurYdcCbjv', 'Linear Mode Connectivity'),
  ('2GmXJnyNM4', 'implicit regularization'),
  ('2GmXJnyNM4', 'tensor factorization'),
  ('2GmXJnyNM4', 'overparameterization');
