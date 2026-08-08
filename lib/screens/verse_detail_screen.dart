// screens/verse_detail_screen.dart
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../models/verse.dart';
import '../services/bss_repository.dart';
import '../services/translations.dart';

/// A single verse of a scripture in detail: reference, original, translation
/// and commentary from the `verses` table. Reached from the reading pane's
/// reference link and from the book reader. Supports paging through the
/// book's verses in chronological order.
class VerseDetailScreen extends StatefulWidget {
  final BssRepository repository;
  final int verseId;

  const VerseDetailScreen({
    super.key,
    required this.repository,
    required this.verseId,
  });

  @override
  State<VerseDetailScreen> createState() => _VerseDetailScreenState();
}

class _VerseDetailScreenState extends State<VerseDetailScreen> {
  late int _verseId = widget.verseId;
  late Future<Verse?> _verseFuture = _loadVerse(_verseId);

  /// The chronological order of the verse's whole book, used to page
  /// prev/next through it.
  List<Verse> _bookVerses = const [];

  Future<Verse?> _loadVerse(int verseId) async {
    final verse = await widget.repository.getVerseById(verseId);
    if (verse != null && _bookVerses.isEmpty) {
      _bookVerses = await widget.repository.getVersesForBook(verse.bookId);
    }
    return verse;
  }

  void _goTo(int verseId) {
    setState(() {
      _verseId = verseId;
      _verseFuture = _loadVerse(verseId);
    });
  }

  int? get _currentIndex => _bookVerses.indexWhere((v) => v.id == _verseId);

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final subTextCol = isDark ? BssColors.darkOakSubText : BssColors.subText;

    return Scaffold(
      appBar: AppBar(title: Text(Translations.t('screen.verse.title'))),
      body: FutureBuilder<Verse?>(
        future: _verseFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          final verse = snapshot.data;
          if (verse == null) {
            return Center(
              child: Text(
                Translations.t('screen.verse.empty'),
                style: TextStyle(color: subTextCol),
              ),
            );
          }

          final int index = _currentIndex ?? 0;
          final int? prevId = index > 0 ? _bookVerses[index - 1].id : null;
          final int? nextId =
              index < _bookVerses.length - 1 ? _bookVerses[index + 1].id : null;

          return Column(
            children: [
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    Text(
                      verse.refDisplay,
                      style: TextStyle(
                        color: goldColor,
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 12),
                    if (verse.originalText.isNotEmpty) ...[
                      Text(
                        verse.originalText,
                        style: const TextStyle(fontSize: 17, height: 1.4),
                      ),
                      const SizedBox(height: 12),
                    ],
                    if (verse.translationText.isNotEmpty) ...[
                      Text(
                        verse.translationText,
                        style: const TextStyle(fontSize: 16, height: 1.4),
                      ),
                      const SizedBox(height: 12),
                    ],
                    if (verse.commentaryText.isNotEmpty) ...[
                      Text(
                        verse.commentaryText,
                        style: TextStyle(fontSize: 14, height: 1.4, color: subTextCol),
                      ),
                    ],
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  border: Border(
                    top: BorderSide(color: goldColor.withAlpha(76), width: 1.0),
                  ),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    TextButton.icon(
                      onPressed: prevId == null
                          ? null
                          : () => _goTo(prevId),
                      icon: const Icon(Icons.chevron_left),
                      label: Text(Translations.t('common.previous')),
                      style: TextButton.styleFrom(foregroundColor: goldColor),
                    ),
                    TextButton.icon(
                      onPressed: nextId == null
                          ? null
                          : () => _goTo(nextId),
                      icon: const Icon(Icons.chevron_right),
                      label: Text(Translations.t('common.next')),
                      iconAlignment: IconAlignment.end,
                      style: TextButton.styleFrom(foregroundColor: goldColor),
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
