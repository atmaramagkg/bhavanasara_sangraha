import 'dart:io';

import 'package:flutter/services.dart' show rootBundle;
import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

/// Every user-visible word comes from the `translations` table
/// inside the bundled database. Nothing is hardcoded here.
class AppDatabase {
  AppDatabase._();

  static final AppDatabase instance = AppDatabase._();

  /// Pre-built database shipped inside the app assets.
  static const String _assetPath =
      'assets/db/Bhavanasara-Sangraha_En.sqlite';

  Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    await init();
    return _db!;
  }

  /// Copies the bundled database to a writable location on first launch.
  Future<void> init() async {
    if (_db != null) return;

    final String path = join(
      await getDatabasesPath(),
      'bhavanasara.db',
    );

    if (!await databaseExists(path)) {
      await Directory(dirname(path)).create(recursive: true);

      final data = await rootBundle.load(_assetPath);
      final bytes =
          data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes);
      await File(path).writeAsBytes(bytes, flush: true);
    }

    _db = await openDatabase(path);
    await _db!.execute('PRAGMA foreign_keys = ON');
  }

  // ------------------------------------------------------------------
  // Language helpers (words come from the DB, not from code)
  // ------------------------------------------------------------------

  Future<int> getCurrentLanguageId() async {
    final Database db = await database;

    String code = 'en';

    final List<Map<String, Object?>> setting = await db.rawQuery(
      "SELECT setting_value FROM app_settings "
      "WHERE setting_key = ?",
      ['selected_language_code'],
    );
    if (setting.isNotEmpty) {
      code = setting.first['setting_value'] as String? ?? 'en';
    }

    final List<Map<String, Object?>> lang = await db.rawQuery(
      'SELECT id FROM languages WHERE code = ?',
      [code],
    );
    if (lang.isNotEmpty) return lang.first['id'] as int;

    return 1;
  }

  /// Translates a key: selected language -> English -> the key itself.
  Future<String> translate(String key) async {
    final Database db = await database;
    final int langId = await getCurrentLanguageId();

    final List<Map<String, Object?>> rows = await db.rawQuery(
      '''
      SELECT COALESCE(
        (SELECT translated_text FROM translations
          WHERE translation_key = ? AND language_id = ?),
        (SELECT translated_text FROM translations
          WHERE translation_key = ?
            AND language_id = (SELECT id FROM languages WHERE code = 'en')),
        ?
      ) AS text
      ''',
      [key, langId, key, key],
    );

    return rows.first['text'] as String? ?? key;
  }

  // ------------------------------------------------------------------
  // Queries (names resolved from translations, never hardcoded)
  // ------------------------------------------------------------------

  Future<List<Map<String, dynamic>>> getMainPeriods() async {
    final Database db = await database;
    final int langId = await getCurrentLanguageId();

    final List<Map<String, Object?>> rows = await db.rawQuery(
      '''
      SELECT
        pn.id,
        pn.code,
        pn.time_start,
        pn.time_end,
        pn.sort_order,
        COALESCE(
          (SELECT translated_text FROM translations
            WHERE translation_key = pn.name_key AND language_id = ?),
          (SELECT translated_text FROM translations
            WHERE translation_key = pn.name_key
              AND language_id = (SELECT id FROM languages WHERE code = 'en')),
          pn.code
        ) AS name
      FROM period_nodes pn
      WHERE pn.parent_id IS NULL
      ORDER BY pn.sort_order ASC
      ''',
      [langId],
    );

    return rows.map((row) => Map<String, dynamic>.from(row)).toList();
  }

  Future<List<Map<String, dynamic>>> getSubPeriods(int parentId) async {
    final Database db = await database;
    final int langId = await getCurrentLanguageId();

    final List<Map<String, Object?>> rows = await db.rawQuery(
      '''
      SELECT
        pn.id,
        pn.code,
        pn.time_start,
        pn.time_end,
        pn.sort_order,
        COALESCE(
          (SELECT translated_text FROM translations
            WHERE translation_key = pn.name_key AND language_id = ?),
          (SELECT translated_text FROM translations
            WHERE translation_key = pn.name_key
              AND language_id = (SELECT id FROM languages WHERE code = 'en')),
          pn.code
        ) AS name
      FROM period_nodes pn
      WHERE pn.parent_id = ?
      ORDER BY pn.sort_order ASC
      ''',
      [langId, parentId],
    );

    return rows.map((row) => Map<String, dynamic>.from(row)).toList();
  }

  Future<List<Map<String, dynamic>>> getSections(int subPeriodId) async {
    final Database db = await database;
    final int langId = await getCurrentLanguageId();

    final List<Map<String, Object?>> rows = await db.rawQuery(
      '''
      SELECT
        s.id,
        s.sort_order,
        COALESCE(
          (SELECT translated_text FROM translations
            WHERE translation_key = s.title_key AND language_id = ?),
          (SELECT translated_text FROM translations
            WHERE translation_key = s.title_key
              AND language_id = (SELECT id FROM languages WHERE code = 'en')),
          s.title_key
        ) AS title
      FROM sections s
      WHERE s.period_node_id = ?
      ORDER BY s.sort_order ASC
      ''',
      [langId, subPeriodId],
    );

    return rows.map((row) => Map<String, dynamic>.from(row)).toList();
  }

  Future<List<Map<String, dynamic>>> getBooks() async {
    final Database db = await database;
    final int langId = await getCurrentLanguageId();

    final List<Map<String, Object?>> rows = await db.rawQuery(
      '''
      SELECT
        b.id,
        b.slug,
        COALESCE(
          (SELECT translated_text FROM translations
            WHERE translation_key = b.title_key AND language_id = ?),
          (SELECT translated_text FROM translations
            WHERE translation_key = b.title_key
              AND language_id = (SELECT id FROM languages WHERE code = 'en')),
          b.slug
        ) AS title,
        COALESCE(
          (SELECT translated_text FROM translations
            WHERE translation_key = b.author_key AND language_id = ?),
          (SELECT translated_text FROM translations
            WHERE translation_key = b.author_key
              AND language_id = (SELECT id FROM languages WHERE code = 'en')),
          b.author_key
        ) AS author
      FROM books b
      ORDER BY b.id ASC
      ''',
      [langId, langId],
    );

    return rows.map((row) => Map<String, dynamic>.from(row)).toList();
  }

  Future<void> close() async {
    await _db?.close();
    _db = null;
  }
}