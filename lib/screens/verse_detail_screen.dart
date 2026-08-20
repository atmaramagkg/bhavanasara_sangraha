// screens/verse_detail_screen.dart
import 'package:flutter/material.dart';
import '../app_theme.dart';
import '../models/verse.dart';
import '../services/app_settings.dart';
import '../services/bss_repository.dart';
import '../services/translations.dart';

/// A single verse in detail: transliteration, Sanskrit text, and translation
/// in the current language. Supports paging through the book's verses.
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
  late final Future<List<Verse>> _bookFuture = _loadBook();
  late final PageController _pageController = PageController();
  int _currentPage = 0;
  int _initialIndex = 0;
  bool _needsInitialJump = true;

  Future<List<Verse>> _loadBook() async {
    final verse = await widget.repository.getVerseById(widget.verseId);
    if (verse == null) return const [];
    if (verse.bookId == null) return [verse];
    final verses = await widget.repository.getVersesForBook(verse.bookId!);
    final idx = verses.indexWhere((v) => v.id == widget.verseId);
    _initialIndex = idx >= 0 ? idx : 0;
    return verses;
  }

  void _goTo(int page) {
    _pageController.animateToPage(
      page,
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeInOut,
    );
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final subTextCol = isDark ? BssColors.darkOakSubText : BssColors.subText;

    return Scaffold(
      appBar: AppBar(
        title: Text(Translations.t('screen.verse.title')),
      ),
      body: FutureBuilder<List<Verse>>(
        future: _bookFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          final verses = snapshot.data ?? const <Verse>[];
          if (verses.isEmpty) {
            return Center(
              child: Text(
                Translations.t('screen.verse.empty'),
                style: TextStyle(color: subTextCol),
              ),
            );
          }

          if (_needsInitialJump) {
            _needsInitialJump = false;
            if (_initialIndex > 0) {
              _currentPage = _initialIndex;
              WidgetsBinding.instance.addPostFrameCallback((_) {
                if (mounted && _pageController.hasClients) {
                  _pageController.jumpToPage(_initialIndex);
                }
              });
            }
          }

          final int currentPage = _currentPage.clamp(0, verses.length - 1).toInt();

          return Column(
            children: [
              Expanded(
                child: PageView.builder(
                  controller: _pageController,
                  itemCount: verses.length,
                  onPageChanged: (page) {
                    setState(() => _currentPage = page);
                  },
                  itemBuilder: (context, index) =>
                      _VersePage(verse: verses[index]),
                ),
              ),
              SafeArea(
                top: false,
                child: Container(
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
                        onPressed: currentPage == 0
                            ? null
                            : () => _goTo(currentPage - 1),
                        icon: const Icon(Icons.chevron_left),
                        label: Text(Translations.t('common.previous')),
                        style: TextButton.styleFrom(foregroundColor: goldColor),
                      ),
                      Text(
                        '${currentPage + 1} / ${verses.length}',
                        style: TextStyle(color: subTextCol, fontSize: 13),
                      ),
                      TextButton.icon(
                        onPressed: currentPage == verses.length - 1
                            ? null
                            : () => _goTo(currentPage + 1),
                        icon: const Icon(Icons.chevron_right),
                        label: Text(Translations.t('common.next')),
                        iconAlignment: IconAlignment.end,
                        style: TextButton.styleFrom(foregroundColor: goldColor),
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

/// The scrollable content of one verse page.
class _VersePage extends StatelessWidget {
  final Verse verse;

  const _VersePage({required this.verse});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final goldColor = isDark ? BssColors.darkOakGold : BssColors.goldAccent;
    final subTextCol = isDark ? BssColors.darkOakSubText : BssColors.subText;
    final sanskritColor = isDark ? BssColors.darkOakSanskritText : BssColors.sanskritText;
    final langCode = AppSettings.locale.value.languageCode;
    final translation = verse.translationForCode(langCode);

    return ListView(
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
        if (verse.sanskritText.isNotEmpty) ...[
          Text(
            verse.sanskritText,
            style: TextStyle(fontSize: 18, height: 1.6, color: sanskritColor),
          ),
          const SizedBox(height: 8),
        ],
        if (verse.transliteration.isNotEmpty) ...[
          Text(
            verse.transliteration,
            style: TextStyle(
              fontSize: 15,
              height: 1.4,
              fontStyle: FontStyle.italic,
              color: subTextCol,
            ),
          ),
          const SizedBox(height: 12),
        ],
        if (translation.isNotEmpty) ...[
          Text(
            translation,
            style: const TextStyle(fontSize: 16, height: 1.4),
          ),
        ],
      ],
    );
  }
}
