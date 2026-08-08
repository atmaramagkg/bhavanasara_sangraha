// screens/book_reader_screen.dart
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../models/book.dart';
import '../models/verse.dart';
import '../services/bss_repository.dart';
import '../services/translations.dart';
import 'verse_detail_screen.dart';

/// A full-text reader for one source scripture: all of its verses from the
/// `verses` table in chronological order. The verses table is gradually
/// populated with full texts, so for now most rows only carry the quoted
/// translation -- as full texts arrive they appear here automatically.
class BookReaderScreen extends StatefulWidget {
  final BssRepository repository;
  final Book book;

  const BookReaderScreen({
    super.key,
    required this.repository,
    required this.book,
  });

  @override
  State<BookReaderScreen> createState() => _BookReaderScreenState();
}

class _BookReaderScreenState extends State<BookReaderScreen> {
  late Future<List<Verse>> _versesFuture;

  @override
  void initState() {
    super.initState();
    _versesFuture = widget.repository.getVersesForBook(widget.book.id);
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final textColor = isDark ? BssColors.darkOakText : BssColors.darkText;
    final subTextCol = isDark ? BssColors.darkOakSubText : BssColors.subText;

    return Scaffold(
      appBar: AppBar(title: Text(widget.book.title)),
      body: FutureBuilder<List<Verse>>(
        future: _versesFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          final verses = snapshot.data ?? const [];
          if (verses.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  Translations.t('screen.book_reader.empty'),
                  textAlign: TextAlign.center,
                  style: TextStyle(color: subTextCol),
                ),
              ),
            );
          }

          return ListView.separated(
            padding: const EdgeInsets.all(12),
            itemCount: verses.length,
            separatorBuilder: (_, _) => Divider(height: 1, color: goldColor.withAlpha(60)),
            itemBuilder: (context, index) {
              final v = verses[index];
              return InkWell(
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => VerseDetailScreen(
                        repository: widget.repository,
                        verseId: v.id,
                      ),
                    ),
                  );
                },
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 4),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              v.refDisplay,
                              style: TextStyle(
                                color: goldColor,
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                          ),
                          Icon(Icons.chevron_right, size: 16, color: goldColor.withAlpha(160)),
                        ],
                      ),
                      const SizedBox(height: 6),
                      if (v.originalText.isNotEmpty) ...[
                        Text(
                          v.originalText,
                          style: const TextStyle(fontSize: 15, height: 1.4),
                        ),
                        const SizedBox(height: 6),
                      ],
                      if (v.translationText.isNotEmpty)
                        Text(
                          v.translationText,
                          style: TextStyle(
                            fontSize: 14,
                            height: 1.4,
                            fontFamily: 'NotoSerif',
                            color: textColor,
                          ),
                        ),
                      if (v.commentaryText.isNotEmpty) ...[
                        const SizedBox(height: 6),
                        Text(
                          v.commentaryText,
                          style: TextStyle(fontSize: 13, height: 1.4, color: subTextCol),
                        ),
                      ],
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
