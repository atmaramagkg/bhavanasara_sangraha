import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:sqflite/sqflite.dart';

import '../core/database/app_database.dart';

/// Reads the CSV seed files from assets/csv/ and imports them
/// into the SQLite database.
///
/// This service does NOT depend on any external CSV package -
/// it contains its own small, robust CSV parser.
class CsvImportService {
  /// All CSV files and the tables they fill, in the correct order
  /// (parent tables first, because of foreign keys).
  static const List<Map<String, String>> _files = [
    {'asset': 'assets/csv/languages.csv', 'table': 'languages'},
    {'asset': 'assets/csv/books.csv', 'table': 'books'},
    {'asset': 'assets/csv/book_aliases.csv', 'table': 'book_aliases'},
    {'asset': 'assets/csv/translations.csv', 'table': 'translations'},
    {'asset': 'assets/csv/period_schemes.csv', 'table': 'period_schemes'},
    {'asset': 'assets/csv/period_nodes.csv', 'table': 'period_nodes'},
    {'asset': 'assets/csv/sections.csv', 'table': 'sections'},
    {'asset': 'assets/csv/verses.csv', 'table': 'verses'},
    {'asset': 'assets/csv/compiled_sections.csv', 'table': 'compiled_sections'},
    {'asset': 'assets/csv/quotes.csv', 'table': 'quotes'},
    {'asset': 'assets/csv/citations.csv', 'table': 'citations'},
  ];

  /// Imports every CSV file that exists.
  /// Tables that already contain data are skipped (unless [force] is true),
  /// so it is safe to call this on every app start.
  static Future<void> importAll({bool force = false}) async {
    final Database db = await AppDatabase.instance.database;

    for (final Map<String, String> file in _files) {
      await _importFile(
        db,
        file['asset']!,
        file['table']!,
        force: force,
      );
    }
  }

  /// Convenience wrapper - import only empty tables.
  static Future<void> importIfEmpty() => importAll(force: false);

  /// Re-import everything, overwriting existing rows.
  static Future<void> reimportAll() => importAll(force: true);

  // ------------------------------------------------------------------
  // Internal helpers
  // ------------------------------------------------------------------

  static Future<void> _importFile(
    Database db,
    String asset,
    String table, {
    bool force = false,
  }) async {
    try {
      // Skip tables that already have data (unless forced).
      if (!force) {
        final int count = await _tableCount(db, table);
        if (count < 0) return; // table does not exist in this schema
        if (count > 0) {
          debugPrint('CsvImport: "$table" already has data - skipped.');
          return;
        }
      }

      final String raw = await rootBundle.loadString(asset);
      final List<List<String>> rows = _parseCsv(raw);
      if (rows.length < 2) {
        debugPrint('CsvImport: "$asset" is empty.');
        return;
      }

      final List<String> headers = rows.first;
      final Batch batch = db.batch();

      for (int i = 1; i < rows.length; i++) {
        final List<String> line = rows[i];
        if (line.isEmpty ||
            (line.length == 1 && line[0].trim().isEmpty)) {
          continue;
        }

        final Map<String, Object?> map = <String, Object?>{};
        for (int c = 0; c < headers.length; c++) {
          final String value = c < line.length ? line[c] : '';
          map[headers[c].trim()] = _normalize(value);
        }

        batch.insert(
          table,
          map,
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }

      await batch.commit(noResult: true);
      debugPrint('CsvImport: imported ${rows.length - 1} rows into "$table".');
    } catch (e) {
      // Missing asset file or missing table - not fatal, just report it.
      debugPrint('CsvImport: skipped $asset -> $e');
    }
  }

  /// Returns row count of a table, or -1 if the table does not exist.
  static Future<int> _tableCount(Database db, String table) async {
    final List<Map<String, Object?>> check = await db.rawQuery(
      "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
      [table],
    );
    if (check.isEmpty) return -1;

    final List<Map<String, Object?>> result =
        await db.rawQuery('SELECT COUNT(*) AS c FROM $table');
    final Object? value = result.first['c'];
    if (value is int) return value;
    return int.tryParse(value?.toString() ?? '0') ?? 0;
  }

  /// Empty string -> null, whole numbers -> int, everything else -> String.
  static Object? _normalize(String value) {
    final String v = value.trim();
    if (v.isEmpty) return null;
    final int? asInt = int.tryParse(v);
    if (asInt != null) return asInt;
    return v;
  }

  // ------------------------------------------------------------------
  // Small CSV parser (supports quotes, commas and line breaks in fields)
  // ------------------------------------------------------------------

  static List<List<String>> _parseCsv(String input) {
    final List<List<String>> rows = <List<String>>[];
    List<String> row = <String>[];
    final StringBuffer field = StringBuffer();
    bool inQuotes = false;

    // Remove BOM if present.
    if (input.isNotEmpty && input.codeUnitAt(0) == 0xFEFF) {
      input = input.substring(1);
    }

    for (int i = 0; i < input.length; i++) {
      final String ch = input[i];

      if (inQuotes) {
        if (ch == '"') {
          if (i + 1 < input.length && input[i + 1] == '"') {
            field.write('"'); // escaped quote ""
            i++;
          } else {
            inQuotes = false;
          }
        } else {
          field.write(ch);
        }
      } else {
        if (ch == '"') {
          inQuotes = true;
        } else if (ch == ',') {
          row.add(field.toString());
          field.clear();
        } else if (ch == '\n' || ch == '\r') {
          if (ch == '\r' && i + 1 < input.length && input[i + 1] == '\n') {
            i++; // treat \r\n as one line break
          }
          row.add(field.toString());
          field.clear();
          if (row.any((String cell) => cell.trim().isNotEmpty)) {
            rows.add(row);
          }
          row = <String>[];
        } else {
          field.write(ch);
        }
      }
    }

    // Last field / row when the file does not end with a newline.
    row.add(field.toString());
    if (row.any((String cell) => cell.trim().isNotEmpty)) {
      rows.add(row);
    }

    return rows;
  }
}