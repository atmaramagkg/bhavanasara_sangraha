import 'package:sqflite/sqflite.dart';
import '../models/lila_period.dart';
import '../models/book.dart';
import '../models/verse.dart';
import '../models/danda.dart';

class SubPeriod {
  final int id;
  final int parentId;
  final String code;
  final String title;
  final String timeRange;

  const SubPeriod({
    required this.id,
    required this.parentId,
    required this.code,
    required this.title,
    required this.timeRange,
  });
}

class LilaSectionItem {
  final int id;
  final int periodNodeId;
  final int sortOrder;
  final String title;

  const LilaSectionItem({
    required this.id,
    required this.periodNodeId,
    required this.sortOrder,
    required this.title,
  });
}

class VerseDetail {
  final int quoteId;
  final String quoteText;
  final String refDisplay;
  final String bookTitle;
  final int? verseId;

  const VerseDetail({
    required this.quoteId,
    required this.quoteText,
    required this.refDisplay,
    required this.bookTitle,
    this.verseId,
  });
}

class ContinuousReadingItem {
  final LilaPeriod mainPeriod;
  final SubPeriod subPeriod;
  final LilaSectionItem section;
  final List<VerseDetail> verses;
  final bool isFirstInSubPeriod;
  final bool isFirstInMainPeriod;

  const ContinuousReadingItem({
    required this.mainPeriod,
    required this.subPeriod,
    required this.section,
    required this.verses,
    this.isFirstInSubPeriod = false,
    this.isFirstInMainPeriod = false,
  });
}

class BssRepository {
  final Database db;

  BssRepository(this.db);

  Future<List<LilaPeriod>> getMainPeriods({int languageId = 1}) async {
    const query = '''
      SELECT 
        p.id,
        p.code,
        p.name_key,
        p.time_start,
        p.time_end,
        COALESCE(
          (SELECT translated_text FROM translations WHERE translation_key = p.name_key AND language_id = ?),
          (SELECT translated_text FROM translations WHERE translation_key = p.name_key AND language_id = (SELECT id FROM languages WHERE code = 'en')),
          p.code
        ) AS title
      FROM period_nodes p
      WHERE p.period_type = 'main'
      ORDER BY p.sort_order ASC;
    ''';

    final List<Map<String, dynamic>> results = await db.rawQuery(query, [languageId]);

    return results.map<LilaPeriod>((row) {
      final start = row['time_start'] as String? ?? '';
      final end = row['time_end'] as String? ?? '';
      final timeDisplay = (start.isNotEmpty && end.isNotEmpty) ? '$start - $end' : '';

      return LilaPeriod(
        id: (row['id'] as int?) ?? 1,
        code: (row['code'] as String?) ?? '',
        nameKey: (row['name_key'] as String?) ?? '',
        title: (row['title'] as String?) ?? '',
        timeRange: timeDisplay,
      );
    }).toList();
  }

  Future<List<SubPeriod>> getSubPeriods(int mainPeriodId, {int languageId = 1}) async {
    const query = '''
      SELECT 
        p.id,
        p.parent_id,
        p.code,
        p.time_start,
        p.time_end,
        COALESCE(
          (SELECT translated_text FROM translations WHERE translation_key = p.name_key AND language_id = ?),
          (SELECT translated_text FROM translations WHERE translation_key = p.name_key AND language_id = (SELECT id FROM languages WHERE code = 'en')),
          p.code
        ) AS title
      FROM period_nodes p
      WHERE p.parent_id = ? AND p.period_type = 'sub'
      ORDER BY p.sort_order ASC;
    ''';

    final List<Map<String, dynamic>> results = await db.rawQuery(query, [languageId, mainPeriodId]);

    return results.map<SubPeriod>((row) {
      final start = row['time_start'] as String? ?? '';
      final end = row['time_end'] as String? ?? '';
      final timeDisplay = (start.isNotEmpty && end.isNotEmpty) ? '$start - $end' : '';

      return SubPeriod(
        id: (row['id'] as int?) ?? 0,
        parentId: (row['parent_id'] as int?) ?? 0,
        code: (row['code'] as String?) ?? '',
        title: (row['title'] as String?) ?? '',
        timeRange: timeDisplay,
      );
    }).toList();
  }

  Future<List<Danda>> getDandas({int? languageId}) async {
    final int langId = languageId ?? await _currentLanguageId();
    const query = '''
      SELECT
        d.id,
        d.main_period_id,
        d.sort_order,
        d.time_start,
        d.time_end,
        COALESCE(
          (SELECT translated_text FROM translations WHERE translation_key = d.description_key AND language_id = ?),
          (SELECT translated_text FROM translations WHERE translation_key = d.description_key AND language_id = (SELECT id FROM languages WHERE code = 'en')),
          d.description_key
        ) AS description
      FROM dandas d
      ORDER BY d.sort_order ASC;
    ''';

    final List<Map<String, dynamic>> results =
        await db.rawQuery(query, [langId]);

    return results.map<Danda>((row) {
      return Danda(
        id: (row['id'] as int?) ?? 0,
        mainPeriodId: (row['main_period_id'] as int?) ?? 0,
        sortOrder: (row['sort_order'] as int?) ?? 0,
        timeStart: (row['time_start'] as String?) ?? '',
        timeEnd: (row['time_end'] as String?) ?? '',
        description: (row['description'] as String?) ?? '',
      );
    }).toList();
  }

  /// Resolves the id of the currently selected language from `app_settings`,
  /// falling back to the id of English ('en').
  Future<int> _currentLanguageId() async {
    String code = 'en';
    final List<Map<String, dynamic>> settings = await db.rawQuery(
      "SELECT setting_value FROM app_settings WHERE setting_key = 'selected_language_code'",
    );
    if (settings.isNotEmpty) {
      code = settings.first['setting_value'] as String? ?? 'en';
    }
    final List<Map<String, dynamic>> languages = await db.rawQuery(
      'SELECT id FROM languages WHERE code = ?',
      [code],
    );
    if (languages.isNotEmpty) return languages.first['id'] as int;
    return 1;
  }

  Future<List<LilaSectionItem>> getSectionsForPeriod(int periodNodeId, {int languageId = 1}) async {
    const query = '''
      SELECT 
        s.id,
        s.period_node_id,
        s.sort_order,
        COALESCE(
          (SELECT translated_text FROM translations WHERE translation_key = s.title_key AND language_id = ?),
          (SELECT translated_text FROM translations WHERE translation_key = s.title_key AND language_id = (SELECT id FROM languages WHERE code = 'en')),
          s.title_key
        ) AS title
      FROM sections s
      WHERE s.period_node_id = ?
      ORDER BY s.sort_order ASC;
    ''';

    final List<Map<String, dynamic>> results = await db.rawQuery(query, [languageId, periodNodeId]);

    return results.map<LilaSectionItem>((row) {
      return LilaSectionItem(
        id: (row['id'] as int?) ?? 0,
        periodNodeId: (row['period_node_id'] as int?) ?? 0,
        sortOrder: (row['sort_order'] as int?) ?? 0,
        title: (row['title'] as String?) ?? '',
      );
    }).toList();
  }

  Future<List<VerseDetail>> getVersesForSection(int sectionId, {int languageId = 1}) async {
    const query = '''
      SELECT 
        q.id AS quote_id,
        COALESCE(q.quote_text, '') AS quote_text,
        COALESCE(c.ref_display, '') AS ref_display,
        c.source_verse_id AS verse_id,
        COALESCE(tb.translated_text, b.slug, '') AS book_title
      FROM quotes q
      LEFT JOIN citations c ON q.id = c.quote_id
      LEFT JOIN books b ON c.source_book_id = b.id
      LEFT JOIN translations tb 
        ON b.title_key = tb.translation_key 
       AND tb.language_id = ?
      WHERE q.section_id = ?
      ORDER BY q.sort_order ASC;
    ''';

    final List<Map<String, dynamic>> results = await db.rawQuery(query, [languageId, sectionId]);

    return results.map<VerseDetail>((row) {
      return VerseDetail(
        quoteId: (row['quote_id'] as int?) ?? 0,
        quoteText: (row['quote_text'] as String?) ?? '',
        refDisplay: (row['ref_display'] as String?) ?? '',
        bookTitle: (row['book_title'] as String?) ?? '',
        verseId: (row['verse_id'] as int?) ?? 0,
      );
    }).toList();
  }

  /// Builds the entire continuous reading feed (every main period -> every
  /// sub period -> every section -> every quote in it) in a single round
  /// trip to the database.
  ///
  /// This used to be a triple-nested loop that issued one query per main
  /// period, one per sub period, one per section, and one per section's
  /// quotes -- roughly 1 + 8 + ~24 + 129 ~= 160+ sequential awaited queries
  /// for the full 129-section feed. That's now a single JOIN query, with
  /// the nested period/section/quote structure rebuilt by grouping the flat
  /// result rows in Dart (they arrive pre-sorted, so grouping is a single
  /// linear pass, not a search).
  Future<List<ContinuousReadingItem>> loadFullContinuousFeed({int languageId = 1}) async {
    const query = '''
      SELECT
        pm.id AS main_id, pm.code AS main_code, pm.name_key AS main_name_key,
        pm.time_start AS main_time_start, pm.time_end AS main_time_end,
        COALESCE(tm.translated_text, tm_en.translated_text, pm.code) AS main_title,

        ps.id AS sub_id, ps.parent_id AS sub_parent_id, ps.code AS sub_code,
        ps.time_start AS sub_time_start, ps.time_end AS sub_time_end,
        COALESCE(tsub.translated_text, tsub_en.translated_text, ps.code) AS sub_title,

        sec.id AS section_id, sec.period_node_id AS section_period_node_id,
        sec.sort_order AS section_sort_order,
        COALESCE(tsec.translated_text, tsec_en.translated_text, sec.title_key) AS section_title,

        q.id AS quote_id, COALESCE(q.quote_text, '') AS quote_text,
        COALESCE(c.ref_display, '') AS ref_display, c.source_verse_id AS verse_id,
        COALESCE(tb.translated_text, b.slug, '') AS book_title

      FROM period_nodes pm
      JOIN period_nodes ps ON ps.parent_id = pm.id AND ps.period_type = 'sub'
      JOIN sections sec ON sec.period_node_id = ps.id
      LEFT JOIN quotes q ON q.section_id = sec.id
      LEFT JOIN citations c ON c.quote_id = q.id
      LEFT JOIN books b ON b.id = c.source_book_id
      LEFT JOIN translations tm
        ON tm.translation_key = pm.name_key AND tm.language_id = ?
      LEFT JOIN translations tm_en
        ON tm_en.translation_key = pm.name_key
       AND tm_en.language_id = (SELECT id FROM languages WHERE code = 'en')
      LEFT JOIN translations tsub
        ON tsub.translation_key = ps.name_key AND tsub.language_id = ?
      LEFT JOIN translations tsub_en
        ON tsub_en.translation_key = ps.name_key
       AND tsub_en.language_id = (SELECT id FROM languages WHERE code = 'en')
      LEFT JOIN translations tsec
        ON tsec.translation_key = sec.title_key AND tsec.language_id = ?
      LEFT JOIN translations tsec_en
        ON tsec_en.translation_key = sec.title_key
       AND tsec_en.language_id = (SELECT id FROM languages WHERE code = 'en')
      LEFT JOIN translations tb
        ON tb.translation_key = b.title_key AND tb.language_id = ?

      WHERE pm.period_type = 'main'
      ORDER BY pm.sort_order ASC, ps.sort_order ASC, sec.sort_order ASC, q.sort_order ASC;
    ''';

    final List<Map<String, dynamic>> rows = await db.rawQuery(
      query,
      [languageId, languageId, languageId, languageId],
    );

    final List<ContinuousReadingItem> items = [];

    int previousMainId = -1;
    int previousSubId = -1;

    LilaPeriod? currentMain;
    SubPeriod? currentSub;
    LilaSectionItem? currentSection;
    List<VerseDetail> currentVerses = [];
    int currentSectionId = -1;

    // Pushes the section being accumulated (main+sub+section+its verses)
    // onto `items` as one ContinuousReadingItem, then updates the
    // "previous" trackers used to compute isFirst*Period for the next one.
    void flushCurrentSection() {
      if (currentSection == null || currentMain == null || currentSub == null) {
        return;
      }

      items.add(ContinuousReadingItem(
        mainPeriod: currentMain,
        subPeriod: currentSub,
        section: currentSection,
        verses: List<VerseDetail>.from(currentVerses),
        isFirstInSubPeriod: currentSub.id != previousSubId,
        isFirstInMainPeriod: currentMain.id != previousMainId,
      ));

      previousMainId = currentMain.id;
      previousSubId = currentSub.id;
    }

    for (final row in rows) {
      final int sectionId = (row['section_id'] as int?) ?? 0;

      if (sectionId != currentSectionId) {
        // Rows are pre-sorted by section, so a change in section id means
        // the previous section's group is complete.
        flushCurrentSection();

        final String mainStart = (row['main_time_start'] as String?) ?? '';
        final String mainEnd = (row['main_time_end'] as String?) ?? '';
        currentMain = LilaPeriod(
          id: (row['main_id'] as int?) ?? 1,
          code: (row['main_code'] as String?) ?? '',
          nameKey: (row['main_name_key'] as String?) ?? '',
          title: (row['main_title'] as String?) ?? '',
          timeRange: (mainStart.isNotEmpty && mainEnd.isNotEmpty)
              ? '$mainStart - $mainEnd'
              : '',
        );

        final String subStart = (row['sub_time_start'] as String?) ?? '';
        final String subEnd = (row['sub_time_end'] as String?) ?? '';
        currentSub = SubPeriod(
          id: (row['sub_id'] as int?) ?? 0,
          parentId: (row['sub_parent_id'] as int?) ?? 0,
          code: (row['sub_code'] as String?) ?? '',
          title: (row['sub_title'] as String?) ?? '',
          timeRange: (subStart.isNotEmpty && subEnd.isNotEmpty)
              ? '$subStart - $subEnd'
              : '',
        );

        currentSection = LilaSectionItem(
          id: sectionId,
          periodNodeId: (row['section_period_node_id'] as int?) ?? 0,
          sortOrder: (row['section_sort_order'] as int?) ?? 0,
          title: (row['section_title'] as String?) ?? '',
        );

        currentVerses = [];
        currentSectionId = sectionId;
      }

      // Sections with zero quotes still produce one row (LEFT JOIN quotes),
      // with quote_id NULL -- skip adding a verse for those.
      final int? quoteId = row['quote_id'] as int?;
      if (quoteId != null) {
        currentVerses.add(VerseDetail(
          quoteId: quoteId,
          quoteText: (row['quote_text'] as String?) ?? '',
          refDisplay: (row['ref_display'] as String?) ?? '',
          bookTitle: (row['book_title'] as String?) ?? '',
          verseId: (row['verse_id'] as int?) ?? 0,
        ));
      }
    }

    flushCurrentSection(); // the final group is never flushed inside the loop

    return items;
  }

  /// The id of whichever main period the current device time falls in,
  /// or null if the lookup fails for any reason (caller should fall back
  /// to a sensible default, e.g. period 1).
  Future<int?> getCurrentMainPeriodId({DateTime? now}) async {
    const query = '''
      SELECT id, time_start, time_end
      FROM period_nodes
      WHERE period_type = 'main'
      ORDER BY sort_order ASC;
    ''';

    final List<Map<String, dynamic>> results = await db.rawQuery(query);
    if (results.isEmpty) return null;

    final DateTime t = now ?? DateTime.now();
    final String nowHm = _toHm(t);

    for (final row in results) {
      final String start = (row['time_start'] as String?) ?? '';
      final String end = (row['time_end'] as String?) ?? '';
      if (_timeInRange(nowHm, start, end)) return row['id'] as int?;
    }
    return results.first['id'] as int?;
  }

  /// The main + sub period pair the current device time falls in, or null if
  /// the lookup fails (caller should fall back to a sensible default).
  /// Sub periods tile the whole day contiguously and are where the reading
  /// sections actually live, so matching a sub period is the precise answer
  /// to "what am I supposed to be reading right now".
  Future<({int mainPeriodId, int subPeriodId})?> getCurrentPeriodPair({DateTime? now}) async {
    const query = '''
      SELECT p.id AS sub_id, p.parent_id, p.time_start, p.time_end
      FROM period_nodes p
      WHERE p.period_type = 'sub'
      ORDER BY p.sort_order ASC;
    ''';

    final List<Map<String, dynamic>> results = await db.rawQuery(query);
    if (results.isEmpty) return null;

    final DateTime t = now ?? DateTime.now();
    final String nowHm = _toHm(t);

    for (final row in results) {
      final String start = (row['time_start'] as String?) ?? '';
      final String end = (row['time_end'] as String?) ?? '';
      if (_timeInRange(nowHm, start, end)) {
        return (
          mainPeriodId: (row['parent_id'] as int?) ?? 1,
          subPeriodId: (row['sub_id'] as int?) ?? 0,
        );
      }
    }
    return null;
  }

  /// "HH:MM" of [t], zero-padded, e.g. '05:07'.
  static String _toHm(DateTime t) =>
      '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

  /// Whether nowHm ("HH:MM") is inside [start, end). Ranges that wrap past
  /// midnight (start > end, e.g. Niśa: 22:48 -> 03:36) are handled.
  static bool _timeInRange(String nowHm, String start, String end) {
    if (start.isEmpty || end.isEmpty) return false;
    return start.compareTo(end) <= 0
        ? nowHm.compareTo(start) >= 0 && nowHm.compareTo(end) < 0
        : nowHm.compareTo(start) >= 0 || nowHm.compareTo(end) < 0;
  }

  /// All source scriptures, with how many quotes cite each one.
  Future<List<Book>> getAllBooks({int languageId = 1}) async {
    const query = '''
      SELECT
        b.id,
        b.slug,
        COALESCE(
          (SELECT translated_text FROM translations WHERE translation_key = b.title_key AND language_id = ?),
          (SELECT translated_text FROM translations WHERE translation_key = b.title_key AND language_id = (SELECT id FROM languages WHERE code = 'en')),
          b.slug
        ) AS title,
        COALESCE(
          (SELECT translated_text FROM translations WHERE translation_key = b.author_key AND language_id = ?),
          (SELECT translated_text FROM translations WHERE translation_key = b.author_key AND language_id = (SELECT id FROM languages WHERE code = 'en')),
          ''
        ) AS author,
        (SELECT COUNT(*) FROM citations c WHERE c.source_book_id = b.id) AS quote_count
      FROM books b
      WHERE (SELECT COUNT(*) FROM citations c WHERE c.source_book_id = b.id) > 0
      ORDER BY title ASC;
    ''';

    final List<Map<String, dynamic>> results =
        await db.rawQuery(query, [languageId, languageId]);

    return results.map((row) {
      return Book(
        id: (row['id'] as int?) ?? 0,
        slug: (row['slug'] as String?) ?? '',
        title: (row['title'] as String?) ?? '',
        author: (row['author'] as String?) ?? '',
        quoteCount: (row['quote_count'] as int?) ?? 0,
      );
    }).toList();
  }

  /// A single book's title (used to give the verse-detail screen book
  /// context, since verses.ref_display alone -- e.g. "10.13.1" -- doesn't
  /// say which scripture it's from).
  Future<Book?> getBookById(int bookId, {int languageId = 1}) async {
    const query = '''
      SELECT
        b.id,
        b.slug,
        COALESCE(
          (SELECT translated_text FROM translations WHERE translation_key = b.title_key AND language_id = ?),
          (SELECT translated_text FROM translations WHERE translation_key = b.title_key AND language_id = (SELECT id FROM languages WHERE code = 'en')),
          b.slug
        ) AS title,
        COALESCE(
          (SELECT translated_text FROM translations WHERE translation_key = b.author_key AND language_id = ?),
          (SELECT translated_text FROM translations WHERE translation_key = b.author_key AND language_id = (SELECT id FROM languages WHERE code = 'en')),
          ''
        ) AS author
      FROM books b
      WHERE b.id = ?
      LIMIT 1;
    ''';

    final List<Map<String, dynamic>> results =
        await db.rawQuery(query, [languageId, languageId, bookId]);
    if (results.isEmpty) return null;

    final row = results.first;
    return Book(
      id: (row['id'] as int?) ?? 0,
      slug: (row['slug'] as String?) ?? '',
      title: (row['title'] as String?) ?? '',
      author: (row['author'] as String?) ?? '',
      quoteCount: 0,
    );
  }

  /// All verses of a book from the `verses` table, ordered the way they
  /// appear in the book (division -> chapter -> verse), not the way they
  /// were inserted. Full texts arrive gradually, so most rows currently only
  /// carry the quoted translation.
  Future<List<Verse>> getVersesForBook(int bookId) async {
    final List<Map<String, dynamic>> rows = await db.query(
      'verses',
      where: 'book_id = ?',
      whereArgs: [bookId],
    );

    final List<Verse> verses = rows.map(Verse.fromMap).toList();
    verses.sort(_compareChronological);
    return verses;
  }

  /// The full record of one verse from the `verses` table (used by the
  /// verse reader reached from the reading pane and the book reader).
  Future<Verse?> getVerseById(int verseId) async {
    final List<Map<String, dynamic>> rows = await db.query(
      'verses',
      where: 'id = ?',
      whereArgs: [verseId],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return Verse.fromMap(rows.first);
  }

  /// Sorts verses as they appear in the book. Chapters may be dotted
  /// ("10.9", "2.6") so the segments are compared numerically, and a range
  /// verse (verse_start != verse_end) sorts by its start.
  static int _compareChronological(Verse a, Verse b) {
    final List<int> aChapter = _chapterParts(a.chapter);
    final List<int> bChapter = _chapterParts(b.chapter);
    final int shared = aChapter.length < bChapter.length ? aChapter.length : bChapter.length;
    for (int i = 0; i < shared; i++) {
      if (aChapter[i] != bChapter[i]) return aChapter[i].compareTo(bChapter[i]);
    }
    if (aChapter.length != bChapter.length) {
      return aChapter.length.compareTo(bChapter.length);
    }

    final int aStart = int.tryParse(a.verseStart ?? '') ?? 0;
    final int bStart = int.tryParse(b.verseStart ?? '') ?? 0;
    if (aStart != bStart) return aStart.compareTo(bStart);

    final int aEnd = int.tryParse(a.verseEnd ?? '') ?? aStart;
    final int bEnd = int.tryParse(b.verseEnd ?? '') ?? bStart;
    return aEnd.compareTo(bEnd);
  }

  static List<int> _chapterParts(String? chapter) {
    if (chapter == null || chapter.isEmpty) return const [];
    return chapter
        .split('.')
        .map((part) => int.tryParse(part.trim()) ?? 0)
        .toList();
  }

  /// Looks up a handful of sections by id (used by the bookmarks list),
  /// together with the main-period and subperiod they belong to.
  Future<List<ContinuousReadingItem>> getSectionsByIds(
    List<int> sectionIds, {
    int languageId = 1,
  }) async {
    if (sectionIds.isEmpty) return [];

    final List<ContinuousReadingItem> allItems = await loadFullContinuousFeed(languageId: languageId);
    final Map<int, ContinuousReadingItem> bySectionId = {
      for (final item in allItems) item.section.id: item,
    };

    return sectionIds
        .map((id) => bySectionId[id])
        .whereType<ContinuousReadingItem>()
        .toList();
  }
}