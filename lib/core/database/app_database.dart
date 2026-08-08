import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart' show rootBundle, AssetManifest;
import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

/// A language that ships with the app, discovered from a bundled database
/// file (`assets/db/Bhavanasara-Sangraha_<code>.sqlite`).
class AvailableLanguage {
  final String code;
  final String name;

  const AvailableLanguage({required this.code, required this.name});
}

/// Every user-visible word comes from the `translations` table
/// inside the bundled database. Nothing is hardcoded here.
class AppDatabase {
  AppDatabase._();

  static final AppDatabase instance = AppDatabase._();

  /// Which language file is currently open. Each language ships as its own
  /// self-contained database (content + translations in that language).
  static String _languageCode = 'en';

  /// Pre-built databases shipped inside the app assets.
  static const String _enAssetPath =
      'assets/db/Bhavanasara-Sangraha_En.sqlite';
  static const String _ruAssetPath =
      'assets/db/Bhavanasara-Sangraha_Ru.sqlite';

  static final RegExp _assetNamePattern =
      RegExp(r'assets/db/Bhavanasara-Sangraha_(\w+)\.sqlite$');

  static String get _assetPath =>
      _languageCode == 'ru' ? _ruAssetPath : _enAssetPath;

  static String get _dbFileName => 'bhavanasara_$_languageCode.db';

  Database? _db;

  /// Languages bundled with the app, discovered from the database files that
  /// are actually present in the assets. The display name of each language is
  /// read from its own file's `languages` table, so no language list is
  /// hardcoded in code.
  static Future<List<AvailableLanguage>> availableLanguages() async {
    final AssetManifest manifest =
        await AssetManifest.loadFromAssetBundle(rootBundle);
    final List<AvailableLanguage> result = <AvailableLanguage>[];

    for (final String asset in manifest.listAssets()) {
      final Match? match = _assetNamePattern.firstMatch(asset);
      if (match == null) continue;

      final String code = match.group(1)!.toLowerCase();
      final String name = await _languageNameFromAsset(asset, code);
      result.add(AvailableLanguage(code: code, name: name));
    }

    result.sort((a, b) => a.code.compareTo(b.code));
    return result;
  }

  /// Reads the `languages` table of a bundled database file to get the native
  /// name of [code]. The file is probed through a throwaway writable copy so
  /// sqlite can open it; the active databases are not affected.
  static Future<String> _languageNameFromAsset(
    String assetPath,
    String code,
  ) async {
    try {
      final ByteData data = await rootBundle.load(assetPath);
      final Uint8List bytes =
          data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes);

      final String probePath = join(
        await getDatabasesPath(),
        'lang_probe_$code.db',
      );
      final File probe = File(probePath);
      if (!await probe.exists() ||
          !listEquals(await probe.readAsBytes(), bytes)) {
        await Directory(dirname(probePath)).create(recursive: true);
        await probe.writeAsBytes(bytes, flush: true);
      }

      final Database probeDb = await openDatabase(probePath, readOnly: true);
      try {
        final List<Map<String, Object?>> rows = await probeDb.query(
          'languages',
          columns: ['name'],
          where: 'code = ?',
          whereArgs: [code],
          limit: 1,
        );
        if (rows.isNotEmpty) return rows.first['name'] as String;
      } finally {
        await probeDb.close();
      }
    } catch (_) {
      // Fall through: report the code itself if the file cannot be read.
    }
    return code;
  }

  Future<Database> get database async {
    if (_db != null) return _db!;
    await init();
    return _db!;
  }

  /// Copies the bundled database to a writable location, refreshing it
  /// whenever the bundled asset changes (e.g. after a translation update).
  Future<void> init() async {
    if (_db != null) return;

    final String path = join(
      await getDatabasesPath(),
      _dbFileName,
    );

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
    await _ensureLanguage(_languageCode);
  }

  /// Switches the app to the database file for [code] ('en' or 'ru').
  /// Closes the current database, opens the matching one and makes sure its
  /// `languages`/`app_settings` rows describe [code].
  Future<void> switchDatabase(String code) async {
    final String next = code == 'ru' ? 'ru' : 'en';
    if (next == _languageCode && _db != null) return;

    await _db?.close();
    _db = null;
    _languageCode = next;
    await init();
  }

  /// Ensures a `languages` row and the `selected_language_code` setting
  /// exist for [code] so the COALESCE translation queries resolve correctly
  /// no matter how the bundled file was produced.
  Future<void> _ensureLanguage(String code) async {
    final Database? db = _db;
    if (db == null) return;

    final List<Map<String, Object?>> existing = await db.query(
      'languages',
      columns: ['id'],
      where: 'code = ?',
      whereArgs: [code],
    );
    if (existing.isEmpty) {
      final List<Map<String, Object?>> maxId = await db.rawQuery(
        'SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM languages',
      );
      final int nextId = maxId.first['next_id'] as int;
      await db.insert('languages', {
        'id': nextId,
        'code': code,
        'name': code == 'ru' ? 'Русский' : 'English',
        'is_default': 0,
      });
    }

    await db.insert(
      'app_settings',
      {'setting_key': 'selected_language_code', 'setting_value': code},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
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

  /// Loads every translation into a lookup map for the current language,
  /// following the same fallback as [translate]: selected language ->
  /// English -> the key itself. Keys not present in any language are skipped.
  Future<Map<String, String>> loadTranslations() async {
    final Database db = await database;
    final int langId = await getCurrentLanguageId();

    final List<Map<String, Object?>> enRows = await db.rawQuery(
      "SELECT id FROM languages WHERE code = 'en'",
    );
    final int enId = enRows.isNotEmpty ? enRows.first['id'] as int : 1;

    final List<Map<String, Object?>> rows = await db.rawQuery(
      '''
      SELECT t.translation_key AS key,
        COALESCE(
          (SELECT translated_text FROM translations
            WHERE translation_key = t.translation_key AND language_id = ?),
          (SELECT translated_text FROM translations
            WHERE translation_key = t.translation_key AND language_id = ?),
          t.translation_key
        ) AS text
      FROM (SELECT DISTINCT translation_key FROM translations) t
      ''',
      [langId, enId],
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