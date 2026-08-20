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
  final String refDisplay;
  final String transliteration;
  final String translationEn;
  final String translationRu;
  final String translationHi;
  final String sanskritText;

  const VerseDetail({
    required this.verseId,
    required this.refDisplay,
    this.transliteration = '',
    this.translationEn = '',
    this.translationRu = '',
    this.translationHi = '',
    this.sanskritText = '',
  });

  /// Returns the translation for the given language code.
  /// No cross-language fallback for en/ru (shows nothing if unavailable).
  /// Hindi falls back to English.
  String translationForCode(String code) {
    switch (code) {
      case 'hi':
        if (translationHi.isNotEmpty) return translationHi;
        if (translationEn.isNotEmpty) return translationEn;
        return '';
      case 'ru':
        return translationRu;
      default:
        return translationEn;
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
      WHERE p.parent_id = $mainPeriodId AND p.period_type = 'sub'
      ORDER BY p.sort_order ASC;
    ''';

    final List<Map<String, dynamic>> results = await db.rawQuery(query);

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
      return settings.first['setting_value'] as String? ?? 'en';
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
      WHERE s.period_node_id = $periodNodeId
      ORDER BY s.sort_order ASC;
    ''';

    final List<Map<String, dynamic>> results = await db.rawQuery(query);

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
        v.ref_display,
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
        refDisplay: (row['ref_display'] as String?) ?? '',
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
    final String langCode = await _currentLanguageCode();
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

        v.id AS verse_id, v.ref_display, v.transliteration,
        v.translation_en, v.translation_ru, v.translation_hi,
        v.sanskrit_text

      FROM period_nodes pm
      JOIN period_nodes ps ON ps.parent_id = pm.id AND ps.period_type = 'sub'
      JOIN sections sec ON sec.period_node_id = ps.id
      LEFT JOIN verses v ON v.section_id = sec.id
      WHERE pm.period_type = 'main'
      ORDER BY pm.sort_order ASC, ps.sort_order ASC, sec.sort_order ASC, v.sort_order ASC;
    ''';

    final List<Map<String, dynamic>> rows = await db.rawQuery(query);

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
          refDisplay: (row['ref_display'] as String?) ?? '',
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
      WHERE b.id = $bookId
      LIMIT 1;
    ''';

    final List<Map<String, dynamic>> results = await db.rawQuery(query);
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

  /// Looks up sections by id (used by the bookmarks list).
  Future<List<ContinuousReadingItem>> getSectionsByIds(
    List<int> sectionIds,
  ) async {
    if (sectionIds.isEmpty) return [];

    final List<ContinuousReadingItem> allItems = await loadFullContinuousFeed();
    final Map<int, ContinuousReadingItem> bySectionId = {
      for (final item in allItems) item.section.id: item,
    };

    return sectionIds
        .map((id) => bySectionId[id])
        .whereType<ContinuousReadingItem>()
        .toList();
  }
}
