"""Los 5 prompts estandarizados de calidad (Parte A.3) y su clave de corrección.

La rúbrica 0-3 completa está en benchmarks/RUBRIC.md. Cada prompt incluye
"check": pistas objetivas que el corrector humano usa al puntuar.
"""

QUALITY_PROMPTS = [
    {
        "id": "math",
        "category": "matemáticas",
        "prompt": ("A train leaves at 14:30 and arrives at 18:05. It stops for "
                   "12 minutes in total. What is the actual moving time in "
                   "minutes? Show your work briefly."),
        "check": "Respuesta correcta: 215 - 12 = 203 minutos.",
    },
    {
        "id": "code",
        "category": "código",
        "prompt": ("Write a Python function `is_balanced(s)` that returns True "
                   "if the parentheses (), [], {} in the string are balanced. "
                   "Only output the code."),
        "check": ("Debe usar una pila, mapear cierres a aperturas y devolver "
                  "not stack al final. Se valida ejecutándola sobre 5 casos."),
    },
    {
        "id": "summary",
        "category": "resumen",
        "prompt": ("Summarize in exactly 3 bullet points: 'The Transformer "
                   "architecture replaced recurrence with self-attention, "
                   "enabling parallel training over sequences. Its encoder-"
                   "decoder design uses multi-head attention and positional "
                   "encodings. Scaling these models led to modern LLMs, but "
                   "inference cost grows with context length because attention "
                   "is quadratic and the KV cache grows linearly.'"),
        "check": ("3 bullets exactos; debe conservar: self-attention/paralelismo, "
                  "multi-head+positional encodings, coste de inferencia/KV cache."),
    },
    {
        "id": "factual",
        "category": "memoria factual",
        "prompt": ("What year was the Python programming language first "
                   "released, and who created it? Answer in one sentence."),
        "check": "1991, Guido van Rossum.",
    },
    {
        "id": "reasoning",
        "category": "razonamiento",
        "prompt": ("Anna is taller than Berta. Carla is shorter than Berta. "
                   "Diana is taller than Anna. Who is the second tallest? "
                   "Explain in two sentences."),
        "check": "Anna (orden: Diana > Anna > Berta > Carla).",
    },
]
