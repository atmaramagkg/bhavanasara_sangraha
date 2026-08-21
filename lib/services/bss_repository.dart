import 'package:sqflite/sqflite.dart';
import '../core/database/language_code.dart';
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
  final String hindiHeading;

  const LilaSectionItem({
    required this.id,
    required this.periodNodeId,
    required this.sortOrder,
    required this.title,
    this.hindiHeading = '',
  });
}

/// A verse displayed in the reading feed. In the new unified schema, this
/// is a row from the `verses` table joined to its section.
class VerseDetail {
  final int verseId;
  final int? bookId;
  final String refDisplay;
  final String sourceRefs;
  final String transliteration;
  final String translationEn;
  final String translationRu;
  final String translationHi;
  final String sanskritText;

  const VerseDetail({
    required this.verseId,
    this.bookId,
    required this.refDisplay,
    this.sourceRefs = '',
    this.transliteration = '',
    this.translationEn = '',
    this.translationRu = '',
    this.translationHi = '',
    this.sanskritText = '',
  });

  /// Returns the translation for the given language code.
  /// Hindi falls back to English; English/Russian fall back to the
  /// transliteration, so a verse whose prose translation isn't in yet
  /// still shows the romanized Sanskrit instead of going blank.
  String translationForCode(String code) {
    switch (code) {
      case 'hi':
        if (translationHi.isNotEmpty) return translationHi;
        if (translationEn.isNotEmpty) return translationEn;
        return transliteration;
      case 'ru':
        if (translationRu.isNotEmpty) return translationRu;
        return transliteration;
      default:
        if (translationEn.isNotEmpty) return translationEn;
        return transliteration;
    }
  }
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

  Future<List<LilaPeriod>> getMainPeriods() async {
    final String langCode = await _currentLanguageCode();
    final query = '''
      SELECT 
        p.id,
        p.code,
        p.name_key,
        p.time_start,
        p.time_end,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = p.name_key),
          (SELECT en FROM translations WHERE translation_key = p.name_key),
          p.code
        ) AS title
      FROM period_nodes p
      WHERE p.period_type = 'main'
      ORDER BY p.sort_order ASC;
    ''';

    final List<Map<String, dynamic>> results = await db.rawQuery(query);

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

  Future<List<SubPeriod>> getSubPeriods(int mainPeriodId) async {
    final String langCode = await _currentLanguageCode();
    final query = '''
      SELECT 
        p.id,
        p.parent_id,
        p.code,
        p.time_start,
        p.time_end,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = p.name_key),
          (SELECT en FROM translations WHERE translation_key = p.name_key),
          p.code
        ) AS title
      FROM period_nodes p
      WHERE p.parent_id = ? AND p.period_type = 'sub'
      ORDER BY p.sort_order ASC;
    ''';

    final List<Map<String, dynamic>> results =
        await db.rawQuery(query, [mainPeriodId]);

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

  Future<List<Danda>> getDandas() async {
    final String langCode = await _currentLanguageCode();
    final query = '''
      SELECT
        d.id,
        d.main_period_id,
        d.sort_order,
        d.time_start,
        d.time_end,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = d.description_key),
          (SELECT en FROM translations WHERE translation_key = d.description_key),
          d.description_key
        ) AS description
      FROM dandas d
      ORDER BY d.sort_order ASC;
    ''';

    final List<Map<String, dynamic>> results = await db.rawQuery(query);

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

  Future<String> _currentLanguageCode() async {
    final List<Map<String, dynamic>> settings = await db.rawQuery(
      "SELECT setting_value FROM app_settings WHERE setting_key = 'selected_language_code'",
    );
    if (settings.isNotEmpty) {
      return sanitizeLanguageCode(settings.first['setting_value'] as String?);
    }
    return 'en';
  }

  Future<List<LilaSectionItem>> getSectionsForPeriod(int periodNodeId) async {
    final String langCode = await _currentLanguageCode();
    final query = '''
      SELECT 
        s.id,
        s.period_node_id,
        s.sort_order,
        s.hindi_heading,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = s.title_key),
          (SELECT en FROM translations WHERE translation_key = s.title_key),
          s.title_key
        ) AS title
      FROM sections s
      WHERE s.period_node_id = ?
      ORDER BY s.sort_order ASC;
    ''';

    final List<Map<String, dynamic>> results =
        await db.rawQuery(query, [periodNodeId]);

    return results.map<LilaSectionItem>((row) {
      return LilaSectionItem(
        id: (row['id'] as int?) ?? 0,
        periodNodeId: (row['period_node_id'] as int?) ?? 0,
        sortOrder: (row['sort_order'] as int?) ?? 0,
        title: (row['title'] as String?) ?? '',
        hindiHeading: (row['hindi_heading'] as String?) ?? '',
      );
    }).toList();
  }

  Future<List<VerseDetail>> getVersesForSection(int sectionId) async {
    const query = '''
      SELECT 
        v.id AS verse_id,
        v.book_id,
        v.ref_display,
        v.source_refs,
        v.transliteration,
        v.translation_en,
        v.translation_ru,
        v.translation_hi,
        v.sanskrit_text
      FROM verses v
      WHERE v.section_id = ?
      ORDER BY v.sort_order ASC;
    ''';

    final List<Map<String, dynamic>> results = await db.rawQuery(query, [sectionId]);

    return results.map<VerseDetail>((row) {
      return VerseDetail(
        verseId: (row['verse_id'] as int?) ?? 0,
        bookId: row['book_id'] as int?,
        refDisplay: (row['ref_display'] as String?) ?? '',
        sourceRefs: (row['source_refs'] as String?) ?? '',
        transliteration: (row['transliteration'] as String?) ?? '',
        translationEn: (row['translation_en'] as String?) ?? '',
        translationRu: (row['translation_ru'] as String?) ?? '',
        translationHi: (row['translation_hi'] as String?) ?? '',
        sanskritText: (row['sanskrit_text'] as String?) ?? '',
      );
    }).toList();
  }

  /// Builds the entire continuous reading feed in a single JOIN query.
  /// New schema: period_nodes -> sections -> verses (no more quotes/citations).
  Future<List<ContinuousReadingItem>> loadFullContinuousFeed() async {
    final List<Map<String, dynamic>> rows = await _queryContinuousFeedRows();
    return _parseContinuousFeedRows(rows);
  }

  /// The shared JOIN behind [loadFullContinuousFeed] and [getSectionsByIds].
  /// When [sectionIds] is given, the query is scoped to just those sections
  /// via `WHERE sec.id IN (...)` instead of walking every section in the book.
  Future<List<Map<String, dynamic>>> _queryContinuousFeedRows({
    List<int>? sectionIds,
  }) async {
    final String langCode = await _currentLanguageCode();

    final String sectionFilter = (sectionIds != null && sectionIds.isNotEmpty)
        ? 'AND sec.id IN (${List.filled(sectionIds.length, '?').join(', ')})'
        : '';

    final query = '''
      SELECT
        pm.id AS main_id, pm.code AS main_code, pm.name_key AS main_name_key,
        pm.time_start AS main_time_start, pm.time_end AS main_time_end,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = pm.name_key),
          (SELECT en FROM translations WHERE translation_key = pm.name_key),
          pm.code
        ) AS main_title,

        ps.id AS sub_id, ps.parent_id AS sub_parent_id, ps.code AS sub_code,
        ps.time_start AS sub_time_start, ps.time_end AS sub_time_end,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = ps.name_key),
          (SELECT en FROM translations WHERE translation_key = ps.name_key),
          ps.code
        ) AS sub_title,

        sec.id AS section_id, sec.period_node_id AS section_period_node_id,
        sec.sort_order AS section_sort_order, sec.hindi_heading AS section_hindi_heading,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = sec.title_key),
          (SELECT en FROM translations WHERE translation_key = sec.title_key),
          sec.title_key
        ) AS section_title,

        v.id AS verse_id, v.book_id, v.ref_display, v.source_refs, v.transliteration,
        v.translation_en, v.translation_ru, v.translation_hi,
        v.sanskrit_text

      FROM period_nodes pm
      JOIN period_nodes ps ON ps.parent_id = pm.id AND ps.period_type = 'sub'
      JOIN sections sec ON sec.period_node_id = ps.id
      LEFT JOIN verses v ON v.section_id = sec.id
      WHERE pm.period_type = 'main' $sectionFilter
      ORDER BY pm.sort_order ASC, ps.sort_order ASC, sec.sort_order ASC, v.sort_order ASC;
    ''';

    return db.rawQuery(query, sectionIds ?? const []);
  }

  /// Groups the flat JOIN rows from [_queryContinuousFeedRows] back into
  /// one [ContinuousReadingItem] per section.
  List<ContinuousReadingItem> _parseContinuousFeedRows(
    List<Map<String, dynamic>> rows,
  ) {
    final List<ContinuousReadingItem> items = [];

    int previousMainId = -1;
    int previousSubId = -1;

    LilaPeriod? currentMain;
    SubPeriod? currentSub;
    LilaSectionItem? currentSection;
    List<VerseDetail> currentVerses = [];
    int currentSectionId = -1;

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
          hindiHeading: (row['section_hindi_heading'] as String?) ?? '',
        );

        currentVerses = [];
        currentSectionId = sectionId;
      }

      // Sections with zero verses still produce one row (LEFT JOIN verses),
      // with verse_id NULL -- skip adding a verse for those.
      final int? verseId = row['verse_id'] as int?;
      if (verseId != null) {
        currentVerses.add(VerseDetail(
          verseId: verseId,
          bookId: row['book_id'] as int?,
          refDisplay: (row['ref_display'] as String?) ?? '',
          sourceRefs: (row['source_refs'] as String?) ?? '',
          transliteration: (row['transliteration'] as String?) ?? '',
          translationEn: (row['translation_en'] as String?) ?? '',
          translationRu: (row['translation_ru'] as String?) ?? '',
          translationHi: (row['translation_hi'] as String?) ?? '',
          sanskritText: (row['sanskrit_text'] as String?) ?? '',
        ));
      }
    }

    flushCurrentSection();

    return items;
  }

  /// The id of whichever main period the current device time falls in,
  /// or null if the lookup fails.
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

  /// The main + sub period pair the current device time falls in.
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

  static String _toHm(DateTime t) =>
      '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

  static bool _timeInRange(String nowHm, String start, String end) {
    if (start.isEmpty || end.isEmpty) return false;
    return start.compareTo(end) <= 0
        ? nowHm.compareTo(start) >= 0 && nowHm.compareTo(end) < 0
        : nowHm.compareTo(start) >= 0 || nowHm.compareTo(end) < 0;
  }

  /// All source scriptures, with how many verses cite each one.
  Future<List<Book>> getAllBooks() async {
    final String langCode = await _currentLanguageCode();
    final query = '''
      SELECT
        b.id,
        b.slug,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = b.title_key),
          (SELECT en FROM translations WHERE translation_key = b.title_key),
          b.slug
        ) AS title,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = b.author_key),
          (SELECT en FROM translations WHERE translation_key = b.author_key),
          ''
        ) AS author,
        (SELECT COUNT(*) FROM verses v WHERE v.book_id = b.id) AS verse_count
      FROM books b
      WHERE (SELECT COUNT(*) FROM verses v WHERE v.book_id = b.id) > 0
      ORDER BY title ASC;
    ''';

    final List<Map<String, dynamic>> results = await db.rawQuery(query);

    return results.map((row) {
      return Book(
        id: (row['id'] as int?) ?? 0,
        slug: (row['slug'] as String?) ?? '',
        title: (row['title'] as String?) ?? '',
        author: (row['author'] as String?) ?? '',
        quoteCount: (row['verse_count'] as int?) ?? 0,
      );
    }).toList();
  }

  /// A single book's title.
  Future<Book?> getBookById(int bookId) async {
    final String langCode = await _currentLanguageCode();
    final query = '''
      SELECT
        b.id,
        b.slug,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = b.title_key),
          (SELECT en FROM translations WHERE translation_key = b.title_key),
          b.slug
        ) AS title,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = b.author_key),
          (SELECT en FROM translations WHERE translation_key = b.author_key),
          ''
        ) AS author
      FROM books b
      WHERE b.id = ?
      LIMIT 1;
    ''';

    final List<Map<String, dynamic>> results = await db.rawQuery(query, [bookId]);
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

  Future<Book?> getBookBySlug(String slug) async {
    final String langCode = await _currentLanguageCode();
    final query = '''
      SELECT
        b.id,
        b.slug,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = b.title_key),
          (SELECT en FROM translations WHERE translation_key = b.title_key),
          b.slug
        ) AS title,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = b.author_key),
          (SELECT en FROM translations WHERE translation_key = b.author_key),
          ''
        ) AS author
      FROM books b
      WHERE b.slug = ?
      LIMIT 1;
    ''';
    final List<Map<String, dynamic>> results = await db.rawQuery(query, [slug]);
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

  /// All verses of a book from the unified `verses` table.
  Future<List<Verse>> getVersesForBook(int bookId) async {
    final List<Map<String, dynamic>> rows = await db.query(
      'verses',
      where: 'book_id = ?',
      whereArgs: [bookId],
      orderBy: 'sort_order ASC',
    );

    return rows.map(Verse.fromMap).toList();
  }

  /// The full record of one verse.
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

  /// Finds a verse by book slug and verse ref (e.g. 'govinda-lilamrta' + '1.107').
  /// Returns the verse ID or null if not found.
  Future<int?> getVerseIdByBookAndRef(String slug, String verseRef) async {
    final bookRows = await db.query('books', where: 'slug = ?', whereArgs: [slug], limit: 1);
    if (bookRows.isEmpty) return null;
    final bookId = bookRows.first['id'] as int;
    final rows = await db.query(
      'verses',
      where: 'book_id = ? AND ref_display LIKE ?',
      whereArgs: [bookId, '%$verseRef%'],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    return rows.first['id'] as int;
  }

  /// Looks up sections by id (used by the bookmarks list).
  /// Queries just the requested sections directly, rather than building the
  /// full continuous feed (every period/section/verse) and discarding the
  /// rest — the bookmarks list only ever needs a handful of sections out of
  /// the whole book.
  Future<List<ContinuousReadingItem>> getSectionsByIds(
    List<int> sectionIds,
  ) async {
    if (sectionIds.isEmpty) return [];

    final List<Map<String, dynamic>> rows =
        await _queryContinuousFeedRows(sectionIds: sectionIds);
    final List<ContinuousReadingItem> items = _parseContinuousFeedRows(rows);

    final Map<int, ContinuousReadingItem> bySectionId = {
      for (final item in items) item.section.id: item,
    };

    return sectionIds
        .map((id) => bySectionId[id])
        .whereType<ContinuousReadingItem>()
        .toList();
  }
}
