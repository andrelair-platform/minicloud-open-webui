"""
Build-time version of the French BM25 preprocessor patch.

Patches /app/backend/open_webui/retrieval/utils.py in-place during docker build.
Semantically identical to the runtime patch-bm25-french init container in the
previous deployment — same function injected, same BM25Retriever.from_texts()
call modified, same idempotency check.

What this does:
- Replaces the default BM25Retriever tokenizer (whitespace split) with a
  French Snowball stemmer + stop-word filter.
- "sinistres" and "sinistre" → same stem (sinistr)
- "réassurance" and "réassurer" → same stem (réassur)
- Common French prepositions/articles removed before scoring
"""

TARGET = '/app/backend/open_webui/retrieval/utils.py'

with open(TARGET) as f:
    src = f.read()

if '_french_bm25_preprocess' in src:
    print('bm25-french-patch: already applied, skipping')
    raise SystemExit(0)

if 'from langchain_community.retrievers import BM25Retriever' not in src:
    print('ERROR: BM25Retriever import anchor not found in utils.py')
    print('The Open WebUI version may have changed — patch needs updating.')
    raise SystemExit(1)

if 'BM25Retriever.from_texts(' not in src:
    print('ERROR: BM25Retriever.from_texts() call not found in utils.py')
    print('The Open WebUI version may have changed — patch needs updating.')
    raise SystemExit(1)

french_fn = (
    '\n'
    '# French BM25 preprocessor — baked into image at build time\n'
    '_bm25_fr_stemmer = None\n'
    '\n'
    '\n'
    'def _french_bm25_preprocess(text):\n'
    '    """Tokenise French text for BM25: lowercase, stem, drop stop words."""\n'
    '    import re as _re\n'
    '    from nltk.stem.snowball import SnowballStemmer as _S\n'
    '    global _bm25_fr_stemmer\n'
    '    if _bm25_fr_stemmer is None:\n'
    '        _bm25_fr_stemmer = _S(\'french\')\n'
    '    _STOP = {\n'
    '        \'le\', \'la\', \'les\', \'de\', \'du\', \'des\', \'un\', \'une\',\n'
    '        \'et\', \'en\', \'au\', \'aux\', \'ce\', \'se\', \'sa\', \'son\', \'ses\',\n'
    '        \'il\', \'elle\', \'ils\', \'elles\', \'je\', \'tu\', \'nous\', \'vous\', \'on\',\n'
    '        \'que\', \'qui\', \'dont\', \'ou\', \'est\', \'sont\',\n'
    '        \'par\', \'pour\', \'sur\', \'sous\', \'dans\', \'avec\', \'sans\',\n'
    '        \'mais\', \'ni\', \'si\', \'ne\', \'pas\', \'plus\', \'aussi\', \'comme\',\n'
    '        \'tout\', \'tous\', \'cette\', \'cet\', \'ces\', \'y\', \'qu\', \'ca\',\n'
    '    }\n'
    '    tokens = _re.findall(\n'
    '        r\'[a-zàâäéèêë\'\n'
    '        r\'îïôùûüç]+\',\n'
    '        text.lower(),\n'
    '    )\n'
    '    return [\n'
    '        _bm25_fr_stemmer.stem(t)\n'
    '        for t in tokens\n'
    '        if t not in _STOP and len(t) > 2\n'
    '    ]\n'
    '\n'
    '\n'
)

src = src.replace(
    'from langchain_community.retrievers import BM25Retriever\n',
    'from langchain_community.retrievers import BM25Retriever\n' + french_fn,
)

src = src.replace(
    '        bm25_retriever = BM25Retriever.from_texts(\n'
    '            texts=bm25_texts,\n'
    '            metadatas=bm25_metadatas,\n'
    '        )',
    '        bm25_retriever = BM25Retriever.from_texts(\n'
    '            texts=bm25_texts,\n'
    '            metadatas=bm25_metadatas,\n'
    '            preprocess_func=_french_bm25_preprocess,\n'
    '        )',
)

if '_french_bm25_preprocess' not in src:
    print('ERROR: patch was applied but function not found in output — check replace anchors')
    raise SystemExit(1)

with open(TARGET, 'w') as f:
    f.write(src)

print('bm25-french-patch: successfully patched utils.py with French BM25 preprocessor')
