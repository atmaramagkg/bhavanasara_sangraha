import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

/// A language available in the app, read from the single unified database.
class AvailableLanguage {
  final String code;
  final String name;

  const AvailableLanguage({required this.code, required this.name});
}

/// Every user-visible word comes from the `translations` table
/// inside the bundled unified database. Nothing is hardcoded here.
class AppDatabase {
  AppDatabase._();

  static final AppDatabase instance = AppDatabase._();

  static const String _assetPath =
      'assets/db/Bhavanasara-Sangraha.sqlite';
  static const String _dbFileName = 'bhavanasara_unified.db';

  Database? _db;

  /// Languages available in the unified database.
  static Future<List<AvailableLanguage>> availableLanguages() async {
    final Database db = await instance.database;
    final List<Map<String, Object?>> rows = await db.query(
      'languages',
      columns: ['code', 'name'],
      orderBy: 'code ASC',
    );
    return rows
        .map((r) => AvailableLanguage(
              code: r['code'] as String,
              name: r['name'] as String,
            ))
        .toList();
  }

  Future<Database> get database async {
    if (_db != null) return _db!;
    await init();
    return _db!;
  }

  /// Copies the bundled unified database to a writable location, refreshing
  /// it whenever the bundled asset changes.
  Future<void> init() async {
    if (_db != null) return;

    final String path = join(await getDatabasesPath(), _dbFileName);

    final ByteData data = await rootBundle.load(_assetPath);
    final bytes =
        data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes);

    final File file = File(path);
    final bool needsWrite =
        !await file.exists() || !listEquals(await file.readAsBytes(), bytes);
    if (needsWrite) {
      await Directory(dirname(path)).create(recursive: true);
      await file.writeAsBytes(bytes, flush: true);
    }

    _db = await openDatabase(path);
    await _db!.execute('PRAGMA foreign_keys = ON');
  }

  /// Returns the language code currently selected (from app_settings),
  /// defaulting to 'en'.
  Future<String> getCurrentLanguageCode() async {
    final Database db = await database;
    final List<Map<String, Object?>> rows = await db.rawQuery(
      "SELECT setting_value FROM app_settings WHERE setting_key = 'selected_language_code'",
    );
    if (rows.isNotEmpty) {
      return rows.first['setting_value'] as String? ?? 'en';
    }
    return 'en';
  }

  /// Persists the selected language code.
  Future<void> setCurrentLanguageCode(String code) async {
    final Database db = await database;
    await db.insert(
      'app_settings',
      {'setting_key': 'selected_language_code', 'setting_value': code},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  // ------------------------------------------------------------------
  // Translation helpers — new schema: translations table has en/ru/hi columns
  // ------------------------------------------------------------------

  /// Translates a key using COALESCE: current language -> English -> the key itself.
  Future<String> translate(String key) async {
    final String langCode = await getCurrentLanguageCode();
    final Database db = await database;

    final List<Map<String, Object?>> rows = await db.rawQuery(
      '''
      SELECT COALESCE(
        (SELECT $langCode FROM translations WHERE translation_key = ?),
        (SELECT en FROM translations WHERE translation_key = ?),
        ?
      ) AS text
      ''',
      [key, key, key],
    );

    return rows.first['text'] as String? ?? key;
  }

  /// Loads every translation into a lookup map for the current language,
  /// using the new column-based schema: COALESCE(current_lang, en, key).
  Future<Map<String, String>> loadTranslations() async {
    final String langCode = await getCurrentLanguageCode();
    final Database db = await database;

    final List<Map<String, Object?>> rows = await db.rawQuery(
      '''
      SELECT translation_key AS key,
        COALESCE(
          $langCode,
          en,
          translation_key
        ) AS text
      FROM translations
      ''',
    );

    return {
      for (final Map<String, Object?> row in rows)
        row['key'] as String: (row['text'] as String? ?? row['key']) as String,
    };
  }

  // ------------------------------------------------------------------
  // Queries (names resolved from translations, never hardcoded)
  // ------------------------------------------------------------------

  Future<List<Map<String, dynamic>>> getMainPeriods() async {
    final String langCode = await getCurrentLanguageCode();
    final Database db = await database;

    final List<Map<String, Object?>> rows = await db.rawQuery(
      '''
      SELECT
        pn.id,
        pn.code,
        pn.time_start,
        pn.time_end,
        pn.sort_order,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = pn.name_key),
          (SELECT en FROM translations WHERE translation_key = pn.name_key),
          pn.code
        ) AS name
      FROM period_nodes pn
      WHERE pn.parent_id IS NULL
      ORDER BY pn.sort_order ASC
      ''',
    );

    return rows.map((row) => Map<String, dynamic>.from(row)).toList();
  }

  Future<List<Map<String, dynamic>>> getSubPeriods(int parentId) async {
    final String langCode = await getCurrentLanguageCode();
    final Database db = await database;

    final List<Map<String, Object?>> rows = await db.rawQuery(
      '''
      SELECT
        pn.id,
        pn.code,
        pn.time_start,
        pn.time_end,
        pn.sort_order,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = pn.name_key),
          (SELECT en FROM translations WHERE translation_key = pn.name_key),
          pn.code
        ) AS name
      FROM period_nodes pn
      WHERE pn.parent_id = ?
      ORDER BY pn.sort_order ASC
      ''',
      [parentId],
    );

    return rows.map((row) => Map<String, dynamic>.from(row)).toList();
  }

  Future<List<Map<String, dynamic>>> getSections(int subPeriodId) async {
    final String langCode = await getCurrentLanguageCode();
    final Database db = await database;

    final List<Map<String, Object?>> rows = await db.rawQuery(
      '''
      SELECT
        s.id,
        s.sort_order,
        COALESCE(
          (SELECT $langCode FROM translations WHERE translation_key = s.title_key),
          (SELECT en FROM translations WHERE translation_key = s.title_key),
          s.title_key
        ) AS title
      FROM sections s
      WHERE s.period_node_id = ?
      ORDER BY s.sort_order ASC
      ''',
      [subPeriodId],
    );

    return rows.map((row) => Map<String, dynamic>.from(row)).toList();
  }

  Future<List<Map<String, dynamic>>> getBooks() async {
    final String langCode = await getCurrentLanguageCode();
    final Database db = await database;

    final List<Map<String, Object?>> rows = await db.rawQuery(
      '''
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
          b.author_key
        ) AS author
      FROM books b
      ORDER BY b.id ASC
      ''',
    );

    return rows.map((row) => Map<String, dynamic>.from(row)).toList();
  }

  Future<void> close() async {
    await _db?.close();
    _db = null;
  }
}
