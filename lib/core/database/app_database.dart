import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

import 'schema.dart';

class AppDatabase {
  AppDatabase._();

  static final AppDatabase instance = AppDatabase._();

  Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    await init();
    return _db!;
  }

  Future<void> init() async {
    if (_db != null) return;

    final path = join(
      await getDatabasesPath(),
      'bhavanasara.db',
    );

    _db = await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        for (final statement in schemaStatements) {
          await db.execute(statement);
        }
        await seedBasicData(db);
      },
    );

    await _db!.execute('PRAGMA foreign_keys = ON');
  }

  // Helper method to replace firstIntValue
  Future<int> _getCount(Database db, String tableName) async {
    final result = await db.rawQuery(
      'SELECT COUNT(*) AS count FROM $tableName',
    );

    if (result.isEmpty) return 0;

    final value = result.first['count'];

    if (value is int) {
      return value;
    }

    return int.tryParse(value?.toString() ?? '0') ?? 0;
  }

  Future<void> seedBasicData(Database db) async {
    // Seed period_schemes
    final schemeCount = await _getCount(db, 'period_schemes');

    if (schemeCount == 0) {
      await db.insert(
        'period_schemes',
        {
          'id': 1,
          'name': 'Aṣṭa-kālīya-līlā main periods',
        },
      );
    }

    // Seed period_nodes (8 main periods)
    final periodCount = await _getCount(db, 'period_nodes');

    if (periodCount == 0) {
      final periods = [
        {
          'id': 1,
          'scheme_id': 1,
          'parent_id': null,
          'code': 'nishanta',
          'name': 'Niśānta-līlā',
          'time_start': '03:36',
          'time_end': '06:00',
          'sort_order': 1,
        },
        {
          'id': 2,
          'scheme_id': 1,
          'parent_id': null,
          'code': 'pratah',
          'name': 'Prātaḥ-līlā',
          'time_start': '06:00',
          'time_end': '08:24',
          'sort_order': 2,
        },
        {
          'id': 3,
          'scheme_id': 1,
          'parent_id': null,
          'code': 'purvahna',
          'name': 'Pūrvāhna-līlā',
          'time_start': '08:24',
          'time_end': '10:48',
          'sort_order': 3,
        },
        {
          'id': 4,
          'scheme_id': 1,
          'parent_id': null,
          'code': 'madhyahna',
          'name': 'Madhyāhna-līlā',
          'time_start': '10:48',
          'time_end': '15:36',
          'sort_order': 4,
        },
        {
          'id': 5,
          'scheme_id': 1,
          'parent_id': null,
          'code': 'aparahna',
          'name': 'Aparāhna-līlā',
          'time_start': '15:36',
          'time_end': '18:00',
          'sort_order': 5,
        },
        {
          'id': 6,
          'scheme_id': 1,
          'parent_id': null,
          'code': 'sayahna',
          'name': 'Sāyāhna-līlā',
          'time_start': '18:00',
          'time_end': '20:24',
          'sort_order': 6,
        },
        {
          'id': 7,
          'scheme_id': 1,
          'parent_id': null,
          'code': 'pradosha',
          'name': 'Pradośa-līlā',
          'time_start': '20:24',
          'time_end': '22:48',
          'sort_order': 7,
        },
        {
          'id': 8,
          'scheme_id': 1,
          'parent_id': null,
          'code': 'nisha',
          'name': 'Niśā-līlā',
          'time_start': '22:48',
          'time_end': '03:36',
          'sort_order': 8,
        },
      ];

      for (final period in periods) {
        await db.insert('period_nodes', period);
      }
    }

    // Seed books (30 main books)
    final bookCount = await _getCount(db, 'books');

    if (bookCount == 0) {
      final books = [
        {'id': 1, 'slug': 'srimad-bhagavatam', 'title': 'Śrīmad Bhāgavatam', 'author': 'Veda Vyāsa'},
        {'id': 2, 'slug': 'gopala-campu', 'title': 'Gopāla-campū', 'author': 'Śrīla Jīva Gosvāmī'},
        {'id': 3, 'slug': 'bhakti-rasamrta-sindhu', 'title': 'Bhakti-rasāmṛta-sindhu', 'author': 'Śrīla Rūpa Gosvāmī'},
        {'id': 4, 'slug': 'ujjvala-nilamani', 'title': 'Ujjvala-nīlamaṇi', 'author': 'Śrīla Rūpa Gosvāmī'},
        {'id': 5, 'slug': 'caitanya-caritamrta', 'title': 'Caitanya-caritāmṛta', 'author': 'Śrīla Kṛṣṇadāsa Kavirāja Gosvāmī'},
        {'id': 6, 'slug': 'brhad-bhagavatamrta', 'title': 'Bṛhad-bhāgavatāmṛta', 'author': 'Śrīla Sanātana Gosvāmī'},
        {'id': 7, 'slug': 'ananda-vrndavana-campu', 'title': 'Ānanda-vṛndāvana-campū', 'author': 'Śrīla Kavi Karṇapūra'},
        {'id': 8, 'slug': 'radha-rasa-sudha-nidhi', 'title': 'Rādhā-rasa-sudhā-nidhi', 'author': 'Śrīla Prabodhānanda Sarasvatī'},
        {'id': 9, 'slug': 'vidagdha-madhava', 'title': 'Vidagdha-mādhava', 'author': 'Śrīla Rūpa Gosvāmī'},
        {'id': 10, 'slug': 'lalita-madhava', 'title': 'Lalitā-mādhava', 'author': 'Śrīla Rūpa Gosvāmī'},
        {'id': 11, 'slug': 'vilapa-kusumanjali', 'title': 'Vilāpa-kusumāñjali', 'author': 'Śrīla Raghunātha dāsa Gosvāmī'},
        {'id': 12, 'slug': 'krama-dipika', 'title': 'Krama-dīpīkā', 'author': 'Śrīla Kavi Karṇapūra'},
        {'id': 13, 'slug': 'padyavali', 'title': 'Padyāvalī', 'author': 'Śrīla Rūpa Gosvāmī'},
        {'id': 14, 'slug': 'sangita-madhava', 'title': 'Saṅgīta-mādhava', 'author': 'Śrīla Kavi Karṇapūra'},
        {'id': 15, 'slug': 'stava-mala', 'title': 'Stava-mālā', 'author': 'Śrīla Rūpa Gosvāmī'},
        {'id': 16, 'slug': 'caitanya-caritamrta-maha-kavya', 'title': 'Caitanya-caritāmṛta-mahā-kāvya', 'author': 'Śrīla Kavi Karṇapūra'},
        {'id': 17, 'slug': 'caitanya-candrodaya-nataka', 'title': 'Caitanya-candrodaya-nāṭaka', 'author': 'Śrīla Kavi Karṇapūra'},
        {'id': 18, 'slug': 'govinda-lilamrta', 'title': 'Govinda-līlāmṛta', 'author': 'Śrīla Viśvanātha Cakravartī Ṭhākura'},
        {'id': 19, 'slug': 'stavavali', 'title': 'Stavāvaḷī', 'author': 'Śrīla Rūpa Gosvāmī'},
        {'id': 20, 'slug': 'dana-keli-kaumudi', 'title': 'Dāna-keli-kaumudī', 'author': 'Śrīla Rūpa Gosvāmī'},
        {'id': 21, 'slug': 'krsnahnika-kaumudi', 'title': 'Kṛṣṇāhnika-kaumudī', 'author': 'Śrīla Kavi Karṇapūra'},
        {'id': 22, 'slug': 'gita-govinda', 'title': 'Gīta-govinda', 'author': 'Śrīla Jayadeva Gosvāmī'},
        {'id': 23, 'slug': 'alankara-kaustubha', 'title': 'Alaṅkāra-kaustubha', 'author': 'Śrīla Kavi Karṇapūra'},
        {'id': 24, 'slug': 'jagannatha-vallabha-nataka', 'title': 'Jagannatha-vallabha-nāṭaka', 'author': 'Śrīla Rūpa Gosvāmī'},
        {'id': 25, 'slug': 'krsna-bhavanamrta', 'title': 'Kṛṣṇa-bhāvanāmṛta', 'author': 'Śrīla Viśvanātha Cakravartī Ṭhākura'},
        {'id': 26, 'slug': 'krsna-karnamrta', 'title': 'Kṛṣṇa-karṇāmṛta', 'author': 'Śrīla Bilvamaṅgala Ṭhākura'},
        {'id': 27, 'slug': 'vrndavana-sataka', 'title': 'Vṛndāvana-śātaka', 'author': 'Gaudiya tradition'},
        {'id': 28, 'slug': 'stavamrta-lahari', 'title': 'Stavāmṛta-laharī', 'author': 'Śrīla Raghunātha dāsa Gosvāmī'},
        {'id': 29, 'slug': 'madhu-keli-valli', 'title': 'Madhu-keli-vallī', 'author': 'Gaudiya tradition'},
        {'id': 30, 'slug': 'govinda-rati-manjari', 'title': 'Govinda-rati-mañjarī', 'author': 'Gaudiya tradition'},
      ];

      for (final book in books) {
        await db.insert('books', book);
      }
    }
  }

  // Get all main periods
  Future<List<Map<String, dynamic>>> getMainPeriods() async {
    final db = await database;

    final rows = await db.query(
      'period_nodes',
      where: 'scheme_id = ? AND parent_id IS NULL',
      whereArgs: [1],
      orderBy: 'sort_order ASC',
    );

    return rows
        .map(
          (row) => Map<String, dynamic>.from(row),
        )
        .toList();
  }

  // Get subperiods for a given main period
  Future<List<Map<String, dynamic>>> getSubPeriods(int parentId) async {
    final db = await database;

    final rows = await db.query(
      'period_nodes',
      where: 'parent_id = ?',
      whereArgs: [parentId],
      orderBy: 'sort_order ASC',
    );

    return rows
        .map(
          (row) => Map<String, dynamic>.from(row),
        )
        .toList();
  }

  // Get all books
  Future<List<Map<String, dynamic>>> getBooks() async {
    final db = await database;

    final rows = await db.query(
      'books',
      orderBy: 'id ASC',
    );

    return rows
        .map(
          (row) => Map<String, dynamic>.from(row),
        )
        .toList();
  }

  // Close the database
  Future<void> close() async {
    await _db?.close();
    _db = null;
  }
}