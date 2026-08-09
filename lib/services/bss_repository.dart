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
        COALESCE(t.translated_text, p.code) AS title
      FROM period_nodes p
      LEFT JOIN translations t 
        ON p.name_key = t.translation_key 
       AND t.language_id = ?
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
        COALESCE(t.translated_text, p.code) AS title
      FROM period_nodes p
      LEFT JOIN translations t 
        ON p.name_key = t.translation_key 
       AND t.language_id = ?
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
        COALESCE(t.translated_text, d.description_key) AS description
      FROM dandas d
      LEFT JOIN translations t
        ON d.description_key = t.translation_key
       AND t.language_id = ?
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
        COALESCE(t.translated_text, s.title_key) AS title
      FROM sections s
      LEFT JOIN translations t 
        ON s.title_key = t.translation_key 
       AND t.language_id = ?
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

  Future<List<ContinuousReadingItem>> loadFullContinuousFeed({int languageId = 1}) async {
    final List<LilaPeriod> mainPeriods = await getMainPeriods(languageId: languageId);
    final List<ContinuousReadingItem> items = [];

    int previousMainId = -1;
    int previousSubId = -1;

    for (final main in mainPeriods) {
      final List<SubPeriod> subPeriods = await getSubPeriods(main.id, languageId: languageId);

      for (final sub in subPeriods) {
        final List<LilaSectionItem> sections = await getSectionsForPeriod(sub.id, languageId: languageId);

        for (final sec in sections) {
          final List<VerseDetail> verses = await getVersesForSection(sec.id, languageId: languageId);

          final bool isFirstInMain = (main.id != previousMainId);
          final bool isFirstInSub = (sub.id != previousSubId);

          items.add(ContinuousReadingItem(
            mainPeriod: main,
            subPeriod: sub,
            section: sec,
            verses: verses,
            isFirstInSubPeriod: isFirstInSub,
            isFirstInMainPeriod: isFirstInMain,
          ));

          previousMainId = main.id;
          previousSubId = sub.id;
        }
      }
    }

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
        COALESCE(tt.translated_text, b.slug) AS title,
        COALESCE(ta.translated_text, '') AS author,
        (SELECT COUNT(*) FROM citations c WHERE c.source_book_id = b.id) AS quote_count
      FROM books b
      LEFT JOIN translations tt
        ON tt.translation_key = b.title_key AND tt.language_id = ?
      LEFT JOIN translations ta
        ON ta.translation_key = b.author_key AND ta.language_id = ?
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
        COALESCE(tt.translated_text, b.slug) AS title,
        COALESCE(ta.translated_text, '') AS author
      FROM books b
      LEFT JOIN translations tt
        ON tt.translation_key = b.title_key AND tt.language_id = ?
      LEFT JOIN translations ta
        ON ta.translation_key = b.author_key AND ta.language_id = ?
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