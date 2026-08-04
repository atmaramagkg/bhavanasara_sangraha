const List<String> schemaStatements = [
  '''
  CREATE TABLE IF NOT EXISTS period_schemes (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
  )
  ''',

  '''
  CREATE TABLE IF NOT EXISTS period_nodes (
    id INTEGER PRIMARY KEY,
    scheme_id INTEGER NOT NULL REFERENCES period_schemes(id),
    parent_id INTEGER REFERENCES period_nodes(id),
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    time_start TEXT,
    time_end TEXT,
    sort_order INTEGER DEFAULT 0
  )
  ''',

  '''
  CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    notes TEXT
  )
  ''',

  '''
  CREATE TABLE IF NOT EXISTS verses (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id),

    division_1 TEXT,
    division_2 TEXT,
    chapter TEXT,
    section TEXT,

    verse_start TEXT,
    verse_end TEXT,

    ref_display TEXT,

    original_text TEXT,
    translation_text TEXT,
    commentary_text TEXT,

    sort_order INTEGER DEFAULT 0,

    UNIQUE(book_id, ref_display)
  )
  ''',

  '''
  CREATE TABLE IF NOT EXISTS compiled_sections (
    id INTEGER PRIMARY KEY,
    chapter_title TEXT,
    section_title TEXT,
    main_period_id INTEGER REFERENCES period_nodes(id),
    subperiod_id INTEGER REFERENCES period_nodes(id),
    sort_order INTEGER DEFAULT 0
  )
  ''',

  '''
  CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY,
    compiled_section_id INTEGER NOT NULL REFERENCES compiled_sections(id),
    quote_type TEXT DEFAULT 'quote',
    quote_text TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0
  )
  ''',

  '''
  CREATE TABLE IF NOT EXISTS citations (
    id INTEGER PRIMARY KEY,
    quote_id INTEGER NOT NULL REFERENCES quotes(id),
    source_book_id INTEGER REFERENCES books(id),
    source_verse_id INTEGER REFERENCES verses(id),
    ref_display TEXT,
    confidence TEXT DEFAULT 'exact',
    notes TEXT
  )
  ''',
];