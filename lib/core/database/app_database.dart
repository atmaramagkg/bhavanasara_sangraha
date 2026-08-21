import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

import 'language_code.dart';

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
      return sanitizeLanguageCode(rows.first['setting_value'] as String?);
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

  Future<void> close() async {
    await _db?.close();
    _db = null;
  }
}
