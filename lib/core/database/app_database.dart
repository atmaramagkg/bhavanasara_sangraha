import 'dart:io';
import 'package:flutter/services.dart' show rootBundle;
import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

class AppDatabase {
  AppDatabase._();

  static final AppDatabase instance = AppDatabase._();

  static const String _dbFileName = 'Bhavanasara-Sangraha_En.sqlite';
  static const String _assetPath = 'assets/db/Bhavanasara-Sangraha_En.sqlite';

  Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    await init();
    return _db!;
  }

  Future<void> init() async {
    if (_db != null) return;

    final databasesPath = await getDatabasesPath();
    final path = join(databasesPath, _dbFileName);

    final exists = await databaseExists(path);

    if (!exists) {
      // Ensure the directory exists
      await Directory(dirname(path)).create(recursive: true);

      // Copy from assets to writable location on the device
      final data = await rootBundle.load(_assetPath);
      final bytes = data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes);
      await File(path).writeAsBytes(bytes, flush: true);
    }

    // Open the copied database
    _db = await openDatabase(path);

    await _db!.execute('PRAGMA foreign_keys = ON');
  }

  // Get all main periods with translated names
  Future<List<Map<String, dynamic>>> getMainPeriods({int languageId = 1}) async {
    final db = await database;

    final rows = await db.rawQuery('''
      SELECT 
        pn.id, 
        pn.code, 
        pn.time_start, 
        pn.time_end, 
        pn.sort_order,
        t.translated_text AS name
      FROM period_nodes pn
      LEFT JOIN translations t ON pn.name_key = t.translation_key AND t.language_id = ?
      WHERE pn.parent_id IS NULL
      ORDER BY pn.sort_order ASC
    ''', [languageId]);

    return rows.map((row) => Map<String, dynamic>.from(row)).toList();
  }

  // Get subperiods for a given main period with translated names
  Future<List<Map<String, dynamic>>> getSubPeriods(int parentId, {int languageId = 1}) async {
    final db = await database;

    final rows = await db.rawQuery('''
      SELECT 
        pn.id, 
        pn.code, 
        pn.time_start, 
        pn.time_end, 
        pn.sort_order,
        t.translated_text AS name
      FROM period_nodes pn
      LEFT JOIN translations t ON pn.name_key = t.translation_key AND t.language_id = ?
      WHERE pn.parent_id = ?
      ORDER BY pn.sort_order ASC
    ''', [languageId, parentId]);

    return rows.map((row) => Map<String, dynamic>.from(row)).toList();
  }

  // Get all books with translated titles and authors
  Future<List<Map<String, dynamic>>> getBooks({int languageId = 1}) async {
    final db = await database;

    final rows = await db.rawQuery('''
      SELECT 
        b.id, 
        b.slug,
        t_title.translated_text AS title,
        t_author.translated_text AS author
      FROM books b
      LEFT JOIN translations t_title ON b.title_key = t_title.translation_key AND t_title.language_id = ?
      LEFT JOIN translations t_author ON b.author_key = t_author.translation_key AND t_author.language_id = ?
      ORDER BY b.id ASC
    ''', [languageId, languageId]);

    return rows.map((row) => Map<String, dynamic>.from(row)).toList();
  }

  // Close the database
  Future<void> close() async {
    await _db?.close();
    _db = null;
  }
}