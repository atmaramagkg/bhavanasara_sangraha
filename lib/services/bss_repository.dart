import 'package:sqflite/sqflite.dart';
import '../models/lila_period.dart';

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

  const VerseDetail({
    required this.quoteId,
    required this.quoteText,
    required this.refDisplay,
    required this.bookTitle,
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
    final String nowHm =
        '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

    for (final row in results) {
      final String start = (row['time_start'] as String?) ?? '';
      final String end = (row['time_end'] as String?) ?? '';
      if (start.isEmpty || end.isEmpty) continue;

      final bool within = start.compareTo(end) <= 0
          ? nowHm.compareTo(start) >= 0 && nowHm.compareTo(end) < 0
          // period wraps past midnight (e.g. Niśa: 22:48 -> 03:36)
          : nowHm.compareTo(start) >= 0 || nowHm.compareTo(end) < 0;

      if (within) return row['id'] as int?;
    }
    return results.first['id'] as int?;
  }
}