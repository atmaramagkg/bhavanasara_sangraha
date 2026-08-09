import 'package:flutter/material.dart';

import '../core/database/app_database.dart';

class VerseReaderScreen extends StatefulWidget {
  final int verseId;

  const VerseReaderScreen({super.key, required this.verseId});

  @override
  State<VerseReaderScreen> createState() => _VerseReaderScreenState();
}

class _VerseReaderScreenState extends State<VerseReaderScreen> {
  late int _verseId = widget.verseId;

  Future<Map<String, dynamic>> _loadData(int id) async {
    final db = await AppDatabase.instance.database;
    final int langId = await AppDatabase.instance.getCurrentLanguageId();

    final rows = await db.rawQuery('''
      SELECT v.*,
        COALESCE(
          (SELECT translated_text FROM translations
            WHERE translation_key = b.title_key AND language_id = ?),
          (SELECT translated_text FROM translations
            WHERE translation_key = b.title_key
              AND language_id = (SELECT id FROM languages WHERE code = 'en')),
          b.slug
        ) AS book_title
      FROM verses v
      JOIN books b ON b.id = v.book_id
      WHERE v.id = ?
    ''', [langId, id]);

    if (rows.isEmpty) return {'verse': null};

    final verse = Map<String, dynamic>.from(rows.first);
    final int bookId = verse['book_id'] as int;
    final int sortOrder = verse['sort_order'] as int;

    final prev = await db.rawQuery('''
      SELECT id FROM verses
      WHERE book_id = ? AND sort_order < ?
      ORDER BY sort_order DESC LIMIT 1
    ''', [bookId, sortOrder]);

    final next = await db.rawQuery('''
      SELECT id FROM verses
      WHERE book_id = ? AND sort_order > ?
      ORDER BY sort_order ASC LIMIT 1
    ''', [bookId, sortOrder]);

    return {
      'verse': verse,
      'prevId': prev.isEmpty ? null : prev.first['id'],
      'nextId': next.isEmpty ? null : next.first['id'],
    };
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Verse')),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _loadData(_verseId),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(child: Text('Database error: ${snapshot.error}'));
          }

          final data = snapshot.data ?? {};
          final verse = data['verse'] as Map<String, dynamic>?;

          if (verse == null) {
            return const Center(child: Text('Verse not found.'));
          }

          final int? prevId = data['prevId'] as int?;
          final int? nextId = data['nextId'] as int?;
          final String? original = verse['original_text'] as String?;
          final String translation = verse['translation_text'] as String? ?? '';

          return Column(
            children: [
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    Text(
                      '${verse['book_title']}  ${verse['ref_display']}',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 12),
                    if (original != null && original.isNotEmpty) ...[
                      Text(original, style: const TextStyle(fontSize: 16)),
                      const SizedBox(height: 12),
                    ],
                    Text(translation, style: const TextStyle(fontSize: 16)),
                  ],
                ),
              ),
              SafeArea(
                top: false,
                child: Container(
                  padding: const EdgeInsets.all(8),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      ElevatedButton(
                        onPressed: prevId == null
                            ? null
                            : () => setState(() => _verseId = prevId),
                        child: const Text('Previous'),
                      ),
                      ElevatedButton(
                        onPressed: nextId == null
                            ? null
                            : () => setState(() => _verseId = nextId),
                        child: const Text('Next'),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}