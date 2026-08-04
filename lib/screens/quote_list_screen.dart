import 'package:flutter/material.dart';

import '../core/database/app_database.dart';

/// Level 4 screen: shows the quotes of one section,
/// each with its source citation(s).
class QuoteListScreen extends StatelessWidget {
  final Map<String, dynamic> section;

  const QuoteListScreen({super.key, required this.section});

  // ------------------------------------------------------------------
  // Database queries (self-contained)
  // ------------------------------------------------------------------

  Future<List<Map<String, dynamic>>> _loadQuotes() async {
    final db = await AppDatabase.instance.database;

    final rows = await db.rawQuery('''
      SELECT id, quote_type, quote_text, sort_order
      FROM quotes
      WHERE section_id = ?
      ORDER BY sort_order ASC
    ''', [section['id']]);

    return rows.map((row) => Map<String, dynamic>.from(row)).toList();
  }

  Future<List<Map<String, dynamic>>> _loadCitations(int quoteId) async {
    final db = await AppDatabase.instance.database;

    final rows = await db.rawQuery('''
      SELECT c.id, c.ref_display, c.source_verse_id,
             b.title AS book_title
      FROM citations c
      LEFT JOIN books b ON b.id = c.source_book_id
      WHERE c.quote_id = ?
      ORDER BY c.id ASC
    ''', [quoteId]);

    return rows.map((row) => Map<String, dynamic>.from(row)).toList();
  }

  // ------------------------------------------------------------------
  // UI
  // ------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    final String sectionTitle = section['title'] as String? ?? '';

    return Scaffold(
      appBar: AppBar(title: Text(sectionTitle)),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _loadQuotes(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(child: Text('Database error: ${snapshot.error}'));
          }

          final List<Map<String, dynamic>> quotes = snapshot.data ?? [];

          if (quotes.isEmpty) {
            return const Center(
              child: Text('No quotes yet for this section.'),
            );
          }

          return ListView.separated(
            itemCount: quotes.length,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (context, index) {
              return _QuoteCard(
                quote: quotes[index],
                loadCitations: _loadCitations,
              );
            },
          );
        },
      ),
    );
  }
}

class _QuoteCard extends StatelessWidget {
  final Map<String, dynamic> quote;
  final Future<List<Map<String, dynamic>>> Function(int) loadCitations;

  const _QuoteCard({
    required this.quote,
    required this.loadCitations,
  });

  @override
  Widget build(BuildContext context) {
    final int quoteId = quote['id'] as int;
    final String quoteText = quote['quote_text'] as String? ?? '';
    final String quoteType = quote['quote_type'] as String? ?? '';

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (quoteType.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Text(
                  quoteType,
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
            Text(quoteText),
            const SizedBox(height: 10),
            FutureBuilder<List<Map<String, dynamic>>>(
              future: loadCitations(quoteId),
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const SizedBox.shrink();
                }

                final List<Map<String, dynamic>> citations =
                    snapshot.data ?? [];

                if (citations.isEmpty) {
                  return const SizedBox.shrink();
                }

                return Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: [
                    for (final citation in citations)
                      ActionChip(
                        label: Text(
                          citation['ref_display'] as String? ?? '',
                        ),
                        onPressed: () {
                          // Verse reader screen comes in the next step.
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(
                                '${citation['book_title'] ?? ''} '
                                '${citation['ref_display'] ?? ''}',
                              ),
                            ),
                          );
                        },
                      ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}