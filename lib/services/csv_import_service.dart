import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:sqflite/sqflite.dart';

import '../core/database/app_database.dart';

class CsvImportService {
  /// Main import method.
  static Future<void> importAll() async {
    final db = await AppDatabase.instance.database;

    // Temporarily disable foreign keys while importing.
    await db.execute('PRAGMA foreign_keys = OFF;');

    try {
      await _importFile(
        db,
        'assets/csv/books.csv',
        'books',
        ['id', 'slug', 'title', 'author', 'notes'],
      );

      await _importFile(
        db,
        'assets/csv/book_aliases.csv',
        'book_aliases',
        ['id', 'book_id', 'alias'],
      );

      await _importFile(
        db,
        'assets/csv/period_schemes.csv',
        'period_schemes',
        ['id', 'name'],
      );

      await _importFile(
        db,
        'assets/csv/period_nodes.csv',
        'period_nodes',
        [
          'id',
          'scheme_id',
          'parent_id',
          'code',
          'name',
          'time_start',
          'time_end',
          'sort_order',
        ],
      );

      await _importFile(
        db,
        'assets/csv/verses.csv',
        'verses',
        [
          'id',
          'book_id',
          'division_1',
          'division_2',
          'chapter',
          'section',
          'verse_start',
          'verse_end',
          'ref_display',
          'original_text',
          'translation_text',
          'commentary_text',
          'sort_order',
        ],
      );

      await _importFile(
        db,
        'assets/csv/compiled_sections.csv',
        'compiled_sections',
        [
          'id',
          'chapter_title',
          'section_title',
          'main_period_id',
          'subperiod_id',
          'sort_order',
        ],
      );

      await _importFile(
        db,
        'assets/csv/quotes.csv',
        'quotes',
        [
          'id',
          'compiled_section_id',
          'quote_type',
          'quote_text',
          'sort_order',
        ],
      );

      await _importFile(
        db,
        'assets/csv/citations.csv',
        'citations',
        [
          'id',
          'quote_id',
          'source_book_id',
          'source_verse_id',
          'ref_display',
          'confidence',
          'notes',
        ],
      );

      debugPrint('CSV import finished successfully.');
    } catch (e, stack) {
      debugPrint('CSV import error: $e');
      debugPrint(stack.toString());
    } finally {
      // Enable foreign keys again.
      await db.execute('PRAGMA foreign_keys = ON;');
    }
  }

  /// Optional aliases in case your main.dart uses another name.
  static Future<void> importAllIfEmpty() => importAll();
  static Future<void> importIfEmpty() => importAll();

  static Future<void> _importFile(
    Database db,
    String path,
    String tableName,
    List<String> columns,
  ) async {
    final rows = await _loadCsv(path);

    if (rows == null || rows.length < 2) {
      debugPrint('No CSV data found in: $path');
      return;
    }

    final batch = db.batch();

    // Start from 1 because row 0 is the header.
    for (var i = 1; i < rows.length; i++) {
      final row = rows[i];

      // Skip completely empty rows.
      if (row.every((cell) => cell.trim().isEmpty)) {
        continue;
      }

      final map = <String, Object?>{};

      for (var j = 0; j < columns.length; j++) {
        final value = j < row.length ? row[j] : '';
        map[columns[j]] = _normalize(value);
      }

      batch.insert(
        tableName,
        map,
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }

    await batch.commit(noResult: true);

    debugPrint('Imported ${rows.length - 1} rows into $tableName from $path');
  }

  static Future<List<List<String>>?> _loadCsv(String path) async {
    try {
      final raw = await rootBundle.loadString(path);
      return _parseCsv(raw);
    } catch (e) {
      debugPrint('Could not load CSV file: $path');
      debugPrint(e.toString());
      return null;
    }
  }

  /// Simple CSV parser.
  ///
  /// Supports:
  /// - commas inside quoted fields
  /// - double quotes escaped as ""
  /// - newlines inside quoted fields
  /// - Windows line endings \r\n
  static List<List<String>> _parseCsv(String input) {
    final rows = <List<String>>[];
    var row = <String>[];
    var field = StringBuffer();
    var inQuotes = false;

    // Remove BOM if present.
    if (input.isNotEmpty && input.codeUnitAt(0) == 0xFEFF) {
      input = input.substring(1);
    }

    for (var i = 0; i < input.length; i++) {
      final char = input[i];

      if (inQuotes) {
        if (char == '"') {
          // Escaped quote: ""
          if (i + 1 < input.length && input[i + 1] == '"') {
            field.write('"');
            i++;
          } else {
            inQuotes = false;
          }
        } else {
          field.write(char);
        }
      } else {
        if (char == '"') {
          inQuotes = true;
        } else if (char == ',') {
          row.add(field.toString());
          field.clear();
        } else if (char == '\n') {
          row.add(field.toString());
          field.clear();

          if (row.any((cell) => cell.trim().isNotEmpty)) {
            rows.add(row);
          }

          row = [];
        } else if (char == '\r') {
          // Ignore carriage return.
          continue;
        } else {
          field.write(char);
        }
      }
    }

    // Add last field/row if file does not end with newline.
    row.add(field.toString());

    if (row.any((cell) => cell.trim().isNotEmpty)) {
      rows.add(row);
    }

    return rows;
  }

  static Object? _normalize(String value) {
    final trimmed = value.trim();

    if (trimmed.isEmpty) {
      return null;
    }

    if (trimmed.toLowerCase() == 'null') {
      return null;
    }

    final asInt = int.tryParse(trimmed);

    if (asInt != null) {
      return asInt;
    }

    return trimmed;
  }
}