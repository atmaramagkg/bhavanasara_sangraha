// services/db_service.dart
import 'package:sqflite/sqflite.dart';
import '../models/lila_period.dart';

class BssDatabaseService {
  final Database db;

  BssDatabaseService(this.db);

  Future<List<LilaPeriod>> getMainPeriods({int languageId = 1}) async {
    final String query = '''
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

    return results.map((row) {
      final start = row['time_start'] ?? '';
      final end = row['time_end'] ?? '';
      final timeDisplay = (start.isNotEmpty && end.isNotEmpty) ? '$start - $end' : '';

      return LilaPeriod(
        id: row['id'] as int,
        code: row['code'] as String,
        nameKey: row['name_key'] as String,
        title: row['title'] as String,
        timeRange: timeDisplay,
      );
    }).toList();
  }
}